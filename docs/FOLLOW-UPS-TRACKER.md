# Follow-Ups Tracker — Codex-Surfaced Items

Items raised by codex (or other adversarial reviews) that were not applied
in their originating session. Organized by source session. Each entry carries
a severity, a description, and a disposition.

**Disposition vocabulary:**

- `defer indefinitely` — known low-value; leave open without an owner.
- `address-before-Wave-X` — must close before that wave dispatches.
- `address-when-Wave-X-touches-audits` — non-blocking; close
  opportunistically when the named wave next edits the audit doc.
- `fold-into-Wave-X-coordinator-prep` — non-blocking but must be
  ratified inside the named wave's coordinator briefing.
- `folded-into-session-Y` — addressed by a later session; cite the session.
- `schedule-for-after-Wave-X` — deferred work that has an owner and a
  scheduling trigger but not yet a session.
- `skip-as-redundant` — superseded or no longer applies.
- `closed in <session>` — resolved; kept here as a paper trail.

---

## Session E — verifier patch (2026-04-27)

- **LOW: COLLATE NOCASE on ResourceId for future-proofing alphanumeric
  dotted IDs** — the catalog ResourceId-first lookup is case-sensitive;
  future Logos catalog conventions might emit case-variant IDs.
  Disposition: **defer indefinitely**.
- **LOW: Single sqlite3 connection in `_resolve_bare_stem`** — opens a new
  connection per resolution; perf-only concern at current scale.
  Disposition: **skip-as-redundant** (perf is not currently a constraint).
- **INFO: Dotted-stem path is the only viable resolution for these
  resources** — informational only; no action.
  Disposition: **defer indefinitely** (informational).

---

## Session C-2 — Sefaria URL hardening (2026-04-28)

- **MEDIUM: cache-identity drift via authority** — different authority
  spellings could map to the same resource and cache under different keys.
  Disposition: **closed in C-3**.
- **MEDIUM: validator/runtime drift on URL paths** — validator and runtime
  applied different canonicalization. Disposition: **closed in C-2**.
- **LOW: HTML stripping editorial markers** — Sefaria HTML retains
  bracket/italic editorial markers that survive plain-text extraction.
  Disposition: **defer indefinitely**.
- **LOW: cache writes non-atomic** — writes can leave a partial file on
  crash. Disposition: **defer indefinitely** (cache is rebuildable).
- **LOW: non-object JSON crashes** — Sefaria responses that aren't JSON
  objects raise instead of erroring cleanly.
  Disposition: **defer indefinitely**.

---

## Session C-3 — Sefaria URL hardening v2 (2026-04-28)

- **MEDIUM: ref-segment character allowlist** — accept only
  RFC-compliant ref characters in segment names.
  Disposition: **closed in C-4**.
- **LOW: empty-userinfo regression test** — unit test guarding `urlparse`
  empty-userinfo handling. Disposition: **closed in C-4**.

---

## Session C-4 — allowlist (2026-04-28)

Four advisory items, all deferred:

- **ADVISORY: unit-test pinning urlparse empty-userinfo behavior** —
  defense-in-depth. Disposition: **defer indefinitely**.
- **ADVISORY: NBSP edge tests** — edge-case characters in ref segments.
  Disposition: **defer indefinitely**.
- **ADVISORY: defense-in-depth validate inside `_fetch`** — currently
  validates at boundary; codex suggests double-validation.
  Disposition: **defer indefinitely**.
- **ADVISORY: Wave-6-scoped allowlist docstring** — the allowlist
  comment should note its Wave-6 scope.
  Disposition: **defer indefinitely**.

---

## Session F — Wave 1 codex audit

- **17 supportStatus relabels** — applied via
  `tools/apply_wave1_relabels.py`.
  Disposition: **closed in commit `3593a89`**.

---

## Session D-2 codex review

- **6 IMPORTANT findings** on the initial `translations[]` schema +
  `external-ocr` generalization.
  Disposition: **folded-into-session D-2.5**.

---

## Session D-2.5 codex review

- **C-1: English-target enforcement** — validator did not require an
  `en` target on every non-English quote.
  Disposition: **folded-into-session D-2.6**.
- **C-2: Markdown SSoT not machine-enforced** — `_TRANSLATION_CONFIG.md`
  is the SSoT but no code reads it programmatically.
  Disposition: **defer indefinitely** (config is operator-facing).
- **C-3: Doc cleanups** — schema doc / config doc small edits.
  Disposition: **folded-into-session D-2.6**.

---

## Session D-2.6 codex review

- **Schema doc opening sentence contradiction** — the schema doc's
  opening sentence contradicted a later section.
  Disposition: **closed by PM via direct Edit before K-2**.
- **Test overlap nit** — two tests covered nearly the same code path.
  Disposition: **defer indefinitely**.

---

## Wave 6.1 / Wave 6.2 / H-2 / K-3

- **9 supportStatus relabels** across the Jewish-reception scholars —
  applied via `tools/apply_wave6_fixes.py`.
  Disposition: **closed in commit `f06d4de`**.
- **3 commit-message accuracy nits on K-3** — wording polish only.
  Disposition: **defer indefinitely**.

---

## Sessions D-1.6 / D-1.5 / D-1J codex reviews

- **Lingering audit-doc cleanups (D-1.6 pass-3)** — six specific items
  flagged in pass-3 across the patristic+Reformation and Jewish-reception
  audits:
  - Lambert engagement-inferred qualifier — engagement-density label
    needs an explicit "INFERRED" marker on the audit row.
  - PG 70 listing-only label — Cyril of Alexandria PG 70 row is a
    listing-only entry; should be marked as such, not implied
    full-text.
  - WA DB 11/II already-surfaced note — the Luther *Vorrede* row
    duplicates a finding surfaced earlier in the audit; consolidate.
  - §4a 6-vs-7 voice count — narrative says 6 voices in one place and
    7 in another; reconcile to the actual count.
  - §3 PD-count narrative inconsistency — public-domain count in §3
    prose disagrees with the §3 table; reconcile.
  - §6 Wave-6 cumulative-effect narrative — §6 conclusion needs a
    Wave-6 cumulative-effect paragraph reflecting the 8 new
    Jewish-reception voices.
  Disposition: **address-when-Wave-3-touches-audits** (audits will be
  re-touched as Waves 3–7 land cumulative-effect updates); no dedicated
  session.

- **Sefaria/Steinsaltz license adjudication (handoff §"Pending Decisions"
  #1–2)** — Sefaria reports `license: unknown` on "Midrash Rabbah — TE"
  and "Yalkut Shimoni on Nach"; Steinsaltz Center copyright applies to
  both Hebrew and English Steinsaltz. The corpus uses LLM translations
  only (not Sefaria's English) for license-restricted entries; the rule
  is enforced at survey time, not in the validator.
  Disposition: **fold-into-Wave-6.3-coordinator-prep** (decision must
  be ratified before Wave 6.3 fires; document the rule in the briefing
  so Wave 6.3 surveys do not import Sefaria English).

- **Theodoret OCR-quote tightening (handoff #9; codex pass-3)** — pass-3
  flagged several PG 81 col 1426 fragments as too short to bear their
  rationale weight; tightening means swapping fragmentary quotes for
  longer adjacent strings or downgrading supportStatus.
  Disposition: **schedule-for-after-Wave-2-supplementary** — fold into
  the Wave 2-supplementary OCR-prep tightening pass when sectarian-
  scrolls survey is dispatched, or into the next general OCR-prep pass
  if a tightening cycle is scheduled sooner. Not blocking K-4.

---

## Wave 2 codex review (2026-04-30) — ACTIVE

- **~30 dq over-application relabels** distributed approximately as:
  Cyril of Jerusalem ~15–20; Victorinus ~9+; Chrysostom 2; Bauckham 2–3;
  DSS art. 8242 1.
  Disposition: **address-before-K-4 via Session H-3**.
- **Subagent pre-commit cleanup: delete
  `docs/research/scholars/.cyril_shas.tmp`** — leftover scratch file
  from the Cyril survey subagent.
  Disposition: **address in H-3**.
- **Victorinus recension flag terminology** — "Jeromian" is imprecise;
  use "post-Augustinian / pseudo-Hieronymian redaction".
  Disposition: **address in H-3**.
- **Victorinus passageCoverage cleanup** — remove Dan 2:31–45 from the
  passageCoverage array (no substantive engagement on those verses).
  Disposition: **address in H-3**.

## Deferred — schedule pending

- **DSS supplementary survey** — Wave 2 codex review (2026-04-30)
  flagged that `LLS:LDSSHEIB` contains only the biblical Daniel
  manuscripts; sectarian scrolls (1QM, 4Q174, 11Q13, 4Q246, 4Q243-245)
  live in other Lexham DSS volumes. M6 stays PARTIAL until the
  sectarian scrolls are surveyed.
  Disposition: **schedule-for-after-Wave-3** — survey LLS resources
  containing 1QM / 4Q174 / 11Q13 / 4Q246 / 4Q243-245 sectarian scrolls
  once Wave 3 dispatch lands. Not blocking K-4.

## M-3 codex review (2026-04-30)

- **[advisory] `tools/apply_wave2_fixes.py` write-when-no-change** —
  the script rewrites scholar JSONs even when all expected relabels
  are already at the target supportStatus values (idempotent rerun
  triggers a no-op write of the same content). Cosmetic; doesn't
  affect correctness. Disposition: **defer indefinitely** — not worth
  a session; if a future apply-script is written, build idempotent
  no-op-detection in from the start.

---

## OCR-1 codex review

- **README inconsistency on `file://` language vs https-only validation**
  — docstring and validator disagree on whether local-file URLs are
  accepted.
  Disposition: **defer indefinitely**.
- **CCEL HTML extraction over-broad** — CCEL fetch path strips more
  than it should in some pages.
  Disposition: **address as encountered in OCR-prep × 5** (per-language
  sessions surface concrete cases).
- **Cache naming aliases on basename collision** — two different URLs
  with the same basename collide in the cache.
  Disposition: **defer indefinitely**.
- **Sefaria / YU links out of scope** — explicitly excluded from OCR-1
  scope. Disposition: **acknowledged, no action**.

---

## Wave 3 codex review (2026-04-30) — ACTIVE

Audit at `/tmp/wave3-codex-audit.md`. Verdict: **PASS-with-conditions**.
5/5 strict-validate; 236/236 citation verifications independent of codex.
35 `directly-quoted` over-applications flagged across the 5 files.

- **35 dq over-application relabels** distributed as:
  Driver 4 (lines 160, 797, 849, 968 → 2 pa + 2 si);
  Montgomery 4 (130, 893, 1100, 1217 → 2 pa + 2 si);
  Charles 11 (348, 432, 463, 484, 693, 766, 808, 973, 1306, 1327, 1438 →
  9 pa + 1 si + 1 duplicate-pa); Beale NIGTC 13 (233, 317, 662, 724,
  745, 837, 927, 1233, 1254, 1302, 1323, 1350, 1377 → 6 pa + 7 si);
  Sib Or 3 (296, 494, 515 → 1 pa + 2 si).
  Disposition: **address-before-Wave-4** in a Wave-3 cleanup session.
  Build a `tools/apply_wave3_fixes.py` script analogous to
  `tools/apply_wave2_fixes.py` that applies the relabels precisely as
  flagged. Run validator + sweep + tests after; commit as a single unit.

- **Beale NIGTC tradition tag — `reformed-amil` flagged as borderline.**
  Codex recommends switching to `evangelical-biblical-theology` or
  `evangelical-cross-book-reception` for cross-Beale tag uniformity (the
  existing `beale-use-of-daniel-in-revelation.json` uses
  `evangelical-cross-book-reception`; M10 §6 of the sufficiency map
  classifies Beale/Hamilton as Evangelical-BT). The Wave 3 dispatch
  briefing called the work "reformed-amil major Revelation," which is
  why the subagent landed on that tag. Codex's argument: Beale himself
  uses "inaugurated millennialism" + "eclecticism / redemptive-historical
  modified idealism" as self-descriptors, not a confessional Reformed-
  amil label.
  Disposition: **bring-to-Bryan** during the Wave-3 cleanup session.
  This is a tradition-cluster vocabulary decision (PM-Charter §9 escalation
  trigger). Default action if no input: keep `reformed-amil` and add a
  `notes` field explaining Beale's self-labels.

- **passageCoverage cleanups — 8 entries to remove or move to
  crossBookReadings.**
    - Driver: `Rev 13` (source-note level only; belongs in
      `crossBookReadings[]`)
    - Montgomery: `Mark 13`, `Matt 24`, `Rev 1`, `Rev 13` (textual-variant
      and parallel-note material, not substantive treatment)
    - Beale NIGTC: `Matt 24`, `Mark 13`, `1 En 37-71` (crossBook rows
      weakly anchored; NIGTC quote support inadequate)
  Codex marks Driver/Montgomery `1 En 37-71` and Charles `1 En 37-71` as
  borderline-but-acceptable (each scholar has a substantive Son-of-Man /
  Parables note). Disposition: **address-before-Wave-4** with the dq
  relabel pass.

- **Sib Or filename × resourceId mismatch.** File is named
  `sibylline-oracles-charlesworth-otp2.json` but its `resourceId` is
  `LLS:OTPSEUD01` because Sib Or actually lives in OTP Vol 1, not Vol 2
  as the briefing said. The pivot is correct (data > spec); but future
  maintainers may be misled by the "otp2" filename. Codex recommends a
  `notes`/`auditNotes` field documenting the deliberate pivot, or a
  follow-up rename to `sibylline-oracles-charlesworth-otp1.json`.
  Disposition: **address-before-Wave-4**. Default action: rename in the
  Wave-3 cleanup session and update any references; or, if rename costs
  too much, add a top-level `notes` field documenting the pivot.

- **Beale NIGTC × Beale monograph topical overlap — accepted with
  condition.** Codex confirms the two Beale entries are not redundant
  (NIGTC adds Rev 20 inaugurated millennialism, Rev 17 emperor-count
  adjudication, full commentary exegesis). The condition: NIGTC's
  `Matt 24`, `Mark 13`, `1 En 37-71` rows currently recapitulate
  monograph material without adequate NIGTC quote support; addressed by
  the passageCoverage cleanup above.

- **Charles source-table fragments overused as direct quotes.** Several
  Charles citations cite verified-but-unintelligible source-table
  fragments ("Likewise in Dan. 7:9", "appear to have suggested the
  clauses in our text", "Here again our author has drawn upon Daniel").
  These are quote-sufficiency problems, not quote-verification problems.
  Subset of the 11 Charles relabels above. Disposition: **address as part
  of the dq-relabel pass**.

- **[charter violation, MEDIUM] Sib Or subagent deleted other coordinators'
  staging files.** The Wave 3.5 subagent removed `_*.json` files from
  `docs/research/scholars/` including `_montgomery_citations.json` (which
  was Montgomery's in-flight staging file, not Sib Or's). Montgomery's
  pipeline survived (final output verified 51/51). But this violated the
  PM-Charter §5 cross-coordinator coordination rule: "Coordinators (and
  their subagents) MUST NOT delete or overwrite files outside their
  assigned scope." Disposition: **fold-into-Wave-4-coordinator-prep**.
  Update the parallel-coordinator briefing template to add an explicit
  "do not delete sibling staging files matching `_*.json`,
  `*_citations.json`, `*.tmp.*`, etc." rule for subagents. The Wave 4
  briefing should enumerate this explicitly.

- **[advisory] Subagent harness friction with Write tool path
  permissions.** Driver and Sib Or subagents both reported the harness
  blocked Write into `docs/research/scholars/` and they had to work
  around via `python3 -c` + `os.write` / Path.write_text-inside-script
  hacks. Outputs are correct but the workaround is fragile. Disposition:
  **defer indefinitely** unless it blocks future waves.

---

## OCR-prep × 5 + OCR-1.5 (2026-04-30 / 2026-05-01) — ACTIVE

- **[gap, MEDIUM] Pellican on Daniel — manual-download exhausted.** BSB
  legacy endpoint, BSB modern Mirador, Google Books PDF export, e-rara,
  and archive.org full-text search all failed to produce a working PDF.
  Logged as a permanent gap in `docs/research/method-and-limits.md` §3a.
  Wave 7 dispatches without Pellican; the existing Reformation cluster
  (Bullinger + Œcolampadius + Melanchthon + Lambert) carries the load.
  Disposition: **schedule-for-after-Wave-7** — re-attempt acquisition if
  a research-library scan surfaces or if free-online holdings get
  re-digitized; non-blocking for Wave 7 PASS.

- **[gap, LOW] Mede Latin original — no open-access scan located.**
  D-1.5 audit search did not find Cambridge / Bodleian / EEBO open-access
  digitizations of *Clavis Apocalyptica*. Cooper 1833 English translation
  is verified on archive.org and serves as the corpus's Mede witness.
  Disposition: **schedule-for-after-Wave-7** — same trigger as Pellican.

- **[blocked, MEDIUM] Abrabanel *Mayyenei ha-Yeshuah* — HebrewBooks
  Cloudflare-blocked.** OCR-prep-Hebrew restart confirmed 403 on six
  HebrewBooks endpoints with browser-class UA and Accept-Language headers.
  No fabrication: no output file was created. Notes file at
  `external-resources/hebrew/_OCR-PREP-NOTES.md` has the complete
  hand-off command sequence for browser-side download. Disposition:
  **fold-into-Wave-6.3-coordinator-prep** — Bryan's manual browser
  download is the only currently-known path; if it succeeds, OCR-prep-
  Hebrew runs the cache-honoring re-invocation. If the manual download
  also fails, Abrabanel becomes a permanent gap in `method-and-limits.md`
  and Wave 6.3 dispatches without him.

- **[audit error, IMPORTANT] Saadia attribution: Klein 1977, not Hurvitz
  1977.** OCR-prep-Judeo-Arabic established that the YU DSpace thesis on
  Saadia's Aramaic Daniel is by Klein, not Hurvitz as audit §B2 stated.
  Disposition: **address-when-Wave-6.3-touches-audits** — D-1J pass-3 or
  Wave-6.3 coordinator prep should correct the attribution in the audit
  doc and in any survey briefing that references the source.

- **[scope correction, IMPORTANT] Saadia OCR scope: edited body starts
  Dan 2:1, not Dan 2:4b.** Codex caught that Klein's edited Aramaic body
  begins at Dan 2:1 (the scope description on the thesis title page says
  "2:4b–7:28" but the actual edited text is broader). Wave 6.3 survey
  should cite from Dan 2:1 onward, not Dan 2:4b. Disposition:
  **fold-into-Wave-6.3-coordinator-prep** — survey briefing notes the
  expanded scope.

- **[boundary, IMPORTANT] Yefet ben Eli OCR contains a second bound
  work.** Margoliouth 1889 print binds Yefet's Daniel commentary together
  with "THE PALESTINIAN VERSION" (a different work, likely a Karaite
  Hexapla witness). Yefet body runs lines 1–9741; the Palestinian Version
  begins at line 9742. The OCR file
  `external-resources/judeo-arabic/yefet-ben-eli-margoliouth-1889.txt`
  spans both. Disposition: **fold-into-Wave-6.3-coordinator-prep** —
  Wave 6.3 Yefet survey briefing must instruct subagents to read only
  lines ≤ 9741 OR the file must be split into two separate text files
  (`yefet-ben-eli-margoliouth-1889.txt` truncated at line 9741 + a
  separate `palestinian-version-margoliouth-1889.txt` for the bound
  second work, which is out of pilot scope but useful as a reception-
  history footnote). Pick whichever is cleaner during K-5-prep.

- **[scope decision pattern, INFO] Bible-scale Fraktur slice technique.**
  OCR-prep-German located the Luther 1545 Bibel Daniel preface (PDF
  pp. 915–938 in a 1,535-page volume) via streaming the archive.org
  djvu.xml WORD-content search rather than full-volume OCR (which would
  have been ~13h for `frk` Fraktur). Pattern documented in
  `external-resources/german/_OCR-PREP-NOTES.md`. Disposition:
  **defer indefinitely** — informational only; future Bible-scale
  Fraktur sources can reuse the technique.

- **[follow-on, LOW] Saadia + Yefet: 4 codex conditions in OCR-prep
  notes await transcription.** Per OCR-prep-Judeo-Arabic report, codex
  flagged 4 conditions captured in
  `external-resources/judeo-arabic/_OCR-PREP-NOTES.md` "Codex review
  findings" section that should be promoted into this tracker by a
  follow-on PM-Edit. Disposition: **address-before-K-5** — PM reads the
  notes file and adds entries here before the K-5 commit. (Self-
  reference: this entry is the placeholder.)

- **[audit redirect, IMPORTANT] Origen primary surface: PG 13 → CCEL
  *Contra Celsum*.** OCR-prep-Greek confirmed PG 13 has no contiguous
  Origen Daniel commentary; only the Ezek 14:14 Noah-Daniel-Job
  typology cluster is substantive (captured in
  `external-resources/greek/origen-pg13-daniel-fragments.txt`).
  Wave 7 Origen dispatch must source the primary Daniel-engaging surface
  from CCEL *Contra Celsum* (where Origen's Son-of-Man + Daniel typology
  lives) via the planned external-html backend, NOT from PG 13. The
  PG 13 OCR remains useful as a corroborating fragment file but is not
  the primary surface. Logged as a gap-redirect in
  `docs/research/method-and-limits.md` §3a. Disposition:
  **fold-into-Wave-7-coordinator-prep** — Wave 7 Origen survey briefing
  must specify CCEL *Contra Celsum* as the primary surface + the PG 13
  fragment as supplementary. Also surfaces the latent question of
  whether external-html backend implementation should be added to the
  Wave-7 prerequisite list (currently CCEL extraction is via
  extract_ocr.sh --html mode, which OCR-1 implemented).

- **[survey discipline, IMPORTANT] Abrabanel OCR-quality requires
  visual-PDF-anchored quote extraction.** OCR-prep-Hebrew-pt-2 reported
  acceptable-with-caveat quality on
  `external-resources/hebrew/abrabanel-mayyenei-ha-yeshuah.txt`:
  Daniel keyword density unexpectedly low (דניאל=16, חיות=20, קרן=24,
  בן.אנש=0) due to OCR character substitutions corrupting Hebrew proper
  nouns. The text is substantively usable but blind LLM extraction will
  miss content. Wave 6.3 Abrabanel survey discipline: subagent reads the
  source PDF (HebrewBooks 23900) in a viewer to identify Daniel-7-engaging
  passages first, then locates the matching OCR substring as a short
  consonantal phrase (3-7 Hebrew letters) for the quote anchor. Disposition:
  **fold-into-Wave-6.3-coordinator-prep** — survey briefing must mandate
  this workflow.

- **[OCR re-do candidate, LOW] Abrabanel + Cyril Greek may benefit from
  re-OCR with tighter parameters.** OCR-prep-Hebrew-pt-2 noted a
  future re-OCR pass with `--psm 4` or watermark pre-suppression may
  improve Abrabanel quality. Cyril Mai vol 2 already required `--psm 4
  --dpi 300` to handle the parallel-column layout. Pattern: when an OCR
  output is "acceptable with substantive error rate," try alternate
  tesseract parameters before treating as final. Disposition:
  **schedule-for-after-Wave-6.3** — re-attempt only if Wave 6.3
  Abrabanel survey is materially blocked by OCR quality; otherwise
  defer indefinitely (the visual-PDF-anchored discipline above mostly
  obviates the need).
