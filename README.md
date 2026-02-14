# Bible Search & Scraper

This project is a tool for scraping Bible texts and providing a foundation for a search interface. It is built using Node.js.

## Project Structure

- **`scraper/`**: Contains the logic for scraping Bible texts.
  - `scrape_bible.js`: The main script to scrape data.
  - `test_scrape.js`: Tests for the scraping functionality.
- **`data/`**: Stores the scraped Bible text.
  - Organized by Book -> Chapter (JSON files).

## Getting Started

### Prerequisites

- Node.js installed on your machine.

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

### Usage

**Run the Scraper:**

To scrape the Bible data (if not already present or to update it):

```bash
npm run scrape
```

**Run Tests:**

To verify the scraping logic:

```bash
npm test
```

## Data Format

The data is stored in the `data/` directory. Each book of the Bible has its own folder, and within that folder, each chapter is a separate JSON file (e.g., `data/Genesis/1.json`).