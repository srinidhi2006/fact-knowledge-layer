import pymupdf
import re

for fname in ["01-india-economic-survey-2024-25-excerpt.pdf", "02-rbi-annual-report-2024-25-excerpt.pdf", "03-imf-india-2025-article-iv-excerpt.pdf"]:
    path = f"india-macroeconomy/{fname}"
    doc = pymupdf.open(path)
    print(f"\nScanning {fname} (pages: {len(doc)})...")
    for idx in range(min(25, len(doc))):
        text = doc[idx].get_text()
        for kw in ["real gdp", "gdp growth", "cpi inflation", "fiscal deficit"]:
            m = re.search(r"([^\n.]{0,40}" + kw + r"[^\n.]{0,60})", text, re.IGNORECASE)
            if m:
                print(f"  P{idx+1} [{kw}]: {m.group(0).strip().replace(chr(10), ' ')}")
                break
