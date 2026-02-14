from flask import Flask, jsonify, request, abort, render_template, redirect, url_for
from peewee import SqliteDatabase
from src.models import db, Sentence
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
    query = request.args.get("q")
    if not query:
        abort(400, description="Missing 'q' parameter")

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
                }
                for r in results
            ],
            "meta": {
                "count": len(results),
                "execution_time": duration,
            },
        }
    )


# Frontend Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search_page():
    query = request.args.get("q")
    if not query:
        return redirect(url_for("index"))

    page = request.args.get("page", 1, type=int)
    use_lemma = request.args.get("use_lemma", "off") == "on"
    sort = request.args.get("sort", "rank").strip()
    is_command = request.args.get("is_command") == "on"
    is_hypothetical = request.args.get("is_hypothetical") == "on"

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
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
