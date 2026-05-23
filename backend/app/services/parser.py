"""
File Parsing Service
Handles CSV (via pandas) and PDF (via pdfplumber) bank statement parsing.
Returns a list of raw transaction dicts for the categorization layer.
"""

import re
import uuid
import io
from datetime import date, datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import pdfplumber


# ── CSV Parsing ───────────────────────────────────────────────────────────────

# Common column name aliases across different bank formats
DATE_COLS   = ["date", "txn date", "transaction date", "value date", "posting date"]
DESC_COLS   = ["description", "narration", "particulars", "details", "remarks", "payee"]
AMOUNT_COLS = ["amount", "txn amount", "transaction amount", "debit", "credit"]
TYPE_COLS   = ["type", "dr/cr", "debit/credit", "transaction type"]


def _clean_amount(val) -> float:
    """Strip currency symbols, commas; return float."""
    if pd.isna(val):
        return 0.0
    return float(re.sub(r"[₹$,\s]", "", str(val).strip()) or 0)


def _parse_date(val) -> Optional[date]:
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Find the first matching column name (case-insensitive)."""
    lower_cols = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_cols:
            return lower_cols[name.lower()]
    return None


def parse_csv(content: bytes) -> List[Dict[str, Any]]:
    """
    Parse a CSV bank statement.
    Supports multiple column-name conventions used by Indian banks.
    """
    try:
        df = pd.read_csv(io.BytesIO(content), skip_blank_lines=True)
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")

    df.columns = [str(c).strip() for c in df.columns]
    df.dropna(how="all", inplace=True)

    date_col   = _find_col(df, DATE_COLS)
    desc_col   = _find_col(df, DESC_COLS)
    amount_col = _find_col(df, AMOUNT_COLS)
    type_col   = _find_col(df, TYPE_COLS)

    if not (date_col and desc_col and amount_col):
        raise ValueError(
            "CSV must have columns for date, description, and amount. "
            f"Found: {list(df.columns)}"
        )

    transactions = []
    for _, row in df.iterrows():
        amount = _clean_amount(row.get(amount_col))
        if amount <= 0:
            continue

        parsed_date = _parse_date(row.get(date_col))
        if not parsed_date:
            continue

        desc = str(row.get(desc_col, "")).strip() or "Unknown"

        # Determine type: explicit column, or separate debit/credit columns
        tx_type = "debit"
        if type_col:
            raw_type = str(row.get(type_col, "")).lower()
            if any(k in raw_type for k in ["cr", "credit", "in"]):
                tx_type = "credit"
        elif "credit" in df.columns and "debit" in df.columns:
            credit_val = _clean_amount(row.get("credit", 0))
            debit_val  = _clean_amount(row.get("debit", 0))
            if credit_val > 0:
                amount, tx_type = credit_val, "credit"
            elif debit_val > 0:
                amount, tx_type = debit_val, "debit"

        transactions.append({
            "temp_id":     str(uuid.uuid4()),
            "date":        parsed_date,
            "description": desc,
            "amount":      round(amount, 2),
            "type":        tx_type,
        })

    return transactions


# ── PDF Parsing ───────────────────────────────────────────────────────────────

# Pattern: date  description  amount  [Dr/Cr]
TRANSACTION_PATTERN = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"       # date
    r"\s+"
    r"(.+?)"                                   # description (lazy)
    r"\s+"
    r"([\d,]+(?:\.\d{2})?)"                   # amount
    r"(?:\s+(Dr|Cr|DR|CR|debit|credit))?"     # optional type
    r"\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_pdf(content: bytes) -> List[Dict[str, Any]]:
    """
    Parse a PDF bank statement using pdfplumber.
    Attempts table extraction first; falls back to regex on raw text.
    """
    transactions = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            # Try structured table first (most modern bank statements)
            tables = page.extract_tables()
            for table in tables:
                txns = _parse_table(table)
                transactions.extend(txns)

            # If no table found, use regex on raw text
            if not tables:
                text = page.extract_text() or ""
                txns = _parse_text(text)
                transactions.extend(txns)

    if not transactions:
        raise ValueError(
            "Could not extract transactions from PDF. "
            "Please ensure the file is a text-based (not scanned) bank statement."
        )

    # Deduplicate by (date, amount, description)
    seen = set()
    unique = []
    for tx in transactions:
        key = (tx["date"], tx["amount"], tx["description"][:20])
        if key not in seen:
            seen.add(key)
            unique.append(tx)

    return unique


def _parse_table(table: List[List]) -> List[Dict]:
    """Extract transactions from a pdfplumber table."""
    if not table or len(table) < 2:
        return []

    header = [str(h or "").lower().strip() for h in table[0]]
    rows   = table[1:]
    results = []

    date_idx   = next((i for i, h in enumerate(header) if any(d in h for d in ["date"])), None)
    desc_idx   = next((i for i, h in enumerate(header) if any(d in h for d in ["desc", "narration", "particular", "detail"])), None)
    amt_idx    = next((i for i, h in enumerate(header) if any(d in h for d in ["amount", "amt", "debit", "credit"])), None)
    type_idx   = next((i for i, h in enumerate(header) if any(d in h for d in ["type", "dr", "cr"])), None)

    if None in (date_idx, desc_idx, amt_idx):
        return []

    for row in rows:
        try:
            if len(row) <= max(filter(None, [date_idx, desc_idx, amt_idx])):
                continue
            parsed_date = _parse_date(row[date_idx])
            amount      = _clean_amount(row[amt_idx])
            desc        = str(row[desc_idx] or "").strip()

            if not parsed_date or amount <= 0 or not desc:
                continue

            tx_type = "debit"
            if type_idx and type_idx < len(row):
                raw = str(row[type_idx] or "").lower()
                if "cr" in raw or "credit" in raw:
                    tx_type = "credit"

            results.append({
                "temp_id":     str(uuid.uuid4()),
                "date":        parsed_date,
                "description": desc,
                "amount":      round(amount, 2),
                "type":        tx_type,
            })
        except Exception:
            continue

    return results


def _parse_text(text: str) -> List[Dict]:
    """Fallback: regex-based extraction from raw PDF text."""
    results = []
    for m in TRANSACTION_PATTERN.finditer(text):
        parsed_date = _parse_date(m.group(1))
        amount      = _clean_amount(m.group(3))
        if not parsed_date or amount <= 0:
            continue
        raw_type = (m.group(4) or "").lower()
        tx_type  = "credit" if "cr" in raw_type or "credit" in raw_type else "debit"
        results.append({
            "temp_id":     str(uuid.uuid4()),
            "date":        parsed_date,
            "description": m.group(2).strip(),
            "amount":      round(amount, 2),
            "type":        tx_type,
        })
    return results
