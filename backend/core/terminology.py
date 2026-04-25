import json
import re
from pathlib import Path


class TerminologyDict:
    """Financial terminology dictionary for query expansion and chunk enrichment."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.terms: dict[str, dict] = {}
        self._index: dict[str, str] = {}  # lowercase key -> term key
        self.load()

    def load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.terms = data.get("terms", {})
        self._build_index()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"terms": self.terms}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _build_index(self):
        """Build lookup index: all lowercase forms -> term key.
        Also builds a regex pattern for word-boundary matching.
        """
        self._index = {}
        for key, entry in self.terms.items():
            self._index[key.lower()] = key
            # Also index the canonical_form
            cf = entry.get("canonical_form", "").lower()
            if cf and cf != key.lower():
                self._index[cf] = key
            for abbr in entry.get("abbreviations", []):
                self._index[abbr.lower()] = key
            for syn in entry.get("synonyms", []):
                self._index[syn.lower()] = key

        # Build combined regex for fast matching
        sorted_keys = sorted(self._index.keys(), key=len, reverse=True)
        multi_word = []
        single_word = []
        for k in sorted_keys:
            if " " in k or "-" in k or "/" in k:
                multi_word.append((k, self._index[k]))
            else:
                single_word.append((k, self._index[k]))

        # Multi-word phrases: combined with |
        if multi_word:
            combined = "|".join(re.escape(k) for k, _ in multi_word)
            self._multi_regex = re.compile(combined, re.IGNORECASE)
            self._multi_map = {k: v for k, v in multi_word}
        else:
            self._multi_regex = None
            self._multi_map = {}

        # Single words: combined with ASCII word boundaries
        if single_word:
            combined = "|".join(rf"(?<![a-zA-Z0-9]){re.escape(k)}(?![a-zA-Z0-9])" for k, _ in single_word)
            self._single_regex = re.compile(combined, re.IGNORECASE)
            self._single_map = {k.lower(): v for k, v in single_word}
        else:
            self._single_regex = None
            self._single_map = {}

    def lookup(self, term: str) -> dict | None:
        """Look up a term (case-insensitive). Returns the term entry or None."""
        key = self._index.get(term.lower())
        if key:
            return {"key": key, **self.terms[key]}
        return None

    def _match_terms(self, text: str) -> set[str]:
        """Find all matching term keys using combined regex (fast)."""
        text_lower = text.lower()
        matched_keys = set()

        if self._multi_regex:
            for m in self._multi_regex.finditer(text_lower):
                matched = m.group(0).lower()
                if matched in self._multi_map:
                    matched_keys.add(self._multi_map[matched])

        if self._single_regex:
            for m in self._single_regex.finditer(text_lower):
                matched = m.group(0).lower()
                if matched in self._single_map:
                    matched_keys.add(self._single_map[matched])

        return matched_keys

    def expand_query(self, text: str) -> str:
        """Expand recognized terms in query text.

        For each matched term, appends: canonical_form + synonyms + components.
        Original text is preserved.
        """
        expansions = []

        matched_keys = self._match_terms(text)

        for term_key in matched_keys:
            entry = self.terms[term_key]
            parts = [entry["canonical_form"]]
            parts.extend(entry.get("synonyms", []))
            parts.extend(entry.get("components", []))
            expansions.append(", ".join(parts))

        if not expansions:
            return text

        return f"{text} [Related terms: {'; '.join(expansions)}]"

    def enrich_chunk_text(self, text: str) -> tuple[str, list[str]]:
        """Enrich chunk text by appending detected term info.

        Appends canonical_form + synonyms + components for each matched term.
        Returns (enriched_text, list_of_detected_term_keys).
        """
        detected = []
        enrichment_parts = []

        matched_keys = self._match_terms(text)

        for term_key in matched_keys:
            entry = self.terms[term_key]
            detected.append(term_key)

            parts = [entry["canonical_form"]]
            synonyms = entry.get("synonyms", [])
            components = entry.get("components", [])
            if synonyms:
                parts.append("Syn: " + ", ".join(synonyms))
            if components:
                parts.append("Comp: " + ", ".join(components))
            enrichment_parts.append(" | ".join(parts))

        if not enrichment_parts:
            return text, detected

        enriched = f"{text} [Terms: {'; '.join(enrichment_parts)}]"
        return enriched, detected

    def get_all_abbreviations(self) -> set[str]:
        """Return all abbreviations and synonyms for keyword matching."""
        return set(self._index.keys())

    def add_term(self, key: str, entry: dict):
        """Add or update a term entry."""
        self.terms[key.lower()] = entry
        self._build_index()

    def get_terms_by_category(self, category: str) -> list[str]:
        """Get all term keys belonging to a category."""
        return [
            k for k, v in self.terms.items()
            if v.get("category") == category
        ]


# Module-level singleton
def _init_terminology_dict() -> TerminologyDict:
    from config import TERMINOLOGY_DICT_PATH
    return TerminologyDict(TERMINOLOGY_DICT_PATH)


terminology_dict = _init_terminology_dict()
