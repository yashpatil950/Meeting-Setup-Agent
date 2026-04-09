# main.py
import os, asyncio
from datetime import timedelta, datetime
from fastapi import FastAPI, Request, Form
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from services.gmail_client import list_recent_messages, read_message
from services.calendar_client import create_event
from services.whatsapp_client import send_whatsapp
from filters import is_relevant
from agent import extract_event
import store

load_dotenv()
store.init_db()
app = FastAPI()
scheduler = AsyncIOScheduler()

APP_BASE = os.getenv("APP_BASE_URL", "http://localhost:8000")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "90"))

def _fmt_preview(pid: int, c):
    when = c.start_iso or "(unknown time)"
    loc = c.location or (c.online_link or "TBD")
    return (f"Event #{pid}\n"
            f"Title: {c.title}\nWhen: {when}\nWhere: {loc}\n"
            f"Reply with: approve {pid}  OR  skip {pid}")

async def scan_email_once():
    # Look for likely invites
    print(f"[{datetime.now().isoformat()}] Scanning email...")
    msgs = list_recent_messages(q='newer_than:2d (invite OR meeting OR calendar OR event OR seminar OR colloquium)')
    for m in msgs:
        msg_id = m["id"]
        if store.seen_before(msg_id): 
            continue

        subject, body, meta = read_message(msg_id)
        # quick relevance filter
        if not is_relevant(subject, body):
            store.mark_seen(msg_id)
            continue

        # LLM extraction
        candidate = extract_event(subject, body, str(meta), msg_id)

        # best-effort defaults if end missing
        if candidate.start_iso and not candidate.end_iso:
            try:
                start = datetime.fromisoformat(candidate.start_iso)
                candidate.end_iso = (start + timedelta(hours=1)).isoformat()
            except:
                pass

        # queue for approval if we have at least title + start
        if candidate.title and candidate.start_iso:
            pid = store.add_pending({
                "message_id": msg_id,
                "title": candidate.title,
                "start_iso": candidate.start_iso,
                "end_iso": candidate.end_iso,
                "location": candidate.location,
                "online_link": candidate.online_link,
            })
            send_whatsapp(_fmt_preview(pid, candidate))

        store.mark_seen(msg_id)
    print(f"[{datetime.now().isoformat()}] Scan complete.")

@app.on_event("startup")
async def _startup():
    scheduler.add_job(scan_email_once, "interval", seconds=POLL_SECONDS, next_run_time=datetime.now())
    scheduler.start()

@app.post("/twilio/whatsapp")
async def twilio_webhook(
    Body: str = Form(""),
    From: str = Form(None),
    WaId: str = Form(None),
):
    incoming = (Body or "").strip().lower()

    if incoming.startswith("approve"):
        p = store.get_pending_by_phrase(incoming)
        if not p:
            # Quick ack so Twilio doesn't retry; we send outbound msg separately
            send_whatsapp("Couldn't find that pending ID. Try again.")
            return PlainTextResponse("OK", status_code=200)

        ev = create_event(p["title"], p["start_iso"], p["end_iso"], p["location"], p["online_link"])
        send_whatsapp(f"✅ Added to Calendar: {p['title']} ({ev.get('htmlLink','')})")
        store.delete_pending(p["id"])
        return PlainTextResponse("OK", status_code=200)

    if incoming.startswith("skip"):
        p = store.get_pending_by_phrase(incoming)
        if not p:
            send_whatsapp("Couldn't find that pending ID. Try again.")
            return PlainTextResponse("OK", status_code=200)

        store.delete_pending(p["id"])
        send_whatsapp(f"⏭️ Skipped #{p['id']}: {p['title']}")
        return PlainTextResponse("OK", status_code=200)

    # Fallback help text
    send_whatsapp("Reply 'approve <id>' or 'skip <id>' (e.g., approve 12)")
    return PlainTextResponse("OK", status_code=200)

@app.get("/")
def health():
    return {"status": "ok"}