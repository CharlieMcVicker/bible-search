import os

import pytest
from peewee import SqliteDatabase

from src.models import Sentence, SentenceIndex, SentenceTag, db
from src.search import SearchEngine


@pytest.fixture
def test_db_session():
    db_path = "test_sentences.db"
    test_db = SqliteDatabase(db_path)
    db.initialize(test_db)
    db.connect()
    db.create_tables([Sentence, SentenceIndex, SentenceTag])

    # Populate with sample data
    Sentence.create(
        ref_id="1",
        english="If it rains, stay inside.",
        syllabary="...",
        phonetic="...",
        is_hypothetical=True,
        is_command=False,
        lemma_text="if it rain , stay inside .",
    )
    Sentence.create(
        ref_id="2",
        english="Put the book on the table.",
        syllabary="...",
        phonetic="...",
        is_hypothetical=False,
        is_command=True,
        lemma_text="put the book on the table .",
    )
    Sentence.create(
        ref_id="3",
        english="The cat is sleeping.",
        syllabary="...",
        phonetic="...",
        is_hypothetical=False,
        is_command=False,
        lemma_text="the cat be sleep .",
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


def test_basic_search(searcher):
    results, _ = searcher.search("cat")
    assert len(results) == 1
    assert results[0].ref_id == "3"


def test_hypothetical_filter(searcher):
    results, _ = searcher.search("inside", is_hypothetical=True)
    assert len(results) == 1
    assert results[0].ref_id == "1"

    results, _ = searcher.search("inside", is_hypothetical=False)
    assert len(results) == 0


def test_command_filter(searcher):
    results, _ = searcher.search("book", is_command=True)
    assert len(results) == 1
    assert results[0].ref_id == "2"


def test_lemma_search(searcher):
    # "rains" matches "rain" in lemma
    results, _ = searcher.search("rain", use_lemma=True)
    assert len(results) == 1
    assert "rains" in results[0].english
