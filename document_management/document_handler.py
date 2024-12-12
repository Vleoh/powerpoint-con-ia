# Lógica para manejar la gestión de documentos

import os
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Document:
    filename: str
    path: str
    created_at: datetime
    format: str
    size: int

class DocumentHandler:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for dir_name in ['presentations', 'pdfs', 'temp']:
            dir_path = os.path.join(self.base_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
    
    def save_document(self, content: bytes, filename: str, format: str) -> Document:
        """Save a document to the appropriate directory"""
        # Normalize format and determine directory
        format = format.lower()
        dir_name = 'presentations' if format == 'pptx' else 'pdfs'
        
        # Ensure filename has correct extension
        if not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"
        
        # Create full path
        file_path = os.path.join(self.base_dir, dir_name, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create and return document metadata
        return Document(
            filename=filename,
            path=file_path,
            created_at=datetime.now(),
            format=format,
            size=os.path.getsize(file_path)
        )
    
    def list_documents(self, format: Optional[str] = None) -> List[Document]:
        """List all documents, optionally filtered by format"""
        documents = []
        
        for dir_name in ['presentations', 'pdfs']:
            dir_path = os.path.join(self.base_dir, dir_name)
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                file_format = filename.split('.')[-1].lower()
                if format and file_format != format.lower():
                    continue
                
                file_path = os.path.join(dir_path, filename)
                documents.append(Document(
                    filename=filename,
                    path=file_path,
                    created_at=datetime.fromtimestamp(os.path.getctime(file_path)),
                    format=file_format,
                    size=os.path.getsize(file_path)
                ))
        
        return sorted(documents, key=lambda x: x.created_at, reverse=True)
    
    def get_document(self, filename: str) -> Optional[Document]:
        """Retrieve a specific document by filename"""
        for doc in self.list_documents():
            if doc.filename == filename:
                return doc
        return None
    
    def delete_document(self, filename: str) -> bool:
        """Delete a document by filename"""
        doc = self.get_document(filename)
        if doc and os.path.exists(doc.path):
            os.remove(doc.path)
            return True
        return False

def manage_documents():
    # Aquí irá el código para gestionar los documentos
    pass
