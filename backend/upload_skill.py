from pathlib import Path
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY
from anthropic.lib import files_from_dir

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SKILL_PATH = Path(__file__).resolve().parent.parent / "skills" / "requirement-analyzer"


new_version = client.skills.versions.create(
    skill_id="skill_01ThVaPpqpDe7LGtNTBKiQXP",
    files=files_from_dir(SKILL_PATH)
)

print("Updated Skill version:", new_version.id)


# skill_names = [
#     "requirement-analyzer",
#     "test-case-generator",
#     "test-case-reviewer"
# ]

# print(f"SKILLS_DIR: {SKILLS_DIR}")

# for name in skill_names:
#     skill_path = SKILLS_DIR / name
    
#     skill = client.skills.create(
#         files=files_from_dir(skill_path)
#     )
    
#     print(f"Uploaded skill '{name}' with ID: {skill.id}")