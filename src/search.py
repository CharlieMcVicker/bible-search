from peewee import fn
from src.models import db, Book, Chapter, Verse, VerseIndex
from src.nlp import extract_bible_references

class BibleSearch:
    def __init__(self, db_path='bible.db'):
        self.db = db
        # Ensure connection is open if not already (Peewee handles this well usually)
        if self.db.is_closed():
            self.db.connect()

    def get_verse(self, book_name, chapter_num, verse_num):
        """
        Retrieves a specific verse.
        """
        try:
            return (Verse
                    .select()
                    .join(Chapter)
                    .join(Book)
                    .where(
                        (fn.Lower(Book.name) == book_name.lower()) &
                        (Chapter.number == chapter_num) &
                        (Verse.number == verse_num)
                    )
                    .get())
        except Verse.DoesNotExist:
            return None

    def search(self, query, limit=10, offset=0):
        """
        Performs a full-text search on verses using BM25 ranking (default in FTS5).
        """
        # FTS5 match query
        # We can use the simple 'MATCH' operator.
        # Peewee's FTS5 support: VerseIndex.search(query) usually works if defined, 
        # but here we might need to use the match operator directly.
        
        # Using raw query or peewee's expression for flexibility
        # VerseIndex.match(query) is the standard way.
        
        results = (Verse
                   .select(Verse, VerseIndex.rank().alias('score'))
                   .join(VerseIndex, on=(Verse.id == VerseIndex.rowid))
                   .where(VerseIndex.match(query))
                   .order_by(VerseIndex.rank())
                   .limit(limit)
                   .offset(offset))
        
        return list(results)

    def parse_and_search(self, query):
        """
        Parses the query to see if it's a reference, otherwise does a text search.
        """
        refs = extract_bible_references(query)
        if refs:
            # For now, just handle the first reference found
            ref = refs[0]
            book_name = ref['book']
            chapter_num = ref['chapter']
            v_start = ref['verse_start']
            v_end = ref['verse_end']

            if v_start is not None:
                if v_start == v_end:
                    # Single verse
                    verse = self.get_verse(book_name, chapter_num, v_start)
                    if verse:
                        return [verse]
                else:
                    # Verse range
                    return list(Verse
                                .select()
                                .join(Chapter)
                                .join(Book)
                                .where(
                                    (fn.Lower(Book.name) == book_name.lower()) &
                                    (Chapter.number == chapter_num) &
                                    (Verse.number >= v_start) &
                                    (Verse.number <= v_end)
                                )
                                .order_by(Verse.number))
            else:
                # Whole chapter
                return list(Verse
                            .select()
                            .join(Chapter)
                            .join(Book)
                            .where(
                                (fn.Lower(Book.name) == book_name.lower()) &
                                (Chapter.number == chapter_num)
                            )
                            .order_by(Verse.number))
            
            # If we reached here, it means we had a reference but found no verses (e.g. invalid verse number)
            # We should probably return empty list instead of falling back to search, 
            # as "John 99:99" causing a text search error (FTS column syntax) is bad.
            return []
            
        # If no reference or reference look up failed (or returned nothing), do text search
        return self.search(query)
