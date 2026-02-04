import os
import sys
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class DocumentLoader:
    """
    Handles loading of documents from various formats (Text, PDF).
    Supports OCR for scanned PDFs.
    """

    def load(self, file_path: str) -> str:
        """
        Detects file type and extracts text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            return self._load_txt(file_path)
        elif ext == ".pdf":
            return self._load_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _load_txt(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_pdf(self, file_path):
        if PdfReader is None:
            raise ImportError("pypdf is required for PDF support. Install it via 'pip install pypdf'")
        
        reader = PdfReader(file_path)
        text = []
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text.append(content)
        
        full_text = "\n".join(text)

        # Check for scanned PDF (empty or very little text)
        if len(full_text.strip()) < 50:
            print("[!] Detected scanned/image PDF. Attempting OCR...")
            return self._ocr_pdf(file_path)
        
        return full_text

    def _ocr_pdf(self, file_path):
        if not OCR_AVAILABLE:
            print("[!] OCR dependencies not found (pytesseract/pdf2image).")
            print("    Please install Tesseract-OCR and Poppler.")
            return ""

        try:
            # Convert PDF to images
            # Note: poppler_path might need to be configured if not in PATH
            images = convert_from_path(file_path)
            
            ocr_text = []
            for i, image in enumerate(images):
                print(f"    Processing page {i+1} with OCR...")
                page_text = pytesseract.image_to_string(image)
                ocr_text.append(page_text)
            
            return "\n".join(ocr_text)

        except Exception as e:
            print(f"[!] OCR Failed: {e}")
            print("    Ensure Tesseract and Poppler are installed and in System PATH.")
            return ""
