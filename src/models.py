from peewee import *
from playhouse.sqlite_ext import FTS5Model, SearchField, RowIDField

# Proxy for late initialization
db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


class Book(BaseModel):
    name = CharField(unique=True)


class Chapter(BaseModel):
    book = ForeignKeyField(Book, backref="chapters")
    number = IntegerField()

    class Meta:
        # Ensuring (book, number) is unique
        indexes = ((("book", "number"), True),)


class Verse(BaseModel):
    chapter = ForeignKeyField(Chapter, backref="verses")
    number = IntegerField()
    text = TextField()  # Using KJV as primary for now
    text_chr = TextField(null=True)  # Cherokee translation
    lemma_text = TextField(null=True)  # Lemmatized version of text
    is_command = BooleanField(default=False)
    is_hypothetical = BooleanField(default=False)

    class Meta:
        # Ensuring (chapter, number) is unique
        indexes = ((("chapter", "number"), True),)


# Full Text Search Index
class VerseIndex(FTS5Model):
    rowid = RowIDField()
    text = SearchField()
    lemma_text = SearchField()

    class Meta:
        database = db
        # Using the content option to point to the Verse table
        # This keeps the index small and synchronized
        options = {"content": Verse}


class Entity(BaseModel):
    name = CharField()
    label = CharField()  # PERSON, GPE, etc.

    class Meta:
        indexes = ((("name", "label"), True),)  # Unique constraint on name+label


class VerseEntity(BaseModel):
    verse = ForeignKeyField(Verse, backref="entities")
    entity = ForeignKeyField(Entity, backref="verses")

    class Meta:
        indexes = ((("verse", "entity"), True),)


class VerbStat(BaseModel):
    form = CharField(unique=True)
    subclause_count = IntegerField(default=0)
    matrix_count = IntegerField(default=0)
    total_count = IntegerField(default=0)


class Sentence(BaseModel):
    ref_id = CharField(unique=True)
    english = TextField()
    syllabary = TextField()
    phonetic = TextField()
    audio = CharField(null=True)
    lemma_text = TextField(null=True)
    is_command = BooleanField(default=False)
    is_hypothetical = BooleanField(default=False)
    subclause_types = CharField(
        null=True
    )  # Comma-separated list of subclause types (dep labels)


class SentenceTag(BaseModel):
    ref_id = CharField()
    word_index = IntegerField()
    tag = CharField()

    class Meta:
        # One tag per word per sentence specific tag type?
        # User said "tag a word". A word could technically have multiple tags,
        # but usually UI allows one selection.
        # "select a word and tag it" -> suggests one tag per word.
        # Let's verify requirement "2a. the tags for now should be 'converb,' 'yi+converb,' and 'incompletive deverbal'"
        # A word likely won't be both "converb" and "incompletive deverbal".
        # Let's enforce unique (ref_id, word_index, tag) just in case, or (ref_id, word_index) to limit to 1.
        # Let's assume one tag per word for now to keep UI simple, but unique on triplet allows multiple.
        # Wait, if I want to "tag it", usually that implies assigning A tag.
        # Let's stick to unique constraint on (ref_id, word_index) effectively making it one tag slot.
        # Actually user might want to change the tag.
        # Let's make it unique on (ref_id, word_index).
        indexes = ((("ref_id", "word_index"), True),)


class SentenceIndex(FTS5Model):
    rowid = RowIDField()
    english = SearchField()
    lemma_text = SearchField()
    syllabary = SearchField()

    class Meta:
        database = db
        options = {"content": Sentence}


def init_db(db_path="bible.db"):
    database = SqliteDatabase(db_path)
    db.initialize(database)
    db.connect()
    db.create_tables(
        [
            Book,
            Chapter,
            Verse,
            VerseIndex,
            Entity,
            VerseEntity,
            VerbStat,
            Sentence,
            SentenceIndex,
            SentenceTag,
        ]
    )
    db.close()


if __name__ == "__main__":
    init_db()
