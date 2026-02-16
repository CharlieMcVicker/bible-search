import pytest
import spacy

from src.nlp import is_command, is_hypothetical, is_inability


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Go to the store.", True),
        ("Please sit down.", True),
        ("Don't do that.", True),
        ("Eat your vegetables.", True),
        ("Leave the chair.", True),
        ("Chop up some cabbage to cook.", True),
        ("Sit.", True),
        # Negative cases
        ("I am going to the store.", False),
        ("He sits down.", False),
        ("They don't do that.", False),
        ("We ate our vegetables.", False),
        ("Crossing the road, I was almost run over by a car.", False),
        ("You should leave.", False),
        ("Relax. You'll get exhausted.", True),  # "Relax" is a command
    ],
)
def test_is_command(nlp, text, expected):
    doc = nlp(text)
    # Check individual sentences if multiple
    results = [is_command(nlp(sent.text)) for sent in doc.sents]
    assert any(results) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("If it rains, we stay inside.", True),
        ("Unless you help, I won't finish.", True),
        ("I would go if I could.", True),
        ("You should study.", True),
        ("Except for the rain, it was nice.", True),
        ("It is raining.", False),
    ],
)
def test_is_hypothetical(nlp, text, expected):
    doc = nlp(text)
    assert is_hypothetical(doc) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I cannot swim.", True),
        ("I am unable to swim.", True),
        ("He could not find it.", True),
        ("They will not be able to come.", True),
        ("I can swim.", False),
        ("I am not a doctor.", False),
    ],
)
def test_is_inability(nlp, text, expected):
    doc = nlp(text)
    assert is_inability(doc) == expected
