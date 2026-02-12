import datetime
from pathlib import Path
from src.core.config import settings
from src.core.github_client import GitHubClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_daily_log():
    today = datetime.date.today()
    log_filename = f"{today.strftime('%Y-%m-%d')}.md"
    log_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Logs" / log_filename

    if log_path.exists():
        logger.info(f"Daily log for {today} already exists.")
        return

    logger.info(f"Generating daily log for {today}...")

    # Fetch Prio 1 issues
    github_client = GitHubClient()
    # Assuming 'P1' label for priority 1.
    # Adjust label name as per user's convention.
    issues = github_client.get_issues(state='open', labels=['P1'])

    tasks_list = ""
    if issues:
        for issue in issues:
            tasks_list += f"- [ ] #{issue.number} {issue.title}\n"
    else:
        tasks_list = "- [ ] Geen Prio 1 taken gevonden.\n"

    content = f"""# Logboek {today.strftime('%Y-%m-%d')}

## 🎯 Focus van Vandaag (Gegenereerd door AI uit GitHub Prio 1 taken)
{tasks_list}
## 🧠 Brain Dump
(Hier typ ik losse ideeën)
"""

    try:
        # Ensure Logs directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Created daily log: {log_path}")
    except Exception as e:
        logger.error(f"Error creating daily log: {e}")

if __name__ == "__main__":
    generate_daily_log()
