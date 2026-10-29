# Support Ticket Router

Reads customer support emails (`.eml`), asks Claude to classify each one (category, urgency, summary, team),
and creates a Jira ticket. Emails the system is unsure about are **held for a person** instead of being guessed.

```
.eml ─► read_email ─► Claude + Instructor ─► schema & validators ─► code rules ─┬─► Jira ticket
                        (retries on errors)                                     └─► needs a person
                                                                                    (output/needs_human.json)
```

## Setup

```powershell
uv sync
copy .env.example .env      # then fill in ANTHROPIC_API_KEY and the JIRA_* values
```

`.env` holds secrets and is in `.gitignore`. Never commit it.

## Run

```powershell
uv run support-ticket-router --dry-run                                    # all emails, no Jira tickets
uv run support-ticket-router --dry-run emails/ticket_005_slow_application.eml
uv run support-ticket-router                                              # real run: creates Jira tickets
```

At the end of every run there is a **RUN SUMMARY** with three groups: tickets created, needs a person, and
failed. Held emails are saved to `output/needs_human.json` with the reason and the model's suggestion.
The exit code is 1 if any email needs a person or failed.

## What decides the result

| Layer | Where | What it does |
|---|---|---|
| Schema | `models.py` | Allowed values only; a definition for each label; summary 15–240 chars; `route_to` must match `category`; low confidence must set `needs_human` |
| Retries | `main.py` `classify_email` | Instructor sends validation errors back to Claude, up to 2 retries; after that the email is held, never dropped |
| Prompt | `main.py` `SYSTEM_PROMPT` | Rules, label definitions, 4 hard-case examples; all customer text inside `<email>` tags and escaped |
| Code rules | `main.py` `review_reasons` | Hold if the model asks, if the email contains instruction-like text, or if `critical` lacks outage evidence; empty emails skip the model |
| Jira | `jira.py` | Urgency → priority; labels for category and `route-<team>` |

## Evaluation

```powershell
uv run python eval/run_eval.py                          # accuracy per field on 21 labelled emails
uv run python eval/run_eval.py --split tune --repeat 5  # does the same email get the same answer?
```

Results and notes: [`eval/EVAL.md`](eval/EVAL.md). Presentation: [`docs/presentation.html`](docs/presentation.html).
