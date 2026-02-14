import unittest
from src.nlp import extract_bible_references

class TestBibleReferenceExtraction(unittest.TestCase):
    def test_book_chapter_verse(self):
        text = "John 3:16"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['book'], "John")
        self.assertEqual(refs[0]['chapter'], 3)
        self.assertEqual(refs[0]['verse'], 16)

    def test_book_chapter(self):
        text = "Genesis 1"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['book'], "Genesis")
        self.assertEqual(refs[0]['chapter'], 1)
        self.assertIsNone(refs[0]['verse'])

    def test_multiple_references(self):
        text = "Read John 3:16 and 1 Peter 5:7 please."
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]['book'], "John")
        self.assertEqual(refs[0]['chapter'], 3)
        self.assertEqual(refs[0]['verse'], 16)
        self.assertEqual(refs[1]['book'], "1 Peter")
        self.assertEqual(refs[1]['chapter'], 5)
        self.assertEqual(refs[1]['verse'], 7)

    def test_numbered_book(self):
        text = "2 Timothy 2:15"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['book'], "2 Timothy")
        self.assertEqual(refs[0]['chapter'], 2)
        self.assertEqual(refs[0]['verse'], 15)

    def test_no_reference(self):
        text = "There is no reference here."
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 0)

if __name__ == "__main__":
    unittest.main()
