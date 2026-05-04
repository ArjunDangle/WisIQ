import frontmatter
import logging
from pathlib import Path
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import Document

logger = logging.getLogger(__name__)

def parse_markdown_file(file_path: str):
    """
    Extracts frontmatter and parses the markdown body into chunks.
    Implements a strict Deterministic Metadata Formula based on file paths and Docusaurus YAML.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None,[]

    if not post.metadata:
        logger.warning(f"Skipped {file_path}: No YAML frontmatter found.")
        return None,[]

    path_obj = Path(file_path)
    path_parts = path_obj.parts

    # --- 1. DETERMINISTIC METADATA FORMULA ---
    category = "unknown"
    base_sku = "unknown"
    
    # Extract Category and SKU directly from the directory structure
    # e.g., .../product-categories/wisgate/rak7289v2/overview.md
    try:
        base_idx = path_parts.index("product-categories")
        if len(path_parts) > base_idx + 1:
            category = path_parts[base_idx + 1]  # e.g., "wisgate"
        if len(path_parts) > base_idx + 2:
            base_sku = path_parts[base_idx + 2]  # e.g., "rak7289v2"
    except ValueError:
        pass # Fallback to unknown if 'product-categories' isn't in the path

    # Extract Doc Type (Prefer 'sidebar_label' from YAML, fallback to filename)
    doc_type = post.metadata.get('sidebar_label', path_obj.stem)

    # Extract Product Codes (SKUs)
    # 1. Start with the SKU extracted from the folder name
    product_codes_set = {base_sku} if base_sku != "unknown" else set()
    
    # 2. Scan the keywords array to find additional exact SKUs (e.g., rak7289cv2)
    keywords = post.metadata.get('keywords',[])
    for kw in keywords:
        kw_str = str(kw).strip().lower()
        if kw_str.startswith('rak') or kw_str.startswith('wis'):
            product_codes_set.add(kw_str)

    # Compile the final document-level metadata payload
    doc_meta = {
        "url_slug": post.metadata.get('slug', f"/product-categories/{category}/{base_sku}/{path_obj.stem}"),
        "product_category": category,
        "product_codes": list(product_codes_set),
        "doc_type": doc_type,
        "tags": post.metadata.get('tags',[]),
        "keywords": keywords
    }

    # --- 2. CHUNKING & HEADER PATH TRACKING ---
    parser = MarkdownNodeParser()
    llama_doc = Document(text=post.content)
    nodes = parser.get_nodes_from_documents([llama_doc])

    chunks =[]
    for idx, node in enumerate(nodes):
        raw_text = node.get_content().strip()
        if not raw_text:
            continue
            
        # Extract headers from LlamaIndex metadata
        headers =[]
        for i in range(1, 7): # Cover H1 through H6
            header_val = node.metadata.get(f"Header_{i}")
            if header_val:
                headers.append(header_val.strip())
        
        # Fallback: If LlamaIndex missed the header but the text starts with '#', grab it manually
        if not headers and raw_text.startswith('#'):
            first_line = raw_text.split('\n')[0]
            headers.append(first_line.lstrip('#').strip())

        # Construct the breadcrumb (Fallback to Doc Type if completely headerless)
        header_path = " > ".join(headers) if headers else doc_meta["doc_type"]

        chunks.append({
            "text": raw_text,
            "header_path": header_path,
            "chunk_index": idx
        })

    return doc_meta, chunks