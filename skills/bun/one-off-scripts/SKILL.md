---
name: one-off-scripts
description: >-
  Build, review, or adapt one-time Bun/TypeScript scripts for project
  maintenance tasks such as reports, CSV exports, data backfills, reconciliation,
  API audits, account/user fixes, and safe production or staging operations. Use
  when Codex needs to create a standalone script under a project's scripts
  directory, reuse existing local patterns, handle env guards, Prisma or
  database access, API calls, batching, bounded concurrency, pagination, bulk
  writes, retries, dry-runs, CSV output, or mutation safety checks.
---

# Bun One-Off Scripts

## Overview

Use this skill to produce small, repo-native Bun scripts that solve an immediate
operational task without turning into a hidden subsystem. The script should feel
like it belongs beside the project's existing one-off scripts.

## Workflow

1. Inspect the local script directory first. Search for nearby scripts that use
   the same dependencies, database client, env files, API clients, CSV helpers,
   logging style, and validation commands.
2. Classify the task before writing code:
   - Report or audit: read-only, summarize clearly, default to CSV/output files
     when the result is larger than a console summary.
   - Backfill or reconciliation: batch, checkpoint where possible, log progress,
     and keep idempotency visible.
   - Mutation or live operation: prefer a dry-run/report mode first, require
     explicit env guards, and preserve or add user confirmation for destructive
     actions.
3. Reuse existing project helpers before inventing new plumbing. Look for shared
   API clients, retry helpers, schema validators, CSV utilities, and Prisma or
   database setup conventions.
4. For large jobs, use performance patterns deliberately: bounded concurrency,
   in-memory indexes, paginated fetch loops, chunked writes, idempotent inserts,
   and retry/backoff. Keep small scripts simple.
5. Keep the script standalone. Avoid adding services, background workers, new
   app routes, or broad abstractions unless the user explicitly asks for a
   durable feature.
6. Validate with Bun-compatible commands. Do not switch to another runtime for
   formatting or checks when the script is meant to run with Bun.

For concrete script structure, read
`references/one-off-script-patterns.md` before drafting or editing a nontrivial
script.

## Safety Rules

- Ask before running the script against real credentials, production env files,
  or live external APIs unless the user has explicitly requested that run.
- Ask before installing packages, starting servers, or running build scripts.
- Never silently point a script at production. Make the environment source
  visible in the run comment, env guard, console summary, or CLI flags.
- For scripts that mutate data or call write/delete API endpoints, include at
  least one of: dry-run mode, interactive confirmation, explicit target filters,
  small batch limits, or a preflight count.
- Make skipped records and partial failures visible. A one-off script is often
  used during an incident or migration; silent drops create follow-up work.

## Output Expectations

- Include a run comment near `main()` showing the Bun command and env-file shape.
- Guard required env vars before creating clients or making calls.
- Use clear types for input rows, selected database records, parsed API payloads,
  and final result rows.
- Print enough progress for long jobs: counts found, counts skipped, batch
  progress, failures, output path, and elapsed time.
- Avoid unbounded `Promise.all` for large input sets. Use bounded concurrency or
  explicit batches so API limits and database pools stay under control.
- Close database clients in `finally`, even when the script fails.
- Prefer narrow validation such as formatter/checker commands for the changed
  script over whole-repo builds unless the user asks for broader validation.
