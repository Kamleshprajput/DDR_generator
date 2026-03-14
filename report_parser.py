"""
Report parsing utilities for DDR reports.
"""
import json
from typing import Dict, Any, List, Optional


class DDRReport:
    """Structured DDR Report data class."""
    
    def __init__(self, data: Dict[str, Any]):
        self.property_summary = data.get('property_summary', {})
        self.area_observations = data.get('area_observations', [])
        self.root_causes = data.get('root_causes', [])
        self.severity = data.get('severity', {})
        self.recommended_actions = data.get('recommended_actions', [])
        self.additional_notes = data.get('additional_notes', 'Not Available')
        self.missing_information = data.get('missing_information', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'property_summary': self.property_summary,
            'area_observations': self.area_observations,
            'root_causes': self.root_causes,
            'severity': self.severity,
            'recommended_actions': self.recommended_actions,
            'additional_notes': self.additional_notes,
            'missing_information': self.missing_information
        }


def parse_report(response_text: str) -> DDRReport:
    """
    Parse Gemini's JSON response into DDRReport object.
    
    Args:
        response_text: Raw response text from Gemini
        
    Returns:
        DDRReport object
    """
    # Clean the response - remove markdown code blocks if present
    cleaned = response_text.strip()
    
    # Remove ```json or ``` markers
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:].strip()
    
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3].strip()
    
    # Try to extract JSON if there's any preamble
    json_start = cleaned.find('{')
    json_end = cleaned.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        cleaned = cleaned[json_start:json_end]
    
    try:
        data = json.loads(cleaned)
        return DDRReport(data)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse Gemini response as JSON. "
            f"Error: {e}. Raw response (first 500 chars): {response_text[:500]}"
        )

