# Lógica para generar texto y sugerencias visuales

from typing import List, Dict, Optional
from dataclasses import dataclass
from rag.rag_handler import RAGHandler
import traceback
import json

@dataclass
class SlideContent:
    """Represents the content of a single slide"""
    title: str
    content: List[str]
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert SlideContent to dictionary"""
        return {
            'title': self.title,
            'content': self.content,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SlideContent':
        """Create SlideContent from dictionary"""
        return cls(
            title=data.get('title', ''),
            content=data.get('content', []),
            notes=data.get('notes', '')
        )

    def __str__(self) -> str:
        """String representation for debugging"""
        return f"SlideContent(title='{self.title}', content={self.content}, notes='{self.notes}')"
    
    def format_bullet_points(self, content: List[str]) -> List[str]:
        """Format content as bullet points"""
        return [f"• {point}" for point in content if point.strip()]

class ContentGenerator:
    def __init__(self, rag_handler: RAGHandler):
        self.rag_handler = rag_handler
    
    def generate_title_slide(self, topic: str) -> SlideContent:
        """Generate content for the title slide"""
        return SlideContent(
            title=topic,
            content=["Presentación generada automáticamente"],
            notes="Slide de título principal"
        )
    
    def generate_content(self, topic: str) -> List[Dict]:
        """Generar contenido basado en el tema"""
        raw_content = self.rag_handler.retrieve_information(topic, generate=True)

        # Procesar el contenido en secciones
        sections = []  # Aquí se debe procesar el contenido en secciones
        lines = raw_content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('Sección'):
                if current_section:
                    sections.append(current_section)
                current_section = {'title': line, 'content': []}
            else:
                if current_section:
                    current_section['content'].append(line)

        if current_section:
            sections.append(current_section)  # Agregar última sección si existe

        # Crear diapositivas a partir de las secciones procesadas
        slides = []
        for section in sections:
            slide = SlideContent(
                title=section['title'],
                content=section['content']
            )
            slides.append(slide.to_dict())  # Usar to_dict para convertir a dict

        return slides
    
    def format_bullet_points(self, content: List[str]) -> List[str]:
        """Format content as bullet points"""
        return [f"• {point}" for point in content if point.strip()]
