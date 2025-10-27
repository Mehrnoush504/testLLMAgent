"""
Helpers for reading and writing the Google Sheet.
Assumes a Google service account JSON file and that the sheet is shared with the service account email.
"""
import os
import gspread
from datetime import datetime, timezone

GOOGLE_SA_JSON = os.environ.get("GOOGLE_SA_JSON")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "inventory")

if not GOOGLE_SA_JSON:
    raise RuntimeError("Set GOOGLE_SA_JSON in env pointing to service account json path")

gc = gspread.service_account(filename=GOOGLE_SA_JSON)
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

COLS = {
    'sku': 1,
    'description': 2,
    'on_hand_qty': 3,
    'reorder_threshold': 4,
    'last_checked': 5,
    'supplier_email': 6,
    'supplier_name': 7,
    'reorder_qty': 8,
    'comments': 9,
    'po_log': 10,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_all_items():
    """Return list of dict rows. First row assumed header (will be skipped by gspread's get_all_records())."""
    rows = worksheet.get_all_records()
    # Normalize rows — ensure keys are consistent
    out = []
    for r in rows:
        # convert numeric fields safely
        try:
            on_hand = int(r.get('on_hand_qty') or 0)
        except Exception:
            on_hand = 0
        try:
            reorder_threshold = int(r.get('reorder_threshold') or 0)
        except Exception:
            reorder_threshold = 0
        out.append({
            'sku': r.get('sku'),
            'description': r.get('description'),
            'on_hand_qty': on_hand,
            'reorder_threshold': reorder_threshold,
            'last_checked': r.get('last_checked'),
            'supplier_email': r.get('supplier_email'),
            'supplier_name': r.get('supplier_name'),
            'reorder_qty': int(r.get('reorder_qty') or 0),
            'comments': r.get('comments') or '',
            'po_log': r.get('po_log') or '',
        })
    return out


def update_row_by_sku(sku, updates: dict):
    """Find row index containing sku and update given columns. updates keys are column names matching header.
    """
    cell = worksheet.find(sku)
    if not cell:
        raise ValueError(f"SKU {sku} not found")
    row_idx = cell.row
    for k, v in updates.items():
        col_idx = COLS.get(k)
        if not col_idx:
            continue
        worksheet.update_cell(row_idx, col_idx, v)

def append_po_log(sku, text):
    """Append text to po_log column for sku"""
    cell = worksheet.find(sku)
    if not cell:
        raise ValueError(f"SKU {sku} not found")
    row_idx = cell.row
    col_idx = COLS['po_log']
    old = worksheet.cell(row_idx, col_idx).value or ''
    new = (old + '\n' + text).strip()
    worksheet.update_cell(row_idx, col_idx, new)
