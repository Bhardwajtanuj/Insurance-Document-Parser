# Intelligent Insurance Document Extraction Engine

A production-ready, modular document parsing system designed to extract structured financial and identification data from semi-structured insurance policy documents (PDF/Image/Text).

The engine is layout-agnostic, multi-insurer extensible, and confidence-aware, making it suitable for automated processing pipelines and Human-in-the-Loop verification systems.

---

# 🚀 Overview

Insurance policy documents vary significantly in structure, labeling conventions, formatting, and template design. This engine extracts critical business fields using a **Hybrid Rule-Based Architecture** that combines:

- Deterministic Regex Extraction (High Precision)
- Fuzzy Matching using RapidFuzz (High Recall)
- Pattern Abstraction for Multi-Insurer Support
- Field-Level Confidence Scoring
- OCR Fallback for Scanned PDFs

---

# 🏗️ System Architecture

The system follows a modular pipeline design:

    [Input Document]
            ↓
    [DocumentLoader]  → (PDF / OCR detection)
            ↓
    [TextPreprocessor] → (Normalization)
            ↓
    [FieldExtractor]
            ↓
       ├── RegexExtractor (Strict Match)
       ├── FuzzyFieldLocator (Fallback)
            ↓
    [ConfidenceScorer]
            ↓
    [OutputFormatter]
            ↓
         JSON Output

---

# 📌 Extracted Fields

| Field | Data Type | Example | Validation Rule |
|-------|----------|----------|----------------|
| Policy Number | Alphanumeric | HDFC12345 | Regex `[A-Z0-9-]+` |
| Net Premium | Float | 22000.00 | Must be numeric |
| GST / Tax | Float | 3960.00 | Optional, numeric |
| Total Premium | Float | 25960.00 | Must be numeric |
| Sum Assured | Float | 500000.00 | Must be > Premium |
| Policy Term | Integer/String | 20 Years | Numeric duration |
| Payment Frequency | Enum | Annual | Annual/Monthly/Quarterly |
| Maturity Value | Float | 750000.00 | Must be numeric |
| Insurer Name | String | HDFC Life | Non-empty |
| Customer ID | Alphanumeric | CUST09876 | Alphanumeric |

---

# 🧠 Extraction Strategy

## Tier 1 – Strict Regex Matching

Uses relational patterns:

~~~regex
(Label)\s*:\s*(Value)
~~~

Advantages:
- High precision
- Strong structural validation
- Minimal false positives

Confidence: **0.95 – 1.0**

---

## Tier 2 – Fuzzy Matching (RapidFuzz)

If regex fails:

1. Locate label using `rapidfuzz.partial_ratio`
2. Threshold > 85
3. Extract numeric/alphanumeric value from same line

Advantages:
- Handles OCR errors
- Handles label variation (e.g., "Premum", "Ann. Prem.")

Confidence:
- > 90 similarity → 0.80–0.85  
- 80–90 similarity → 0.60–0.75  

---

# 🔄 Multi-Insurer Pattern Abstraction

Patterns are NOT hardcoded inside extraction logic.

Directory structure:

    patterns/
    ├── base_patterns.py
    ├── hdfc_patterns.py
    ├── lic_patterns.py

Each insurer inherits from `BASE_FIELDS` and overrides only deviating patterns.

Example:

~~~python
patterns = {
    "premium_amount": {
        "keywords": ["premium", "total payable"],
        "regex": r"(?:Premium)\s*[:]\s*([\d,]+)"
    }
}
~~~

Benefits:

- Clean separation of logic and configuration
- Easy onboarding of new insurers
- Zero modification to extraction engine

---

# 🎯 Confidence Scoring Model

| Method | Condition | Score |
|--------|----------|-------|
| Regex | Exact structured match | 0.95–1.0 |
| Fuzzy | Similarity > 90 | 0.80–0.85 |
| Fuzzy | Similarity 80–90 | 0.60–0.75 |
| No Match | Not found | 0.0 |

Use Cases:
- STP (Straight Through Processing)
- Human-in-the-loop routing
- Quality threshold enforcement

---

# 🧾 Output Schema

~~~json
{
  "policy_number": {
    "value": "HDFC12345",
    "confidence": 0.95,
    "method": "regex"
  },
  "premium_amount": {
    "value": "25960.00",
    "confidence": 0.82,
    "method": "fuzzy"
  }
}
~~~

---

# 🛠️ Tech Stack

- Python 3.9+
- pypdf
- pytesseract
- pdf2image
- rapidfuzz
- unittest

---

# 🧪 Unit Testing Strategy

### 1. Regex Validation Tests
Ensure patterns match known inputs.

### 2. Fuzzy Variation Tests
Inject typos such as `"Plicy Num"` and verify extraction robustness.

### 3. Synthetic Layout Tests
Simulate multiple insurer layouts.

### 4. Negative Tests
Ensure unrelated documents produce zero-confidence outputs.

Run tests:

    python -m unittest discover

---

# 📦 Installation

    pip install -r requirements.txt

---

# ▶️ Usage

~~~python
from extractor import DocumentParser

parser = DocumentParser(insurer="hdfc")
result = parser.parse("sample_policy.pdf")

print(result)
~~~

---

# ⚙️ Edge Case Handling

### Currency Formats
- Rs. 25,000
- 25000.00
- 25.000,00

Normalized during preprocessing.

### Multiple Monetary Values
Specific regex anchors prioritize final payable amount.

### OCR Noise
Fuzzy matching tolerates label corruption.

---

# 📈 Scalability

- Stateless extractor
- Horizontal scaling supported
- Worker-based parallel processing
- Structured logging enabled

---

# 🔮 Future Enhancements

- LayoutLM integration (Text + Layout understanding)
- NER-based semantic extraction
- ML-based confidence calibration
- Insurer auto-classification module

---



# 👤 Author

Tanuj Bhardwaj  

Insurance Document Intelligence System
