import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

# API Keys
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# LLM Settings
LLM_MODEL = "deepseek-chat"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_TEMPERATURE = 0

# Embedding Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Retrieval Settings
TOP_K = 10
MAX_RETRIES = 2
MAX_DOCUMENTS = 10

# Terminology Settings
TERMINOLOGY_DICT_PATH = DATA_DIR / "terminology.json"
TERMINOLOGY_ENRICH_CHUNKS = True
TERMINOLOGY_EXPAND_QUERIES = True

# Chunking Settings
CHUNK_MAX_CHARS = 2000
CHUNK_OVERLAP = 200
TABLE_MIN_CHARS = 30

# Vector Store Settings
VECTOR_STORE_BATCH_SIZE = 100

# 10-K Section patterns
SECTION_PATTERNS = {
    "item_1_business": r"Item\s+1[\.\:]?\s*Business",
    "item_1a_risk": r"Item\s+1A[\.\:]?\s*Risk Factors",
    "item_1b_unresolved": r"Item\s+1B[\.\:]?\s*Unresolved Staff Comments",
    "item_2_properties": r"Item\s+2[\.\:]?\s*Properties",
    "item_3_legal": r"Item\s+3[\.\:]?\s*Legal Proceedings",
    "item_4_mine": r"Item\s+4[\.\:]?\s*Mine Safety",
    "item_5_market": r"Item\s+5[\.\:]?\s*Market",
    "item_6_reserved": r"Item\s+6[\.\:]?\s*Reserved",
    "item_7_mda": r"Item\s+7[\.\:]?\s*Management.{0,5}s Discussion and Analysis",
    "item_7a_market_risk": r"Item\s+7A[\.\:]?\s*Quantitative and Qualitative",
    "item_8_financials": r"Item\s+8[\.\:]?\s*Financial Statements",
    "item_9_changes": r"Item\s+9[\.\:]?\s*Changes in and Disagreements",
    "item_9a_controls": r"Item\s+9A[\.\:]?\s*Controls and Procedures",
    "item_10_directors": r"Item\s+10[\.\:]?\s*Directors",
    "item_11_executive": r"Item\s+11[\.\:]?\s*Executive Compensation",
    "item_12_security": r"Item\s+12[\.\:]?\s*Security Ownership",
    "item_13_relations": r"Item\s+13[\.\:]?\s*Certain Relationships",
    "item_14_fees": r"Item\s+14[\.\:]?\s*Principal Accountant",
    "item_15_exhibits": r"Item\s+15[\.\:]?\s*Exhibits and Financial Statement Schedules",
    "item_16_form": r"Item\s+16[\.\:]?\s*Form 10-K Summary",
}

# Company name normalization map
COMPANY_ALIASES = {
    "apple": "apple", "aapl": "apple",
    "microsoft": "microsoft", "msft": "microsoft",
    "google": "google", "alphabet": "google", "googl": "google", "goog": "google",
    "amazon": "amazon", "amzn": "amazon",
    "tesla": "tesla", "tsla": "tesla",
    "meta": "meta", "facebook": "meta", "fb": "meta",
    "nvidia": "nvidia", "nvda": "nvidia",
    "netflix": "netflix", "nflx": "netflix",
}

# Pipeline node names (for WebSocket step tracking)
NODE_NAMES = {"query_rewriter", "metadata_extractor", "retriever", "answer_generator"}
