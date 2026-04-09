# services/whatsapp_client.py
import os
from twilio.rest import Client

def send_whatsapp(body: str):
    acc = os.getenv("TWILIO_ACCOUNT_SID")
    tok = os.getenv("TWILIO_AUTH_TOKEN")
    from_ = os.getenv("WHATSAPP_FROM")
    to = os.getenv("WHATSAPP_TO")
    c = Client(acc, tok)
    c.messages.create(from_=from_, to=to, body=body)