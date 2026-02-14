from flask import Flask, jsonify, request, abort, render_template, redirect, url_for
from peewee import SqliteDatabase, fn
from src.models import db, Book, Chapter, Verse, Entity, VerseEntity, VerbStat
from src.search import BibleSearch
import time
import math

app = Flask(__name__)

# Initialize database
database = SqliteDatabase("bible.db")
db.initialize(database)

searcher = BibleSearch()


@app.before_request
def _db_connect():
    if db.is_closed():
        db.connect()


@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


# API Routes
@app.route("/api/books", methods=["GET"])
def get_books():
    books = Book.select().order_by(Book.id)
    return jsonify([{"id": book.id, "name": book.name} for book in books])


@app.route("/api/books/<int:book_id>/chapters", methods=["GET"])
def get_chapters(book_id):
    try:
        book = Book.get_by_id(book_id)
    except Book.DoesNotExist:
        abort(404, description="Book not found")

    chapters = Chapter.select().where(Chapter.book == book).order_by(Chapter.number)
    return jsonify(
        [{"id": chapter.id, "number": chapter.number} for chapter in chapters]
    )


@app.route("/api/passage", methods=["GET"])
def get_passage():
    ref = request.args.get("ref")
    if not ref:
        abort(400, description="Missing 'ref' parameter")

    start_time = time.time()
    results = searcher.parse_and_search(ref)
    duration = time.time() - start_time

    if not results:
        abort(404, description="Reference not found")

    response_data = {
        "data": [
            {
                "book": r.chapter.book.name,
                "chapter": r.chapter.number,
                "verse": r.number,
                "text": r.text,
            }
            for r in results
        ],
        "meta": {"total": len(results), "execution_time": duration},
    }
    return jsonify(response_data)


@app.route("/api/search", methods=["GET"])
def search_verses():
    query = request.args.get("q")
    if not query:
        abort(400, description="Missing 'q' parameter")

    try:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        use_lemma = request.args.get("use_lemma", "false").lower() == "true"
        entity = request.args.get("entity")
        construction = request.args.get("construction")  # command or hypothetical
        sort = request.args.get("sort")
    except ValueError:
        abort(400, description="Invalid limit or offset")

    start_time = time.time()
    results = searcher.search(
        query,
        limit=limit,
        offset=offset,
        use_lemma=use_lemma,
        entity_filter=entity,
        construction_filter=construction,
        sort=sort,
    )
    duration = time.time() - start_time

    return jsonify(
        {
            "data": [
                {
                    "book": r.chapter.book.name,
                    "chapter": r.chapter.number,
                    "verse": r.number,
                    "text": r.text,
                    "lemma": r.lemma_text,
                    "is_command": r.is_command,
                    "is_hypothetical": r.is_hypothetical,
                }
                for r in results
            ],
            "meta": {
                "count": len(results),  # This is page count
                "execution_time": duration,
            },
        }
    )


# Frontend Routes
@app.route("/")
def index():
    books = Book.select().order_by(Book.id)
    # Get top 100 entities for the datalist/dropdown
    top_entities = (
        Entity.select(Entity.name)
        .join(VerseEntity)
        .group_by(Entity.name)
        .order_by(fn.COUNT(VerseEntity.id).desc())
        .limit(100)
    )
    return render_template("index.html", books=books, top_entities=top_entities)


@app.route("/read")
def read_redirect():
    # Redirect to Genesis 1 if no params
    return redirect(url_for("read_chapter", book_name="Genesis", chapter_num=1))


@app.route("/read/<book_name>/<int:chapter_num>")
def read_chapter(book_name, chapter_num):
    try:
        book = Book.get(fn.Lower(Book.name) == book_name.lower())
    except Book.DoesNotExist:
        abort(404, description="Book not found")

    try:
        chapter = Chapter.get(Chapter.book == book, Chapter.number == chapter_num)
    except Chapter.DoesNotExist:
        abort(404, description="Chapter not found")

    verses = Verse.select().where(Verse.chapter == chapter).order_by(Verse.number)

    # Navigation Logic
    prev_chapter = None
    next_chapter = None

    # Previous
    if chapter.number > 1:
        prev_chapter = {"book_name": book.name, "chapter_num": chapter.number - 1}
    else:
        # Get previous book
        prev_book = (
            Book.select().where(Book.id < book.id).order_by(Book.id.desc()).first()
        )
        if prev_book:
            # Get last chapter of previous book
            last_chap = (
                Chapter.select()
                .where(Chapter.book == prev_book)
                .order_by(Chapter.number.desc())
                .first()
            )
            if last_chap:
                prev_chapter = {
                    "book_name": prev_book.name,
                    "chapter_num": last_chap.number,
                }

    # Next
    # Check if next chapter exists in current book
    next_chap_in_book = (
        Chapter.select()
        .where(Chapter.book == book, Chapter.number == chapter.number + 1)
        .first()
    )
    if next_chap_in_book:
        next_chapter = {"book_name": book.name, "chapter_num": chapter.number + 1}
    else:
        # Get next book
        next_book = Book.select().where(Book.id > book.id).order_by(Book.id).first()
        if next_book:
            next_chapter = {"book_name": next_book.name, "chapter_num": 1}

    return render_template(
        "read.html",
        book=book,
        chapter=chapter,
        verses=verses,
        prev_chapter=prev_chapter,
        next_chapter=next_chapter,
    )


@app.route("/search")
def search_page():
    query = request.args.get("q")
    if not query:
        return redirect(url_for("index"))

    page = request.args.get("page", 1, type=int)
    use_lemma = request.args.get("use_lemma", "off") == "on"  # Checkbox sends 'on'
    entity = request.args.get("entity", "").strip()
    construction = request.args.get("construction", "").strip()
    sort = request.args.get("sort", "rank").strip()

    if not entity:
        entity = None
    if not construction:
        construction = None

    per_page = 20
    offset = (page - 1) * per_page

    # Check if it's a reference (only if not doing advanced search)
    if not use_lemma and not entity and not construction and page == 1:
        from src.nlp import extract_bible_references

        ref_meta = extract_bible_references(query)

        if ref_meta:
            # Redirect to the first reference found
            r = ref_meta[0]
            target_url = url_for(
                "read_chapter", book_name=r["book"], chapter_num=r["chapter"]
            )
            if r["verse_start"]:
                target_url += f"#verse-{r['verse_start']}"
            return redirect(target_url)

    # Otherwise text search
    start_time = time.time()
    results = searcher.search(
        query,
        limit=per_page,
        offset=offset,
        use_lemma=use_lemma,
        entity_filter=entity,
        construction_filter=construction,
        sort=sort,
    )
    duration = time.time() - start_time

    # Get top entities for refinement as well
    top_entities = (
        Entity.select(Entity.name)
        .join(VerseEntity)
        .group_by(Entity.name)
        .order_by(fn.COUNT(VerseEntity.id).desc())
        .limit(100)
    )

    return render_template(
        "results.html",
        query=query,
        verses=results,
        count=len(results),
        page=page,
        per_page=per_page,
        use_lemma=use_lemma,
        entity=entity,
        construction=construction,
        sort=sort,
        top_entities=top_entities,
    )


@app.route("/analysis")
def analysis_page():
    # Get all verb stats, sorted by total occurrences
    stats = VerbStat.select().order_by(VerbStat.total_count.desc()).limit(100)
    return render_template("analysis.html", stats=stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
