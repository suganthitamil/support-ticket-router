
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# Each label gets one line that says exactly when it applies (guide section 3).
# The lines are joined with newlines so the model reads them as a list, not one run-on string.
CATEGORY_DEFINITIONS = "\n".join([
    "Choose exactly one category:",
    "account_access - one person or a few people cannot log in or reach their account or workspace: "
    "passwords, MFA, invitations, permissions, suspicious logins.",
    "incident - something is broken or unavailable (errors, outages, failures), usually for many users. "
    "If it works but slowly, use performance instead.",
    "billing - invoices, charges, refunds, payments, subscriptions, tax details.",
    "feature_request - asks for something new or different; nothing is broken.",
    "performance - the product still works but is slower than normal (long load times, timeouts on one area).",
    "other - none of the above, including cosmetic problems such as typos.",
])

URGENCY_DEFINITIONS = "\n".join([
    "Judge urgency from the facts in the email, not from capital letters or words like URGENT:",
    "critical - service is down or failing for many users, or money, data or security is being lost right now.",
    "high - a person or team cannot do their work and has no workaround, or there is a deadline today.",
    "medium - something is wrong or degraded but people can still work, or a one-off problem to fix soon.",
    "low - a question, an idea, an admin change or a cosmetic issue, with no deadline.",
])

ROUTE_DEFINITIONS = "\n".join([
    "The team that should handle it. It must match the category:",
    "account_access -> support, incident -> engineering, billing -> billing,",
    "feature_request -> product, performance -> engineering, other -> support.",
])

EXPECTED_ROUTES = {
    "account_access": "support",
    "incident": "engineering",
    "billing": "billing",
    "feature_request": "product",
    "performance": "engineering",
    "other": "support",
}


class EmailClassification(BaseModel):
    category: Literal[
        "account_access",
        "incident",
        "billing",
        "feature_request",
        "performance",
        "other",
    ] = Field(description=CATEGORY_DEFINITIONS)

    urgency: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = Field(description=URGENCY_DEFINITIONS)

    summary: str = Field(
        min_length=15,
        max_length=240,
        description="One sentence: what the customer wants and what is broken. "
        "Use only facts stated in the email.",
    )

    route_to: Literal[
        "support",
        "engineering",
        "billing",
        "product",
    ] = Field(description=ROUTE_DEFINITIONS)

    # A way out, so the model is not forced to guess (guide section 4).
    confidence: Literal["high", "medium", "low"] = Field(
        description="How sure you are about category and urgency. "
        "low if the email is empty, too short to understand, or mixes several unrelated problems."
    )

    needs_human: bool = Field(
        description="true if a person should read this email before a ticket is created: "
        "no readable content, several unrelated problems in one email, or you cannot tell what is wanted."
    )

    @model_validator(mode="after")
    def validate_route(self):
        expected_route = EXPECTED_ROUTES[self.category]

        if self.route_to != expected_route:
            raise ValueError(
                f"Invalid route_to '{self.route_to}' for category '{self.category}'. "
                f"Expected route_to: '{expected_route}'."
            )

        return self

    @model_validator(mode="after")
    def low_confidence_needs_human(self):
        if self.confidence == "low" and not self.needs_human:
            raise ValueError("confidence is 'low', so needs_human must be true.")

        return self
