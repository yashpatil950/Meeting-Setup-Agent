# Meeting Setup Agent

An intelligent agent that monitors your Gmail for meeting invitations, extracts event details using AI, and allows you to approve or skip events via WhatsApp before adding them to your Google Calendar.

## Features

- 📧 **Gmail Monitoring**: Automatically scans Gmail for meeting invitations
- 🤖 **AI-Powered Extraction**: Uses OpenAI to extract event details from emails
- 📱 **WhatsApp Integration**: Sends previews via WhatsApp for approval/skip decisions
- 📅 **Google Calendar**: Automatically creates calendar events when approved
- 🔄 **Smart Filtering**: Focuses on CS/TAMU related meetings and events

## Setup

### 1. Environment Variables

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=sk-...
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8081/
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+1XXXXXXXXXX
APP_BASE_URL=http://localhost:8000
POLL_SECONDS=90
CALENDAR_ID=primary
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
uvicorn main:app --reload --port 8000
```

### 4. Google OAuth Setup

On first run, visit the authorization URL that appears in the console to grant Gmail and Calendar permissions.

### 5. Twilio WhatsApp Setup

1. Install ngrok: `brew install ngrok/ngrok/ngrok`
2. Start ngrok: `ngrok http 8000`
3. Configure Twilio webhook: `https://xxxxx.ngrok.io/twilio/whatsapp`

## Usage

1. Send yourself a CS/TAMU meeting email
2. Within ~90 seconds, you'll receive a WhatsApp notification:
   ```
   Event #12
   Title: CS Seminar — Distributed Systems @ TAMU
   When: 2025-09-15T14:00:00-05:00
   Where: HRBB 124
   Reply with: approve 12  OR  skip 12
   ```
3. Reply with `approve 12` to add to calendar or `skip 12` to ignore

## Architecture -

- **FastAPI**: Web server and API endpoints
- **APScheduler**: Email polling every 90 seconds
- **OpenAI GPT-4**: Event extraction from email content
- **Google APIs**: Gmail reading and Calendar event creation
- **Twilio**: WhatsApp messaging
- **SQLite**: Local storage for seen emails and pending events

## API Endpoints

- `GET /`: Health check
- `POST /twilio/whatsapp`: Twilio webhook for WhatsApp messages

## Project Structure

```
├── main.py                 # FastAPI application and email scanning
├── agent.py               # AI-powered event extraction
├── filters.py             # Email relevance filtering
├── store.py               # SQLite database operations
├── services/
│   ├── gmail_client.py    # Gmail API integration
│   ├── calendar_client.py # Google Calendar integration
│   └── whatsapp_client.py # Twilio WhatsApp integration
└── requirements.txt       # Python dependencies
```
# Meeting-Setup-Agent
