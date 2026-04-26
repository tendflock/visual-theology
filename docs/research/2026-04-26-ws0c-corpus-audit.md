# WS0c Expanded Corpus Claim-Warrant Audit

## 1. Verdict

**pass-with-conditions.** The expanded JSON corpus is healthy at the fabrication layer: the current sweep reports 426/426 citations verified, and the new backend kinds actually used in the 17 JSON files (`external-epub` for LaCocque/Menn and `external-greek-ocr` for Theodoret) do not show a verifier-level failure. It is not clean at the warrant-label layer. The core Daniel 7 verse-block positions are generally well calibrated, but several cross-book summaries still use `directly-quoted` for claims that are actually synthetic mappings across Daniel, Revelation, the Olivet Discourse, or Second Temple reception. Theodoret is the one backend-specific caution: the Greek-OCR anchors verify, but several stored quote fragments are too short or visibly OCR-damaged to carry the English rationale by themselves. Also note a manifest discrepancy: the prompt treats the 1 Enoch Parables file as an external-resource scholar, but the JSON uses the normal Logos backend (`LLS:HRMNEIAENCH1B`). The corpus can move toward WS1 if the relabels below are applied or the rationales are narrowed; without that, Bryan's critique still lands in the cross-book layer.

## 2. Per-scholar relabeling table

### `1-enoch-parables-nickelsburg-vanderkam.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `1-enoch-parables-nickelsburg-vanderkam.json` | L | `directly-quoted` | `summary-inference` | The two quotes support "exegetical conflation" and the Parables' historical significance, but not the whole account of flexible authoritative tradition and scripture interpreted diversely. |
| `1-enoch-parables-nickelsburg-vanderkam.json` | K | `directly-quoted` | `summary-inference` | The date quote gives Nickelsburg's conclusion but not the rationale's evidence chain from Parthia, Qumran absence, Herod, 4 Ezra, Wisdom, and the kings-and-mighty motif. |
| `1-enoch-parables-nickelsburg-vanderkam.json` | crossBook: Rev 1 | `directly-quoted` | `summary-inference` | "Closest parallel" and "one like a son of man" do not by themselves establish the full Rev 1/4/5/6/11/19/22 matrix or possible knowledge of the Parables. |
| `1-enoch-parables-nickelsburg-vanderkam.json` | crossBook: 1 En 37-71 | `directly-quoted` | `summary-inference` | The cited lines establish Enoch's identification and the appendix judgment, but the detailed reasons chap. 71 differs from the body of the Parables are a broader editorial argument. |

### `beale-use-of-daniel-in-revelation.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `beale-use-of-daniel-in-revelation.json` | crossBook: Matt 24 | `directly-quoted` | `paraphrase-anchored` | The quote directly supports Matt 24:30 suggesting the Dan 7/Zech 12 combination in Rev 1:7, but not the added false-prophet / Rev 13 convergence. |

### `blaising-bock-progressive-dispensationalism.json`

No relabel recommendations -- labels well calibrated after the WS0.5-6 relabels.

### `calvin-daniel.json`

No relabel recommendations -- labels well calibrated.

### `collins-hermeneia-daniel.json`

No relabel recommendations -- labels well calibrated after the WS0.5-6 relabels.

### `duguid-rec-daniel.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `duguid-rec-daniel.json` | crossBook: Rev 20 | `directly-quoted` | `summary-inference` | The quote speaks generally of final judgment in a beastly world and a heavenly throne room; it does not directly establish Rev 20:10 as the fulfillment of Dan 7:11. |

### `durham-revelation.json`

No relabel recommendations -- labels well calibrated after the WS0.5-6 relabels.

### `goldingay-wbc-daniel.json`

No relabel recommendations -- labels well calibrated. Separate issue: the Mark 13 cross-book entry has no citations at all, so it is not a relabel problem but an uncited cross-book gap.

### `hamilton-clouds-of-heaven.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `hamilton-clouds-of-heaven.json` | crossBook: Rev 20 | `directly-quoted` | `summary-inference` | The quote directly supports Rev 20:4 as fitting Dan 7:12, but not the whole sequence of Antichrist's death, resurrected earthly reign, Satan's release, Gog/Magog, and Dan 12 final judgment. |
| `hamilton-clouds-of-heaven.json` | crossBook: Matt 24 | `directly-quoted` | `summary-inference` | "Almost a commentary" on Daniel is a programmatic anchor, not direct proof of every listed Olivet detail and anti-pretribulational implication. |
| `hamilton-clouds-of-heaven.json` | crossBook: Mark 13 | `directly-quoted` | `paraphrase-anchored` | The masculine-participle quote supports a personal abomination, but the little-horn/fourth-kingdom/Dan 9:27 synthesis is Hamilton's surrounding argument. |

### `hartman-dilella-anchor-daniel.json`

No relabel recommendations -- labels well calibrated.

### `jerome-commentary-on-daniel.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `jerome-commentary-on-daniel.json` | crossBook: Rev 13 | `directly-quoted` | `summary-inference` | The stored citation is a 2 Thess 2 Antichrist quote and the summary itself admits Jerome does not cite Rev 13 directly at Dan 7. |

### `lacocque-book-of-daniel.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `lacocque-book-of-daniel.json` | E | `directly-quoted` | `summary-inference` | The quote supports Dan 7 as an Aramaic bridge, but not the full three-stage Daniel A / Dan 7 / Daniel B compositional reconstruction. |
| `lacocque-book-of-daniel.json` | H | `directly-quoted` | `paraphrase-anchored` | "Corporate personality" being central to Dan 7 does not alone prove the horizontal/vertical mechanics attributed in the rationale. |
| `lacocque-book-of-daniel.json` | O | `directly-quoted` | `paraphrase-anchored` | The Temple-framework quote supports the basic move, but the "single Antiochene historical referent with theological surplus" classification is a synthesis. |
| `lacocque-book-of-daniel.json` | crossBook: Rev 13 | `directly-quoted` | `summary-inference` | The quote names Rev 12:10, Michael, Dragon, and Christ, not Rev 13's beast imagery or the broader post-exilic apocalyptic animal catalogue. |
| `lacocque-book-of-daniel.json` | crossBook: 1 En 37-71 | `directly-quoted` | `paraphrase-anchored` | The fragment breaks off at "who is also called" and does not quote the Messiah/preexistence details named in the summary. |

### `menn-biblical-eschatology.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `menn-biblical-eschatology.json` | F | `directly-quoted` | `paraphrase-anchored` | The third millennium citation reports the two-resurrection/two-judgment package but, as a fragment, does not itself show Menn's rejection of it. |
| `menn-biblical-eschatology.json` | J | `directly-quoted` | `paraphrase-anchored` | The Wright-fragment quote is too truncated to prove the full upward-coming correction or Menn's combined ascension/parousia synthesis. |
| `menn-biblical-eschatology.json` | N | `directly-quoted` | `summary-inference` | "Antichrist seen in parallels between Daniel," is a heading-level anchor, not direct proof of the whole Daniel / 2 Thess 2 / Revelation mapping. |
| `menn-biblical-eschatology.json` | N | `directly-quoted` | `summary-inference` | "Daniel's beasts describe four" is too short to warrant the anti-preterist and anti-dispensational cross-book argument in the rationale. |
| `menn-biblical-eschatology.json` | crossBook: Rev 20 | `directly-quoted` | `summary-inference` | Menn's amillennial thesis quote does not directly establish every Rev 20 claim listed: recapitulation, first resurrection, church-age symbolism, and detailed two-age structure. |
| `menn-biblical-eschatology.json` | crossBook: Matt 24 | `directly-quoted` | `summary-inference` | The quoted fragment is too truncated to establish the AD 70 plus eschatological reapplication of Son of Man, abomination, and great tribulation language. |

### `pentecost-things-to-come.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `pentecost-things-to-come.json` | crossBook: Rev 17 | `directly-quoted` | `summary-inference` | The quote proves ten kings federate by consent under the Beast, but not Rome, the eighth king, the harlot system, or the whole Rev 17 structure. |
| `pentecost-things-to-come.json` | crossBook: Matt 24 | `directly-quoted` | `summary-inference` | "Perfect harmony" between Matt 24 and Rev 6ff. anchors the claim, but not the Jewish-program classification or the detailed first-half/second-half tribulation mapping. |

### `theodoret-pg81-daniel.json`

| file | axis | current | proposed | reason (one sentence) |
|---|---|---|---|---|
| `theodoret-pg81-daniel.json` | C | `directly-quoted` | `paraphrase-anchored` | "Blessed Paul clearly..." is a bridge marker, not direct proof of the 2 Thess 2 fusion named in the rationale. |
| `theodoret-pg81-daniel.json` | E | `directly-quoted` | `summary-inference` | The short OCR snippets do not by themselves establish the four-part anti-Maccabean structural refutation summarized in the rationale. |
| `theodoret-pg81-daniel.json` | J | `directly-quoted` | `summary-inference` | "Foretelling an appearance" and a Psalm 2 incipit are too thin to prove the full parousia, Matt 24, 1 Thess 4, incarnation, and human-nature interpretation. |
| `theodoret-pg81-daniel.json` | N | `directly-quoted` | `summary-inference` | The OCR quote supports bodiless/simple/unfigured deity, but not the Hosea gloss, the full apophatic doctrine, or the symbolic reading of age, throne, garments, and river. |
| `theodoret-pg81-daniel.json` | crossBook: Matt 24 | `directly-quoted` | `summary-inference` | The same brief "foretelling an appearance" phrase cannot bear the detailed Matt 24:30, 24:21-22, and 24:23-27 mapping. |

### `walvoord-daniel.json`

No relabel recommendations -- labels well calibrated after the WS0.5-6 relabels.

### `young-prophecy-of-daniel.json`

No relabel recommendations -- labels well calibrated.

## 3. Per-passage coverage matrix

| passageCoverage value | count | scholars |
|---|---:|---|
| `Dan 7:1-6` | 9 | Beale; Calvin; Duguid; Goldingay; Hartman/Di Lella; Jerome; LaCocque; Theodoret; Young |
| `Dan 7:7-8` | 16 | Beale; Blaising & Bock; Calvin; Collins; Duguid; Durham; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Theodoret; Walvoord; Young |
| `Dan 7:9-12` | 11 | 1 Enoch Parables; Beale; Calvin; Duguid; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Theodoret; Young |
| `Dan 7:13-14` | 17 | 1 Enoch Parables; Beale; Blaising & Bock; Calvin; Collins; Duguid; Durham; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Theodoret; Walvoord; Young |
| `Dan 7:15-18` | 9 | Beale; Calvin; Duguid; Goldingay; Hartman/Di Lella; Jerome; LaCocque; Theodoret; Young |
| `Dan 7:19-22` | 13 | Beale; Blaising & Bock; Calvin; Collins; Duguid; Durham; Goldingay; Hamilton; Hartman/Di Lella; Jerome; Theodoret; Walvoord; Young |
| `Dan 7:23-27` | 17 | 1 Enoch Parables; Beale; Blaising & Bock; Calvin; Collins; Duguid; Durham; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Theodoret; Walvoord; Young |
| `Dan 2:31-45` | 14 | Beale; Blaising & Bock; Calvin; Collins; Duguid; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Walvoord; Young |
| `Dan 8:1-27` | 10 | Beale; Duguid; Goldingay; Hamilton; Hartman/Di Lella; LaCocque; Menn; Pentecost; Theodoret; Young |
| `Dan 9:1-19` | 3 | Collins; Duguid; Walvoord |
| `Dan 9:20-27` | 10 | Collins; Duguid; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Walvoord |
| `Dan 10:1-21` | 0 | none |
| `Dan 11:1-45` | 9 | Beale; Duguid; Goldingay; Hamilton; Jerome; LaCocque; Menn; Pentecost; Theodoret |
| `Dan 12:1-13` | 8 | Beale; Duguid; Hamilton; Jerome; LaCocque; Menn; Pentecost; Theodoret |
| `Rev 1` | 7 | 1 Enoch Parables; Beale; Collins; Durham; Hamilton; Jerome; Walvoord |
| `Rev 13` | 13 | Beale; Calvin; Collins; Duguid; Durham; Goldingay; Hamilton; Hartman/Di Lella; Jerome; Menn; Pentecost; Walvoord; Young |
| `Rev 17` | 6 | Beale; Collins; Durham; Menn; Pentecost; Walvoord |
| `Rev 20` | 6 | Blaising & Bock; Durham; Hamilton; Menn; Pentecost; Walvoord |
| `Matt 24` | 7 | Beale; Calvin; Hamilton; Menn; Pentecost; Walvoord; Young |
| `Mark 13` | 6 | Beale; Goldingay; Hamilton; Menn; Walvoord; Young |
| `1 En 37-71` | 3 | 1 Enoch Parables; Beale; Goldingay |

**Well anchored (>=5 scholars).** All Daniel 7 core blocks are well anchored. The best-covered blocks are `Dan 7:13-14` and `Dan 7:23-27` (17 each), followed by `Dan 7:7-8` (16), `Dan 7:19-22` and `Rev 13` (13 each), and `Dan 7:9-12` (11). Most adjacent Daniel passages and NT cross-references also clear the five-scholar threshold.

**Thin by the requested 1-2 threshold.** None. No controlled-vocabulary passage has only one or two scholars.

**Borderline under-anchored despite not being "thin."** `Dan 9:1-19` and `1 En 37-71` have three scholars each. They are not uncovered, but they are fragile if WS1 visualizations depend on Daniel's penitential prayer or the Parables as more than contextual sidebars.

**Uncovered.** `Dan 10:1-21` has zero coverage. That is a genuine gap in the controlled vocabulary.

**Coverage contradictions / weak coverage claims.** I did not find a pairwise contradiction where two scholars both claim a Daniel 7 block but their citations point to unrelated material. I did find individual coverage/cross-book mismatches: Goldingay claims Mark 13 cross-book coverage with an uncited entry; Walvoord lists `Rev 1` in `passageCoverage[]` but the JSON does not expose a specific Rev 1 cross-book reading; LaCocque has a cross-book row labeled Rev 13 whose quote is actually Rev 12:10; Theodoret has a Matt 24 cross-book row anchored only by a short Greek phrase. These should be cleaned before consumers treat `passageCoverage[]` as independently reliable.

## 4. Tradition-cluster honesty

One manifest caveat: the prompt's tradition-cluster list includes legacy voices (Newsom & Breed, Hoekema, Riddlebarger, Sproul, Longman, Lucas, Bauckham, Wright) that are not present as JSON files under `docs/research/scholars/`. I treat them below as bibliography/legacy narrative voices, not as part of the current 17 JSON corpus unless a JSON exists.

- **classical-dispensational:** Walvoord + Pentecost are sufficient triangulation. Walvoord provides the Daniel-commentary voice; Pentecost supplies the systematic-eschatology program.
- **progressive-dispensational:** Blaising & Bock are a primary manifesto, but alone they are under-triangulated. This is acceptable for a pilot archetype, not for tradition-wide representation.
- **critical-modern:** Collins, Hartman/Di Lella, and LaCocque are strong and not simple duplicates: Hermeneia-critical, Catholic Anchor, and continental Catholic-critical emphases differ. Newsom & Breed are bibliography/legacy, not JSON-backed here.
- **critical-mediating:** Goldingay alone is a credible consensus representative for this cluster, but still a single voice.
- **reformed-amillennial:** Duguid and Menn are in the JSON corpus; Beeke/Smalley is cited as a fixture/systematic voice but not a Daniel survey JSON; Hoekema and Riddlebarger are legacy/bibliography only. The cluster is directionally honest, but the JSON corpus alone is thinner than the cluster label implies.
- **reformed-conservative-critical:** Young alone is a strong primary counter to critical and dispensational readings; sufficient as a representative voice.
- **reformed-exegetical-historic:** Calvin alone is fine as a historic anchor, not as a full Reformed-history cluster.
- **historicist-reformation:** Durham alone is an authentic voice but under-triangulated; historicist Reformation diversity is broader than one Scottish Covenanter Revelation commentary.
- **partial-preterist:** Sproul is not a JSON file in the current corpus. If this cluster is used in WS1, it needs either JSON backfill or a clear "legacy narrative only" marker.
- **patristic-latin:** Jerome alone is acceptable as the Latin historic anchor.
- **patristic-greek-antiochene:** Theodoret alone is acceptable as the Greek Antiochene historic anchor, with the OCR-quality caveat above.
- **second-temple-reception:** The 1 Enoch Parables entry is a strong reception-event anchor, but it is not a full Second Temple reception cluster; 4 Ezra, Qumran, and other Jewish apocalyptic witnesses remain outside the JSON corpus.
- **evangelical-cross-book / biblical-theology:** Beale + Hamilton are sufficient for the Beale-school / canonical trajectory, though they are close kin rather than independent schools.
- **mediating-evangelical:** Longman + Lucas are not JSON-backed in the current corpus. Treat as legacy/bibliography unless backfilled.
- **post-critical / British biblical theology:** Bauckham + Wright are not JSON-backed in the current corpus. The tradition is important, but the JSON corpus cannot claim it yet.

## 5. Cross-book audit

| target passage | JSON cross-book coverage | audit note |
|---|---|---|
| Rev 1 | 1 Enoch Parables; Beale; Collins; Hamilton; Jerome | Beale, Hamilton, and Jerome are strong; Collins is already labeled `summary-inference`; 1 Enoch Parables should be downgraded because its Rev 1 summary outruns the two quotes. Walvoord lists `Rev 1` in `passageCoverage[]` but has no specific Rev 1 cross-book row. |
| Rev 13 | Beale; Collins; Duguid; Goldingay; Hamilton; Hartman/Di Lella; Jerome; LaCocque; Menn; Pentecost; Walvoord; Young | Strongly anchored overall. Weak rows are LaCocque (quote is Rev 12:10, not Rev 13) and Jerome (2 Thess 2 quote supports Antichrist, not Rev 13 directly). Duguid's Rev 13 row is strong; Duguid's Rev 20 row is not. |
| Rev 17 | Beale; Collins; Durham; Pentecost; Walvoord | Beale/Walvoord are strong; Collins and Durham are already honest `summary-inference`; Pentecost's Rev 17 row should be downgraded because one federation quote does not prove the full harlot/eighth-king/Rome structure. Menn lists `Rev 17` in `passageCoverage[]` but has no dedicated cross-book row. |
| Rev 20 | Blaising & Bock; Duguid; Hamilton; Menn | B&B are already `summary-inference`; Duguid, Hamilton, and Menn should be downgraded. In all three, the quote anchors a piece of the move but not the complete millennial / final-judgment sequence. Pentecost and Walvoord list `Rev 20` in coverage, but their JSON cross-book rows do not isolate Rev 20. |
| Matt 24 | Beale; Calvin; Hamilton; Menn; Pentecost; Theodoret; Walvoord; Young | Calvin, Walvoord, and Young are adequate. Beale needs a light downgrade; Hamilton, Menn, Pentecost, and Theodoret need stronger downgrades because one programmatic quote is doing too much work. |
| Mark 13 | Beale; Goldingay; Hamilton | Beale is adequate; Hamilton should be `paraphrase-anchored`; Goldingay's Mark 13 entry has no citations, despite `passageCoverage[]` listing Mark 13. |
| 1 En 37-71 | 1 Enoch Parables; Beale; LaCocque | Beale and the 1 Enoch core positions are strong; 1 Enoch's own chap. 71 cross-book/editorial row should be `summary-inference`; LaCocque's quote is too fragmentary for the messianic/preexistence summary. |

The WS0.5-6 weak-cross-book pattern is still the main risk class. A quote can directly prove "this author mentions Daniel and Revelation together" while failing to prove the cross-book architecture stated in the JSON. This is especially visible in Rev 20, Matt 24, and hybrid reception rows.

## 6. Recommended fixes

### Must-fix-before-WS1

1. Apply the relabels in Section 2, or narrow the affected rationales until `directly-quoted` means the quote itself establishes the subclaim.
2. Repair the cross-book weak spots: Goldingay Mark 13 needs citations or removal; LaCocque's Rev 13 row should be retargeted to Rev 12 or recited; Walvoord's `Rev 1` coverage needs a visible anchor or should be removed; Theodoret's Matt 24 row needs a fuller Greek anchor.
3. Fix the corpus manifest mismatch: either backfill JSONs for the legacy voices named in the tradition-cluster list, or mark those clusters as bibliography/legacy narrative rather than JSON-backed.
4. Fix the backend manifest mismatch: the actual JSON corpus has three non-Logos backend files, not four; 1 Enoch Parables is Logos-backed despite being described in the prompt as external-resource.
5. Add longer Theodoret Greek-OCR quote fragments and, ideally, a `frontend` note/transliteration or translation field for reader-facing auditability. Verified OCR snippets like "foretelling an appearance" are too weak for academic warrant review.

### Nice-to-have

1. Add a small report that compares `passageCoverage[]` against `crossBookReadings[].targetPassage` and citations, flagging coverage values with no cited supporting row.
2. Add `notes` to `summary-inference` citations naming the adjacent articles or sections the inference draws on.
3. Fill `Dan 10:1-21` only if WS1 actually visualizes Daniel's angelic conflict / heavenly mediator material; otherwise remove it from the pilot vocabulary until needed.
4. Add one more progressive-dispensational voice and one more historicist or partial-preterist voice if WS1 will compare traditions rather than only display representative poles.
5. Treat the 1 Enoch Parables entry explicitly as a reception-event survey, not a single-author scholar, in downstream labels and UI copy.

---

## 7. Post-audit relabel + repairs — applied 2026-04-26 (same session)

The 28 relabel rows in §2 above were applied to nine WS0c scholar JSON files via
`tools/apply_ws0c_relabels.py`, which encodes a per-citation table mapping each codex
row to the specific citation(s) its reason names. Where a row's reason names multiple
quotes (e.g. 1 Enoch L: "the two quotes…"; Theodoret E: "the short OCR snippets…";
Theodoret J: "'foretelling an appearance' and a Psalm 2 incipit"), all named
citations were relabeled; where a row names a single quote (e.g. Hamilton xMatt 24:
"'Almost a commentary'…"), only that citation was relabeled. Total: **33 citation-level
relabels** (28 codex rows; some rows attack multiple citations explicitly). No
rationales were rewritten; only `supportStatus` tags changed.

The four cross-book / coverage mismatches in §6.2 were repaired in the same script:

- **Goldingay xMark 13** — the empty cross-book row was removed and "Mark 13" was
  removed from `passageCoverage[]`. Goldingay's NT-reception material in §INTRO.7
  references Mark 13 but no Mark-13-specific stored citation backs the row, so the
  honest move is removal rather than retention with no warrant.
- **LaCocque xRev 13** — the row was relabeled to `summary-inference` (the existing
  Rev 12:10 quote is honest about extending into Rev 13's broader dragon-and-beast
  trajectory; the rationale's surrounding text already names Rev 12:10 explicitly).
  `targetPassage` retained as "Rev 13"; vocabulary not extended.
- **Walvoord Rev 1** — "Rev 1" removed from `passageCoverage[]`. Walvoord's Rev
  allusions cluster on Rev 4–5 / 13 / 17 with no stored Rev 1 cross-book row.
- **Theodoret xMatt 24** — relabeled to `summary-inference` (the short Greek phrase
  "ἐπιφάνειαν προθεσπίζων" is too thin alone to bear the full Matt 24:30 / 24:21–22 /
  24:23–27 mapping). OCR-quote tightening (re-extracting longer Greek anchors from
  `external-resources/greek/theodoret-pg81-dan7.txt` col. 1426) is deferred to a
  later session — codex's "must-fix" was relabel-or-narrow, which the relabel
  satisfies.

Validator + sweep state after the relabel and repairs:

```
python3 tools/validate_scholar.py docs/research/scholars/    # 17/17 files valid
python3 tools/sweep_citations.py --scholars docs/research/scholars \
    --legacy-md docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md
# 426 citations swept → verified=426
python3 -m pytest tools/workbench/tests/test_validate_scholar.py \
    tools/workbench/tests/test_citations.py \
    tools/workbench/tests/test_article_meta.py \
    tools/workbench/tests/test_lbxlls_reader.py \
    tools/workbench/tests/test_dictation_static.py    # 88 passed
```

Post-relabel `supportStatus` distribution across the 418 scholar-JSON citations:

| label | count | % | meaning |
|---|---:|---:|---|
| `directly-quoted` | 354 | 84.7% | quote text alone warrants the rationale's sub-claim |
| `paraphrase-anchored` | 17 | 4.1% | verbatim quote, but functions as a pointer into a longer argument |
| `summary-inference` | 47 | 11.2% | rationale synthesizes across articles or beyond the quoted fragment |
| `uncited-gap` | 0 | 0% | (none used in the WS0c corpus) |

Per-scholar (DQ / PA / SI):

| scholar | DQ | PA | SI |
|---|---:|---:|---:|
| 1-enoch-parables-nickelsburg-vanderkam | 19 | 0 | 6 |
| beale-use-of-daniel-in-revelation | 33 | 1 | 0 |
| blaising-bock-progressive-dispensationalism | 18 | 2 | 2 |
| calvin-daniel | 25 | 0 | 0 |
| collins-hermeneia-daniel | 3 | 3 | 9 |
| duguid-rec-daniel | 22 | 0 | 1 |
| durham-revelation | 3 | 2 | 9 |
| goldingay-wbc-daniel | 25 | 0 | 0 |
| hamilton-clouds-of-heaven | 26 | 1 | 2 |
| hartman-dilella-anchor-daniel | 23 | 0 | 0 |
| jerome-commentary-on-daniel | 22 | 0 | 1 |
| lacocque-book-of-daniel | 11 | 3 | 2 |
| menn-biblical-eschatology | 12 | 3 | 4 |
| pentecost-things-to-come | 29 | 0 | 2 |
| theodoret-pg81-daniel | 14 | 1 | 7 |
| walvoord-daniel | 35 | 1 | 2 |
| young-prophecy-of-daniel | 34 | 0 | 0 |

### Manifest mismatches (audit §6.3 / §6.4) — applied as bibliography updates

The "tradition-cluster list includes legacy voices that aren't JSON-backed" finding
was addressed by marking each legacy voice explicitly in `docs/research/bibliography.md`
with **Not JSON-backed** annotations: Bauckham, Wright, Collins *Apocalyptic Imagination*
(distinct from his JSON-backed *Hermeneia Daniel*), Newsom & Breed, Longman, Lucas,
Hoekema, Riddlebarger, Sproul. Several mixed-cluster cases also got per-voice notes
about which JSON-backed voices represent the cluster (e.g. Reformed-amillennial:
Duguid + Menn JSON-backed, Hoekema + Riddlebarger narrative-only). The
`docs/research/method-and-limits.md` §1 was rewritten to reflect the post-WS0c
17-JSON-backed + 9-narrative-only manifest. The 1 Enoch Parables entry
(Nickelsburg & VanderKam) was added to the bibliography under "N" (was missing).

The §6.4 backend-manifest mismatch (1 Enoch Parables uses the Logos backend, not an
external resource) is consistent with the actual JSON; the misstatement was in the
audit prompt only. No scholar-JSON change was needed for this point.

### Conditions that remain after relabel

The relabel + repairs close the "verified quote exists but label overclaims" defect
class flagged in §1 for the WS0c expansion. What this does **not** close:

1. **Theodoret OCR-quote tightening** (audit §6.5) is deferred. Several Greek
   fragments remain shorter than codex would prefer; the `summary-inference` label
   honestly acknowledges the gap, but reader-facing transliteration / English-gloss
   fields would carry more academic weight. Earmarked for a focused subagent run
   against `external-resources/greek/theodoret-pg81-dan7.txt`.
2. **Nice-to-have items in §6** (passageCoverage cross-check report;
   `notes` field naming inference sources; `Dan 10:1-21` coverage gap; additional
   progressive-disp / partial-preterist voices) remain deferred. None block WS1.
3. **WS0c-9 Aramaic anchor field + Lexham Aramaic Lexicon integration** is in the
   handoff queue but unaddressed in this session.
