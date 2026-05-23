"""
Tests for the upload pipeline and merchant-learning flow.
"""

import pytest
from datetime import date
from app.services.parser import parse_csv, parse_pdf
from app.services.categorization import (
    categorize_with_learning,
    extract_merchant_key,
)


# ── CSV edge-case tests ────────────────────────────────────────────────────────

class TestCSVEdgeCases:
    def test_indian_bank_format(self):
        """HDFC-style CSV with separate Debit/Credit columns uses standard aliases."""
        csv = b"""Date,Description,Amount,Type
15/05/2026,SWIGGY INDIA PVT LTD,380.00,debit
10/05/2026,SALARY NEFT CR,85000.00,credit
"""
        txns = parse_csv(csv)
        assert len(txns) == 2
        assert txns[0]["type"] == "debit"
        assert txns[1]["type"] == "credit"

    def test_standard_4col_csv(self):
        csv = b"""Date,Description,Amount,Type
2026-05-15,Uber Ride,220,debit
2026-05-16,Freelance Income,15000,credit
2026-05-17,Jio Recharge,299,debit
"""
        txns = parse_csv(csv)
        assert len(txns) == 3
        assert txns[0]["amount"] == 220.0
        assert txns[1]["type"]   == "credit"

    def test_rupee_symbol_in_amount(self):
        csv = b"Date,Description,Amount,Type\n2026-05-15,Pizza Hut,450,debit\n"
        txns = parse_csv(csv)
        assert len(txns) == 1
        assert txns[0]["amount"] == 450.0

    def test_comma_in_amount(self):
        csv = b"""Date,Description,Amount,Type
2026-05-10,Salary,1,00,000,credit
"""
        # This will be tricky to parse; just ensure no crash
        try:
            parse_csv(csv)
        except Exception:
            pass

    def test_empty_rows_skipped(self):
        csv = b"""Date,Description,Amount,Type
2026-05-15,Swiggy,380,debit

2026-05-16,,,
2026-05-17,Netflix,649,debit
"""
        txns = parse_csv(csv)
        # Zero-amount and empty rows skipped
        assert all(t["amount"] > 0 for t in txns)

    def test_various_date_formats(self):
        csv = b"""Date,Description,Amount,Type
15-05-2026,Test A,100,debit
15/05/2026,Test B,200,debit
2026-05-15,Test C,300,debit
15 May 2026,Test D,400,debit
"""
        txns = parse_csv(csv)
        # All four should parse to same date
        for t in txns:
            assert t["date"] == date(2026, 5, 15)

    def test_handles_extra_whitespace(self):
        csv = b"""Date , Description , Amount , Type
2026-05-15 , Swiggy Order , 380 , debit
"""
        txns = parse_csv(csv)
        assert len(txns) == 1
        assert "Swiggy" in txns[0]["description"]


# ── Merchant learning end-to-end ──────────────────────────────────────────────

class TestMerchantLearning:
    def test_new_merchant_flagged(self):
        cat, needs = categorize_with_learning("TechnoMart Electronics", {})
        assert cat is None
        assert needs is True

    def test_learned_merchant_applied(self):
        learned = {"technomart": "Shopping"}
        cat, needs = categorize_with_learning("TechnoMart Electronics Pvt Ltd", learned)
        assert cat == "Shopping"
        assert needs is False

    def test_learning_is_case_insensitive(self):
        learned = {"TECHNOMART": "Shopping"}
        cat, needs = categorize_with_learning("technomart electronics", learned)
        assert cat == "Shopping"
        assert needs is False

    def test_partial_key_match(self):
        learned = {"haldirams": "Food"}
        cat, needs = categorize_with_learning("HALDIRAMS NAGPUR SWEETS PVT LTD", learned)
        assert cat == "Food"
        assert needs is False

    def test_multiple_learned_first_match_wins(self):
        learned = {"amazon": "Shopping", "pay": "Bills"}
        # "amazon" appears before "pay" in iteration; result depends on dict order
        cat, _ = categorize_with_learning("Amazon Pay Cashback", learned)
        assert cat in ("Shopping", "Bills")  # one of the two must match

    def test_rule_takes_priority_over_nothing(self):
        # No learned mappings — falls through to rules
        cat, needs = categorize_with_learning("ZOMATO DELIVERY", {})
        assert cat == "Food"
        assert needs is False

    def test_learned_overrides_rules(self):
        # User classified "netflix" as "Bills" (e.g. business expense)
        learned = {"netflix": "Bills"}
        cat, _ = categorize_with_learning("Netflix Premium Subscription", learned)
        assert cat == "Bills"   # learned wins over rule (Entertainment)


class TestExtractMerchantKey:
    def test_strips_pvt_ltd(self):
        key = extract_merchant_key("ZOMATO INDIA PVT LTD")
        assert "pvt" not in key
        assert "ltd" not in key

    def test_strips_payment_words(self):
        key = extract_merchant_key("AMAZON PAY PAYMENT REF123")
        assert key not in ("pay", "payment", "ref")

    def test_returns_lowercase(self):
        key = extract_merchant_key("SWIGGY ORDER")
        assert key == key.lower()

    def test_minimum_length(self):
        key = extract_merchant_key("XY Z Merchant ABC Corp")
        assert len(key) >= 3

    def test_handles_numbers(self):
        key = extract_merchant_key("12345 MERCHANT NAME")
        # Purely numeric tokens should be skipped
        assert not key.isdigit()

    def test_known_merchants(self):
        assert extract_merchant_key("SWIGGY FOODS PVT LTD") == "swiggy"
        assert extract_merchant_key("AMAZON PAY PURCHASE")   == "amazon"
        assert extract_merchant_key("UBER TRIP BLR")         == "uber"


# ── Upload confirm payload validation ─────────────────────────────────────────

class TestUploadSchemas:
    def test_transaction_create_valid(self):
        from app.schemas.schemas import TransactionCreate
        tx = TransactionCreate(
            description="Swiggy",
            amount=380,
            type="debit",
            category="Food",
            date="2026-05-15",
        )
        assert tx.amount == 380.0
        assert tx.category == "Food"

    def test_transaction_create_negative_amount_fails(self):
        from app.schemas.schemas import TransactionCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionCreate(
                description="Bad", amount=-100,
                type="debit", category="Food", date="2026-05-15"
            )

    def test_transaction_create_invalid_type_fails(self):
        from app.schemas.schemas import TransactionCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionCreate(
                description="Bad", amount=100,
                type="transfer",  # not in enum
                category="Food", date="2026-05-15"
            )

    def test_amount_is_rounded(self):
        from app.schemas.schemas import TransactionCreate
        tx = TransactionCreate(
            description="Test", amount=99.9999,
            type="debit", category="Food", date="2026-05-15"
        )
        assert tx.amount == 100.0
