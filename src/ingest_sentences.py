import json
import os

import spacy
from peewee import SqliteDatabase

from src.models import Sentence, SentenceIndex, db

DATA_FILE = os.path.join("data", "sentences.json")
DB_FILE = "bible.db"


def ingest_sentences():
    if not os.path.exists(DATA_FILE):
        print(f"Data file '{DATA_FILE}' not found.")
        return

    print("Loading spaCy model...")
    try:
        nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])
    except OSError:
        from spacy.cli import download

        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])

    print("Connecting to database...")
    database = SqliteDatabase(DB_FILE)
    db.initialize(database)
    db.connect()

    # Drop and recreate to ensure schema updates
    db.drop_tables([Sentence, SentenceIndex], safe=True)
    db.create_tables([Sentence, SentenceIndex], safe=True)

    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} sentences. Ingesting...")

    # We can use bulk insert for speed, but we need lemmatization first.
    # To keep it simple and progress indicators separate, we'll loop.
    # Or strict peewee bulk_create with batching.

    batch_size = 100
    batch = []
    total_ingested = 0

    with db.atomic():
        # Clear existing? Maybe. Or just upsert.
        # Let's clear for now to be clean, user said "only use the new source going forward"
        # but we are keeping Bible tables. We should clear Sentence table.
        from src.models import SentenceTag

        Sentence.delete().execute()

        for item in data:
            ref_id = item.get("id")
            english = item.get("english", "")
            syllabary = item.get("syllabary", "")
            phonetic = item.get("phonetic", "")
            audio = item.get("audio")

            # NLP Processing
            doc = nlp(english)
            lemma_text = " ".join([token.lemma_ for token in doc])

            from src.nlp import (
                get_subclause_types,
                is_command,
                is_hypothetical,
                is_inability,
            )

            is_hypothetical = is_hypothetical(doc)
            is_command = is_command(doc)
            is_inability = is_inability(doc)
            subclause_list = get_subclause_types(doc)
            subclause_types = ",".join(subclause_list) if subclause_list else None

            # Prepare sentence record
            batch.append(
                {
                    "ref_id": ref_id,
                    "english": english,
                    "syllabary": syllabary,
                    "phonetic": phonetic,
                    "audio": audio,
                    "lemma_text": lemma_text,
                    "is_hypothetical": is_hypothetical,
                    "is_command": is_command,
                    "is_inability": is_inability,
                    "subclause_types": subclause_types,
                }
            )

            if len(batch) >= batch_size:
                Sentence.insert_many(batch).execute()
                total_ingested += len(batch)
                batch = []
                print(f"Ingested {total_ingested}...")

        if batch:
            Sentence.insert_many(batch).execute()
            total_ingested += len(batch)

    print("Rebuilding FTS index...")
    SentenceIndex.rebuild()
    print("Optimization...")
    SentenceIndex.optimize()

    print(f"Complete! Ingested {total_ingested} sentences.")
    db.close()


if __name__ == "__main__":
    ingest_sentences()
