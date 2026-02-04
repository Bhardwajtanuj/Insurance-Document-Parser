@echo off
echo ==========================================
echo Running HDFC Sample Extraction...
echo ==========================================
python main.py "tests/sample_docs/hdfc_sample.txt" --insurer hdfc

echo.
echo ==========================================
echo Running Unit Tests...
echo ==========================================
python -m unittest discover tests

pause
