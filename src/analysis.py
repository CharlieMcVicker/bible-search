from collections import Counter

import spacy

from src.models import SqliteDatabase, VerbStat, Verse, db


def analyze_hypothetical_verbs():
    """
    Analyzes all verses marked as hypothetical and counts the occurrences of each verb form
    distinguishing between subclause (e.g., after 'if') and matrix clause.
    """
    # Initialize database proxy
    database = SqliteDatabase("bible.db")
    db.initialize(database)

    if db.is_closed():
        db.connect()

    print("Loading spaCy model...")
    # We need the parser to determine clause structure
    nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])

    hypothetical_verses = Verse.select().where(Verse.is_hypothetical == True)
    count = hypothetical_verses.count()
    print(f"Analyzing {count} hypothetical verses...")

    subclause_counts = Counter()
    matrix_counts = Counter()

    for i, verse in enumerate(hypothetical_verses):
        if i % 500 == 0 and i > 0:
            print(f"Processed {i}/{count}...")

        doc = nlp(verse.text)

        for token in doc:
            if token.pos_ == "VERB":
                form = token.text.lower()

                # Heuristic for subclause vs matrix
                is_subclause = False
                curr = token
                while curr.dep_ != "ROOT":
                    if curr.dep_ == "advcl":
                        is_subclause = True
                        break
                    curr = curr.head

                if is_subclause:
                    subclause_counts[form] += 1
                else:
                    matrix_counts[form] += 1

    return subclause_counts, matrix_counts


def save_verb_stats():
    """
    Runs the analysis and saves results to the VerbStat table.
    """
    sub_counts, mat_counts = analyze_hypothetical_verbs()

    print("Saving verb stats to database...")
    # Ensure table exists
    db.create_tables([VerbStat])

    all_forms = set(sub_counts.keys()) | set(mat_counts.keys())

    with db.atomic():
        # Clear existing
        VerbStat.delete().execute()

        for form in all_forms:
            sub = sub_counts[form]
            mat = mat_counts[form]
            VerbStat.create(
                form=form, subclause_count=sub, matrix_count=mat, total_count=sub + mat
            )
    print("Done!")


if __name__ == "__main__":
    save_verb_stats()

    # Also print top results for confirmation
    print("\nTop Verb Forms in Hypotheticals (Saved to DB):")
    print(f"{'Form':<15} | {'Subclause':<10} | {'Matrix':<10} | {'Total':<10}")
    print("-" * 55)

    query = VerbStat.select().order_by(VerbStat.total_count.desc()).limit(50)
    for stat in query:
        print(
            f"{stat.form:<15} | {stat.subclause_count:<10} | {stat.matrix_count:<10} | {stat.total_count:<10}"
        )
