# services/gmail_client.py
import os, base64, re
from typing import List, Dict, Tuple
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

def _load_creds() -> Credentials:
    token_path = "token.json"
    client_secret_path = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")

    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path, SCOPES)

    # Prefer the real secrets file if present
    if os.path.exists(client_secret_path):
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    else:
        # Fallback to env-based config (INCLUDES client_secret!)
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost")
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "project_id": "email-meeting-agent",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            SCOPES
        )

    # Local loopback server for consent; keeps refresh token
    creds = flow.run_local_server(port=8081, access_type="offline", prompt="consent")
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    return creds

    token_path = "token.json"
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")

    if os.path.exists(token_path):
        return Credentials.from_authorized_user_file(token_path, SCOPES)

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "project_id": "email-meeting-agent",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }, SCOPES
    )
    creds = flow.run_local_server(port=8081)
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    return creds

def gmail_service():
    creds = _load_creds()
    return build("gmail", "v1", credentials=creds)

def list_recent_messages(q: str = None, max_results: int = 15) -> List[Dict]:
    svc = gmail_service()
    res = svc.users().messages().list(userId="me", q=q or "", maxResults=max_results).execute()
    return res.get("messages", [])

def read_message(msg_id: str) -> Tuple[str, str, Dict]:
    svc = gmail_service()
    msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    subject = headers.get("Subject", "(no subject)")

    # best-effort body extraction
    def _walk_parts(p):
        if p.get("mimeType", "").startswith("text/plain") and "data" in p.get("body", {}):
            return base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8", errors="ignore")
        if "parts" in p:
            for c in p["parts"]:
                t = _walk_parts(c)
                if t: return t
        return ""

    body = _walk_parts(msg["payload"]) or ""
    meta = {
        "From": headers.get("From"), "To": headers.get("To"),
        "Date": headers.get("Date"), "Message-Id": headers.get("Message-Id", msg_id)
    }
    return subject, body, meta