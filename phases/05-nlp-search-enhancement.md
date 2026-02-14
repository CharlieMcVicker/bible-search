> [!NOTE]
> This phase document pertains to the original Bible search implementation. The project has since migrated to a general Cherokee Sentence Search corpus. See [migration_plan.md](../migration_plan.md) for details.
# Phase 5: NLP-Enhanced Search

## Goal
Integrate spaCy's linguistic capabilities to enable smarter searching, including lemmatized search (matching word roots) and entity-based filtering (People, Locations).

## Tasks
1.  **Database Schema Updates**
    - [ ] Add a `lemmatized_text` field to the `Verse` model (and FTS index).
    - [ ] Create an `Entity` model to store unique entities (e.g., "Moses", "Jerusalem").
    - [ ] Create a `VerseEntity` through-table to link verses to entities with their label (PERSON, GPE, etc.).

2.  **Ingestion Pipeline Upgrade**
    - [ ] Update `ingest.py` to process verse text through the spaCy pipeline.
    - [ ] Extract and store lemmatized text (e.g., "loved" -> "love").
    - [ ] Extract and index Named Entities.

3.  **Search Logic Enhancements**
    - [ ] Add a "Lemma Search" mode to `BibleSearch` (searches `lemmatized_text`).
    - [ ] Add an "Entity Filter" to `BibleSearch` (e.g., `entities=['Peter']`).
    - [ ] Update API endpoint `/api/search` to accept `use_lemma=true` and `entity` params.

4.  **Frontend Integration**
    - [ ] Add an "Advanced Search" toggle in the UI.
    - [ ] Add a checkbox for "Match Word Roots" (Lemmatization).
    - [ ] (Optional) Display detected entities in the reading view or search results.

## Deliverables
- A re-ingested database containing rich linguistic data.
- Enhanced search API supporting lemmatization and entity filtering.
- Updated Frontend UI with advanced search options.
