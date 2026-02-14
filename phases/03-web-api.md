# Phase 3: Web API Development

## Goal
Expose the core search functionality via a RESTful API using Flask.

## Tasks
1.  **API Setup**
    - [ ] Initialize a Flask app structure.
    - [ ] Configure the app to use the existing `bible.db`.

2.  **API Endpoints**
    - [ ] `GET /api/books`: List all books of the Bible.
    - [ ] `GET /api/books/<book_id>/chapters`: List chapters for a book.
    - [ ] `GET /api/passage`: Get text for a specific reference (e.g., `?ref=John+3:16`).
    - [ ] `GET /api/search`: Search verses by keyword/phrase (e.g., `?q=light`).
        - Support pagination (limit/offset).

3.  **Response Formatting**
    - [ ] Ensure all responses are JSON.
    - [ ] Include metadata in search results (total matches, execution time).

4.  **Error Handling**
    - [ ] Return 404 for non-existent references.
    - [ ] Return 400 for malformed queries.

## Deliverables
- A running Flask server with documented API endpoints.
- Integration tests for the API endpoints.
