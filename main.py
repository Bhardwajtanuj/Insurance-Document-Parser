import argparse
import json
import os
import sys

from loader import DocumentLoader
from preprocessor import clean_text
from extractor import FieldExtractor
from patterns import base_patterns, hdfc, lic

def get_patterns(insurer_name: str):
    """
    Factory to get patterns based on insurer name.
    """
    name = insurer_name.lower()
    if name == "hdfc":
        return hdfc.HDFC_FIELDS
    elif name == "lic":
        return lic.LIC_FIELDS
    else:
        print(f"Warning: Unknown insurer '{insurer_name}'. Using base patterns.")
        return base_patterns.BASE_FIELDS

def main():
    parser = argparse.ArgumentParser(description="Insurance Document Parser Engine")
    parser.add_argument("file_path", help="Path to the document (PDF/TXT)")
    parser.add_argument("--insurer", default="base", help="Insurer name (hdfc, lic) for specific patterns")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()

    # 1. Load Document
    print(f"[*] Loading document: {args.file_path}...")
    loader = DocumentLoader()
    try:
        raw_text = loader.load(args.file_path)
    except Exception as e:
        print(f"[!] Error loading file: {e}")
        sys.exit(1)

    # 2. Preprocess
    print("[*] Cleaning text...")
    cleaned_text = clean_text(raw_text)
    
    # 3. Select Patterns
    print(f"[*] Loading patterns for: {args.insurer}...")
    patterns = get_patterns(args.insurer)

    # 4. Extract
    print("[*] Extracting data...")
    extractor = FieldExtractor(patterns)
    results = extractor.extract(cleaned_text)

    # 5. Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*40)
        print(f"Extraction Results ({args.insurer.upper()})")
        print("="*40)
        for field, data in results.items():
            val = data['value'] if data['value'] else "Not Found"
            conf = data['confidence']
            method = data['method']
            print(f"{field:<20} : {val:<20} (Conf: {conf}, Method: {method})")
        print("="*40)

if __name__ == "__main__":
    main()
