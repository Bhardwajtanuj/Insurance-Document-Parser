class ConfidenceScorer:
    """
    Centralized logic for calculating confidence scores.
    """
    
    @staticmethod
    def calculate(method: str, match_quality: float = 100.0) -> float:
        """
        Determines confidence based on extraction method and quality.
        match_quality: 0-100 scale (e.g. fuzz ratio)
        """
        if method == "regex":
            # Regex is deterministic and high precision
            return 0.95
        
        if method == "fuzzy":
            # Fuzzy usually implies some uncertainty.
            # We scale the match quality (0-100) to a 0-1.0 confidence.
            # But even a perfect fuzzy match of a keyword might yield a wrong value if the document structure is weird.
            # So we cap it at 0.85
            normalized_score = match_quality / 100.0
            return round(normalized_score * 0.85, 2)
            
        return 0.0
