import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
from pathlib import Path
import time
import sys
import logging

# Setup test environment
test_kb_path = Path("test_kb")
if test_kb_path.exists():
    shutil.rmtree(test_kb_path)
test_kb_path.mkdir(exist_ok=True)

# Set dummy env vars BEFORE importing config
os.environ["GOOGLE_API_KEY"] = "dummy_key"
os.environ["GITHUB_TOKEN"] = "dummy_token"
os.environ["GITHUB_REPO"] = "owner/repo"
os.environ["KNOWLEDGE_BASE_PATH"] = str(test_kb_path)

# Add life-os to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import settings
from src.services.project_manager import create_project
from src.services.daily_setup import generate_daily_log
from src.services.input_handler import InboxHandler
from src.services.task_enricher import TaskEnricher
from src.core.github_client import GitHubClient
from src.core.gemini_client import GeminiClient

logging.disable(logging.CRITICAL)

class TestLifeOS(unittest.TestCase):
    def setUp(self):
        # Ensure test directory exists (it should, but just in case tearDown removed it)
        if not test_kb_path.exists():
            test_kb_path.mkdir()

        # Override settings path to absolute path of test dir just to be sure
        self.original_kb_path = settings.KNOWLEDGE_BASE_PATH
        settings.KNOWLEDGE_BASE_PATH = test_kb_path

    def tearDown(self):
        settings.KNOWLEDGE_BASE_PATH = self.original_kb_path
        # Clean up files inside, but maybe keep directory to avoid import error on re-run?
        # No, re-run is a new process.
        if test_kb_path.exists():
            shutil.rmtree(test_kb_path)

    def test_create_project(self):
        create_project("TestProject", "TestClient")
        project_path = test_kb_path / "Projects" / "TestClient" / "TestProject"
        self.assertTrue(project_path.exists())
        self.assertTrue((project_path / "01_Admin" / "context.yaml").exists())

    @patch('src.services.daily_setup.GitHubClient')
    def test_daily_log(self, MockGithub):
        mock_gh = MockGithub.return_value
        # Mock issue object
        issue = MagicMock()
        issue.number = 1
        issue.title = "Prio Task"
        mock_gh.get_issues.return_value = [issue]

        generate_daily_log()

        today = time.strftime('%Y-%m-%d')
        log_path = test_kb_path / "Logs" / f"{today}.md"
        self.assertTrue(log_path.exists())
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("# Logboek", content)
            self.assertIn("Prio Task", content)

    @patch('src.services.input_handler.GeminiClient')
    @patch('src.services.input_handler.GitHubClient')
    def test_input_handler_text(self, MockGithub, MockGemini):
        # Create Inbox
        (test_kb_path / "Inbox").mkdir()
        (test_kb_path / "Archive" / "Raw").mkdir(parents=True)

        handler = InboxHandler()
        mock_gemini = MockGemini.return_value
        mock_gemini.generate_content.return_value = '[{"title": "Task 1", "body": "Body 1", "labels": ["todo"]}]'

        # Create dummy text file
        test_file = test_kb_path / "Inbox" / "note.txt"
        with open(test_file, "w") as f:
            f.write("Do something")

        handler.handle_text(test_file)

        # Check if archived
        self.assertFalse(test_file.exists())
        self.assertTrue((test_kb_path / "Archive" / "Raw" / "note.txt").exists())

        # Check github call
        MockGithub.return_value.create_issue.assert_called()

    @patch('src.services.task_enricher.GeminiClient')
    @patch('src.services.task_enricher.GitHubClient')
    def test_enricher(self, MockGithub, MockGemini):
        enricher = TaskEnricher()
        mock_gh = MockGithub.return_value
        mock_gemini = MockGemini.return_value

        # Mock issue
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.body = "Body"
        mock_issue.labels = []

        # Create context
        path = test_kb_path / "Projects" / "Client" / "Project" / "01_Admin"
        path.mkdir(parents=True)
        with open(path / "context.yaml", "w") as f:
            f.write("project_name: Project")

        mock_gemini.generate_content.return_value = "Enriched content"

        enricher.enrich_issue(mock_issue)

        mock_gh.comment_on_issue.assert_called()
        mock_gh.add_label.assert_called_with(1, "enriched")

if __name__ == '__main__':
    unittest.main()
