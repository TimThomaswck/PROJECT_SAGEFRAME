"""Field parsing utilities for extracting structured data from OCR text."""

import re
from typing import Dict, Optional
from datetime import datetime


def parse_bill_fields(text: str) -> Dict[str, Optional[str]]:
    """Parse bill/invoice fields from OCR text.
    
    Extracts:
    - amount: monetary value (e.g., $123.45, USD 100.00)
    - due_date: date strings
    - vendor: company/vendor name heuristics
    
    Returns dict with extracted fields or None values if not found.
    """
    if not text:
        return {"amount": None, "due_date": None, "vendor": None}
    
    result = {
        "amount": _extract_amount(text),
        "due_date": _extract_date(text),
        "vendor": _extract_vendor(text),
    }
    return result


def _extract_amount(text: str) -> Optional[str]:
    """Extract monetary amount from text."""
    # Look for patterns like $123.45, USD 100.00, Total: $50.00, etc.
    patterns = [
        r'(?:total|amount|balance|due|subtotal)[:\s]*[\$]?([\d,]+\.?\d{0,2})',
        r'[\$]([\d,]+\.?\d{2})',
        r'(?:USD|CAD|EUR)\s*([\d,]+\.?\d{0,2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", "")
    return None


def _extract_date(text: str) -> Optional[str]:
    """Extract date from text (due date, invoice date, etc.)."""
    # Look for common date patterns
    patterns = [
        r'(?:due|payment\s+due|invoice\s+date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:due|payment\s+due|invoice\s+date)[:\s]*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})',
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Try to normalize date format
            try:
                # Attempt parse and reformat
                for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
                    try:
                        dt = datetime.strptime(date_str.replace(",", ""), fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            except Exception:
                pass
            return date_str
    return None


def _extract_vendor(text: str) -> Optional[str]:
    """Extract vendor/company name from top of document."""
    # Simple heuristic: first non-empty line that looks like a company name
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        # Return first line that's not a date or number-heavy
        for line in lines[:5]:
            if len(line) > 3 and not re.match(r'^\d', line):
                return line
    return None
