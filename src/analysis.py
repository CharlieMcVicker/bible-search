import spacy
from collections import Counter, defaultdict
from src.models import Verse, db, SqliteDatabase

def analyze_hypothetical_verbs():
    """
    Analyzes all verses marked as hypothetical and counts the occurrences of each verb form.
    """
    # Initialize database proxy
    database = SqliteDatabase('bible.db')
    db.initialize(database)
    
    if db.is_closed():
        db.connect()

    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "textcat"])
    
    hypothetical_verses = Verse.select().where(Verse.is_hypothetical == True)
    count = hypothetical_verses.count()
    print(f"Analyzing {count} hypothetical verses...")

    verb_form_counts = Counter()
    verb_lemma_to_forms = defaultdict(Counter)
    
    for i, verse in enumerate(hypothetical_verses):
        if i % 500 == 0 and i > 0:
            print(f"Processed {i}/{count}...")
            
        doc = nlp(verse.text)
        for token in doc:
            if token.pos_ == "VERB":
                form = token.text.lower()
                lemma = token.lemma_.lower()
                verb_form_counts[form] += 1
                verb_lemma_to_forms[lemma][form] += 1

    return verb_form_counts, verb_lemma_to_forms

if __name__ == "__main__":
    form_counts, lemma_to_forms = analyze_hypothetical_verbs()
    
    print("\nTop 50 Verb Forms in Hypotheticals:")
    print("-" * 35)
    for form, count in form_counts.most_common(50):
        print(f"{form:<15}: {count}")

    print("\nVerb Forms by Lemma (Top 10 Lemmas):")
    print("-" * 35)
    # Sort lemmas by total frequency
    sorted_lemmas = sorted(lemma_to_forms.items(), 
                           key=lambda x: sum(x[1].values()), 
                           reverse=True)
    
    for lemma, forms in sorted_lemmas[:20]:
        total = sum(forms.values())
        forms_str = ", ".join([f"{f} ({c})" for f, c in forms.most_common(5)])
        print(f"{lemma:<10} ({total:>3}): {forms_str}")