import spacy
from peewee import fn
from src.models import db, Sentence, SentenceIndex


class SearchEngine:
    def __init__(self, db_path="bible.db"):
        self.db = db
        self.nlp = None
        if self.db.is_closed():
            self.db.connect()

    def _get_nlp(self):
        if self.nlp is None:
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

    def search(
        self,
        query,
        limit=10,
        offset=0,
        use_lemma=False,
        sort=None,
        is_command=None,
        is_hypothetical=None,
    ):
        """
        Performs a full-text search on sentences using BM25 ranking.
        """
        search_query = query
        if use_lemma:
            nlp = self._get_nlp()
            doc = nlp(query)
            search_query = " ".join([token.lemma_ for token in doc])
            search_query = f"lemma_text: {search_query}"
        else:
            # Simple text match; might want to match English and maybe Syllabary?
            # For now let's assume query is English or just matches text fields
            # FTS5 default matches all columns if column not specified.
            # But let's be specific if we want.
            # actually "text: query" isn't valid for SentenceIndex unless we have a 'text' column.
            # SentenceIndex has: english, lemma_text, syllabary.
            # If we want to search all, we just pass the query string to match()
            pass

        # We construct the FTS5 query carefully.
        # If use_lemma, we already set "lemma_text: ...".
        # If not, let's just pass the query directly to FTS match, which searches all indexed columns.

        q = (
            Sentence.select(Sentence, SentenceIndex.rank().alias("score"))
            .join(SentenceIndex, on=(Sentence.id == SentenceIndex.rowid))
            .where(SentenceIndex.match(search_query))
        )

        # Apply filters
        if is_command is not None:
            q = q.where(Sentence.is_command == is_command)
        if is_hypothetical is not None:
            q = q.where(Sentence.is_hypothetical == is_hypothetical)

        # Sorting
        if sort == "length_asc":
            q = q.order_by(fn.length(Sentence.syllabary))
        elif sort == "length_desc":
            q = q.order_by(fn.length(Sentence.syllabary).desc())
        else:
            q = q.order_by(SentenceIndex.rank())

        results = q.limit(limit).offset(offset)
        return list(results)
