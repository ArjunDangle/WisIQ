import os
import re
import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any

# Step up 3 levels: scripts -> infra -> WisIQ
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "product-categories"
REPORT_PATH = BASE_DIR / "data" / "processed" / "validation_report.json"

# A strict list of structural/formatting HTML tags.
TARGET_HTML_TAGS = {
    "br", "div", "span", "p", "img", "table", "thead", "tbody", 
    "tr", "th", "td", "strong", "em", "sub", "sup", "details", 
    "summary", "center", "font", "iframe", "script", "style",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "ul", "ol", "li"
}

def validate_markdown_file(filepath: Path) -> Dict[str, Any]:
    """Scans a single markdown file for structural anomalies and extracts actual HTML tags."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except UnicodeDecodeError:
        return {"issues": ["CRITICAL: Non-UTF-8 encoding detected."], "html_tags": {}}

    # 1. Structural Checks
    h1_matches = re.findall(r'^#\s+.+$', content, re.MULTILINE)
    if len(h1_matches) > 1:
        issues.append(f"Multiple H1 headers found: {len(h1_matches)}. (Expected exactly 1)")
    elif len(h1_matches) == 0:
        issues.append("Missing H1 root header.")

    # 2. Code Block Integrity (Strictly checking for closures only)
    code_block_ticks = re.findall(r'^```', content, re.MULTILINE)
    if len(code_block_ticks) % 2 != 0:
        issues.append("Unclosed code block detected (odd number of ```).")

    # 3. HTML Tag Extraction & Contamination Check (Filtered for actual HTML)
    raw_tags = re.findall(r'</?([a-zA-Z0-9]+)[^>]*>', content)
    
    html_tags_counter = Counter([
        tag.lower() for tag in raw_tags if tag.lower() in TARGET_HTML_TAGS
    ])
    
    total_tags = sum(html_tags_counter.values())
    
    if total_tags > 10:
         issues.append(f"Heavy HTML contamination detected: {total_tags} structural tags.")

    # 4. Table Formatting (Basic delimiter check)
    for i, line in enumerate(lines):
        if re.match(r'\|[-:]+[-| :]*\|', line):
            header_cols = len(lines[i-1].split('|')) - 2 if i > 0 else 0
            delim_cols = len(line.split('|')) - 2
            if header_cols != delim_cols and header_cols > 0:
                issues.append(f"Table column mismatch near line {i}: Header has {header_cols}, Delimiter has {delim_cols}.")

    return {
        "issues": issues,
        "html_tags": dict(html_tags_counter)
    }

def run_audit():
    """Iterates through the corpus and generates a global audit report."""
    print(f"Scanning directory: {RAW_DATA_DIR}")
    
    if not RAW_DATA_DIR.exists():
        print("Error: Raw data directory not found. Ensure you are running from the project root.")
        return

    audit_report = {
        "total_files_scanned": 0,
        "files_passed": 0,
        "files_with_issues": 0,
        "file_details": {}
    }

    for md_file in RAW_DATA_DIR.rglob("*.md"):
        audit_report["total_files_scanned"] += 1
        relative_path = str(md_file.relative_to(RAW_DATA_DIR))
        
        result = validate_markdown_file(md_file)
        
        has_issues = len(result["issues"]) > 0
        has_tags = len(result["html_tags"]) > 0

        if not has_issues:
            audit_report["files_passed"] += 1
        else:
            audit_report["files_with_issues"] += 1
            
        if has_issues or has_tags:
            audit_report["file_details"][relative_path] = {}
            if has_issues:
                audit_report["file_details"][relative_path]["issues"] = result["issues"]
            if has_tags:
                audit_report["file_details"][relative_path]["html_tags"] = result["html_tags"]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=4)
        
    print(f"\nAudit complete. Scanned {audit_report['total_files_scanned']} files.")
    print(f"Passed: {audit_report['files_passed']} | Failed: {audit_report['files_with_issues']}")
    print(f"Report generated at: {REPORT_PATH}")

if __name__ == "__main__":
    run_audit()