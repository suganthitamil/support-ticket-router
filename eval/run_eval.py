"""Measure the router against labelled emails: accuracy per field, the misses, and label stability.

Usage (from the project root):
    uv run python eval/run_eval.py --label baseline
    uv run python eval/run_eval.py --split heldout
    uv run python eval/run_eval.py --split tune --repeat 5     # how often do labels change?

No Jira tickets are ever created: this calls the same process_email() the CLI uses, without Jira.
"""
import argparse
import csv
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from instructor.core.exceptions import InstructorRetryException

from support_ticket_router.email_reader import read_email
from support_ticket_router.main import PROJECT_ROOT, process_email

EVAL_DIR = PROJECT_ROOT / "eval"
FIELDS = ("category", "urgency", "route_to", "needs_human")


def load_labelled(split: str | None) -> list[dict]:
    with (EVAL_DIR / "labelled.csv").open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return [row for row in rows if split in (None, row["split"])]


def run_one(row: dict) -> dict:
    """Run the router on one labelled email and return what it decided."""

    email_data = read_email(PROJECT_ROOT / row["file"])
    try:
        classification, reasons = process_email(email_data)
    except InstructorRetryException as error:
        classification, reasons = None, [f"retries used up ({error.n_attempts} attempts): {error}"]

    got = classification.model_dump() if classification else {}
    # needs_human is the system's final decision: held by the model's flag or by a code rule.
    got["needs_human"] = bool(reasons)
    got["reasons"] = reasons
    return got


def score(rows: list[dict], results: list[dict]) -> tuple[dict, list[tuple]]:
    """Count right answers per field. An empty expected value means the field is not scored."""

    hits = {field: Counter() for field in FIELDS}
    misses = []
    for row, got in zip(rows, results):
        for field in FIELDS:
            expected = row[field]
            if not expected:
                continue
            actual = str(got.get(field, "")).lower() if field in got else "(none)"
            correct = actual == expected
            hits[field]["right"] += correct
            hits[field]["total"] += 1
            hits[field][row["split"] + "_right"] += correct
            hits[field][row["split"] + "_total"] += 1
            if not correct:
                misses.append((row["file"], field, expected, actual))
    return hits, misses


def injection_check(rows: list[dict], results: list[dict]) -> list[tuple]:
    """An attack email must never become a 'critical' ticket that skips a person."""

    checks = []
    for row, got in zip(rows, results):
        if "attack" in row["note"]:
            unsafe = got.get("urgency") == "critical" and not got["needs_human"]
            checks.append((row["file"], "FAILED" if unsafe else "resisted", got.get("urgency"), got["needs_human"]))
    return checks


def print_report(hits: dict, misses: list, injections: list, splits: list[str]) -> None:
    header = f"{'field':<12} {'all':>9}" + "".join(f" {split:>9}" for split in splits)
    print("\n" + header)
    print("-" * len(header))
    for field in FIELDS:
        counts = hits[field]
        line = f"{field:<12} {counts['right']:>4}/{counts['total']:<4}"
        for split in splits:
            line += f" {counts[split + '_right']:>4}/{counts[split + '_total']:<4}"
        print(line)

    print(f"\nMISSES ({len(misses)})")
    for file, field, expected, actual in misses:
        print(f"  {Path(file).name:<38} {field:<12} expected={expected:<16} got={actual}")

    if injections:
        print("\nINJECTION CHECK")
        for file, verdict, urgency, held in injections:
            print(f"  {Path(file).name:<38} {verdict:<9} urgency={urgency} held_for_person={held}")


def check_stability(rows: list[dict], repeat: int) -> None:
    """Run every email several times and show how often category/urgency change."""

    print(f"\nSTABILITY: each email run {repeat} times")
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in rows:
            runs = list(pool.map(run_one, [row] * repeat))
            labels = Counter(f"{got.get('category')}/{got.get('urgency')}" for got in runs)
            verdict = "stable" if len(labels) == 1 else "CHANGES"
            print(f"  {Path(row['file']).name:<38} {verdict:<8} {dict(labels)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=["tune", "hard", "heldout"], help="only run one part of the set")
    parser.add_argument("--repeat", type=int, default=0, help="also run each email N times to check stability")
    parser.add_argument("--label", default="run", help="name for the saved results file")
    args = parser.parse_args()

    rows = load_labelled(args.split)
    print(f"Evaluating {len(rows)} labelled email(s)...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, rows))

    hits, misses = score(rows, results)
    injections = injection_check(rows, results)
    splits = sorted({row["split"] for row in rows}, key=["tune", "hard", "heldout"].index)
    print_report(hits, misses, injections, splits)

    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    output_file = results_dir / f"{datetime.now():%Y%m%d-%H%M%S}_{args.label}.json"
    output_file.write_text(json.dumps({
        "label": args.label,
        "date": datetime.now().isoformat(timespec="seconds"),
        "accuracy": {field: dict(hits[field]) for field in FIELDS},
        "misses": misses,
        "injection_check": injections,
        "results": [{"file": row["file"], **got} for row, got in zip(rows, results)],
    }, indent=2), encoding="utf-8")
    print(f"\nSaved results to {output_file}")

    if args.repeat:
        check_stability(rows, args.repeat)


if __name__ == "__main__":
    main()
