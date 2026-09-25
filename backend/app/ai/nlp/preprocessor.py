"""NLP Preprocessor for Financial Transaction Descriptions and Query Normalization.

Features:
- Lowercasing, whitespace compaction.
- Punctuation handling while preserving financial markers (INR, Rs, UPI, NEFT, POS, SIP, EMI).
- Scikit-learn BaseEstimator / TransformerMixin integration for zero-leakage pipelines.
"""

import re
from typing import List, Union
from sklearn.base import BaseEstimator, TransformerMixin


def clean_financial_text(text: Union[str, None]) -> str:
    """Normalizes raw merchant descriptions and financial strings."""
    if not text or not isinstance(text, str):
        return ""

    # Convert to lowercase
    s = text.lower().strip()

    # Standardize currency abbreviations (handle ₹ which is non-ascii word boundary)
    s = re.sub(r"(?:₹|\b(?:rs\.?|inr)\b)", " inr ", s)

    # Normalize UPI/POS/NEFT prefix delimiters
    s = re.sub(r"upi/([a-z0-9_\-\.]+)/([0-9]+)", r"upi \1 ", s)
    s = re.sub(r"\bpos\b", " pos ", s)
    s = re.sub(r"\bref\s*#?[0-9]+\b", " ", s)

    # Replace special punctuation with whitespace, preserving alphanumeric
    s = re.sub(r"[^a-z0-9\s]", " ", s)

    # Compact multi-spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


class TextNormalizer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible text normalization transformer.

    Ensures that text transformation parameters and logic are encapsulated
    inside sklearn Pipelines to avoid train-test data leakage.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X: List[str]) -> List[str]:
        return [clean_financial_text(x) for x in X]
