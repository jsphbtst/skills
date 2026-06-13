# skills

Agent skills by Joseph Bautista.

## Install

```bash
npx skills add jsphbtst/skills
```

Or install a single skill:

```bash
npx skills add jsphbtst/skills --skill anki-vocab-mining
```

## Skills

- **[anki-vocab-mining](skills/anki-vocab-mining/SKILL.md)** — mine vocabulary/terms from any source (PPTX, PDF, Notion, web page, image, text/CSV) into an Anki deck via the Anki MCP server: extract candidates, de-dup against the target deck, match the deck's note model, tag for traceability, and sync.

## Troubleshooting

**Installed, but Claude Code can't find the skill?** When you run `npx skills add` *without* an agent flag, it drops the real files in an agent-agnostic `.agents/skills/` directory and symlinks them **only into agent directories that already exist**. If there's no `.claude/` directory in the target yet, nothing gets linked there — and Claude Code only scans `.claude/skills/`, `~/.claude/skills/`, and plugins, never `.agents/`. The skill installs but stays invisible.

Cleanest fix: name the agent explicitly so it installs straight into `.claude/skills/`. The agent is `claude-code` (not `claude`):

```bash
npx skills add jsphbtst/skills --skill anki-vocab-mining -a claude-code
```

Add `-g` to install for every project (`~/.claude/skills/`) instead of just the current one.

Already installed into `.agents/` only? Either create a `.claude/` directory and re-run (the CLI will auto-link into it), or add the symlink yourself:

```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/anki-vocab-mining .claude/skills/anki-vocab-mining
```

The real files stay in `.agents/`, so a later `npx skills` update still flows through the symlink — don't copy, a copy drifts on update.
