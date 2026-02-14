import unittest
import os
from peewee import SqliteDatabase
from src.models import db, Sentence, SentenceIndex
from src.search import SearchEngine


class TestSentenceSearch(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_sentences.db"
        self.test_db = SqliteDatabase(self.db_path)
        db.initialize(self.test_db)
        db.connect()
        db.create_tables([Sentence, SentenceIndex])

        # Populate with sample data
        self.populate_data()

        # We don't close here because SearchEngine might need it,
        # but SearchEngine initializes its own connection if closed.
        self.searcher = SearchEngine(self.db_path)

    def tearDown(self):
        if not self.test_db.is_closed():
            db.drop_tables([Sentence, SentenceIndex])
            db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def populate_data(self):
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

    def test_basic_search(self):
        results = self.searcher.search("cat")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ref_id, "3")

    def test_hypothetical_filter(self):
        results = self.searcher.search("inside", is_hypothetical=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ref_id, "1")

        results = self.searcher.search("inside", is_hypothetical=False)
        self.assertEqual(len(results), 0)

    def test_command_filter(self):
        results = self.searcher.search("book", is_command=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ref_id, "2")

    def test_lemma_search(self):
        # "rains" matches "rain" in lemma
        results = self.searcher.search("rain", use_lemma=True)
        self.assertEqual(len(results), 1)
        self.assertIn("rains", results[0].english)


if __name__ == "__main__":
    unittest.main()
