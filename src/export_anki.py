import genanki

from src.models import Sentence, SentenceTag, init_db

# Constants for Deck
DECK_ID = 2059300110  # Unique ID for this deck
MODEL_ID = 1607392322  # Unique ID for the note type


def generate_anki_deck(output_filename="Cherokee_Sentences.apkg"):
    # Initialize DB
    init_db("bible.db")

    # Fetch all tags
    tags = list(SentenceTag.select())
    tags_by_ref = {}

    # Assert single tag per sentence (grouping first to check)
    for t in tags:
        if t.ref_id not in tags_by_ref:
            tags_by_ref[t.ref_id] = []
        tags_by_ref[t.ref_id].append(t)

    # Filter/Validate: Each sentence must have exactly one tag
    valid_ref_ids = []
    skipped_count = 0

    for ref_id, sentence_tags in tags_by_ref.items():
        if len(sentence_tags) != 1:
            print(
                f"Skipping {ref_id}: Has {len(sentence_tags)} tags (expected exactly 1)."
            )
            print(f"Tags: {[t.tag for t in sentence_tags]}")
            skipped_count += 1
            continue
        valid_ref_ids.append(ref_id)

    print(
        f"Processing {len(valid_ref_ids)} sentences. Skipped {skipped_count} invalid ones."
    )

    # Fetch all sentences
    sentences_map = {}
    chunk_size = 500
    for i in range(0, len(valid_ref_ids), chunk_size):
        chunk = valid_ref_ids[i : i + chunk_size]
        # Peewee `in_` clause
        sq = Sentence.select().where(Sentence.ref_id.in_(chunk))
        for s in sq:
            sentences_map[s.ref_id] = s

    # Define Anki Model
    # Fields: Text (Cloze), English, Tag
    # The Text field will contain both syllabary and phonetic with the same cloze c1
    model = genanki.Model(
        MODEL_ID,
        "Cherokee with Cloze",
        fields=[
            {"name": "Text"},
            {"name": "English"},
            {"name": "Tag"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": '{{cloze:Text}}<br><br><div style="font-size: 0.8em;">{{English}}</div><br><br><span style="font-size:small">{{Tag}}</span>',
                "afmt": '{{cloze:Text}}<br><br><div style="font-size: 0.8em;">{{English}}</div><br><br><span style="font-size:small">{{Tag}}</span>',
            },
        ],
        css="""
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
        }
        .cloze {
            font-weight: bold;
            color: blue;
        }
        .nightMode .cloze {
            color: lightblue;
        }
        """,
    )

    deck = genanki.Deck(DECK_ID, "Cherokee Sentences")

    for ref_id in valid_ref_ids:
        if ref_id not in sentences_map:
            print(
                f"Warning: Data integrity issue. {ref_id} has tag but no sentence found."
            )
            continue

        sentence = sentences_map[ref_id]
        tag_obj = tags_by_ref[ref_id][0]  # We already validated length is 1
        word_idx = tag_obj.word_index
        tag_label = tag_obj.tag

        syllabary_words = sentence.syllabary.split(" ")
        phonetic_words = sentence.phonetic.split(" ") if sentence.phonetic else []

        # Validate indices
        if word_idx >= len(syllabary_words):
            print(
                f"Warning: Index {word_idx} out of bounds for syllabary in {ref_id}. Skipping."
            )
            continue

        # Construct Cloze String
        # Syllabary
        s_target = syllabary_words[word_idx]
        syllabary_clozed = list(syllabary_words)
        syllabary_clozed[word_idx] = "{{c1::" + s_target + "}}"
        syllabary_str = " ".join(syllabary_clozed)

        # Phonetic
        phonetic_str = ""
        if len(phonetic_words) == len(syllabary_words):
            p_target = phonetic_words[word_idx]
            phonetic_clozed = list(phonetic_words)
            phonetic_clozed[word_idx] = "{{c1::" + p_target + "}}"
            phonetic_str = " ".join(phonetic_clozed)
        else:
            print(
                f"Warning: Phonetic/Syllabary word count mismatch for {ref_id}. Syllabary ({len(syllabary_words)}) vs Phonetic ({len(phonetic_words)}). Phonetic will not be clozed properly."
            )
            phonetic_str = (
                sentence.phonetic
            )  # Fallback: No cloze on phonetic or just display full text?
            # User requested "cloze on both scripts". If we can't align, maybe best to show full phonetic but marked?
            # Or just skip cloze on phonetic. Let's show full phonetic if alignment fails.

        # Combined Text for Card
        # <div class=syllabary>...</div><br><div class=phonetic>...</div>
        combined_text = f"<div class='syllabary' style='font-size: 1.5em; margin-bottom: 0.5em;'>{syllabary_str}</div>"
        if phonetic_str:
            combined_text += (
                f"<div class='phonetic' style='color: #666;'>{phonetic_str}</div>"
            )

        note = genanki.Note(
            model=model,
            fields=[combined_text, sentence.english, tag_label],
            tags=[
                tag_label.replace(" ", "_")
            ],  # Anki tags usually shouldn't have spaces
        )
        deck.add_note(note)

    # Save
    genanki.Package(deck).write_to_file(output_filename)
    print(f"Generated deck with {len(deck.notes)} notes: {output_filename}")


if __name__ == "__main__":
    generate_anki_deck()
