## Summary

Add a `CONTRIBUTING.md` guide to the repo root that explains how to add a new skill to this collection — the expected file layout, the required `SKILL.md` frontmatter, and how a skill gets tested here before it's considered done.

## Motivation

This repo currently has no contributor-facing documentation at all — just a one-line `README.md` describing it as a sandbox for testing the `create-issue` skill. There's no `skills/` directory yet and nothing written down about what a valid skill looks like or where it should live.

As more skills get added here, anyone (including future-us) trying to contribute a new one has to reverse-engineer the conventions from scratch or ask around. A `CONTRIBUTING.md` fixes that by writing the process down once, so it's consistent from the very first skill onward rather than something that gets retrofitted later.

## Proposed Solution

Add a `CONTRIBUTING.md` at the repo root covering:

- Where a new skill's files live (e.g. `skills/<skill-name>/SKILL.md`, plus any supporting scripts/resources)
- The required `SKILL.md` frontmatter (`name`, `description`, and any other supported fields) and what makes a good trigger `description`
- Naming conventions for the skill directory and the `name` field
- How to test a skill locally before opening a PR
- What reviewers will check for (e.g. clear triggering conditions, no overlap with existing skills)
- How to submit the change (branch/PR expectations, if any)

## Checklist
- [ ] Write `CONTRIBUTING.md` at the repo root
- [ ] Document the required `SKILL.md` structure and frontmatter fields
- [ ] Document directory/naming conventions for new skills
- [ ] Document how to test a skill before submitting it
- [ ] Link `CONTRIBUTING.md` from `README.md`
