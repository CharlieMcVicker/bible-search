# Phase 1: Project Setup and Data Ingestion

## Goal
Establish the project structure, select a database, and ingest the Bible text (e.g., KJV) into a structured format suitable for querying.

## Tasks
1.  **Initialize Project**
    - [ ] Create a virtual environment (`python -m venv venv`).
    - [ ] Create `requirements.txt` with initial dependencies (`Flask`, `peewee` or `SQLAlchemy` or raw `sqlite3`).
    - [ ] Set up a basic project structure:
        ```
        bible-search/
        ├── data/           # Raw text files
        ├── src/            # Source code
        │   ├── models.py   # Database models
        │   └── ingest.py   # Ingestion script
        ├── tests/          # Unit tests
        └── app.py          # Main entry point
        ```

2.  **Acquire Bible Data**
    - [ ] Download a public domain Bible text (e.g., KJV) in JSON or XML format.
    - [ ] Verify the data integrity (66 books, 1189 chapters, ~31k verses).

3.  **Database Design**
    - [ ] Design a schema for `Books`, `Chapters`, and `Verses`.
    - [ ] Choose SQLite for simplicity and portability.
    - [ ] Plan for Full-Text Search (FTS5) capabilities in SQLite for efficient querying.

4.  **Ingestion Script**
    - [ ] Write a script (`src/ingest.py`) to parse the source file.
    - [ ] Insert data into the SQLite database.
    - [ ] Ensure proper indexing on `book_id`, `chapter`, and `verse`.

## Deliverables
- A populated `bible.db` SQLite database.
- A repeatable ingestion script.
