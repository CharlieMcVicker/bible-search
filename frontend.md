# Frontend Workflows

## 1. Search (Home Page)

- **URL**: `/`
- **User Action**:
  - Enter query in text input.
  - Toggle initial filters:
    - Word Roots (`use_lemma`)
    - Hypothetical (`is_hypothetical`)
    - Imperative (`is_command`)
  - Click "Search" button.
- **System Action**: Submits GET request to `/search` with query parameters.

## 2. Search Results & Refinement

- **URL**: `/search?q=...`
- **Display**: Lists matching sentences with:
  - Syllabary (broken into words)
  - Phonetic
  - English
  - Subclause tags (badges)
  - Audio player (if available)
  - Lemma (if "Roots" search enabled)
- **Refinement (Top Bar)**:
  - Toggle Filters (auto-submit on change):
    - Roots
    - Hypothetical
    - Imperative
    - Time Clauses (`is_time_clause`)
  - Dropdowns:
    - **Tag**: Filter by specific tag (e.g., converb).
    - **Sort**: Relevance, Shortest, Longest.
    - **Subclauses**: Multiselect via dropdown checkboxes (e.g., Adverbial Clause, Relative Clause).
- **Pagination**: standard Next/Previous links.

## 3. Tagging Functionality

- **Location**: Results page (`/search`).
- **Activation**: Toggle "Enable Tagging" button.
- **Workflow**:
  1.  User clicks a Cherokee word (token) in the results while Tagging Mode is ON.
  2.  A **Tagging Drawer** appears from the bottom.
  3.  User selects a tag from the list: `converb`, `yi+converb`, `incompletive deverbal`, or `completive deverbal`.
  4.  Custom tags can also be entered.
  5.  **Save**: Sends POST to `/api/sentences/<ref_id>/tags` with `{word_index, tag}`.
  6.  **UI Update**: The tag appears directly below the word in the search results.
  7.  **Remove**: Clicking "Remove Tag" in the drawer sends DELETE to `/api/sentences/<ref_id>/tags`.

## 4. Reading Integration (Notes)

- **Status**: Appears to be legacy/disabled.
- **Files**: `read.html`, `main.js` (verse copying).
- **Observation**: No routes in `app.py` point to `read.html`. Current application logic is focused purely on Sentence Search.

## API Dependencies

The frontend relies on:

- **HTML Serving**: `/` (index), `/search` (results).
- **AJAX**:
  - `POST /api/sentences/<ref_id>/tags`: Add/Update tag.
  - `DELETE /api/sentences/<ref_id>/tags`: Remove tag.
  - `GET /search`: (HTML) Used for all search interactions.
  - `GET /api/search`: (JSON) Exists but seemingly unused by current frontend (used for raw data access?). **Note**: Currently lacks `subclause_types` support found in HTML route.
