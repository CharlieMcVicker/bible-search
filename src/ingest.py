import os
import json
import spacy
from peewee import SqliteDatabase
from src.models import db, Book, Chapter, Verse, VerseIndex, Entity, VerseEntity

DATA_DIR = 'data'
FULL_DATA_FILE = os.path.join(DATA_DIR, 'kjv_full.json')

def ingest_data():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found.")
        return

    print("Loading spaCy model...")
    # Disable parser and textcat for speed, we need tagger (for lemma) and ner
    try:
        nlp = spacy.load("en_core_web_sm", disable=["parser", "textcat"])
    except OSError:
        print("Downloading spaCy model...")
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["parser", "textcat"])

    print("Connecting to database...")
    database = SqliteDatabase('bible.db')
    db.initialize(database)
    db.connect()
    
    # Drop and recreate tables to ensure clean state
    print("Dropping and recreating tables...")
    db.drop_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity], safe=True)
    db.create_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
    
    total_verses = 0
    entity_cache = {} # (name, label) -> entity_instance

    def process_verse(chapter, verse_num, text):
        doc = nlp(text)
        
        # Lemma text
        lemma_text = " ".join([token.lemma_ for token in doc])
        
        verse = Verse.create(
            chapter=chapter, 
            number=verse_num, 
            text=text,
            lemma_text=lemma_text
        )
        
        # Entities
        seen_entities = set()
        for ent in doc.ents:
            # Filter interested labels
            if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "NORP"]:
                key = (ent.text, ent.label_)
                
                # Check if we already linked this entity for this verse
                if key in seen_entities:
                    continue
                seen_entities.add(key)
                
                if key not in entity_cache:
                    entity, created = Entity.get_or_create(name=ent.text, label=ent.label_)
                    entity_cache[key] = entity
                
                VerseEntity.create(verse=verse, entity=entity_cache[key])
                
        return 1

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
                        total_verses += process_verse(chapter, j + 1, verse_text)
                        
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
                            
                            total_verses += process_verse(chapter, verse_num, text)

    # Rebuild the FTS index
    print("Rebuilding FTS index...")
    VerseIndex.rebuild()
    
    print(f"Ingestion complete! Added {total_verses} verses.")
    db.close()

if __name__ == "__main__":
    ingest_data()