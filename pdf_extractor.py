"""
PDF extraction module for extracting text and images from PDF files.
"""
import io
from typing import List, Dict, Tuple
import PyPDF2
import pdfplumber
from PIL import Image
import base64


class ExtractedImage:
    """Represents an extracted image from a PDF."""
    def __init__(self, page_num: int, base64_data: str, mime_type: str):
        self.page_num = page_num
        self.base64_data = base64_data
        self.mime_type = mime_type


class PDFExtractor:
    """Extracts text and images from PDF files."""
    
    @staticmethod
    def extract_text(pdf_file) -> str:
        """
        Extract text from PDF using pdfplumber (better text extraction).
        
        Args:
            pdf_file: File-like object or bytes
            
        Returns:
            Extracted text as string
        """
        text_parts = []
        
        try:
            # Try pdfplumber first (better for text extraction)
            if hasattr(pdf_file, 'read'):
                pdf_file.seek(0)
                pdf_bytes = pdf_file.read()
            else:
                pdf_bytes = pdf_file
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            print(f"Warning: pdfplumber extraction failed: {e}")
            # Fallback to PyPDF2
            try:
                if hasattr(pdf_file, 'read'):
                    pdf_file.seek(0)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                else:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            except Exception as e2:
                print(f"Error: Both extraction methods failed: {e2}")
                return ""
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def extract_images(pdf_file) -> List[ExtractedImage]:
        """
        Extract images from PDF pages.
        
        Args:
            pdf_file: File-like object or bytes
            
        Returns:
            List of ExtractedImage objects
        """
        images = []
        
        try:
            if hasattr(pdf_file, 'read'):
                pdf_file.seek(0)
                pdf_bytes = pdf_file.read()
            else:
                pdf_bytes = pdf_file
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    if '/XObject' in page.get('/Resources', {}):
                        xobject = page['/Resources']['/XObject'].get_object()
                        
                        for obj in xobject:
                            if xobject[obj]['/Subtype'] == '/Image':
                                try:
                                    img_obj = xobject[obj]
                                    img_data = img_obj.get_data()
                                    
                                    # Determine image format
                                    if '/Filter' in img_obj:
                                        filter_type = img_obj['/Filter']
                                        if '/DCTDecode' in filter_type or filter_type == '/DCTDecode':
                                            mime_type = 'image/jpeg'
                                        elif '/FlateDecode' in filter_type or filter_type == '/FlateDecode':
                                            mime_type = 'image/png'
                                        else:
                                            mime_type = 'image/jpeg'  # Default
                                    else:
                                        mime_type = 'image/jpeg'
                                    
                                    # Convert to base64
                                    base64_data = base64.b64encode(img_data).decode('utf-8')
                                    
                                    images.append(ExtractedImage(
                                        page_num=page_num,
                                        base64_data=base64_data,
                                        mime_type=mime_type
                                    ))
                                except Exception as e:
                                    print(f"Warning: Failed to extract image from page {page_num}: {e}")
                                    continue
                except Exception as e:
                    print(f"Warning: Failed to process page {page_num}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Warning: Image extraction failed: {e}")
            # Return empty list - text extraction will still work
        
        return images
    
    @staticmethod
    def extract_all(pdf_file) -> Tuple[str, List[ExtractedImage]]:
        """
        Extract both text and images from PDF.
        
        Args:
            pdf_file: File-like object or bytes
            
        Returns:
            Tuple of (text, images)
        """
        text = PDFExtractor.extract_text(pdf_file)
        images = PDFExtractor.extract_images(pdf_file)
        return text, images

