"""
Unit tests for Fact Normalizer: Currency, Tonnage, Parcels, Percentages, Periods, and Metrics.
"""

import pytest
from app.services.fact_normalizer import FactNormalizer


def test_currency_normalization_crore_to_million():
    # ₹1 crore = 10 million
    val, unit = FactNormalizer.normalize_value_and_unit("1", "INR crore", "revenue_from_services")
    assert val == 10.0
    assert unit == "INR million"

    # ₹8,142 crore -> 81,420 million
    val, unit = FactNormalizer.normalize_value_and_unit("8,142", "INR crore", "revenue_from_services")
    assert val == 81420.0
    assert unit == "INR million"

    # ₹127 Cr -> 1,270 million
    val, unit = FactNormalizer.normalize_value_and_unit("127", "Cr", "ebitda")
    assert val == 1270.0
    assert unit == "INR million"


def test_currency_normalization_million_unchanged():
    # ₹81,415 million stays 81,415 million
    val, unit = FactNormalizer.normalize_value_and_unit("81,415", "INR million", "revenue_from_services")
    assert val == 81415.0
    assert unit == "INR million"

    # With decimal: 81,415.38
    val, unit = FactNormalizer.normalize_value_and_unit("81,415.38", "INR million", "revenue_from_services")
    assert val == 81415.38
    assert unit == "INR million"


def test_parentheses_negative_numbers():
    val = FactNormalizer.parse_numeric_string("(452)")
    assert val == -452.0

    val = FactNormalizer.parse_numeric_string("(4,516)")
    assert val == -4516.0

    norm_val, norm_unit = FactNormalizer.normalize_value_and_unit("(452)", "Cr", "ebitda")
    assert norm_val == -4520.0
    assert norm_unit == "INR million"


def test_tonnage_normalization():
    # 1,429K tonnes -> 1,429,000 tonnes
    val, unit = FactNormalizer.normalize_value_and_unit("1,429", "K tonnes", "ptl_freight_tonnage")
    assert val == 1429000.0
    assert unit == "tonnes"

    # 1.4 Mn Tons -> 1,400,000 tonnes
    val, unit = FactNormalizer.normalize_value_and_unit("1.4", "Mn Tons", "ptl_freight_tonnage")
    assert val == 1400000.0
    assert unit == "tonnes"


def test_parcel_shipments_normalization():
    # 740 Mn -> 740.0 million
    val, unit = FactNormalizer.normalize_value_and_unit("740", "Mn", "express_parcel_shipments")
    assert val == 740.0
    assert unit == "million"

    # 2.8 Bn -> 2,800.0 million
    val, unit = FactNormalizer.normalize_value_and_unit("2.8", "Bn", "express_parcel_shipments")
    assert val == 2800.0
    assert unit == "million"


def test_period_normalization():
    # Fiscal years
    assert FactNormalizer.normalize_period("FY 2023-24") == "FY24"
    assert FactNormalizer.normalize_period("FY 2024") == "FY24"
    assert FactNormalizer.normalize_period("Fiscal 2024") == "FY24"
    assert FactNormalizer.normalize_period("FY24") == "FY24"
    assert FactNormalizer.normalize_period("FY23") == "FY23"
    assert FactNormalizer.normalize_period("FY 2020-21") == "FY21"

    # Quarters
    assert FactNormalizer.normalize_period("Q4 FY24") == "Q4 FY24"
    assert FactNormalizer.normalize_period("Q4 FY 2024") == "Q4 FY24"
    assert FactNormalizer.normalize_period("Q1 FY23") == "Q1 FY23"

    # Inception
    assert FactNormalizer.normalize_period("since inception") == "Inception to Date"


def test_predicate_normalization():
    assert FactNormalizer.normalize_predicate("Revenue from services") == "revenue_from_services"
    assert FactNormalizer.normalize_predicate("revenue from operations") == "revenue_from_services"
    assert FactNormalizer.normalize_predicate("sale of services") == "revenue_from_services"
    assert FactNormalizer.normalize_predicate("Express parcels shipped") == "express_parcel_shipments"
    assert FactNormalizer.normalize_predicate("PTL freight delivered") == "ptl_freight_tonnage"
    assert FactNormalizer.normalize_predicate("NWC days") == "net_working_capital_days"
    assert FactNormalizer.normalize_predicate("Pin codes covered") == "pin_code_reach"
