---
name: anki-vocab-mining
description: >-
  Mine vocabulary, terms, or flashcard content from a source resource — PPTX,
  PDF, Notion page/database, web page, image/screenshot, or plain text/CSV — and
  ingest it into an Anki deck via the Anki MCP server. Use when the user wants to
  turn a document or resource into Anki cards: extract the items, de-duplicate
  against the target deck, format them to match the deck's note model, tag them
  for traceability, and sync. Discovers the target deck/model/fields rather than
  assuming them. Requires the Anki MCP server (AnkiConnect) running; some sources
  need their own MCP/tooling (e.g. the Notion MCP for Notion sources).
---

# Anki Vocab Mining

Turn a source resource into review-ready Anki cards. The skill is
**source-agnostic** (PPTX / PDF / Notion / web / image / text) and
**deck-agnostic** (it inspects the target deck's note model and matches it,
rather than hardcoding a format).

## Core principles

- **Discover, don't assume.** Inspect the target deck + note model + fields
  before formatting cards. If they're not specified and can't be inferred from
  an existing deck, ask.
- **Only ingest what's in the source.** Never invent terms, sentences, or whole
  sections. If unsure an item exists, go back and verify it in the source.
- **The deck is the source of truth.** De-dup new candidates against what's
  already in the target deck before adding.
- **Flag anything you generated.** Readings/translations/definitions you
  produced yourself (vs. taken from the source) should be called out for the
  user to spot-check.

## Step 1 — Understand the target

Use the Anki MCP to learn where cards go and what shape they take:

1. `list_decks` — confirm/locate the target deck (look it up by name).
2. `model_names` + `model_field_names` — get the note model and its fields.
3. Pull a few existing notes (`find_notes` → `notes_info`) to see the **actual
   formatting convention** in use (what's on the front, how the back is laid
   out, any HTML like `<br>`, tag patterns). Match it.

If the user hasn't named a deck/model and there's no obvious existing one, ask:
which deck, which note model, and how fields map (what goes on the prompt side
vs. the answer side). Don't guess silently for a bulk add.

## Step 2 — Extract candidates from the source

Goal: a clean candidate list, each item = the **key/prompt field** (the term)
plus whatever **supporting fields** the source provides (reading, definition,
translation, example sentence, part of speech).

Pick the technique by source type:

- **PPTX** — files are often 100 MB+ (embedded media). **Never unzip the whole
  archive.** Use the bundled helper, which extracts only the slide XML:
  ```bash
  python3 scripts/extract_pptx_slides.py "<file>.pptx"
  ```
  It prints text grouped per slide so list/term/summary structure stays visible.

- **PDF** — for text PDFs, `pdftotext "<file>.pdf" -` or a Python extractor. For
  scanned/image-heavy or layout-sensitive PDFs, the **Read tool reads PDFs
  visually** (use the `pages` range; ≤20 pages/request) — better for tables and
  furigana/diacritics than raw text extraction.

- **Notion** — `notion-fetch` the page → it usually contains an inline database
  (`<database … data-source-url="collection://…">`). Fetch the `collection://…`
  data source for its schema, then **sweep it**: semantic `notion-search` caps
  at ~25 results/query, so run several themed queries scoped to the
  `data_source_url` until new queries only return already-seen rows. `notion-fetch`
  individual rows for exact field values when the net-new set is small.
  *Gotcha:* a guest-shared page from **another** workspace is unreachable by the
  integration (404 / object_not_found) — have the user duplicate it into their
  own space and share that. Token expired → user runs `/mcp` to re-authorize.

- **Image / screenshot** — use the **Read tool** (vision) to read terms off the
  image.

- **Web page** — `WebFetch` the URL and extract the term list from the content.

- **Plain text / CSV / TSV / Markdown** — parse directly into rows.

Capture **source-provided readings/definitions verbatim** when present (they're
authoritative). Generate them yourself only to fill gaps, and flag those.

## Step 3 — De-duplicate against the target deck

1. `find_notes deck:"<deck>"` (limit ≤500) to get all note IDs.
2. `notes_info` in batches of **≤100** (hard cap), `include_fields:["<key
   field>"]` to keep responses small. Hold every existing key value in memory.
3. Drop candidates whose key field already exists in the deck — including
   trivial punctuation/variant forms. When a near-variant is *meaningfully*
   different (a real distinction worth a separate card), hold it and ask rather
   than silently adding or dropping.
4. Keep a list of everything you skipped, to report.

> Cross-deck duplicates are usually fine: a focused study deck is its own
> environment, so pass `allow_duplicate=true` to ignore warnings that fire only
> because the item exists in *another* deck. (This is the sensible default;
> confirm if the user wants stricter behavior.)

## Step 4 — Add the cards

`add_notes` with:
- `deck_name`, `model_name` (from Step 1),
- `notes`: each with `fields` mapped to the model's field names,
- `allow_duplicate: true` (per the dedup note above),
- shared `tags` for traceability — at minimum a stable project/source tag, plus
  a per-source tag (e.g. a lesson/chapter id or the source date), and optional
  finer sub-tags. Mirror whatever tagging convention the deck already uses.
- batches **≤100** (one batch per source file).

Keep the returned `note_id`s — you'll need them for repositioning and reporting.

## Step 5 — Reposition (only if asked)

If the user wants new cards prioritized, `card_management` → `reposition` with
the **actual** card IDs from Step 4 (never guessed/sequential IDs),
`shift_existing: true`, `starting_from: 1`. Otherwise leave order alone.

## Step 6 — Sync and report

- `mcp__anki__sync`.
- Report concisely: **added** (count, grouped by kind, with tags), **skipped**
  (every dedup collision/variant, so the user can override), **judgment calls**
  (anything held back or skipped as non-content scaffolding), **verification**
  (source-provided vs. self-generated fields; for swept sources, whether
  coverage saturated), the **deck total**, and whether you repositioned.

## Anki MCP reference

- `mcp__anki__list_decks`, `model_names`, `model_field_names` — discover target.
- `mcp__anki__find_notes` — query (limit ≤500).
- `mcp__anki__notes_info` — details; **≤100 notes/call**; use `include_fields`.
- `mcp__anki__add_notes` — batch add; `allow_duplicate`; **≤100/batch**; returns
  `note_id`s.
- `mcp__anki__card_management` (`reposition`) — only on request; **real** card
  IDs; `shift_existing:true`.
- `mcp__anki__sync` — at the end.

## Guardrails

- **Never fabricate.** Only add items verified present in the fetched source.
  Don't query made-up IDs or assume a source "should" contain a section. (Once
  you commit invented cards, someone has to find and delete them.)
- **Confirm format before bulk-adding** when the deck/model/field-mapping isn't
  already established — a wrong mapping means re-doing the whole batch.
- **Use real `note_id`s for reposition.** Guessed sequential IDs silently
  reposition 0 cards.
- **Flag self-generated fields** (auto readings, machine translations) for a
  spot-check; prefer source-provided values.
- **Respect tool limits** (≤100 per `notes_info` / `add_notes` batch).
- **Don't expand scope** beyond the requested source/resource.

## Bundled scripts

- `scripts/extract_pptx_slides.py` — extract slide text from a large `.pptx`
  without unpacking embedded media. Language-agnostic.

## Wiring this skill up

Install it with `npx skills add jsphbtst/skills --skill anki-vocab-mining`. It
then auto-activates on requests like "mine the vocab from this deck/PDF into
Anki," or can be invoked explicitly.
