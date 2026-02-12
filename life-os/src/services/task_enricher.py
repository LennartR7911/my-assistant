import time
import yaml
import logging
from pathlib import Path
from src.core.config import settings
from src.core.github_client import GitHubClient
from src.core.gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskEnricher:
    def __init__(self):
        self.github = GitHubClient()
        self.gemini = GeminiClient()
        self.context_cache = {} # Simple cache, could use TTL

    def load_project_contexts(self):
        """Loads all context.yaml files from Projects directory."""
        projects_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Projects"
        contexts = []
        if projects_path.exists():
            for context_file in projects_path.rglob("context.yaml"):
                try:
                    with open(context_file, "r") as f:
                        data = yaml.safe_load(f)
                        contexts.append(data)
                except Exception as e:
                    logger.warning(f"Failed to read context file {context_file}: {e}")
        return contexts

    def find_relevant_logs(self, keywords):
        """Scans recent logs for keywords."""
        logs_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Logs"
        relevant_snippets = []
        if logs_path.exists():
            # Check last 5 log files
            log_files = sorted(logs_path.glob("*.md"), reverse=True)[:5]
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Simple keyword matching (case-insensitive)
                        if any(kw.lower() in content.lower() for kw in keywords):
                            relevant_snippets.append(f"From {log_file.name}:\n{content[:500]}...") # Snippet
                except Exception as e:
                    logger.warning(f"Failed to read log file {log_file}: {e}")
        return "\n\n".join(relevant_snippets)

    def enrich_issue(self, issue):
        logger.info(f"Enriching issue #{issue.number}: {issue.title}")

        # 1. Gather Context
        project_contexts = self.load_project_contexts()

        # Extract keywords from title (simple split)
        keywords = issue.title.split()
        log_context = self.find_relevant_logs(keywords)

        # Format context for Gemini
        context_str = "Project Contexts:\n"
        for ctx in project_contexts:
            context_str += yaml.dump(ctx, sort_keys=False) + "\n---\n"

        context_str += f"\nRelevant Logs:\n{log_context}"

        # 2. Call Gemini
        prompt = f"""
        Taak: {issue.title}
        Beschrijving: {issue.body}

        Gebruik de bovenstaande context (Projecten en Logs) om deze taak te verrijken.
        Geef een korte samenvatting, identificeer de belangrijkste stakeholders (uit context.yaml), en geef 3 concrete actiepunten.
        """

        enrichment = self.gemini.generate_content(prompt, context=context_str)

        if enrichment:
            # 3. Post Comment
            comment_body = f"🤖 **AI Context Enrichment**\n\n{enrichment}"
            self.github.comment_on_issue(issue.number, comment_body)

            # 4. Add Label
            self.github.add_label(issue.number, "enriched")
            logger.info(f"Issue #{issue.number} enriched successfully.")

    def run_loop(self):
        logger.info("Starting Task Enricher loop...")
        while True:
            try:
                issues = self.github.get_issues(state='open')
                for issue in issues:
                    label_names = [l.name for l in issue.labels]
                    if "enriched" not in label_names:
                        self.enrich_issue(issue)
                        # Avoid hitting rate limits
                        time.sleep(5)

                logger.info("Enricher cycle complete. Sleeping for 60s.")
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in enricher loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    enricher = TaskEnricher()
    enricher.run_loop()
