---
name: commit-message
description: >-
  Draft a commit message for staged or described changes, following the
  conventions already in the repo's git log. Use when asked for a commit
  message, commit msg, how to word or name a commit, or how to split work into
  multiple commits. Does not stage files or run git commit unless explicitly
  asked.
---

# Commit Message

Your job is to provide the user an appropriate commit message. Unless otherwise specified, you aren't here to stage the diffs and make the commit yourself. Your job is solely to write the commit message the user is asking for.

## Gather context

1. Read the change. Start with `git diff --cached`. If nothing is staged, fall back to `git diff`. If both are empty and the user didn't describe the change, ask which files or changes the message is for.
2. Learn the conventions. Run `git log -n 20` (not `--oneline`, so bodies and trailers are visible). Increase `20` if the history is mixed or sparse. Note the subject style (conventional commits, imperative plain English, ticket prefixes), whether bodies are used, and any trailers such as `Signed-off-by` or `Co-authored-by`.
3. Check for `.gitmessage`, `commitlint.config.*`, or a `CONTRIBUTING.md` section on commits. These override what you infer from the log.

Match what the repo does, even if you'd do it differently. Don't introduce conventional-commit prefixes into a repo that doesn't use them, and don't drop them from one that does.

## Write the message

- Subject in the imperative mood, around 50 characters, no trailing period.
- Body only when the diff needs explaining: why the change was made, what a reviewer couldn't infer from the code, anything surprising. Wrap at 72. Skip it for self-explanatory changes.
- One commit message per logical change. If the diff contains unrelated changes, say so and offer the multi-commit form below.

## Output

Return the message in a fenced code block, ready to paste:

```
feat: add retry to webhook delivery

Transient 5xx responses from downstream were dropping events. Retry up
to three times with backoff before dead-lettering.
```

Nothing else unless the user asked for reasoning.

## Multi-commit mode

If the user says "multiple" or "multi", or the diff clearly contains unrelated changes, provide the shell commands instead so the user can run them:

```
git add src/webhook.ts src/retry.ts
git commit -m "feat: add retry to webhook delivery"
git add README.md
git commit -m "docs: document webhook retry policy"
```

Grouping rules:

- One logical change per commit. Don't mix a refactor with a behavior change.
- Order commits so each one builds and makes sense on its own.
- Use `git add -p` in the commands only when a single file needs splitting, and say so.
