# Romans 3:9-20 TEAM Page — Design Spec

Date: 2026-04-27
Status: Draft v1 (post-brainstorm, awaiting user review before implementation plan)
Author: Bryan + Claude
Spec lineage: brainstorm session 2026-04-26 / 2026-04-27, mockups in `.superpowers/brainstorm/45010-1777296249/content/`

---

## Project Context

Bryan preaches a sermon weekly, then teaches an afternoon "TEAM" session that goes deeper into the same passage. TEAM is a fixed four-block format he runs every week:

- **T**each — language, history, archaeology, theology.
- **E**quip — quick overview of the sermon points (the morning-handout structure).
- **A**pply — Socratic application questions.
- **M**ission — evangelism, apologetics, and missions (home and abroad) questions.

Bryan attempted to build a static page for the Romans 3:9-20 TEAM session via codex CLI; the result is at `tendflock/romans3_chalk_and_talk`. It applied a literal chalkboard skeumorphism (wood frame, slate, rotated chalk-paper labels) and stacked six redundant sections that all restated the sermon outline in different costumes. Bryan rejected it. The reference design he wanted the page to draw from is `tendflock/Romans3` — a muted-editorial textual-history site for Romans 3:10-18 with a mosaic of Paul's six OT sources, single-source-of-truth `data.js`, and motion that argues rather than decorates.

This spec defines the rebuild.

## Project Goal

Build a static, projection-friendly, single-page TEAM teaching aid for Romans 3:9-20 that:

1. Uses the visual-editorial discipline of `tendflock/Romans3` (oklch palette, three-font type stack, motion-only-when-it-argues, single-source `data.js`).
2. Adapts each TEAM section's interaction pattern to its content rather than forcing one pattern across all four.
3. Functions as a template — a sibling repo per future passage, with `data.js` as the only file that needs editing for content.
4. Serves Bryan as live driver with clicker-compatible keyboard shortcuts at 1080p projection in a 15-40 person fellowship hall.

The Romans 3:9-20 build is week one. Future weeks (Romans 3:21-26, etc.) follow the same template.

## Audience and Setting

- **Setting:** fellowship hall / classroom, 15-40 people, single projected screen behind Bryan.
- **Driver:** Bryan with laptop or tablet at the front, optionally a presenter clicker.
- **Format:** ~45 minutes total — Teach ~15, Equip ~7, Apply ~12, Mission ~10.
- **No new handout.** Attendees brought the morning sermon handout (with blanks they filled during the sermon). Equip references that handout; it does not duplicate it as a printable.

The page is purely a projected teaching surface. There is no print view, no per-attendee URL, no companion app.

## Argument Arc (TEAM)

The page renders the four TEAM letters as four sections plus a Hero opener and a Send-out closer. Each section's interaction pattern is chosen for its content:

- **Hero** — scene-setting; passage, homiletical point, take-home truth, T/E/A/M roadmap.
- **Teach** — long-scroll editorial with four sub-blocks (catena, Greek terms, courtroom, body-parts).
- **Equip** — single panoramic panel: three-card sermon structure with revealable blanks.
- **Apply** — slide-by-slide; one question per screen, ten total.
- **Mission** — slide-by-slide; one question per screen, ten total, mixed tags (evangelism / apologetics / home / abroad).
- **Send-out** — take-home truth + optional outbound link to deeper resources.

Theme alternates Hero (light) → Teach (light) → Equip (dark) → Apply (light) → Mission (dark) → Send-out (light). The contrast keeps each section visually distinct as the room moves through 45 minutes.

## Page Anatomy and Section Interactions

### Hero

Static. Single screen. Contents:

- Passage label: `Romans 3:9-20 · TEAM`.
- Homiletical point in italic: *Stop trying to justify yourself and look to Christ for righteousness.*
- Take-home truth in muted serif: *Accept the guilty verdict of sinner and flee to Christ, the only righteous one.*
- TEAM roadmap chip: `Teach · Equip · Apply · Mission` (no times; see "Out of scope").

Light theme.

### Teach

Light theme. Long-scroll editorial. Four blocks; each block has a "show, don't tell" graphic that animates in as Bryan clicks or scrolls through it. The active block brightens; others dim slightly.

**Block 1 — Catena.** Eyebrow label: `CATENA`. Title: *Paul's six sources flowing into Romans 3:10-18.* Graphic: a schematic of six color-coded curves (one per source) drawing into a baseline that represents the Romans 3:10-18 verse. Each source's curve and verse phrase highlight together when its label is clicked. Sources and colors are ported from `tendflock/Romans3`.

**Block 2 — Greek terms.** Eyebrow label: `GREEK`. Title: *Key terms — what the words carry.* Graphic: a row of clickable Greek-term chips in Gentium Plus. Click any chip to expand inline with gloss, verse reference, and a short note on what the term does in Paul's argument. Active chip is dark.

The seven terms for Romans 3:9-20: ὑφ' ἁμαρτίαν (under sin), οὐκ ἔστιν / οὐδὲ εἷς (universal negation), ὑπόδικος (answerable to God), δικαιωθήσεται (will be justified), ἐξ ἔργων νόμου (by works of law), ἐπίγνωσις ἁμαρτίας (knowledge of sin), δίκαιος (righteous).

**Block 3 — Courtroom.** Eyebrow label: `COURTROOM`. Title: *God as righteous Judge — the frame from Romans 2-3.* Graphic: four nodes connected by arrows showing the courtroom-language chain: 2:2-6 (judge truly) → 3:4 (God true) → 3:6 (judge world) → 3:19-20 (verdict). Each node lights as Bryan clicks; the verdict node is the climax.

**Block 4 — Body-parts.** Eyebrow label: `BODY-PARTS`. Title: *Throat · tongue · lips · mouth · feet · paths · eyes.* Graphic: a typographic verse mosaic of Romans 3:13-18 in paraphrastic English. Each phrase is on its own line, color-coded by body part, with a small-caps label and verse reference at the right margin. Click any phrase to make it active (dark ink + bg). The "eyes" phrase is the climax (rebellion at the root) and renders as the default active phrase.

The English is paraphrastic per the Romans3 editorial rule (no copyrighted translations).

### Equip

Dark theme. Single panel. No subhead — just `Equip` as the eyebrow.

Layout (top to bottom):

1. **Big Idea statement** — full sentence with two revealable blanks: *Accept the guilty `____` of sinner and `____` to Christ, the only righteous one.* Answers: `verdict`, `flee`.
2. **Three-card row** — Charge / Proof / Verdict, side by side. Each card shows roman numeral, name (revealable blank), verse range, summary, and a Christ-thread sentence with one revealable blank.
   - I — *The `____`* (vv. 9-12) — Universal condemnation — *Christ is the only `____`.* Blanks: `Charge`, `exception`.
   - II — *The `____`* (vv. 13-18) — Evidence of depravity — *Christ was the only one `____` yet without sin.* Blanks: `Proof`, `tested`.
   - III — *The `____`* (vv. 19-20) — No self-justification possible — *Christ is the only `____`.* Blanks: `Verdict`, `answer`.
3. **This Week row** — *When you sin, don't `____` yourself — `____` to Christ for righteousness.* Blanks: `justify`, `flee`.

Click any blank to fill it. Press `r` to reveal all blanks at once.

The blanks correspond to what attendees already wrote on their morning handout. The page reviews; it does not re-quiz.

### Apply

Light theme. Slide-by-slide. Ten Socratic questions, one per screen. Each slide:

- Section eyebrow: `QUESTION N OF 10`.
- Question in large italic serif (Source Serif 4, ~1.6rem).
- Tag chips below question (e.g., `Confession`, `Self-justification`, `Words`, `Comparison`, `Family`, `Conscience`).

Arrow keys, space, page-down, or clicker advance. Mini pagination dots in the corner.

### Mission

Dark theme. Slide-by-slide. Same pattern as Apply, ten questions. Tags split across four flavors:

- `Evangelism` — how to share the gospel with unbelievers.
- `Apologetics` — how to answer objections.
- `Missions Home` — local outreach.
- `Missions Abroad` — cross-cultural / international.

A given question may carry one or more tags.

### Send-out

Light theme. Static. Contents:

- Eyebrow: `CLOSE`.
- Heading: *Take-home truth.*
- Take-home truth in italic serif: *Accept the guilty verdict of sinner and flee to Christ, the only righteous one.*
- Optional outbound link: *Romans 3 textual history* → `https://tendflock.github.io/Romans3` for attendees who want to dig deeper into the catena scholarship.

## Visual Identity

### Type stack (inherited from Romans3)

- **Source Serif 4** — all English prose, headings, UI.
- **Gentium Plus** — Greek (NT and LXX).
- **Frank Ruhl Libre** — Hebrew (loaded but rarely used in TEAM Romans 3:9-20; available for other passages).

No fourth face. No system fonts.

### Palette

All colors via `oklch()`. Chroma stays low (~0.05-0.13) for body and mid-tone elements. Section accent (eyebrows, active highlights) sits at oklch(0.50 0.13 25) — a muted dark rust matching the Romans3 site.

**Light theme** (Hero, Teach, Apply, Send-out):

- Page bg — `oklch(0.95 0.02 80)` (warm cream).
- Card bg — `#ffffff`.
- Body ink — `#222`.
- Muted ink — `#666` to `#888`.
- Section accent — `oklch(0.50 0.13 25)`.

**Dark theme** (Equip, Mission):

- Page bg — `#1a1a1a`.
- Body ink — `#f5f0e8` (warm cream).
- Eyebrow accent — `#d8c098`.
- Question italic on dark page sits calmly while the room thinks.

**Catena source colors** — six muted hues at chroma ~0.05-0.13, one per OT source. Ported directly from Romans3's `sources` table:

| Source | Hue | Role |
|--------|-----|------|
| Psalm 14 / 53 | 25 | Paul's anchor; first quotation block |
| Psalm 5 | 200 | First catena pivot |
| Psalm 140 | 290 | Venom line |
| Psalm 10 | 75 | Cursing / πικρίας |
| Isaiah 59 | 340 | Feet / paths / no peace |
| Psalm 36 | 158 | Closing — no fear of God |

**Body-parts colors** — six muted hues, one per non-climax body part. The body-parts palette is *independent* of the catena palette (each visualization picks hues for internal visual distinction; we don't try to map a body part to its source-of-origin hue, which would force throat-tongue to share a hue and weaken the sequence). Body-parts hues: 32 / 200 / 290 / 78 / 344 / 158. The eyes phrase renders as dark ink on cream rather than tinted — it is the climax (rebellion at the root).

### T / E / A / M rail

A sticky left-side rail with five circles, top to bottom: Hero dot (`·`), then `T`, `E`, `A`, `M`.

- **Outline state** — letter is upcoming; light cream fill, gray ink, thin border.
- **Active state** — letter is current section; dark fill, cream ink.
- **Passed state** — letter is completed; medium-cream fill, muted gray ink, thin border.

Click any letter to jump-scroll to that section. Hidden below 768px viewport width; replaced by a top-edge nav strip.

## Driver UX (Keyboard)

A standard presenter clicker maps to PageDown / PageUp. The page also responds to:

| Key | Action |
|-----|--------|
| `↓` / `Space` / `PgDn` | Advance — next slide in Apply/Mission, smooth-scroll to next block in Teach/Equip |
| `↑` / `PgUp` | Back — previous slide or block |
| `1` / `2` / `3` / `4` | Jump to Teach / Equip / Apply / Mission |
| `Home` | Top of page (Hero) |
| `End` | Bottom of page (Send-out) |
| `r` | Reveal all blanks (Equip only) |
| `f` | Fullscreen toggle (browser API) |
| `?` | Toggle keyboard help overlay |

## Data Model — `data.js`

Single source of truth for the passage's content. Renderer (`app.js`) is passage-agnostic; new passages adapt by editing this file.

```javascript
window.TEAM_DATA = {
  meta: {
    passage: "Romans 3:9-20",
    burden: "Stop trying to justify yourself and look to Christ for righteousness.",
    takeHome: "Accept the guilty verdict of sinner and flee to Christ, the only righteous one.",
    sermon: { title: "Stop Trying to Justify Yourself", date: "2026-04-26" }
  },

  teach: [
    { kind: "catena",          title: "Paul's six sources flowing into Romans 3:10-18",
      sources: [...],          phrases: [...] },
    { kind: "greek-terms",     title: "Key terms — what the words carry",
      terms: [
        { greek: "ὑφ' ἁμαρτίαν", gloss: "under sin", ref: "3:9",
          note: "Slavery, power, guilt, condemnation",
          cue: "Sin is not only acts committed; it is a realm and ruler apart from Christ." },
        // ... 7 total
      ] },
    { kind: "courtroom-chain", title: "God as righteous Judge — the frame from Romans 2-3",
      nodes: [
        { ref: "2:2-6",   label: "judge truly" },
        { ref: "3:4",     label: "God true" },
        { ref: "3:6",     label: "judge world" },
        { ref: "3:19-20", label: "verdict", terminal: true }
      ] },
    { kind: "body-parts",      title: "Throat · tongue · lips · mouth · feet · paths · eyes",
      phrases: [
        { part: "THROAT", english: "Their throat is an opened grave",
          image: "grave",   ref: "3:13a",   hue: 32  },
        { part: "TONGUE", english: "Their tongues practice deceit",
          image: "deceit",  ref: "3:13b",   hue: 200 },
        { part: "LIPS",   english: "The venom of vipers is under their lips",
          image: "poison",  ref: "3:13c",   hue: 290 },
        { part: "MOUTH",  english: "Their mouth is full of cursing and bitterness",
          image: "cursing", ref: "3:14",    hue: 78  },
        { part: "FEET",   english: "Their feet are swift to spill blood",
          image: "violence", ref: "3:15",   hue: 344 },
        { part: "PATHS",  english: "Ruin and misery mark their paths; the road of peace they have not known",
          image: "ruin",    ref: "3:16-17", hue: 158 },
        { part: "EYES",   english: "There is no fear of God before their eyes",
          image: "no fear of God", ref: "3:18", climax: true }
      ] }
  ],

  equip: {
    bigIdea: {
      template: "Accept the guilty {a} of sinner and {b} to Christ, the only righteous one.",
      blanks: [{ key: "a", answer: "verdict" }, { key: "b", answer: "flee" }]
    },
    movements: [
      { roman: "I",   nameTemplate: "The {a}",
        nameBlank: { answer: "Charge" },  ref: "vv. 9-12",  summary: "Universal condemnation",
        christ: { template: "Christ is the only {a}",
                  blanks: [{ key: "a", answer: "exception" }] } },
      { roman: "II",  nameTemplate: "The {a}",
        nameBlank: { answer: "Proof" },   ref: "vv. 13-18", summary: "Evidence of depravity",
        christ: { template: "Christ was the only one {a} yet without sin",
                  blanks: [{ key: "a", answer: "tested" }] } },
      { roman: "III", nameTemplate: "The {a}",
        nameBlank: { answer: "Verdict" }, ref: "vv. 19-20", summary: "No self-justification possible",
        christ: { template: "Christ is the only {a}",
                  blanks: [{ key: "a", answer: "answer" }] } }
    ],
    thisWeek: {
      template: "When you sin, don't {a} yourself — {b} to Christ for righteousness.",
      blanks: [{ key: "a", answer: "justify" }, { key: "b", answer: "flee" }]
    }
  },

  apply: [
    { question: "Where do you most quickly defend yourself: home, work, church, or private conscience?",
      tags: ["self-justification"] },
    // ... 10 total
  ],

  mission: [
    { question: "How can Romans 3 help us evangelize without sounding morally superior?",
      tags: ["evangelism"] },
    { question: "What's a self-justification story common in our community that the gospel exposes?",
      tags: ["apologetics", "home"] },
    // ... 10 total, mixed tags from {evangelism, apologetics, home, abroad}
  ],

  sendOut: {
    takeHome: "Accept the guilty verdict of sinner and flee to Christ, the only righteous one.",
    deeperLink: { url: "https://tendflock.github.io/Romans3",
                  label: "Romans 3 textual history" }
  }
};
```

The renderer dispatches each Teach block by its `kind`. Adding a new kind for a future passage requires one render function in `app.js` and matching styles. The seven kinds anticipated across passages: `catena`, `greek-terms`, `hebrew-terms`, `courtroom-chain` (or generic `verse-chain`), `body-parts` (generic `phrase-mosaic`), `historical-context`, `theological-categories`. Only the first four are needed for Romans 3:9-20.

## File Layout

```
romans-3-9-20-team/
├── index.html        single page; loads data.js, app.js, styles.css, theme.css
├── data.js           ONE FILE for content (the template seam)
├── app.js            renderer + interactions (passage-agnostic)
├── styles.css        full design system: type, palette, layout primitives
├── theme.css         per-section themes (light/dark alternation)
├── README.md         how to view it
├── STYLE.md          editorial rules — voice, BC/AD, no-emoji, paraphrastic English
├── TEMPLATE.md       how to copy this repo for a new passage
└── data.example.js   blank skeleton showing required fields
```

`app.js`, `styles.css`, `theme.css` contain no Romans-3 references. They know about content kinds (catena, greek-terms, courtroom-chain, body-parts, equip, apply, mission), not about specific passages.

## Template Seam (Week Two and Beyond)

To prepare a TEAM page for the next sermon:

1. Rename a fresh GitHub repo (or duplicate) to `<passage>-team` (e.g., `romans-3-21-26-team`).
2. Edit `data.js`. Update `meta`. Drop or add Teach blocks by `kind`. Refill Equip's `bigIdea`, `movements`, `thisWeek`. Write fresh `apply` and `mission` arrays. Update `sendOut`.
3. If the passage needs a Teach block kind that does not yet exist (e.g., `kind: "covenant-pattern"` for a passage on covenant theology), add a render function in `app.js` plus matching styles. The shape is small — typically 30-60 lines.
4. Run the schema validator (see "Testing"). Open in Chrome at 1080p. Drive through the whole session by keyboard. Confirm.

`TEMPLATE.md` walks through this in plain language. `data.example.js` shows the empty skeleton with required fields.

## Repo Decision

Rename the existing `tendflock/romans3_chalk_and_talk` GitHub repository to `tendflock/romans-3-9-20-team`, wipe the codex chalkboard implementation, and rebuild inside it. Same git history, new name. The codex commit stays as visible "what we tried first" archaeology in the log.

Reasoning: keeps the codex artifact accessible without polluting the org, gives the project a name that reflects the format, and avoids creating a sibling repo with a misnamed predecessor still alive.

## Editorial Charter (Inherited from Romans3)

Non-negotiable:

- **Scholarly but accessible voice.** Educated reader who isn't a specialist. Translate every Greek word the first time it appears in prose.
- **No emoji. BC/AD** (not BCE/CE).
- **Paraphrastic English only.** No pasted ESV, NIV, NRSV, NASB, KJV, or any copyrighted translation.
- **Ancient text from public-domain critical editions only.** Nestle-Aland / UBS for the Greek NT, Rahlfs-Hanhart for LXX.
- **No filler.** If a paragraph doesn't move the argument forward, cut it.
- **Muted oklch palette**, chroma low. No hard-coded hex except for true neutrals (`#fff`, `#222`, `#1a1a1a`).
- **Type stack fixed** — Source Serif 4, Gentium Plus, Frank Ruhl Libre. No fourth face.
- **Motion argues or doesn't exist.** Catena curves, Greek-term expansions, courtroom-chain build, body-parts active-phrase shift, Equip blank reveals, Apply/Mission slide advance — all argumentative. No decorative entrance animations.

TEAM-specific additions:

- **Adapt interaction per content.** Teach is editorial scroll. Equip is one panoramic panel with reveals. Apply and Mission are slide-by-slide. The page is one continuous scroll; sections vary in interaction without violating the scroll.
- **Theme alternation** Hero light → Teach light → Equip dark → Apply light → Mission dark → Send-out light.
- **No new handout.** Equip mirrors the morning sermon handout. Don't print or duplicate.

## Testing Strategy

- **Manual end-to-end** — open `index.html` in Chrome at 1080p (projection target). Drive through the whole session by keyboard (`↓ ↓ 1 2 3 4 r`). Verify:
  - Each Teach block's graphic animates in.
  - Catena curves draw and corresponding phrase highlights together.
  - Greek terms expand inline with gloss.
  - Courtroom verse-chain builds left to right.
  - Body-parts active phrase moves on click.
  - Equip blanks reveal individually and `r` reveals all.
  - Apply and Mission slides advance with arrow / clicker.
  - T/E/A/M rail tracks the active section.
  - Theme alternation reads correctly.
- **`data.js` schema validator** — `tools/validate-team-data.js`. Confirms required fields, array minimum lengths (Teach >= 1 block, Apply >= 1 question, Mission >= 1 question), valid `kind` values per Teach block. Run before each weekly deploy.
- **Optional Playwright screenshot tests** — capture each section at 1080p; diff on changes. Worth adding once we have 2-3 passages built and want to catch design-system regressions.
- **Adversarial review** — once spec and first build are done, run codex CLI as adversarial reader on the final page, viewed in projection-target conditions. Log feedback in `docs/research/2026-04-XX-team-page-codex-review.md`.

## What We Cut from Codex's `romans3_chalk_and_talk`

- Chalkboard skeumorphism (wood frame, slate, rotated chalk-paper labels).
- The "movements grid" section (redundant with Equip's three cards).
- The "leader flow / workshop" cards (instructions to the leader; doesn't earn screen time).
- The standalone "marks filter" UI (sermon-mark labels live inline in the morning handout, not on this page).
- The tabbed session-panel UI (anti-long-scroll; replaced by T/E/A/M rail and per-section adaptation).
- The handout block (attendees brought the morning handout; no need to duplicate).

Most of the existing `data.js` content survives — burden, movements, body-parts list, Greek key terms, sources, application questions, mission questions, sermon outline marks, take-home truth. It is re-shaped into the TEAM data model above.

## Out of Scope

- **Print handout.** No printable view. The morning sermon handout fills that role.
- **Per-attendee URL or device.** The page is a projected single screen. Attendees do not need their own copy.
- **Per-section timer / countdown.** Bryan paces by feel; on-screen times distract the room.
- **Slide counts shown on dividers.** Section dividers say `— TEACH —`, etc., without metadata.
- **Multi-passage app.** Each passage gets its own repo. A future passage index, if needed, is its own project.
- **Authentication, analytics, comments.** Static site, no backend.

## Open Questions

None. All design forks resolved during the brainstorm:

| Decision | Resolved |
|----------|----------|
| Setting | Fellowship hall, projected, 15-40 people |
| Presentation mode | Hybrid long-scroll with focused active section |
| Reuse pattern | Single passage per repo, `data.js` as template seam |
| Teach blocks | Catena · Greek · Courtroom · Body-parts (4) |
| Apply / Mission pacing | Slide-by-slide, one question per screen |
| Equip layout | Three-card panoramic + Big Idea + This Week, blanks revealable |
| Equip heading | Just "Equip" — no subhead |
| Apply / Mission counts | 10 + 10 |
| Body-parts visualization | Color-coded English verse mosaic, "eyes" climax dark |
| Theme alternation | Hero L · Teach L · Equip D · Apply L · Mission D · Send-out L |
| Repo | Rename existing `romans3_chalk_and_talk` to `romans-3-9-20-team` |

---

End of spec.
