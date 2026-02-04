# Technical Design Document: Intelligent Insurance Document Extraction Engine

## 1. Problem Statement

The objective of this system is to automate the extraction of critical financial and identification data from semi-structured insurance policy documents. Insurance policies typically appear in PDF or image formats and lack a standardized layout across different providers (insurers). Even within a single insurer, document templates often change over time, rendering rigid positional extraction methods ineffective.

Key financial fields required for extraction include, but are not limited to:
- **Policy Number**: Unique identifier for the contract.
- **Net Premium**: Base premium amount before taxes.
- **GST / Tax Amount**: Applicable goods and services tax.
- **Total Premium Payable**: Final amount to be paid by the customer.
- **Sum Assured**: Total coverage amount.
- **Policy Term**: Duration of the insurance coverage (e.g., 20 Years).
- **Payment Frequency**: Mode of payment (Annual, Monthly, Quarterly).
- **Maturity Value**: Projected return at the end of the term.
- **Insurer Name**: The issuing entity.
- **Customer ID**: Unique client identifier.

The variability in field labeling (e.g., "Total Premium" vs. "Premium Payable"), layout density, and potential optical character recognition (OCR) noise necessitates a robust, fault-tolerant extraction engine capable of handling heterogeneity while maintaining high precision.

---

## 2. System Architecture

The architecture follows a modular, pipelined approach designed for separation of concerns and testability. The data flows sequentially through isolation layers, transforming raw bytes into structured, scored metadata.

### Architectural Components

1.  **DocumentIngestionLayer (`DocumentLoader`)**: 
    Responsible for file I/O and format normalization. It abstracts the underlying file type (native PDF, scanned PDF, plain text) and provides a unified stream of raw text to the downstream processors. It integrates fallback logic to trigger OCR (via Tesseract) when native text extraction yields insufficient data.

2.  **PreprocessingLayer (`TextPreprocessor`)**:
    Reduces noise in the raw text stream. Operations include whitespace normalization, artifact removal, Unicode standardization (e.g., replacing non-breaking spaces), and currency symbol sanitization.

3.  **PatternRegistry**:
    A configuration management layer that serves retrieval patterns based on the document context (Insurer). It utilizes an inheritance model where improved specific patterns override a common baseline.

4.  **ExtractionEngine (`FieldExtractor`)**:
    The core processing unit implementing a hybrid extraction strategy. It orchestrates sub-modules:
    -   **RegexExtractor**: Deterministic extraction based on rigid patterns.
    -   **FuzzyFieldLocator**: Probabilistic extraction based on approximate string matching (utilizing `rapidfuzz`).

5.  **ScoringEngine (`ConfidenceScorer`)**:
    Evaluates the quality of each extraction. It assigns a normalized confidence score (0.0 to 1.0) based on the extraction method and signal strength, enabling downstream systems to set quality thresholds.

6.  **OutputFormatter**:
    Serializes the internal data structures into a standardized JSON schema, ensuring consistent API contracts.

### Pipeline Flow

```text
[Input Document] 
       ⬇
[DocumentLoader] --> (Format Detection / OCR Fallback)
       ⬇
[TextPreprocessor] --> (Normalization / Cleaning)
       ⬇
[FieldExtractor] <-- [PatternRegistry] (Contextual Rules)
       ⬇
   [Strategy A: Regex] 
       ⬇
   [Strategy B: Fuzzy Fallback]
       ⬇
[ConfidenceScorer] --> (Quality Assessment)
       ⬇
[OutputFormatter] --> {JSON}
```

---

## 3. Pattern Abstraction for Multi-Insurer Support

Hardcoding regular expressions directly into business logic creates technical debt and limits scalability. As new insurers are onboarded, a monolithic extraction function becomes unmaintainable. To address this, the system implements a **Pattern Registry**.

### Design Pattern
The registry utilizes a configuration-driven approach. A `BASE_FIELDS` dictionary defines the standard patterns applicable to generic documents. Insurer-specific modules (e.g., `patterns.hdfc`, `patterns.lic`) import this base configuration and perform dictionary updates only for fields that deviate from the norm.

### Extensibility benefits
1.  **Isolation**: Adding a new insurer requires creating a single configuration file, with no changes to the core `FieldExtractor`.
2.  **Inheritance**: Common fields utilize base patterns, reducing code duplication.
3.  **Hot-Swapping**: Patterns can be loaded dynamically at runtime based on user input or classification results.

**Example Configuration Structure:**

```python
patterns = {
    "premium_amount": {
        "keywords": ["premium", "total payable"],
        "regex": r"(?:Premium)\s*[:]\s*([\d,]+)"
    }
}
```

---

## 4. Extraction Logic & Comparative Analysis

### Core Identification Logic
The system employs a **Key-Value Pair (KVP) Proximity Algorithm** designed to handle semi-structured streams of text.
1.  **Anchor Detection**: The engine first scans the text to identify specific "anchors" (field labels like "Policy No", "Total Premium").
2.  **Value Association**: Once an anchor is located, the algorithm scans the immediate context (same line or regex capture group) for a token matching the expected data type (e.g., a numeric sequence for Premium, an alphanumeric string for Policy ID).

This is implemented via two tiered strategies:
-   **Tier 1: Relational Regex (Strict)**: Defines a strict spatial relationship. The pattern `(Label)\s*:\s*(Value)` asserts that the label and value must be adjacent and separated by specific delimiters. This identifies the field *and* validates the structure simultaneously.
-   **Tier 2: Fuzzy Proximity (Heuristic)**: Decouples the label from the value. It first locates the Anchor via string similarity (using `rapidfuzz`). If found with high confidence (>85), it parses the *remainder of the line* to identify valid value candidates (e.g., matching a currency pattern).

### Why this approach? (Comparative Justification)

We selected this **Hybrid Rule-Based approach** over alternative paradigms for the following reasons:

#### 1. vs. Pure Machine Learning (NER/BERT)
-   **Analysis**: Deep Learning models (like LayoutLM or Bi-LSTM CRFs) are powerful but data-hungry.
-   **Why Rejected**: Training a robust NER model requires thousands of labeled examples per insurer. For a specific set of ~5 fields, the engineering overhead of labeling data and managing heavy inference infrastructure outweighs the benefits. Our rule-based approach is **Zero-Shot** (works immediately) and **Interpretable**.

#### 2. vs. Coordinate-Based Parsing (Zonal OCR)
-   **Analysis**: Tools like AWS Textract Queries or localized coordinates work well for rigid forms (e.g., DMV forms).
-   **Why Rejected**: Insurance policies are "flow documents" where content shifts dynamically based on coverage details. A localized approach breaks if margins shift by 2mm or if a paragraph is added. Our logic is **Layout-Agnostic** because it relies on text proximity, not X/Y coordinates.

#### 3. vs. Pure Regex
-   **Analysis**: Standard regex is fast but brittle.
-   **Why Rejected**: A simple typo in a label ("Premum" instead of "Premium") causes a regex to fail silently (False Negative). By layering Fuzzy Matching as a safety net, we achieve the recall of NLP with the precision of Regex.

**Verdict**: The Hybrid approach offers the optimal trade-off between **Precision, Maintainability, and Performance** for high-variance, low-volume business documents.

---

## 5. Fuzzy Matching Design

Variability in insurance documents is non-deterministic. A field formally defined as "Annual Premium" might appear as "Ann. Prem.", "Total Premium", or "Prem Payable". 

### Implementation
The `FuzzyFieldLocator` utilizes the `rapidfuzz` library, specifically the `partial_ratio` algorithm. This algorithm detects the best alignment of a keyword within a longer string (a line of text), which is crucial when labels are embedded in sentences.

### Thresholding
A rigid threshold (e.g., 85/100) is enforced. Matches below this score are discarded as noise. This filtering prevents common words from triggering false field detections.

### Logic
1.  Iterate through document lines.
2.  Calculate similarity score between target keyword and line content.
3.  If score > Threshold:
    -   Scan the line for value candidates (e.g., numeric sequences).
    -   Return the candidate with a penalized confidence score.

---

## 6. Confidence Scoring Mechanism

Downstream consumption of extracted data (e.g., by RPA bots or human verifiers) requires a reliability metric. The `ConfidenceScorer` standardizes this metric.

### Scoring Model

| Extraction Method | Condition | Score Range |
| :--- | :--- | :--- |
| **Regex Match** | Exact pattern match | **0.95 - 1.0** |
| **Fuzzy Match** | High textual similarity (>90) | **0.75 - 0.85** |
| **Fuzzy Match** | Moderate textual similarity (80-90) | **0.60 - 0.75** |
| **No Match** | Field not found | **0.0** |

### Importance
This mechanism allows the calling system to implement "Human-in-the-Loop" workflows. For example, documents with an average confidence score < 0.80 can be routed to a manual review queue, while high-confidence documents are processed automatically (STP - Straight Through Processing).

---

## 7. Edge Case Handling

### Multiple Values
Insurance documents often list multiple monetary figures (Net Premium, Tax, Total Premium). 
*Mitigation*: The pattern regex is designed to be specific to the *final* payable amount (e.g., anchoring on "Total"). Fuzzy logic prioritizes values appearing at the end of a line, which is standard for invoice-style layouts.

### Currency Formatting
Values may appear as `1,000.00`, `1000`, `Rs. 1000`, or `1.000,00` (European style).
*Mitigation*: The `TextPreprocessor` standardizes all numeric captures, stripping currency symbols and normalizing decimal separators before final output.

### Noisy OCR
Scanned documents often introduce artifacts (e.g., `l` instead of `1`).
*Mitigation*: Fuzzy matching tolerates label corruption. Value validation checks (isnumeric) ensure that extracted values conform to expected data types.

---

## 8. Scalability and Production Readiness

### Batch Processing
The stateless design of the `FieldExtractor` allows for massive horizontal scaling. Multiple worker processes can instantiate the parser to process documents in parallel without shared state contention.

### Logging
Structure logging is implemented to capture extraction traces, allowing engineers to debug why a specific field was missed (e.g., "Regex failed, Fuzzy score 75 < Threshold 85").

### OCR Integration
The system seamlessly integrates `pytesseract` and `pdf2image`. It employs a heuristic (text length check) to auto-detect scanned files, ensuring that computational expensive OCR is only invoked when necessary.

---

## 9. Output Schema

The system outputs a strict JSON schema. This structured format decouples the parser from the consumer.

```json
{
  "policy_number": {
    "value": "12345678",
    "confidence": 0.95,
    "method": "regex"
  },
  "net_premium": {
    "value": "22000.00",
    "confidence": 0.95,
    "method": "regex"
  },
  "tax_amount": {
    "value": "3960.00",
    "confidence": 0.92,
    "method": "regex"
  },
  "premium_amount": {
    "value": "25960.00",
    "confidence": 0.82,
    "method": "fuzzy"
  },
  "payment_frequency": {
    "value": "Annual",
    "confidence": 0.95,
    "method": "regex"
  }
}
```

**Rationale**: Including `confidence` and `method` provides transparency/explainability, essential for auditing automated financial processes.

---

## 10. Unit Testing Strategy

A rigorous testing suite ensures reliability.

-   **Test-Driven Validation**: Core patterns are validated against known inputs.
-   **Synthetic Document Tests**: Tests run against artificially generated text blocks simulating various layouts.
-   **Fuzzy Variation Tests**: Specific test cases introduce typos to labels (e.g., "Plicy Num") to verify the robustness of the fuzzy logic.
-   **Null Hypothesis**: Tests verify that unrelated documents yield empty results/zero confidence rather than false positives.

---

## 11. Technology Stack

-   **Language**: Python 3.9+ (Strong ecosystem for text processing).
-   **PDF Ingestion**: `pypdf` (Lightweight, effective for digital PDFs).
-   **OCR**: `pytesseract` (Tesseract Wrapper) + `pdf2image` (Renderer).
-   **Fuzzy Logic**: `rapidfuzz` (Selected for O(N) performance superiority over `fuzzywuzzy`).
-   **Testing**: `unittest` (Standard library, zero-dependency test runner).

---

## 12. Future Improvements

To achieve State-of-the-Art (SOTA) performance:

1.  **Named Entity Recognition (NER)**: Train a spaCy or HuggingFace transformer model to recognize "Premium" entities based on semantic context rather than rule-based proximity.
2.  **LayoutLM Implementation**: Utilize multimodal models (Text + Layout) to understand document structure, improving accuracy on complex tables.
3.  **Confidence Calibration**: Implement logistic regression to calibrate raw confidence scores against ground-truth accuracy rates.
