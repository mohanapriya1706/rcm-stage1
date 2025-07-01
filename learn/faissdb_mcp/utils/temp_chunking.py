import os
import json
import re
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Load environment variables
load_dotenv('gemini.env', override=True)
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def safe_parse_llm_output(text: str):
    """
    Safely parse LLM output that claims to return a JSON list of strings,
    even if it contains headers or formatting issues.
    """
    text = text.strip()

    # Remove common headers or code block markers
    prefix_patterns = [
        r'```json', r'```', r'Here is the JSON[:\-\\s]*', r'JSON[:\-\\s]*'
    ]
    for pattern in prefix_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove leftover backticks and whitespace
    text = text.strip('` \n')

    # Replace curly quotes with straight quotes
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")

    # Try direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.warning(" JSON parsing failed. Attempting regex fallback.")

    # Fallback: extract quoted strings
    matches = re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    cleaned = [m.encode('utf-8').decode('unicode_escape').strip() for m in matches if m.strip()]

    if cleaned:
        return cleaned

    # Final fallback: use markdown-style headers
    return [s.strip() for s in text.split('\n') if s.strip().startswith("###")]

def split_markdown_semantically(input_path: str, output_path: str):
    """
    Split a markdown file into semantically meaningful sections using Gemini,
    and save the result as a JSON list of objects like: { "chunk": "..." }
    """
    with open(input_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    prompt = f"""
Split the following Notice of Privacy Practices document into semantically meaningful sections.
Each section should start with the heading (e.g., ### Section Name), followed by its corresponding text.

Return the output as a JSON list of strings. Each string should include both the title and its paragraph(s).

Document:
{md_text}
"""

    logging.info("Asking Gemini to split semantically...")
    response = model.generate_content(prompt)

    # Handle different Gemini output formats
    content = getattr(response, 'text', None) or getattr(response, 'parts', [])[0].text

    try:
        raw_chunks = safe_parse_llm_output(content)

        # Wrap each string in a dictionary
        structured_chunks = [{"chunk": chunk} for chunk in raw_chunks]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structured_chunks, f, indent=2)

        logging.info(f"Chunked into {len(structured_chunks)} semantic sections.")
    except Exception as e:
        logging.error("Failed to parse Gemini response.")
        logging.debug("Response text:\n" + content)
        raise e

if __name__ == "__main__":
    INPUT_FILE = "NPP.md"
    OUTPUT_FILE = "semantic_chunks.json"
    split_markdown_semantically(INPUT_FILE, OUTPUT_FILE)
