import logging
import re
import uuid
import pdfplumber
from config import (
    SECTION_PATTERNS,
    COMPANY_ALIASES,
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP,
    TABLE_MIN_CHARS,
)

logger = logging.getLogger(__name__)


def parse_pdf(pdf_path: str, doc_id: str | None = None) -> tuple[list[dict], dict]:
    """Parse a 10-K PDF into structure-aware chunks.

    Returns:
        (chunks, metadata): chunks list and document-level metadata
    """
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info("Starting PDF parse: %s (%d pages)", pdf_path, total_pages)

        # Extract document-level metadata
        doc_metadata = _extract_doc_metadata(pdf, pdf_path)
        company_name = doc_metadata["company_name"]
        year = doc_metadata["year"]
        quarter = doc_metadata.get("quarter", "")

        # Build page-to-section mapping
        section_map = _build_section_map(pdf)

        # Extract chunks from each page
        chunks = []
        chunk_index = 0
        failed_pages = 0

        for page_num, page in enumerate(pdf.pages):
            page_sections = section_map.get(page_num, ["unknown"])

            try:
                # Extract and chunk text
                text = page.extract_text() or ""
                if text.strip():
                    text_chunks = _chunk_text(text, CHUNK_MAX_CHARS, CHUNK_OVERLAP)
                    for tc in text_chunks:
                        chunks.append({
                            "text": tc,
                            "metadata": {
                                "doc_id": doc_id,
                                "company_name": company_name,
                                "year": year,
                                "quarter": quarter,
                                "page_no": page_num + 1,
                                "section": page_sections[0] if page_sections else "unknown",
                                "chunk_type": "text",
                                "chunk_index": chunk_index,
                            },
                        })
                        chunk_index += 1

                # Extract tables (each table = one chunk, preserved whole)
                tables = _extract_tables(page)
                for table_text in tables:
                    chunks.append({
                        "text": table_text,
                        "metadata": {
                            "doc_id": doc_id,
                            "company_name": company_name,
                            "year": year,
                            "quarter": quarter,
                            "page_no": page_num + 1,
                            "section": page_sections[0] if page_sections else "unknown",
                            "chunk_type": "table",
                            "chunk_index": chunk_index,
                        },
                    })
                    chunk_index += 1

            except Exception as e:
                # Graceful degradation: if tables fail, try text-only
                logger.warning("Full parse failed on page %d, retrying text-only: %s",
                               page_num + 1, e)
                failed_pages += 1
                try:
                    text = page.extract_text() or ""
                    if text.strip():
                        text_chunks = _chunk_text(text, CHUNK_MAX_CHARS, CHUNK_OVERLAP)
                        for tc in text_chunks:
                            chunks.append({
                                "text": tc,
                                "metadata": {
                                    "doc_id": doc_id,
                                    "company_name": company_name,
                                    "year": year,
                                    "quarter": quarter,
                                    "page_no": page_num + 1,
                                    "section": page_sections[0] if page_sections else "unknown",
                                    "chunk_type": "text",
                                    "chunk_index": chunk_index,
                                },
                            })
                            chunk_index += 1
                except Exception as e2:
                    logger.error("Text extraction also failed on page %d: %s",
                                 page_num + 1, e2)

            if (page_num + 1) % 25 == 0:
                logger.info("Parsed %d/%d pages, %d chunks so far",
                            page_num + 1, total_pages, chunk_index)

        logger.info("Finished PDF parse: %d chunks from %d pages (%d pages degraded)",
                    len(chunks), total_pages, failed_pages)

    return chunks, doc_metadata


def _extract_doc_metadata(pdf, filename: str) -> dict:
    """Extract company name and year from filename or first page."""
    basename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    # Strategy 1: filename regex
    name_match = re.search(
        r"(apple|microsoft|msft|aapl|googl?|amzn|tsla|meta|fb|nvda|nflx)[-_]",
        basename, re.I,
    )
    year_match = re.search(r"(20\d{2})", basename)

    company_name = ""
    if name_match:
        company_name = COMPANY_ALIASES.get(name_match.group(1).lower(), name_match.group(1).lower())

    year = year_match.group(1) if year_match else ""

    # Strategy 2: first page text if filename didn't work
    if not company_name or not year:
        first_page_text = ""
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""

        if not company_name and first_page_text:
            for alias, canonical in COMPANY_ALIASES.items():
                if alias in first_page_text.lower():
                    company_name = canonical
                    break

        if not year and first_page_text:
            fy_match = re.search(r"fiscal\s+year\s+(?:ended|ending)?\s*(20\d{2})", first_page_text, re.I)
            if fy_match:
                year = fy_match.group(1)
            elif not year:
                years = re.findall(r"20\d{2}", first_page_text)
                if years:
                    year = years[0]

    return {
        "doc_id": "",
        "company_name": company_name,
        "year": year,
        "quarter": "",
        "filename": basename,
        "total_pages": len(pdf.pages),
    }


def _build_section_map(pdf) -> dict[int, list[str]]:
    """Map each page to its 10-K section(s)."""
    section_map: dict[int, list[str]] = {}

    # Collect all section boundaries: (page_num, section_name)
    boundaries = []
    for page_num, page in enumerate(pdf.pages):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            logger.warning("section_map: failed on page %d: %s", page_num + 1, e)
            continue
        for section_name, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, text, re.I):
                boundaries.append((page_num, section_name))
                break

    # Assign pages to sections
    if not boundaries:
        return section_map

    for i, (start_page, section_name) in enumerate(boundaries):
        end_page = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(pdf.pages)
        for p in range(start_page, end_page):
            section_map.setdefault(p, []).append(section_name)

    return section_map


def _extract_tables(page) -> list[str]:
    """Extract tables from a page, format as row-wise text."""
    try:
        tables = page.extract_tables({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
            "join_tolerance": 3,
        })
    except Exception as e:
        logger.warning("Table extraction failed on a page: %s", e)
        return []

    results = []
    for table in tables:
        if not table or len(table) < 2:
            continue

        headers = [cell.strip() if cell else "" for cell in table[0]]
        rows_text = []
        for row in table[1:]:
            pairs = []
            for h, v in zip(headers, row):
                if h:
                    val = v.strip() if v else "N/A"
                    pairs.append(f"{h}: {val}")
            if pairs:
                rows_text.append(" | ".join(pairs))

        chunk_text = "\n".join(rows_text)
        if len(chunk_text.strip()) > TABLE_MIN_CHARS:
            results.append(chunk_text)

    return results


def _chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split text into chunks at paragraph/sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    # Split into paragraphs
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 1 <= max_chars:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Keep overlap from end of current chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Single paragraph exceeds max_chars, split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= max_chars:
                        current_chunk = f"{current_chunk} {sent}" if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
