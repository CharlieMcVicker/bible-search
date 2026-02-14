from src.models import db, Book, Chapter, Verse

def main():
    print("Bible Search App")
    db.connect()
    book_count = Book.select().count()
    verse_count = Verse.select().count()
    print(f"Database contains {book_count} books and {verse_count} verses.")
    db.close()

if __name__ == "__main__":
    main()
