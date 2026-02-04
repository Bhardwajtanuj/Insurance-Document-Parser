import re
import logging
from rapidfuzz import fuzz
from scorer import ConfidenceScorer

logger = logging.getLogger(__name__)


class FieldExtractor:
    def __init__(self, patterns):
        """
        Initialize with a specific pattern set (dict).
        """
        self.patterns = patterns

    def extract(self, text: str) -> dict:
        """
        Extracts fields from text based on configured patterns.
        Returns a dict with value and confidence for each field.
        """
        results = {}
        lines = text.split("\n")

        for field_name, config in self.patterns.items():
            extracted_data = {
                "value": None,
                "confidence": 0.0,
                "method": "none"
            }

            # Strategy 1: Strict Regex Match
            # We search the whole text first for multi-line regex capabilities if needed
            match = re.search(config["regex"], text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Assuming the last group is the value we want. 
                # Our patterns use capturing groups: (Label)...(Value)
                # So groups()[-1] should be the value.
                value = match.groups()[-1].strip()
                extracted_data = {
                    "value": value,
                    "confidence": ConfidenceScorer.calculate("regex"),
                    "method": "regex"
                }
            
            # Strategy 2: Fuzzy Logic Fallback
            if not extracted_data["value"]:
                fuzzy_res = self._fuzzy_search(lines, config["keywords"])
                if fuzzy_res:
                    extracted_data = fuzzy_res

            results[field_name] = extracted_data

        return results

    def _fuzzy_search(self, lines: list, keywords: list) -> dict:
        """
        Scans lines for fuzzy matches of keywords.
        Returns the best match or None.
        """
        best_candidate = None
        best_score = 0
        best_method_score = 0

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            for keyword in keywords:
                # Use partial_ratio to find keyword inside a sentence
                score = fuzz.partial_ratio(keyword.lower(), line.lower())
                
                # Threshold for considering it a "match" of the label
                if score >= 85:
                    # If we found the label, look for a value nearby (in the same line)
                    # This is a heuristic: usually "Premium: 1000"
                    
                    # Extract potential values (numbers/money) from the *same line*
                    # This is a simple heuristic; can be expanded to looking at next line.
                    numbers = re.findall(r"(?:Rs\.|₹)?\s?([\d,]+\.?\d*)", line)
                    
                    # Filter out purely whitespace or empty matches
                    valid_values = [n for n in numbers if n.strip() and any(c.isdigit() for c in n)]
                    
                    if valid_values:
                        # Take the last number found in line (often the value is at end)
                        # or the one that is not the label itself if numeric.
                        
                        # Confidence Score Calculation
                        # Use the centralized scorer
                        confidence = ConfidenceScorer.calculate("fuzzy", score)
                        
                        if confidence > best_score:
                            best_score = confidence
                            best_candidate = valid_values[-1] # assumption
                            best_method_score = score
                            
        if best_candidate:
            return {
                "value": best_candidate,
                "confidence": best_score,
                "method": f"fuzzy (score: {best_method_score})"
            }
        return None
