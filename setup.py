"""
Setup script for DDR Report Generator (optional, for package installation)
"""
from setuptools import setup, find_packages

setup(
    name="ddr-report-generator",
    version="1.0.0",
    description="DDR Report Generator using Streamlit and Gemini AI",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.31.0",
        "google-generativeai>=0.3.2",
        "PyPDF2>=3.0.1",
        "pdfplumber>=0.10.3",
        "Pillow>=10.2.0",
        "pdf2image>=1.16.3",
        "reportlab>=4.0.7",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)

