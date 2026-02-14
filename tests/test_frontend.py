import unittest
import os
from peewee import SqliteDatabase
from src.app import app
from src.models import db, Book, Chapter, Verse, VerseIndex

class TestBibleFrontend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_bible_frontend.db'
        self.test_db = SqliteDatabase(self.db_path)
        db.initialize(self.test_db)
        db.connect()
        db.create_tables([Book, Chapter, Verse, VerseIndex])
        self.populate_data()
        db.close()
        
        self.client = app.test_client()

    def tearDown(self):
        if self.test_db.is_closed():
            self.test_db.connect()
        db.drop_tables([Book, Chapter, Verse, VerseIndex])
        db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
    def populate_data(self):
        john = Book.create(name="John")
        ch3 = Chapter.create(book=john, number=3)
        Verse.create(chapter=ch3, number=16, text="For God so loved the world...")
        
        VerseIndex.rebuild()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bible Search", response.data)
        self.assertIn(b"John", response.data)

    def test_read_redirect(self):
        response = self.client.get('/read')
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"/read/Genesis/1", response.data)

    def test_read_chapter(self):
        response = self.client.get('/read/John/3')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"For God so loved the world", response.data)
        self.assertIn(b"John 3", response.data)

    def test_read_chapter_not_found(self):
        response = self.client.get('/read/John/99')
        self.assertEqual(response.status_code, 404)

    def test_search_redirect_reference(self):
        # Searching for a reference should redirect to read view
        response = self.client.get('/search?q=John+3:16')
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"/read/John/3", response.data)

    def test_search_text(self):
        response = self.client.get('/search?q=loved')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Results for", response.data)
        self.assertIn(b"For God so loved", response.data)

if __name__ == "__main__":
    unittest.main()
