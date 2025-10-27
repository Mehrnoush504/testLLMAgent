import os
import smtplib
from email.message import EmailMessage
from jinja2 import Template
from itsdangerous import TimestampSigner, BadSignature

HITL_SECRET = os.environ.get('HITL_SECRET', 'devsecret')
HITL_BASE_URL = os.environ.get('HITL_BASE_URL', 'http://localhost:8000')
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL', SMTP_USER)

signer = TimestampSigner(HITL_SECRET)

def make_token(action: str, sku: str):
    payload = f"{action}:{sku}"
    return signer.sign(payload.encode()).decode()

def verify_token(token: str, max_age: int = 60*60*24):
    try:
        payload = signer.unsign(token, max_age=max_age)
        return payload.decode()
    except BadSignature:
        return None

def confirm_url(sku: str):
    token = make_token('confirm', sku)
    return f"{HITL_BASE_URL}/hitl/confirm?token={token}&sku={sku}"

def reject_url(sku: str):
    token = make_token('reject', sku)
    return f"{HITL_BASE_URL}/hitl/reject?token={token}&sku={sku}"

def send_owner_email(owner_email: str, item: dict):
    subject = f"Reorder approval required — {item['sku']}"
    with open(os.path.join(os.path.dirname(__file__), 'templates', 'owner_email.html')) as f:
        tpl = Template(f.read())
    body_html = tpl.render(item=item, confirm_url=confirm_url(item['sku']), reject_url=reject_url(item['sku']))

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = owner_email
    msg.set_content(f"Open this email in HTML-capable client.")
    msg.add_alternative(body_html, subtype='html')

    # send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)

def send_supplier_email(to_email: str, subject: str, body: str, cc: list = None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    if cc:
        msg['Cc'] = ', '.join(cc)
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)
