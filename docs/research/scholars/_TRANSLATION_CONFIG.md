# Translation Configuration

Single source of truth for translator identifiers used in scholar JSON
`translations[]` entries. Subagents producing surveys MUST read this
file and use the values below verbatim.

## Current values (last updated 2026-04-29)

- **translator**: `anthropic:claude-opus-4-7`
- **method**: `llm`
- **register**: `modern-faithful`

## Update protocol

When a new Opus model ships, update the `translator` field above and
set the date. Past surveys retain their original translator identifier
(provenance preserved); do NOT rewrite history when the value rolls
forward. The validator's `translator` regex
(`^[a-z0-9_-]+:[a-z0-9._-]+$`) accepts any well-formed
`<provider>:<model>` string, so older entries continue to validate
after this file is updated.

## Why this file exists

Hardcoding the translator identifier in `_SURVEY_BRIEFING.md` (or in
per-scholar dispatch prompts) caused drift the moment a new Opus
shipped: the briefing said `claude-opus-4-6` while the runtime was
already on `claude-opus-4-7`. Pulling the value into one document
keeps every survey subagent in lockstep with the project's current
LLM-translation contract and makes the rollover a single-file edit.
