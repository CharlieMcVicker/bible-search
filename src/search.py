import spacy
from peewee import fn

from src.models import Sentence, SentenceIndex, SentenceTag, db


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
        subclause_types=None,
        is_time_clause=None,
        tag_filter=None,
        untagged_only=False,
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

        if search_query:
            q = (
                Sentence.select(Sentence, SentenceIndex.rank().alias("score"))
                .join(SentenceIndex, on=(Sentence.id == SentenceIndex.rowid))
                .where(SentenceIndex.match(search_query))
            )
        else:
            # If no query, just select all with a default score
            from peewee import Value

            q = Sentence.select(Sentence, Value(0).alias("score"))

        # Apply filters
        if is_command is not None:
            q = q.where(Sentence.is_command == is_command)
        if is_hypothetical is not None:
            q = q.where(Sentence.is_hypothetical == is_hypothetical)

        if untagged_only:
            # Subquery to find all ref_ids that ARE tagged
            tagged_ref_ids = SentenceTag.select(SentenceTag.ref_id)
            q = q.where(Sentence.ref_id.not_in(tagged_ref_ids))

        if subclause_types:
            if isinstance(subclause_types, str):
                subclause_types = [subclause_types]

            # Combine multiple subclause filters with OR
            clause_filters = []
            for stype in subclause_types:
                if stype == "any":
                    clause_filters.append(Sentence.subclause_types.is_null(False))
                elif stype == "none":
                    clause_filters.append(Sentence.subclause_types.is_null(True))
                else:
                    clause_filters.append(Sentence.subclause_types.contains(stype))

            if clause_filters:
                from peewee import operator, reduce

                q = q.where(reduce(operator.or_, clause_filters))

                q = q.where(reduce(operator.or_, clause_filters))

        if is_time_clause:
            # Must have advcl and contain time keywords
            # This is a heuristic.
            q = q.where(Sentence.subclause_types.contains("advcl"))
            time_keywords = [
                "when",
                "while",
                "after",
                "before",
                "until",
                "since",
                "as soon as",
            ]
            # Peewee OR for keywords
            from peewee import operator, reduce

            keyword_filters = [Sentence.english.contains(kw) for kw in time_keywords]
            q = q.where(reduce(operator.or_, keyword_filters))

        if tag_filter:
            q = (
                q.join(SentenceTag, on=(Sentence.ref_id == SentenceTag.ref_id))
                .where(SentenceTag.tag == tag_filter)
                .distinct()
            )
        elif untagged_only:
            subquery = SentenceTag.select(SentenceTag.ref_id)
            q = q.where(Sentence.ref_id.not_in(subquery))
        if sort == "length_asc":
            q = q.order_by(fn.length(Sentence.syllabary))
        elif sort == "length_desc":
            q = q.order_by(fn.length(Sentence.syllabary).desc())
        elif search_query:
            q = q.order_by(SentenceIndex.rank())
        else:
            q = q.order_by(Sentence.ref_id)

        total_count = q.count()
        results = list(q.limit(limit).offset(offset))

        # Attach tags to results
        if results:
            ref_ids = [r.ref_id for r in results]
            tags = SentenceTag.select().where(SentenceTag.ref_id.in_(ref_ids))

            # Map ref_id -> list of tags
            tag_map = {}
            for t in tags:
                if t.ref_id not in tag_map:
                    tag_map[t.ref_id] = []
                tag_map[t.ref_id].append({"word_index": t.word_index, "tag": t.tag})

            for r in results:
                r.tags = tag_map.get(r.ref_id, [])

        return results, total_count
