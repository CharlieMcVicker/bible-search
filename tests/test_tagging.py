import pytest
import os
import json
from peewee import SqliteDatabase
from src.models import db, Sentence, SentenceIndex, SentenceTag
from src.search import SearchEngine
from src.app import app


@pytest.fixture
def test_db():
    db_path = "test_tagging.db"
    test_db = SqliteDatabase(db_path)
    db.initialize(test_db)
    db.connect()
    db.create_tables([Sentence, SentenceIndex, SentenceTag])

    # Sample data
    Sentence.create(
        ref_id="time1",
        english="I will go when he comes.",
        syllabary="...",
        phonetic="...",
        subclause_types="advcl",
    )
    Sentence.create(
        ref_id="time2",
        english="He ate after he arrived.",
        syllabary="...",
        phonetic="...",
        subclause_types="advcl",
    )
    Sentence.create(
        ref_id="nontime1",
        english="Because it rained, we stayed.",
        syllabary="...",
        phonetic="...",
        subclause_types="advcl",
    )
    Sentence.create(
        ref_id="plain1",
        english="This is a plain sentence.",
        syllabary="syllabary words",
        phonetic="...",
        subclause_types=None,
    )

    SentenceIndex.rebuild()

    yield db_path

    if not test_db.is_closed():
        db.drop_tables([Sentence, SentenceIndex, SentenceTag])
        db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def searcher(test_db):
    return SearchEngine(test_db)


@pytest.fixture
def client(test_db):
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_time_clause_filter(searcher):
    # Should find 'when' and 'after' sentences, but not 'because'
    results = searcher.search("", is_time_clause=True)
    ids = {r.ref_id for r in results}
    assert "time1" in ids
    assert "time2" in ids
    assert "nontime1" not in ids
    assert "plain1" not in ids


def test_tag_and_filter(searcher, client):
    ref_id = "plain1"
    # Tag the first word (index 0)
    res = client.post(
        f"/api/sentences/{ref_id}/tags", json={"word_index": 0, "tag": "converb"}
    )
    assert res.status_code == 200

    # Verify in DB
    tag = SentenceTag.get_or_none(ref_id=ref_id, word_index=0)
    assert tag is not None
    assert tag.tag == "converb"

    # Search by tag
    results = searcher.search("", tag_filter="converb")
    assert len(results) == 1
    assert results[0].ref_id == ref_id

    # Check if tags are attached to the result
    assert hasattr(results[0], "tags")
    assert len(results[0].tags) == 1
    assert results[0].tags[0]["tag"] == "converb"
    assert results[0].tags[0]["word_index"] == 0


def test_api_remove_tag(client):
    ref_id = "plain1"
    # Setup: Add a tag
    client.post(
        f"/api/sentences/{ref_id}/tags", json={"word_index": 1, "tag": "yi+converb"}
    )

    # Delete tag
    res = client.delete(f"/api/sentences/{ref_id}/tags", json={"word_index": 1})
    assert res.status_code == 200

    # Verify removed
    tag = SentenceTag.get_or_none(ref_id=ref_id, word_index=1)
    assert tag is None


def test_api_search_with_filters(client):
    # Test API response format
    res = client.get("/api/search?q=&is_time_clause=true")
    assert res.status_code == 200
    data = res.get_json()
    assert "data" in data
    assert len(data["data"]) >= 2

    # Ensure tags field is present in each item
    for item in data["data"]:
        assert "tags" in item
