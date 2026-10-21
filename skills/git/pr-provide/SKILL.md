---
name: pr-provide
description: >-
  Draft a pull request title and markdown body that follow the repo's PR
  template and the conventions of past PRs. Use when asked for a PR title, PR
  description, PR body, or help wording a pull request. Does not open the PR;
  the user creates it themselves.
---

# PR Provide

Your job is to provide the user an appropriately named PR title and body. You aren't here to create the PR on behalf of the user, because the user wants to make the PR themselves.

## Gather context

1. Read the full change, not just the last commit. Diff against the base branch: `git diff main...HEAD` (substitute the real base). Also run `git log main..HEAD` to see how the author described the work in commits.
2. Look for a PR template, in this order:
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.github/PULL_REQUEST_TEMPLATE/` (pick the one that fits, and tell the user which)
   - `PULL_REQUEST_TEMPLATE.md` or `docs/PULL_REQUEST_TEMPLATE.md`
3. If there is no template, check how past PRs were written: `gh pr list --state merged --limit 10`, then `gh pr view <n>` on two or three. Match their title style and body structure. Follow the existing standard rather than inventing a new one.
4. Look for a ticket reference in the branch name or commits (`#123`, `PROJ-456`). Include it in the body using the repo's linking convention, such as `Closes #123`.

## Title

Follow the convention of previous PRs unless the user says otherwise. Keep it under about 70 characters, specific to the change, imperative mood. If the repo uses prefixes or ticket keys in titles, use them.

## Body

If a template exists, fill it. Leave out sections that don't apply rather than writing "N/A", unless the template or past PRs clearly expect every heading present.

If there is no template, use this shape and drop any part that's empty:

- One or two sentences on what the PR does and why.
- What changed, as short bullets grouped by area.
- How to test or verify.
- Anything the reviewer should look at first, or known gaps.
- Ticket link, if any.

Keep it concise. Short sentences, straight to the point. Describe the change at a level a reviewer needs to orient, not every line of the diff. Don't restate code the reviewer can read, don't add marketing adjectives, and don't explain things the title already says.

## Output

Title on its own line, then the body in a fenced markdown block so it pastes cleanly into GitHub:

Title: `feat: add retry to webhook delivery`

```markdown
## Summary
Downstream 5xx responses were dropping webhook events. This adds bounded retry with backoff before dead-lettering.

## Changes
- `WebhookSender` retries up to 3 times with exponential backoff
- Failed deliveries after retries go to the `webhook_dlq` table

## Testing
- Unit tests for retry and dead-letter paths
- Verified against staging with a forced 503 from the mock receiver

Closes #412
```
