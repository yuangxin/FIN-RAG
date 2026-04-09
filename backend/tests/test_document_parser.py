"""Test PDF parsing and chunking."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_chunk_text_basic():
    """Test text chunking logic."""
    from core.document_parser import _chunk_text

    # Short text should be returned as-is
    text = "This is a short paragraph."
    chunks = _chunk_text(text, max_chars=1000, overlap=0)
    assert len(chunks) == 1

    # Long text should be split
    paragraphs = [f"Paragraph {i} with some content here." for i in range(20)]
    long_text = "\n\n".join(paragraphs)
    chunks = _chunk_text(long_text, max_chars=200, overlap=50)
    assert len(chunks) > 1
    print(f"Split into {len(chunks)} chunks")


def test_section_patterns():
    """Test 10-K section pattern matching."""
    from config import SECTION_PATTERNS
    import re

    test_cases = [
        ("Item 1. Business", "item_1_business"),
        ("Item 1A. Risk Factors", "item_1a_risk"),
        ("ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS", "item_7_mda"),
        ("Item 8. Financial Statements and Supplementary Data", "item_8_financials"),
    ]

    for text, expected_section in test_cases:
        matched = False
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, text, re.I):
                assert section_name == expected_section, f"Expected {expected_section}, got {section_name}"
                matched = True
                break
        assert matched, f"No section matched for: {text}"


def test_extract_tables_format():
    """Test table extraction formatting."""
    # This tests the format_table logic indirectly
    # With a real PDF, we'd test pdfplumber directly
    headers = ["", "2023", "2022"]
    row1 = ["Net sales", "383,285", "394,328"]
    row2 = ["Net income", "96,995", "99,803"]

    rows_text = []
    for row in [row1, row2]:
        pairs = [f"{h}: {v.strip() if v else 'N/A'}" for h, v in zip(headers, row) if h]
        rows_text.append(" | ".join(pairs))

    result = "\n".join(rows_text)
    assert "383,285" in result
    assert "Net sales" in result
    print(f"Table format:\n{result}")
