# services/calendar_client.py
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from .gmail_client import SCOPES  # unified scopes (gmail + calendar)

CAL_SCOPES = SCOPES  # ensure same set

def _cal_creds() -> Credentials:
    token_path = "token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, CAL_SCOPES)
        # If token lacks calendar scope, refresh via InstalledAppFlow below
        if creds.scopes and set(creds.scopes) >= set(CAL_SCOPES):
            return creds

    # Either no token.json, or missing scopes → prompt once
    client_secret_path = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, CAL_SCOPES)
    creds = flow.run_local_server(port=8081, access_type="offline", prompt="consent")
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    return creds

def calendar_service():
    creds = _cal_creds()
    return build("calendar", "v3", credentials=creds)

def create_event(summary, start_iso, end_iso, location=None, online_link=None, description=None):
    cal_id = os.getenv("CALENDAR_ID", "primary")
    svc = calendar_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso or start_iso},  # fallback if needed
    }
    if location:
        event["location"] = location
    if online_link:
        # Put link in description; creating native Meet links requires different scope/flow
        event["description"] = (description or "") + f"\nJoin: {online_link}"
    elif description:
        event["description"] = description

    return svc.events().insert(calendarId=cal_id, body=event).execute()
