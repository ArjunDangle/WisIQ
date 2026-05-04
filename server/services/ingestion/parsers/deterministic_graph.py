# FILE: services/ingestion/parsers/deterministic_graph.py

import re
from typing import List, Dict, Set, Tuple

# Strict Whitelists for Deterministic Extraction
KNOWN_FIRMWARES = {
    "rui3", "rui", "wisgateos", "wisgateos 2", "wisgateos2", "rakpios"
}

KNOWN_PROTOCOLS = {
    "lorawan", "lora", "ble", "bluetooth", "wi-fi", "wifi", 
    "mqtt", "bacnet", "modbus", "cellular", "nb-iot", "lte-m"
}

KNOWN_INTEGRATIONS = {
    "chirpstack", "ttn", "the things network", "aws iot", "aws greengrass"
}

def extract_deterministic_triplets(doc_meta: Dict, text: str) -> List[Dict[str, str]]:
    """
    Pure Python rules engine. Zero LLM. Zero Hallucination.
    Generates Neo4j triplets based purely on directory structure, 
    YAML metadata, and exact text matching against strict whitelists.
    """
    triplets: Set[Tuple[str, str, str]] = set()
    
    product_category = doc_meta.get("product_category", "unknown").lower()
    product_codes = [code.lower() for code in doc_meta.get("product_codes", [])]
    tags =[tag.lower() for tag in doc_meta.get("tags", [])]
    
    text_lower = text.lower()

    for code in product_codes:
        if not code or code == "unknown":
            continue

        # 1. Structural Relationships (From File Path)
        if product_category != "unknown":
            triplets.add((code, "BELONGS_TO_FAMILY", product_category))

        # 2. Tag Relationships (From YAML Frontmatter)
        for tag in tags:
            if tag in KNOWN_PROTOCOLS:
                triplets.add((code, "SUPPORTS_PROTOCOL", tag))
            elif tag in KNOWN_INTEGRATIONS:
                triplets.add((code, "INTEGRATES_WITH", tag))

        # 3. Exact Firmware Matching (Regex on Body Text)
        for fw in KNOWN_FIRMWARES:
            # Word boundary regex to ensure exact match (e.g., matches "rui3" but not "trui3")
            if re.search(r'\b' + re.escape(fw) + r'\b', text_lower):
                # Normalize wisgateos 2 variations
                normalized_fw = "wisgateos2" if fw in["wisgateos 2", "wisgateos2"] else fw
                triplets.add((code, "RUNS_FIRMWARE", normalized_fw))

        # 4. Exact Protocol Matching (Regex on Body Text)
        for protocol in KNOWN_PROTOCOLS:
            if re.search(r'\b' + re.escape(protocol) + r'\b', text_lower):
                normalized_proto = "wi-fi" if protocol == "wifi" else protocol
                triplets.add((code, "SUPPORTS_PROTOCOL", normalized_proto))
                
        # 5. Exact Integration Matching (Regex on Body Text)
        for integration in KNOWN_INTEGRATIONS:
            if re.search(r'\b' + re.escape(integration) + r'\b', text_lower):
                normalized_int = "ttn" if integration == "the things network" else integration
                triplets.add((code, "INTEGRATES_WITH", normalized_int))

    # Convert set of tuples back to list of dicts for JSON serialization
    return[{"source": s, "relation": r, "target": t} for s, r, t in triplets]