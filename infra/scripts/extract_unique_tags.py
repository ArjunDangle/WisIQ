import json
from pathlib import Path

# Step up 3 levels: scripts -> infra -> WisIQ
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = BASE_DIR / "data" / "processed" / "validation_report.json"

def get_unique_tags():
    if not REPORT_PATH.exists():
        print(f"Error: Could not find the validation report at {REPORT_PATH}")
        return

    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        report = json.load(f)

    unique_tags = set()

    # Iterate through every file logged in the report
    file_details = report.get("file_details", {})
    for filepath, details in file_details.items():
        if "html_tags" in details:
            # Add all the keys (the tag names) to our set
            unique_tags.update(details["html_tags"].keys())

    # Convert the set to a sorted list
    unique_tags_array = sorted(list(unique_tags))

    print(f"Found {len(unique_tags_array)} unique structural tags in the corpus:\n")
    print(json.dumps(unique_tags_array, indent=4))

if __name__ == "__main__":
    get_unique_tags()