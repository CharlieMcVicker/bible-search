# Migration Plan: Bible to Sentences Corpus (Status: Core Migration Complete)

## Goal

Switch the primary data source from the KJV Bible to `sentences.json`, while maintaining the ability to ingest the Bible for legacy purposes. The frontend has been updated to reflect this change, removing "Bible" specific terminology and focusing on Cherokee sentence search.

## Completed Tasks

- [x] **Data Models**: Refactored `src/models.py` to include `Sentence` and `SentenceIndex` (FTS5).
- [x] **Ingestion Logic**: Developed `src/ingest_sentences.py` to populate the database from `data/sentences.json`.
- [x] **Search Engine**: Refactored `src/search.py` to target the `Sentence` model and implement BM25 ranking.
- [x] **Backend Update**: Updated `src/app.py` to use the new `SearchEngine` and updated routes for sentence search.
- [x] **Frontend Redesign**:
  - [x] Renamed site to "Cherokee Search".
  - [x] Removed Bible-specific navigation/grid.
  - [x] Updated search results to display Syllabary, Phonetic, English, and Audio.
  - [x] Added filters for "Imperative" (Command) and "Hypothetical".

## User Review Required

> [!IMPORTANT]
>
> - The application now primarily searches `sentences.json`. Bible search is disabled in the UI.
> - "Books of the Bible" browsing has been removed from the home page.
> - Existing Bible data is preserved in the database if already ingested, but new tables are used for the main application.

## Detailed Implementation Notes

### Data & Models

- `Sentence` model fields: `ref_id`, `english`, `syllabary`, `phonetic`, `audio`, `lemma_text`, `is_command`, `is_hypothetical`.
- `SentenceIndex` provides FTS5 search across `english`, `lemma_text`, and `syllabary`.

### Ingestion

- `data/sentences.json` is the source of truth.
- `src/ingest_sentences.py` handles loading and lemmatization using `spaCy`.

### Search Engine

- `SearchEngine` class now handles all sentence search logic.
- Supports sorting by relevance (rank) and syllabary length.
- Optional lemma-based search.

## Remaining / Follow-up Tasks

- [ ] Update documentation (`README.md`) to reflect the new primary purpose.
- [ ] Verify audio file paths and availability in `src/static/audio/`.
- [ ] Final verification of "Imperative" and "Hypothetical" tagging logic in `ingest_sentences.py`.

## Verification Results

- [x] `python3 src/ingest_sentences.py` verified.
- [x] `pytest` runs (after conversion to pytest).
- [x] Manual verification of search functionality on `localhost:4000`.
- [x] Verification of English, Phonetic, and Syllabary display.
