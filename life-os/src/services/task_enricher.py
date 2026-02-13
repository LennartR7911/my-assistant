import time
import yaml
import logging
from pathlib import Path
from src.core.config import settings
from src.core.github_client import GitHubClient
from src.core.gemini_client import GeminiClient
from src.core.rag_engine import RAGClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskEnricher:
    def __init__(self):
        self.github = GitHubClient()
        self.gemini = GeminiClient()
        self.rag = RAGClient()
        # Initial index on startup
        try:
            self.rag.index_knowledge_base()
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")

    def enrich_issue(self, issue):
        logger.info(f"Enriching issue #{issue.number}: {issue.title}")

        # 1. Gather Context via RAG
        query = f"{issue.title} {issue.body}"
        rag_context = self.rag.search(query, n_results=5)

        # Format context for Gemini
        context_str = f"Relevant Knowledge Base Context:\n{rag_context}"

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
