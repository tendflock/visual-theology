# Romans 3:9-20 TEAM Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static, projection-friendly single-page TEAM teaching aid for Romans 3:9-20 that follows the muted-editorial discipline of `tendflock/Romans3` and adapts each TEAM letter's interaction to its content.

**Architecture:** Single-page static site, no build step. `index.html` loads `data.js` (single source of truth for content), `app.js` (passage-agnostic renderer + interactions), and the design system in `styles.css` + `theme.css`. The page is a long-scroll with a sticky `T/E/A/M` rail; each section adapts its interaction (Teach editorial scroll-with-focus, Equip panoramic with revealable blanks, Apply/Mission slide-by-slide, Send-out static). Theme alternates light/dark per section.

**Tech Stack:**
- HTML5 + vanilla CSS + vanilla JavaScript (no frameworks, no build).
- Google Fonts: Source Serif 4, Gentium Plus, Frank Ruhl Libre.
- Node.js 20+ for the schema validator (only at edit time, not at runtime).
- Hosting: GitHub Pages (static).
- Reference repo: `tendflock/Romans3` (catena renderer to port).
- Working repo: `tendflock/romans3_chalk_and_talk` (to be renamed and rebuilt).

---

## Spec

Authoritative spec: `docs/superpowers/specs/2026-04-27-romans3-team-page-design.md` (commit `e845168`).

## Project Working Directory

All implementation work happens in `/Volumes/External/romans3_chalk_and_talk/` (this directory will be renamed at the end of the project but not mid-implementation, to avoid breaking the local clone). The plan and spec live in `/Volumes/External/Logos4/docs/`.

## File Structure

By end of implementation:

```
romans3_chalk_and_talk/                 (to be renamed romans-3-9-20-team)
|-- index.html                          page markup; mount points for renderers
|-- data.js                             window.TEAM_DATA — passage content
|-- data.example.js                     blank skeleton for new passages
|-- app.js                              renderer dispatch + interactions
|-- styles.css                          design system: type, palette, layout primitives
|-- theme.css                           per-section light/dark themes
|-- tools/
|   |-- validate-team-data.js           schema validator (Node CLI)
|   |-- validate-team-data.test.js      validator tests
|-- README.md                           how to view the page
|-- STYLE.md                            editorial rules (inherits from Romans3)
|-- TEMPLATE.md                         how to copy the repo for a new passage
```

Codex's existing files (`app.js`, `data.js`, `index.html`, `styles.css`, `assets/`, `README.md`) are wiped during Task 1.

---

## Task 1: Repo prep and HTML scaffold

**Goal:** Wipe codex's chalkboard implementation, scaffold the new directory layout, push a barebones `index.html` with semantic mount points for each section.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/` (whole repo cleanup)
- Create: `/Volumes/External/romans3_chalk_and_talk/index.html`
- Create: `/Volumes/External/romans3_chalk_and_talk/tools/` (empty dir for now)

- [ ] **Step 1: Snapshot codex's version on a tag, then wipe content**

```bash
cd /Volumes/External/romans3_chalk_and_talk
git tag codex-chalkboard-v1
git rm -rf app.js data.js index.html styles.css README.md assets/
mkdir -p tools
git status
```

Expected: `app.js`, `data.js`, `index.html`, `styles.css`, `README.md`, and `assets/` are deleted (staged). The `.git`, `.gitignore`, and `LICENSE` (if present) remain.

- [ ] **Step 2: Create the new index.html scaffold**

Path: `/Volumes/External/romans3_chalk_and_talk/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Romans 3:9-20 · TEAM</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400;1,8..60,500&family=Gentium+Plus:ital,wght@0,400;0,700;1,400&family=Frank+Ruhl+Libre:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="theme.css">
</head>
<body>
  <nav class="rail" aria-label="TEAM section navigation" id="rail"></nav>

  <main id="main">
    <section class="hero" id="hero" data-section="hero" data-theme="light"></section>

    <section class="teach" id="teach" data-section="teach" data-theme="light">
      <div class="section-divider"><span>— TEACH —</span></div>
      <div class="teach-blocks" id="teach-blocks"></div>
    </section>

    <section class="equip" id="equip" data-section="equip" data-theme="dark">
      <div class="section-divider"><span>— EQUIP —</span></div>
      <div class="equip-panel" id="equip-panel"></div>
    </section>

    <section class="apply" id="apply" data-section="apply" data-theme="light">
      <div class="section-divider"><span>— APPLY —</span></div>
      <div class="slides" id="apply-slides"></div>
    </section>

    <section class="mission" id="mission" data-section="mission" data-theme="dark">
      <div class="section-divider"><span>— MISSION —</span></div>
      <div class="slides" id="mission-slides"></div>
    </section>

    <section class="send-out" id="send-out" data-section="send-out" data-theme="light">
      <div class="section-divider"><span>— SEND-OUT —</span></div>
      <div id="send-out-panel"></div>
    </section>
  </main>

  <div class="kbd-help" id="kbd-help" hidden></div>

  <script src="data.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Verify the scaffold loads**

Start a local static server with `python3 -m http.server 5500`, then open `http://localhost:5500/` in a browser. Expected: page returns HTTP 200, renders blank (no CSS/JS yet), no console errors.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: wipe codex chalkboard, scaffold TEAM index.html"
```

---

## Task 2: Schema validator (TDD)

**Goal:** Write a Node CLI that validates `data.js` against the TEAM schema. Tests first, then implementation.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/tools/validate-team-data.test.js`
- Create: `/Volumes/External/romans3_chalk_and_talk/tools/validate-team-data.js`

- [ ] **Step 1: Write the failing test file**

Path: `tools/validate-team-data.test.js`

```javascript
// Run with: node tools/validate-team-data.test.js
// No external test runner — uses Node's built-in `assert`.

const assert = require("node:assert/strict");
const { validate } = require("./validate-team-data.js");

let failed = 0;
let passed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ok ${name}`);
    passed++;
  } catch (err) {
    console.log(`  FAIL ${name}`);
    console.log(`    ${err.message}`);
    failed++;
  }
}

function makeValidData() {
  return {
    meta: {
      passage: "Romans 3:9-20",
      burden: "B",
      takeHome: "T",
      sermon: { title: "S", date: "2026-04-26" }
    },
    teach: [
      { kind: "catena", title: "T", sources: [{ id: "ps14", label: "Ps 14", hue: 25 }],
        phrases: [{ id: "p1", text: "x", sourceId: "ps14" }] }
    ],
    equip: {
      bigIdea: { template: "{a}", blanks: [{ key: "a", answer: "x" }] },
      movements: [
        { roman: "I", nameTemplate: "The {a}", nameBlank: { answer: "Charge" },
          ref: "v.1", summary: "s",
          christ: { template: "{a}", blanks: [{ key: "a", answer: "x" }] } }
      ],
      thisWeek: { template: "{a}", blanks: [{ key: "a", answer: "x" }] }
    },
    apply: [{ question: "q", tags: [] }],
    mission: [{ question: "q", tags: ["evangelism"] }],
    sendOut: { takeHome: "t" }
  };
}

console.log("validate-team-data");

test("accepts valid data", () => {
  const result = validate(makeValidData());
  assert.equal(result.ok, true, JSON.stringify(result.errors));
});

test("rejects missing meta", () => {
  const data = makeValidData();
  delete data.meta;
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors[0], /meta/);
});

test("rejects empty teach array", () => {
  const data = makeValidData();
  data.teach = [];
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /teach/);
});

test("rejects unknown teach kind", () => {
  const data = makeValidData();
  data.teach[0].kind = "imaginary";
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /kind/);
});

test("rejects empty apply array", () => {
  const data = makeValidData();
  data.apply = [];
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /apply/);
});

test("rejects mission question without tags", () => {
  const data = makeValidData();
  data.mission[0].tags = [];
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /mission.*tag/);
});

test("rejects equip movement without blanks", () => {
  const data = makeValidData();
  data.equip.movements[0].christ.blanks = [];
  const result = validate(data);
  assert.equal(result.ok, false);
});

test("rejects template with blank key not declared", () => {
  const data = makeValidData();
  data.equip.bigIdea.template = "{a} {b}";
  const result = validate(data);
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /b/);
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
```

- [ ] **Step 2: Run the test file to confirm it fails**

Run: `node tools/validate-team-data.test.js`
Expected: error like `Cannot find module './validate-team-data.js'` (the implementation does not exist yet).

- [ ] **Step 3: Implement validate-team-data.js**

Path: `tools/validate-team-data.js`

```javascript
"use strict";

const KNOWN_TEACH_KINDS = new Set([
  "catena", "greek-terms", "courtroom-chain", "body-parts",
  "hebrew-terms", "phrase-mosaic", "historical-context", "theological-categories"
]);

const KNOWN_MISSION_TAGS = new Set(["evangelism", "apologetics", "home", "abroad"]);

function validateBlankTemplate(label, template, blanks, errors) {
  if (typeof template !== "string") {
    errors.push(`${label}: template must be a string`);
    return;
  }
  const declared = new Set((blanks || []).map(b => b.key));
  const referenced = new Set();
  const re = /\{([a-z])\}/g;
  let m;
  while ((m = re.exec(template))) referenced.add(m[1]);
  for (const k of referenced) {
    if (!declared.has(k)) {
      errors.push(`${label}: template references {${k}} but no blank with key "${k}" is declared`);
    }
  }
  for (const b of blanks || []) {
    if (typeof b.key !== "string" || typeof b.answer !== "string") {
      errors.push(`${label}: blank must have string key and answer`);
    }
  }
  if (!Array.isArray(blanks) || blanks.length === 0) {
    errors.push(`${label}: must declare at least one blank`);
  }
}

function validate(data) {
  const errors = [];

  if (!data || typeof data !== "object") {
    return { ok: false, errors: ["data is not an object"] };
  }

  if (!data.meta || typeof data.meta !== "object") {
    errors.push("meta is required");
  } else {
    for (const k of ["passage", "burden", "takeHome"]) {
      if (typeof data.meta[k] !== "string" || !data.meta[k]) {
        errors.push(`meta.${k} must be a non-empty string`);
      }
    }
  }

  if (!Array.isArray(data.teach) || data.teach.length === 0) {
    errors.push("teach must be a non-empty array");
  } else {
    data.teach.forEach((block, i) => {
      if (!KNOWN_TEACH_KINDS.has(block.kind)) {
        errors.push(`teach[${i}].kind "${block.kind}" is not a known kind`);
      }
      if (typeof block.title !== "string" || !block.title) {
        errors.push(`teach[${i}].title is required`);
      }
    });
  }

  if (!data.equip || typeof data.equip !== "object") {
    errors.push("equip is required");
  } else {
    if (data.equip.bigIdea) {
      validateBlankTemplate("equip.bigIdea", data.equip.bigIdea.template,
        data.equip.bigIdea.blanks, errors);
    } else {
      errors.push("equip.bigIdea is required");
    }
    if (!Array.isArray(data.equip.movements) || data.equip.movements.length === 0) {
      errors.push("equip.movements must be a non-empty array");
    } else {
      data.equip.movements.forEach((mv, i) => {
        if (typeof mv.roman !== "string") errors.push(`equip.movements[${i}].roman required`);
        if (!mv.christ) errors.push(`equip.movements[${i}].christ required`);
        else validateBlankTemplate(`equip.movements[${i}].christ`, mv.christ.template,
          mv.christ.blanks, errors);
      });
    }
    if (data.equip.thisWeek) {
      validateBlankTemplate("equip.thisWeek", data.equip.thisWeek.template,
        data.equip.thisWeek.blanks, errors);
    } else {
      errors.push("equip.thisWeek is required");
    }
  }

  if (!Array.isArray(data.apply) || data.apply.length === 0) {
    errors.push("apply must be a non-empty array");
  } else {
    data.apply.forEach((q, i) => {
      if (typeof q.question !== "string" || !q.question) {
        errors.push(`apply[${i}].question required`);
      }
      if (!Array.isArray(q.tags)) errors.push(`apply[${i}].tags required (may be empty)`);
    });
  }

  if (!Array.isArray(data.mission) || data.mission.length === 0) {
    errors.push("mission must be a non-empty array");
  } else {
    data.mission.forEach((q, i) => {
      if (typeof q.question !== "string" || !q.question) {
        errors.push(`mission[${i}].question required`);
      }
      if (!Array.isArray(q.tags) || q.tags.length === 0) {
        errors.push(`mission[${i}] must have at least one tag`);
      } else {
        q.tags.forEach(t => {
          if (!KNOWN_MISSION_TAGS.has(t)) {
            errors.push(`mission[${i}].tag "${t}" is not a known mission tag`);
          }
        });
      }
    });
  }

  if (!data.sendOut || typeof data.sendOut.takeHome !== "string") {
    errors.push("sendOut.takeHome required");
  }

  return { ok: errors.length === 0, errors };
}

if (require.main === module) {
  const path = require("node:path");
  const fs = require("node:fs");
  const file = process.argv[2] || path.join(__dirname, "..", "data.js");
  if (!fs.existsSync(file)) {
    console.error(`File not found: ${file}`);
    process.exit(2);
  }
  const code = fs.readFileSync(file, "utf8");
  const ctx = { window: {} };
  // eslint-disable-next-line no-new-func
  new Function("window", code)(ctx.window);
  const data = ctx.window.TEAM_DATA;
  if (!data) {
    console.error(`No window.TEAM_DATA found in ${file}`);
    process.exit(2);
  }
  const { ok, errors } = validate(data);
  if (ok) {
    console.log(`ok ${file} — valid TEAM data`);
    process.exit(0);
  } else {
    console.error(`FAIL ${file} — ${errors.length} error(s):`);
    errors.forEach(e => console.error(`  - ${e}`));
    process.exit(1);
  }
}

module.exports = { validate, KNOWN_TEACH_KINDS, KNOWN_MISSION_TAGS };
```

Note: This script uses `new Function(code)` to evaluate `data.js` in a sandboxed `window` object. The input is our own repo's `data.js` (not user input), so injection is not a concern. If you prefer a stricter loader, swap to a regex extract of the assigned object literal — but that breaks if the data file ever uses computed values.

- [ ] **Step 4: Run tests, expect green**

Run: `node tools/validate-team-data.test.js`
Expected: `8 passed, 0 failed`, exit status `0`.

- [ ] **Step 5: Commit**

```bash
git add tools/
git commit -m "feat(validator): TEAM data schema validator with tests"
```

---

## Task 3: Fill data.js with Romans 3:9-20 content

**Goal:** Populate `window.TEAM_DATA` with the actual Romans 3:9-20 content from the spec. Validator must pass.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/data.js`

- [ ] **Step 1: Write data.js**

Path: `data.js`

```javascript
window.TEAM_DATA = {
  meta: {
    passage: "Romans 3:9-20",
    burden: "Stop trying to justify yourself and look to Christ for righteousness.",
    takeHome: "Accept the guilty verdict of sinner and flee to Christ, the only righteous one.",
    sermon: { title: "Stop Trying to Justify Yourself and Look to Christ for Righteousness", date: "2026-04-26" }
  },

  teach: [
    {
      kind: "catena",
      title: "Paul's six sources flowing into Romans 3:10-18",
      blurb: "Six Old Testament sources, woven phrase by phrase. Click any source to see how it lands in the verse below.",
      sources: [
        { id: "ps14",  label: "Psalm 14 / 53", ref: "Rom 3:10-12",  hue: 25  },
        { id: "ps5",   label: "Psalm 5",       ref: "Rom 3:13a-b",  hue: 200 },
        { id: "ps140", label: "Psalm 140",     ref: "Rom 3:13c",    hue: 290 },
        { id: "ps10",  label: "Psalm 10",      ref: "Rom 3:14",     hue: 75  },
        { id: "isa59", label: "Isaiah 59",     ref: "Rom 3:15-17",  hue: 340 },
        { id: "ps36",  label: "Psalm 36",      ref: "Rom 3:18",     hue: 158 }
      ],
      phrases: [
        { id: "p1",  ref: "3:10",    text: "There is no one righteous, not even one",                                                  sourceId: "ps14"  },
        { id: "p2",  ref: "3:11",    text: "There is no one who understands; no one seeks God",                                        sourceId: "ps14"  },
        { id: "p3",  ref: "3:12a",   text: "All have turned aside; together become worthless",                                         sourceId: "ps14"  },
        { id: "p4",  ref: "3:12b",   text: "There is no one who does good, not even one",                                              sourceId: "ps14"  },
        { id: "p5",  ref: "3:13a",   text: "Their throat is an opened grave",                                                          sourceId: "ps5"   },
        { id: "p6",  ref: "3:13b",   text: "Their tongues practice deceit",                                                            sourceId: "ps5"   },
        { id: "p7",  ref: "3:13c",   text: "The venom of vipers is under their lips",                                                  sourceId: "ps140" },
        { id: "p8",  ref: "3:14",    text: "Their mouth is full of cursing and bitterness",                                            sourceId: "ps10"  },
        { id: "p9",  ref: "3:15",    text: "Their feet are swift to spill blood",                                                      sourceId: "isa59" },
        { id: "p10", ref: "3:16-17", text: "Ruin and misery mark their paths; the road of peace they have not known",                  sourceId: "isa59" },
        { id: "p11", ref: "3:18",    text: "There is no fear of God before their eyes",                                                sourceId: "ps36"  }
      ]
    },

    {
      kind: "greek-terms",
      title: "Key terms — what the words carry",
      blurb: "Click any term to expand its gloss and what it does in Paul's argument.",
      terms: [
        { greek: "ὑφ' ἁμαρτίαν",     gloss: "under sin",            ref: "3:9",
          note: "Slavery, power, guilt, condemnation",
          cue: "Sin is not only acts committed; it is a realm and ruler apart from Christ." },
        { greek: "οὐκ ἔστιν",        gloss: "there is not",         ref: "3:10-12",
          note: "Repeated negation — hammering the no-exceptions point",
          cue: "Let the repetition do its work: Paul removes every proposed exception." },
        { greek: "οὐδὲ εἷς",         gloss: "not even one",         ref: "3:10, 12",
          note: "Absolute universality",
          cue: "God's-eye verdict on natural humanity, not a comparison between better and worse sinners." },
        { greek: "δίκαιος",          gloss: "righteous",            ref: "3:10",
          note: "The status nobody possesses in Adam",
          cue: "Romans 3:21-26 will answer the lack named here." },
        { greek: "ὑπόδικος",         gloss: "answerable to God",    ref: "3:19",
          note: "Liable before the judge",
          cue: "The courtroom reaches silence before it reaches relief." },
        { greek: "δικαιωθήσεται",    gloss: "will be justified",    ref: "3:20",
          note: "Courtroom / legal declaration",
          cue: "Justification is the category works cannot secure and Christ will supply." },
        { greek: "ἐξ ἔργων νόμου",   gloss: "by works of law",      ref: "3:20",
          note: "No human obedience establishes righteous standing",
          cue: "The law can prosecute sinners; it cannot become their savior." },
        { greek: "ἐπίγνωσις ἁμαρτίας", gloss: "knowledge of sin",   ref: "3:20",
          note: "The law reveals and names sin",
          cue: "The law gives diagnosis, not deliverance." }
      ]
    },

    {
      kind: "courtroom-chain",
      title: "God as righteous Judge — the frame from Romans 2-3",
      blurb: "The courtroom language builds across four moments. Click each node to advance the chain.",
      nodes: [
        { ref: "2:2-6",   label: "judges truly",  note: "God's judgment is according to truth, not partiality." },
        { ref: "3:4",     label: "God true",      note: "Let God be true though every human is false." },
        { ref: "3:6",     label: "judges world",  note: "How otherwise could God judge the world? The verdict is His." },
        { ref: "3:19-20", label: "verdict",       note: "Every mouth stopped. The whole world held accountable. No flesh justified by law.", terminal: true }
      ]
    },

    {
      kind: "body-parts",
      title: "Throat · tongue · lips · mouth · feet · paths · eyes",
      blurb: "The indictment runs through the body, climaxing at the eyes — no fear of God. Click any phrase to make it active.",
      phrases: [
        { part: "THROAT", english: "Their throat is an opened grave",                                       image: "grave",          ref: "3:13a",   hue: 32  },
        { part: "TONGUE", english: "Their tongues practice deceit",                                         image: "deceit",         ref: "3:13b",   hue: 200 },
        { part: "LIPS",   english: "The venom of vipers is under their lips",                               image: "poison",         ref: "3:13c",   hue: 290 },
        { part: "MOUTH",  english: "Their mouth is full of cursing and bitterness",                         image: "cursing",        ref: "3:14",    hue: 78  },
        { part: "FEET",   english: "Their feet are swift to spill blood",                                   image: "violence",       ref: "3:15",    hue: 344 },
        { part: "PATHS",  english: "Ruin and misery mark their paths; the road of peace they have not known", image: "ruin",         ref: "3:16-17", hue: 158 },
        { part: "EYES",   english: "There is no fear of God before their eyes",                             image: "no fear of God", ref: "3:18",    climax: true }
      ]
    }
  ],

  equip: {
    bigIdea: {
      template: "Accept the guilty {a} of sinner and {b} to Christ, the only righteous one.",
      blanks: [
        { key: "a", answer: "verdict" },
        { key: "b", answer: "flee" }
      ]
    },
    movements: [
      {
        roman: "I",
        nameTemplate: "The {a}",
        nameBlank: { answer: "Charge" },
        ref: "vv. 9-12",
        summary: "Universal condemnation",
        christ: {
          template: "Christ is the only {a}",
          blanks: [{ key: "a", answer: "exception" }]
        }
      },
      {
        roman: "II",
        nameTemplate: "The {a}",
        nameBlank: { answer: "Proof" },
        ref: "vv. 13-18",
        summary: "Evidence of depravity",
        christ: {
          template: "Christ was the only one {a} yet without sin",
          blanks: [{ key: "a", answer: "tested" }]
        }
      },
      {
        roman: "III",
        nameTemplate: "The {a}",
        nameBlank: { answer: "Verdict" },
        ref: "vv. 19-20",
        summary: "No self-justification possible",
        christ: {
          template: "Christ is the only {a}",
          blanks: [{ key: "a", answer: "answer" }]
        }
      }
    ],
    thisWeek: {
      template: "When you sin, don't {a} yourself — {b} to Christ for righteousness.",
      blanks: [
        { key: "a", answer: "justify" },
        { key: "b", answer: "flee" }
      ]
    }
  },

  apply: [
    { question: "Where do you most quickly defend yourself: home, work, church, or private conscience?",                tags: ["self-justification"] },
    { question: "What words do you use to soften sin — stress, personality, weakness, misunderstanding, trauma, tiredness, or someone else's fault?", tags: ["confession"] },
    { question: "What would confession sound like this week if Christ's righteousness were enough for you?",            tags: ["confession", "christ-thread"] },
    { question: "When have your words acted like poison rather than grace — and who felt it?",                          tags: ["words", "relationships"] },
    { question: "How would your parenting, marriage, or friendships change if you were free to say, \"I was wrong\"?", tags: ["family", "relationships"] },
    { question: "What is the difference between being crushed by guilt and accepting the verdict so you can flee to Christ?", tags: ["conscience", "christ-thread"] },
    { question: "Where does comparison with other people's sin help you avoid honest accounting before God?",           tags: ["self-justification", "conscience"] },
    { question: "Which body part — throat, tongue, lips, mouth, feet, paths, eyes — most exposes you, and why?",        tags: ["confession"] },
    { question: "When your heart condemns you this week, what specific sentence will you say to remember Christ's righteousness?", tags: ["christ-thread", "discipleship"] },
    { question: "What practice could help you confess quickly rather than defend slowly — daily prayer, end-of-day examen, accountability conversation?", tags: ["discipleship"] }
  ],

  mission: [
    { question: "How can Romans 3 help us evangelize without sounding morally superior?",                               tags: ["evangelism"] },
    { question: "What self-justification stories are common in our community that the gospel exposes?",                  tags: ["apologetics", "home"] },
    { question: "How would you ask Ray-Comfort-style diagnostic questions with gentleness rather than performance?",      tags: ["evangelism"] },
    { question: "Why does universal guilt create universal opportunity for mission?",                                     tags: ["evangelism", "abroad"] },
    { question: "How do guilt, shame, honor, comparison, and achievement function as false defenses in different cultures?", tags: ["abroad", "apologetics"] },
    { question: "What would it sound like to say, \"I need the same righteousness I am offering to you in Christ\"?",     tags: ["evangelism"] },
    { question: "When someone says, \"I'm a good person,\" how does Romans 3 respond without crushing them prematurely?", tags: ["apologetics"] },
    { question: "What does evangelism look like in your own home — to a spouse, child, neighbor, coworker?",              tags: ["home"] },
    { question: "How does the catena (six OT voices) model honoring older Scripture when we proclaim Christ?",            tags: ["apologetics"] },
    { question: "If our mission abroad rests on universal guilt and universal need, how does that shape what we send and whom we partner with?", tags: ["abroad"] }
  ],

  sendOut: {
    takeHome: "Accept the guilty verdict of sinner and flee to Christ, the only righteous one.",
    deeperLink: { url: "https://tendflock.github.io/Romans3", label: "Romans 3 textual history" }
  }
};
```

- [ ] **Step 2: Run validator on the data**

Run: `node tools/validate-team-data.js data.js`
Expected: `ok data.js — valid TEAM data`, exit `0`. If it fails, read the listed errors and fix the `data.js` content.

- [ ] **Step 3: Commit**

```bash
git add data.js
git commit -m "feat(content): Romans 3:9-20 TEAM data"
```

---

## Task 4: styles.css — design system base

**Goal:** Type stack, oklch palette tokens, layout primitives. No section-specific styles yet.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Write styles.css**

Path: `styles.css`

```css
/* TEAM page — design system base
 * Inherits the editorial discipline of tendflock/Romans3.
 */

:root {
  --font-prose: "Source Serif 4", Georgia, "Times New Roman", serif;
  --font-greek: "Gentium Plus", "Source Serif 4", Georgia, serif;
  --font-hebrew: "Frank Ruhl Libre", "Source Serif 4", Georgia, serif;
  --font-mono: "SF Mono", Menlo, Consolas, monospace;

  --bg-page: oklch(0.95 0.02 80);
  --bg-card: #fff;
  --ink-body: #222;
  --ink-muted: #666;
  --ink-faint: #888;
  --border-card: oklch(0.85 0.03 80);
  --border-soft: oklch(0.90 0.02 80);
  --accent: oklch(0.50 0.13 25);
  --accent-on: #fff;
  --highlight-bg: oklch(0.98 0.02 80);

  --dark-bg-page: #1a1a1a;
  --dark-ink-body: #f5f0e8;
  --dark-ink-muted: #bbb;
  --dark-eyebrow: #d8c098;
  --dark-border: #333;

  --rail-width: 80px;
  --content-max: 920px;
  --content-pad-x: 2rem;
  --section-pad-y: 4rem;

  --fs-eyebrow: 0.78rem;
  --fs-body: 1.05rem;
  --fs-title: 2.2rem;
  --fs-subtitle: 1.4rem;
  --fs-question: 2rem;

  --t-fast: 180ms;
  --t-slow: 420ms;
  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }

body {
  font-family: var(--font-prose);
  font-size: var(--fs-body);
  line-height: 1.55;
  color: var(--ink-body);
  background: var(--bg-page);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

main { margin-left: var(--rail-width); }

@media (max-width: 768px) {
  main { margin-left: 0; }
}

section {
  padding: var(--section-pad-y) var(--content-pad-x);
  scroll-margin-top: 1rem;
}
section > * { max-width: var(--content-max); margin-left: auto; margin-right: auto; }

.section-divider {
  text-align: center;
  font-size: var(--fs-eyebrow);
  letter-spacing: 0.22em;
  color: var(--accent);
  font-weight: 700;
  margin: 0 0 2.5rem 0;
}

.eyebrow {
  font-size: var(--fs-eyebrow);
  letter-spacing: 0.18em;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  margin: 0 0 0.6rem 0;
}
.title {
  font-size: var(--fs-title);
  font-weight: 600;
  color: var(--ink-body);
  margin: 0 0 1rem 0;
  line-height: 1.18;
  letter-spacing: -0.01em;
}
.subtitle {
  font-size: var(--fs-subtitle);
  font-style: italic;
  color: var(--ink-body);
  margin: 0 0 1rem 0;
  line-height: 1.35;
}
.muted { color: var(--ink-muted); font-size: 0.92rem; }

.greek { font-family: var(--font-greek); }
.hebrew { font-family: var(--font-hebrew); direction: rtl; }
.italic { font-style: italic; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 1.4rem 1.6rem;
  border-radius: 3px;
}

.reveal { opacity: 0; transform: translateY(8px); transition: opacity var(--t-slow) var(--ease-out), transform var(--t-slow) var(--ease-out); }
.reveal.in { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  .reveal { opacity: 1; transform: none; transition: none; }
}

.rail {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--rail-width);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  background: var(--bg-page);
  border-right: 1px solid var(--border-soft);
  z-index: 10;
}
.rail-letter {
  width: 46px; height: 46px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-prose);
  font-weight: 600; font-size: 1rem;
  background: var(--bg-card);
  color: var(--ink-muted);
  border: 1px solid var(--border-card);
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}
.rail-letter[data-state="active"] {
  background: var(--ink-body);
  color: var(--dark-eyebrow);
  border-color: var(--ink-body);
}
.rail-letter[data-state="passed"] {
  background: oklch(0.92 0.03 80);
  color: var(--ink-faint);
}
@media (max-width: 768px) {
  .rail {
    position: sticky; top: 0; left: 0; right: 0;
    width: 100%; height: 56px;
    flex-direction: row; gap: 0.4rem;
    border-right: 0; border-bottom: 1px solid var(--border-soft);
  }
  .rail-letter { width: 36px; height: 36px; font-size: 0.85rem; }
}

.hero { padding-top: 6rem; padding-bottom: 6rem; }
.hero .title { font-size: 3rem; }
.hero .subtitle { font-size: 1.6rem; }

.blank {
  display: inline-block;
  min-width: 4.5rem;
  padding: 0 0.5rem;
  border-bottom: 2px solid currentColor;
  cursor: pointer;
  color: var(--ink-faint);
  text-align: center;
  font-style: normal;
}
.blank.filled {
  color: var(--accent);
  font-weight: 600;
  border-bottom-color: var(--accent);
}

.kbd-help {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.kbd-help[hidden] { display: none; }
.kbd-help-card {
  background: var(--bg-card);
  padding: 2rem 2.4rem;
  border-radius: 4px;
  max-width: 480px;
}
.kbd-help kbd {
  background: var(--ink-body);
  color: var(--dark-eyebrow);
  padding: 2px 8px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.85em;
}

.slide {
  min-height: 70vh;
  display: flex; flex-direction: column; justify-content: center;
  padding: 4rem var(--content-pad-x);
  scroll-snap-align: start;
}
.slides { scroll-snap-type: y mandatory; }
.slide .question {
  font-family: var(--font-prose);
  font-size: var(--fs-question);
  font-style: italic;
  line-height: 1.3;
  font-weight: 400;
  margin: 0 0 1.5rem 0;
  max-width: 760px;
}
.slide .tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.slide .tag {
  font-size: 0.78rem;
  padding: 0.3rem 0.7rem;
  border-radius: 3px;
  letter-spacing: 0.05em;
}
.slide .pagination {
  position: absolute; bottom: 2rem; right: 2rem;
  display: flex; gap: 0.4rem;
}
.slide .pagination .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ink-faint);
  opacity: 0.5;
}
.slide .pagination .dot.active { background: var(--accent); opacity: 1; }
```

- [ ] **Step 2: Verify in a browser**

Start a local server (`python3 -m http.server 5500`). Open `http://localhost:5500/`. Body text is in Source Serif 4 (loaded from Google Fonts). Section dividers render in muted dark rust. The rail container is visible on the left (empty until Task 7). Inspect in dev tools — confirm `var(--font-prose)` resolves and `body { background: oklch(...) }` applies. No console errors.

- [ ] **Step 3: Commit**

```bash
git add styles.css
git commit -m "feat(styles): design system base — type, palette, layout"
```

---

## Task 5: theme.css — light/dark alternation

**Goal:** Each section's `data-theme` attribute swaps palette. Verify alternation visually.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/theme.css`

- [ ] **Step 1: Write theme.css**

Path: `theme.css`

```css
/* Per-section themes. Hero/Teach/Apply/Send-out are light;
 * Equip/Mission are dark. */

section[data-theme="dark"] {
  background: var(--dark-bg-page);
  color: var(--dark-ink-body);
  --bg-card: oklch(0.18 0.01 80);
  --border-card: var(--dark-border);
  --ink-body: var(--dark-ink-body);
  --ink-muted: var(--dark-ink-muted);
  --ink-faint: oklch(0.55 0.02 80);
  --accent: var(--dark-eyebrow);
  --highlight-bg: oklch(0.22 0.02 80);
}

section[data-theme="dark"] .title,
section[data-theme="dark"] .subtitle {
  color: var(--dark-ink-body);
}

section[data-theme="dark"] .section-divider {
  color: var(--dark-eyebrow);
}

section[data-theme="dark"] .blank {
  color: oklch(0.45 0.02 80);
  border-bottom-color: oklch(0.45 0.02 80);
}
section[data-theme="dark"] .blank.filled {
  color: var(--dark-eyebrow);
  border-bottom-color: var(--dark-eyebrow);
}
```

- [ ] **Step 2: Verify visually**

Reload the page. Hero / Teach / Apply / Send-out sections are cream; Equip and Mission section dividers sit on dark `#1a1a1a` backgrounds. Section-divider colors flip from rust on light to gold-cream on dark.

- [ ] **Step 3: Commit**

```bash
git add theme.css
git commit -m "feat(theme): light/dark alternation per section"
```

---

## Task 6: app.js scaffold + render hero

**Goal:** Boot script, helpers, render the hero section from `data.meta`. Stubs for later tasks.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/app.js`

- [ ] **Step 1: Write app.js scaffold**

Path: `app.js`

```javascript
(function () {
  "use strict";

  const D = window.TEAM_DATA;
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  const state = {
    activeSection: "hero",
    revealedBlanks: new Set()
  };

  // Helpers — these are used by Equip in Task 12
  function renderBlankTemplate(template, blanksByKey, scopeId) {
    return template.replace(/\{([a-z])\}/g, (_, key) => {
      const blank = blanksByKey[key];
      if (!blank) return `{${key}}`;
      const id = `${scopeId}-${key}`;
      return `<button type="button" class="blank" data-blank-id="${id}" data-answer="${blank.answer}">_______</button>`;
    });
  }

  function blanksToMap(blanks) {
    const m = {};
    (blanks || []).forEach(b => { m[b.key] = b; });
    return m;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[m]));
  }

  // ── HERO ─────────────────────────────────────────────────────────────
  function renderHero() {
    const el = $("#hero");
    if (!el || !D || !D.meta) return;
    const m = D.meta;
    el.innerHTML = `
      <div class="hero-inner reveal">
        <div class="eyebrow">${m.passage} · TEAM</div>
        <h1 class="title">${m.passage}</h1>
        <p class="subtitle">${m.burden}</p>
        <p class="muted">${m.takeHome}</p>
        <div class="roadmap">
          <span>Teach</span><span>Equip</span><span>Apply</span><span>Mission</span>
        </div>
      </div>
    `;
  }

  // Renderer dispatch — populated in later tasks
  const teachRenderers = {};

  function renderTeach() {
    const mount = $("#teach-blocks");
    if (!mount || !D || !D.teach) return;
    mount.innerHTML = "";
    D.teach.forEach((block, i) => {
      const renderer = teachRenderers[block.kind];
      if (!renderer) {
        console.warn(`No renderer for teach kind "${block.kind}"`);
        return;
      }
      const blockEl = document.createElement("article");
      blockEl.className = `teach-block teach-block--${block.kind} reveal`;
      blockEl.dataset.kind = block.kind;
      blockEl.dataset.index = String(i);
      renderer(blockEl, block);
      mount.appendChild(blockEl);
    });
  }

  function fillBlank(btn) {
    if (btn.classList.contains("filled")) return;
    btn.textContent = btn.dataset.answer;
    btn.classList.add("filled");
    state.revealedBlanks.add(btn.dataset.blankId);
  }

  function renderEquip() { /* Task 12 */ }
  function renderApply() { /* Task 13 */ }
  function renderMission() { /* Task 13 */ }
  function renderSendOut() { /* Task 14 */ }
  function renderRail() { /* Task 7 */ }
  function setupRailObserver() { /* Task 7 */ }
  function setupKeyboard() { /* Task 15 */ }

  function setupReveal() {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("in"); }),
      { rootMargin: "0px 0px -10% 0px", threshold: 0.05 }
    );
    $$(".reveal").forEach(el => obs.observe(el));
  }

  function init() {
    if (!D) {
      console.error("window.TEAM_DATA is missing");
      return;
    }
    renderHero();
    renderTeach();
    renderEquip();
    renderApply();
    renderMission();
    renderSendOut();
    renderRail();
    setupRailObserver();
    setupKeyboard();
    setupReveal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose for debugging
  window.__TEAM = { D, state, $, $$, fillBlank };
})();
```

- [ ] **Step 2: Add hero-specific styles**

Append to `styles.css`:

```css
.hero-inner { text-align: left; }
.hero-inner .roadmap {
  display: inline-flex; gap: 1.4rem;
  font-size: 0.92rem;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
  margin-top: 2rem;
  padding: 0.8rem 1.2rem;
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: 3px;
}
.hero-inner .roadmap span:not(:last-child)::after { content: "·"; margin-left: 1.4rem; color: var(--ink-faint); }
```

- [ ] **Step 3: Verify in browser**

Reload. Hero shows: eyebrow `Romans 3:9-20 · TEAM`, h1 `Romans 3:9-20`, subtitle italic burden, muted take-home, roadmap chip with `Teach · Equip · Apply · Mission`. Console shows warnings about missing teach renderers — that is expected; renderers are added in Tasks 8-11.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(app): scaffold + render hero"
```

---

## Task 7: Render rail + active-section tracking

**Goal:** Sticky T/E/A/M rail with five circles (plus Hero/Send-out dots). IntersectionObserver tracks which section is active. Click a letter to jump-scroll.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`

- [ ] **Step 1: Replace the rail stubs**

In `app.js`, replace `function renderRail() { /* Task 7 */ }` and `function setupRailObserver() { /* Task 7 */ }` with:

```javascript
  function renderRail() {
    const rail = $("#rail");
    if (!rail) return;
    const stops = [
      { id: "hero",      letter: "·" },
      { id: "teach",     letter: "T" },
      { id: "equip",     letter: "E" },
      { id: "apply",     letter: "A" },
      { id: "mission",   letter: "M" },
      { id: "send-out",  letter: "·" }
    ];
    rail.innerHTML = stops.map(s =>
      `<button class="rail-letter" data-target="${s.id}" data-state="upcoming"
               aria-label="Jump to ${s.id}">${s.letter}</button>`
    ).join("");
    rail.addEventListener("click", (e) => {
      const btn = e.target.closest(".rail-letter");
      if (!btn) return;
      const target = document.getElementById(btn.dataset.target);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function setupRailObserver() {
    const stops = ["hero", "teach", "equip", "apply", "mission", "send-out"];
    const sections = stops.map(id => document.getElementById(id)).filter(Boolean);
    if (!sections.length) return;

    let active = "hero";
    function paint() {
      $$(".rail-letter").forEach(btn => {
        const t = btn.dataset.target;
        const tIdx = stops.indexOf(t);
        const aIdx = stops.indexOf(active);
        if (tIdx < aIdx) btn.dataset.state = "passed";
        else if (tIdx === aIdx) btn.dataset.state = "active";
        else btn.dataset.state = "upcoming";
      });
    }
    paint();

    const obs = new IntersectionObserver((entries) => {
      const visible = entries.filter(e => e.isIntersecting);
      if (visible.length) {
        visible.sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        active = visible[0].target.id;
        state.activeSection = active;
        paint();
      }
    }, { rootMargin: "-30% 0px -50% 0px", threshold: [0, 0.25, 0.5, 0.75] });

    sections.forEach(s => obs.observe(s));
  }
```

- [ ] **Step 2: Verify in browser**

Reload. The rail on the left shows six circles (·, T, E, A, M, ·). The one matching the current scroll position is dark-filled. Scrolling updates the active circle. Clicking any letter jump-scrolls to that section.

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "feat(rail): T/E/A/M rail with active-section tracking"
```

---

## Task 8: Teach renderer — catena

**Goal:** Catena renderer + interactions. Source labels (color chips), curve graphic (SVG), verse mosaic below. Clicking a source highlights its curve and matching phrases.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js` (add `teachRenderers.catena`)
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Add catena renderer**

In `app.js`, replace `const teachRenderers = {};` with:

```javascript
  const teachRenderers = {
    catena(el, block) {
      const sources = block.sources;
      const phrases = block.phrases;

      const head = document.createElement("div");
      head.className = "teach-head";
      head.innerHTML = `
        <div class="eyebrow">CATENA</div>
        <h2 class="title">${block.title}</h2>
        ${block.blurb ? `<p class="muted">${block.blurb}</p>` : ""}
      `;
      el.appendChild(head);

      const chips = document.createElement("div");
      chips.className = "catena-chips";
      chips.innerHTML = sources.map(s => `
        <button class="catena-chip" data-src="${s.id}"
                style="background: oklch(0.50 0.13 ${s.hue}); color: #fff;">
          <span class="chip-label">${s.label}</span>
          <span class="chip-ref">${s.ref}</span>
        </button>
      `).join("");
      el.appendChild(chips);

      const svgWrap = document.createElement("div");
      svgWrap.className = "catena-svg-wrap";
      svgWrap.innerHTML = `
        <svg class="catena-svg" viewBox="0 0 600 140" preserveAspectRatio="none">
          ${sources.map((s, i) => {
            const x = 60 + i * (480 / (sources.length - 1));
            return `<path class="catena-curve" data-src="${s.id}"
              d="M ${x} 10 Q ${x} 80 ${(x + 300) / 2} 130"
              stroke="oklch(0.50 0.13 ${s.hue})" fill="none" stroke-width="2.5" opacity="0.35"/>`;
          }).join("")}
          <line x1="40" y1="130" x2="560" y2="130" stroke="#222" stroke-width="2"/>
        </svg>
      `;
      el.appendChild(svgWrap);

      const verses = document.createElement("ol");
      verses.className = "catena-verses";
      verses.innerHTML = phrases.map(p => {
        const src = sources.find(s => s.id === p.sourceId);
        return `
          <li class="catena-line" data-src="${p.sourceId}"
              style="--src-bg: oklch(0.92 0.04 ${src ? src.hue : 0});">
            <span class="v">${p.ref}</span>
            <span class="t">${p.text}</span>
          </li>
        `;
      }).join("");
      el.appendChild(verses);

      let activeSrc = null;
      function setActive(srcId) {
        activeSrc = srcId;
        $$(".catena-chip", el).forEach(c => c.dataset.active = (c.dataset.src === srcId) ? "true" : "false");
        $$(".catena-curve", el).forEach(c => c.style.opacity = (c.dataset.src === srcId) ? "1" : "0.15");
        $$(".catena-line", el).forEach(line => line.dataset.active = (line.dataset.src === srcId) ? "true" : "false");
      }
      chips.addEventListener("click", (e) => {
        const btn = e.target.closest(".catena-chip");
        if (!btn) return;
        if (activeSrc === btn.dataset.src) {
          activeSrc = null;
          $$(".catena-chip", el).forEach(c => c.dataset.active = "false");
          $$(".catena-curve", el).forEach(c => c.style.opacity = "0.35");
          $$(".catena-line", el).forEach(line => line.dataset.active = "false");
        } else {
          setActive(btn.dataset.src);
        }
      });
    }
  };
```

- [ ] **Step 2: Add catena styles**

Append to `styles.css`:

```css
.teach-block { margin-bottom: 4rem; }
.teach-head { margin-bottom: 1.4rem; }
.teach-head .title { font-size: 1.7rem; }

.catena-chips {
  display: flex; gap: 0.55rem; flex-wrap: wrap;
  margin-bottom: 1.5rem;
}
.catena-chip {
  font: inherit;
  border: 0;
  padding: 0.35rem 0.75rem;
  border-radius: 3px;
  cursor: pointer;
  display: inline-flex;
  flex-direction: column; gap: 0.05rem;
  text-align: left;
  opacity: 0.7;
  transition: opacity var(--t-fast);
}
.catena-chip[data-active="true"] { opacity: 1; outline: 2px solid var(--ink-body); outline-offset: 2px; }
.catena-chip .chip-label { font-weight: 600; font-size: 0.85rem; letter-spacing: 0.02em; }
.catena-chip .chip-ref { font-size: 0.7rem; opacity: 0.85; }

.catena-svg-wrap {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 1rem 1.2rem;
  margin-bottom: 1.2rem;
}
.catena-svg { width: 100%; height: 140px; display: block; }
.catena-curve { transition: opacity var(--t-fast); }

.catena-verses { list-style: none; margin: 0; padding: 0; }
.catena-line {
  display: grid; grid-template-columns: 70px 1fr;
  gap: 1rem; align-items: baseline;
  padding: 0.45rem 0.7rem;
  border-radius: 3px;
  transition: background var(--t-fast);
}
.catena-line .v { font-size: 0.78rem; color: var(--ink-faint); }
.catena-line .t { font-size: 1rem; line-height: 1.4; }
.catena-line[data-active="true"] {
  background: var(--src-bg, var(--highlight-bg));
  color: var(--ink-body);
}
```

- [ ] **Step 3: Verify in browser**

Reload. Catena block renders: eyebrow `CATENA`, title, six color chips (six sources), SVG with six muted curves, eleven numbered verse lines below. Clicking `Ps 14 / 53` makes its curve opaque and tints the four matching phrases (3:10, 3:11, 3:12a, 3:12b).

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(teach): catena renderer — chips, SVG curves, verse mosaic"
```

---

## Task 9: Teach renderer — greek-terms

**Goal:** Greek term chips that expand inline on click, showing gloss / verse / cue.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Add greek-terms renderer to teachRenderers**

In `app.js`, inside `teachRenderers` after `catena`, add (mind the comma):

```javascript
    "greek-terms"(el, block) {
      const head = document.createElement("div");
      head.className = "teach-head";
      head.innerHTML = `
        <div class="eyebrow">GREEK</div>
        <h2 class="title">${block.title}</h2>
        ${block.blurb ? `<p class="muted">${block.blurb}</p>` : ""}
      `;
      el.appendChild(head);

      const grid = document.createElement("div");
      grid.className = "greek-grid";
      grid.innerHTML = block.terms.map((t, i) => `
        <button class="greek-chip" data-i="${i}" aria-expanded="false">
          <div class="gk-greek greek">${t.greek}</div>
          <div class="gk-gloss">${t.gloss}</div>
        </button>
      `).join("");
      el.appendChild(grid);

      const detail = document.createElement("div");
      detail.className = "greek-detail";
      detail.hidden = true;
      el.appendChild(detail);

      let activeIdx = null;
      grid.addEventListener("click", (e) => {
        const btn = e.target.closest(".greek-chip");
        if (!btn) return;
        const i = Number(btn.dataset.i);
        if (activeIdx === i) {
          activeIdx = null;
          detail.hidden = true;
          $$(".greek-chip", el).forEach(c => c.setAttribute("aria-expanded", "false"));
          return;
        }
        activeIdx = i;
        const t = block.terms[i];
        $$(".greek-chip", el).forEach(c => c.setAttribute("aria-expanded", c.dataset.i === String(i) ? "true" : "false"));
        detail.hidden = false;
        detail.innerHTML = `
          <div class="gd-greek greek">${t.greek}</div>
          <div class="gd-gloss"><em>${t.gloss}</em> · <span class="muted">${t.ref}</span></div>
          <div class="gd-note">${t.note}</div>
          <div class="gd-cue">${t.cue}</div>
        `;
      });
    },
```

- [ ] **Step 2: Add greek-terms styles**

Append to `styles.css`:

```css
.greek-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.55rem;
  margin-bottom: 1rem;
}
.greek-chip {
  font: inherit; cursor: pointer;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 0.7rem 0.9rem;
  border-radius: 3px;
  text-align: left;
  transition: background var(--t-fast), border-color var(--t-fast);
}
.greek-chip:hover { border-color: var(--accent); }
.greek-chip[aria-expanded="true"] {
  background: var(--ink-body);
  color: oklch(0.95 0.02 80);
  border-color: var(--ink-body);
}
.greek-chip[aria-expanded="true"] .gk-gloss { color: oklch(0.85 0.04 80); }
.gk-greek { font-size: 1.15rem; line-height: 1.2; margin-bottom: 0.2rem; }
.gk-gloss { font-size: 0.82rem; font-style: italic; color: var(--ink-muted); }

.greek-detail {
  background: var(--ink-body); color: oklch(0.95 0.02 80);
  padding: 1.4rem 1.6rem;
  border-radius: 3px;
}
.gd-greek { font-size: 1.6rem; margin-bottom: 0.3rem; }
.gd-gloss { font-size: 1rem; margin-bottom: 0.7rem; color: oklch(0.85 0.04 80); }
.gd-note { font-size: 0.95rem; margin-bottom: 0.6rem; }
.gd-cue { font-size: 0.88rem; font-style: italic; color: oklch(0.80 0.04 80); }
```

- [ ] **Step 3: Verify in browser**

Reload. After catena, the greek-terms block renders: eight chips in a grid (each Greek + English gloss). Click any chip — it turns dark; a detail panel below shows the term, gloss, ref, note, and cue.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(teach): greek-terms renderer"
```

---

## Task 10: Teach renderer — courtroom-chain

**Goal:** Verse-chain visualization. Four nodes connected by arrows. Click each node to advance the chain.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Add courtroom-chain renderer**

In `app.js`, inside `teachRenderers` after `greek-terms`, add:

```javascript
    "courtroom-chain"(el, block) {
      const head = document.createElement("div");
      head.className = "teach-head";
      head.innerHTML = `
        <div class="eyebrow">COURTROOM</div>
        <h2 class="title">${block.title}</h2>
        ${block.blurb ? `<p class="muted">${block.blurb}</p>` : ""}
      `;
      el.appendChild(head);

      const chain = document.createElement("div");
      chain.className = "court-chain";
      chain.innerHTML = block.nodes.map((n, i) => `
        ${i > 0 ? `<div class="court-arrow" data-i="${i}">→</div>` : ""}
        <button class="court-node ${n.terminal ? "terminal" : ""}" data-i="${i}">
          <div class="cn-ref">${n.ref}</div>
          <div class="cn-label">${n.label}</div>
        </button>
      `).join("");
      el.appendChild(chain);

      const note = document.createElement("div");
      note.className = "court-note";
      note.hidden = true;
      el.appendChild(note);

      let activeIdx = null;
      function paint() {
        $$(".court-node", el).forEach(n => {
          const i = Number(n.dataset.i);
          n.dataset.state = i < activeIdx ? "passed"
                          : i === activeIdx ? "active"
                          : "upcoming";
        });
        $$(".court-arrow", el).forEach(a => {
          const i = Number(a.dataset.i);
          a.dataset.state = i <= activeIdx ? "passed" : "upcoming";
        });
      }

      chain.addEventListener("click", (e) => {
        const btn = e.target.closest(".court-node");
        if (!btn) return;
        const i = Number(btn.dataset.i);
        activeIdx = (activeIdx === i) ? null : i;
        if (activeIdx == null) {
          $$(".court-node", el).forEach(n => n.dataset.state = "upcoming");
          $$(".court-arrow", el).forEach(a => a.dataset.state = "upcoming");
          note.hidden = true;
          return;
        }
        paint();
        const n = block.nodes[activeIdx];
        note.hidden = false;
        note.innerHTML = `<strong>${n.ref}</strong> · ${n.note}`;
      });
    },
```

- [ ] **Step 2: Add courtroom styles**

Append to `styles.css`:

```css
.court-chain {
  display: flex; align-items: center; gap: 0.6rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.court-node {
  font: inherit; cursor: pointer;
  background: var(--bg-card);
  border: 2px solid var(--border-card);
  padding: 0.7rem 1rem;
  border-radius: 3px;
  text-align: center;
  min-width: 130px;
  transition: background var(--t-fast), border-color var(--t-fast), color var(--t-fast);
}
.court-node[data-state="active"] {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.court-node[data-state="passed"] {
  background: oklch(0.92 0.06 25);
  border-color: var(--accent);
  color: var(--ink-body);
}
.court-node.terminal { border-width: 3px; font-weight: 600; }
.cn-ref { font-size: 0.7rem; letter-spacing: 0.12em; color: var(--ink-faint); margin-bottom: 0.2rem; }
.court-node[data-state="active"] .cn-ref,
.court-node[data-state="passed"] .cn-ref { color: inherit; opacity: 0.8; }
.cn-label { font-size: 0.95rem; }
.court-arrow {
  font-size: 1.4rem; color: var(--ink-faint);
  transition: color var(--t-fast);
}
.court-arrow[data-state="passed"] { color: var(--accent); }

.court-note {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 1rem 1.2rem;
  border-radius: 3px;
}
```

- [ ] **Step 3: Verify in browser**

Reload. Courtroom block shows four nodes connected by arrows. Click `3:6` — it turns accent, earlier nodes go to "passed" tint, arrows up to it color accent. Note panel below shows the full verse note.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(teach): courtroom-chain renderer"
```

---

## Task 11: Teach renderer — body-parts

**Goal:** Color-coded English verse mosaic for Rom 3:13-18. Click a phrase to make it active. Eyes is climax (default active).

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Add body-parts renderer**

In `app.js`, inside `teachRenderers` after `courtroom-chain`, add:

```javascript
    "body-parts"(el, block) {
      const head = document.createElement("div");
      head.className = "teach-head";
      head.innerHTML = `
        <div class="eyebrow">BODY-PARTS</div>
        <h2 class="title">${block.title}</h2>
        ${block.blurb ? `<p class="muted">${block.blurb}</p>` : ""}
      `;
      el.appendChild(head);

      const list = document.createElement("ol");
      list.className = "body-mosaic";
      list.innerHTML = block.phrases.map((p, i) => {
        const isClimax = !!p.climax;
        const bg = isClimax ? null : `oklch(0.92 0.05 ${p.hue})`;
        return `
          <li class="bp-line${isClimax ? " climax" : ""}"
              data-i="${i}"
              ${bg ? `style="--bp-bg: ${bg};"` : ""}>
            <span class="bp-text">${p.english}</span>
            <span class="bp-meta">— <span class="bp-part">${p.part}</span> · ${p.image} <span class="bp-ref">(${p.ref})</span></span>
          </li>
        `;
      }).join("");
      el.appendChild(list);

      const climaxIdx = block.phrases.findIndex(p => p.climax);
      let activeIdx = climaxIdx >= 0 ? climaxIdx : 0;
      function paint() {
        $$(".bp-line", el).forEach(line => {
          line.dataset.active = String(Number(line.dataset.i) === activeIdx);
        });
      }
      paint();

      list.addEventListener("click", (e) => {
        const li = e.target.closest(".bp-line");
        if (!li) return;
        activeIdx = Number(li.dataset.i);
        paint();
      });
    }
```

(That's the closing of `teachRenderers`. No trailing comma after `body-parts`.)

- [ ] **Step 2: Add body-parts styles**

Append to `styles.css`:

```css
.body-mosaic { list-style: none; padding: 0; margin: 0; }
.bp-line {
  display: flex; align-items: baseline; gap: 0.8rem;
  padding: 0.5rem 0.8rem;
  margin: 0.25rem 0;
  border-radius: 3px;
  cursor: pointer;
  transition: background var(--t-fast);
  background: transparent;
}
.bp-line .bp-text {
  background: var(--bp-bg, transparent);
  padding: 1px 6px;
  font-size: 1.05rem;
  line-height: 1.5;
  color: var(--ink-body);
}
.bp-line .bp-meta { font-size: 0.78rem; color: var(--ink-faint); letter-spacing: 0.04em; }
.bp-part { color: var(--accent); font-weight: 600; }

.bp-line.climax .bp-text {
  background: var(--ink-body);
  color: oklch(0.95 0.02 80);
  font-weight: 500;
}
.bp-line[data-active="true"] {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.bp-line.climax[data-active="true"] {
  outline: none;
}
```

- [ ] **Step 3: Verify in browser**

Reload. Body-parts block renders 7 lines, color-coded. The "There is no fear of God before their eyes" line shows in dark ink + cream background and is outlined as active by default. Clicking another phrase shifts the outline.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(teach): body-parts renderer — color-coded verse mosaic"
```

---

## Task 12: Render Equip with revealable blanks

**Goal:** Single panel with bigIdea + three movement cards + thisWeek. Each blank is clickable to reveal. `r` reveals all (handled in Task 16; for now, an inline keydown placeholder).

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Replace renderEquip stub**

In `app.js`, replace `function renderEquip() { /* Task 12 */ }` with:

```javascript
  function renderEquip() {
    const mount = $("#equip-panel");
    if (!mount || !D || !D.equip) return;
    const eq = D.equip;

    const bigIdeaMap = blanksToMap(eq.bigIdea.blanks);
    const bigIdeaHtml = renderBlankTemplate(eq.bigIdea.template, bigIdeaMap, "bi");

    const moveCards = eq.movements.map((mv, i) => {
      const nameMap = { a: { answer: mv.nameBlank.answer } };
      const nameHtml = renderBlankTemplate(mv.nameTemplate, nameMap, `mv${i}-name`);
      const christMap = blanksToMap(mv.christ.blanks);
      const christHtml = renderBlankTemplate(mv.christ.template, christMap, `mv${i}-ch`);
      return `
        <article class="eq-card">
          <div class="eq-card-roman">${mv.roman}</div>
          <div class="eq-card-name">${nameHtml}</div>
          <div class="eq-card-ref">${mv.ref}</div>
          <div class="eq-card-summary">${mv.summary}</div>
          <div class="eq-card-christ"><em>${christHtml}</em></div>
        </article>
      `;
    }).join("");

    const tw = eq.thisWeek;
    const twHtml = renderBlankTemplate(tw.template, blanksToMap(tw.blanks), "tw");

    mount.innerHTML = `
      <div class="eyebrow">EQUIP</div>
      <p class="eq-bigidea">${bigIdeaHtml}</p>
      <div class="eq-cards">${moveCards}</div>
      <p class="eq-thisweek"><strong class="eyebrow eyebrow-inline">THIS WEEK</strong> · ${twHtml}</p>
      <div class="eq-actions">
        <button type="button" class="reveal-all" id="equip-reveal-all">Reveal all <kbd>r</kbd></button>
      </div>
    `;

    mount.addEventListener("click", (e) => {
      const blank = e.target.closest(".blank");
      if (blank) { fillBlank(blank); return; }
      if (e.target.closest("#equip-reveal-all")) {
        $$(".blank", mount).forEach(b => fillBlank(b));
      }
    });
  }
```

- [ ] **Step 2: Add Equip styles**

Append to `styles.css`:

```css
.eq-bigidea {
  font-size: 1.5rem; line-height: 1.4; font-style: italic;
  text-align: center;
  max-width: 760px; margin: 0 auto 2rem;
}
.eq-cards {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
@media (max-width: 768px) { .eq-cards { grid-template-columns: 1fr; } }
.eq-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  padding: 1.4rem 1.2rem;
  border-radius: 3px;
  display: flex; flex-direction: column; gap: 0.6rem;
}
.eq-card-roman { font-size: 0.82rem; letter-spacing: 0.18em; color: var(--accent); font-weight: 700; }
.eq-card-name  { font-size: 1.3rem; font-weight: 600; }
.eq-card-ref   { font-size: 0.8rem; color: var(--ink-faint); }
.eq-card-summary { font-size: 1rem; color: var(--ink-body); }
.eq-card-christ { font-size: 0.95rem; color: var(--ink-muted); margin-top: auto; }

.eq-thisweek { font-size: 1.05rem; line-height: 1.5; max-width: 760px; margin: 0 auto; }
.eyebrow-inline { font-size: 0.7rem; }

.eq-actions { text-align: center; margin-top: 1.5rem; }
.reveal-all {
  font: inherit; cursor: pointer;
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  padding: 0.5rem 1rem;
  border-radius: 3px;
}
.reveal-all kbd {
  background: var(--accent); color: #fff;
  padding: 1px 6px; border-radius: 2px; font-size: 0.8em;
  margin-left: 0.4rem;
  font-family: var(--font-mono);
}
.reveal-all:hover { background: var(--accent); color: #fff; }
```

- [ ] **Step 3: Verify in browser**

Reload. Equip section (dark theme) shows bigIdea sentence with two visible blanks; three movement cards (Charge / Proof / Verdict) each with name + christ blanks; "This Week" line. Click each blank — it fills with the answer. Click "Reveal all" — all blanks fill at once.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(equip): three-card structure with revealable blanks"
```

---

## Task 13: Render Apply and Mission slides

**Goal:** Apply (10) and Mission (10) rendered as scroll-snapping slide panels via a shared `renderSlides()` helper.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Replace renderApply / renderMission stubs**

In `app.js`:

```javascript
  function renderApply() {
    return renderSlides("#apply-slides", D.apply, "APPLY");
  }
  function renderMission() {
    return renderSlides("#mission-slides", D.mission, "MISSION");
  }

  function renderSlides(mountSel, items, label) {
    const mount = $(mountSel);
    if (!mount || !items) return;
    const total = items.length;
    mount.innerHTML = items.map((q, i) => {
      const tags = (q.tags || []).map(t => `<span class="tag tag--${t}">${t}</span>`).join("");
      const dots = items.map((_, k) => `<span class="dot ${k === i ? "active" : ""}"></span>`).join("");
      return `
        <article class="slide reveal" data-i="${i}">
          <div class="eyebrow">${label} · QUESTION ${i + 1} OF ${total}</div>
          <p class="question">${escapeHtml(q.question)}</p>
          <div class="tags">${tags}</div>
          <div class="pagination">${dots}</div>
        </article>
      `;
    }).join("");
  }
```

- [ ] **Step 2: Add tag color tokens**

Append to `styles.css`:

```css
.tag--evangelism      { background: oklch(0.85 0.06 130); color: #1a1a1a; }
.tag--apologetics     { background: oklch(0.85 0.06 230); color: #1a1a1a; }
.tag--home            { background: oklch(0.86 0.05 80);  color: #1a1a1a; }
.tag--abroad          { background: oklch(0.86 0.05 320); color: #1a1a1a; }
.tag--confession      { background: oklch(0.86 0.05 30);  color: #1a1a1a; }
.tag--self-justification { background: oklch(0.86 0.05 60); color: #1a1a1a; }
.tag--christ-thread   { background: oklch(0.86 0.05 280); color: #1a1a1a; }
.tag--words           { background: oklch(0.86 0.05 100); color: #1a1a1a; }
.tag--family          { background: oklch(0.86 0.05 200); color: #1a1a1a; }
.tag--relationships   { background: oklch(0.86 0.05 220); color: #1a1a1a; }
.tag--conscience      { background: oklch(0.86 0.05 340); color: #1a1a1a; }
.tag--discipleship    { background: oklch(0.86 0.05 160); color: #1a1a1a; }

section[data-theme="dark"] .tag--evangelism      { background: oklch(0.65 0.10 130); }
section[data-theme="dark"] .tag--apologetics     { background: oklch(0.65 0.10 230); }
section[data-theme="dark"] .tag--home            { background: oklch(0.66 0.08 80); }
section[data-theme="dark"] .tag--abroad          { background: oklch(0.66 0.08 320); }
```

- [ ] **Step 3: Add a console-only sanity check for mission tags**

In `app.js`, append inside `init()` after `setupReveal();`:

```javascript
    if (D.mission) {
      const seen = new Set();
      D.mission.forEach(q => (q.tags || []).forEach(t => seen.add(t)));
      const need = ["evangelism", "apologetics", "home", "abroad"];
      const missing = need.filter(t => !seen.has(t));
      if (missing.length) {
        console.warn(`Mission missing tag categories: ${missing.join(", ")}`);
      }
    }
```

- [ ] **Step 4: Verify**

Reload. Apply renders 10 slides; Mission renders 10 slides. Each slide is at least 70vh; scroll-snaps between them. Pagination dots show position. No console warning about missing mission tag categories.

- [ ] **Step 5: Commit**

```bash
git add app.js styles.css
git commit -m "feat(apply,mission): slide-based question renderer with tag colors"
```

---

## Task 14: Render Send-out

**Goal:** Static closing panel — take-home truth + optional outbound link.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Replace renderSendOut stub**

In `app.js`:

```javascript
  function renderSendOut() {
    const mount = $("#send-out-panel");
    if (!mount || !D || !D.sendOut) return;
    const so = D.sendOut;
    const link = so.deeperLink
      ? `<p class="send-link"><a href="${so.deeperLink.url}" target="_blank" rel="noopener">${so.deeperLink.label} →</a></p>`
      : "";
    mount.innerHTML = `
      <div class="eyebrow">CLOSE</div>
      <h2 class="title send-th">Take-home truth</h2>
      <p class="send-truth"><em>${escapeHtml(so.takeHome)}</em></p>
      ${link}
    `;
  }
```

- [ ] **Step 2: Send-out styles**

Append to `styles.css`:

```css
.send-th { font-size: 1.3rem; }
.send-truth { font-size: 1.7rem; line-height: 1.4; max-width: 760px; }
.send-link { margin-top: 2rem; }
.send-link a { color: var(--accent); text-decoration: none; border-bottom: 1px solid currentColor; }
```

- [ ] **Step 3: Verify**

Reload, scroll to the bottom. Send-out section shows eyebrow `CLOSE`, h2 `Take-home truth`, the take-home in italic, and the deeper-link to the Romans3 site.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(send-out): take-home + optional outbound link"
```

---

## Task 15: Keyboard shortcuts

**Goal:** Implement the full keyboard kit. ↓/↑/Space/PgDn/PgUp/1-4/Home/End/r/f/?.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/app.js`

- [ ] **Step 1: Replace setupKeyboard stub**

In `app.js`:

```javascript
  function setupKeyboard() {
    const sectionIds = ["hero", "teach", "equip", "apply", "mission", "send-out"];

    function scrollSlide(dir) {
      const sec = state.activeSection;
      if (sec !== "apply" && sec !== "mission") return false;
      const mountSel = sec === "apply" ? "#apply-slides" : "#mission-slides";
      const slides = $$(`${mountSel} > .slide`);
      if (!slides.length) return false;
      const viewMid = window.scrollY + window.innerHeight / 2;
      let curIdx = 0;
      slides.forEach((s, i) => {
        const r = s.getBoundingClientRect();
        const top = window.scrollY + r.top;
        if (top < viewMid) curIdx = i;
      });
      const next = Math.max(0, Math.min(slides.length - 1, curIdx + dir));
      slides[next].scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }

    function jump(idx) {
      const id = sectionIds[idx];
      const t = id ? document.getElementById(id) : null;
      if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    window.addEventListener("keydown", (e) => {
      if (e.target.closest("input, textarea, [contenteditable]")) return;
      switch (e.key) {
        case "ArrowDown":
        case " ":
        case "PageDown":
          if (scrollSlide(+1)) e.preventDefault();
          break;
        case "ArrowUp":
        case "PageUp":
          if (scrollSlide(-1)) e.preventDefault();
          break;
        case "1": jump(1); e.preventDefault(); break;
        case "2": jump(2); e.preventDefault(); break;
        case "3": jump(3); e.preventDefault(); break;
        case "4": jump(4); e.preventDefault(); break;
        case "Home": jump(0); e.preventDefault(); break;
        case "End":  jump(5); e.preventDefault(); break;
        case "r":
          if (state.activeSection === "equip") {
            $$(".blank").forEach(b => fillBlank(b));
            e.preventDefault();
          }
          break;
        case "f":
          if (document.fullscreenElement) document.exitFullscreen();
          else document.documentElement.requestFullscreen().catch(() => {});
          e.preventDefault();
          break;
        case "?":
          toggleKbdHelp();
          e.preventDefault();
          break;
        case "Escape":
          if (document.fullscreenElement) document.exitFullscreen();
          $("#kbd-help").hidden = true;
          break;
      }
    });
  }

  function toggleKbdHelp() {
    const el = $("#kbd-help");
    if (!el) return;
    if (el.hidden) {
      el.hidden = false;
      el.innerHTML = `
        <div class="kbd-help-card">
          <h3>Keyboard</h3>
          <ul>
            <li><kbd>↓</kbd>/<kbd>Space</kbd>/<kbd>PgDn</kbd> — advance</li>
            <li><kbd>↑</kbd>/<kbd>PgUp</kbd> — back</li>
            <li><kbd>1</kbd>/<kbd>2</kbd>/<kbd>3</kbd>/<kbd>4</kbd> — Teach / Equip / Apply / Mission</li>
            <li><kbd>Home</kbd>/<kbd>End</kbd> — top / bottom</li>
            <li><kbd>r</kbd> — reveal all blanks (in Equip)</li>
            <li><kbd>f</kbd> — fullscreen</li>
            <li><kbd>Esc</kbd> — exit fullscreen / close help</li>
          </ul>
        </div>
      `;
      el.addEventListener("click", () => { el.hidden = true; }, { once: true });
    } else {
      el.hidden = true;
    }
  }
```

- [ ] **Step 2: Add kbd-help-card styles**

Append to `styles.css`:

```css
.kbd-help-card { font-size: 0.95rem; }
.kbd-help-card ul { list-style: none; padding: 0; margin: 0.6rem 0 0; }
.kbd-help-card li { margin: 0.4rem 0; }
.kbd-help-card kbd {
  background: var(--ink-body); color: oklch(0.95 0.02 80);
  padding: 1px 6px; border-radius: 2px; font-family: var(--font-mono); font-size: 0.85em;
  margin-right: 0.3rem;
}
```

- [ ] **Step 3: Verify**

Reload. Press `1` → page jump-scrolls to Teach. Press `?` → keyboard help overlay appears, click it to dismiss. Press `f` → fullscreen toggle. Inside Apply, press `↓` → page scrolls to next question slide. Inside Equip, press `r` → all blanks reveal.

- [ ] **Step 4: Commit**

```bash
git add app.js styles.css
git commit -m "feat(driver): keyboard shortcuts for projector use"
```

---

## Task 16: Responsive — mobile rail strip + spacing tweaks

**Goal:** Below 768px the layout collapses gracefully. The rail-collapse CSS is already in Task 4; this task adds remaining spacing tweaks.

**Files:**
- Modify: `/Volumes/External/romans3_chalk_and_talk/styles.css`

- [ ] **Step 1: Add small-screen tweaks**

Append to `styles.css`:

```css
@media (max-width: 768px) {
  :root { --content-pad-x: 1.2rem; --section-pad-y: 2.5rem; }
  .hero { padding-top: 2rem; padding-bottom: 2.5rem; }
  .hero-inner .title { font-size: 2rem; }
  .hero-inner .subtitle { font-size: 1.1rem; }
  .greek-grid { grid-template-columns: 1fr 1fr; }
  .court-chain { flex-direction: column; align-items: stretch; }
  .court-arrow { transform: rotate(90deg); }
  .slide .question { font-size: 1.4rem; }
  .send-truth { font-size: 1.3rem; }
}
```

- [ ] **Step 2: Verify with viewport resize**

DevTools → device toolbar → iPhone 12 (390x844). Rail collapses to top strip; equip cards stack vertically; courtroom nodes stack with arrows rotated 90°. Apply/Mission slides remain readable.

- [ ] **Step 3: Commit**

```bash
git add styles.css
git commit -m "feat(responsive): mobile fallback below 768px"
```

---

## Task 17: Documentation — README, STYLE.md, TEMPLATE.md, data.example.js

**Goal:** Capture editorial rules and the template-seam instructions so future passages can be added without reading the code.

**Files:**
- Create: `/Volumes/External/romans3_chalk_and_talk/README.md`
- Create: `/Volumes/External/romans3_chalk_and_talk/STYLE.md`
- Create: `/Volumes/External/romans3_chalk_and_talk/TEMPLATE.md`
- Create: `/Volumes/External/romans3_chalk_and_talk/data.example.js`

- [ ] **Step 1: README.md**

Path: `README.md`

```markdown
# Romans 3:9-20 · TEAM Page

Static teaching surface for the Romans 3:9-20 afternoon TEAM session
(Teach · Equip · Apply · Mission). Projects to a fellowship-hall screen;
driven from the front by keyboard or presenter clicker.

## Viewing

Open `index.html` in a modern browser, or serve the directory:

    python3 -m http.server 5500

then open http://localhost:5500/.

No build step. Static HTML, CSS, and vanilla JavaScript.

## Driving the page

- ↓ / Space / PgDn — advance
- ↑ / PgUp — back
- 1 / 2 / 3 / 4 — jump to Teach / Equip / Apply / Mission
- Home / End — top / bottom
- r — reveal all Equip blanks
- f — fullscreen
- ? — keyboard help
- Esc — close overlay / exit fullscreen

## Architecture

| File | Role |
|------|------|
| `index.html` | Page markup with mount points per section. |
| `data.js` | The single content file — edit this for new passages. |
| `app.js` | Renderer + interactions. Passage-agnostic. |
| `styles.css` | Design system: type, palette, layout primitives. |
| `theme.css` | Per-section light/dark themes. |
| `tools/validate-team-data.js` | Schema validator (Node CLI). |

## For new passages

See `TEMPLATE.md`.

## Editorial rules

See `STYLE.md`.
```

- [ ] **Step 2: STYLE.md**

Path: `STYLE.md`

```markdown
# TEAM Page · Style Guide

Inherits the editorial discipline of `tendflock/Romans3`.

## Voice

- Scholarly but accessible. Translate every Greek/Hebrew word the first
  time it appears in prose.
- Pastor's voice. Lead the room into a passage; don't perform expertise.
- Specific over generic. "Walvoord §C ¶3 says X" beats "some scholars
  argue X."

## Hard rules

- No emoji. Anywhere. Ever.
- BC / AD, not BCE / CE. Format: `c. AD 57`, `c. 150 BC`, `3rd c. AD`.
- Paraphrastic English only. All glosses are written fresh for this
  project. Do not paste in ESV, NIV, NRSV, NASB, KJV, or any modern
  copyrighted translation.
- Ancient text from public-domain critical editions only. Greek NT via
  Nestle-Aland / UBS. Greek OT via Rahlfs-Hanhart. Hebrew via the
  Masoretic / BHS family.
- No filler. If a paragraph doesn't move the argument forward, cut it.

## Visual rules

- Three faces only: Source Serif 4 (English), Gentium Plus (Greek),
  Frank Ruhl Libre (Hebrew). No fourth face.
- oklch palette, low chroma. No hard-coded hex except for true
  neutrals (`#fff`, `#222`, `#1a1a1a`).
- Motion argues or doesn't exist. No decorative entrance animation,
  no parallax, no scroll-driven reveals beyond the `.reveal` fade.
- Theme alternates Hero light → Teach light → Equip dark →
  Apply light → Mission dark → Send-out light.

## TEAM-specific rules

- No new handout. Equip mirrors the morning sermon handout.
- One pattern per content shape. Teach is editorial scroll-with-focus;
  Equip is one panoramic panel with revealable blanks; Apply / Mission
  are slide-by-slide. Don't homogenize.
- The room watches one screen. Type is large, contrast is high, motion
  focuses attention rather than competing for it.

## Adding a Teach block kind

If your passage needs a kind not yet implemented (`hebrew-terms`,
`covenant-pattern`, etc.):

1. Add the kind name to `KNOWN_TEACH_KINDS` in
   `tools/validate-team-data.js`.
2. Implement `teachRenderers["new-kind"](el, block)` in `app.js`.
3. Add the kind's styles to `styles.css`.
4. Re-run the validator and re-smoke-test.
```

- [ ] **Step 3: TEMPLATE.md**

Path: `TEMPLATE.md`

```markdown
# Adapting this repo for a new TEAM passage

Each weekly TEAM session gets its own GitHub Pages deploy. To prepare
for next Sunday's passage:

## 1. Duplicate

Easiest: clone this repo into a new GitHub repository and rename. Or:

    gh repo create tendflock/<new-passage>-team --public --clone
    cd <new-passage>-team
    cp -r ../romans-3-9-20-team/{index.html,app.js,styles.css,theme.css,tools,STYLE.md,LICENSE,data.example.js} .
    cp ../romans-3-9-20-team/data.example.js data.js

## 2. Edit `data.js`

This is the only file you need to touch:

- `meta` — passage label, burden, take-home truth, sermon title and date.
- `teach` — array of Teach blocks. Use any of the supported `kind`s
  (catena, greek-terms, hebrew-terms, courtroom-chain, body-parts,
  phrase-mosaic, historical-context, theological-categories). Drop kinds
  not relevant to this passage.
- `equip.bigIdea`, `equip.movements`, `equip.thisWeek` — mirror the
  morning sermon handout's blanks.
- `apply` — 8-12 socratic questions; each with `question` (string) and
  `tags` (array, may be empty).
- `mission` — 8-12 questions, each with at least one tag from the four
  allowed: `evangelism`, `apologetics`, `home`, `abroad`.
- `sendOut.takeHome` — final take-home statement.
- `sendOut.deeperLink` — optional outbound link.

## 3. Validate

    node tools/validate-team-data.js data.js

Expected: `ok data.js — valid TEAM data`. Fix any reported errors.

## 4. Smoke-test the page

    python3 -m http.server 5500

Open http://localhost:5500/ at 1080p (your projection target). Drive the
page by keyboard: Home, 1, 2, 3, 4, End, r, f, ?. Verify every
interaction works for this passage's content.

## 5. Add a new Teach kind (only if needed)

If your passage needs a kind that doesn't exist yet:

1. Add the kind name to `KNOWN_TEACH_KINDS` in
   `tools/validate-team-data.js`.
2. Implement `teachRenderers["new-kind"](el, block)` in `app.js`.
3. Add the kind's styles to `styles.css`.
4. Re-run validator and re-smoke-test.

## 6. Deploy

    git add -A
    git commit -m "feat(content): <passage> TEAM data + first build"
    git push

Enable GitHub Pages from the repo's settings (Pages → main / root).

The page will be at `https://tendflock.github.io/<new-passage>-team/`.
```

- [ ] **Step 4: data.example.js**

Path: `data.example.js`

```javascript
// Skeleton showing required shape. Copy to data.js and fill in.

window.TEAM_DATA = {
  meta: {
    passage: "Book Chapter:Verse-Verse",
    burden: "One-line homiletical point.",
    takeHome: "One-line take-home truth.",
    sermon: { title: "Sermon Title", date: "YYYY-MM-DD" }
  },

  teach: [
    // Drop / add blocks as the passage warrants.
    // { kind: "catena",         title: "...", sources: [...], phrases: [...] },
    // { kind: "greek-terms",    title: "...", terms: [...] },
    // { kind: "courtroom-chain",title: "...", nodes: [...] },
    // { kind: "body-parts",     title: "...", phrases: [...] },
  ],

  equip: {
    bigIdea: { template: "{a}", blanks: [{ key: "a", answer: "..." }] },
    movements: [
      // { roman: "I", nameTemplate: "The {a}", nameBlank: { answer: "..." },
      //   ref: "v.1", summary: "...",
      //   christ: { template: "{a}", blanks: [{ key: "a", answer: "..." }] } }
    ],
    thisWeek: { template: "{a}", blanks: [{ key: "a", answer: "..." }] }
  },

  apply: [
    // { question: "...", tags: [] }
  ],

  mission: [
    // { question: "...", tags: ["evangelism"] }
  ],

  sendOut: {
    takeHome: "Take-home truth.",
    deeperLink: { url: "https://...", label: "Optional deeper resource" }
  }
};
```

- [ ] **Step 5: Commit**

```bash
git add README.md STYLE.md TEMPLATE.md data.example.js
git commit -m "docs: README + STYLE.md + TEMPLATE.md + data.example.js"
```

---

## Task 18: Adversarial review + repo rename + deploy

**Goal:** Run codex CLI as adversarial reviewer. Apply targeted fixes. Rename the GitHub repo. Verify GitHub Pages serves correctly.

**Files:**
- Possibly modify any of the above based on adversarial findings.

- [ ] **Step 1: Final smoke test**

Run validator + tests:

    node tools/validate-team-data.js data.js
    node tools/validate-team-data.test.js

Both expect green. Then start a local server and walk the page in Chrome at 1080p — `Home`, `1`, click each catena chip, click each greek term, click each courtroom node, click each body-part phrase, `2` (Equip), click each blank, `r`, `3` (Apply), advance through 10 slides, `4` (Mission), advance through 10 slides, `End`, `?`. No console errors expected. Make a list of any polish items.

- [ ] **Step 2: Codex adversarial review**

Run codex CLI with this prompt:

```
You are an adversarial reviewer reading a static teaching page for the Romans 3:9-20 TEAM session. Read the spec at /Volumes/External/Logos4/docs/superpowers/specs/2026-04-27-romans3-team-page-design.md. Then read the implementation in /Volumes/External/romans3_chalk_and_talk/. Find:

(1) cases where the implementation diverges from the spec,
(2) cases where the page would fail on a 1080p projection (small type, low contrast, ambiguous interaction state),
(3) cases where the editorial rules in STYLE.md are violated (no emoji, no copyrighted English translations, oklch only).

Report specifically — name the file and line.
```

Save the review output to `/Volumes/External/Logos4/docs/research/2026-04-27-team-page-codex-review.md`.

- [ ] **Step 3: Apply fixes from review**

For each finding, decide: fix, defer, or reject. Apply fixes inline. Commit each as `fix(...): <issue>`. Defer/reject items get a short reason in the review file.

- [ ] **Step 4: Final visual confirmation**

Reload at 1080p. Run through every section once more by keyboard. Confirm:

- Hero renders without console errors.
- Teach catena: clicking each of 6 source chips highlights its curve and matching verses.
- Teach greek: 8 chips clickable; detail panel shows.
- Teach courtroom: 4 nodes click in sequence; verdict node has terminal style.
- Teach body-parts: 7 phrases color-coded; eyes climax dark by default.
- Equip: bigIdea + 3 cards + thisWeek visible. Click each blank fills correctly. `r` reveals all.
- Apply: 10 slides, scroll-snaps work, pagination dots accurate.
- Mission: 10 slides, all four mission tag categories appear.
- Send-out: take-home + deeper link.
- Rail tracks active section; click letters to jump.
- `?` shows keyboard help.

- [ ] **Step 5: Push and rename the GitHub repo**

```bash
git push origin main
git push --tags
gh repo rename romans-3-9-20-team
git remote set-url origin https://github.com/tendflock/romans-3-9-20-team.git
git remote -v
```

Expected: remote is now `https://github.com/tendflock/romans-3-9-20-team.git`.

- [ ] **Step 6: Verify GitHub Pages**

Visit `https://tendflock.github.io/romans-3-9-20-team/` in a browser (allow ~60s for Pages to rebuild after rename). Expected: HTTP 200, page loads, all interactions work.

- [ ] **Step 7: Tag v1**

```bash
git tag v1.0-romans-3-9-20
git push --tags
```

- [ ] **Step 8: Update Logos4 plan with completion note**

In the Logos4 repo, append to this plan file:

```
## Completion

Completed YYYY-MM-DD. Live at https://tendflock.github.io/romans-3-9-20-team/.
Codex adversarial review at docs/research/2026-04-27-team-page-codex-review.md.
```

Then:

```bash
cd /Volumes/External/Logos4
git add docs/superpowers/plans/2026-04-27-romans3-team-page.md docs/research/2026-04-27-team-page-codex-review.md
git commit -m "docs(team-page): mark plan complete; archive codex adversarial review"
```

---

## Self-Review Checklist

After all tasks complete, run this verification before claiming done:

1. `node tools/validate-team-data.js data.js` → `ok valid`.
2. `node tools/validate-team-data.test.js` → `8 passed, 0 failed`.
3. Open `index.html` in Chrome at 1080p. Press `?` — help shows. Press `Esc`. Drive `Home → 1 → 2 → 3 → 4 → End`. Each section renders without console errors.
4. In Teach catena, click each of 6 source chips in turn — curve + matching verse highlight together.
5. In Equip, click each blank in order — they fill with the correct answer (verdict, flee, Charge, exception, Proof, tested, Verdict, answer, justify, flee).
6. In Apply, press `↓` 10 times — pagination dots advance through 10. Press `↑` to walk back.
7. In Mission, confirm all four mission tag categories appear at least once across the 10 questions.
8. Resize to 390px wide; rail collapses to top strip; layout remains readable.
9. GitHub Pages URL `https://tendflock.github.io/romans-3-9-20-team/` returns 200.

If all 9 verifications pass, the implementation matches the spec.
