
from typing import Literal

from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    category: Literal[
        "account_access",
        "incident",
        "billing",
        "feature_request",
        "performance",
        "other",
    ]

    urgency: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]

    summary: str = Field(
        description="A concise summary of the customer's issue"
    )

    route_to: Literal[
        "support",
        "engineering",
        "billing",
        "product",
    ]
