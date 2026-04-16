def chunk_text(text, size=500):
    # Implement chunking logic
    return [text[i:i+size] for i in range(0, len(text), size)]
