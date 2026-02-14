> [!NOTE]
> This phase document pertains to the original Bible search implementation. The project has since migrated to a general Cherokee Sentence Search corpus. See [migration_plan.md](../migration_plan.md) for details.
# Phase 2: Core Search Logic Implementation

## Goal
Develop the core Python logic to search the database efficiently, handling keyword searches, exact phrase matching, and reference lookups (e.g., "John 3:16").

## Tasks
1.  **Database Access Layer**
    - [ ] Create a `BibleSearch` class or module to handle database connections.
    - [ ] Implement a method to retrieve a specific verse by reference (Book, Chapter, Verse).

2.  **Full-Text Search (FTS) Integration**
    - [ ] Enable FTS5 on the `verses` table (or a separate virtual table).
    - [ ] Implement a search method that accepts a query string and returns matching verses.
    - [ ] Support ranking/scoring by relevance (BM25 is standard in FTS5).

3.  **Reference Parsing**
    - [ ] Implement a parser for Bible references (e.g., "Jn 3:16", "Genesis 1:1-5").
    - [ ] Handle common abbreviations for book names.

4.  **Unit Testing**
    - [ ] Write tests for:
        - Exact verse retrieval.
        - Keyword search (e.g., "light", "love").
        - Phrase search (e.g., "God so loved").
        - Edge cases (non-existent verses, malformed queries).

## Deliverables
- A robust Python module for querying the Bible database.
- A suite of passing unit tests covering search functionality.
