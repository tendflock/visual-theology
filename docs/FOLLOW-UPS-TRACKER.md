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
