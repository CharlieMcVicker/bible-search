import spacy
from collections import Counter, defaultdict
from src.models import Verse, db, SqliteDatabase

def analyze_hypothetical_verbs():

    """

    Analyzes all verses marked as hypothetical and counts the occurrences of each verb form

    distinguishing between subclause (e.g., after 'if') and matrix clause.

    """

    # Initialize database proxy

    database = SqliteDatabase('bible.db')

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

                # 1. If the verb or any of its ancestors is an 'advcl' (adverbial clause)

                #    it is likely in the subclause (the 'if' part).

                # 2. If it's the ROOT or a direct child of the ROOT not in an advcl, it's matrix.

                

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



if __name__ == "__main__":

    sub_counts, mat_counts = analyze_hypothetical_verbs()

    

    print("\nTop Verb Forms in Hypotheticals:")

    print(f"{'Form':<15} | {'Subclause':<10} | {'Matrix':<10} | {'Total':<10}")

    print("-" * 55)

    

    all_forms = set(sub_counts.keys()) | set(mat_counts.keys())

    # Sort by total

    sorted_forms = sorted(all_forms, 

                          key=lambda f: sub_counts[f] + mat_counts[f], 

                          reverse=True)

    

    for form in sorted_forms[:50]:

        sub = sub_counts[form]

        mat = mat_counts[form]

        total = sub + mat

        print(f"{form:<15} | {sub:<10} | {mat:<10} | {total:<10}")
