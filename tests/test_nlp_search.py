import unittest
import os
from peewee import SqliteDatabase
from src.models import db, Book, Chapter, Verse, VerseIndex, Entity, VerseEntity
from src.search import BibleSearch
import spacy

class TestBibleNLPSearch(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_bible_nlp.db'
        self.test_db = SqliteDatabase(self.db_path)
        db.initialize(self.test_db)
        db.connect()
        db.create_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
        
        # Populate data manually for control
        self.populate_data()
        db.close()
        
        self.searcher = BibleSearch(self.db_path)

    def tearDown(self):
        if self.test_db.is_closed():
            self.test_db.connect()
        db.drop_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
        db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def populate_data(self):
        # We need a small mock NLP here or just manual insertion
        # Manual insertion is safer for unit tests than relying on model download
        
        john = Book.create(name="John")
        ch3 = Chapter.create(book=john, number=3)
        
        # Verse 1: "For God so loved the world..."
        # Lemma: "for God so love the world"
        v16 = Verse.create(
            chapter=ch3, 
            number=16, 
            text="For God so loved the world...",
            lemma_text="for God so love the world"
        )
        
        # Entity: God (PERSON? In Bible often treated as such or unique)
        god = Entity.create(name="God", label="PERSON")
        VerseEntity.create(verse=v16, entity=god)
        
        # Verse 2: "Jesus wept."
        # Lemma: "Jesus weep ."
        v35 = Verse.create(
            chapter=ch3, 
            number=35, # actually John 11:35 but putting in ch3 for simplicity
            text="Jesus wept.",
            lemma_text="Jesus weep ."
        )
        
        jesus = Entity.create(name="Jesus", label="PERSON")
        VerseEntity.create(verse=v35, entity=jesus)
        
        VerseIndex.rebuild()

    def test_lemma_search(self):
        # Search for "love" should match "loved" if using lemma
        # First, standard search for "love" might fail if text is "loved" (unless stemmer is used by FTS5 default)
        # SQLite FTS5 default tokenizer is simple, usually just splits. 
        # Porter stemmer is optional. We are using standard.
        
        # Standard search "love" -> no match for "loved"
        results = self.searcher.search("love", use_lemma=False)
        # Actually "love" is not in "For God so loved..."
        self.assertEqual(len(results), 0)
        
        # Lemma search "love" -> should match because query "love" matches lemma_text "love"
        results = self.searcher.search("love", use_lemma=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].number, 16)
        
        # Search "weep" -> matches "wept"
        results = self.searcher.search("weep", use_lemma=True)
        self.assertEqual(len(results), 1)
        self.assertIn("Jesus wept", results[0].text)

    def test_entity_filter(self):
        # Filter for "Jesus"
        results = self.searcher.search("wept", entity_filter="Jesus")
        self.assertEqual(len(results), 1)
        
        # Filter for "God" on same query -> should be 0
        results = self.searcher.search("wept", entity_filter="God")
        self.assertEqual(len(results), 0)

if __name__ == "__main__":
    unittest.main()
