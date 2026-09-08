"""
Deterministic Fact Normalizer for currencies, units, reporting periods, and metrics.
"""

import re
from typing import Optional, Tuple, Union


class FactNormalizer:
    # Predicate alias mappings
    PREDICATE_MAP = {
        "revenue": "revenue_from_services",
        "revenue_from_services": "revenue_from_services",
        "revenue from services": "revenue_from_services",
        "revenue from operations": "revenue_from_services",
        "revenue_from_operations": "revenue_from_services",
        "revenue from contracts with customers": "revenue_from_services",
        "revenue from contracts": "revenue_from_services",
        "sale of services": "revenue_from_services",
        
        "express_parcel_shipments": "express_parcel_shipments",
        "express parcel shipments": "express_parcel_shipments",
        "express parcels shipped": "express_parcel_shipments",
        "express parcel volume": "express_parcel_shipments",
        "express parcel shipment volume": "express_parcel_shipments",
        
        "ptl_freight_tonnage": "ptl_freight_tonnage",
        "ptl freight tonnage": "ptl_freight_tonnage",
        "ptl freight delivered": "ptl_freight_tonnage",
        "part-truckload tonnage": "ptl_freight_tonnage",
        "part truckload tonnage": "ptl_freight_tonnage",
        "part truckload freight": "ptl_freight_tonnage",
        
        "ebitda": "ebitda",
        "service ebitda": "service_ebitda",
        "adjusted_ebitda": "adjusted_ebitda",
        "adj. ebitda": "adjusted_ebitda",
        "adjusted ebitda": "adjusted_ebitda",
        "ebitda_margin": "ebitda_margin",
        "ebitda margin": "ebitda_margin",
        "adjusted_ebitda_margin": "adjusted_ebitda_margin",
        
        "net_working_capital_days": "net_working_capital_days",
        "net working capital days": "net_working_capital_days",
        "nwc days": "net_working_capital_days",
        "net working capital cycle": "net_working_capital_days",
        "working capital days": "net_working_capital_days",
        
        "pin_code_reach": "pin_code_reach",
        "pin codes covered": "pin_code_reach",
        "pincodes covered": "pin_code_reach",
        "pin-code reach": "pin_code_reach",
        "pin codes": "pin_code_reach",
        
        "active_customers": "active_customers",
        "no. of active customers": "active_customers",
        "active customer count": "active_customers",
        
        "gateways": "gateways",
        "no. of gateways": "gateways",
        
        "fleet_size_daily_avg": "fleet_size_daily_avg",
        "daily average fleet size": "fleet_size_daily_avg",
        "fleet size - daily average": "fleet_size_daily_avg",
        
        "tractor_trailers_46ft": "tractor_trailers_46ft",
        "46-ft tractors": "tractor_trailers_46ft",
        "count of 46-ft tractors": "tractor_trailers_46ft",

        # Macroeconomic predicates
        "real_gdp_growth": "real_gdp_growth",
        "real gdp growth": "real_gdp_growth",
        "gdp growth": "real_gdp_growth",
        "cpi_inflation": "cpi_inflation",
        "cpi inflation": "cpi_inflation",
        "headline inflation": "cpi_inflation",
        "fiscal_deficit": "fiscal_deficit",
        "fiscal deficit": "fiscal_deficit"
    }

    @classmethod
    def normalize_predicate(cls, predicate: str) -> str:
        """Standardize predicate string into a canonical identifier."""
        cleaned = predicate.strip().lower().replace("-", " ").replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cls.PREDICATE_MAP.get(cleaned, cleaned.replace(" ", "_"))

    @staticmethod
    def parse_numeric_string(raw_val: Union[float, int, str]) -> Optional[float]:
        """Convert a string representation of a number into a float, handling commas and parentheses."""
        if isinstance(raw_val, (int, float)):
            return float(raw_val)
        
        val_str = str(raw_val).strip()
        # Remove currency symbols and comparator signs
        val_str = re.sub(r"[₹$€£><~]", "", val_str).strip()
        val_str = val_str.replace(",", "")

        # Check for parentheses denoting negative numbers e.g. (452) or (4,516)
        match_paren = re.match(r"^\(([0-9.]+)\)$", val_str)
        if match_paren:
            try:
                return -float(match_paren.group(1))
            except ValueError:
                return None

        # Standard negative or positive number
        match_num = re.search(r"[-+]?[0-9]*\.?[0-9]+", val_str)
        if match_num:
            try:
                return float(match_num.group(0))
            except ValueError:
                return None
        return None

    @classmethod
    def normalize_value_and_unit(
        cls, 
        raw_val: Union[float, int, str], 
        raw_unit: Optional[str],
        predicate: Optional[str] = None
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Deterministic unit & value normalization.
        Converts:
        - Currency: ₹ Cr -> INR million (* 10), ₹ Mn -> INR million (* 1)
        - Tonnage: K tonnes / '000 tonnes -> Tonnes (* 1000), Mn tons -> Tonnes (* 1000000)
        - Counts: Mn -> Million
        - Margins / Percentages: % -> Percent
        - Days: days -> Days
        """
        num_val = cls.parse_numeric_string(raw_val)
        if num_val is None:
            return None, raw_unit

        unit_str = (raw_unit or "").strip().lower()
        pred = (predicate or "").lower()

        # Check if raw_val string has the unit embedded (e.g. "₹8,142 Cr" or "740Mn")
        raw_str = str(raw_val).lower()
        combined = f"{raw_str} {unit_str}".strip()

        # 1. Indian Currency (Crore -> INR million)
        if "cr" in combined or "crore" in combined:
            return round(num_val * 10.0, 4), "INR million"

        # 2. Indian / Global Currency (Million -> INR million)
        if ("mn" in combined or "million" in combined) and ("₹" in combined or "rs" in combined or "inr" in combined or "revenue" in pred or "ebitda" in pred):
            return round(num_val, 4), "INR million"

        # 3. Plain INR Currency (₹81,415.38 when table says "in million")
        if "₹" in combined or "rs" in combined or "inr" in combined:
            # If the unit explicitly mentions million
            if "million" in unit_str or "mn" in unit_str:
                return round(num_val, 4), "INR million"
            # If plain ₹ with no multiplier, check magnitude: if > 10,000,000, normalize to million
            if num_val > 10_000_000:
                return round(num_val / 1_000_000.0, 4), "INR million"
            return round(num_val, 4), "INR"

        # 4. Tonnage
        if "k tonne" in combined or "thousand tonne" in combined or "'000 ton" in combined or "k ton" in combined:
            return round(num_val * 1_000.0, 2), "tonnes"
        if "mn ton" in combined or "million ton" in combined or "mn tonne" in combined or "million tonne" in combined:
            return round(num_val * 1_000_000.0, 2), "tonnes"
        if "ton" in combined or "tonne" in combined:
            return round(num_val, 2), "tonnes"

        # 5. Parcels / Shipments / Counts
        if "bn" in combined or "billion" in combined:
            return round(num_val * 1_000.0, 4), "million"
        if "mn" in combined or "million" in combined:
            return round(num_val, 4), "million"

        # 6. Percentages
        if "%" in combined or "percent" in combined or "margin" in pred:
            return round(num_val, 3), "%"

        # 7. Days / Time
        if "day" in combined or "days" in combined or "cycle" in pred or "nwc" in pred:
            return round(num_val, 1), "days"

        # 8. Pin codes / Fleet / Gateways / Counts
        if any(term in pred for term in ["pin_code", "fleet", "gateway", "customer", "tractor", "centre"]):
            return round(num_val, 2), "count"

        # Fallback default
        return round(num_val, 4), raw_unit

    @classmethod
    def normalize_period(cls, period: Optional[str]) -> Optional[str]:
        """
        Standardize reporting period string to canonical format.
        Examples:
        - 'FY 2023-24', 'FY 2024', 'Fiscal 2024', 'FY24' -> 'FY24'
        - 'Q4 FY24', 'Q4 FY 2024', '4th Quarter FY24' -> 'Q4 FY24'
        - 'since inception', 'inception to date' -> 'Inception to Date'
        """
        if not period:
            return None

        p = period.strip().lower()

        # Inception
        if "inception" in p:
            return "Inception to Date"

        # Quarters + FY
        m_q_fy = re.search(r"q([1-4])\s*(?:fy\s*|fiscal\s*)?(?:20)?(\d{2})", p)
        if m_q_fy:
            return f"Q{m_q_fy.group(1)} FY{m_q_fy.group(2)}"

        # Fiscal Year patterns: FY24, FY 2024, FY 2023-24, Fiscal 2024
        m_fy_range = re.search(r"(?:fy|fiscal)\s*(?:20)?(\d{2})[-–/](\d{2})", p)
        if m_fy_range:
            return f"FY{m_fy_range.group(2)}"

        m_fy_single = re.search(r"(?:fy|fiscal)\s*(?:20)?(\d{2})\b", p)
        if m_fy_single:
            return f"FY{m_fy_single.group(1)}"

        # Calendar year e.g. "as of march 31, 2024"
        m_as_of = re.search(r"(?:as of|ended)\s*([a-zA-Z]+ \d{1,2},? \d{4})", p)
        if m_as_of:
            return f"As of {m_as_of.group(1).title()}"

        return period.strip()
