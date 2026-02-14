import unittest
import os
from peewee import SqliteDatabase
from src.models import Book, Chapter, Verse, VerseIndex, db
from src.search import BibleSearch


class TestBibleSearch(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        self.test_db = SqliteDatabase(":memory:")

        # Initialize the proxy
        db.initialize(self.test_db)

        db.connect()
        db.create_tables([Book, Chapter, Verse, VerseIndex])

        # Populate with some sample data
        self.populate_data()

        # Initialize BibleSearch
        self.searcher = BibleSearch()

    def tearDown(self):
        self.test_db.drop_tables([Book, Chapter, Verse, VerseIndex])
        self.test_db.close()

    def populate_data(self):
        # Add John 3:16
        john = Book.create(name="John")
        ch3 = Chapter.create(book=john, number=3)
        Verse.create(
            chapter=ch3,
            number=16,
            text="For God so loved the world, that he gave his only begotten Son...",
        )
        Verse.create(
            chapter=ch3,
            number=17,
            text="For God sent not his Son into the world to condemn the world...",
        )

        # Add Genesis 1:1-3
        gen = Book.create(name="Genesis")
        gen1 = Chapter.create(book=gen, number=1)
        Verse.create(
            chapter=gen1,
            number=1,
            text="In the beginning God created the heaven and the earth.",
        )
        Verse.create(
            chapter=gen1, number=2, text="And the earth was without form, and void..."
        )
        Verse.create(
            chapter=gen1,
            number=3,
            text="And God said, Let there be light: and there was light.",
        )

        # Add 1 Peter 5:7
        pet = Book.create(name="1 Peter")
        pet5 = Chapter.create(book=pet, number=5)
        Verse.create(
            chapter=pet5,
            number=7,
            text="Casting all your care upon him; for he careth for you.",
        )

        # Rebuild index
        VerseIndex.rebuild()

    def test_get_verse(self):
        verse = self.searcher.get_verse("John", 3, 16)
        self.assertIsNotNone(verse)
        self.assertIn("loved the world", verse.text)

        # Test non-existent
        verse = self.searcher.get_verse("John", 99, 99)
        self.assertIsNone(verse)

    def test_search_keywords(self):
        results = self.searcher.search("loved")
        self.assertTrue(len(results) > 0)
        self.assertIn("John", results[0].chapter.book.name)

        results = self.searcher.search("beginning")
        self.assertTrue(len(results) > 0)
        self.assertIn("Genesis", results[0].chapter.book.name)

    def test_search_phrase(self):
        # FTS5 phrase search usually requires quotes
        results = self.searcher.search('"God so loved"')
        self.assertTrue(len(results) > 0)
        self.assertIn("John", results[0].chapter.book.name)

    def test_parse_and_search_reference_single(self):
        results = self.searcher.parse_and_search("John 3:16")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].number, 16)
        self.assertEqual(results[0].chapter.book.name, "John")

    def test_parse_and_search_reference_range(self):
        results = self.searcher.parse_and_search("Genesis 1:1-2")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].number, 1)
        self.assertEqual(results[1].number, 2)

    def test_parse_and_search_reference_chapter(self):
        results = self.searcher.parse_and_search("Genesis 1")
        # Should return all verses in chapter 1 (we added 3)
        self.assertEqual(len(results), 3)

    def test_parse_and_search_fallback(self):
        results = self.searcher.parse_and_search("God created")
        self.assertTrue(len(results) > 0)
        self.assertIn("Genesis", results[0].chapter.book.name)

    def test_abbreviation_search(self):
        results = self.searcher.parse_and_search("Jn 3:16")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chapter.book.name, "John")


if __name__ == "__main__":
    unittest.main()
