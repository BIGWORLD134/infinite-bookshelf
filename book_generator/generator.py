from typing import Dict, Generator, Union, Optional
import json
from groq import Groq

from .models import Book, Section, GenerationStatistics

class BookGenerator:
    def __init__(self, api_key: str):
        self.groq_client = Groq(api_key=api_key)
        self.default_model = "llama-3.3-70b-specdec"
    
    def generate_book(
        self,
        topic: str,
        additional_instructions: str = "",
        writing_style: str = "Formal",
        complexity_level: str = "Intermediate",
        seed_content: str = "",
    ) -> Generator[Union[str, GenerationStatistics, Book], None, None]:
        """
        Generates a book based on the given parameters.
        Yields progress updates and statistics during generation.
        """
        # Generate title
        title = self._generate_title(topic)
        yield f"Generated title: {title}"

        # Generate structure
        structure_stats, structure = self._generate_structure(
            topic, additional_instructions, writing_style, complexity_level, seed_content
        )
        yield structure_stats
        
        # Parse structure and create book
        book_structure = json.loads(structure)
        book = Book(title=title, sections={})
        
        # Generate content for each section
        total_stats = GenerationStatistics(model_name=self.default_model)
        
        for section_title, section_content in self._flatten_structure(book_structure):
            content_stream = self._generate_section(
                section_title,
                section_content,
                additional_instructions,
                writing_style,
                complexity_level,
                seed_content,
            )
            
            section = Section(title=section_title, content="", subsections={})
            
            for chunk in content_stream:
                if isinstance(chunk, GenerationStatistics):
                    total_stats.add(chunk)
                    yield total_stats
                else:
                    section.content += chunk
            
            book.sections[section_title] = section
            
        yield book

    def _generate_title(self, topic: str) -> str:
        completion = self.groq_client.chat.completions.create(
            model=self.default_model,
            messages=[
                {
                    "role": "system",
                    "content": "Generate suitable book titles for the provided topics. There is only one generated book title! Don't give any explanation or add any symbols, just write the title of the book. The requirement for this title is that it must be between 7 and 25 words long, and it must be attractive enough!",
                },
                {
                    "role": "user",
                    "content": f"Generate a book title for the following topic: {topic}",
                },
            ],
            temperature=0.7,
            max_tokens=100,
        )
        return completion.choices[0].message.content.strip()

    def _generate_structure(
        self,
        topic: str,
        additional_instructions: str,
        writing_style: str,
        complexity_level: str,
        seed_content: str,
    ) -> tuple[GenerationStatistics, str]:
        prompt = f"Write a comprehensive structure for a book about: {topic}"
        if additional_instructions:
            prompt += f"\nAdditional instructions: {additional_instructions}"
        if writing_style:
            prompt += f"\nWriting style: {writing_style}"
        if complexity_level:
            prompt += f"\nComplexity level: {complexity_level}"
        if seed_content:
            prompt += f"\nSeed content: {seed_content}"

        completion = self.groq_client.chat.completions.create(
            model=self.default_model,
            messages=[
                {
                    "role": "system",
                    "content": 'Write in JSON format:\n\n{"Title of section goes here":"Description of section goes here"}',
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )

        stats = GenerationStatistics(
            model_name=self.default_model,
            input_time=completion.usage.prompt_time,
            output_time=completion.usage.completion_time,
            input_tokens=completion.usage.prompt_tokens,
            output_tokens=completion.usage.completion_tokens,
            total_time=completion.usage.total_time,
        )

        return stats, completion.choices[0].message.content

    def _generate_section(
        self,
        title: str,
        description: str,
        additional_instructions: str,
        writing_style: str,
        complexity_level: str,
        seed_content: str,
    ) -> Generator[Union[str, GenerationStatistics], None, None]:
        prompt = f"Generate content for section: {title}\nDescription: {description}"
        if additional_instructions:
            prompt += f"\nAdditional instructions: {additional_instructions}"
        if writing_style:
            prompt += f"\nWriting style: {writing_style}"
        if complexity_level:
            prompt += f"\nComplexity level: {complexity_level}"
        if seed_content:
            prompt += f"\nConsider this seed content: {seed_content}"

        stream = self.groq_client.chat.completions.create(
            model=self.default_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert writer. Generate a long, comprehensive, structured chapter for the section provided. Only output the content.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=8000,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            if x_groq := chunk.x_groq:
                if not x_groq.usage:
                    continue
                usage = x_groq.usage
                yield GenerationStatistics(
                    input_time=usage.prompt_time,
                    output_time=usage.completion_time,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_time=usage.total_time,
                    model_name=self.default_model,
                )

    def _flatten_structure(self, structure: dict) -> list[tuple[str, str]]:
        """Flattens nested structure into list of (title, description) tuples."""
        sections = []
        for title, content in structure.items():
            if isinstance(content, str):
                sections.append((title, content))
            elif isinstance(content, dict):
                sections.extend(self._flatten_structure(content))
        return sections