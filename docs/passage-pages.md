# Passage Pages — handbook

Two static-site visual idioms exist for sermon-passage work. Both are GitHub-Pages-hosted, no build step, single-page sites that share the editorial discipline (oklch palette, Source Serif 4 + Gentium Plus + Frank Ruhl Libre, motion that argues, paraphrastic English only, no emoji, BC/AD).

## The two templates

### 1. TEAM page — `tendflock/romans-3-9-20`

**Purpose:** afternoon teaching session that goes deeper into the morning's sermon. Format is **T**each / **E**quip / **A**pply / **M**ission, ~45 minutes, projected to a 15-40 person fellowship hall, driven from the front by keyboard or presenter clicker.

**Visual idiom:** Apple-product-page cinematic — full-viewport scenes per section, massive type, one focal element per scene, generous whitespace, scroll choreography (catena threaded-pearls line draws as you scroll). See `feedback_apple_style_idiom.md` in memory.

**Use this when** the passage is one Bryan preached that morning and the goal is to take the room deeper into language, history, theology, application, and mission.

**Live:** https://tendflock.github.io/romans-3-9-20/
**Spec:** `docs/superpowers/specs/2026-04-27-romans3-team-page-design.md`
**Plan:** `docs/superpowers/plans/2026-04-27-romans3-team-page.md`
**Adaptation walkthrough:** `tendflock/romans-3-9-20/TEMPLATE.md`
**Style rules:** `tendflock/romans-3-9-20/STYLE.md`

### 2. Textual-history page — `tendflock/Romans3`

**Purpose:** scholarly textual-history piece — long-form scrolling narrative tracing how a passage relates to its source texts, how its wording was transmitted, and what the manuscript witnesses say. Confidence-tagged claims (`documented` / `strong-judgment` / `noted-gap`).

**Visual idiom:** muted editorial — chapter-by-chapter argument, motion only when it argues (mosaic, hinge thread, back-absorption animation), text-first.

**Use this when** the goal is research output — a piece you'd link from a sermon footnote, share with a fellow pastor, or use as the deeper-link from a TEAM page.

**Live:** https://tendflock.github.io/Romans3/
**Style rules:** `tendflock/Romans3/STYLE.md`

The two formats are complementary. A TEAM page can link to a textual-history page as its `sendOut.deeperLink` (the Romans 3:9-20 TEAM page links to the Romans3 site for the catena scholarship).

## Repo naming

Passage-only, hyphenated, lowercase: `romans-3-9-20`, `romans-3-21-26`, `daniel-7-1-14`. The TEAM-vs-textual-history distinction is **inside** the repo (style + content shape), not in the name.

## Quick start — new TEAM page for next week's sermon

```bash
cd /Volumes/External
gh repo create tendflock/<passage-slug> --public --clone
cd <passage-slug>
cp -r ../romans-3-9-20-team-source/{index.html,app.js,styles.css,theme.css,tools,STYLE.md,TEMPLATE.md,data.example.js,LICENSE} .
# (Or just clone romans-3-9-20 and rename.)
cp data.example.js data.js
```

Then:

1. Edit `data.js` — passage-specific content. Required fields: `meta`, `teach[]` (drop kinds not relevant; add new kinds as needed), `equip` (mirror the morning handout's blanks), `apply[]` (8-12 socratic questions), `mission[]` (8-12 questions tagged `evangelism` / `apologetics` / `home` / `abroad`), `sendOut`.
2. Validate: `node tools/validate-team-data.js data.js`. Expected: `ok ... — valid TEAM data`.
3. Smoke test in Chrome at 1080p. Drive by keyboard: `Home`, `1`, `2`, `3`, `4`, `End`, `r`, `f`, `?`. Verify each interaction.
4. Push. Enable GitHub Pages from `main` / root. URL is `https://tendflock.github.io/<passage-slug>/`.

The full walkthrough is in `tendflock/romans-3-9-20/TEMPLATE.md`. Editorial rules in `STYLE.md`.

## Quick start — new textual-history page

Clone `tendflock/Romans3`, rename, edit `data.js` to your passage's source-text mapping. The Romans3 build is more idiosyncratic (each passage has different textual-history shape — back-absorption, doublets, manuscript witnesses) so plan on adapting the chapter set per passage rather than just filling a template.

## When to build which

| Audience | Use |
|----------|-----|
| Afternoon TEAM session | TEAM page (`romans-3-9-20` template) |
| Standalone scholarly piece | Textual-history page (`Romans3` template) |
| Both — TEAM links out to deeper textual scholarship | Build both, set `sendOut.deeperLink` on the TEAM page to the textual-history URL |

## Adding a new Teach block kind

If the next passage needs a Teach kind that doesn't exist yet (e.g., `hebrew-terms` for an OT passage, `covenant-pattern` for a Genesis text, `chiasm-structure` for a Hebrew poem):

1. Add the kind name to `KNOWN_TEACH_KINDS` in `tools/validate-team-data.js`.
2. Implement `teachRenderers["new-kind"](el, block)` in `app.js`. Typical shape: 30-60 lines.
3. Add the kind's CSS to `styles.css`.
4. Re-run validator + smoke test.

The four kinds shipped in the Romans 3:9-20 build are `catena`, `greek-terms`, `courtroom-chain`, `body-parts`. Most NT passages will reuse `greek-terms`. Catena/courtroom/body-parts are passage-specific.

## Visual idiom — non-negotiable

(Inherited from `tendflock/Romans3` STYLE.md, with TEAM additions.)

- No emoji. Anywhere.
- BC / AD, not BCE / CE.
- **Paraphrastic English only.** No pasted ESV / NIV / NRSV / NASB / KJV.
- Ancient text from public-domain critical editions only (NA / UBS, Rahlfs-Hanhart, BHS).
- Three faces only: Source Serif 4, Gentium Plus, Frank Ruhl Libre.
- oklch palette, low chroma. No hard-coded hex except true neutrals.
- Motion argues or doesn't exist.
- TEAM page: each section is a full-viewport scene; massive type; one focal element; generous whitespace; theme alternates light/dark/light/dark across sections.
- TEAM page: no new handout — Equip mirrors the morning sermon handout's blanks.

If something feels cramped, it is — make it bigger, give it room, drop the chrome.
