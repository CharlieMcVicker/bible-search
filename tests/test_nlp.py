import unittest
from src.nlp import extract_bible_references


class TestBibleReferenceExtraction(unittest.TestCase):
    def test_book_chapter_verse(self):
        text = "John 3:16"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["book"], "John")
        self.assertEqual(refs[0]["chapter"], 3)
        self.assertEqual(refs[0]["verse_start"], 16)
        self.assertEqual(refs[0]["verse_end"], 16)

    def test_book_chapter(self):
        text = "Genesis 1"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["book"], "Genesis")
        self.assertEqual(refs[0]["chapter"], 1)
        self.assertIsNone(refs[0]["verse_start"])
        self.assertIsNone(refs[0]["verse_end"])

    def test_verse_range(self):
        text = "Genesis 1:1-5"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["book"], "Genesis")
        self.assertEqual(refs[0]["chapter"], 1)
        self.assertEqual(refs[0]["verse_start"], 1)
        self.assertEqual(refs[0]["verse_end"], 5)

    def test_abbreviation(self):
        text = "Jn 3:16"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        # Note: The current extractor implementation returns the found token text as book name
        # It doesn't normalize it yet (except what I tried to add with ent_id, but need to verify)
        # My previous thought process about ent_id might not have been fully implemented in `extract_bible_references`
        # correctly because I only check if `token.ent_id_` exists.
        # Let's verify what `ent_id_` actually contains. In the loop `patterns.append({"label": ..., "id": book})`,
        # so `ent_id_` should be the full book name.
        self.assertEqual(refs[0]["book"], "John")
        self.assertEqual(refs[0]["chapter"], 3)
        self.assertEqual(refs[0]["verse_start"], 16)

    def test_multiple_references(self):
        text = "Read John 3:16 and 1 Peter 5:7 please."
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]["book"], "John")
        self.assertEqual(refs[0]["chapter"], 3)
        self.assertEqual(refs[0]["verse_start"], 16)
        self.assertEqual(refs[1]["book"], "1 Peter")
        self.assertEqual(refs[1]["chapter"], 5)
        self.assertEqual(refs[1]["verse_start"], 7)

    def test_numbered_book(self):
        text = "2 Timothy 2:15"
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["book"], "2 Timothy")
        self.assertEqual(refs[0]["chapter"], 2)
        self.assertEqual(refs[0]["verse_start"], 15)

    def test_no_reference(self):
        text = "There is no reference here."
        refs = extract_bible_references(text)
        self.assertEqual(len(refs), 0)


if __name__ == "__main__":
    unittest.main()
