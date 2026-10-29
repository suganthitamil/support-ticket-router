import httpx

from support_ticket_router.config import settings
from support_ticket_router.models import EmailClassification

JIRA_PRIORITY = {"low": "Low", "medium": "Medium", "high": "High", "critical": "Highest"}

def create_jira_issue(result: EmailClassification) -> str:
    payload = {
        "fields": {
            "project": {"key": settings.JIRA_PROJECT_KEY},
            "issuetype": {"name": "Task"},
            "summary": result.summary[:250],  # Jira caps summaries at 255 chars
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": result.summary}],
                }],
            },
            "priority": {"name": JIRA_PRIORITY.get(result.urgency, "Medium")},
            # route_to becomes a label so the team routing actually reaches Jira.
            "labels": [result.category, f"route-{result.route_to}"],
        }
    }
    response = httpx.post(
        f"{settings.JIRA_BASE_URL}/rest/api/3/issue",
        json=payload,
        auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN.get_secret_value()),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["key"]