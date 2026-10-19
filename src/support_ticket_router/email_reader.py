
from email import policy
from email.parser import BytesParser
from pathlib import Path


def read_email(file_path: Path) -> dict:
    """Read an .eml file and extract its main fields."""

    with file_path.open("rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    body_part = message.get_body(preferencelist=("plain",))

    if body_part is not None:
        body = body_part.get_content()
    else:
        # Fallback for emails without a plain-text body part.
        content = message.get_content()
        body = content if isinstance(content, str) else ""

    return {
        "sender": str(message.get("From", "")),
        "subject": str(message.get("Subject", "")),
        "body": body,
    }
