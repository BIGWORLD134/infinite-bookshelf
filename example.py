import os
from book_generator import BookGenerator

def main():
    # Initialize generator with API key
    generator = BookGenerator(api_key=os.getenv("GROQ_API_KEY"))
    
    # Generate a book
    book_stream = generator.generate_book(
        topic="The history and impact of artificial intelligence",
        additional_instructions="Focus on recent developments and future implications",
        writing_style="Academic",
        complexity_level="Advanced",
        seed_content="AI has transformed various industries..."
    )
    
    # Process the generation stream
    for item in book_stream:
        if isinstance(item, str):
            print("Progress update:", item)
        elif hasattr(item, 'to_markdown'):
            # It's the final book
            print("\nFinal book content:")
            print(item.to_markdown())
            
            # Save to file
            with open("generated_book.md", "w") as f:
                f.write(item.to_markdown())
        else:
            # It's generation statistics
            print("\nGeneration stats:", item)

if __name__ == "__main__":
    main()