"""
Gemini API client for generating DDR reports.
"""
import os
import google.generativeai as genai
from typing import Dict, Any
import base64


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    SYSTEM_PROMPT = """You are a professional property inspector generating a Detailed Diagnostic Report (DDR).
You have been given two documents: an Inspection Report and a Thermal Images Report.

CRITICAL RULES — FOLLOW STRICTLY:
1. ONLY use facts explicitly stated in the provided documents. Do NOT invent, assume, or infer anything not written.
2. If information is missing, write exactly "Not Available" — never substitute or guess.
3. If two documents conflict on the same fact, explicitly state: "Conflict: [doc1 says X], [doc2 says Y]"
4. Use simple, plain English. Avoid unnecessary technical jargon.
5. Merge duplicate observations — do not repeat the same finding twice.
6. Cite thermal image IDs (e.g. RB02380X) and temperature readings exactly as they appear in the thermal report.
7. Property details (name, address, date) must come verbatim from the inspection form.
8. Never add recommendations not supported by the documented evidence.

Return ONLY a raw JSON object with no markdown, no backticks, no preamble. Structure:
{
  "property_summary": {
    "property_type": "string or Not Available",
    "floors": "string or Not Available",
    "inspection_date": "string or Not Available",
    "inspected_by": "string or Not Available",
    "customer_name": "string or Not Available",
    "address": "string or Not Available",
    "previous_audit": "Yes / No / Not Available",
    "previous_repair": "Yes / No / Not Available",
    "overall_score": "string or Not Available",
    "overview": "2-3 sentence plain-English summary of the main issues"
  },
  "area_observations": [
    {
      "area": "area name e.g. Hall, Master Bedroom",
      "negative_side": "observation on the affected/interior side",
      "positive_side": "observation on the source/exposed side",
      "thermal_data": "thermal image IDs and temperature readings, or Not Available",
      "thermal_image_page": "page number in thermal PDF where image appears, or null"
    }
  ],
  "root_causes": ["cause 1", "cause 2"],
  "severity": {
    "level": "Critical | High | Medium | Low",
    "reasoning": "reasoning based only on documented evidence"
  },
  "recommended_actions": ["action 1", "action 2"],
  "additional_notes": "string or Not Available",
  "missing_information": ["item 1", "item 2"]
}"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
        """
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it as an environment variable or pass it directly.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=self.SYSTEM_PROMPT
        )
    
    def build_prompt(self, inspection_text: str, thermal_text: str) -> str:
        """
        Build the user prompt with extracted text.
        
        Args:
            inspection_text: Text from inspection report
            thermal_text: Text from thermal images report
            
        Returns:
            Formatted prompt string
        """
        return f"""Please analyze the following two documents and generate a Detailed Diagnostic Report.

=== INSPECTION REPORT ===
{inspection_text}

=== THERMAL IMAGES REPORT ===
{thermal_text}

Generate the DDR following the structure specified in the system prompt."""
    
    def generate_report(
        self, 
        inspection_pdf_bytes: bytes,
        thermal_pdf_bytes: bytes,
        inspection_text: str,
        thermal_text: str
    ) -> str:
        """
        Generate DDR report using Gemini API.
        
        Args:
            inspection_pdf_bytes: Raw bytes of inspection PDF
            thermal_pdf_bytes: Raw bytes of thermal PDF
            inspection_text: Extracted text from inspection PDF
            thermal_text: Extracted text from thermal PDF
            
        Returns:
            JSON string response from Gemini
        """
        # Build prompt
        prompt = self.build_prompt(inspection_text, thermal_text)
        
        # Convert PDFs to base64
        inspection_base64 = base64.b64encode(inspection_pdf_bytes).decode('utf-8')
        thermal_base64 = base64.b64encode(thermal_pdf_bytes).decode('utf-8')
        
        # Prepare content parts - Gemini expects parts as a list
        # Text and PDFs can be mixed in the parts list
        parts = [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": inspection_base64
                }
            },
            {
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": thermal_base64
                }
            }
        ]
        
        # Generate content
        response = self.model.generate_content(parts)
        
        return response.text

