import pytest
import os
import spacy
from peewee import SqliteDatabase
from src.models import db, Sentence, SentenceIndex, SentenceTag
from src.search import SearchEngine


@pytest.fixture
def test_db_session():
    db_path = "test_subclauses.db"
    test_db = SqliteDatabase(db_path)
    db.initialize(test_db)
    db.connect()
    db.create_tables([Sentence, SentenceIndex, SentenceTag])

    # Sample data with subclause types
    Sentence.create(
        ref_id="1",
        english="When he finished writing letters, he stretched.",
        syllabary="...",
        phonetic="...",
        subclause_types="advcl",
        is_hypothetical=False,
        is_command=False,
    )
    Sentence.create(
        ref_id="2",
        english="He said that he was tired.",
        syllabary="...",
        phonetic="...",
        subclause_types="ccomp",
        is_hypothetical=False,
        is_command=False,
    )
    Sentence.create(
        ref_id="3",
        english="The boy who is playing ball is my friend.",
        syllabary="...",
        phonetic="...",
        subclause_types="relcl",
        is_hypothetical=False,
        is_command=False,
    )
    Sentence.create(
        ref_id="4",
        english="I see a cat.",
        syllabary="...",
        phonetic="...",
        subclause_types=None,  # No subclause
        is_hypothetical=False,
        is_command=False,
    )
    Sentence.create(
        ref_id="5",
        english="I want to go when it stops raining.",
        syllabary="...",
        phonetic="...",
        subclause_types="advcl,xcomp",  # Multiple
        is_hypothetical=False,
        is_command=False,
    )

    SentenceIndex.rebuild()

    yield db_path

    if not test_db.is_closed():
        db.drop_tables([Sentence, SentenceIndex, SentenceTag])
        db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def searcher(test_db_session):
    return SearchEngine(test_db_session)


def test_subclause_filter_single(searcher):
    # Search for adverbial clauses
    results, _ = searcher.search("stretched", subclause_types=["advcl"])
    assert len(results) == 1
    assert results[0].ref_id == "1"


def test_subclause_filter_multiple(searcher):
    # Search for sentences with either relcl or ccomp
    results, _ = searcher.search("he", subclause_types=["relcl", "ccomp"])
    # "He said that..." (ccomp) - matches "he"
    # "The boy who is playing ball is my friend." (relcl) - no "he"
    # Wait, "The boy..." doesn't match "he".
    # Let's search for something that might be in both or just verify count.

    # Just check that it returns the right nodes
    results, _ = searcher.search("", subclause_types=["relcl", "ccomp"])
    assert len(results) == 2
    ids = {r.ref_id for r in results}
    assert "2" in ids
    assert "3" in ids


def test_subclause_filter_any(searcher):
    results, _ = searcher.search("", subclause_types=["any"])
    assert len(results) == 4  # 1, 2, 3, 5
    assert "4" not in {r.ref_id for r in results}


def test_subclause_filter_none(searcher):
    results, _ = searcher.search("", subclause_types=["none"])
    assert len(results) == 1
    assert results[0].ref_id == "4"


def test_subclause_filter_complex(searcher):
    # Multiple types including 'any' (though redundant)
    results, _ = searcher.search("", subclause_types=["advcl", "relcl"])
    assert len(results) == 3  # 1, 3, 5
    ids = {r.ref_id for r in results}
    assert "1" in ids
    assert "3" in ids
    assert "5" in ids
