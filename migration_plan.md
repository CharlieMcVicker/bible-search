# Migration Plan: Bible to Sentences Corpus

## Goal

Switch the primary data source from the KJV Bible to `sentences.json`, while maintaining the ability to ingest the Bible for legacy purposes. The frontend will be updated to reflect this change, removing "Bible" specific terminology.

## User Review Required

> [!IMPORTANT]
>
> - The application will primarily search `sentences.json`. Bible search will be effectively disabled in the UI unless explicitly requested to be kept as an option.
> - "Books of the Bible" browsing will be removed from the home page.
> - Existing Bible data will be preserved in the database if already ingested, but new specific tables for Sentences will be used for the main application.

## Proposed Changes

### Data & Models

#### [NEW] [src/models.py](file:///Users/charlesmcvicker/code/bible-search/src/models.py)

- Refactor to add `Sentence` model.
- Add `SentenceIndex` for FTS5 search on `Sentence` entries.
- Fields: `ref_id` (from JSON id), `english`, `syllabary`, `phonetic`, `audio`, `lemma_text`.

### Ingestion

#### [MOVE] `sentences.json` -> `data/sentences.json`

#### [NEW] [src/ingest_sentences.py](file:///Users/charlesmcvicker/code/bible-search/src/ingest_sentences.py)

- Script to load `data/sentences.json`.
- Uses `spaCy` for lemmatization of English text (similar to `ingest.py`).
- Populates `Sentence` table.

### Search Engine

#### [MODIFY] [src/search.py](file:///Users/charlesmcvicker/code/bible-search/src/search.py)

- Rename `BibleSearch` to `SearchEngine`.
- Update `search()` method to query `SentenceIndex` and return `Sentence` objects.
- Remove or disable `parse_and_search` reference logic if not applicable to `sentences.json` IDs (or adapt if IDs like "8.1-s1" have semantics we can use later).

### Backend Application

#### [MODIFY] [src/app.py](file:///Users/charlesmcvicker/code/bible-search/src/app.py)

- Update code to use `SearchEngine` targeting `Sentence` model.
- Remove routes specific to Bible browsing (e.g., `read_chapter`) if they don't apply, or adapt them to browse Sentences.

### Frontend

#### [MODIFY] [src/templates/base.html](file:///Users/charlesmcvicker/code/bible-search/src/templates/base.html)

- Change title "Bible Search" to "Cherokee Search" (or generic).
- Update footer.

#### [MODIFY] [src/templates/index.html](file:///Users/charlesmcvicker/code/bible-search/src/templates/index.html)

- Remove "Books of the Bible" grid.
- Update hero text.

#### [MODIFY] [src/templates/results.html](file:///Users/charlesmcvicker/code/bible-search/src/templates/results.html)

- Update result card to display `english`, `syllabary`, `phonetic`.
- Remove "Command/Hypothetical" badges unless we compute them for Sentences too (we check `ingest.py` logic, we can probably keep the logic if useful, but `sentences.json` might not map 1:1).

## Verification Plan

### Automated Tests

- Run `python3 src/ingest_sentences.py` to verify ingestion.
- Run `pytest` if there are existing tests (check `tests/`).
- Create a simple script `verify_search.py` to query the new `Sentence` model.

### Manual Verification

- Start app: `python3 -m src.app`.
- Visit `http://localhost:4000`.
- Verify Home page has no Bible references.
- Perform a search (e.g., "playing ball").
- Verify results show English, Syllabary, and Phonetic.
