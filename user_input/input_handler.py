# Lógica para recibir y procesar la entrada del usuario

from flask import request
from dataclasses import dataclass
from typing import List

@dataclass
class UserInput:
    topic: str
    key_points: List[str]
    slides_count: int
    output_format: str = 'pptx'

class InputHandler:
    @staticmethod
    def validate_topic(topic: str) -> bool:
        return bool(topic and len(topic.strip()) > 0)
    
    @staticmethod
    def validate_slides_count(count: int) -> bool:
        return 1 <= count <= 20
    
    @staticmethod
    def validate_key_points(points: List[str]) -> bool:
        return all(len(point.strip()) > 0 for point in points if point)

    @staticmethod
    def get_user_input() -> UserInput:
        """Process and validate user input from the form"""
        topic = request.form.get('topic', '').strip()
        key_points = [p.strip() for p in request.form.get('key_points', '').split('\n') if p.strip()]
        try:
            slides_count = int(request.form.get('slides_count', 5))
        except ValueError:
            slides_count = 5
        
        output_format = request.form.get('output_format', 'pptx').lower()
        
        if not InputHandler.validate_topic(topic):
            raise ValueError("Topic cannot be empty")
        
        if not InputHandler.validate_slides_count(slides_count):
            raise ValueError("Slides count must be between 1 and 20")
        
        if not InputHandler.validate_key_points(key_points):
            raise ValueError("Key points cannot be empty")
        
        return UserInput(
            topic=topic,
            key_points=key_points,
            slides_count=slides_count,
            output_format=output_format
        )
