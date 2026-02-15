# Cherokee Sentence Search

A tool for searching and browsing Cherokee sentences with English translations, phonetic transcriptions, and audio support. Originally based on a Bible search project, it has been migrated to use a broader corpus of Cherokee sentences.

## Features

- **Full-Text Search**: Fast search across Syllabary, English, and Lemmatized text using SQLite FTS5.
- **Search Filters**: Filter results by grammatical mood (Imperative, Hypothetical).
- **Audio Support**: Integrated audio playback for sentences where available.
- **Natural Language Processing**: Lemmatization support for more flexible English searching.
- **API**: RESTful API for searching the sentence corpus.

## Getting Started

### Prerequisites

- **Python 3.8+**
- **spaCy** (with `en_core_web_sm` model)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd bible-search
    ```

2.  **Set up Python Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

### Database Setup

Before running the application, you need to ingest the sentence data into the SQLite database.

1.  **Ingest Sentences:**
    This script reads `data/sentences.json` and populates `bible.db`.
    ```bash
    python3 -m src.ingest_sentences
    ```

### Running the Application

1.  **Start the Server:**

    ```bash
    python3 -m src.app
    ```

2.  **Access the App:**
    Open your browser and navigate to `http://localhost:4000`.

### Running Tests

To verify the installation and code integrity:

```bash
pytest
```

---

## Project Structure

- **`src/`**: Backend Python application code.
  - `app.py`: Flask application entry point.
  - `models.py`: Database models (Peewee).
  - `search.py`: Search engine logic.
  - `ingest_sentences.py`: Sentence corpus ingestion script.
- **`frontend/`**: React application (Typescript/React/Vite).
  - `src/`: React components and logic.
  - `dist/`: Built frontend files (served by Flask).
- **`data/`**: Sentence corpus data storage (`sentences.json`).
- **`tests/`**: Unit and integration tests.
- **`scraper/`**: (Legacy) node.js scripts.
