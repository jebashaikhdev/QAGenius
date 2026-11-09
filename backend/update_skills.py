
from anthropic import Anthropic
from anthropic.lib import files_from_dir
from pathlib import Path

from app.config import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

BASE_DIR = Path(__file__).resolve().parent.parent

skills = {
    "requirement-analyzer": {
        "id": "skill_01ThVaPpqpDe7LGtNTBKiQXP",
        "path": BASE_DIR / "skills/requirement-analyzer"
    },
    "test-case-generator": {
        "id": "skill_01KQh2sMpsN2q9tRzWMDpF2k",
        "path": BASE_DIR / "skills/test-case-generator"
    },
    "test-case-reviewer": {
        "id": "skill_01HZFBbwNjjPUkGqxAhKNsqY",
        "path": BASE_DIR / "skills/test-case-reviewer"
    }
}

for name, details in skills.items():

    skill_path = Path(details["path"])

    version = client.skills.versions.create(
        skill_id=details["id"],
        files=files_from_dir(str(skill_path))
    )

    print(f"{name}: uploaded successfully")
    print(f"New version ID: {version.id}")
    
for name, details in skills.items():
    skill = client.skills.retrieve(
        skill_id=details["id"]
    )
    print(name, skill.latest_version_id)
