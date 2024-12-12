# Lógica para convertir la presentación a PDF

import os
from typing import Optional
import win32com.client
import pythoncom
from document_management.document_handler import Document, DocumentHandler

class PDFExporter:
    def __init__(self, document_handler: DocumentHandler):
        self.document_handler = document_handler
    
    def _pptx_to_pdf(self, pptx_path: str, pdf_path: str) -> bool:
        """Convert PPTX to PDF using PowerPoint COM automation"""
        try:
            pythoncom.CoInitialize()
            powerpoint = win32com.client.Dispatch("Powerpoint.Application")
            powerpoint.Visible = True
            
            # Open presentation
            presentation = powerpoint.Presentations.Open(pptx_path)
            
            # Save as PDF
            presentation.SaveAs(pdf_path, 32)  # 32 is the PDF format number
            
            # Close
            presentation.Close()
            powerpoint.Quit()
            
            return True
        except Exception as e:
            print(f"Error converting PPTX to PDF: {str(e)}")
            return False
        finally:
            pythoncom.CoUninitialize()
    
    def export_to_pdf(self, presentation_filename: str) -> Optional[Document]:
        """Export a presentation to PDF"""
        # Get the presentation document
        pres_doc = self.document_handler.get_document(presentation_filename)
        if not pres_doc or not os.path.exists(pres_doc.path):
            raise FileNotFoundError(f"Presentation not found: {presentation_filename}")
        
        # Create PDF filename
        pdf_filename = os.path.splitext(presentation_filename)[0] + '.pdf'
        pdf_path = os.path.join(self.document_handler.base_dir, 'pdfs', pdf_filename)
        
        # Convert to PDF
        if self._pptx_to_pdf(pres_doc.path, pdf_path):
            # Create PDF document entry
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            return self.document_handler.save_document(
                content=pdf_content,
                filename=pdf_filename,
                format='pdf'
            )
        
        return None
