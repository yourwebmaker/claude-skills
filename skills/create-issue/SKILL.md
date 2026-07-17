---
name: create-issue
description: Turns a feature idea or bug report described in plain language into a structured GitHub issue, published via the gh CLI. Use this whenever the user asks to create, file, open, or write up a GitHub issue for a bug, feature, task, or piece of work — even if they just describe the problem/idea without saying "issue" explicitly (e.g. "we should really add rate limiting to the login endpoint" or "there's a bug where seat numbers sort wrong"). The issue body follows a fixed structure so a separate downstream skill can later read it and pick up the work.
---

# Create Issue

## Why the structure matters

This skill's output is consumed by another skill later: something will read the
issue back and start working from it. That downstream skill can only act
reliably if every issue has the same shape in the same place — a fixed set of
headings, and acceptance criteria / tasks as GitHub checkbox lists (`- [ ]`),
not prose. Checkboxes matter specifically because the downstream skill can
tick them off directly in the issue body as it completes each one, giving a
visible progress trail on the issue itself. Don't improvise a different
structure even if it seems like it would read more naturally for a particular
issue — consistency across issues is what makes the second skill possible at
all.

The one deliberate exception is step 1 below: if the target repo already has
its own issue template, that template's conventions win. Respecting a repo's
existing process matters more than this skill's own default shape — but it
does mean the downstream skill (whenever it's built) needs to tolerate some
variation for repos that have a template, rather than assuming every issue
everywhere looks identical. Keep that in mind if you end up building it.

## Workflow

1. **Check for a repo issue template.** From the repo root
   (`git rev-parse --show-toplevel`), look for `.github/ISSUE_TEMPLATE/`
   (one or more `.md`/`.yml` files) or a single `.github/ISSUE_TEMPLATE.md`.
   If one exists, read it and fit the drafted content into *its* sections
   instead of the default structure in step 3 — map Background/User
   Story/Acceptance Criteria/Tasks content onto whatever headings the
   template actually defines, as faithfully as you can, rather than bolting
   the default structure on top of it. If no template exists, use the
   default structure as-is. Do this check every single time, regardless of
   what structure a previous issue in the same repo happened to use — a
   repo either has a template or it doesn't; that fact doesn't change
   between requests, so there's no situation where matching an earlier
   issue's structure is a reason to skip checking.

2. **Resolve ambiguity before drafting.** A one-line description like
   "Introduce Trip class" or "refactor the Airport class" can be read a
   dozen different ways — what should the API surface look like, does this
   touch the database schema, what's explicitly out of scope? Guessing wrong
   here is expensive: the user has to notice the issue is off, explain what
   they actually meant, and wait for a rewrite. Read the relevant code first
   (that resolves plenty of ambiguity on its own — e.g. seeing there's no
   existing `Trip`-like concept tells you this is greenfield, not a rename).
   For whatever real ambiguity is left that would change what gets built —
   scope, approach, acceptance criteria — ask the user before drafting.
   Don't manufacture questions for the sake of it: if the description is
   already specific and the codebase context resolves the rest, draft
   straight away.

   Narrowing *what* problem is being solved doesn't automatically resolve
   *how* it should be built — those are separate questions, and it's easy to
   stop asking the moment the first one feels settled. If the user says "this
   isn't really a new Trip class, it's just that origin can't equal
   destination," that's real progress, but it still leaves open whether that
   becomes a one-line check bolted onto the existing constructor or a new
   value object that encapsulates the origin/destination pair (which would
   also cut down the parameter list everywhere that pair gets passed around
   separately today — constructors, repository methods, etc.). When the
   codebase already shows a pattern of many-parameter constructors or
   repeated parameter pairs, that's a signal this fork is worth asking about
   explicitly, not assuming the smallest-looking change is what's wanted.

3. **Classify.** Decide whether the user is describing a bug (something is
   broken or behaves incorrectly) or a feature/task (new or changed
   functionality). This determines the label in step 5.

4. **Draft the issue body.** Expand the (now-clarified) description into
   this structure (or the repo's own template structure, per step 1):

   ```markdown
   ## Background
   <Why this matters / what prompted it. A sentence or two of context — pull
   in anything relevant the user mentioned, don't just restate the title.>

   ## User Story
   As a <role>, I want <goal>, so that <benefit>.

   ## Acceptance Criteria
   - [ ] <a specific, checkable condition that must be true when this is done>
   - [ ] <another one>

   ## Tasks
   - [ ] <a concrete implementation step>
   - [ ] <another one>
   ```

   Write a real user story, not a placeholder — infer the role from context
   (e.g. "As a traveler searching for flights...") if the user didn't state
   one explicitly. Acceptance criteria should be testable outcomes, not
   restatements of the tasks. Tasks should be concrete enough that someone
   (or the downstream skill) could start from them without re-deriving the
   approach.

   In Background especially, use real blank-line-separated paragraphs — one
   per distinct idea (e.g. current behavior, then why it matters, then the
   proposed direction) — rather than one dense block. A single `\n` inside a
   paragraph is invisible on GitHub: markdown collapses it, so text that
   looks nicely wrapped in your editor still renders as one unbroken wall of
   text on the actual issue page. Only a blank line produces a visible break.

   Also draft a concise, imperative-style title (e.g. "Add rate limiting to
   login endpoint", not "Rate limiting should be added").

5. **Write the body to a temp file.** Use `mktemp` for this rather than a
   fixed filename, and pass it via `--body-file` rather than `--body`, since
   multiline text reliably breaks shell quoting when passed inline. Create
   the file *inside the target repo's working directory* (e.g. `mktemp
   ./gh-issue-body.XXXXXX` from the repo root), not in a system temp
   directory or scratchpad path — in some environments the tool used to
   write file contents and the tool used to run `gh` don't share the same
   view of paths outside the repo, so a temp file created elsewhere can be
   invisible to the `gh` command that needs to read it.

6. **Publish it.** Run, from the current directory (`gh` infers the repo from
   the local git remote — don't pass `--repo` unless the user explicitly
   names a different one):

   ```bash
   gh issue create --title "<drafted title>" --body-file "<temp file path>" --label "<bug|enhancement>"
   ```

   Use `bug` for bug reports and `enhancement` for features/tasks — these are
   GitHub's actual default label names (not "feature", which doesn't exist by
   default). If the command fails because the label doesn't exist in this
   repo, retry once without `--label` rather than giving up on creating the
   issue entirely — the label is a nice-to-have, the issue itself is the
   point.

7. **Clean up.** Delete the temp file once the issue is created (or once
   creation fails for a reason other than the missing label, since there's
   nothing more to retry).

8. **Report back.** Give the user the issue URL `gh issue create` prints —
   don't just say "done."

## Example

**Input:** "Create an issue to add JWT authentication to the login endpoint."

Assuming the codebase and prior conversation already make the scope clear
(otherwise, ask first — see step 2):

**Output:** An issue titled "Add JWT authentication to login endpoint" with a
Background explaining the current auth approach (if known) or the general
motivation, a User Story ("As a user, I want my session secured with a JWT,
so that..."), Acceptance Criteria like "- [ ] Login endpoint returns a signed
JWT on success" / "- [ ] Protected endpoints reject requests without a valid
JWT", and Tasks like "- [ ] Add JWT library dependency" / "- [ ] Implement
token generation on login" / "- [ ] Add auth middleware to protected routes",
labeled `enhancement`.
