# FinMate Phase 3 — Natural Language Processing (NLP) Architecture

---

## 1. Objectives of the NLP Layer

The NLP component handles:
1. **Transaction Description Normalization**: Standardizing messy financial strings from banking statements and payment gateways.
2. **Feature Extraction**: Constructing unigram and bigram TF-IDF representations that retain semantic meaning.
3. **Query Normalization**: Preparing user personal finance questions for vector embedding and semantic retrieval.

---

## 2. Text Normalization Rules

Implemented in `app.ai.nlp.preprocessor.clean_financial_text`:
- **Case Standardization**: Lowercases all tokens.
- **Currency Preservation**: Standardizes currency symbols (`₹`, `inr`, `rs.`) to a uniform token `" inr "`.
- **Payment Method Standardization**:
  - `UPI/merchant_id/123456` $\rightarrow$ `"upi merchant_id"`
  - `POS MERCHANT` $\rightarrow$ `"pos merchant"`
  - Reference numbers (`Ref #12345`) are stripped to prevent overfitting to transaction IDs.
- **Punctuation Stripping**: Non-alphanumeric characters (slashes, hyphens, exclamation marks) are converted to whitespace.
- **Whitespace Compaction**: Multiple consecutive whitespace characters are collapsed.

---

## 3. Scikit-learn Pipeline Integration

To eliminate data leakage, text normalization is wrapped in `TextNormalizer(BaseEstimator, TransformerMixin)`:

```python
Pipeline([
    ("normalizer", TextNormalizer()),
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=2500,
        sublinear_tf=True
    )),
    ("clf", CalibratedClassifierCV(LinearSVC()))
])
```

---

## 4. Confidence Calibration & Thresholding

- Raw SVM outputs (distance to decision boundary) do not represent class probabilities.
- We utilize `CalibratedClassifierCV` with Platt scaling to convert margins into calibrated probabilities ($P(\text{class} \mid \text{text}) \in [0, 1]$).
- If $\max_k P(k \mid \text{text}) < 0.60$, the system sets:
  ```json
  {
    "requires_user_confirmation": true
  }
  ```
  The user is prompted in the UI to confirm or override the predicted category.
