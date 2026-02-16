import json
import os
from collections import Counter

import spacy

DATA_FILE = os.path.join("data", "sentences.json")


def analyze_subclauses():
    if not os.path.exists(DATA_FILE):
        print(f"Data file '{DATA_FILE}' not found.")
        return

    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")

    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    subclause_deps = Counter()

    print(f"Analyzing {len(data)} sentences...")
    for i, item in enumerate(data):
        english = item.get("english", "")
        doc = nlp(english)
        for token in doc:
            # Check for common clausal dependency labels
            if token.dep_ in [
                "advcl",
                "relcl",
                "ccomp",
                "xcomp",
                "acl",
                "csubj",
                "csubjpass",
            ]:
                subclause_deps[token.dep_] += 1

        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1} sentences...")

    print("\nSubclause Dependency Labels Found:")
    for dep, count in subclause_deps.most_common():
        print(f"{dep}: {count}")


if __name__ == "__main__":
    analyze_subclauses()
