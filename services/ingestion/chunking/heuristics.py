import re

def classify_content(text: str) -> str:
    """
    Evaluates the raw text and categorizes it logically.
    """
    # 1. Check for Code Blocks
    # If the text has fenced code blocks, we calculate the density of code vs text.
    code_matches = list(re.finditer(r'```[\s\S]*?```', text))
    if code_matches:
        code_length = sum(len(m.group(0)) for m in code_matches)
        # If more than 40% of this chunk is code, classify it as a code block
        if code_length / max(len(text), 1) > 0.4:
            return "code_block"
            
    # 2. Check for Markdown Tables
    # Matches typical MD table syntax: | Header | Header |\n|---|---|
    if re.search(r'\|.*\|.*\n\s*\|[\s\-\|]+\|', text):
        return "table"
        
    # 3. Default Fallback
    return "text"