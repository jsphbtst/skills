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

**Installed, but Claude Code can't find the skill?** `npx skills` keeps skills in an agent-agnostic `.agents/skills/` directory and symlinks them into each agent's path. When that symlink into `.claude/skills/` is missing — common with project-local installs — Claude Code can't see the skill, because it only scans `.claude/skills/`, `~/.claude/skills/`, and plugins, never `.agents/`.

Create the symlink yourself, mirroring what the CLI does:

```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/anki-vocab-mining .claude/skills/anki-vocab-mining
```

The real files stay in `.agents/`, so a later `npx skills` update still flows through the symlink (don't copy — a copy drifts on update). Symlink into `~/.claude/skills/` instead if you want the skill available in every project rather than just the current one.
