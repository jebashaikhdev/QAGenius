import os 
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL","claude-haiku-5-5")  # Default to "claude-haiku-5-5" if not set
REQUIREMENT_ANALYZER_SKILL_ID = os.getenv("REQUIREMENT_ANALYZER_SKILL_ID")
TEST_CASE_GENERATOR_SKILL_ID = os.getenv("TEST_CASE_GENERATOR_SKILL_ID")
TEST_CASE_REVIEWER_SKILL_ID = os.getenv("TEST_CASE_REVIEWER_SKILL_ID")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")