import os
import openai

openai.api_key = os.environ.get('OPENAI_API_KEY')

def draft_purchase_order(item: dict, owner_email: str):
    """Use OpenAI API to draft a short PO text. Returns subject, body."""
    prompt = f"Draft a clear purchase order for the supplier.\n\nItem SKU: {item['sku']}\nDescription: {item['description']}\nQuantity: {item['reorder_qty']}\nDeliver to: {owner_email}\nSupplier: {item.get('supplier_name') or ''}\n\nRespond with a subject line on first line prefixed SUBJECT: and then the body."

    resp = openai.Completion.create(
        model='text-davinci-003',
        prompt=prompt,
        max_tokens=300,
        temperature=0.2,
    )
    text = resp.choices[0].text.strip()
    # parse simple SUBJECT: ...\nBODY:\n...
    if text.startswith('SUBJECT:'):
        try:
            subject, body = text.split('\n', 1)
            subject = subject.replace('SUBJECT:', '').strip()
            body = body.strip()
        except ValueError:
            subject = f"Purchase Order — {item['sku']}"
            body = text
    else:
        subject = f"Purchase Order — {item['sku']}"
        body = text
    return subject, body
