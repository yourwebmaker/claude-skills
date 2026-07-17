#!/usr/bin/env python3
"""Grade a single create-issue eval run against the fixed expectations."""

import json
import re
import subprocess
import sys
from pathlib import Path


def read(path):
    p = Path(path)
    return p.read_text() if p.exists() else None


def section(body, heading):
    """Return the text of a '## Heading' section up to the next '## ' or EOF."""
    if body is None:
        return None
    pattern = rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)"
    m = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None


def has_checkboxes(text, min_count=1):
    if text is None:
        return False
    return len(re.findall(r"^\s*-\s*\[ \]", text, re.MULTILINE)) >= min_count


def grade(run_dir):
    run_dir = Path(run_dir)
    outputs = run_dir / "outputs"
    body = read(outputs / "issue_body.md")
    title = read(outputs / "title.txt")
    url = read(outputs / "issue_url.txt")
    url = url.strip() if url else None

    expectations = []

    def add(text, passed, evidence):
        expectations.append({"text": text, "passed": passed, "evidence": evidence})

    bg = section(body, "Background")
    add(
        "Body contains a '## Background' heading",
        bg is not None,
        f"Found section: {bg[:120]!r}" if bg else "No '## Background' heading found",
    )

    us = section(body, "User Story")
    add(
        "Body contains a '## User Story' heading",
        us is not None,
        f"Found section: {us[:120]!r}" if us else "No '## User Story' heading found",
    )

    ac = section(body, "Acceptance Criteria")
    ac_ok = ac is not None and has_checkboxes(ac)
    add(
        "Body contains a '## Acceptance Criteria' heading with checkbox ('- [ ]') items",
        ac_ok,
        f"Found {len(re.findall(chr(10)+'-', ac or ''))} lines, checkboxes={has_checkboxes(ac)}"
        if ac
        else "No '## Acceptance Criteria' heading found",
    )

    tasks = section(body, "Tasks")
    tasks_ok = tasks is not None and has_checkboxes(tasks)
    add(
        "Body contains a '## Tasks' heading with checkbox ('- [ ]') items",
        tasks_ok,
        f"checkboxes={has_checkboxes(tasks)}" if tasks else "No '## Tasks' heading found",
    )

    us_shape = bool(
        us
        and re.search(
            r"as (?:an?\s+.+?|someone.*?),\s*i want\s+.+?,\s*so that\s+.+", us, re.IGNORECASE | re.DOTALL
        )
    )
    add(
        "User Story follows 'As a ..., I want ..., so that ...' shape",
        us_shape,
        (us[:150] if us else "No User Story section to check"),
    )

    url_ok = bool(url and re.match(r"^https://github\.com/[^/]+/[^/]+/issues/\d+$", url))
    add(
        "Issue was actually created (issue_url.txt has a valid github.com issues URL)",
        url_ok,
        url or "issue_url.txt missing or empty",
    )

    label_ok = False
    label_evidence = "Could not check (no valid issue URL)"
    if url_ok:
        try:
            result = subprocess.run(
                ["gh", "issue", "view", url, "--json", "labels"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                labels = [l["name"] for l in json.loads(result.stdout)["labels"]]
                label_ok = "enhancement" in labels
                label_evidence = f"Labels found: {labels}"
            else:
                label_evidence = f"gh issue view failed: {result.stderr.strip()}"
        except Exception as e:
            label_evidence = f"Error checking label: {e}"
    add("Issue has the 'enhancement' label applied", label_ok, label_evidence)

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)

    grading = {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 3) if total else 0.0,
        },
    }

    out_path = run_dir / "grading.json"
    out_path.write_text(json.dumps(grading, indent=2) + "\n")
    print(f"{run_dir}: {passed}/{total} passed")
    return grading


if __name__ == "__main__":
    grade(sys.argv[1])
