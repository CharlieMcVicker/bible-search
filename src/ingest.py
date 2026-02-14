import os
import json
import spacy
from peewee import SqliteDatabase, fn
from src.models import db, Book, Chapter, Verse, VerseIndex, Entity, VerseEntity

DATA_DIR = 'data'
FULL_DATA_FILE = os.path.join(DATA_DIR, 'kjv_full.json')

def ingest_data():
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found.")
        return

    print("Loading spaCy model...")
    try:
        nlp = spacy.load("en_core_web_sm", disable=["textcat"])
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["textcat"])

    print("Connecting to database...")
    database = SqliteDatabase('bible.db')
    db.initialize(database)
    db.connect()
    
    print("Dropping and recreating tables...")
    db.drop_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity], safe=True)
    db.create_tables([Book, Chapter, Verse, VerseIndex, Entity, VerseEntity])
    
    total_verses = 0
    entity_cache = {}

    def process_linguistics(verse, text):
        doc = nlp(text)
        verse.lemma_text = " ".join([token.lemma_ for token in doc])
        
        # Hypothetical detection
        conditional_keywords = {"if", "unless", "except"}
        if any(token.lower_ in conditional_keywords for token in doc):
            verse.is_hypothetical = True
        elif any(token.lower_ in {"would", "should"} for token in doc):
             verse.is_hypothetical = True

        # Command detection
        first_token = None
        for token in doc:
            if not token.is_punct and not token.is_space:
                first_token = token
                break
        
        if first_token:
            if first_token.pos_ == "VERB" and first_token.dep_ in ("ROOT", "advcl"):
                verse.is_command = True
            if first_token.lower_ in {"thou", "ye", "you"}:
                next_token = doc[first_token.i + 1] if first_token.i + 1 < len(doc) else None
                if next_token and next_token.lower_ in {"shalt", "shall"}:
                    verse.is_command = True
        
        verse.save()

        # Entities
        seen_entities = set()
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "NORP"]:
                key = (ent.text, ent.label_)
                if key not in seen_entities:
                    seen_entities.add(key)
                    if key not in entity_cache:
                        entity, _ = Entity.get_or_create(name=ent.text, label=ent.label_)
                        entity_cache[key] = entity
                    VerseEntity.create(verse=verse, entity=entity_cache[key])

    # 1. Ingest Full KJV first
    if os.path.exists(FULL_DATA_FILE):
        print(f"Ingesting full data file: {FULL_DATA_FILE}")
        with open(FULL_DATA_FILE, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            
        with db.atomic():
            for book_data in data:
                book_name = book_data['name']
                print(f"Processing {book_name}...")
                book = Book.create(name=book_name)
                
                chapters = book_data['chapters']
                for i, verses in enumerate(chapters):
                    chapter = Chapter.create(book=book, number=i + 1)
                    for j, verse_text in enumerate(verses):
                        v = Verse.create(chapter=chapter, number=j + 1, text=verse_text)
                        process_linguistics(v, verse_text)
                        total_verses += 1
    
    # 2. Update with Cherokee translations from directories
    print("Updating with Cherokee translations...")
    book_dirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    
    with db.atomic():
        for book_name in sorted(book_dirs):
            try:
                book = Book.get(fn.Lower(Book.name) == book_name.lower())
            except Book.DoesNotExist:
                print(f"Skipping unknown book directory: {book_name}")
                continue
                
            print(f"Updating {book.name}...")
            book_path = os.path.join(DATA_DIR, book_name)
            for chap_file in os.listdir(book_path):
                if not chap_file.endswith('.json'): continue
                try:
                    chap_num = int(os.path.splitext(chap_file)[0])
                    chapter = Chapter.get(Chapter.book == book, Chapter.number == chap_num)
                except (ValueError, Chapter.DoesNotExist):
                    continue
                
                with open(os.path.join(book_path, chap_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        verse_num = int(item['verse'])
                        chr_text = item.get('chr')
                        if chr_text:
                            Verse.update(text_chr=chr_text).where(
                                Verse.chapter == chapter, 
                                Verse.number == verse_num
                            ).execute()

    print("Rebuilding FTS index...")
    VerseIndex.rebuild()
    
    print(f"Ingestion complete! Added {total_verses} verses.")
    db.close()

if __name__ == "__main__":
    ingest_data()