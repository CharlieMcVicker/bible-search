from flask import Flask, jsonify, request, abort, render_template, redirect, url_for
from peewee import SqliteDatabase
from src.models import db, Sentence, SentenceTag
from src.search import SearchEngine
import time

app = Flask(__name__)

# Initialize database
database = SqliteDatabase("bible.db")
db.initialize(database)

searcher = SearchEngine()


@app.before_request
def _db_connect():
    if db.is_closed():
        db.connect()


@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


# API Routes


@app.route("/api/search", methods=["GET"])
def search_sentences():
    query = request.args.get("q", "")

    # Check if we have filters
    has_filters = any(
        k in request.args
        for k in ["is_command", "is_hypothetical", "is_time_clause", "tag"]
    )

    if not query and not has_filters:
        abort(400, description="Missing 'q' parameter or filters")

    try:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        use_lemma = request.args.get("use_lemma", "false").lower() == "true"
        sort = request.args.get("sort")
        is_command = request.args.get("is_command")
        if is_command is not None:
            is_command = is_command.lower() == "true"
        is_hypothetical = request.args.get("is_hypothetical")
        if is_hypothetical is not None:
            is_hypothetical = is_hypothetical.lower() == "true"
        is_time_clause = request.args.get("is_time_clause")
        if is_time_clause is not None:
            is_time_clause = is_time_clause.lower() == "true"
        tag_filter = request.args.get("tag")
    except ValueError:
        abort(400, description="Invalid limit or offset")

    start_time = time.time()
    results = searcher.search(
        query,
        limit=limit,
        offset=offset,
        use_lemma=use_lemma,
        sort=sort,
        is_command=is_command,
        is_hypothetical=is_hypothetical,
        is_time_clause=is_time_clause,
        tag_filter=tag_filter,
    )
    duration = time.time() - start_time

    return jsonify(
        {
            "data": [
                {
                    "ref_id": r.ref_id,
                    "english": r.english,
                    "syllabary": r.syllabary,
                    "phonetic": r.phonetic,
                    "audio": r.audio,
                    "lemma": r.lemma_text,
                    "tags": getattr(r, "tags", []),
                }
                for r in results
            ],
            "meta": {
                "count": len(results),
                "execution_time": duration,
            },
        }
    )


@app.route("/api/sentences/<ref_id>/tags", methods=["POST"])
def add_tag(ref_id):
    data = request.json
    word_index = data.get("word_index")
    tag = data.get("tag")

    if word_index is None or not tag:
        abort(400, description="Missing word_index or tag")

    try:
        # Use primary key of SentenceTag if defined, or just replace by unique constraint
        SentenceTag.replace(ref_id=ref_id, word_index=word_index, tag=tag).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sentences/<ref_id>/tags", methods=["DELETE"])
def remove_tag(ref_id):
    data = request.json
    word_index = data.get("word_index")

    if word_index is None:
        abort(400, description="Missing word_index")

    query = SentenceTag.delete().where(
        (SentenceTag.ref_id == ref_id) & (SentenceTag.word_index == word_index)
    )
    rows = query.execute()
    return jsonify({"status": "success", "deleted": rows})


# Frontend Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search_page():
    query = request.args.get("q", "")

    # Check if we have filters
    has_filters = any(
        k in request.args
        for k in [
            "is_command",
            "is_hypothetical",
            "is_time_clause",
            "tag",
            "subclause_types",
        ]
    )

    if not query and not has_filters:
        return redirect(url_for("index"))

    page = request.args.get("page", 1, type=int)
    use_lemma = request.args.get("use_lemma", "off") == "on"
    sort = request.args.get("sort", "rank").strip()
    is_command = request.args.get("is_command") == "on"
    is_hypothetical = request.args.get("is_hypothetical") == "on"
    is_time_clause = request.args.get("is_time_clause") == "on"
    tag_filter = request.args.get("tag", "").strip() or None

    # Subclause types from multi-select or multiple checkboxes
    selected_subclauses = request.args.getlist("subclause_types")

    # Human readable mapping
    SUBCLAUSE_LABELS = {
        "any": "Any Subclause",
        "none": "No Subclauses",
        "advcl": "Adverbial Clause (When, If, etc.)",
        "relcl": "Relative Clause (Who, Which, etc.)",
        "ccomp": "Clausal Complement (He said that...)",
        "xcomp": "Open Clausal Complement (He wants to...)",
        "acl": "Adjectival Clause (The effort to...)",
        "csubj": "Clausal Subject",
        "csubjpass": "Clausal Passive Subject",
    }

    per_page = 20
    offset = (page - 1) * per_page

    start_time = time.time()
    results = searcher.search(
        query,
        limit=per_page,
        offset=offset,
        use_lemma=use_lemma,
        sort=sort,
        is_command=is_command or None,
        is_hypothetical=is_hypothetical or None,
        subclause_types=selected_subclauses or None,
        is_time_clause=is_time_clause or None,
        tag_filter=tag_filter,
    )
    duration = time.time() - start_time

    return render_template(
        "results.html",
        query=query,
        sentences=results,
        count=len(results),
        page=page,
        per_page=per_page,
        use_lemma=use_lemma,
        sort=sort,
        is_command=is_command,
        is_hypothetical=is_hypothetical,
        is_time_clause=is_time_clause,
        tag_filter=tag_filter,
        subclause_labels=SUBCLAUSE_LABELS,
        selected_subclauses=selected_subclauses,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
