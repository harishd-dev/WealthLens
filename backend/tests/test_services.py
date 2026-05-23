"""
Backend Unit Tests
Run: pytest tests/ -v
"""

import pytest
from datetime import date
from app.services.categorization import (
    categorize_by_rules,
    categorize_with_learning,
    extract_merchant_key,
)
from app.services.parser import parse_csv, _parse_date, _clean_amount


# ── Categorization Tests ──────────────────────────────────────────────────────

class TestCategorizeByRules:
    def test_food_swiggy(self):
        assert categorize_by_rules("SWIGGY ORDER #1234") == "Food"

    def test_food_zomato(self):
        assert categorize_by_rules("Zomato Technologies India") == "Food"

    def test_travel_uber(self):
        assert categorize_by_rules("UBER TRIP - DL123") == "Travel"

    def test_travel_irctc(self):
        assert categorize_by_rules("IRCTC Rail Booking") == "Travel"

    def test_shopping_amazon(self):
        assert categorize_by_rules("Amazon Pay Purchase") == "Shopping"

    def test_shopping_flipkart(self):
        assert categorize_by_rules("FLIPKART INTERNET PVT") == "Shopping"

    def test_bills_airtel(self):
        assert categorize_by_rules("Airtel Postpaid Bill") == "Bills"

    def test_entertainment_netflix(self):
        assert categorize_by_rules("Netflix subscription monthly") == "Entertainment"

    def test_health_apollo(self):
        assert categorize_by_rules("Apollo Pharmacy Purchase") == "Health"

    def test_investment_groww(self):
        assert categorize_by_rules("Groww Mutual Fund SIP") == "Investment"

    def test_income_salary(self):
        assert categorize_by_rules("Salary Credit May 2026") == "Income"

    def test_unknown_returns_none(self):
        assert categorize_by_rules("Random Merchant XYZ 9921") is None

    def test_case_insensitive(self):
        assert categorize_by_rules("SWIGGY") == "Food"
        assert categorize_by_rules("swiggy") == "Food"
        assert categorize_by_rules("Swiggy") == "Food"


class TestCategorizeWithLearning:
    def test_learned_mapping_takes_priority(self):
        learned = {"pizza corner": "Food"}
        cat, needs_review = categorize_with_learning("Pizza Corner Order", learned)
        assert cat == "Food"
        assert needs_review is False

    def test_falls_through_to_rules(self):
        cat, needs_review = categorize_with_learning("Swiggy Dinner Order", {})
        assert cat == "Food"
        assert needs_review is False

    def test_unknown_merchant_needs_review(self):
        cat, needs_review = categorize_with_learning("Some Obscure Merchant 12345", {})
        assert cat is None
        assert needs_review is True

    def test_learned_beats_rules(self):
        # User reclassified "amazon" as Shopping (already in rules), but
        # a learned key should override if it matches first
        learned = {"testmerchant": "Health"}
        cat, _ = categorize_with_learning("TestMerchant Clinic", learned)
        assert cat == "Health"


class TestExtractMerchantKey:
    def test_simple_name(self):
        key = extract_merchant_key("SWIGGY FOODS PVT LTD")
        assert key == "swiggy"

    def test_strips_noise(self):
        key = extract_merchant_key("AMAZON PAY PURCHASE REF123456")
        assert key == "amazon"

    def test_filters_short_tokens(self):
        key = extract_merchant_key("XY LARGE MERCHANT NAME")
        # "XY" is 2 chars and skipped; first ≥3-char word is "large"
        assert len(key) >= 3


# ── Parser Tests ──────────────────────────────────────────────────────────────

class TestParseDate:
    def test_iso_format(self):
        assert _parse_date("2026-05-15") == date(2026, 5, 15)

    def test_indian_slash(self):
        assert _parse_date("15/05/2026") == date(2026, 5, 15)

    def test_indian_dash(self):
        assert _parse_date("15-05-2026") == date(2026, 5, 15)

    def test_text_month(self):
        assert _parse_date("15 May 2026") == date(2026, 5, 15)

    def test_invalid_returns_none(self):
        assert _parse_date("not-a-date") is None


class TestCleanAmount:
    def test_plain_number(self):
        assert _clean_amount("1234.56") == 1234.56

    def test_with_rupee_symbol(self):
        assert _clean_amount("₹1,234.56") == 1234.56

    def test_with_commas(self):
        assert _clean_amount("1,00,000") == 100000.0

    def test_with_dollar(self):
        assert _clean_amount("$500") == 500.0

    def test_empty_returns_zero(self):
        assert _clean_amount("") == 0.0

    def test_nan_returns_zero(self):
        import math
        assert _clean_amount(float("nan")) == 0.0


class TestParseCSV:
    VALID_CSV = b"""Date,Description,Amount,Type
2026-05-15,Swiggy Order,380,debit
2026-05-10,Salary Credit,85000,credit
2026-05-08,Amazon Purchase,2499,debit
"""
    def test_parses_all_rows(self):
        txns = parse_csv(self.VALID_CSV)
        assert len(txns) == 3

    def test_types_correct(self):
        txns = parse_csv(self.VALID_CSV)
        assert txns[0]["type"] == "debit"
        assert txns[1]["type"] == "credit"

    def test_amounts_correct(self):
        txns = parse_csv(self.VALID_CSV)
        assert txns[0]["amount"] == 380.0
        assert txns[1]["amount"] == 85000.0

    def test_dates_parsed(self):
        txns = parse_csv(self.VALID_CSV)
        assert txns[0]["date"] == date(2026, 5, 15)

    def test_descriptions_preserved(self):
        txns = parse_csv(self.VALID_CSV)
        assert "Swiggy" in txns[0]["description"]

    def test_skips_zero_amount_rows(self):
        csv_with_zero = b"""Date,Description,Amount,Type
2026-05-15,Swiggy Order,0,debit
2026-05-10,Salary,85000,credit
"""
        txns = parse_csv(csv_with_zero)
        assert len(txns) == 1

    def test_invalid_csv_raises(self):
        with pytest.raises(Exception):
            parse_csv(b"this is not csv at all\x00\xff")
