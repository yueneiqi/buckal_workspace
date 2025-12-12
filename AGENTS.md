<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Git Commit Message Conventions (AngularJS)

When you create commits in this repo, follow the AngularJS Git commit message conventions:

- **Format:** `<type>(<scope>): <subject>`
  - `<scope>` is optional; use it to name the area touched (e.g., `parser`, `cli`, `docs`).
  - `<type>` must be one of:
    - `feat` — new feature
    - `fix` — bug fix
    - `docs` — documentation-only changes
    - `style` — formatting, missing semi‑colons, etc.; no code change
    - `refactor` — code change that neither fixes a bug nor adds a feature
    - `perf` — performance improvement
    - `test` — adding or correcting tests
    - `chore` — build tooling, dependencies, misc. housekeeping
    - `revert` — revert a previous commit

- **Subject line rules:**
  - Use imperative, present tense (“add”, “fix”, “update”, not “added/adding”).
  - Do not capitalize the first letter.
  - No trailing period.
  - Keep it ≤ 50 characters.

- **Body (optional):**
  - Separate from subject with a blank line.
  - Wrap lines at ~72 characters.
  - Explain *what* changed and *why* (not just how).

- **Footer (optional):**
  - Reference issues/PRs (e.g., `Closes #123`, `Refs #456`).
  - For breaking changes, start with `BREAKING CHANGE:` followed by a clear description and any migration notes.

**Examples**

- `feat(cli): add --dry-run option`
- `fix(parser): handle empty input`
- `docs: clarify local test workflow`
