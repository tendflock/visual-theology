# WS0b Scholar Survey — Shared Briefing

**All four WS0b research subagents read this file first.** Individual scholar specs below override
where they differ.

## Your role

You are one of four parallel research subagents producing structured surveys of named scholars'
positions on Daniel / Revelation. Output = one JSON file at
`docs/research/scholars/<SCHOLAR_SLUG>.json`.

## Why this work matters

Bryan's visual-theology pilot (Daniel 7) must represent every tradition from its own best voices,
factually, with verifiable citations. The current research doc uses article numbers only — a
scholar with the book in hand cannot confirm the citation. Your survey produces citations in the
new dual-citation schema (`docs/schema/citation-schema.md`) that carry native section IDs and
(where available) page numbers.

## Working directory + environment

```bash
cd /Volumes/External/Logos4
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

PM2: never run `pm2 kill`, `pm2 stop all`, `pm2 delete all` — other apps share this PM2. Leave it
alone unless you need to run pytest (you don't for this task).

## The 16-axis taxonomy

Read the "Expanded axis catalog (v2)" section of
`docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md`. Pilot axes are
**A, B, C, E, F, H, J, K, L, N, O** — eleven of sixteen. Axes P, Q are meta; include only if your
scholar explicitly argues on them.

## Toolchain

Use `tools/citations.py` for building citations. Do NOT re-implement sha256 or derivation logic.

```python
import sys; sys.path.insert(0, 'tools')
from citations import build_citation, sha256_of
from study import get_article_meta, read_article_text, get_resource_articles
from logos_batch import LogosBatchReader

# Building a citation (handles page/section/sha256 derivation for you):
c = build_citation(
    resource_file="<RESOURCE_FILE>",   # e.g. "HRMNEIA27DA.lbxlls"
    article_num=123,
    quote_text="... verbatim fragment from article text ...",
    author="Collins",
    short_title="Hermeneia Daniel",
    full_title="Daniel: A Commentary on the Book of Daniel (Hermeneia)",
)

# Fast scanning — batch reader keeps the Logos lib loaded:
r = LogosBatchReader(); r.start()
txt = r.read_article("<RESOURCE_FILE>", article_num, max_chars=200000)
arts = r.list_articles("<RESOURCE_FILE>")  # list of (num, id) tuples
r.stop()

# Single reads (spawn a subprocess per call — slower):
txt = read_article_text("<RESOURCE_FILE>", article_num, max_chars=200000)
```

## Workflow

1. **Orient.** Run `get_resource_articles` or `LogosBatchReader.list_articles` once to see article
   IDs. Article IDs encode content — for Daniel commentaries, expect `DA.7.13`-style IDs.
   Skim the TOC by running `dotnet run --project tools/LogosReader/LogosReader.csproj -- --toc
   <FILE>` if the layout is unclear.
2. **Identify payload.** For Daniel 7 pilot axes, find the articles that engage Daniel 7,
   introductions to major sections (dating, genre, apocalyptic), and any cross-book integrations
   (Son of Man, Little Horn, Four Kingdoms). For systematic works, find the eschatology section.
3. **Read broadly, then deeply.** Sample 5–10 articles across the work; then read the pivotal
   ones fully. Prefer `LogosBatchReader` for speed.
4. **Extract verbatim quotes** (40+ chars preferred) tied to specific axis positions. Always open
   with `max_chars=200000` because articles can be 40k–80k chars and the default truncates.
5. **Compose citations** with `build_citation`. If the article is non-extant or unreadable, skip
   that citation; do not invent.
6. **Validate.** For every citation you emit, run `verify_citation(c)` from `tools/citations.py`
   and confirm `status == "verified"`. If a citation fails to verify, either find a different
   quote that does, or paraphrase (set `quote_text=None`).
7. **Assemble JSON.** See canonical shape below. Write to
   `docs/research/scholars/<SCHOLAR_SLUG>.json`.

## passageCoverage (REQUIRED — added WS0c-8)

Every scholar JSON must include a top-level `passageCoverage[]` array — the list of
biblical verse-blocks the surveyed material engages substantively. The validator
enforces a controlled vocabulary; pick from this list (extend in
`tools/validate_scholar.py:PASSAGE_COVERAGE_VOCAB` if you genuinely need a new one):

- Daniel 7 verse-blocks: `Dan 7:1-6`, `Dan 7:7-8`, `Dan 7:9-12`, `Dan 7:13-14`,
  `Dan 7:15-18`, `Dan 7:19-22`, `Dan 7:23-27`
- Adjacent Daniel: `Dan 2:31-45`, `Dan 8:1-27`, `Dan 9:1-19`, `Dan 9:20-27`,
  `Dan 10:1-21`, `Dan 11:1-45`, `Dan 12:1-13`
- NT cross-refs: `Rev 1`, `Rev 13`, `Rev 17`, `Rev 20`, `Matt 24`, `Mark 13`
- Second-Temple reception: `1 En 37-71`

A scholar who only engages Dan 7 + Rev 13 has `passageCoverage: ["Dan 7:13-14",
"Rev 13"]`. A systematic theology engaging the kingdom across multiple Dan chapters
might have 8+ entries. Be honest about scope; this drives per-passage coverage
diagnostics across the corpus.

## Output JSON shape

```json
{
  "scholarId": "<slug, same as filename>",
  "authorDisplay": "<short author name>",
  "workDisplay": "<short title>",
  "resourceId": "LLS:...",
  "resourceFile": "<file.logos4 or .lbxlls>",
  "traditionTag": "<cluster label, e.g. critical-modern>",
  "commitmentProfile": {
    "strong":   ["<axis_id>: <position> — why (one sentence)"],
    "moderate": [],
    "tentative": []
  },
  "positions": [
    {
      "axis": "B",
      "axisName": "Fourth kingdom",
      "position": "Rome",
      "commitment": "strong",
      "rationale": "<scholar's own argument, one paragraph, no quote>",
      "compositional": null,
      "citations": [ /* objects produced by build_citation() */ ]
    }
  ],
  "crossBookReadings": [
    {
      "targetPassage": "Rev 13",
      "positionSummary": "<one paragraph>",
      "citations": []
    }
  ],
  "distinctiveMoves": [
    "<methodological move — one sentence each>"
  ],
  "uncertainties": [
    "<where the scholar hedges or is silent on a pilot axis>"
  ]
}
```

## Discipline

- **Fabrication kill-switch:** every `quote.text` must appear in the named article (case-insensitive
  after whitespace normalization). `build_citation` + `verify_citation` enforce this. If the
  article lacks the quote, change the quote — never invent.
- **No strawmen.** Represent the scholar in their own vocabulary. Do not retrofit them to a
  tradition stereotype. If they diverge from the tradition's usual summary, say so in
  `distinctiveMoves`.
- **Commitment strength is intrinsic, not derived.** Read the prose for hedges ("I must confess I
  am still unsettled"), explicit commitments ("I hold firmly"), or sub-axes the scholar tags
  secondary.
- **Page numbers are nullable.** Four of our WS0b resources lack milestone indexes (Collins
  Hermeneia, Walvoord, B&B, Durham). `get_article_meta` will return `pageStart: null` for those —
  that's fine, `build_citation` handles it.

## Verification checklist (run before claiming DONE)

```python
# Load your output
import json
with open("docs/research/scholars/<slug>.json") as fh:
    s = json.load(fh)

from citations import verify_citation
total = 0; verified = 0; fails = []
for pos in s["positions"]:
    for c in pos.get("citations", []):
        total += 1
        v = verify_citation(c)
        if v["status"] == "verified": verified += 1
        else: fails.append((pos["axis"], c["backend"], v))
for x in s.get("crossBookReadings", []):
    for c in x.get("citations", []):
        total += 1
        v = verify_citation(c)
        if v["status"] == "verified": verified += 1
        else: fails.append(("crossBook", c["backend"], v))
print(f"verified {verified}/{total}")
for f in fails[:5]: print(f)
```

Ship only if `verified / total >= 0.95` AND every `positions[].citations` list has ≥ 1 verified entry.

## Report back

250 words max:
- Articles sampled and read deeply
- Axes covered (count)
- Citations emitted (and verification rate)
- Any surprises (e.g., scholar silent on an expected axis)
- Time spent

Return status: `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, `NEEDS_CONTEXT`.
