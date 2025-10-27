# Automated Re-Order Concierge

Automates low-stock detection, uses a human-in-the-loop (HITL) owner approval, drafts POs using an LLM, and logs results in a Google Sheet.

## Features
- Hourly inventory check (scheduler)
- Only process items last checked > 24h ago
- Sends owner email with Confirm / Reject links (one-click)
- On Confirm: update sheet, draft PO with LLM, send supplier email, log PO
- On Reject: update sheet with comment
- Error handling & owner alerts

## Setup
1. Create a Python 3.10+ virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
