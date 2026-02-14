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
    book = ForeignKeyField(Book, backref='chapters')
    number = IntegerField()

    class Meta:
        # Ensuring (book, number) is unique
        indexes = (
            (('book', 'number'), True),
        )

class Verse(BaseModel):
    chapter = ForeignKeyField(Chapter, backref='verses')
    number = IntegerField()
    text = TextField() # Using KJV as primary for now
    lemma_text = TextField(null=True) # Lemmatized version of text
    
    class Meta:
        # Ensuring (chapter, number) is unique
        indexes = (
            (('chapter', 'number'), True),
        )

# Full Text Search Index
class VerseIndex(FTS5Model):
    rowid = RowIDField()
    text = SearchField()
    lemma_text = SearchField()

    class Meta:
        database = db
        # Using the content option to point to the Verse table
        # This keeps the index small and synchronized
        options = {'content': Verse}

class Entity(BaseModel):
    name = CharField()
    label = CharField() # PERSON, GPE, etc.
    
    class Meta:
        indexes = (
            (('name', 'label'), True), # Unique constraint on name+label
        )

class VerseEntity(BaseModel):
    verse = ForeignKeyField(Verse, backref='entities')
    entity = ForeignKeyField(Entity, backref='verses')
    
    class Meta:
        indexes = (
            (('verse', 'entity'), True),
        )

def init_db(db_path='bible.db'):
    database = SqliteDatabase(db_path)
    db.initialize(database)
    db.connect()
    db.create_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
    db.close()

if __name__ == "__main__":
    init_db()
