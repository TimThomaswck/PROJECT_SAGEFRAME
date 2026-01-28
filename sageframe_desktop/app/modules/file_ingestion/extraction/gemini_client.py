"""Gemini Vision Client for document image extraction."""

from typing import Optional, Dict, Any
import base64
from pathlib import Path

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from app.modules.ai_copilot.gemini_integration import get_gemini_api_key, configure_gemini


class GeminiVisionClient:
    """Gemini-based vision client for document extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini Vision client.
        
        Args:
            api_key: Gemini API key (if None, retrieves from keyring)
        """
        self.api_key = api_key or get_gemini_api_key()
        if not GENAI_AVAILABLE:
            raise ImportError("google-generativeai not installed")
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=self.api_key)
    
    async def extract_document(
        self, 
        image_path: str, 
        mode: str = "note"
    ) -> Dict[str, Any]:
        """Extract content from document image.
        
        Args:
            image_path: Path to image file
            mode: Extraction mode ("bill" or "note")
            
        Returns:
            Dict with extracted content and structured fields
        """
        # Read image file
        image_data = self._load_image(image_path)
        
        # Generate prompt based on mode
        if mode == "bill":
            prompt = self._get_bill_prompt()
        else:
            prompt = self._get_note_prompt()
        
        # Create model and generate response
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content([prompt, image_data])
        
        if not response or not response.text:
            return {
                "raw_text": None,
                "structured_fields": None,
                "error": "No response from Gemini"
            }
        
        extracted_text = response.text.strip()
        
        # For bill mode, parse structured fields
        structured_fields = None
        if mode == "bill":
            structured_fields = self._parse_bill_response(extracted_text)
        
        return {
            "raw_text": extracted_text,
            "structured_fields": structured_fields,
            "mode": mode,
            "provider": "gemini_vision"
        }
    
    def _load_image(self, image_path: str):
        """Load image file for Gemini API."""
        path = Path(image_path)
        
        # Determine MIME type
        suffix = path.suffix.lower()
        mime_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif'
        }
        mime_type = mime_type_map.get(suffix, 'image/jpeg')
        
        # Upload file to Gemini
        uploaded_file = genai.upload_file(image_path, mime_type=mime_type)
        return uploaded_file
    
    def _get_bill_prompt(self) -> str:
        """Get prompt for bill/invoice extraction."""
        return """You are a document extraction assistant. Analyze this bill/invoice/receipt image and extract the following information:

1. **Vendor/Company Name**: The name of the business or vendor
2. **Items**: List all items/services with their individual prices
3. **Subtotal**: Subtotal amount (if available)
4. **Tax**: Tax amount (if available)
5. **Total Price**: Final total amount
6. **Date**: Transaction date

Format your response as follows:

**VENDOR:**
[Vendor name]

**DATE:**
[Date in YYYY-MM-DD format if possible, or as written]

**ITEMS:**
- [Item 1]: [Price]
- [Item 2]: [Price]
...

**SUBTOTAL:** [Amount]
**TAX:** [Amount]
**TOTAL:** [Total amount]

**ADDITIONAL NOTES:**
[Any other relevant information from the document]

If any information is not visible or unclear, write "Not found" or "Not clear"."""
    
    def _get_note_prompt(self) -> str:
        """Get prompt for generic note/document extraction."""
        return """You are a document extraction assistant. Please read and transcribe all text content from this image.

Provide:
1. **Main Content**: All visible text, preserving structure and formatting where possible
2. **Document Type**: What type of document this appears to be (if identifiable)
3. **Key Information**: Highlight any important dates, names, amounts, or key points

Format your response clearly and preserve the document's organization."""
    
    def _parse_bill_response(self, response_text: str) -> Dict[str, Any]:
        """Parse structured fields from bill extraction response.
        
        Args:
            response_text: Gemini response text
            
        Returns:
            Dict with structured fields
        """
        fields = {
            "vendor": None,
            "date": None,
            "items": [],
            "subtotal": None,
            "tax": None,
            "total": None,
            "notes": None
        }
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Detect sections
            if '**VENDOR:**' in line or 'VENDOR:' in line_upper:
                current_section = 'vendor'
                # Try to extract vendor from same line
                if ':' in line:
                    vendor_part = line.split(':', 1)[1].strip()
                    if vendor_part and vendor_part not in ['Not found', 'Not clear', '[Vendor name]']:
                        fields['vendor'] = vendor_part
                continue
            elif '**DATE:**' in line or 'DATE:' in line_upper:
                current_section = 'date'
                if ':' in line:
                    date_part = line.split(':', 1)[1].strip()
                    if date_part and date_part not in ['Not found', 'Not clear', '[Date in YYYY-MM-DD format if possible, or as written]']:
                        fields['date'] = date_part
                continue
            elif '**ITEMS:**' in line or 'ITEMS:' in line_upper:
                current_section = 'items'
                continue
            elif '**SUBTOTAL:**' in line or 'SUBTOTAL:' in line_upper:
                current_section = 'subtotal'
                if ':' in line:
                    subtotal_part = line.split(':', 1)[1].strip()
                    if subtotal_part and subtotal_part not in ['Not found', 'Not clear', '[Amount]']:
                        fields['subtotal'] = subtotal_part
                continue
            elif '**TAX:**' in line or 'TAX:' in line_upper:
                current_section = 'tax'
                if ':' in line:
                    tax_part = line.split(':', 1)[1].strip()
                    if tax_part and tax_part not in ['Not found', 'Not clear', '[Amount]']:
                        fields['tax'] = tax_part
                continue
            elif '**TOTAL:**' in line or 'TOTAL:' in line_upper:
                current_section = 'total'
                if ':' in line:
                    total_part = line.split(':', 1)[1].strip()
                    if total_part and total_part not in ['Not found', 'Not clear', '[Total amount]']:
                        fields['total'] = total_part
                continue
            elif '**ADDITIONAL NOTES:**' in line or 'ADDITIONAL NOTES:' in line_upper:
                current_section = 'notes'
                continue
            
            # Parse content based on current section
            if not line_stripped:
                continue
            
            if current_section == 'vendor' and not fields['vendor']:
                if line_stripped not in ['Not found', 'Not clear', '[Vendor name]']:
                    fields['vendor'] = line_stripped
            elif current_section == 'date' and not fields['date']:
                if line_stripped not in ['Not found', 'Not clear']:
                    fields['date'] = line_stripped
            elif current_section == 'items':
                # Parse item lines (format: "- Item: Price" or "Item: Price")
                if line_stripped.startswith('-') or line_stripped.startswith('•'):
                    item_text = line_stripped[1:].strip()
                    if item_text and item_text not in ['Not found', 'Not clear']:
                        fields['items'].append(item_text)
            elif current_section == 'notes':
                if fields['notes'] is None:
                    fields['notes'] = line_stripped
                else:
                    fields['notes'] += '\n' + line_stripped
        
        return fields


async def extract_with_gemini(image_path: str, mode: str = "note") -> Dict[str, Any]:
    """Convenience function to extract document using Gemini.
    
    Args:
        image_path: Path to image file
        mode: Extraction mode ("bill" or "note")
        
    Returns:
        Dict with extraction results
    """
    try:
        client = GeminiVisionClient()
        return await client.extract_document(image_path, mode)
    except Exception as e:
        return {
            "raw_text": None,
            "structured_fields": None,
            "error": str(e)
        }
