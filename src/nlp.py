import spacy
from spacy.matcher import Matcher
from spacy.pipeline import EntityRuler

def create_nlp_pipeline():
    """
    Creates and returns a spaCy NLP pipeline with a custom EntityRuler
    for Bible book names.
    """
    nlp = spacy.load("en_core_web_sm")
    
    # Add EntityRuler for Bible books
    # We add it before 'ner' so that our custom entities take precedence or are available for NER
    # but specifically we want to use them in Matcher later, so having them as entities is good.
    # However, Matcher works on tokens, but can use ENT_TYPE.
    # So we need the EntityRuler to run before we use the Matcher in our extraction logic.
    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")
    else:
        ruler = nlp.get_pipe("entity_ruler")
    
    # List of Bible books based on the data directory
    bible_books = [
        "1 Corinthians", "1 John", "1 Peter", "1 Thessalonians", "1 Timothy",
        "2 Corinthians", "2 John", "2 Peter", "2 Thessalonians", "2 Timothy",
        "3 John", "Acts", "Colossians", "Ephesians", "Galatians", "Genesis",
        "Hebrews", "James", "John", "Jude", "Luke", "Mark", "Matthew",
        "Philemon", "Philippians", "Revelation", "Romans", "Titus"
    ]
    
    patterns = []
    for book in bible_books:
        # Create a pattern for the full book name
        # Handling multi-word book names like "1 John"
        book_parts = book.split()
        pattern = [{"LOWER": part.lower()} for part in book_parts]
        patterns.append({"label": "BIBLE_BOOK", "pattern": pattern})

    ruler.add_patterns(patterns)
    
    return nlp

def extract_bible_references(text, nlp=None):
    """
    Extracts Bible references from text.
    Returns a list of dictionaries with 'book', 'chapter', 'verse'.
    Example: "John 3:16" -> {'book': 'John', 'chapter': 3, 'verse': 16}
    """
    if nlp is None:
        nlp = create_nlp_pipeline()
        
    doc = nlp(text)
    matcher = Matcher(nlp.vocab)
    
    # Pattern 1: Book Chapter:Verse (separate tokens)
    # e.g., "John", "3", ":", "16"
    pattern_split = [
        {"ENT_TYPE": "BIBLE_BOOK", "OP": "+"},
        {"LIKE_NUM": True},
        {"TEXT": ":"},
        {"LIKE_NUM": True}
    ]
    matcher.add("BOOK_CHAPTER_VERSE_SPLIT", [pattern_split])
    
    # Pattern 2: Book Chapter:Verse (combined token)
    # e.g., "John", "3:16"
    pattern_combined = [
        {"ENT_TYPE": "BIBLE_BOOK", "OP": "+"},
        {"TEXT": {"REGEX": r"^\d+:\d+$"}}
    ]
    matcher.add("BOOK_CHAPTER_VERSE_COMBINED", [pattern_combined])

    # Pattern 3: Book Chapter (e.g., John 3)
    pattern_book_chapter = [
        {"ENT_TYPE": "BIBLE_BOOK", "OP": "+"},
        {"LIKE_NUM": True}
    ]
    matcher.add("BOOK_CHAPTER", [pattern_book_chapter])

    matches = matcher(doc)
    
    # Sort matches by start position, then by length (longest first) to prefer specific matches
    matches.sort(key=lambda x: (x[1], -x[2]))
    
    references = []
    seen_tokens = set()
    
    for match_id, start, end in matches:
        # Check if we've already processed these tokens (to avoid overlap)
        if any(t in seen_tokens for t in range(start, end)):
            continue
            
        string_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        
        # Mark tokens as seen
        for t in range(start, end):
            seen_tokens.add(t)

        if string_id == "BOOK_CHAPTER_VERSE_SPLIT":
            # Span is [Book tokens..., Chapter, :, Verse]
            book_span = span[:-3]
            chapter = span[-3].text
            verse = span[-1].text
            references.append({
                "book": book_span.text,
                "chapter": int(chapter),
                "verse": int(verse)
            })
        elif string_id == "BOOK_CHAPTER_VERSE_COMBINED":
            # Span is [Book tokens..., Chapter:Verse]
            book_span = span[:-1]
            ref_text = span[-1].text
            chapter, verse = ref_text.split(":")
            references.append({
                "book": book_span.text,
                "chapter": int(chapter),
                "verse": int(verse)
            })
        elif string_id == "BOOK_CHAPTER":
            # Span is [Book tokens..., Chapter]
            book_span = span[:-1]
            chapter = span[-1].text
            references.append({
                "book": book_span.text,
                "chapter": int(chapter),
                "verse": None
            })
            
    return references

if __name__ == "__main__":
    nlp = create_nlp_pipeline()
    test_cases = [
        "I was reading John 3:16 and then 1 Peter 5:7.",
        "Genesis 1 is the beginning.",
        "Check 2 Timothy 2:15 for instruction."
    ]
    
    for text in test_cases:
        print(f"Text: {text}")
        refs = extract_bible_references(text, nlp)
        print("Found references:", refs)
        print("-" * 20)
