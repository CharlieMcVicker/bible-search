> [!NOTE]
> This phase document pertains to the original Bible search implementation. The project has since migrated to a general Cherokee Sentence Search corpus. See [migration_plan.md](../migration_plan.md) for details.
# Phase 6: Grammatical Construction Search

## Goal
Enable searching for specific grammatical constructions: Commands (Imperatives) and Hypotheticals (Conditionals/Subjunctive).

## Tasks
1. **Database Schema Updates**
    - [ ] Add `is_command` (Boolean) and `is_hypothetical` (Boolean) fields to the `Verse` model.

2. **Ingestion Pipeline Upgrade**
    - [ ] Enhance `ingest.py` with linguistic rules to detect:
        - **Commands**: Identifying imperative mood or subject-less verb phrases.
        - **Hypotheticals**: Identifying conditional keywords ("if", "unless") and subjunctive structures.

3. **Search Logic Enhancements**
    - [ ] Update `BibleSearch.search` to support filtering by these new boolean flags.
    - [ ] Update API and frontend routes to handle `construction` parameter.

4. **Frontend Integration**
    - [ ] Add a "Construction" dropdown (All, Commands, Hypotheticals) to the search form.
    - [ ] Highlight the construction type in search results.

## Deliverables
- Re-ingested database with grammatical metadata.
- Advanced search options for grammatical mood.
