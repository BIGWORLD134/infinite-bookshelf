from dataclasses import dataclass
from typing import Dict, Optional, List
import json

@dataclass
class Section:
    title: str
    content: str
    subsections: Dict[str, 'Section']

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'content': self.content,
            'subsections': {k: v.to_dict() for k, v in self.subsections.items()}
        }

@dataclass
class Book:
    title: str
    sections: Dict[str, Section]
    
    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'sections': {k: v.to_dict() for k, v in self.sections.items()}
        }
    
    def to_markdown(self) -> str:
        content = f"# {self.title}\n\n"
        
        def process_section(section: Section, level: int = 1) -> str:
            section_content = f"{'#' * level} {section.title}\n{section.content}\n\n"
            for subsection in section.subsections.values():
                section_content += process_section(subsection, level + 1)
            return section_content
            
        for section in self.sections.values():
            content += process_section(section)
            
        return content

@dataclass
class GenerationStatistics:
    model_name: str
    input_time: float = 0
    output_time: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_time: float = 0

    def get_input_speed(self) -> float:
        return self.input_tokens / self.input_time if self.input_time != 0 else 0

    def get_output_speed(self) -> float:
        return self.output_tokens / self.output_time if self.output_time != 0 else 0

    def add(self, other: 'GenerationStatistics') -> None:
        if not isinstance(other, GenerationStatistics):
            raise TypeError("Can only add GenerationStatistics objects")
        
        self.input_time += other.input_time
        self.output_time += other.output_time
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_time += other.total_time