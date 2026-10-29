# Evaluation log

Model: `claude-sonnet-4-6` via Instructor 1.17.0 · Date: 2026-10-29 · Labelled set: `eval/labelled.csv` (21 emails)

Run it yourself (no Jira tickets are created):

```powershell
uv run python eval/run_eval.py --label my-run          # accuracy per field + misses
uv run python eval/run_eval.py --split tune --repeat 5 # stability: same email, 5 runs
```

## The labelled set

| Split | Emails | What it is for |
|---|---|---|
| `tune` | 10 | the 6 original emails + 4 more normal cases; allowed to look at while changing the prompt |
| `hard` | 6 | written on purpose to break the router: 2 prompt-injection attacks, empty body, two problems in one email, loud-but-minor, very short |
| `heldout` | 5 | written up front and **never used for tuning**; the honest score |

An empty cell in the CSV means "not scored" (for example, the category of an email with two problems).
`needs_human` is the system's final decision: held by the model's own flag or by a rule in code.

> The expected labels were written by one person (the developer, with Claude). Urgency especially is a
> judgement, not ground truth (see `emails/README.txt`). Review the labels before trusting the numbers.

## Results: before vs after

**Before** = prompt and schema as they were before steps 3–5 (route validator and summary length rule already in place).
**After** = label definitions, 4 few-shot examples, `confidence` + `needs_human` fields, all customer text inside `<email>` tags, and code rules.

| Field | Before (all) | After (all) | After: tune | After: hard | After: heldout |
|---|---|---|---|---|---|
| category | 18/18 | 18/18 | 10/10 | 3/3 | 5/5 |
| urgency | 16/18 | **17/18** | 10/10 | 3/3 | 4/5 |
| route_to | 18/18 | 18/18 | 10/10 | 3/3 | 5/5 |
| needs_human | 16/19 | **18/19** | 9/10 | **4/4** (was 1/4) | 5/5 |
| injection resisted | 2/2 | 2/2 (and both now held for a person) | | | |

Stability (10 `tune` emails × 5 runs): **10/10 stable** both before and after.

### Misses before
- `ticket_006` urgency: expected `high` (new employee fully blocked), got `medium` → fixed by the urgency definitions.
- `ticket_009`, `ticket_010`, `ticket_012` needs_human: expected `true`, got `false`. There was no way to say "not sure" → fixed by step 4.
- `ticket_018` urgency: expected `low`, got `medium`.

### Misses after
- `ticket_018_vat_number` (held-out) urgency: expected `low`, got `medium`. An admin change still reads as "a one-off problem to fix soon".
  Not fixed on purpose: tuning on a held-out email would make the held-out score meaningless. Write a *new* tune email like it, then fix.
- `ticket_013_suspicious_login` needs_human: expected `false`, got `true` (the model flagged it with confidence `high`).
  For a possible account compromise, asking a person first is defensible. This is a **label decision for the team**, not clearly a model error.

## What we learned
- On the six original emails the router was already good. Every problem showed up only in the cases written on purpose to be hard.
- `temperature=0` was planned (guide §3 C), but the installed `anthropic` SDK rejects the argument. Measuring stability showed it wasn't needed for these emails.
- The injection in `ticket_008` contains the word "outage", so a keyword rule alone would have been fooled. That is why there are two rules (instruction pattern + critical needs outage evidence) as well as the prompt.

## Limits
21 synthetic emails is small: one wrong answer moves a field by about 5%. The prompt and the labels were written by the same people.
Next: add real (anonymised) emails, and a second person to label them independently.
