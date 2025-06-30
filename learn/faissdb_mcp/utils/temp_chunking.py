import json
import re
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="apikey")
model = genai.GenerativeModel("gemini-2.0-flash")

def safe_parse_llm_output(text: str):
    """
    Safely parse LLM output that claims to return a JSON list of strings,
    even if it contains headers like 'Here is the JSON:' or formatting issues.
    """
    # Remove common leading phrases
    text = text.strip()
    prefix_patterns = [
        r'^```json', r'^```', r'^Here is the JSON[:\-\\s]*', r'^JSON[:\-\\s]*'
    ]
    for pattern in prefix_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

    # Remove code block wrappers
    text = text.strip('` \n')

    # Standardize quotes
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")

    # Try JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠️ JSON parsing failed. Attempting regex fallback.")

    # Fallback: extract double-quoted strings (not perfect, but useful)
    matches = re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    cleaned = [m.encode('utf-8').decode('unicode_escape').strip() for m in matches if m.strip()]

    if not cleaned:
        # Final fallback: extract markdown sections
        cleaned = [s.strip() for s in text.split('\n') if s.strip().startswith("###")]

    return cleaned


# Load your Markdown file
with open("NPP.md", "r", encoding="utf-8") as f:
    md_text = f.read()

# Prompt Gemini to semantically split the document
prompt = """
Split the following Notice of Privacy Practices document into semantically meaningful sections.
Each section should start with the heading (e.g., ### Section Name), followed by its corresponding text.

Return the output as a JSON list of strings. Each string should include both the title and its paragraph(s).

Document:
""" + md_text

print("Asking Gemini to split semantically...")
response = model.generate_content(prompt)

try:
    chunks = safe_parse_llm_output(response.text)
    with open("semantic_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Chunked into {len(chunks)} semantic sections.")
except json.JSONDecodeError:
    print("Failed to parse response. Output was:\n", response.text)


