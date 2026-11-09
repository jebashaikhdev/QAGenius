import httpx

from app.config import (
    JIRA_BASE_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT_KEY
)

async def get_jira_projects():
    if not all([
        JIRA_BASE_URL,
            JIRA_EMAIL,
            JIRA_API_TOKEN,
            JIRA_PROJECT_KEY
    ]):
        raise ValueError("Jira configuration is incomplete")

    url = f"{JIRA_BASE_URL}/rest/api/3/project/{JIRA_PROJECT_KEY}"
    
    async with httpx.AsyncClient(
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        timeout=20.0,
    ) as client:
        response = await client.get(
            url,
            headers={ "Accept": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
    

async def create_jira_issue(summary: str, description: str):
    if not all([
        JIRA_BASE_URL,
        JIRA_EMAIL,
        JIRA_API_TOKEN,
        JIRA_PROJECT_KEY
    ]):
        raise ValueError("Jira configuration is incomplete")

    url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue"

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": "Task"}
        }
    }

    async with httpx.AsyncClient(
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        timeout=20.0
    ) as client:
        response = await client.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

        response.raise_for_status()
        return response.json()
