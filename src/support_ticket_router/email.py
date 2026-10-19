import os
from pathlib import Path
from email import policy
from email.parser import BytesParser



def read_email(file_path: Path) -> dict:
    """Read an .eml file and extract its sender, subject, and body."""

    with open(file_path, "rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    body = message.get_body(preferencelist=("plain",))

    return {
        "sender": str(message.get("From", "")),
        "subject": str(message.get("Subject", "")),
        "body": body.get_content() if body else "",
    }


