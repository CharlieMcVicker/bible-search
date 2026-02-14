import spacy
from peewee import fn
from src.models import db, Book, Chapter, Verse, VerseIndex, Entity, VerseEntity
from src.nlp import extract_bible_references


class BibleSearch:
    def __init__(self, db_path="bible.db"):
        self.db = db
        self.nlp = None
        # Ensure connection is open if not already (Peewee handles this well usually)
        if self.db.is_closed():
            self.db.connect()

    def _get_nlp(self):
        if self.nlp is None:
            # Load small model for lemmatization
            try:
                self.nlp = spacy.load(
                    "en_core_web_sm", disable=["parser", "textcat", "ner"]
                )
            except OSError:
                from spacy.cli import download

                download("en_core_web_sm")
                self.nlp = spacy.load(
                    "en_core_web_sm", disable=["parser", "textcat", "ner"]
                )
        return self.nlp

    def get_verse(self, book_name, chapter_num, verse_num):
        """
        Retrieves a specific verse.
        """
        try:
            return (
                Verse.select()
                .join(Chapter)
                .join(Book)
                .where(
                    (fn.Lower(Book.name) == book_name.lower())
                    & (Chapter.number == chapter_num)
                    & (Verse.number == verse_num)
                )
                .get()
            )
        except Verse.DoesNotExist:
            return None

    def search(
        self,
        query,
        limit=10,
        offset=0,
        use_lemma=False,
        entity_filter=None,
        construction_filter=None,
        sort=None,
    ):
        """
        Performs a full-text search on verses using BM25 ranking.

        :param use_lemma: If True, lemmatizes the query before searching.
        :param entity_filter: Optional string (Entity Name) to filter results.
        :param construction_filter: Optional string ('command' or 'hypothetical') to filter.
        :param sort: Sorting method ('length_asc', 'length_desc', or None for rank).
        """

        search_query = query
        if use_lemma:
            nlp = self._get_nlp()
            doc = nlp(query)
            # Join lemmas
            search_query = " ".join([token.lemma_ for token in doc])

            # If we are using lemmas, we should ideally target the lemma_text column
            # to avoid noise, OR we just trust that matching "love" against "loved" (in text)
            # might not happen but matching "love" in lemma_text will.
            # To be precise, let's target lemma_text column if use_lemma is set.
            # FTS5 syntax: column : query
            search_query = f"lemma_text: {search_query}"
        else:
            # Restrict to text column to avoid matching against lemma_text
            search_query = f"text: {search_query}"

        # Base query
        # We start with selecting Verse and Score
        q = (
            Verse.select(Verse, Chapter, Book, VerseIndex.rank().alias("score"))
            .join(VerseIndex, on=(Verse.id == VerseIndex.rowid))
            .join(Chapter, on=(Verse.chapter == Chapter.id))
            .join(Book, on=(Chapter.book == Book.id))
            .where(VerseIndex.match(search_query))
        )

        # Apply Entity Filter
        if entity_filter:
            q = (
                q.join(VerseEntity, on=(VerseEntity.verse == Verse.id))
                .join(Entity, on=(VerseEntity.entity == Entity.id))
                .where(Entity.name == entity_filter)
            )

        # Apply Construction Filter
        if construction_filter == "command":
            q = q.where(Verse.is_command == True)
        elif construction_filter == "hypothetical":
            q = q.where(Verse.is_hypothetical == True)

        # Apply Sorting
        if sort == "length_asc":
            q = q.order_by(fn.length(Verse.text))
        elif sort == "length_desc":
            q = q.order_by(fn.length(Verse.text).desc())
        else:
            # Default to relevance (BM25 rank)
            q = q.order_by(VerseIndex.rank())

        results = q.limit(limit).offset(offset)

        return list(results)

    def parse_and_search(self, query):
        """
        Parses the query to see if it's a reference, otherwise does a text search.
        """
        refs = extract_bible_references(query)
        if refs:
            # For now, just handle the first reference found
            ref = refs[0]
            book_name = ref["book"]
            chapter_num = ref["chapter"]
            v_start = ref["verse_start"]
            v_end = ref["verse_end"]

            if v_start is not None:
                if v_start == v_end:
                    # Single verse
                    verse = self.get_verse(book_name, chapter_num, v_start)
                    if verse:
                        return [verse]
                else:
                    # Verse range
                    return list(
                        Verse.select()
                        .join(Chapter)
                        .join(Book)
                        .where(
                            (fn.Lower(Book.name) == book_name.lower())
                            & (Chapter.number == chapter_num)
                            & (Verse.number >= v_start)
                            & (Verse.number <= v_end)
                        )
                        .order_by(Verse.number)
                    )
            else:
                # Whole chapter
                return list(
                    Verse.select()
                    .join(Chapter)
                    .join(Book)
                    .where(
                        (fn.Lower(Book.name) == book_name.lower())
                        & (Chapter.number == chapter_num)
                    )
                    .order_by(Verse.number)
                )

            # If we reached here, it means we had a reference but found no verses (e.g. invalid verse number)
            # We should probably return empty list instead of falling back to search,
            # as "John 99:99" causing a text search error (FTS column syntax) is bad.
            return []

        # If no reference or reference look up failed (or returned nothing), do text search
        return self.search(query)
