"""
Smart Categorization Service
Layer 1 — Rule-based merchant keyword matching.
Layer 2 — User-trained merchant → category mapping (stored in Supabase).
"""

import re
from typing import Optional, Dict
from app.schemas.schemas import Category


# ── Layer 1: Built-in Rules ───────────────────────────────────────────────────
# Maps lowercase keyword substrings → Category.
# Ordered from most to least specific (first match wins).

RULES: Dict[str, str] = {
    # Food & Dining
    "swiggy":      Category.food,
    "zomato":      Category.food,
    "dominos":     Category.food,
    "domino":      Category.food,
    "mcdonald":    Category.food,
    "kfc":         Category.food,
    "pizza hut":   Category.food,
    "burger king": Category.food,
    "starbucks":   Category.food,
    "cafe coffee": Category.food,
    "dunzo":       Category.food,
    "blinkit":     Category.food,
    "instamart":   Category.food,
    "bigbasket":   Category.food,
    "grofers":     Category.food,
    "zepto":       Category.food,
    "restaurant":  Category.food,
    "dhaba":       Category.food,
    "hotel food":  Category.food,
    # Travel & Transport
    "uber":        Category.travel,
    "ola cabs":    Category.travel,
    "rapido":      Category.travel,
    "makemytrip":  Category.travel,
    "irctc":       Category.travel,
    "redbus":      Category.travel,
    "goibibo":     Category.travel,
    "yatra":       Category.travel,
    "cleartrip":   Category.travel,
    "indigo":      Category.travel,
    "spicejet":    Category.travel,
    "air india":   Category.travel,
    "petrol":      Category.travel,
    "fuel":        Category.travel,
    "parking":     Category.travel,
    # Shopping
    "amazon":      Category.shopping,
    "flipkart":    Category.shopping,
    "myntra":      Category.shopping,
    "ajio":        Category.shopping,
    "meesho":      Category.shopping,
    "nykaa":       Category.shopping,
    "snapdeal":    Category.shopping,
    "shopclues":   Category.shopping,
    "reliance digital": Category.shopping,
    "croma":       Category.shopping,
    "d-mart":      Category.shopping,
    "dmart":       Category.shopping,
    "big bazaar":  Category.shopping,
    # Bills & Utilities
    "airtel":      Category.bills,
    "jio":         Category.bills,
    "bsnl":        Category.bills,
    "vodafone":    Category.bills,
    "vi mobile":   Category.bills,
    "electricity": Category.bills,
    "bescom":      Category.bills,
    "tata power":  Category.bills,
    "piped gas":   Category.bills,
    "water bill":  Category.bills,
    "rent":        Category.bills,
    "maintenance": Category.bills,
    "insurance":   Category.bills,
    "lic":         Category.bills,
    "broadband":   Category.bills,
    "act fibernet": Category.bills,
    # Entertainment
    "netflix":      Category.entertainment,
    "spotify":      Category.entertainment,
    "hotstar":      Category.entertainment,
    "disney":       Category.entertainment,
    "youtube premium": Category.entertainment,
    "amazon prime": Category.entertainment,
    "zee5":         Category.entertainment,
    "sonyliv":      Category.entertainment,
    "pvr":          Category.entertainment,
    "inox":         Category.entertainment,
    "bookmyshow":   Category.entertainment,
    "gaming":       Category.entertainment,
    "steam":        Category.entertainment,
    # Health & Wellness
    "apollo":       Category.health,
    "practo":       Category.health,
    "pharmacy":     Category.health,
    "medplus":      Category.health,
    "netmeds":      Category.health,
    "1mg":          Category.health,
    "hospital":     Category.health,
    "clinic":       Category.health,
    "lab test":     Category.health,
    "diagnostics":  Category.health,
    "gym":          Category.health,
    "cult fit":     Category.health,
    # Investment
    "groww":        Category.investment,
    "zerodha":      Category.investment,
    "upstox":       Category.investment,
    "angel broking": Category.investment,
    "mutual fund":  Category.investment,
    "nps":          Category.investment,
    "ppf":          Category.investment,
    "sip":          Category.investment,
    "demat":        Category.investment,
    "smallcase":    Category.investment,
    "coin by zerodha": Category.investment,
    # Income signals
    "salary":       Category.income,
    "neft cr":      Category.income,
    "imps cr":      Category.income,
    "upi cr":       Category.income,
    "cashback":     Category.income,
    "refund":       Category.income,
    "credit int":   Category.income,
    "dividend":     Category.income,
    "freelance":    Category.income,
    "bonus":        Category.income,
}


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def categorize_by_rules(description: str) -> Optional[str]:
    """
    Layer 1: scan description against built-in keyword map.
    Returns a Category value string or None.
    """
    normalized = _normalize(description)
    for keyword, category in RULES.items():
        if keyword in normalized:
            return category
    return None


def categorize_with_learning(
    description: str,
    learned: Dict[str, str],
) -> tuple[Optional[str], bool]:
    """
    Full two-layer categorization.

    Returns:
        (category_string_or_None, needs_review_bool)
        needs_review = True  → send to user for classification
        needs_review = False → category was determined automatically
    """
    normalized = _normalize(description)

    # Layer 2 first — user-trained mappings take priority
    for merchant_key, category in learned.items():
        if merchant_key.lower() in normalized:
            return category, False

    # Layer 1 — built-in rules
    rule_cat = categorize_by_rules(description)
    if rule_cat:
        return rule_cat, False

    # Unknown merchant → needs user review
    return None, True


def extract_merchant_key(description: str) -> str:
    """
    Derive a short, reusable merchant key from a description.
    Used when saving to the merchant_learning table.
    e.g. "AMAZON PAY PURCHASE REF123" → "amazon"
    """
    normalized = _normalize(description)
    # Remove common noise words
    noise = r"\b(pvt|ltd|payment|purchase|transaction|ref|cr|dr|neft|imps|upi|order|booking|debit|credit|auto|pay|pos|atm)\b"
    cleaned = re.sub(noise, "", normalized).strip()
    # Take first meaningful word (≥ 3 chars)
    tokens = [t for t in cleaned.split() if len(t) >= 3 and not t.isdigit()]
    return tokens[0] if tokens else normalized[:20]
