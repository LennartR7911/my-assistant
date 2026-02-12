from typing import List, Optional, Any
from github import Github, Auth
from github.Issue import Issue
from src.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self) -> None:
        auth = Auth.Token(settings.GITHUB_TOKEN)
        self.g = Github(auth=auth)
        self.repo = self.g.get_repo(settings.GITHUB_REPO)
        logger.info(f"Connected to GitHub Repo: {settings.GITHUB_REPO}")

    def get_issues(self, state: str = 'open', labels: Optional[List[str]] = None) -> Any:
        """
        Fetches issues with optional filtering.
        """
        try:
            if labels:
                return self.repo.get_issues(state=state, labels=labels)
            return self.repo.get_issues(state=state)
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            return []

    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[Issue]:
        try:
            issue = self.repo.create_issue(title=title, body=body, labels=labels or [])
            logger.info(f"Created issue #{issue.number}: {title}")
            return issue
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return None

    def comment_on_issue(self, issue_number: int, body: str) -> Any:
        try:
            issue = self.repo.get_issue(issue_number)
            comment = issue.create_comment(body)
            logger.info(f"Commented on issue #{issue_number}")
            return comment
        except Exception as e:
            logger.error(f"Error commenting on issue #{issue_number}: {e}")
            return None

    def add_label(self, issue_number: int, label_name: str) -> bool:
        try:
            issue = self.repo.get_issue(issue_number)
            issue.add_to_labels(label_name)
            logger.info(f"Added label '{label_name}' to issue #{issue_number}")
            return True
        except Exception as e:
            logger.error(f"Error adding label to issue #{issue_number}: {e}")
            return False

    def get_issue(self, issue_number: int) -> Optional[Issue]:
        try:
            return self.repo.get_issue(issue_number)
        except Exception as e:
            logger.error(f"Error fetching issue #{issue_number}: {e}")
            return None
