import sys
import os

print("PYTHONPATH:", sys.path)
print("CWD:", os.getcwd())

try:
    from patterns.base_patterns import BASE_FIELDS
    print("[SUCCESS] Imported patterns")
except ImportError as e:
    print(f"[FAIL] Import patterns: {e}")

try:
    from extractor import FieldExtractor
    print("[SUCCESS] Imported extractor")
except ImportError as e:
    print(f"[FAIL] Import extractor: {e}")

try:
    from scorer import ConfidenceScorer
    print("[SUCCESS] Imported scorer")
except ImportError as e:
    print(f"[FAIL] Import scorer: {e}")

from extractor import FieldExtractor
extractor = FieldExtractor(BASE_FIELDS)
print("Extractor instantiated.")

res = extractor.extract("Policy Number: 12345")
print("Extraction result:", res)
