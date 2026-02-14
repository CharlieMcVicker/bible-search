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
    # Map full names to themselves, and we'll add abbreviations
    bible_books_map = {
        "1 Corinthians": ["1 Cor", "1 Co", "I Cor", "I Co"],
        "1 John": ["1 Jn", "I Jn"],
        "1 Peter": ["1 Pet", "1 Pt", "I Pet", "I Pt"],
        "1 Thessalonians": ["1 Thess", "1 Thes", "I Thess", "I Thes"],
        "1 Timothy": ["1 Tim", "I Tim"],
        "2 Corinthians": ["2 Cor", "2 Co", "II Cor", "II Co"],
        "2 John": ["2 Jn", "II Jn"],
        "2 Peter": ["2 Pet", "2 Pt", "II Pet", "II Pt"],
        "2 Thessalonians": ["2 Thess", "2 Thes", "II Thess", "II Thes"],
        "2 Timothy": ["2 Tim", "II Tim"],
        "3 John": ["3 Jn", "III Jn"],
        "Acts": ["Act"],
        "Colossians": ["Col"],
        "Ephesians": ["Eph"],
        "Galatians": ["Gal"],
        "Genesis": ["Gen", "Gn"],
        "Hebrews": ["Heb"],
        "James": ["Jas", "Jam"],
        "John": ["Jn", "Joh"],
        "Jude": ["Jud"],
        "Luke": ["Lk", "Luk"],
        "Mark": ["Mk", "Mrk"],
        "Matthew": ["Matt", "Mt"],
        "Philemon": ["Phm", "Phile"],
        "Philippians": ["Phil", "Php"],
        "Revelation": ["Rev"],
        "Romans": ["Rom", "Ro"],
        "Titus": ["Tit"],
    }
    
    # Flatten list for patterns
    # We want to normalize the extracted entity to the full book name if possible,
    # but EntityRuler just assigns a label. We'll handle normalization in the extractor.
    
    patterns = []
    for book, abbreviations in bible_books_map.items():
        # Full name
        book_parts = book.split()
        pattern = [{"LOWER": part.lower()} for part in book_parts]
        patterns.append({"label": "BIBLE_BOOK", "pattern": pattern, "id": book})
        
        # Abbreviations
        for abbr in abbreviations:
            abbr_parts = abbr.split()
            pattern = [{"LOWER": part.lower()} for part in abbr_parts]
            # Optional period after abbreviation (e.g., "Gen.")
            # This is tricky with tokenization. "Gen." might be one token or "Gen" "."
            # We'll rely on simple token matching first.
            patterns.append({"label": "BIBLE_BOOK", "pattern": pattern, "id": book})
            
            # Pattern with period if it's a single word abbreviation
            if len(abbr_parts) == 1:
                patterns.append({"label": "BIBLE_BOOK", "pattern": [{"LOWER": abbr_parts[0].lower()}, {"TEXT": "."}], "id": book})

    ruler.add_patterns(patterns)
    
    return nlp

def extract_bible_references(text, nlp=None):
    """
    Extracts Bible references from text.
    Returns a list of dictionaries with 'book', 'chapter', 'verse_start', 'verse_end'.
    Example: 
    "John 3:16" -> {'book': 'John', 'chapter': 3, 'verse_start': 16, 'verse_end': 16}
    "Genesis 1:1-5" -> {'book': 'Genesis', 'chapter': 1, 'verse_start': 1, 'verse_end': 5}
    """
    if nlp is None:
        nlp = create_nlp_pipeline()
        
    doc = nlp(text)
    
    matcher = Matcher(nlp.vocab)
    
    # Helper to create patterns
    def make_pattern(book_op="+"):
        return {"ENT_TYPE": "BIBLE_BOOK", "OP": book_op}

    # Pattern 1a: Range with split tokens
    # e.g., "John 3 : 16 - 17"
    pattern_range_split = [
        make_pattern(),
        {"LIKE_NUM": True}, # Chapter
        {"TEXT": ":"},
        {"LIKE_NUM": True}, # Start Verse
        {"TEXT": "-"},
        {"LIKE_NUM": True}  # End Verse
    ]
    matcher.add("REF_RANGE_SPLIT", [pattern_range_split])

    # Pattern 1b: Range with combined Chapter:Verse token
    # e.g., "John 3:16-17" or "John 3:16 - 17"
    # Tokenization: "3:16", "-", "17"
    pattern_range_combined = [
        make_pattern(),
        {"TEXT": {"REGEX": r"^\d+:\d+$"}}, # Chapter:StartVerse
        {"TEXT": "-"},
        {"LIKE_NUM": True}  # End Verse
    ]
    matcher.add("REF_RANGE_COMBINED", [pattern_range_combined])
    
    # Pattern 2a: Single Reference split
    # e.g., "John 3 : 16"
    pattern_single_split = [
        make_pattern(),
        {"LIKE_NUM": True}, # Chapter
        {"TEXT": ":"},
        {"LIKE_NUM": True}  # Verse
    ]
    matcher.add("REF_SINGLE_SPLIT", [pattern_single_split])
    
    # Pattern 2b: Single Reference combined
    # e.g., "John 3:16"
    pattern_single_combined = [
        make_pattern(),
        {"TEXT": {"REGEX": r"^\d+:\d+$"}} # Chapter:Verse
    ]
    matcher.add("REF_SINGLE_COMBINED", [pattern_single_combined])
    
    # Pattern 3: Whole Chapter
    pattern_chapter = [
        make_pattern(),
        {"LIKE_NUM": True}
    ]
    matcher.add("REF_CHAPTER", [pattern_chapter])

    matches = matcher(doc)
    
    # Sort matches by start position, then by length (longest first)
    matches.sort(key=lambda x: (x[1], -x[2]))
    
    references = []
    seen_tokens = set()
    
    for match_id, start, end in matches:
        if any(t in seen_tokens for t in range(start, end)):
            continue
            
        string_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        
        chapter = None
        v_start = None
        v_end = None
        book_span = None

        if string_id == "REF_RANGE_SPLIT":
            # [Book..., Ch, :, V1, -, V2]
            book_span = span[:-5]
            chapter = int(span[-5].text)
            v_start = int(span[-3].text)
            v_end = int(span[-1].text)
            
        elif string_id == "REF_RANGE_COMBINED":
            # [Book..., Ch:V1, -, V2]
            book_span = span[:-3]
            ch_v = span[-3].text
            chapter, v_start = map(int, ch_v.split(":"))
            v_end = int(span[-1].text)
            
        elif string_id == "REF_SINGLE_SPLIT":
            # [Book..., Ch, :, V1]
            book_span = span[:-3]
            chapter = int(span[-3].text)
            v_start = int(span[-1].text)
            v_end = v_start
            
        elif string_id == "REF_SINGLE_COMBINED":
            # [Book..., Ch:V1]
            book_span = span[:-1]
            ch_v = span[-1].text
            chapter, v_start = map(int, ch_v.split(":"))
            v_end = v_start
            
        elif string_id == "REF_CHAPTER":
            # [Book..., Ch]
            book_span = span[:-1]
            chapter = int(span[-1].text)
            v_start = None
            v_end = None
            
        book_name = book_span.text
        # Use EntID if available for normalization
        for token in book_span:
            if token.ent_id_:
                book_name = token.ent_id_
                break
        
        references.append({
            "book": book_name,
            "chapter": chapter,
            "verse_start": v_start,
            "verse_end": v_end
        })
        
        for t in range(start, end):
            seen_tokens.add(t)
            
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
