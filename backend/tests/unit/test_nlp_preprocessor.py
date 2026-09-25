"""Unit tests for NLP Preprocessor and Text Normalizer."""

import pytest
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer

from app.ai.nlp.preprocessor import clean_financial_text, TextNormalizer


def test_clean_financial_text_basic():
    raw = "  Swiggy  Order  123!!  "
    cleaned = clean_financial_text(raw)
    assert cleaned == "swiggy order 123"


def test_clean_financial_text_currencies():
    raw = "Amazon Prime INR 1499 and Rs. 500 or ₹2000"
    cleaned = clean_financial_text(raw)
    assert "inr" in cleaned
    assert "₹" not in cleaned
    assert "rs" not in cleaned


def test_clean_financial_text_upi_and_pos():
    raw = "UPI/swiggyfood/987654 Ref #44901 POS ZARA"
    cleaned = clean_financial_text(raw)
    assert "upi swiggyfood" in cleaned
    assert "pos" in cleaned
    assert "zara" in cleaned


def test_clean_financial_text_empty():
    assert clean_financial_text(None) == ""
    assert clean_financial_text("") == ""
    assert clean_financial_text("   ") == ""


def test_text_normalizer_transformer_in_pipeline():
    pipe = Pipeline([
        ("normalizer", TextNormalizer()),
        ("vect", CountVectorizer())
    ])
    data = ["Swiggy Order ₹450", "Uber Ride Ref #12"]
    pipe.fit(data)
    transformed = pipe.transform(data)
    assert transformed.shape[0] == 2
    assert "inr" in pipe.named_steps["vect"].get_feature_names_out()
