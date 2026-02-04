import re

def clean_text(text: str) -> str:
    """
    Cleans and normalizes text from PDF/Images.
    1. Replaces non-breaking spaces.
    2. Collapses multiple spaces.
    3. Standardizes currency symbols (optional validation step).
    """
    if not text:
        return ""
        
    # Replace non-breaking space
    text = text.replace("\xa0", " ")
    
    # Remove control characters except newlines
    text = "".join(ch for ch in text if ch.isprintable() or ch == '\n')

    # Normalize whitespace (but keep newlines for context)
    # Convert multiple spaces to single space, but preserve newlines
    lines = text.split('\n')
    cleaned_lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
    text = "\n".join(cleaned_lines)
    
    return text

def normalize_amount(amount_str: str) -> float:
    """
    Converts currency string '25,000.00' to float 25000.00
    """
    if not amount_str:
        return 0.0
    
    # Remove currency symbols and commas
    cleaned = re.sub(r"[^\d.]", "", amount_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
