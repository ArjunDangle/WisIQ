# FILE: infra/db/seeds/seed_taxonomy.py

import json
import asyncio
from pathlib import Path
from prisma import Prisma

# Dynamically resolve project root
BASE_DIR = Path(__file__).resolve().parents[3]
JSONL_PATH = BASE_DIR / "data" / "processed" / "knowledge_base.jsonl"

# Your strict EOL list
EOL_PRODUCTS =[
    'RAK7240', 'RAK7289', 'RAK7249', 'RAK7258', 'RAK7268', 'RAK10701-P',
    'RAK7243', 'RAK7243C', 'RAK7244', 'RAK7244C', 'RAK7246G',
    'RAK4200', 'RAK4260', 'RAK4270', 'RAK4600',
    'RAK811', 'RAK813', 'RAK831', 'RAK833',
    'RAK2245 Stamp', 'RAK2245 Pi HAT', 'RAK2247',
    'RAK5005-O', 'RAK1910', 'RAK2171',
    'RAK7200', 'RAK7204', 'RAK612', 'RAK7201', 'RAK2011', 'RAK2013',
    "RAK815", "RAK7205", "RAK5205", "RAK8212"
]

def normalize_code(code: str) -> str:
    """Normalizes codes for reliable EOL matching (lowercase, no spaces/hyphens)."""
    return str(code).lower().replace(" ", "").replace("-", "")

# Create a highly-optimized O(1) lookup set
NORMALIZED_EOL = set(normalize_code(p) for p in EOL_PRODUCTS)

async def seed_taxonomy():
    db = Prisma()
    await db.connect()
    
    print("🔌 Connected to PostgreSQL. Reading JSONL...")
    
    if not JSONL_PATH.exists():
        print(f"❌ Error: Could not find {JSONL_PATH}")
        await db.disconnect()
        return

    # Temporary storage for unique values
    families = set()
    family_to_codes = {}

    # 1. First Pass: Extract unique entities from the dataset
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): 
                continue
                
            data = json.loads(line)
            doc_meta = data.get("document_level", {})
            
            family = doc_meta.get("product_category")
            codes = doc_meta.get("product_codes",[])

            if not family or family == "unknown":
                continue
            
            families.add(family)
            if family not in family_to_codes:
                family_to_codes[family] = set()
            
            for code in codes:
                if code:
                    family_to_codes[family].add(code)

    print(f"📊 Extracted {len(families)} Product Families from the JSONL.")
    
    # 2. Upsert Families (Insert if new, skip if exists)
    for family in families:
        await db.productfamily.upsert(
            where={"name": family},
            data={
                "create": {"name": family},
                "update": {} # Do nothing if it already exists
            }
        )
    
    print("✅ Product Families seeded. Unrolling Product Codes...")

    inserted_codes = 0
    eol_codes_flagged = 0

    # 3. Upsert Product Codes with EOL logic
    for family, codes in family_to_codes.items():
        # Get the DB record of the family to retrieve its UUID
        family_record = await db.productfamily.find_unique(where={"name": family})
        
        for code in codes:
            # Check against our normalized EOL list
            is_eol = normalize_code(code) in NORMALIZED_EOL
            
            if is_eol:
                eol_codes_flagged += 1

            await db.productcode.upsert(
                where={"code": code},
                data={
                    "create": {
                        "code": code,
                        "is_eol": is_eol,
                        "product_family_id": family_record.id
                    },
                    "update": {
                        "is_eol": is_eol # Update flag if list changed
                    }
                }
            )
            inserted_codes += 1

    print(f"✅ Seeded {inserted_codes} Product Codes.")
    print(f"🚨 Flagged {eol_codes_flagged} codes as End-of-Life (EOL).")
    
    await db.disconnect()
    print("🔒 Database connection closed.")

if __name__ == '__main__':
    asyncio.run(seed_taxonomy())