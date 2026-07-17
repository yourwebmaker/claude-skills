#!/usr/bin/env python3
"""Manually build benchmark.json from grading.json + timing.json, per schemas.md."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent
ITERATION = WORKSPACE / "iteration-1"

EVALS = [
    (1, "symfony-validator-refactor"),
    (2, "more-fixture-flights"),
    (3, "airport-class-refactor"),
    (4, "introduce-trip-class"),
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
by_config = {"with_skill": {"pass_rate": [], "time_seconds": [], "tokens": []},
             "without_skill": {"pass_rate": [], "time_seconds": [], "tokens": []}}

for eval_id, name in EVALS:
    for config in ["with_skill", "without_skill"]:
        run_dir = ITERATION / name / config
        grading = json.loads((run_dir / "grading.json").read_text())
        timing = json.loads((run_dir / "timing.json").read_text())
        summary = grading["summary"]

        run = {
            "eval_id": eval_id,
            "eval_name": name,
            "configuration": config,
            "run_number": 1,
            "result": {
                "pass_rate": summary["pass_rate"],
                "passed": summary["passed"],
                "failed": summary["failed"],
                "total": summary["total"],
                "time_seconds": timing["total_duration_seconds"],
                "tokens": timing["total_tokens"],
                "tool_calls": 0,
                "errors": 0,
            },
            "expectations": grading["expectations"],
            "notes": [],
        }
        runs.append(run)
        by_config[config]["pass_rate"].append(summary["pass_rate"])
        by_config[config]["time_seconds"].append(timing["total_duration_seconds"])
        by_config[config]["tokens"].append(timing["total_tokens"])

run_summary = {}
for config in ["with_skill", "without_skill"]:
    run_summary[config] = {
        "pass_rate": stats(by_config[config]["pass_rate"]),
        "time_seconds": stats(by_config[config]["time_seconds"]),
        "tokens": stats(by_config[config]["tokens"]),
    }

delta_pass = run_summary["with_skill"]["pass_rate"]["mean"] - run_summary["without_skill"]["pass_rate"]["mean"]
delta_time = run_summary["with_skill"]["time_seconds"]["mean"] - run_summary["without_skill"]["time_seconds"]["mean"]
delta_tokens = run_summary["with_skill"]["tokens"]["mean"] - run_summary["without_skill"]["tokens"]["mean"]

run_summary["delta"] = {
    "pass_rate": f"{delta_pass:+.2f}",
    "time_seconds": f"{delta_time:+.1f}",
    "tokens": f"{delta_tokens:+.0f}",
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
        "All 4 with_skill runs scored a clean 7/7 — the fixed Background/User Story/"
        "Acceptance Criteria/Tasks structure with checkboxes was followed consistently.",
        "All 4 without_skill (baseline) runs scored 1/7 — they only pass 'issue was "
        "actually created'; none used the fixed heading structure or checkbox lists, "
        "confirming the skill's structural contract isn't something Claude does by "
        "default without the skill.",
        "with_skill runs took longer on average, likely because grounding the issue in "
        "real code (reading FlightController.php, AirportCode.php, etc.) adds "
        "exploration time before drafting — this cost buys a issue that's actually "
        "specific to the codebase rather than generic.",
    ],
}

out_path = ITERATION / "benchmark.json"
out_path.write_text(json.dumps(benchmark, indent=2) + "\n")
print(f"Wrote {out_path}")
print(json.dumps(run_summary, indent=2))
