import os
import time

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from peewee import SqliteDatabase

from src.models import Sentence, SentenceTag, TaggingGroup, db
from src.search import SearchEngine

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


@app.route("/api/tagging-groups", methods=["GET"])
def list_tagging_groups():
    groups = TaggingGroup.select().order_by(TaggingGroup.name)
    return jsonify(
        [
            {
                "id": g.id,
                "name": g.name,
                "tags": g.tags,
                "query": g.query.get("q", "") if isinstance(g.query, dict) else "",
                "filters": g.query,
            }
            for g in groups
        ]
    )


@app.route("/api/tagging-groups", methods=["POST"])
def save_tagging_group():
    data = request.json
    name = data.get("name")
    tags = data.get("tags", [])
    query = data.get("filters", {})

    if not name:
        abort(400, description="Missing name")

    # Use name as a unique identifier for simplicity or use ref_id if you want
    # For now, let's just use replace or update by name
    group, created = TaggingGroup.get_or_create(name=name, defaults={"ref_id": name})
    group.tags = tags
    group.query = query
    group.save()

    return jsonify({"status": "success", "id": group.id})


@app.route("/api/tagging-groups/<int:group_id>", methods=["DELETE"])
def delete_tagging_group(group_id):
    TaggingGroup.delete().where(TaggingGroup.id == group_id).execute()
    return jsonify({"status": "success"})


@app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
