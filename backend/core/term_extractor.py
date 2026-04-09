"""
Offline terminology extraction tool using RAKE.

Usage:
    python -m core.term_extractor --file path/to/10k.pdf
    python -m core.term_extractor --dir path/to/documents/
"""
import argparse
import json
from pathlib import Path


def extract_from_text(text: str, top_n: int = 50) -> list[str]:
    """Extract key phrases from text using RAKE."""
    from rake_nltk import Rake

    r = Rake()
    r.extract_keywords_from_text(text)
    ranked = r.get_ranked_phrases()
    return ranked[:top_n]


def extract_from_file(file_path: str, top_n: int = 50) -> list[str]:
    """Extract key phrases from a single file (PDF or text)."""
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".pdf":
        import pdfplumber
        texts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
        text = "\n".join(texts)
    else:
        text = file_path.read_text(encoding="utf-8")

    if not text.strip():
        return []

    return extract_from_text(text, top_n=top_n)


def extract_from_directory(dir_path: str, top_n_per_file: int = 30) -> list[str]:
    """Extract key phrases from all documents in a directory."""
    dir_path = Path(dir_path)
    all_keywords = []

    for f in sorted(dir_path.iterdir()):
        if f.suffix.lower() in (".pdf", ".txt", ".md"):
            print(f"Extracting from: {f.name}")
            kws = extract_from_file(str(f), top_n=top_n_per_file)
            all_keywords.extend(kws)
            print(f"  Found {len(kws)} keywords")

    # Deduplicate and rank by frequency
    kw_freq = {}
    for kw in all_keywords:
        key = kw.lower().strip()
        kw_freq[key] = kw_freq.get(key, 0) + 1

    # Sort by frequency
    sorted_kws = sorted(kw_freq.items(), key=lambda x: -x[1])
    return [kw for kw, freq in sorted_kws]


def export_results(keywords: list[str], output_path: str):
    """Export extracted keywords to a JSON file for review."""
    data = {
        "extracted_keywords": [
            {"keyword": kw, "reviewed": False}
            for kw in keywords
        ]
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(keywords)} keywords to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract financial terminology from documents")
    parser.add_argument("--file", help="Path to a single file")
    parser.add_argument("--dir", help="Path to a directory of files")
    parser.add_argument("--output", default="data/extracted_keywords.json", help="Output JSON path")
    parser.add_argument("--top-n", type=int, default=50, help="Top N keywords per file")
    args = parser.parse_args()

    if args.file:
        keywords = extract_from_file(args.file, top_n=args.top_n)
    elif args.dir:
        keywords = extract_from_directory(args.dir, top_n_per_file=args.top_n)
    else:
        print("Please specify --file or --dir")
        exit(1)

    print(f"\nTop keywords ({len(keywords)}):")
    for i, kw in enumerate(keywords[:30], 1):
        print(f"  {i}. {kw}")

    export_results(keywords, args.output)
