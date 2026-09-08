"""
Text cleaner and sanitizer preserving numerical and currency formats.
"""

import re
import unicodedata


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """
        Clean text while strictly preserving:
        - Currency symbols (₹, Rs, Rs., $, INR)
        - Financial signs and brackets for negative values: (452), (1,008), -2,533
        - Numerical multipliers: Cr, Mn, Bn, K, crore, million, billion, tonnes
        - Time markers: FY24, Q4, 2024, March 31
        """
        if not text:
            return ""

        # Normalize unicode characters (NFKC handles composite symbols)
        text = unicodedata.normalize("NFKC", text)

        # Standardize dashes to regular hyphen-minus
        text = re.sub(r"[–—―−]", "-", text)

        # Normalize common quote characters
        text = re.sub(r"[''՚’‘]", "'", text)
        text = re.sub(r'[""“”«»]', '"', text)

        # Fix broken words across lines (e.g. "com-\n pany" -> "company")
        text = re.sub(r"(\b\w+)-\s*\n\s*(\w+\b)", r"\1\2", text)

        # Replace consecutive newlines with double newline to preserve paragraph separation
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        # Clean multiple spaces within a line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

        # Remove repetitive header/footer artifacts
        filtered_lines = []
        for line in lines:
            if not line:
                filtered_lines.append("")
                continue
            # Skip standalone page numbers or recurring filing tags
            if re.match(r"^\d{1,4}$", line):
                continue
            if re.match(r"^(Annual Report \d{4}-\d{2}|Statutory Reports|Corporate Overview|Financial Statements)$", line, re.IGNORECASE):
                continue
            filtered_lines.append(line)

        cleaned = "\n".join(filtered_lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def extract_context_window(full_text: str, snippet: str, window_chars: int = 150) -> str:
        """Finds snippet in full text and extracts a surrounding context window."""
        if not full_text or not snippet:
            return snippet
        idx = full_text.find(snippet)
        if idx == -1:
            # Try case-insensitive search
            pattern = re.escape(snippet)
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                idx = m.start()
            else:
                return snippet

        start = max(0, idx - window_chars)
        end = min(len(full_text), idx + len(snippet) + window_chars)
        
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(full_text) else ""
        return f"{prefix}{full_text[start:end].strip()}{suffix}"
