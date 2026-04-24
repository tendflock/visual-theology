# WS0 Audit Report

## 1. Verdict

**pass-with-conditions**

WS0b cleared the biggest risk Bryan was worried about: the four new scholar files are primary-voice, directly quoted, and the verification sweep reports a **100% verified rate across the new JSONs (89/89)**. The remaining problems are not fabrication problems; they are **schema-drift and calibration problems**. One file (`blaising-bock-progressive-dispensationalism.json`) departs from the locked axis map in ways that would miswire WS1 ingestion, and two files (especially Collins and Durham) contain rationales that outrun what the stored quote set actually proves. Those issues are fixable, but they should be fixed before WS1 treats this data as production-ready.

## 2. Tradition Audit

| Tradition | Status | Evidence |
|---|---|---|
| Critical-modern Daniel → Collins (Hermeneia) | ✓ | `collins-hermeneia-daniel.json` gives Collins in his own voice on A/B/C/J; e.g. §`P...322`: “Antiochus IV was the first Hellenistic king to introduce divine epithets...” and §`P...309`: “The decisive objection against the messianic interpretation...” |
| Classical dispensational Daniel → Walvoord | ✓ | `walvoord-daniel.json` gives Walvoord directly on B/C/K/N; e.g. §`DIV76`: fourth beast = Rome, §`DIV82`: Antiochus only foreshadows, §`DIV2`: “three prophetic programs... nations, Israel, and the church.” |
| Progressive dispensational → Blaising & Bock | ✓ | `blaising-bock-progressive-dispensationalism.json` is primary voice throughout; e.g. §`PT1.CH1.6.3`: the church is “neither a separate race of humanity,” §`PT1.CH1.6.5`: blessings are “partial and inaugurated,” §`PT3.CH8.3`: future millennial kingdom. |
| Historicist-Reformation → Durham | ✓ | `durham-revelation.json` is plainly primary voice; e.g. §`JUDI`: “the Pope of Rome his being that Antichrist,” §`CH17.4`: “if Rome be the seat... the Pope Antichrist.” |
| Amillennial (Reformed) → Hoekema, Riddlebarger | ✓ | Still present in `2026-04-23-daniel-interpretive-taxonomy-survey.md`: Hoekema art. 743, “present reign of the souls of deceased believers with Christ in heaven”; Riddlebarger art. 702 on the church militant / present millennium and art. 667 on the two-threats pattern. |
| Moderate/mediating evangelical → Longman, Lucas | ✓ | Still present in the 2026-04-23 survey: Longman art. 518, “the multivalent imagery intends to prohibit definite historical identifications”; Lucas art. 314 on Jesus finding in Dan 7:13 “a ready-made image for his own self-understanding.” |
| Partial preterist → Sproul | ✓ | Still present in the 2026-04-23 survey: Sproul is explicitly tagged moderate/partial preterist, with art. 225 (“I must confess that I am still unsettled...”) and art. 240 (“fatal flaw” of full preterism). |
| Reception/literary → Newsom & Breed | ✓ | Still present in the 2026-04-23 survey: Newsom & Breed art. 488, later chapters “reinterpret this figure with increasing specificity... as Michael”; Breed’s reception-history method is named from the same work. |

No tradition named in §A is now represented only through an opponent’s summary. The “no strawmen” requirement is materially met.

## 3. Verification Audit

- Overall verified rate in the four new scholar JSONs: **100% (89 verified / 89 total)**.
- Scholar files below 90% verified: **none**.
- `partial` citations in the new scholar JSONs: **none**.
- `quote-not-found` citations in the new scholar JSONs: **none**.

The only verification failures in the sweep are in the legacy `2026-04-23-daniel-interpretive-taxonomy-survey.md`, not the four WS0b files:

| Scholar | Legacy location | Likely axis |
|---|---|---|
| Bauckham art. 119 | 2026-04-23 survey | Q / genre-eschatology relation |
| Bauckham art. 120 | 2026-04-23 survey | N / cross-book coherence |
| Collins art. 1415 | 2026-04-23 survey | P/Q / meaning-locus or genre framing |
| Lucas art. 314 | 2026-04-23 survey | J / Son of Man |

Five high-stakes quote-to-rationale spot-checks:

1. `walvoord-daniel.json`, Axis K, `strong`: **clean**. The stored quotes directly support the “three prophetic programs” / Israel-church distinction claim.
2. `blaising-bock-progressive-dispensationalism.json`, Axis K, `strong`: **clean**. The quotes directly support rejection of the church as a separate humanity and affirm a unified redemption plan.
3. `collins-hermeneia-daniel.json`, Axis J, `strong`: **clean**. The quote set really does support Collins’s Michael/angelic reading against messianic and collective alternatives.
4. `collins-hermeneia-daniel.json`, Axis C, `strong`: **over-claimed rationale**. The stored quotes verify Antiochus coinage and cultic-calendar disruption, but the rationale also claims support for the three uprooted horns and the three-and-a-half-year period without storing quotes for those moves.
5. `durham-revelation.json`, Axis N, `strong`: **over-claimed rationale**. The stored quote proves a Danielic beast-template, but not yet the fuller claim that Revelation “borrows types,” reapplies Antiochus-language to Antichrist, and escalates this specifically into papal succession. That needs more citation support.

## 4. Divergence Audit

Classical dispensationalism vs progressive dispensationalism is **not flattened** on the core live axes:

- Axis H: Walvoord is future-only / consistent futurist; B&B are explicitly inaugurated.
- Axis K: Walvoord preserves the nations-Israel-church program split; B&B explicitly reject classical heavenly/earthly dualism and the church-as-separate-people model.
- Axis O: Walvoord is future-only with type/antitype foreshadowing; B&B are explicit already/not-yet partial fulfillment advocates.

But there are two divergence problems:

- `blaising-bock-progressive-dispensationalism.json` does **not serialize Axis B** even though its own `commitmentProfile` says the fourth-kingdom identification is tentative. That means the Walvoord/B&B divergence or non-divergence on B is narrated but not modeled.
- The same file drifts from the locked axis map: it uses `E` for apocalyptic/current-events decoding, `F` for Son of Man, and `J` for Millennium, whereas the taxonomy in the locked survey/spec uses `E = Revelation approach`, `F = Millennium`, `J = Son of Man`. This is a WS1 blocker because downstream code will misread the positions.

Hoekema vs Riddlebarger divergence **is preserved** in the 2026-04-23 survey: Hoekema is explicitly heaven-located amillennialism; Riddlebarger is explicitly earth-located church-militant amillennialism.

## 5. Commitment Calibration

Strong commitments generally look well calibrated when the scholar is stating a programmatic or signature claim:

- Walvoord A/B/C/K/N: calibrated as `strong`.
- Blaising & Bock H/I/K/O: calibrated as `strong`.
- Durham C/E/J: calibrated as `strong`.
- Collins A/B/J/L: calibrated as `strong`.

The main calibration issue is not widespread overstatement of confidence; it is **missing tentative serialization**:

- Collins: no tentative positions exposed.
- Walvoord: no tentative positions exposed.
- Durham: no tentative positions exposed.
- Blaising & Bock: one tentative item appears only in `commitmentProfile` (`B`), but there is no corresponding `positions[]` entry to audit or render.

So I could not perform the requested “five tentative spot-checks per file” because the files do not provide them. That is itself a finding: the commitment-gradient machinery exists in prose summary form, but the new files do not yet operationalize tentative commitments as first-class positions.

Specific calibration findings:

- `collins-hermeneia-daniel.json`, Axis H, `strong`: commitment is plausible, but the stored quote is thinner than the rationale. Add more quote support or narrow the rationale.
- `durham-revelation.json`, Axis N, `strong`: commitment is plausible, but the single stored quote is too thin for the full rationale.
- `blaising-bock-progressive-dispensationalism.json`, tentative Axis B: the tentative label itself looks right; the problem is that it is missing from `positions[]`.

## 6. Pilot Coverage Matrix

| Pilot axis | Covered by new scholars? | Scholar(s) |
|---|---|---|
| A | ✓ | Collins, Walvoord |
| B | ✓ | Collins, Walvoord |
| C | ✓ | Collins, Walvoord, Blaising & Bock, Durham |
| E | ✓ | Walvoord, Durham |
| F | ✓ | Walvoord, Durham |
| H | ✓ | Collins, Walvoord, Blaising & Bock |
| J | ✓ | Collins, Walvoord, Durham |
| K | ✓ | Walvoord, Blaising & Bock |
| L | ✓ | Collins, Walvoord, Durham |
| N | ✓ | Walvoord, Durham |
| O | ✓ | Collins, Walvoord, Blaising & Bock |

Zero-coverage pilot axes after merging: **none**.

Important caveat: the B&B file’s axis-letter drift means its data cannot be trusted for automated axis-based merging until the letters are corrected, even though the underlying content is useful.

## 7. Page-Discipline Audit

This passes.

- All four new scholar files use `frontend.page: null` and `frontend.pageEnd: null` throughout.
- That matches the metadata investigation: Collins Hermeneia, Walvoord, Blaising & Bock, and Durham all lack accessible embedded milestone indexes for printed page extraction.
- I found **no fabricated page numbers** in the new scholar JSONs.

## 8. Voice Audit

The new files are mostly compatible with the spec’s charitable intent, but they do **not yet consistently embody the three editorial habits**.

- Habit 1, “name the kind of disagreement”: mostly absent. The rationales usually describe the position but rarely label the disagreement as textual, inferential, or systemic.
- Habit 2, pastoral de-escalation: mixed. B&B comes closest; Durham is the farthest from it because the rationale reproduces anti-Rome polemical energy without much framing.
- Habit 3, text / inference / system distinction: only partially present. Walvoord and Collins often blend text claims with system claims in one paragraph; B&B is best at marking system-level moves.

This is not a hard WS0 failure, but it means WS1/WS6 should not assume these rationales are publication-ready prose.

## 9. Recommended Fixes

### Must change before WS1

1. **Normalize `blaising-bock-progressive-dispensationalism.json` to the locked axis map.** The current `E`/`F`/`J` usage is inconsistent with the taxonomy and will miswire ingestion.
2. **Serialize B&B Axis B explicitly** as a tentative position, since the file already claims tentative uncertainty in `commitmentProfile`.
3. **Tighten or re-cite over-claimed rationales** at minimum for Collins Axis C, Collins Axis H, and Durham Axis N. The quotes are real, but the rationale currently says more than the citation set proves.
4. **Decide how tentative commitments are represented in data, not just in `commitmentProfile`.** Right now the gradient is narratively acknowledged but structurally under-modeled.

### Can be deferred

1. Repair the four legacy verification failures in `2026-04-23-daniel-interpretive-taxonomy-survey.md`.
2. Add more explicit disagreement typing (`textual` / `inferential` / `systemic`) to rationales.
3. Add pastoral-de-escalation framing, especially anywhere Durham is summarized for lay use.
4. Backfill more reading-rule serialization if WS1 wants strict separation of text axes from higher-order hermeneutical rules.

---

## 10. Post-audit fixes (applied 2026-04-24)

The "must change before WS1" items were applied in-session after this audit ran; status of each:

1. **B&B axis-letter remap — done.** `blaising-bock-progressive-dispensationalism.json` now uses
   the locked letters: `L` for Apocalyptic hermeneutic (was `E`), `J` for Son of Man (was `F`),
   `F` for Millennium (was `J`). `commitmentProfile` updated in lockstep. Re-sweep confirms 22/22
   citations still verify.
2. **B&B Axis B serialized — done.** A tentative `positions[]` entry for Axis B ("Fourth
   kingdom: Unspecified/generic") is now present, with `citations: []` and a rationale explaining
   that B&B discuss Gentile kingdoms corporately in the surveyed material rather than naming a
   specific empire. This establishes the pattern for tentative-without-quote commitments:
   serialize them as `positions[]` entries with empty `citations`.
3. **Rationale tightening — done** for Collins C, Collins H, and Durham N. Each rationale now
   stays within what the stored quotes actually prove and explicitly names the claims that are
   scholar-level summary rather than verbatim-cited. No new fabrication introduced.
4. **Tentative-position data-shape decision — adopted.** The pattern in #2 above is the
   operational rule: tentative and hedged commitments that the scholar holds without supplying a
   verbatim quote become `positions[]` entries with `commitment: "tentative"` and
   `citations: []`. The `commitmentProfile` remains the summary index.

After these four changes the WS0 deliverables meet the "pass" bar — no conditions remain before
WS1 can begin ingestion.
