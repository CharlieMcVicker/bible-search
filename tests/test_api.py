import unittest
import json
import os
from peewee import SqliteDatabase
from src.app import app
from src.models import db, Book, Chapter, Verse, VerseIndex, Entity, VerseEntity

class TestBibleAPI(unittest.TestCase):
    def setUp(self):
        # Use a temporary file DB for tests to persist across requests (since app closes connection)
        self.db_path = 'test_bible.db'
        self.test_db = SqliteDatabase(self.db_path)
        
        # Initialize the proxy with our test database
        db.initialize(self.test_db)
        
        db.connect()
        db.create_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
        
        self.populate_data()
        db.close() # Close so app can connect
        
        self.client = app.test_client()

    def tearDown(self):
        # Connect to drop tables
        if self.test_db.is_closed():
            self.test_db.connect()
        db.drop_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
        db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
    def populate_data(self):
        # Add John 3:16
        john = Book.create(name="John")
        ch3 = Chapter.create(book=john, number=3)
        Verse.create(chapter=ch3, number=16, text="For God so loved the world...")
        
        # Add Genesis 1
        gen = Book.create(name="Genesis")
        gen1 = Chapter.create(book=gen, number=1)
        Verse.create(chapter=gen1, number=1, text="In the beginning God created the heaven and the earth.")
        
        VerseIndex.rebuild()

    def test_get_books(self):
        response = self.client.get('/api/books')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        names = [b['name'] for b in data]
        self.assertIn("John", names)
        self.assertIn("Genesis", names)

    def test_get_chapters(self):
        # Get ID for John
        john_id = Book.get(Book.name == "John").id
        
        response = self.client.get(f'/api/books/{john_id}/chapters')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['number'], 3)
        
    def test_get_chapters_not_found(self):
        response = self.client.get('/api/books/999/chapters')
        self.assertEqual(response.status_code, 404)

    def test_get_passage(self):
        response = self.client.get('/api/passage?ref=John+3:16')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['text'], "For God so loved the world...")

    def test_get_passage_not_found(self):
        response = self.client.get('/api/passage?ref=John+99:99')
        self.assertEqual(response.status_code, 404)

    def test_search(self):
        response = self.client.get('/api/search?q=loved')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 1)
        self.assertIn("John", data['data'][0]['book'])

    def test_search_pagination(self):
        # Add more data to test pagination if needed, but we have 2 verses total.
        # "God" appears in both.
        response = self.client.get('/api/search?q=God&limit=1&offset=0')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 1)
        
        response = self.client.get('/api/search?q=God&limit=1&offset=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 1)

if __name__ == "__main__":
    unittest.main()
