import os
import json
from src.models import db, Book, Chapter, Verse, VerseIndex

DATA_DIR = 'data'
FULL_DATA_FILE = os.path.join(DATA_DIR, 'kjv_full.json')

def ingest_data():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found.")
        return

    print("Connecting to database...")
    db.connect()
    
    # Drop and recreate tables to ensure clean state
    print("Dropping and recreating tables...")
    db.drop_tables([Book, Chapter, Verse, VerseIndex], safe=True)
    db.create_tables([Book, Chapter, Verse, VerseIndex])
    
    total_verses = 0
    
    # Check for full JSON file first
    if os.path.exists(FULL_DATA_FILE):
        print(f"Found full data file: {FULL_DATA_FILE}")
        with open(FULL_DATA_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        with db.atomic():
            for book_data in data:
                book_name = book_data['name']
                print(f"Processing {book_name}...")
                book = Book.create(name=book_name)
                
                chapters = book_data['chapters']
                for i, verses in enumerate(chapters):
                    chapter_num = i + 1
                    chapter = Chapter.create(book=book, number=chapter_num)
                    
                    for j, verse_text in enumerate(verses):
                        verse_num = j + 1
                        Verse.create(chapter=chapter, number=verse_num, text=verse_text)
                        total_verses += 1
    else:
        print("Full data file not found. Falling back to directory structure...")
        
        # Get all book directories
        book_dirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
        
        if not book_dirs:
            print("No book directories found.")
            return

        with db.atomic(): # Transaction for speed
            for book_name in sorted(book_dirs):
                print(f"Processing {book_name}...")
                book, created = Book.get_or_create(name=book_name)
                
                book_path = os.path.join(DATA_DIR, book_name)
                chapter_files = [f for f in os.listdir(book_path) if f.endswith('.json')]
                
                try:
                    chapter_files.sort(key=lambda x: int(os.path.splitext(x)[0]))
                except ValueError:
                    print(f"Warning: Non-numeric chapter file found in {book_name}")
                    continue

                for chap_file in chapter_files:
                    chap_num = int(os.path.splitext(chap_file)[0])
                    chapter, created = Chapter.get_or_create(book=book, number=chap_num)
                    
                    with open(os.path.join(book_path, chap_file), 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            print(f"Error reading {chap_file}")
                            continue
                            
                        for item in data:
                            verse_num = int(item['verse'])
                            text = item.get('kjv', '') # Default to KJV
                            
                            if not text:
                                text = item.get('web', '') # Fallback
                            
                            Verse.create(chapter=chapter, number=verse_num, text=text)
                            total_verses += 1

    # Rebuild the FTS index
    print("Rebuilding FTS index...")
    VerseIndex.rebuild()
    
    print(f"Ingestion complete! Added {total_verses} verses.")
    db.close()

if __name__ == "__main__":
    ingest_data()
