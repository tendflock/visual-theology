# WS0.5-6 Claim-vs-Quote Warrant Audit

## 1. Verdict

**pass-with-conditions.** The four WS0b files pass the fabrication layer: the cited quotations are real per the current 97/97 verification sweep. They do not yet pass the stricter warrant-label layer. The dominant defect is not false citation but overconfident `directly-quoted` labeling where the quote functions as a pointer into a broader argument, especially in Collins and Durham. Walvoord is the strongest file; Blaising & Bock are strong on their own programmatic identity but thin where the Daniel-specific referent is absent. Before WS1 treats citation labels as semantically meaningful, the relabels below should be applied or the rationales narrowed and re-cited.

## 2. Per-scholar relabeling table

### Collins, `collins-hermeneia-daniel.json`

| file | axis | current `supportStatus` | proposed `supportStatus` | reason |
|---|---:|---|---|---|
| `collins-hermeneia-daniel.json` | A | `directly-quoted` | `summary-inference` | The quote only says "we can date Daniel 7 rather precisely to late 167 b.c.e."; the rationale adds 7:25, relation to chs. 8-12, whole-book Maccabean setting, and pseudonymity. |
| `collins-hermeneia-daniel.json` | B | `directly-quoted` | `summary-inference` | The quote supports the Babylon-Media-Persia-Greece sequence, but not the Seleucid culmination, Antiochus IV, ten horns, or little-horn details asserted in the rationale. |
| `collins-hermeneia-daniel.json` | C | `directly-quoted` | `paraphrase-anchored` | The Antiochus coinage quote supports divine epithets, but the link to "great words against the Most High" is an exegetical move beyond the fragment. |
| `collins-hermeneia-daniel.json` | C | `directly-quoted` | `paraphrase-anchored` | "The reference here is to the disruption of the cultic calendar" points into Collins's discussion of 7:25 but is not self-contained proof of the full "change times and law" claim. |
| `collins-hermeneia-daniel.json` | D | `directly-quoted` | `summary-inference` | The round-number quote does not directly support the Joshua/Onias/Antiochus/covenant/half-week identifications. |
| `collins-hermeneia-daniel.json` | D | `directly-quoted` | `summary-inference` | "The modern critical interpretation requires..." anchors the Antiochene horizon but not the rationale's full named-referent chronology. |
| `collins-hermeneia-daniel.json` | H | `directly-quoted` | `summary-inference` | The quote supports divine judgment on the present gentile kingdom, while the rationale adds Semeia-14, eternal divine kingdom, Chaoskampf, and two-tier angelic framing. |
| `collins-hermeneia-daniel.json` | J | `directly-quoted` | `paraphrase-anchored` | "The view that Michael..." names the history of the view, not by itself Collins's adoption of it; the next citation does the direct warrant work. |
| `collins-hermeneia-daniel.json` | L | `directly-quoted` | `summary-inference` | "The parallels are of significance..." supports one methodological axiom, not the full Gunkel/Canaanite/diachronic method summary. |
| `collins-hermeneia-daniel.json` | O | `directly-quoted` | `summary-inference` | "served as a paradigm" supports reuse, but the rationale names Antiochus, 4 Ezra, Revelation, and non-layered fulfillment as a synthesis. |
| `collins-hermeneia-daniel.json` | P | `directly-quoted` | `summary-inference` | The quote classifies Dan 7 as a symbolic dream vision; it does not directly prove Collins as Semeia architect or that non-apocalyptic readings are category mistakes. |
| `collins-hermeneia-daniel.json` | crossBook: Rev 1/13/14/17 | `directly-quoted` | `summary-inference` | The quote only supports Christian identification of the humanlike figure with Jesus and second coming hope; the summary adds Rev 1 fusion, Old Greek error, beast reuse, and 4 Ezra retargeting. |

### Walvoord, `walvoord-daniel.json`

| file | axis | current `supportStatus` | proposed `supportStatus` | reason |
|---|---:|---|---|---|
| `walvoord-daniel.json` | E | `directly-quoted` | `paraphrase-anchored` | The Revelation 6-19 catastrophe quote supports Walvoord's end-time scenario but only indirectly supports the rationale's "parallel extension of Daniel" claim. |
| `walvoord-daniel.json` | O | `directly-quoted` | `summary-inference` | The future-fulfillment quote supports futurism, but the rationale's chapter-by-chapter past/future structure and Antiochus-as-type distinction draw on more than this fragment. |
| `walvoord-daniel.json` | O | `directly-quoted` | `summary-inference` | The Dan 11:36 quote supports future fulfillment after v. 36, not the whole single-fulfillment model summarized in the rationale. |

Axis B, the canary case, should remain `directly-quoted`: the cited quotes directly support Rome, a yet-future fourth-empire stage, and Rev 13/17 locking the ten kings to Rome's final stage.

### Blaising & Bock, `blaising-bock-progressive-dispensationalism.json`

| file | axis | current `supportStatus` | proposed `supportStatus` | reason |
|---|---:|---|---|---|
| `blaising-bock-progressive-dispensationalism.json` | J | `directly-quoted` | `paraphrase-anchored` | The Dan 7 quote says Daniel sees "One like a Son of Man"; it does not directly state individual Messiah or saints-as-beneficiaries. |
| `blaising-bock-progressive-dispensationalism.json` | crossBook: Rev 20 | `directly-quoted` | `summary-inference` | The quote only says Rev 20 is the sole explicit intermediate-millennium text; the summary adds two resurrections, mortal nations, final release, judgment, and 1 Cor 15. |
| `blaising-bock-progressive-dispensationalism.json` | crossBook: Matt 13 | `directly-quoted` | `summary-inference` | The quote supports a pre-consummation kingdom stage but not the wheat-and-tares, mustard-seed, and leaven details. |
| `blaising-bock-progressive-dispensationalism.json` | crossBook: Acts 2/Ps 110 | `directly-quoted` | `paraphrase-anchored` | The quote directly supports heavenly enthronement, but not by itself the "signature progressive-dispensational move resisted by classical/revised dispensationalists" contrast. |

Axis K, the canary case, is adequately warranted: the citations directly support non-separate church identity, holistic redemption, the classical heavenly/earthly contrast, and future Israel.

### Durham, `durham-revelation.json`

| file | axis | current `supportStatus` | proposed `supportStatus` | reason |
|---|---:|---|---|---|
| `durham-revelation.json` | C | `directly-quoted` | `paraphrase-anchored` | "the Pope and his Kingdom, supposing him to be Antichrist" is a pointer inside Durham's argument, not a standalone assertion as strong as the rationale's papal-Antichrist claim. |
| `durham-revelation.json` | C | `directly-quoted` | `paraphrase-anchored` | "Roman Empire under its seventh and last government" needs the surrounding exposition to yield "the papacy" and the rejected rival candidates. |
| `durham-revelation.json` | E | `directly-quoted` | `summary-inference` | The two quotes support future prophecy and Roman seventh government, but not the dated continuous-history scheme with 600, 750/766, Otho III, and Charles IV. |
| `durham-revelation.json` | E | `directly-quoted` | `summary-inference` | Same as above: "things which must shortly come to passe" is not direct proof of the full historicist chronology. |
| `durham-revelation.json` | L | `directly-quoted` | `summary-inference` | The quotes support future orientation and Danielic beast imagery, not the full last-Will, immediate-beginning, end-of-world, Bellarmine/Daniel/Ezekiel argument. |
| `durham-revelation.json` | L | `directly-quoted` | `summary-inference` | The Daniel-beast quote is an anchor for the hermeneutic, not direct proof of the whole rationale. |
| `durham-revelation.json` | N | `directly-quoted` | `summary-inference` | The post-audit rationale is now honest that the quote only supplies the beast-template; the citation label should match that summary-pointer posture. |
| `durham-revelation.json` | F | `directly-quoted` | `summary-inference` | The first Rev 20 quote supports church-wide reigning, but not physical-resurrection denial, final loosing, modern postmillennial classification, or Durham's hedging. |
| `durham-revelation.json` | F | `directly-quoted` | `summary-inference` | The computation quote supports the starting point, not the full millennium taxonomy asserted in the rationale. |
| `durham-revelation.json` | crossBook: Daniel 7/Revelation | `directly-quoted` | `summary-inference` | The Daniel-beast quote supports a template only; it does not directly prove Antiochus-to-Antichrist application or papal succession to Daniel's beasts. |
| `durham-revelation.json` | crossBook: Daniel 7/Revelation | `directly-quoted` | `summary-inference` | The Son of Man quote supports Durham's Christ identification at Rev 14:14, but not the broader Daniel 7:9-14/Revelation mapping. |

## 3. Over-claim findings

1. **Collins §A overbuilds a one-line date quote.** At `collins-hermeneia-daniel.json:31`, the rationale asserts late 167 BCE, 7:25 as Antiochene cult suppression, composition before chs. 8-12, whole-book Maccabean origin, and apocalyptic pseudonymity. The only citation at `:49` says, "we can date Daniel 7 rather precisely to late 167 b.c.e." The date is warranted; the rest needs more citations or should be moved into an explicitly uncited summary note.

2. **Collins §D names too many historical referents for two broad chronology quotes.** The rationale at `:141` identifies Joshua, Onias III, Antiochus, Hellenizing Jews, and half-week suppression. The quotes at `:159` and `:179` support schematic seventy weeks and the Antiochene horizon, but not those specific referents. This is a classic "verified quote exists, historical mapping not warranted by that quote set" case.

3. **Collins §P turns genre classification into a polemical exclusion.** The quote at `:389` says "Daniel 7 is a symbolic dream vision..." That supports apocalyptic genre classification. The rationale at `:371` further says non-apocalyptic long-range predictive readings are "category-mistaken"; that may be Collins-compatible, but it is not directly readable from the quote.

4. **Walvoord §N is mostly right but imports uncited links.** The rationale at `walvoord-daniel.json:712` mentions 2 Thessalonians 2 and the Olivet Discourse as decisive. Its three citations at `:730`, `:750`, and `:770` support Rev 4-5, Rev 13, and the Daniel 11/Revelation 13 identification. They do not cite 2 Thessalonians 2 or Matthew 24 in that position, even though the cross-book section later has Matthew quotes.

5. **Blaising & Bock §B is structurally honest but academically uncited.** The rationale at `blaising-bock-progressive-dispensationalism.json:31` says their reticence reflects progressive dispensationalism's resistance to classical specificity. Since `citations: []`, the absence of a fourth-kingdom identification is represented, but the explanation of why they are reticent is an uncited interpretive attribution.

6. **Blaising & Bock §J overstates the first quote.** The rationale at `:420` says "individual Son of Man = Messiah, saints are the corporate beneficiaries." The first quote at `:438` only says Daniel envisions "One like a Son of Man" coming before the Ancient of Days. The second quote at `:458` supports Jesus' appropriation, but the saints-beneficiaries claim is not cited.

7. **Durham §C and §E carry detailed historicist machinery with thin direct support.** The papal-Antichrist core is well quoted (`durham-revelation.json:45`, `:85`), but the rationale at `:27` also invokes rejected rival candidates, Virgil, Ovid, Bellarmine, a nailed chair, and Reformed zeal. The historicist rationale at `:117` invokes 600, 750/766, Otho III, and Charles IV, while the quotes at `:135` and `:155` only support Roman seventh government and future prophetic scope.

8. **Durham cross-book remains the weakest high-risk item.** The rewritten Axis N rationale at `:217` is much safer because it admits the extra claims are not reproduced as quotes. The cross-book summary at `:326`, however, again asserts Antiochus-language applied to Antichrist and the seven-headed papal successor of Daniel's four beasts. Its quotes at `:343` and `:363` support Danielic beast grammar and Christ as Son of Man, not the full typological transfer.

## 4. Distinctive-moves audit

- **Collins:** No clear misattribution, but the Canaanite/Ugaritic "controlling background" and Semeia-priority moves are under-cited by the current stored fragments. They should be treated as scholar-level summaries unless backed by additional quotations.
- **Walvoord:** The "supernaturalism is the deciding question" move is a fair synthesis of the file's Axis A and L material, not a caricature. It should be presented as a synthesis, not as a quote-level claim. The Roman-fourth-kingdom canary is accurately represented.
- **Blaising & Bock:** "Adopts Ladd-style inaugurated eschatology" is not distinctive in origin; the distinctive move is progressive dispensational adoption of inaugurated eschatology while retaining national Israel and premillennial consummation. The pastoral Israel-state/antisemitism entry may be true to the book, but it is not warranted by the audited Daniel 7 citation set and needs a citation if retained.
- **Durham:** "Every beast-exposition begins by asserting the Daniel template" overstates the stored evidence; the file has one strong Rev 13 Daniel-template quote. The seven-hilled Rome and papal-Antichrist moves are tradition-consensus historicist positions Durham shares, not uniquely Durham's distinctive move, unless framed as his particular evidential deployment.

## 5. Cross-book audit

- **Collins, Rev 1/13/14/17:** Weak. The quote supports Christian appropriation of the humanlike figure as Jesus and second-coming hope. It does not support Rev 1 fusion, Old Greek textual error, Revelation's beasts, or 4 Ezra retargeting. Relabel `summary-inference` and add citations.
- **Walvoord, Rev 13/17:** Strong. The quotes directly support Rev 13/17 ten kings as future and the beast of Rev 13 as the same individual as Daniel's little horn/Dan 11 king.
- **Walvoord, Matthew 24:** Adequate for future orientation. The quotes directly support Christ treating the abomination as future; the "dominical endorsement of sixth-century Daniel" phrasing is a theological inference from "Daniel the prophet" and should be phrased cautiously.
- **Blaising & Bock, Rev 20:** Weak as labeled. The quote supports Rev 20 as the only explicit intermediate-millennium text, not the detailed two-resurrection sequence or 1 Cor 15 relation.
- **Blaising & Bock, Matt 13:** Weak as labeled. The quote supports a present stage before apocalyptic establishment, not the specific parable-by-parable claims.
- **Blaising & Bock, Acts 2/Ps 110:** Mostly adequate for heavenly Davidic enthronement; the classical/revised contrast needs a separate quote or `paraphrase-anchored` label.
- **Durham, Daniel 7 through Revelation 13/17:** Weak. The quotes establish Danielic beast grammar and Christ as Son of Man; they do not directly prove Antiochus-to-Antichrist typology or papal succession to Daniel's four-beast schema.

## 6. Methodology check

- **Walvoord** is the least thin file: many axes, multiple direct citations, and most strong commitments are well matched to their quote sets.
- **Collins** is academically rich but citation-thin relative to the density of the rationales. Several positions summarize complex Hermeneia arguments with one or two short fragments.
- **Blaising & Bock** are structurally compliant and excellent for progressive-dispensational self-definition, but thin as a Daniel 7 file: Axis B has no citations, and several cross-book claims summarize whole NT arguments from one representative quote.
- **Durham** is structurally compliant but academically the thinnest for Daniel 7 proper because the source is a Revelation commentary. That is acceptable as a historicist-Reformation primary voice only if cross-book claims are labeled as summary inferences, not direct Daniel exegesis.

## 7. Recommended fixes

1. **must-fix-before-WS1:** Apply the relabels in section 2, or narrow the affected rationales until each `directly-quoted` label only claims what the stored quote directly says.
2. **must-fix-before-WS1:** Rework Durham Axis N and Durham cross-book labels to `summary-inference`; add direct quotes for Antiochus-to-Antichrist typology and papal succession if those claims remain.
3. **must-fix-before-WS1:** Rework Collins Axis A, D, H, L, O, and P as summary/inference positions or add direct quotations for the specific named claims.
4. **must-fix-before-WS1:** For B&B Axis B, either keep it as a citationless tentative position but remove the uncited causal explanation of "reticence," or add a quote from B&B explaining the hermeneutical restraint.
5. **must-fix-before-WS1:** For cross-book entries, do not use `directly-quoted` unless the quote itself names both sides of the cross-book move.
6. **nice-to-have:** Add a short `notes` field or rationale sentence wherever `summary-inference` is used, naming exactly which adjacent sections/articles the inference draws on.
7. **nice-to-have:** Split long rationales into directly cited subclaims plus explicitly marked summary sentences so future audits can distinguish quotation proof from editorial synthesis.

---

## 8. Post-audit relabel — applied 2026-04-24 (same session)

The 30 relabel rows in §2 above were applied to the four WS0b scholar JSON files in
the same working session as the audit. No rationales were rewritten; only the
per-citation ``supportStatus`` tag was changed. The project's strict validator
(``tools/validate_scholar.py``) still accepts all four files, and the citation sweep
(``tools/sweep_citations.py``) still reports **97/97 verified** — the relabels move
citations between honest labels; they do not change which quotations exist in the
source texts.

Post-relabel ``supportStatus`` distribution across the 89 WS0b citations:

| label | count | % | meaning |
|---|---:|---:|---|
| `directly-quoted` | 59 | 66.3% | quote text alone warrants the rationale's sub-claim |
| `paraphrase-anchored` | 8 | 9.0% | verbatim quote, but functions as a pointer into a longer argument |
| `summary-inference` | 22 | 24.7% | rationale synthesizes across articles or beyond the quoted fragment |
| `uncited-gap` | 0 | 0% | (none used in the WS0b corpus) |

Per-scholar:

| scholar | DQ | PA | SI |
|---|---:|---:|---:|
| Walvoord | 35 | 1 | 2 |
| Blaising & Bock | 18 | 2 | 2 |
| Collins | 3 | 3 | 9 |
| Durham | 3 | 2 | 9 |

Why each relabel was applied exactly once to the citation(s) named in §2 (and not
extended uniformly across whole axes): earlier I over-applied four relabels (Walvoord
axis E [0] and [1]; Durham axis C [0] and [2]). Those were reverted to
``directly-quoted`` after the count discrepancy was flagged; the final distribution
above matches §2's 30 relabel rows exactly.

### Conditions that remain after relabel

The relabel closes the "verified quote exists but label overclaims" category of defect
that §1 of this audit flagged as the primary block. Specifically, applying the
relabels:

- Honestly reflects that Collins's Hermeneia file is rich in synthesis (22 of 89
  citations now `summary-inference` across the corpus, with 9 of those in Collins).
- Keeps Walvoord's programmatic-voice strength intact (33 of 38 Walvoord citations
  are still `directly-quoted` — Walvoord's prose really does pin specific claims to
  specific quotations).
- Acknowledges Durham's distinctive position as a Revelation-commentary primary
  voice being applied cross-book to Daniel (9 of 14 Durham citations are now
  `summary-inference`, matching the cross-book nature of the Daniel 7 pilot's use of
  his material).

What the relabel **does not** close:

1. The *nice-to-have* items in §7 — adding a `notes` field naming the adjacent
   sections each `summary-inference` citation actually draws on — remain deferred.
2. The warrant-level check for every citation (not just the 30 flagged here)
   against every line of rationale remains manual. A future expansion of the
   adversarial audit could widen the sample if a WS1 visualization depends on
   label precision more than the pilot does.
3. The legacy `2026-04-23-daniel-interpretive-taxonomy-survey.md` has not been
   re-audited at the warrant-label level — only its four quote-not-found
   failures from the WS0 sweep were repaired in WS0.5-3. Applying the same
   scrutiny to the nine second-pass scholars is a future workstream.

With these conditions noted in writing, the WS0b corpus now meets the "pass" bar
this audit's §1 held open.
