import os
import datetime
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from src.core.config import settings
from src.core.rag_engine import RAGClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.rag = RAGClient()
        self._authenticate()

    def _authenticate(self):
        token_path = Path(settings.KNOWLEDGE_BASE_PATH) / "token.json"
        creds_path = Path(settings.KNOWLEDGE_BASE_PATH) / "credentials.json"

        if token_path.exists():
            self.creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if creds_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                    self.creds = flow.run_local_server(port=0)
                else:
                    logger.warning("No credentials.json found. Calendar integration disabled.")
                    return

            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

        if self.creds:
            self.service = build('calendar', 'v3', credentials=self.creds)

    def get_todays_events(self):
        if not self.service:
            return []

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        # End of day
        end_of_day = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'

        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, timeMax=end_of_day,
            singleEvents=True, orderBy='startTime').execute()
        return events_result.get('items', [])

    def generate_briefing(self):
        if not self.service:
            logger.info("Calendar service not available. Skipping briefing.")
            return

        events = self.get_todays_events()
        if not events:
            logger.info("No events found for today.")
            return

        briefing_content = f"# Morning Briefing {datetime.date.today()}\n\n"

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')

            briefing_content += f"## 📅 {summary} ({start})\n"

            # RAG Context
            query = f"{summary} {description}"
            context = self.rag.search(query, n_results=2)

            if context:
                briefing_content += "### 🧠 Context from Knowledge Base\n"
                briefing_content += context + "\n\n"
            else:
                briefing_content += "_No relevant context found._\n\n"

        # Save briefing
        briefing_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Logs" / "Briefings" / f"{datetime.date.today()}_Briefing.md"
        briefing_path.parent.mkdir(parents=True, exist_ok=True)

        with open(briefing_path, "w", encoding="utf-8") as f:
            f.write(briefing_content)

        logger.info(f"Generated morning briefing: {briefing_path}")

if __name__ == "__main__":
    # Create dummy credentials for testing if needed
    cal = CalendarClient()
    cal.generate_briefing()
