# claude-skills

Custom [Claude Code](https://claude.com/claude-code) skills, developed and tested here.

## Layout

- `skills/` — skill source (`SKILL.md` + bundled resources)
- `tests/` — eval workspace per skill: test prompts, grading scripts, and
  per-iteration outputs/benchmarks from running each skill with and without
  itself against real prompts
- `packages/` — packaged `.skill` archives, ready to install elsewhere

## Skills

### `create-issue`

Turns a plain-language feature idea or bug report into a structured GitHub
issue via the `gh` CLI — fixed Background/User Story/Acceptance
Criteria/Tasks sections (or the target repo's own issue template, if it has
one), asks clarifying questions when scope is genuinely ambiguous, and is
meant to be read later by a separate downstream skill that picks up the work.

This repo's own `.github/ISSUE_TEMPLATE/feature_request.md` was added
specifically to test that template-detection behavior.