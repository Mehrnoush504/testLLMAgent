from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.mailer import verify_token
from app.sheets import update_row_by_sku, append_po_log
from app.llm import draft_purchase_order
from app.mailer import send_supplier_email
import os
from datetime import datetime, timezone

app = FastAPI()

OWNER_EMAIL = os.environ.get('OWNER_EMAIL')

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/hitl/confirm')
async def hitl_confirm(token: str, sku: str):
    payload = verify_token(token)
    if not payload or not payload.startswith('confirm:'):
        raise HTTPException(status_code=403, detail='Invalid or expired token')
    # Process confirm path
    now = datetime.now(timezone.utc).isoformat()
    # update last_checked
    update_row_by_sku(sku, {'last_checked': now})

    # Read row again via sheets helper — simple approach: read_all_items and find sku
    from app.sheets import read_all_items
    items = read_all_items()
    item = next((i for i in items if i['sku'] == sku), None)
    if not item:
        raise HTTPException(status_code=404, detail='SKU not found')

    # Draft PO via LLM
    try:
        subj, body = draft_purchase_order(item, OWNER_EMAIL)
    except Exception as e:
        append_po_log(sku, f"LLM draft failed: {e} on {now}")
        raise HTTPException(status_code=500, detail='LLM drafting failed')

    # Send supplier email
    try:
        send_supplier_email(item['supplier_email'], subj, body, cc=[OWNER_EMAIL])
        append_po_log(sku, f"PO sent to {item['supplier_email']} at {now}: {subj}")
    except Exception as e:
        append_po_log(sku, f"Email to supplier failed: {e} on {now}")
        # alert owner — for simplicity we return error
        raise HTTPException(status_code=500, detail='Failed to send supplier email')

    return HTMLResponse(content=f"<html><body><h3>Confirmed and PO sent for {sku}</h3></body></html>")

@app.get('/hitl/reject')
async def hitl_reject(token: str, sku: str):
    payload = verify_token(token)
    if not payload or not payload.startswith('reject:'):
        raise HTTPException(status_code=403, detail='Invalid or expired token')
    now = datetime.now(timezone.utc).isoformat()
    update_row_by_sku(sku, {'last_checked': now, 'comments': 'Rejected by owner'})
    append_po_log(sku, f"Rejected by owner at {now}")
    return HTMLResponse(content=f"<html><body><h3>Rejected {sku}</h3></body></html>")
