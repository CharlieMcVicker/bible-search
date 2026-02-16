import json
import os

import pytest
from peewee import SqliteDatabase

from src.models import (
    Sentence,
    SentenceGroup,
    SentenceIndex,
    SentenceTag,
    TaggingGroup,
    db,
)
from src.search import SearchEngine


@pytest.fixture
def test_db():
    db_path = "test_groups.db"
    test_db = SqliteDatabase(db_path)
    db.initialize(test_db)
    db.connect()
    db.create_tables(
        [Sentence, SentenceIndex, SentenceTag, SentenceGroup, TaggingGroup]
    )

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
        ref_id="plain1",
        english="This is a plain sentence.",
        syllabary="syllabary words",
        phonetic="...",
        subclause_types=None,
    )

    SentenceIndex.rebuild()

    yield db_path

    if not test_db.is_closed():
        db.drop_tables(
            [Sentence, SentenceIndex, SentenceTag, SentenceGroup, TaggingGroup]
        )
        db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_sentence_group_creation(test_db):
    group_name = "Test Group"
    SentenceGroup.create(ref_id="time1", group_name=group_name)
    SentenceGroup.create(ref_id="time2", group_name=group_name)

    count = SentenceGroup.select().where(SentenceGroup.group_name == group_name).count()
    assert count == 2

    # Test uniqueness
    with pytest.raises(Exception):
        SentenceGroup.create(ref_id="time1", group_name=group_name)


def test_tagging_group_creation(test_db):
    ref_id = "test-run"
    name = "Test Group"
    tags = ["tag1", "tag2"]
    query = {"is_time_clause": True}

    TaggingGroup.create(ref_id=ref_id, name=name, tags=tags, query=query)

    tg = TaggingGroup.get(TaggingGroup.ref_id == ref_id)
    assert tg.name == name
    assert tg.tags == tags
    assert tg.query == query

    # Test uniqueness
    with pytest.raises(Exception):
        TaggingGroup.create(ref_id=ref_id, name="Another Name", tags=[], query={})


def test_retrieval_by_group(test_db):
    group_name = "Time clauses"
    SentenceGroup.create(ref_id="time1", group_name=group_name)
    SentenceGroup.create(ref_id="time2", group_name=group_name)
    SentenceGroup.create(ref_id="plain1", group_name="Other")

    results = (
        Sentence.select()
        .join(SentenceGroup, on=(Sentence.ref_id == SentenceGroup.ref_id))
        .where(SentenceGroup.group_name == group_name)
    )

    ids = {r.ref_id for r in results}
    assert "time1" in ids
    assert "time2" in ids
    assert "plain1" not in ids
    assert len(ids) == 2
