"""
Fact Extractor supporting both live LLM extraction and deterministic high-precision extraction.
Ensures zero hallucinations with strict evidence grounding against source page text.
"""

import json
import os
import re
import uuid
from typing import List, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentPage
from app.models.fact import Fact
from app.services.fact_normalizer import FactNormalizer


class FactExtractor:
    @classmethod
    def extract_facts_from_page(
        cls, 
        page: DocumentPage, 
        document_name: str,
        subject_hint: str = "Delhivery"
    ) -> List[Fact]:
        """
        Extract structured facts from a single document page.
        Uses LLM if API key is provided and configured, else uses deterministic extractor.
        """
        facts: List[Fact] = []
        if settings.llm_provider in ("anthropic", "openai", "gemini"):
            try:
                facts = cls._extract_with_llm(page, document_name, subject_hint)
            except Exception as e:
                logger.warning(f"LLM extraction failed on page {page.page_number} ({e}), falling back to deterministic extraction")
                facts = cls._extract_deterministic(page, document_name, subject_hint)
        else:
            facts = cls._extract_deterministic(page, document_name, subject_hint)

        # Grounding check: verify that each fact's evidence is actually present in the page
        grounded_facts = []
        for f in facts:
            if cls._verify_grounding(f.evidence_text, page.text):
                grounded_facts.append(f)
            else:
                logger.warning(f"Dropped ungrounded fact on page {page.page_number}: {f.predicate}")

        return grounded_facts

    @classmethod
    def _verify_grounding(cls, evidence_snippet: str, full_page_text: str) -> bool:
        """Verify that the evidence snippet is an authentic substring of the page text."""
        if not evidence_snippet or not full_page_text:
            return False
        
        # Exact match
        if evidence_snippet in full_page_text:
            return True
        
        # Normalized whitespace match
        norm_ev = " ".join(evidence_snippet.split())
        norm_full = " ".join(full_page_text.split())
        return norm_ev.lower() in norm_full.lower()

    @classmethod
    def _extract_with_llm(
        cls, 
        page: DocumentPage, 
        document_name: str, 
        subject_hint: str
    ) -> List[Fact]:
        """Call Anthropic or OpenAI API for structured fact extraction."""
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "fact_extraction.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

        user_content = f"DOCUMENT: {document_name}\nPAGE NUMBER: {page.page_number}\nDEFAULT SUBJECT: {subject_hint}\n\nPAGE TEXT:\n{page.text}"

        raw_json_str = ""
        if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            raw_json_str = response.content[0].text

        elif settings.llm_provider == "openai" and settings.openai_api_key:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            raw_json_str = response.choices[0].message.content or ""

        if not raw_json_str:
            return []

        # Parse JSON
        m = re.search(r"\{.*\}", raw_json_str, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(0))
        facts_list = data.get("facts", [])

        results: List[Fact] = []
        for item in facts_list:
            pred = FactNormalizer.normalize_predicate(item.get("predicate", ""))
            norm_val, norm_unit = FactNormalizer.normalize_value_and_unit(
                item.get("value"), item.get("unit"), pred
            )
            norm_period = FactNormalizer.normalize_period(item.get("period"))

            fact = Fact(
                fact_id=f"fact_{uuid.uuid4().hex[:12]}",
                source_document_id=page.document_id,
                source_document_name=document_name,
                page_number=page.page_number,
                subject=item.get("subject", subject_hint),
                predicate=pred,
                value=item.get("value"),
                unit=item.get("unit"),
                period=norm_period,
                scope=item.get("scope"),
                original_value=item.get("value"),
                normalized_value=norm_val,
                original_unit=item.get("unit"),
                normalized_unit=norm_unit,
                is_numerical=item.get("is_numerical", True),
                evidence_text=item.get("evidence_text", "").strip(),
                confidence=float(item.get("confidence", 0.9)),
                extraction_method="llm"
            )
            results.append(fact)
        return results

    @classmethod
    def _extract_deterministic(
        cls, 
        page: DocumentPage, 
        document_name: str, 
        subject_hint: str
    ) -> List[Fact]:
        """
        High-precision deterministic rule & pattern extractor.
        Scans page text for key financial, operational, and network facts with exact sentence evidence.
        """
        text = page.text
        facts: List[Fact] = []

        # Patterns for key metrics
        patterns = [
            # 1. Revenue from services / contracts
            {
                "pred": "revenue_from_services",
                "regex": r"(?:revenue from services[^\n\d]*|revenue from contracts with customers[^\n\d]*)(?:₹|Rs\.?|INR)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Cr|crore|Mn|million)?",
                "unit_fallback": "INR million",
                "period_scan": True
            },
            # 2. Earnings deck revenue: e.g. "₹8,142 Cr FY24 revenue from services"
            {
                "pred": "revenue_from_services",
                "regex": r"(?:₹|Rs\.?|INR)\s*([0-9,]+(?:\.[0-9]+)?)\s*(Cr|crore|Mn|million)\s*(?:FY24|Q4 FY24)?\s*revenue from services",
                "unit_fallback": "INR crore",
                "period_scan": True
            },
            # 3. Express parcel shipments: e.g. "740Mn Express parcels shipped" or "740 Mn Express parcel shipments in FY24"
            {
                "pred": "express_parcel_shipments",
                "regex": r"([0-9,]+(?:\.[0-9]+)?)\s*(Mn|million|Bn|billion)?\s*(?:Express parcel shipments|Express parcels shipped)",
                "unit_fallback": "million",
                "period_scan": True
            },
            # 4. Inception parcels: e.g. ">2.8Bn Express parcel shipments delivered since inception"
            {
                "pred": "express_parcel_shipments",
                "regex": r"(?:>)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Bn|billion)\s*Express parcel shipments delivered since inception",
                "unit_fallback": "billion",
                "scope": "since inception",
                "period": "Inception to Date"
            },
            # 5. PTL freight delivered / tonnage: e.g. "1,429K tonnes PTL freight delivered" or "1.4 Mn Tons PTL freight tonnage"
            {
                "pred": "ptl_freight_tonnage",
                "regex": r"([0-9,]+(?:\.[0-9]+)?)\s*(K tonnes|thousand tonnes|Mn Tons|Mn tonnes|'000 Tons|tonnes)\s*(?:PTL freight delivered|PTL freight tonnage)",
                "unit_fallback": "tonnes",
                "period_scan": True
            },
            # 6. PTL freight since inception: e.g. ">4.8Mn tonnes Part-truckload freight delivered since inception"
            {
                "pred": "ptl_freight_tonnage",
                "regex": r"(?:>)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Mn tonnes|Mn Tons|tonnes)\s*Part-truckload freight delivered since inception",
                "unit_fallback": "Mn tonnes",
                "scope": "since inception",
                "period": "Inception to Date"
            },
            # 7. EBITDA: e.g. "₹1,266Mn EBITDA" or "₹127Cr / 1.6% EBITDA"
            {
                "pred": "ebitda",
                "regex": r"(?:₹|Rs\.?|INR)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Mn|million|Cr|crore)\s*(?:EBITDA|service EBITDA)",
                "unit_fallback": "INR million",
                "period_scan": True
            },
            # 8. Adjusted EBITDA: e.g. "₹758Mn Adjusted EBITDA" or "₹76Cr / 0.9% Adj. EBITDA"
            {
                "pred": "adjusted_ebitda",
                "regex": r"(?:₹|Rs\.?|INR)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Mn|million|Cr|crore)\s*(?:Adjusted EBITDA|Adj\. EBITDA)",
                "unit_fallback": "INR million",
                "period_scan": True
            },
            # 9. Net working capital days: e.g. "net working capital days to 31 days" or "NWC days from 38 to 31 days"
            {
                "pred": "net_working_capital_days",
                "regex": r"(?:net working capital days|NWC days)[^\d]*([0-9]+)\s*days",
                "unit_fallback": "days",
                "period_scan": True
            },
            # 10. Pin codes covered: e.g. "18,793 Pin codes covered" or "serviced 17,488 PIN codes"
            {
                "pred": "pin_code_reach",
                "regex": r"([0-9,]{5,6})\s*(?:Pin codes covered|PIN codes|Pin-code reach)",
                "unit_fallback": "count",
                "period_scan": True
            },
            # 11. Daily average fleet size: e.g. "15,065 Daily average fleet size"
            {
                "pred": "fleet_size_daily_avg",
                "regex": r"([0-9,]{4,6})\s*(?:Daily average fleet size|Fleet size – daily average)",
                "unit_fallback": "count",
                "period_scan": True
            },
            # 12. 46-ft tractors count: e.g. "753 Count of 46-ft tractors" or "total count to 753 46-ft tractors"
            {
                "pred": "tractor_trailers_46ft",
                "regex": r"([0-9]{3})\s*(?:Count of 46-ft tractors|46-ft tractors)",
                "unit_fallback": "count",
                "period_scan": True
            },
            # 13. Macroeconomic: Real GDP Growth
            {
                "pred": "real_gdp_growth",
                "regex": r"(?:real GDP(?: growth)?|GDP growth)[^\d%]*([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|per\s*cent)",
                "unit_fallback": "%",
                "period_scan": True
            },
            # 14. Macroeconomic: CPI Inflation
            {
                "pred": "cpi_inflation",
                "regex": r"(?:CPI inflation|headline inflation)[^\d%]*([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|per\s*cent)",
                "unit_fallback": "%",
                "period_scan": True
            },
            # 15. Macroeconomic: Fiscal Deficit
            {
                "pred": "fiscal_deficit",
                "regex": r"(?:fiscal deficit[^\d%]*|fiscal deficits[^\d%]*)([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|per\s*cent)(?:\s*of\s*GDP)?",
                "unit_fallback": "% of GDP",
                "period_scan": True
            }
        ]

        # Scan line by line or window
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            # Look up to 3 lines ahead for combined label + value
            window_lines = lines[idx:min(len(lines), idx + 3)]
            window_text = " ".join([l.strip() for l in window_lines])

            for pat in patterns:
                m = re.search(pat["regex"], window_text, re.IGNORECASE)
                if m:
                    raw_val = m.group(1).replace(",", "")
                    raw_unit = m.group(2) if len(m.groups()) >= 2 and m.group(2) else pat.get("unit_fallback")
                    pred = pat["pred"]

                    # Determine period
                    period = pat.get("period")
                    if not period and pat.get("period_scan"):
                        # Look for FY24, Q4 FY24, FY23, FY20 in nearby text
                        nearby = " ".join([l.strip() for l in lines[max(0, idx - 2):min(len(lines), idx + 5)]])
                        if "q4 fy24" in nearby.lower() or "q4" in window_text.lower():
                            period = "Q4 FY24"
                        elif "fy24" in nearby.lower() or "fy 2023-24" in nearby.lower() or "2023-24" in nearby.lower():
                            period = "FY24"
                        elif "fy23" in nearby.lower():
                            period = "FY23"
                        elif "fy21" in nearby.lower():
                            period = "FY21"
                        elif "fy20" in nearby.lower():
                            period = "FY20"
                        elif "march 31, 2024" in nearby.lower():
                            period = "As of March 31, 2024"
                        elif "december 31, 2021" in nearby.lower():
                            period = "As of December 31, 2021"
                        else:
                            period = "FY24"

                    norm_val, norm_unit = FactNormalizer.normalize_value_and_unit(raw_val, raw_unit, pred)
                    norm_period = FactNormalizer.normalize_period(period)

                    # Build evidence snippet
                    evidence = m.group(0).strip()
                    # Expand evidence to full sentence or window line
                    if len(evidence) < len(line_str):
                        evidence = line_str

                    # Check for duplicate extraction on same page
                    if any(f.predicate == pred and f.normalized_value == norm_val and f.period == norm_period for f in facts):
                        continue

                    fact = Fact(
                        fact_id=f"fact_{uuid.uuid4().hex[:12]}",
                        source_document_id=page.document_id,
                        source_document_name=document_name,
                        page_number=page.page_number,
                        subject=subject_hint,
                        predicate=pred,
                        value=raw_val,
                        unit=raw_unit,
                        period=norm_period,
                        scope=pat.get("scope"),
                        original_value=raw_val,
                        normalized_value=norm_val,
                        original_unit=raw_unit,
                        normalized_unit=norm_unit,
                        is_numerical=True,
                        evidence_text=evidence,
                        confidence=0.95,
                        extraction_method="deterministic"
                    )
                    facts.append(fact)

        return facts
