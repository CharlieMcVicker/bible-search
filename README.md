# Bible Search & Scraper

A comprehensive tool for searching and reading the Bible. This project includes a Node.js scraper for data acquisition and a Python/Flask web application for browsing and full-text search.

## Features

- **Full-Text Search**: Fast search capability using SQLite FTS5.
- **Smart Reference Parsing**: Supports queries like "John 3:16", "Gen 1:1-5", and abbreviations.
- **Reading Mode**: Distraction-free chapter reading with navigation.
- **API**: RESTful API for developers.

## Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js** (Only required if you want to run the scraper manually)

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

Before running the application, you need to ingest the data into the SQLite database.

1.  **Ingest Data:**
    This script reads the JSON data from the `data/` directory and populates `bible.db`.
    ```bash
    python -m src.ingest
    ```

### Running the Application

1.  **Start the Server:**
    ```bash
    python -m src.app
    ```

2.  **Access the App:**
    Open your browser and navigate to `http://127.0.0.1:5000`.

### Running Tests

To verify the installation and code integrity:

```bash
pytest
```

---

## Data Acquisition (Optional)

If you need to re-scrape the raw JSON data:

1.  **Install Node dependencies:**
    ```bash
    npm install
    ```

2.  **Run the Scraper:**
    ```bash
    npm run scrape
    ```

## Project Structure

- **`src/`**: Python application source code.
  - `app.py`: Flask application entry point.
  - `models.py`: Database models (Peewee).
  - `search.py`: Search logic and reference parsing.
  - `ingest.py`: Data ingestion script.
  - `nlp.py`: Natural Language Processing utilties.
  - `templates/`: HTML templates.
  - `static/`: CSS and JavaScript files.
- **`scraper/`**: Node.js scripts for scraping Bible texts.
- **`data/`**: JSON data storage (Book -> Chapter).
- **`tests/`**: Unit and integration tests.
