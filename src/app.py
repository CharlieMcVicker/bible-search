from flask import (
    Flask,
    jsonify,
    request,
    abort,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
from peewee import SqliteDatabase
from src.models import db, Sentence, SentenceTag
from src.search import SearchEngine
import time
import os

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")

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


@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")


# API Routes


@app.route("/api/search", methods=["GET"])
def search_sentences():
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
            "untagged_only",
        ]
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
        untagged_only = request.args.get("untagged_only", "false").lower() == "true"
        tag_filter = request.args.get("tag")
        subclause_types = request.args.getlist("subclause_types")
    except ValueError:
        abort(400, description="Invalid limit or offset")

    start_time = time.time()
    results, total_count = searcher.search(
        query,
        limit=limit,
        offset=offset,
        use_lemma=use_lemma,
        sort=sort,
        is_command=is_command,
        is_hypothetical=is_hypothetical,
        is_time_clause=is_time_clause,
        tag_filter=tag_filter,
        untagged_only=untagged_only,
        subclause_types=subclause_types or None,
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
                "total": total_count,
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


@app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
