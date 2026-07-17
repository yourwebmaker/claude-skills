#!/usr/bin/env python3
"""Build benchmark.json for iteration-2 (with_skill only — no baseline re-run needed,
iteration-1 already established the with/without differentiation)."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent
ITERATION = WORKSPACE / "iteration-2"

EVALS = [
    (1, "symfony-validator-refactor"),
    (2, "more-fixture-flights"),
    (3, "airport-class-refactor"),
    (4, "introduce-trip-class"),
    (5, "introduce-trip-class-live-interview"),
    (6, "template-detection"),
]


def stats(values):
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0
    return {"mean": round(mean, 4), "stddev": round(stddev, 4), "min": round(min(values), 4), "max": round(max(values), 4)}


runs = []
pass_rates, times, tokens = [], [], []

for eval_id, name in EVALS:
    run_dir = ITERATION / name / "with_skill"
    grading = json.loads((run_dir / "grading.json").read_text())
    summary = grading["summary"]

    timing_path = run_dir / "timing.json"
    is_live = not timing_path.exists()
    timing = json.loads(timing_path.read_text()) if not is_live else None

    run = {
        "eval_id": eval_id,
        "eval_name": name,
        "configuration": "with_skill",
        "run_number": 1,
        "result": {
            "pass_rate": summary["pass_rate"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "total": summary["total"],
            "time_seconds": timing["total_duration_seconds"] if timing else 0,
            "tokens": timing["total_tokens"] if timing else 0,
            "tool_calls": 0,
            "errors": 0,
        },
        "expectations": grading["expectations"],
        "notes": ["Run live in conversation (not a background subagent) — no comparable timing/token data."]
        if is_live
        else [],
    }
    runs.append(run)
    pass_rates.append(summary["pass_rate"])
    if timing:
        times.append(timing["total_duration_seconds"])
        tokens.append(timing["total_tokens"])

run_summary = {
    "with_skill": {
        "pass_rate": stats(pass_rates),
        "time_seconds": stats(times),
        "tokens": stats(tokens),
    }
}

benchmark = {
    "metadata": {
        "skill_name": "create-issue",
        "skill_path": "/Users/yourwebmaker/.claude/skills/create-issue",
        "executor_model": "claude-sonnet-5",
        "analyzer_model": "claude-sonnet-5",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evals_run": [name for _, name in EVALS],
        "runs_per_configuration": 1,
    },
    "runs": runs,
    "run_summary": run_summary,
    "notes": [
        "Iteration 2 targets three fixes from iteration-1 feedback: (1) Background "
        "paragraphs now use real blank-line breaks instead of one dense block, "
        "(2) issue-template detection, (3) a clarification step for genuinely "
        "ambiguous requests.",
        "symfony-validator-refactor, airport-class-refactor, and introduce-trip-class "
        "scored 7/7 — confirming the paragraph-break fix held on re-run.",
        "more-fixture-flights scored only 2/7 against the DEFAULT-structure "
        "expectations, but that's a false negative: it correctly detected the "
        "sandbox repo's custom issue template and used Summary/Motivation/"
        "Proposed Solution/Checklist instead, which the grading script (written "
        "for the default structure) doesn't recognize as valid. Manually "
        "confirmed it has real paragraph breaks and checkboxes under the "
        "template's own headings.",
        "template-detection (a dedicated new eval) scored 5/5 against "
        "template-aware expectations — clean adaptation to the repo's actual "
        "template.",
        "introduce-trip-class-live-interview is the one eval that was NOT run as "
        "a background subagent — Claude ran the skill directly in conversation "
        "and asked the real user two rounds of clarifying questions before "
        "drafting, since 'Introduce Trip class' was genuinely ambiguous. The "
        "user's answers substantially changed the scope (from a new Trip entity "
        "to an origin != destination validation rule on the existing Flight "
        "entity) — confirming the clarification step catches real scope drift "
        "that a silent-assumption approach would have missed.",
        "Finding during this round: 3 of the 5 background subagents noticed the "
        "sandbox repo's template but explicitly chose to keep the default "
        "structure anyway, reasoning it should stay 'consistent with the prior "
        "iteration-1 run' — an exception the skill never actually states. This "
        "was mostly an artifact of the test prompt's re-run framing, but the "
        "skill's step 1 was tightened to explicitly close that loophole.",
    ],
}

out_path = ITERATION / "benchmark.json"
out_path.write_text(json.dumps(benchmark, indent=2) + "\n")
print(f"Wrote {out_path}")
print(json.dumps(run_summary, indent=2))
