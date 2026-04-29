# Bibliography (WS0.5-4)

Primary and secondary works surveyed for the Visual Theology Daniel 7 pilot.
Citation form follows SBL Handbook of Style §6.4 (monographs in series) and §6.4.2 (older
works), with an additional Logos electronic-edition field for in-project traceability.

For each entry: print bibliographic data first, then the Logos `LLS:` resource id and
electronic-edition publication date as recorded in the Logos library catalog. Where the
electronic edition is the only available form (e.g. Walvoord *Daniel*, distributed by
Galaxie Software), that is noted explicitly so the reader can find the print original.

The entries below cover three groups:

- **JSON-backed primary voices** (17): the four WS0b voices (Collins *Hermeneia*,
  Walvoord, Blaising & Bock, Durham) plus the 13 added in WS0c (Calvin, Goldingay,
  Hartman & Di Lella, Young, Beale, Pentecost, Duguid, Hamilton, Jerome, Theodoret,
  LaCocque, Menn, 1 Enoch Parables [Nickelsburg & VanderKam]). Each produces a
  scholar JSON under `docs/research/scholars/` with the dual-citation schema and is
  exercised by `tools/sweep_citations.py`.
- **Narrative-only / not-JSON-backed legacy voices** (9): the 2026-04-23 second-pass
  scholars (Bauckham, Wright, Collins *Apocalyptic Imagination*, Newsom & Breed,
  Longman, Lucas, Hoekema, Riddlebarger, Sproul). Each is referenced in the legacy
  taxonomy survey `2026-04-23-daniel-interpretive-taxonomy-survey.md` as a
  bibliography/narrative voice but is **not** directly surveyed. Downstream
  consumers should treat citations to these voices as research-doc summary, not
  verified primary survey.
- **Tooling / fixture entries** (1): Beeke & Smalley *RST 4* (the schema's
  pages-and-sections fixture; not a Daniel survey target, but cited because the
  architecture spec quotes it). Plus Anderson *ITC Daniel*, held in library but not
  yet surveyed (kept here for traceability).

Tradition tags are descriptive, not authoritative — they identify the cluster the project
engages with for each scholar; intra-cluster divergence is captured in the scholar JSON
files, not here. Where a tradition cluster's primary voices are split between JSON-backed
and narrative-only, the entries below mark each individual voice's status explicitly.

---

## A

**Anderson, Robert A.** *Signs and Wonders: A Commentary on the Book of Daniel*.
International Theological Commentary. Grand Rapids: Eerdmans, 1984. Logos electronic
edition `LLS:ITC21DAN`. [Tradition cluster: critical-mainline. Held in library, not
yet surveyed.]

**Bauckham, Richard.** *The Theology of the Book of Revelation*. New Testament Theology.
Cambridge: Cambridge University Press, 1993. Logos electronic edition `LLS:NTTHEO87REV`
(2024-10-18). [Tradition cluster: prophetic-apocalyptic / British biblical theology.
**Not JSON-backed** — narrative reference only in `2026-04-23-daniel-interpretive-taxonomy-survey.md`.]

**Beeke, Joel R., and Paul M. Smalley.** *Church and Last Things*. Reformed Systematic
Theology 4. Wheaton: Crossway, 2024. Logos electronic edition `LLS:RFRMDSYSTH04`
(2024-05-06). [Tradition cluster: Reformed-confessional. Schema fixture for §R48.2 / pp.
1497–1498 in `tests/test_article_meta.py`.]

**Beale, G. K.** *The Use of Daniel in Jewish Apocalyptic Literature and in the
Revelation of St. John*. Eugene, OR: Wipf and Stock, 2010 (originally University Press of
America 1984). Logos electronic edition `LLS:SDNLJWSHRVSTJHN` (2020-01-18). [Tradition
cluster: evangelical-cross-book-reception. WS0c primary voice — Daniel→Second Temple→NT
trajectory monograph; pairs with Hamilton NSBT 32 below.]

**Blaising, Craig A., and Darrell L. Bock.** *Progressive Dispensationalism*. Grand Rapids:
Baker, 2000. Logos electronic edition `LLS:PROGDISPNM` (2009-06-26). [Tradition cluster:
progressive-dispensational. WS0b primary voice.]

## C

**Calvin, John.** *Commentary on the Book of the Prophet Daniel*. Translated by Thomas
Myers. Bellingham, WA: Faithlife (digital reissue of Calvin Translation Society 1852),
2010. Logos electronic edition `LLS:CALCOM27DA` (2016-12-20). [Tradition cluster:
reformed-exegetical-historic. WS0c primary voice — historic Reformed reference for
Daniel exegesis. Original Latin 1561.]

**Collins, John J.** *The Apocalyptic Imagination: An Introduction to Jewish Apocalyptic
Literature*. 3rd ed. Grand Rapids: Eerdmans, 2016. Logos electronic edition
`LLS:PCLYPTCMGNTNPLT` (2019-06-05). [Tradition cluster: critical-modern / apocalyptic
genre studies. **Not JSON-backed** — narrative reference only in
`2026-04-23-daniel-interpretive-taxonomy-survey.md`. Collins's *Hermeneia Daniel*
is JSON-backed; this is a separate work.]

**Collins, John J.** *Daniel: A Commentary on the Book of Daniel*. Hermeneia. Minneapolis:
Fortress Press, 1993. Logos electronic edition `LLS:HRMNEIA27DA` (2006-11-01). [Tradition
cluster: critical-modern. WS0b primary voice.]

## D

**Duguid, Iain M.** *Daniel*. Reformed Expository Commentary. Phillipsburg, NJ: P&R
Publishing, 2008. Logos electronic edition `LLS:REC27DA` (2015-10-27). [Tradition
cluster: reformed-contemporary-expository. WS0c primary voice — fills the contemporary
Reformed Daniel-exegete gap between Calvin (16c) and Beeke/Smalley *RST 4* (systematic).]



**Durham, James.** *A Commentarie upon the Book of the Revelation*. Edinburgh: Robert
Sanders, 1680 (original imprint); Logos digital reprint `LLS:COMMREVDURHAM` (2013-04-03).
[Tradition cluster: historicist-Reformation, Scottish Covenanter. WS0b primary voice. The
Logos edition reproduces the early Edinburgh imprint; pagination of the print original is
not exposed in the digital edition.]

## G

**Goldingay, John.** *Daniel*. Word Biblical Commentary 30. Revised edition.
Grand Rapids: Zondervan, 2019 (original ed. 1989). Logos electronic edition
`LLS:WBC30REVED` (2020-01-13). [Tradition cluster: critical-mediating. WS0c primary
voice — accepts Maccabean dating while affirming canonical/theological authority;
deep on Aramaic + Dan 7:9–12 throne scene.]

## H

**Hamilton, James M., Jr.** *With the Clouds of Heaven: The Book of Daniel in Biblical
Theology*. New Studies in Biblical Theology 32. Downers Grove, IL: IVP / Apollos, 2014.
Logos electronic edition `LLS:NSBT32` (2015-11-11). [Tradition cluster:
evangelical-biblical-theology. WS0c primary voice — Beale-school monograph on Daniel
canonical reception.]

**Hartman, Louis F., and Alexander A. Di Lella.** *The Book of Daniel: A New Translation
with Notes and Commentary*. Anchor Yale Bible 23. New Haven: Yale University Press, 2008
(original Doubleday 1978). Logos electronic edition `LLS:ANCHOR27DA` (2015-04-27).
[Tradition cluster: critical-modern-catholic. WS0c primary voice — major US Catholic
critical commentary, distinct from Collins's German-influenced Hermeneia approach.]

**Hoekema, Anthony A.** *The Bible and the Future*. Grand Rapids: Eerdmans, 1994. Logos
electronic edition `LLS:BBLANDTHEFUTURE` (2014-10-03). [Tradition cluster:
Reformed-amillennial. **Not JSON-backed** — narrative reference only in
`2026-04-23-daniel-interpretive-taxonomy-survey.md`. Reformed-amillennial cluster's
JSON-backed voices are Duguid and Menn.]

## J

**Jerome.** *Commentary on Daniel*. Translated by Gleason L. Archer. Grand Rapids: Baker,
1958 (original Latin *Commentariorum in Danielem libri III*, c. 407 CE). Logos electronic
edition `LLS:JRMSCMMDNL` (2016-08-15). [Tradition cluster: patristic-latin-jerome. WS0c
primary voice — Western patristic flagship; defends 6th-c date against Porphyry's
Maccabean argument; foundational for the Christian typological-Christological reading.]

## L

**LaCocque, André.** *The Book of Daniel*. Eugene, OR: Cascade Books, 2018 (original
Knox Press 1979). EPUB at `external-resources/epubs/9781498221689.epub` (ISBN
9781498221689). [Tradition cluster: critical-continental-catholic. WS0c primary voice
(EPUB ingestion via `backend.kind: external-epub`).]

**Longman, Tremper, III.** *Daniel*. NIV Application Commentary. Grand Rapids: Zondervan,
1999. Logos electronic edition `LLS:NIVAC27DA` (2011-06-24). [Tradition cluster:
mediating-evangelical / typological-restraint. **Not JSON-backed** — narrative
reference only in `2026-04-23-daniel-interpretive-taxonomy-survey.md`. The
mediating-evangelical cluster has no JSON-backed voice in the current corpus.]

**Lucas, Ernest C.** *Daniel*. Apollos Old Testament Commentary. Downers Grove, IL:
InterVarsity / Apollos, 2002. Logos electronic edition `LLS:AOT27DA` (2018-03-16).
[Tradition cluster: mediating-evangelical / near-far fulfillment. **Not JSON-backed**
— narrative reference only in `2026-04-23-daniel-interpretive-taxonomy-survey.md`.]

## M

**Menn, Jonathan.** *Biblical Eschatology*. 2nd ed. Eugene, OR: Resource Publications,
2018. EPUB at `external-resources/epubs/9781532643194.epub` (ISBN 9781532643194).
[Tradition cluster: **covenantal-amillennial-eclectic** (corrected from briefing
assumption of historic-premil — Menn's Appendix 2 explicitly titles his synthesis
"An Amillennial Synthesis of the Biblical Data"). WS0c primary voice (EPUB ingestion).
Useful for the pilot's representation of *covenantal anti-dispensational* readings;
his comparative chapters explicitly engage and reject historic-premil from inside the
covenantal/Reformed camp.]

## N

**Nickelsburg, George W. E., and James C. VanderKam.** *1 Enoch 2: A Commentary on the
Book of 1 Enoch, Chapters 37–82*. Hermeneia. Minneapolis: Fortress Press, 2012. Logos
electronic edition `LLS:HRMNEIAENCH1B` (2014-11-18). [Tradition cluster:
second-temple-reception. WS0c primary voice — the project's anchor for the
*Parables of Enoch* (1 En 37–71) as the pre-Christian Jewish reception event for
Daniel 7's son-of-man figure. Treated downstream as a *reception-event survey*,
not a single-author Daniel commentary.]

**Newsom, Carol A., with Brennan W. Breed.** *Daniel: A Commentary*. The Old Testament
Library. Louisville: Westminster John Knox, 2014. Logos electronic edition `LLS:OTL27DA`
(2017-11-10). [Tradition cluster: critical-modern / reception-history. **Not JSON-backed**
— narrative reference only in `2026-04-23-daniel-interpretive-taxonomy-survey.md`.
The critical-modern cluster's JSON-backed voices are Collins *Hermeneia*,
Hartman & Di Lella, and LaCocque.]

## P

**Pentecost, J. Dwight.** *Things to Come: A Study in Biblical Eschatology*. Grand Rapids:
Zondervan, 1958. Logos electronic edition `LLS:9780310873952` (2023-08-01). [Tradition
cluster: classical-dispensational-systematic. WS0c primary voice — second classical-
dispensational anchor alongside Walvoord; Walvoord's DTS colleague; THE classical-
dispensational systematic-eschatology textbook for two generations.]

## R

**Riddlebarger, Kim.** *A Case for Amillennialism: Understanding the End Times*. Expanded
ed. Grand Rapids: Baker, 2013. Logos electronic edition `LLS:CSAMLLNLSM` (2017-11-08).
[Tradition cluster: Reformed-amillennial / earth-located church-militant.
**Not JSON-backed** — narrative reference only in
`2026-04-23-daniel-interpretive-taxonomy-survey.md`.]

## S

**Sproul, R. C.** *The Last Days according to Jesus: When Did Jesus Say He Would Return?*
Grand Rapids: Baker, 2015. Logos electronic edition `LLS:LSTDYSCCRDNGJSS` (2016-04-04).
[Tradition cluster: partial-preterist (moderate). **Not JSON-backed** — narrative
reference only in `2026-04-23-daniel-interpretive-taxonomy-survey.md`. The
partial-preterist cluster has no JSON-backed voice in the current corpus.]

## T

**Theodoret of Cyrus.** *Commentary on the Visions of the Prophet Daniel*
(*Ἑρμηνεία εἰς τὴν ὅρασιν τοῦ προφήτου Δανιήλ*; *In visiones Danielis prophetae*).
Greek text in J.-P. Migne, ed., *Patrologiae Cursus Completus, Series Graeca*, vol. 81
(Paris, 1864), cols. 1255–1546 (= TLG canon work `4089.028`). OCR'd extracts at
`external-resources/greek/theodoret-pg81-{dan5_6, dan7, dan11_12}.txt`, sourced from
the archive.org Google Books scan (`migne-pg81-archiveorg/`). [Tradition cluster:
patristic-greek-antiochene. WS0c primary voice (Greek-OCR ingestion via
`backend.kind: external-ocr` with `quote.language: grc`). Hill's English translation (WGRW 7, SBL 2006)
referenced bibliographically but not in project corpus.]

## W

**Walvoord, John F.** *Daniel: The Key to Prophetic Revelation*. Chicago: Moody, 1971
(original print imprint); Logos electronic edition `LLS:gs_walv_daniel`, distributed by
Galaxie Software (2008-12-17). [Tradition cluster: classical-dispensational. WS0b primary
voice. The Logos electronic edition is the only form held in this library; print pagination
is not exposed.]

**Wright, N. T.** *The New Testament and the People of God*. Christian Origins and the
Question of God 1. London: SPCK, 1992. Logos electronic edition `LLS:NTPPLOFGOD`
(2018-02-17). [Tradition cluster: post-critical / continuing-exile / British biblical
theology. **Not JSON-backed** — narrative reference only in
`2026-04-23-daniel-interpretive-taxonomy-survey.md`. *Jesus and the Victory of God*
(1996), which would deepen Wright on Dan 7→Jesus self-understanding, is not in the
project's Logos library; see `method-and-limits.md` §3a.]

---

## Y

**Young, Edward J.** *The Prophecy of Daniel: A Commentary*. Grand Rapids: Eerdmans, 1949
(reissue 1980). Logos electronic edition `LLS:PRPHCYDNLCMM` (2016-01-29). [Tradition
cluster: reformed-conservative-critical. WS0c primary voice — Westminster Theological
Seminary OT chair; conservative-critical defender of 6th-c date and predictive prophecy;
explicit covenantal-amillennial counter to Walvoord's dispensationalism. Page-numbered
citations available (resource has milestone index).]

## Notes on the Logos electronic-edition convention

For each entry, the second sentence gives the resource as it lives in the project's Logos
library:

- `LLS:` prefix is Logos Library System's stable identifier; it does not change across
  Logos software upgrades and is the same string used as `backend.resourceId` in the
  scholar JSON files.
- The dated stamp (e.g. `2017-11-10`) is the resource-file version from
  `ResourceManager.Resources.Version` — the on-disk file's version as recorded by
  `Data/e3txalek.5iq/ResourceManager/ResourceManager.db`. It is *not*
  `LibraryCatalog.Records.Version` (the catalog-metadata revision, which can lag years
  behind the resource file) and not `Records.ElectronicPublicationDate` (a separately
  tracked catalog field). `method-and-limits.md` §8a documents the provenance and
  names the verified sample-matches. The stamp identifies the specific digital cut
  surveyed; if a later re-cut alters paragraph offsets, citations may need
  re-extraction. The `tools/citations.py:verify_citation` SHA-256 mechanism flags
  drift.

Print pagination is exposed only for resources with an embedded milestone index
(`SegmentReferences_page`); see `docs/research/2026-04-24-codex-logos-metadata-design.md`.
For the four WS0b primary voices, the digital edition does not expose printed page
numbers, so scholar citations report `page: null` and rely on `nativeSectionId` plus
heading.

## Method note

Inclusion criterion for this bibliography: every author cited in the four WS0b scholar
JSON files plus the nine 2026-04-23 second-pass surveys. Works referenced only in passing
or only in the architecture spec (e.g. tools, dictionaries, lexicons) are catalogued in
`docs/research/2026-04-23-daniel-interpretive-taxonomy-survey.md` §"File Paths Surveyed"
rather than re-listed here. The intent of *this* bibliography is the scholarly-voice
manifest the visual-theology pilot represents.
