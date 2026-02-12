import time
import json
import shutil
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.core.config import settings
from src.core.gemini_client import GeminiClient
from src.core.github_client import GitHubClient
import logging
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InboxHandler(FileSystemEventHandler):
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.github_client = GitHubClient()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        # Ignore temporary files
        if filepath.name.startswith('.'):
            return

        logger.info(f"New file detected: {filepath}")

        # Small delay to ensure file write is complete
        time.sleep(2)

        try:
            if filepath.suffix.lower() == '.mp3':
                self.handle_audio(filepath)
            elif filepath.suffix.lower() == '.txt':
                self.handle_text(filepath)
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}")

    def handle_audio(self, filepath):
        logger.info(f"Processing audio: {filepath}")
        prompt = "Transcribeer deze audio en vat samen. Focus op besluiten en actiepunten. Format as Markdown."

        summary = self.gemini_client.process_audio(filepath, prompt)

        if summary:
            today = datetime.date.today().strftime('%Y-%m-%d')
            note_filename = f"{today}_Meeting.md"
            note_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Meeting_Notes" / note_filename

            # Append if exists or create new with timestamp
            mode = "a" if note_path.exists() else "w"
            with open(note_path, mode, encoding="utf-8") as f:
                f.write(f"\n\n# Meeting Note ({datetime.datetime.now().strftime('%H:%M')})\n")
                f.write(summary)

            logger.info(f"Meeting notes saved to {note_path}")

            # Archive
            archive_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Archive" / "Audio" / filepath.name
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(filepath), str(archive_path))
            logger.info(f"Moved audio to {archive_path}")

    def handle_text(self, filepath):
        logger.info(f"Processing text: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        prompt = """
        Analyseer de volgende tekst en haal actiepunten eruit.
        Geef het antwoord ALLEEN als een JSON list van objecten.
        Elk object moet deze velden hebben:
        - title: Korte titel van de taak
        - body: Beschrijving met context
        - labels: Lijst van labels (bijv. ["todo", "from-text"])

        Tekst:
        """

        response = self.gemini_client.generate_content(prompt, context=content)

        if response:
            try:
                # Clean markdown code blocks if present
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.startswith("```"):
                    json_str = json_str[3:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]

                actions = json.loads(json_str.strip())

                if isinstance(actions, list):
                    for action in actions:
                        self.github_client.create_issue(
                            title=action.get("title", "New Task"),
                            body=action.get("body", ""),
                            labels=action.get("labels", [])
                        )

                # Archive
                archive_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Archive" / "Raw" / filepath.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(filepath), str(archive_path))
                logger.info(f"Moved text to {archive_path}")

            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Gemini response: {response}")

def start_input_watcher():
    path = Path(settings.KNOWLEDGE_BASE_PATH) / "Inbox"
    path.mkdir(parents=True, exist_ok=True)

    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=False)
    observer.start()
    logger.info(f"Started watching {path}")
    return observer
