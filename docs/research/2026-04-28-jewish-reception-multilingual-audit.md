# Jewish Reception of Daniel 7 — Free-Online Original-Language Audit

**Session:** D-1J (2026-04-28). **Author:** PM. **Status:** research-only; corpus
unmodified. **Supersedes-scope-of:** gap-mapping §5b/§5d "permanent gap"
classifications for several Jewish-reception voices.

---

## 1. Overview

### 1.1 Why this exists

The peer-review-sufficiency map (`docs/research/2026-04-26-ws06-peer-review-sufficiency-map.md`)
flags M7 (Daniel 7 in Jewish interpretation) as **FAIL** — the corpus has zero
JSON-backed Jewish-reception voices. Wave 6 (gap-mapping §6 / sufficiency-map §8)
plans 5 medieval Jewish surveys via the Sefaria backend.

The original gap-mapping audit was implicitly scoped to Sefaria's English-bearing
pages and to free PD English translations. Voices whose primary engagement with
Daniel 7 survives only in Hebrew, Aramaic, or Judeo-Arabic were classified as
"permanent gaps" (Saadia, Yefet, Ralbag, Ramban, Abrabanel — gap-mapping §5d
U8–U11) on the basis of English-translation availability, not original-language
availability. This audit re-checks every Jewish-reception voice against
**original-language free-online sources**, and re-evaluates the gap classification.

The relevant precedent is `docs/research/scholars/1-enoch-parables-nickelsburg-vanderkam.json`,
which already operates in a multilingual mode (English commentary + Greek/Aramaic
text-critical apparatus). Surveying Hebrew/Aramaic/Judeo-Arabic primary sources
with PD English where available, and LLM-translation-with-original-attached
otherwise, is consistent with that precedent and fits the existing
verification discipline.

### 1.2 Method

For each candidate voice:

1. Probe **Sefaria** via `https://www.sefaria.org/api/v3/texts/<title>.7?version=<lang>`
   (Daniel chapter 7 specifically). HTTP 200 with non-empty `text` array =
   Hebrew availability VERIFIED. Probe `version=english` separately to record
   PD ET status.
2. Probe **HebrewBooks** via direct book-page URL `https://hebrewbooks.org/<ID>`.
   The specific HebrewBooks endpoints tested in this session (`/<id>`,
   `/pdf.aspx?req=<id>`, `/pdfpager.aspx?req=<id>&pgnum=N`,
   `/downloadhandler.ashx?req=<id>`) returned HTTP 403 to scripted requests
   (Cloudflare WAF + UA filter on the tested endpoints); presence is INFERRED
   via Google's indexed result snippets and via National Library of Israel
   cross-references. **Caveat (D-1.6 per codex IMPORTANT-4):** "all HebrewBooks
   endpoints" was an over-claim relative to the empirical sample. The audit's
   evidence supports "the specific HebrewBooks endpoints tested returned 403
   under WebFetch / scripted-request paths"; alternate hosts (e.g.,
   archive.org-hosted HebrewBooks scans, mirror sites, browser-direct fetches
   under different UA strings) were not exhaustively probed and may behave
   differently.
3. Probe **archive.org** via the search API `archive.org/advancedsearch.php?q=…&output=json`,
   then fetch the candidate item's `details/<id>` page and (where available) the
   `_djvu.txt` plain-text extract to confirm chapter coverage.
4. Probe **Wikisource (he.wikisource.org)** via direct URL `wiki/<title>`.
   HTTP 200 with non-trivial body = available.
5. **NLI / YU repository** pages all returned 403 to scripted requests this
   session (likely Cloudflare); recorded as "catalog-confirmed via search-engine
   index, fetch blocked" — a weaker form of verification than direct fetch.

VERIFIED status requires direct-fetch confirmation with content visible.
INFERRED status means existence is well-attested in indexed search results,
publication catalogs, or scholarly bibliographies, but the file itself was not
fetched and inspected this session. GAP means no free-online primary text was
identified in any repository searched.

### 1.3 Repositories actively searched

- **sefaria.org** — REST API works, Hebrew+English JSON endpoints reliable.
- **archive.org** — search API works; full-text djvu extracts available.
- **hebrewbooks.org** — blocks scripted access; URLs present per Google index.
- **he.wikisource.org** — direct fetch works for some pages.
- **National Library of Israel (nli.org.il)** — blocks scripted access.
- **Yeshiva University DSpace (repository.yu.edu)** — blocks scripted access.
- **biblejew.com (Project Saadia Gaon)** — fetched; Torah only, no Daniel.
- **alhatorah.org** — fetched; commentator-list pages accessible (no per-verse
  Daniel pages found by URL probe).

Repositories not separately probed this session (low expected yield for Daniel 7
specifically; deferred to a possible second pass): Otzar HaChochma free tier,
Bar-Ilan Responsa free portion, Gallica BnF, Tübingen / Munich digital
manuscripts, HathiTrust public-domain set.

### 1.4 Terminology used in this audit

- **PD ET** = public-domain English translation. Distinguished from "free-to-read"
  modern translations under restrictive license (Sefaria's Steinsaltz is
  Copyright Steinsaltz Center; readable but not redistributable).
- **PD original** = public-domain original-language text (older than 95 years
  for typical scholarly editions in the U.S.; older than 70 years post-mortem
  in most other jurisdictions).
- **Sefaria-borne** = available through `https://www.sefaria.org/api/v3/texts/…`.
- **HebrewBooks-borne** = available at hebrewbooks.org, requiring a backend that
  can either negotiate Cloudflare or work from a saved-PDF / OCR-text export.

---

## 2. Per-voice audit

### 2.1 Priority A — voices already in Wave 6 plan (sanity check)

#### A1. Rashi on Daniel 7 (Solomon ben Isaac, 1040–1105, France) — **rabbinic plain-meaning**

- **Original-language source.**
  - URL: `https://www.sefaria.org/api/v3/texts/Rashi_on_Daniel.7?version=hebrew`
  - Repository: Sefaria.
  - Format: API JSON; 28 verse-anchored Hebrew comments for Dan 7.
  - Language: Hebrew (vocalized; "Sefaria vocalized edition").
  - Sample: `<b>בְּאֵדַיִן חֶלְמָא כְּתַב.</b> אָז (הַחֲלוֹם כָּתַב) וְרָאשֵׁי הַדְּבָרִים אָמַר:` (Dan 7:1).
  - **Backup mirror**: `https://he.wikisource.org/wiki/רש"י_על_דניאל_ז` HTTP 200 (115 KB body).
- **Public-domain English translation.**
  - URL: `https://www.sefaria.org/api/v3/texts/Rashi_on_Daniel.7?version=english`
  - Translator: A. J. Rosenberg, *The Judaica Press complete Tanach with Rashi*.
  - License: **CC-BY** (versionSource: nli.org.il/en/items/NNL_ALEPH990019164710205171/NLI).
  - Quality: modern faithful (Rosenberg is the standard 20th-century English
    Rashi-to-Tanach project).
- **Expected citation surface.** Verse-by-verse on all 12 chapters; Dan 7 alone
  has 28 comments with strong four-kingdoms + son-of-man material.
- **Confidence:** **VERIFIED** (both Hebrew and English fetched, content confirmed).

#### A2. Ibn Ezra on Daniel 7 (Abraham ibn Ezra, 12c. Spain/Italy/France) — **grammatical-philological**

- **Original-language source.**
  - URL: `https://www.sefaria.org/api/v3/texts/Ibn_Ezra_on_Daniel.7?version=hebrew`
  - Repository: Sefaria, sourced from "Daat" (versionTitle: "Ibn Ezra on Daniel - Daat").
  - Format: API JSON; 16 Hebrew comments for Dan 7.
  - Language: Hebrew (unvocalized).
  - Sample: `בשנת חדה לבלשצר - עתה אחל לפרש הנבואות.` (Dan 7:1) and
    `ריש מלין אמר - אמר יפת: ראשי דברים דבר ולא כל דברים. ולפי דעתי: ככה ראשית דברי דניאל.`
    (Dan 7:1 cont. — note Ibn Ezra's interaction with Yefet ben Eli within the comment.)
  - Recension note: Sefaria does not flag long-vs-short recension; the body is the
    standard short recension reflected in Mikraot Gedolot.
- **Public-domain English translation.** **None on Sefaria** (`version=english`
  returned no English text). Ibn Ezra's Daniel commentary has no widely
  available PD English translation. Strickman's *Commentary of Ibn Ezra on…*
  series covers other books; Daniel was not part of Strickman's published set.
- **Expected citation surface.** Dan 7 alone has 16 comments; Ibn Ezra is
  briefer per-verse than Rashi but engages text-critical and grammatical
  questions including the bar-enash phrase.
- **Confidence:** **VERIFIED** Hebrew; **GAP** for PD ET (LLM-translation needed).

#### A3. Joseph ibn Yahya on Daniel 7 (Bologna 1538) — **early-modern Sephardic post-expulsion**

- **Original-language source.**
  - URL: `https://www.sefaria.org/api/v3/texts/Joseph_ibn_Yahya_on_Daniel.7?version=hebrew`
  - Repository: Sefaria; versionTitle: "Perush Chamesh Megillot u-Ketuvim. Joseph ibn Yahya. Bologna: 1538".
  - Format: API JSON; 28 Hebrew comments for Dan 7 (matches verse count).
  - Language: Hebrew (unvocalized; HTML `<b>` markup for lemmas).
  - Sample (Dan 7:1): `<b>הפרשה הח׳</b><br><b>בשנת חדא לבלאשצר וגו׳ דניאל חלום ראה. ומראות שכלו היו על משכבו</b>. היינו כי החלום היה בלילה בהיותו ישן על מטתו ולא ביום בהקיץ…`
- **Public-domain English translation.** **None.** No published English
  translation of ibn Yahya's Daniel commentary exists. LLM-translation needed.
- **Expected citation surface.** Long discursive comments on each verse; ibn
  Yahya's introduction to chapter 7 (`הפרשה הח׳` = "The 8th portion") frames the
  vision in eschatological-historical terms relevant to M7's four-kingdoms +
  little-horn dossier work.
- **Confidence:** **VERIFIED** Hebrew; **GAP** for PD ET.

#### A4. Malbim on Daniel 7 (Meir Leibush ben Yehiel Michel Wisser, 1809–1879) — **modern-Hebrew anti-Haskalah**

- **Original-language source.**
  - URL: `https://www.sefaria.org/api/v3/texts/Malbim_on_Daniel.7?version=hebrew`
  - Repository: Sefaria, sourced from Wikisource (versionTitle: "Malbim on Daniel -- Wikisource").
  - Format: API JSON; 28 Hebrew comments for Dan 7.
  - Language: Hebrew (unvocalized).
  - **Backup mirror**: `https://he.wikisource.org/wiki/מלבי"ם_על_דניאל_ז` HTTP 200
    (102 KB body; same source the Sefaria text derives from).
  - Sample (Dan 7:1): `<b>בשנת חדא לבלשאצר, </b>כבר ספר מסוף ימי בלשאצר ומלכות דריוש, רק כאן מתחיל החלק השני מזה הספר…`
- **Public-domain English translation.** **None.** Sefaria advertises a
  "Sefaria Community Translation" English layer (CC0) but the text array for
  Dan 7 is empty — placeholder, not actual translation. Print English Malbim
  exists for Pentateuch (Faier) but not for Daniel. LLM-translation needed.
- **Expected citation surface.** Long, idea-rich comments engaging both peshat
  and the anti-Haskalah polemical mode that distinguishes Malbim. Strong on
  Dan 7's four-kingdom typology.
- **Confidence:** **VERIFIED** Hebrew; **GAP** for PD ET.

#### A5. Steinsaltz on Daniel 7 (Adin Even-Israel Steinsaltz, 1937–2020) — **modern Orthodox**

- **Original-language source.**
  - URL: `https://www.sefaria.org/api/v3/texts/Steinsaltz_on_Daniel.7?version=hebrew`
  - Repository: Sefaria; versionTitle: "The Koren Steinsaltz Tanakh HaMevoar - Hebrew".
  - Format: API JSON; 28 Hebrew elucidated-text comments for Dan 7.
  - Language: Hebrew, fully vocalized; format is Steinsaltz's signature
    interleaving of MT lemma (bold) with explanatory expansion (brackets).
  - **License: "Copyright: Steinsaltz Center"** — free-to-read on Sefaria, but
    NOT public domain. Quote storage in our corpus would be permissible under
    fair-use for short quotations; full-text redistribution would not be.
- **Public-domain English translation.** **None.** Sefaria carries
  "The Steinsaltz Tanakh - English" (translator: Koren Publishers) but with the
  same `Copyright: Steinsaltz Center` licensing — free-to-read, not redistributable.
  Sample (Dan 7:1): `<b>In the first year of Belshatzar king of Babylon, Daniel saw a dream and visions in his head </b>which arose <b>while </b>he was dreaming<b> on</b> <b>his bed; then he wrote </b>down <b>the dream`. Quality is modern faithful.
- **License caveat (important).** Gap-mapping §5b implicitly classified
  Steinsaltz as a freely-online voice. **It is freely *readable* on Sefaria but
  not freely redistributable.** Survey workflow may use it for short quotations
  (fair use) but downstream republication is restricted. The same caveat
  applies to the English Steinsaltz on Daniel.
- **Expected citation surface.** Verse-by-verse with Steinsaltz's distinctive
  elucidation; modern Orthodox theological framing.
- **Confidence:** **VERIFIED** content; **license-restricted** for both Hebrew
  and English (free-read only, not redistributable).

---

### 2.2 Priority B — gap voices flagged in §5d but recoverable in original language

This is the core of the audit. Each voice is re-evaluated on original-language
availability rather than English-translation availability.

#### B1. Abrabanel, *Ma'yanei ha-Yeshuah* (Don Isaac Abrabanel, 1437–1508)

- **Daniel-engaging work and date.** *Ma'yanei ha-Yeshuah* ("Wells of Salvation"
  / "Springs of Salvation"), Abrabanel's verse-by-verse commentary on Daniel.
  Composed Naples/Corfu c. 1496–97 after the Iberian expulsion;
  **first printed Ferrara 1551** (per multiple bibliographies); **edition
  primarily extant on HebrewBooks: Amsterdam 1647** (HebrewBooks #23900,
  per Google's indexed result with title `מעיני הישועה -- אברבנאל, יצחק בן יהודה, 1437-1508`).
- **Original-language source.**
  - URL: `https://hebrewbooks.org/23900` (catalog page).
  - Repository: HebrewBooks.org.
  - Format: scanned PDF (HebrewBooks default; downloadable via `pdfpager.aspx`
    and `pdf.aspx` endpoints).
  - Language: Hebrew (early-modern unpointed).
  - **Verification status: INFERRED, not VERIFIED.** The specific HebrewBooks
    endpoints tested this session (`/<id>`, `/pdf.aspx?req=<id>`,
    `/pdfpager.aspx?req=<id>&pgnum=N`, `/downloadhandler.ashx?req=<id>`)
    returned HTTP 403 under scripted-request / WebFetch (Cloudflare + UA
    filter on those endpoints; D-1.6 narrowing per codex IMPORTANT-4 —
    not a repository-wide claim). The book's existence is attested by
    Google's indexed search-result title and by NLI's catalog records
    (NNL_ALEPH990010886860205171 — the Lipschitz/Tischendorf-style record;
    NNL_ALEPH990010886840205171 — additional edition with editor Baruch);
    NLI also returned 403 to scripted requests, so cross-verification was
    likewise via search-engine index.
  - **A second physical scan**: NLI catalogs a critical edition with
    editor Oren Golan (Hebrew, modern; record NNL_ALEPH990040870020205171).
    Status, format, and access not directly fetched.
- **Public-domain English translation.**
  - **No PD ET.** Hal Miller's *Wellsprings of Salvation: Commentary of Abarbanel
    on the Writings* (Amazon, 2024-onwards; ISBN B0DR29B41H) is paid and not PD.
  - **Sephardic Studies Institute** (sephardicstudies.org/don.html) hosts an
    older partial English presentation of Abrabanel on Daniel; not a
    full-text PD ET, but a useful summary-style reference.
- **Expected citation surface.** Verse-by-verse on all 12 chapters; Abrabanel
  is the most verbose Jewish Daniel commentator (his Daniel commentary is the
  longest of his prophetic commentaries). Strong on four-kingdoms = Babylon /
  Persia / Greece / **Rome** (Ishmael / Christendom in his post-expulsion
  framing) and on the eschatological calculation tradition.
- **GAP-MAPPING REVISION:** `gap-mapping §5d U10` listed Abrabanel as
  "Sefaria 404 → permanent gap." This is **incorrect**. The Hebrew text
  is freely available at HebrewBooks #23900; the gap is in PD English
  translation, not in original-language availability. Recoverable via
  HebrewBooks-borne backend (subject to Cloudflare-bypass implementation).
- **Confidence:** **INFERRED** (HebrewBooks page indexed; not directly fetched
  this session due to WAF). PROMOTABLE to VERIFIED with manual PDF download
  by Bryan or with a Cloudflare-aware fetcher.

#### B2. Saadia Gaon, *Tafsir on Daniel* (Sa'adiah ben Yosef al-Fayyumi, 882–942) — **Geonic, Judeo-Arabic**

- **Daniel-engaging work and date.** Saadia's *Tafsir* is his Judeo-Arabic
  translation-cum-commentary; the Daniel volume historically covered the
  entire book including the Aramaic chapters. Composed early-mid 10th c.
  Babylonia.
- **Scope clarification (D-1.6 per codex IMPORTANT-3):** the **free-online
  candidate identified in this audit is Hurvitz's YU 1977 thesis, which covers
  only the *Aramaic portion* of Daniel — Dan 2:4b–7:28**. Saadia's full Tafsir
  on Daniel (including chs 1, 8–12 in the Hebrew portion of the book) is
  attested in scholarly catalogs but a free-online Judeo-Arabic edition of
  the Hebrew-portion chapters has **not** been located this audit. For the
  M7 dossier the practical effect is favourable — Daniel 7 sits inside the
  Aramaic portion (2:4b–7:28) Hurvitz covers — but the audit must not
  imply whole-book Saadia recoverability. Chapters 1, 8, 9, 10, 11, 12 of
  Saadia's Tafsir remain a **structural gap for free original-language
  recoverability** in this audit.
- **Original-language source.**
  - **Sefaria's "Tafsir Rasag" entry covers Torah only** — five Pentateuchal
    books, no Daniel. Verified directly: the Sefaria Tafsir Rasag table of
    contents lists only Genesis (50 chapters), Exodus (40), Leviticus (27),
    Numbers (36), Deuteronomy (34). **Daniel is not included.**
  - **Yeshiva University DSpace repository:** Elazar Hurvitz, "Rav Saadia
    Gaon's Tafsir on the Aramaic portion of Daniel edited from manuscripts and
    Cairo Geniza fragments with an introduction" (M.A. thesis, YU, 1977). URL:
    `https://repository.yu.edu/items/f04a17f7-cc80-422c-8f75-cd5132521785`. The
    page returned HTTP 403 to scripted requests this session (Cloudflare or
    DSpace bot-block); existence and metadata confirmed via Google's indexed
    snippet and via WorldCat/NLI cross-references. **Coverage: Aramaic portion
    of Daniel only** (Dan 2:4b–7:28), which is **exactly the chapter 7 dossier's
    primary text** and the four-kingdoms / little-horn / son-of-man / Ancient
    of Days material.
  - **Project Saadia Gaon** (biblejew.com) — fetched directly; offers Torah
    only, no Daniel commentary; commercial bookstore pricing $119–$219 per
    volume; not PD.
  - **NLI catalog**: NNL_ALEPH990025069250205171 (Alobaidi 2006 critical
    edition with English translation, paid academic press) — not PD.
- **Public-domain English translation.**
  - **No PD ET in widely available form.** Alobaidi 2006 (Peter Lang;
    *Bible in History* series) is the standard scholarly English; paid only.
- **Expected citation surface.** Saadia is the foundational rabbinic Daniel
  commentator (per scholarly consensus) and the first Jewish exegete to engage
  Daniel within a sustained philological-historical framework rather than
  midrashically. His four-kingdoms reading and his explanation of the seventy
  weeks are foundational to all subsequent rabbinic Daniel reception.
- **GAP-MAPPING REVISION:** `gap-mapping §5d U9` said "only fragments survive
  in Judeo-Arabic; no consolidated ET." The first half is **inaccurate** —
  the *Tafsir* on Daniel is preserved (chapters 1, 8–12 in Judeo-Arabic; Aramaic
  chapters 2:4b–7:28 also extant via Hurvitz's edition from manuscripts +
  Geniza). The English-availability framing was correct; the original-language
  availability framing was wrong. Hurvitz's YU thesis is the closest free
  Judeo-Arabic edition for Dan 7, but its DSpace download requires breaking
  past the WAF. **Status: existence VERIFIED via published catalogs and
  scholarly cross-references; direct file access INFERRED, not VERIFIED.**
- **Confidence:** **INFERRED** for the YU thesis PDF (catalog-confirmed,
  fetch-blocked). **GAP** for any PD ET. **Promotable to VERIFIED** if the YU
  DSpace allows browser-based download for Bryan.

#### B3. Yefet ben Eli, *Commentary on Daniel* (Karaite, late 10th c. Jerusalem) — **Karaite Judeo-Arabic**

- **Daniel-engaging work and date.** Yefet (Yefet ha-Levi al-Basri) was the
  foremost Karaite Bible commentator. His Daniel commentary is in Judeo-Arabic
  and is essentially complete in surviving manuscripts.
- **Original-language source.**
  - URL: `https://archive.org/details/commentaryonbook00japhuoft`
  - Repository: archive.org (scanned from University of Toronto, Robarts Library).
  - Edition: D. S. Margoliouth, ed./trans., *A Commentary on the Book of Daniel
    by Jephet ibn Ali the Karaite*, Oxford: Clarendon Press, 1889 (Anecdota
    Oxoniensia, Semitic Series Part III). 344 leaves; English translation pp. 1-87,
    Glossary pp. 89-96, Arabic Text pp. 1-159 (PDF / EPUB / DjVu / plain-text
    djvu / ABBYY / HOCR).
  - License: NOT_IN_COPYRIGHT (1889 publication; 95+ years).
  - **Coverage (D-1.6 EMPIRICAL REVERSAL per codex IMPORTANT-1):** Daniel
    **chapters 1–12 in full** (entire book). The D-1 / D-1J framing of "chapters
    1–6 only" was empirically wrong. Re-fetching the djvu plain-text this D-1.6
    session and grepping for the running page-headers ("[CHAPTER. VERSE.]
    COMMENTARY ON DANIEL. PAGE") yields a complete progression:
    `[VII. 4.]`→`[VII. 26.]` (Dan 7), `[VIII. 7.]`→`[VIII. 27.]` (Dan 8),
    `[IX. 1.]`→`[IX. 25.]` (Dan 9), `[X. 2.]`→`[X. 21.]` (Dan 10),
    `[XI. 1.]`→`[XI. 40.]` (Dan 11), and `[XII. 2.]`→`[XII. 13.]` (Dan 12).
    The English translation ends on p. 87 with "XII. 13.] COMMENTARY ON
    DANIEL. 87" (the final verse of Daniel: "go thy way till the end be").
    Yefet's commentary on Dan 7:25 ("a time, times and half a time") is at p. 37
    of the English translation; Dan 7:13 (Bar-Enash, son-of-man) sits between
    `[VII. 12.]` p. 35 and `[VII. 26.]` p. 37. **The audit's prior claim that
    "no chapter 7 or later content is present in the Margoliouth volume"
    was a misread of the chapter-marker format — page-running headers carry
    the chapter:verse anchor, not section headers like "(Fourth Chapter.)".**
    The single explicit `(Fourth Chapter.)` header found in the prior pass was
    in fact for a sub-portion within Dan 4 (Nebuchadnezzar's letter), not the
    end of the commentary's coverage.
  - Format: facing-page Judeo-Arabic (in Hebrew script with Arabic-script
    apparatus) + Margoliouth's English translation.
  - Language: Judeo-Arabic original + English translation.
- **Public-domain English translation.** Margoliouth 1889 itself **is** the PD
  ET — for **Daniel 1–12 in full** (D-1.6 corrected). Margoliouth's verse-by-verse
  English of Yefet covers the whole book of Daniel including all of chapter 7
  (the M7 primary scope) and chapters 8-12.
- **Expected citation surface.** Margoliouth is verse-by-verse on the entire
  book, long discursive Karaite comments. Daniel 7 specifically — including
  the four-beasts vision (7:1-8), Ancient of Days (7:9-10), bar-enash (7:13-14),
  saints of the Most High (7:18, 25), and the time-times-and-half-a-time
  formula (7:25) — is fully covered with explicit Karaite-historicist
  interpretation (Yefet identifies the four kingdoms and reads Dan 7:25 in
  light of Muhammad's appearance, per the body of the commentary at pp. 33-43).
- **GAP-MAPPING REVISION:** `gap-mapping §5d U8` said "Karaite Judeo-Arabic;
  rare 1889 OUP edition; not on archive.org." This is **incorrect** on both counts:
  (a) the Margoliouth 1889 edition **is** at archive.org
  (`commentaryonbook00japhuoft`); (b) the edition covers **all 12 chapters**
  including Dan 7. The practical effect on the M7 dossier is therefore
  substantial: Yefet on Dan 7 is **freely available in original Judeo-Arabic
  + PD English translation** via Margoliouth, contrary to the gap-mapping's
  permanent-gap classification and contrary to D-1J's prior partial-gap framing.
- **Confidence:** **VERIFIED** for Daniel chapters 1–12 in full (D-1.6 empirical
  reversal of D-1J's "chapters 1–6 only" claim, per codex IMPORTANT-1
  re-verification request). Margoliouth's running-header progression confirms
  unbroken chapter coverage from VII through XII; the English translation
  reaches p. 87 ending at Dan 12:13.

#### B4. Ralbag (Levi ben Gershon, Gersonides), *Commentary on Daniel* (1288–1344, Provence) — **medieval Jewish philosophical-rationalist**

- **Daniel-engaging work and date.** Ralbag wrote a verse-by-verse commentary
  on Daniel, completed before his death in 1344, included in the Mikraot
  Gedolot tradition and printed in the *Qehillot Mosheh* rabbinic Bible
  (Amsterdam 1724–27, ed. Moses Frankfurter).
- **Original-language source.**
  - **Sefaria 404** for `Ralbag_on_Daniel`. Sefaria's Ralbag corpus covers
    Torah, Joshua, Judges, Samuel, Kings, Proverbs, Job, Song of Songs, Ruth,
    Ecclesiastes, Esther, Ezra, Nehemiah, Chronicles — **Daniel is missing**.
  - **archive.org Mikraot Gedolot, Second Rabbinic Bible** (Venice 1525, ed.
    Ya'aqov ben Hayyim, Bomberg): `https://archive.org/details/RabbinicbibleotMikraotGedolotBombergshebrewtanach.jacobBenChaim.1525`
    and `https://archive.org/details/The_Second_Rabbinic_Bible_Vol_4`. The
    1525 Mikraot Gedolot vol. 4 (Ketuvim) includes Daniel with the
    accompanying medieval commentaries. Whether Ralbag's Daniel commentary is
    *in* the 1525 MG vol. 4 specifically (vs. the 1517 vol. 4, vs. later
    expansions like Frankfurter 1724) was **not confirmed by direct page
    inspection** this session — INFERRED via Wikipedia's account of Ralbag's
    Daniel commentary appearing in *Qehillot Mosheh* 1724.
  - **HebrewBooks**: search blocked by Cloudflare; whether HebrewBooks hosts
    a discrete Ralbag-Daniel print could not be directly verified.
- **Public-domain English translation.** **No PD ET.** Ralbag's Daniel
  commentary has never been published in English; LLM-translation needed
  if surveyed.
- **Expected citation surface.** Ralbag is a rationalist commentator with
  systematic philosophical engagement; on Daniel he reads the four kingdoms
  in a Maimonidean-rationalist frame and engages the eschatological-calendrical
  questions. Important for showing that Jewish reception of Dan 7 is not
  uniformly midrashic.
- **GAP-MAPPING REVISION:** `gap-mapping §5d U11` said "Sefaria 404; Ralbag's
  Daniel commentary survives but is not online-digitized in any free
  repository found this session." Sefaria-404 confirmed. The **digitization
  claim** is partially superseded: Ralbag's Daniel commentary is **almost
  certainly** present in the Mikraot Gedolot 1525 Bomberg vol. 4 archive.org
  scan (or in Frankfurter's *Qehillot Mosheh* 1724–27 if HebrewBooks holds
  that). Direct verification deferred.
- **Confidence:** **INFERRED** (existence and free-online presence in scanned
  rabbinic Bibles is well-attested; specific page-anchor for Ralbag-on-Dan-7
  not confirmed this session). **GAP** for PD ET.

#### B5. Ramban (Moshe ben Nahman, Nahmanides, 1194–1270, Catalonia/Land of Israel) — **medieval Jewish kabbalistic-typological**

- **Daniel-engaging works and dates.**
  1. *Sefer ha-Geulah* ("Book of Redemption"), c. 1263, written in connection
     with the 1263 Barcelona Disputation. Engages Dan 7 four-kingdoms +
     eschatological-calculation tradition.
  2. *Drashah le-Shabbat ha-Gadol* / Torah commentary cross-references — Ramban
     does **not** have a complete verse-by-verse Daniel commentary, but
     references Dan 7 typologically in his Torah commentary at multiple
     locations.
- **Original-language source.**
  - **Sefaria 404** for `Ramban_on_Daniel`. Sefaria's Ramban corpus covers
    Torah, Job — no Daniel.
  - **Sefer ha-Geulah, Lipschitz 1909 London edition** — published from
    a British Library MS by Jacob Lipschitz (Whitechapel, London, 1909).
    Documented at jewishmiscellanies.com (catalog blog post) but no direct PDF
    URL was located on this blog; the same edition is **likely scanned at
    HebrewBooks** or NLI but neither could be verified due to access blocks.
  - **Ramban's Torah commentary** — *is* available on Sefaria
    (`Ramban_on_Genesis`, ..., `Ramban_on_Numbers`, `Ramban_on_Deuteronomy`)
    in Hebrew, with cross-references to Daniel scattered throughout.
- **Public-domain English translation.**
  - Ramban's Torah commentary: Charles Chavel's English translation (Shilo
    Publishing, 1971–1976, 5 vols.) is the standard English. Not PD; print
    only; selectively reproduced on Sefaria as paid-license content
    (`Ramban_on_Genesis` English on Sefaria is from Chavel where licensed).
  - *Sefer ha-Geulah*: no PD ET. Charles Chavel translated *Sefer ha-Geulah*
    in *Writings and Discourses of Nachmanides* (Shilo, 1978); paid only.
- **Expected citation surface.** *Sefer ha-Geulah* engages Dan 7 directly in
  its four-kingdoms / messianic-calculation discussion. Ramban's Torah commentary
  has scattered Dan-7-typology engagements (most notably his commentary on
  Gen 49:10 and on the four-kingdoms theme in the Joseph cycle).
- **GAP-MAPPING REVISION:** `gap-mapping §5d U10` said "Sefaria 404; Ramban
  did not write a complete Daniel commentary; references only in his other
  works." This is **mostly correct**: there is no complete Daniel commentary,
  and Sefer ha-Geulah's free-online status is uncertain. The Torah-commentary
  cross-references *are* available on Sefaria and are useful, even if
  scattered.
- **Confidence:** **VERIFIED** (Sefaria) for Ramban's Torah commentary
  cross-references; **INFERRED / not freely confirmed** for Sefer ha-Geulah
  Hebrew text. **GAP** for PD ET of Sefer ha-Geulah.

---

### 2.3 Priority C — Talmud, Midrash, Targum

These are reception-event-style sources analogous to the existing
`1-enoch-parables-nickelsburg-vanderkam.json` (multilingual; verse-anchored;
short evidence quotes).

#### C1. Bavli Sanhedrin 96b — Dan 7:9 "thrones plural"

- URL: `https://www.sefaria.org/api/v3/texts/Sanhedrin.96b?version=hebrew`
  and `?version=english`.
- Hebrew version: William Davidson Edition - Vocalized Aramaic (CC-BY-NC).
- English version: William Davidson Edition - English (CC-BY-NC).
- Coverage: contains the throne-plurality discussion of Dan 7:9 ("His throne
  was fiery flames" vs. "thrones were placed and the Ancient of Days sat") —
  the famous Akiva-Yose ben Galili "one for him and one for David" debate.
- **Confidence:** **VERIFIED** (both Hebrew and English fetched; Dan-7-9
  reception passage confirmed in segments [4]–[5] of 96b; Sefaria's English
  for [4] reads literally: "*One verse states: 'His throne was fiery flames'*
  *(Daniel 7:9)*, *and another phrase in the same verse states: 'Till thrones*
  *were placed, and one who was ancient of days sat,'* *implying the existence*
  *of multiple thrones.*").

#### C2. Bavli Sanhedrin 98a — Dan 7:13 "with the clouds of heaven"

- URL: `https://www.sefaria.org/api/v3/texts/Sanhedrin.98a?version=hebrew`.
- Hebrew version: William Davidson Edition - Vocalized Aramaic (CC-BY-NC).
- Coverage: 21 segments. Segment [12] preserves the famous R. Joshua ben
  Levi reading of Dan 7:13 against Zech 9:9: `אָמַר רַבִּי אֲלֶכְּסַנְדְּרִי: רַבִּי יְהוֹשֻׁעַ בֶּן לֵוִי רָמֵי, כְּתִיב: ״וַאֲרוּ עִם עֲנָנֵי שְׁמַיָּא כְּבַר אֱנָשׁ אָתֵה״, וּכְתִיב: ״עָנִי וְרֹכֵב עַל חֲמוֹר״. זָכוּ – עִם עֲנָנֵי שְׁמַיָּא, לֹא זָכוּ – עָנִי וְרוֹכֵב עַל חֲמוֹר.`
- **Confidence:** **VERIFIED** (Aramaic citation of Dan 7:13 confirmed at
  segment [12]; English available via the same endpoint with `version=english`).

#### C3. Bavli Hagigah 14a — Dan 7:9 "thrones plural" parallel

- URL: `https://www.sefaria.org/api/v3/texts/Hagigah.14a?version=hebrew`
  and `?version=english`.
- Hebrew version: William Davidson Edition - Vocalized Aramaic (CC-BY-NC).
- English version: William Davidson Edition - English (CC-BY-NC).
- Coverage: 18 segments. Segments [4]–[5] preserve the parallel "two thrones"
  passage with the Akiva ↔ Yose ben Galili exchange citing Dan 7:9 directly:
  `כָּתוּב אֶחָד אוֹמֵר: "כׇּרְסְיֵהּ שְׁבִיבִין דִּינוּר", וְכָתוּב אֶחָד אוֹמֵר: "עַד דִּי כׇרְסָוָן רְמִיו וְעַתִּיק יוֹמִין יְתִיב"`.
  This is the textual root of the rabbinic discomfort with Dan 7:9's plural
  thrones, and a critical reception document for the M7 dossier.
- **Confidence:** **VERIFIED** (Hebrew + English fetched; Dan 7:9 reception
  confirmed in segments [4]–[5]).

#### C4. Vayikra Rabbah 13:5 — four-kingdoms midrash

- URL: `https://www.sefaria.org/api/v3/texts/Vayikra_Rabbah.13?version=hebrew`.
- Hebrew version: "Midrash Rabbah -- TE" (license: unknown; likely public-domain
  Vilna-edition base).
- Coverage: 5 segments. Segment [4] preserves R. Shmuel bar Nahman's "all the
  prophets saw the kingdoms in their occupations" + R. Yehoshua ben Levi's
  schematized four-kingdoms typology — a foundational midrashic four-kingdom
  frame deriving from Dan 2 and Dan 7.
- **Confidence:** **VERIFIED** Hebrew; license unknown — needs checking before
  storing in corpus.

#### C5. Yalkut Shimoni on Nakh §1066 — Daniel 7 collection

- URL: `https://www.sefaria.org/api/v3/texts/Yalkut_Shimoni_on_Nach.1066?version=hebrew`.
- Hebrew version: "Yalkut Shimoni on Nach" (license: unknown).
- Coverage: 25 segments collecting earlier-rabbinic Dan 7 material. Segment [0]
  begins `וְעַד עַתִּיק יוֹמַיָּא מְטָה וגו' אִתְכְּרִית רוּחִי אֲנָה דָּנִיֵּאל…` — direct
  Dan 7:13 / Dan 7:15 anchor. Sections [1]–[3] handle Dan 8 (the ram and the
  he-goat) explicitly. Yalkut Shimoni Nach §1066 is the core Dan 7 anthology;
  §1067 is Dan 8; §1064–§1065 are Dan 5–6.
- **Confidence:** **VERIFIED** Hebrew; license unknown.

#### C6. Bereshit Rabbah / other midrashim with Dan 7 cross-references

- Bereshit Rabbah engages Dan 7's Ancient of Days at e.g. BR 88:6 (parallels in
  Sanhedrin 38b and the Akiva-Metatron tradition) — **filter in this session
  did not directly land Dan-7-anchored hits in BR 99 or Numbers Rabbah 13;
  these need targeted re-search by midrash-specific verse numbers**, deferred
  to a future pass.
- Pirkei DeRabbi Eliezer 30 — found 1 Dan-7-keyword hit; relevance not
  verified at the segment level this session.
- **Confidence:** **GAP** for this audit pass; the midrashic surface should be
  surveyed with a separate dedicated pass.

#### C7. Targum on Daniel — **honest gap**

- `Targum_Onkelos_on_Daniel`: Sefaria HTTP 404.
- `Targum_Jonathan_on_Daniel`: Sefaria HTTP 404.
- **Reason:** The book of Daniel has no classical Targum. Daniel itself contains
  long Aramaic sections (2:4b–7:28) and the rabbinic period did not produce a
  separate Targum. Onkelos covers the Pentateuch; Jonathan covers the Prophets
  *excluding* Daniel (Daniel is in the Ketuvim in the Jewish canon and was
  never targumized in the surviving tradition).
- **Confidence:** **CONFIRMED GAP** (canonical absence, not search failure).
  This should be acknowledged in `method-and-limits.md` rather than treated
  as a recoverable source.

---

### 2.4 Priority D — early-modern + modern Hebrew commentaries

#### D1. Metzudat David on Daniel (David Altschuler, c. 1740–1780) — **plain-meaning**

- URL: `https://www.sefaria.org/api/v3/texts/Metzudat_David_on_Daniel.7?version=hebrew`
  (gap-mapping F4 — already verified-by-existence in §5b).
- **Status (D-1.6 demotion per codex CRITICAL-1):** **INFERRED**, not VERIFIED.
  Sefaria's index walk this session confirmed the work exists in Sefaria's title
  list and resolves at the API endpoint at the index level, but **chapter-7
  content was not API-tested directly this pass** — the body was not fetched
  and inspected for Dan 7 material. Under the audit's own §1.2 + §8 method
  (VERIFIED requires direct-fetch confirmation with content visible), D1 is
  index-confirmed only. Promotable to VERIFIED via a single `?version=hebrew`
  fetch on `Metzudat_David_on_Daniel.7` confirming non-empty Dan 7 segments.

#### D2. Metzudat Zion on Daniel (companion to D1) — **lexical**

- URL: `https://www.sefaria.org/api/v3/texts/Metzudat_Zion_on_Daniel.7`
  (gap-mapping F5).
- **Status (D-1.6 demotion per codex CRITICAL-1):** **INFERRED**, not VERIFIED.
  Same posture as D1: Sefaria index confirms the work exists for the Daniel
  range; chapter-7 content fetch pending verification.

#### D3. Minchat Shai on Daniel (Yedidiah Norzi, 1626) — **Masoretic textual notes**

- URL: `https://www.sefaria.org/api/v3/texts/Minchat_Shai_on_Daniel.7`
  (gap-mapping F6). Less Dan-7-thematic; useful for textual-history micro-citations.
- **Status (D-1.6 demotion per codex CRITICAL-1):** **INFERRED**, not VERIFIED.
  Same posture as D1, D2: Sefaria index confirms the work exists for the Daniel
  range; chapter-7 content fetch pending verification.

#### D4–. Other Acharonim with Daniel commentary

Sefaria's Daniel-commentator corpus is fully enumerated (per Sefaria's
`/api/index/` walk performed this session): Rashi, Ibn Ezra, Joseph ibn Yahya,
Metzudat David, Metzudat Zion, Minchat Shai, Malbim, Steinsaltz. **No additional
named-Acharonim Daniel commentary is on Sefaria** beyond these 8.

HebrewBooks likely holds additional voices (e.g., Yefe To'ar — a 17th-c. midrash
super-commentary; the Vilna Gaon's marginalia where preserved; Hassidic
homiletical Daniel material). Direct probing was blocked by Cloudflare. **Not
audited in detail this session;** these would be a third-pass survey effort.

---

## 3. Summary table

Status legend: **V** = VERIFIED (URL fetched, content confirmed in original
language); **I** = INFERRED (catalog/index-confirmed but file not fetched
directly this session — typically due to bot-block); **G** = GAP; **G***
= partial gap (no rows currently use this status after D-1.6's Yefet 1–12 reversal; legend retained for completeness).

PD-ET legend (D-1.6 corrected per codex IMPORTANT-2 — three states, not two):
**PD** = pure public domain (no licensing restrictions; safe for redistribution).
**OL-MF** = open-licensed-modern-faithful (CC-BY, CC-BY-NC, etc. — modern
faithful translation, free-to-read AND free-to-redistribute under license terms,
but **not public domain**; commercial use may be restricted by NC clauses).
**LR** = license-restricted (free-to-read only; not redistributable, e.g.
Steinsaltz).
**None** = no free PD or open-licensed ET; LLM-translation needed.
Quality labels (orthogonal): **MF** = modern faithful; **W** = older wooden ET.

| # | Voice | Period / tradition | Work | Original-source URL | Lang | PD ET | Status |
|---|---|---|---|---|---|---|---|
| A1 | Rashi on Daniel | 11c. France, rabbanite plain-meaning | Rashi on Daniel | sefaria.org `/api/v3/texts/Rashi_on_Daniel.7?version=hebrew` | He | OL-MF (Rosenberg / Judaica Press, CC-BY) | V |
| A2 | Ibn Ezra on Daniel | 12c. Spain/Italy, grammatical | Perush al Daniel (short rec.) | sefaria.org `/api/v3/texts/Ibn_Ezra_on_Daniel.7?version=hebrew` | He | None (LLM-translation needed) | V |
| A3 | Joseph ibn Yahya on Daniel | 16c. Italy / Sephardic post-expulsion | Perush Chamesh Megillot u-Ketuvim (Bologna 1538) | sefaria.org `/api/v3/texts/Joseph_ibn_Yahya_on_Daniel.7?version=hebrew` | He | None | V |
| A4 | Malbim on Daniel | 19c. anti-Haskalah modern Hebrew | Malbim on Daniel (Wikisource source) | sefaria.org `/api/v3/texts/Malbim_on_Daniel.7?version=hebrew` ; mirror he.wikisource.org | He | None | V |
| A5 | Steinsaltz on Daniel | 20–21c. modern Orthodox | Tanakh HaMevoar | sefaria.org `/api/v3/texts/Steinsaltz_on_Daniel.7?version=hebrew` | He | LR (free-read on Sefaria; not redistributable) | V (license-restricted) |
| B1 | Abrabanel on Daniel | 15–16c. post-expulsion Sephardic | *Ma'yanei ha-Yeshuah* | hebrewbooks.org/23900 (Amsterdam 1647) | He | None (Miller 2024 paid; Sephardic Studies partial) | I |
| B2 | Saadia Gaon on Daniel | 10c. Geonic | *Tafsir on Daniel* (Aramaic portion of Daniel) | repository.yu.edu/items/f04a17f7-cc80-422c-8f75-cd5132521785 (Hurvitz YU thesis 1977) | JA | None (Alobaidi 2006 paid) | I |
| B3 | Yefet ben Eli on Daniel 1–12 | 10c. Karaite Jerusalem | Margoliouth 1889 OUP (Anecdota Oxoniensia) | archive.org/details/commentaryonbook00japhuoft | JA + En facing | PD (Margoliouth 1889 itself; pure public domain) | V (full book; D-1.6 reversal of "1-6 only" per codex IMPORTANT-1) |
| B4 | Ralbag on Daniel | 14c. Provence rationalist | Mikraot Gedolot 1525 vol 4 + Qehillot Mosheh 1724–27 | archive.org/details/RabbinicbibleotMikraotGedolotBombergshebrewtanach.jacobBenChaim.1525 (vol 4 needs page-anchor) | He | None | I |
| B5 | Ramban on Daniel | 13c. Spanish kabbalist | *Sefer ha-Geulah* (Lipschitz 1909) + Torah-commentary cross-refs | Sefaria Ramban-on-Torah; *Sefer ha-Geulah* PDF location uncertain | He | None for SHG; Chavel paid for Torah | I (SHG); V (Torah cross-refs) |
| C1 | Bavli Sanhedrin 96b | rabbinic Aramaic, c. 500 CE | Talmud Bavli | sefaria.org `/api/v3/texts/Sanhedrin.96b?version=hebrew` + en | Ar+He | OL-MF (William Davidson, CC-BY-NC — open-licensed-modern-faithful, NOT public domain) | V |
| C2 | Bavli Sanhedrin 98a | (same) | Talmud Bavli | sefaria.org `/api/v3/texts/Sanhedrin.98a?version=hebrew` + en | Ar+He | OL-MF (William Davidson, CC-BY-NC — open-licensed-modern-faithful, NOT public domain) | V |
| C3 | Bavli Hagigah 14a | (same) | Talmud Bavli | sefaria.org `/api/v3/texts/Hagigah.14a?version=hebrew` + en | Ar+He | OL-MF (William Davidson, CC-BY-NC — open-licensed-modern-faithful, NOT public domain) | V |
| C4 | Vayikra Rabbah 13:5 | tannaitic-amoraic midrash | Midrash Rabbah | sefaria.org `/api/v3/texts/Vayikra_Rabbah.13?version=hebrew` | He | license unknown — needs check | V (license-pending) |
| C5 | Yalkut Shimoni on Nach §1066 | 13c. anthological midrash | Yalkut Shimoni | sefaria.org `/api/v3/texts/Yalkut_Shimoni_on_Nach.1066?version=hebrew` | He | license unknown | V (license-pending) |
| C6 | Bereshit Rabbah / other midrashim | (rabbinic) | various | Sefaria — needs targeted re-search | He | varies | G (this pass) |
| C7 | Targum on Daniel | n/a | none survives | n/a | — | n/a | Confirmed structural gap |
| D1 | Metzudat David on Daniel | 18c. Galician plain-meaning | Metzudat David on Daniel | sefaria.org `/api/v3/texts/Metzudat_David_on_Daniel.7?version=hebrew` | He | None | I (D-1.6: index-confirmed, ch-7 fetch pending) |
| D2 | Metzudat Zion on Daniel | 18c. lexical companion | Metzudat Zion on Daniel | sefaria.org `/api/v3/texts/Metzudat_Zion_on_Daniel.7?version=hebrew` | He | None | I (D-1.6: index-confirmed, ch-7 fetch pending) |
| D3 | Minchat Shai on Daniel | 17c. Masoretic | Minchat Shai on Daniel | sefaria.org `/api/v3/texts/Minchat_Shai_on_Daniel.7?version=hebrew` | He | None | I (D-1.6: index-confirmed, ch-7 fetch pending) |

**Counts (D-1.6 corrected per codex CRITICAL-2 — unit explicitly stated; no
double-counting; columns sum to row count).**

**Unit:** one row per voice / collection. Total rows after dropping B3'
(merged into B3 per codex IMPORTANT-1 reversal): **20 rows total** (A1–A5,
B1, B2, B3, B4, B5, C1–C7, D1–D3 = 5+5+7+3 = 20). Each row is placed in
exactly one *primary* status bucket below; license-flag annotations are
orthogonal and do **not** add a separate count.

By primary status:

- **V (verified, fetched, content confirmed)**: **9 rows** —
  A1 Rashi, A2 Ibn Ezra, A3 ibn Yahya, A4 Malbim, A5 Steinsaltz (V with
  license-restricted annotation), B3 Yefet on Daniel 1–12 (D-1.6 reversal),
  C1 Sanhedrin 96b, C2 Sanhedrin 98a, C3 Hagigah 14a.
- **V (license-pending)**: **2 rows** — C4 Vayikra Rabbah 13:5,
  C5 Yalkut Shimoni Nach §1066 (Sefaria license "unknown"; content fetched
  and Daniel-anchored confirmed).
- **I (inferred — index-confirmed or fetch-blocked, content not fetched
  this pass)**: **7 rows** — B1 Abrabanel, B2 Saadia/Hurvitz, B4 Ralbag,
  B5 Ramban Sefer ha-Geulah; D1 Metzudat David, D2 Metzudat Zion,
  D3 Minchat Shai (D1–D3 demoted from V to I in D-1.6 per codex CRITICAL-1
  — they were index-confirmed via Sefaria's title list, not chapter-7
  content-fetched).
- **G (gap — confirmed structural absence)**: **2 rows** — C6 Midrash
  beyond what was checked (this audit pass), C7 Targum on Daniel
  (canonical absence).

**Sum check:** 9 + 2 + 7 + 2 = **20** ✓ (matches the 20-row table).

D-1J's prior "12 voices" V-count incorrectly (a) treated D1–D3 as content-
verified despite admitting only an index walk, (b) double-counted A5 in both
the 12-voice V bloc and a separate "V (license-restricted)" bloc, and
(c) treated B3 as ch-1–6-only-V plus a separate B3' G row. All three
are corrected above.

By language (D-1.6 corrected — Yefet now full-book):

- **Hebrew primary**: A1–A5, B1, B4, B5, D1–D3, C4, C5 (12 rows). Plus the
  Hebrew side of C1–C3 (William Davidson "Vocalized Aramaic" is rendered
  in Hebrew script; the underlying language is Talmudic Aramaic).
- **Aramaic primary**: C1–C3 (Talmudic Aramaic); plus Daniel 2:4b–7:28 in MT
  itself (orthogonal — text-not-reception).
- **Judeo-Arabic primary**: B2 Saadia/Hurvitz (Aramaic chs 2:4b–7:28 only;
  D-1.6 scope clarification per codex IMPORTANT-3); B3 Yefet (Margoliouth,
  full chs 1–12 per D-1.6 reversal).

By ET availability (D-1.6 three-state taxonomy per codex IMPORTANT-2):

- **PD (pure public domain) ET available**: **2 rows** — B3 Yefet/Margoliouth
  1889 (full Daniel 1–12, PD by 1889+95yr rule); plus C7 = N/A (no Targum
  exists at all). Strictly: 1 actual PD ET (Yefet/Margoliouth).
- **OL-MF (open-licensed-modern-faithful — CC-BY or CC-BY-NC, not pure PD)**:
  **4 rows** — A1 Rashi (Rosenberg, CC-BY); C1, C2, C3 Talmud (William
  Davidson, CC-BY-NC). Open-licensed but **not** public domain — codex
  CRITICAL-2 / IMPORTANT-2 corrected.
- **LR (license-restricted, free-to-read only, not redistributable)**:
  **1 row** — A5 Steinsaltz (Hebrew + English both Steinsaltz Center
  copyright).
- **License-pending (Sefaria reports "unknown")**: **2 rows** — C4 Vayikra
  Rabbah, C5 Yalkut Shimoni.
- **No free ET available (LLM-translation needed)**: **11 rows** — A2 Ibn
  Ezra; A3 ibn Yahya; A4 Malbim; B1 Abrabanel (Miller paid); B2 Saadia
  (Alobaidi paid; chs 2:4b–7:28 only via Hurvitz); B4 Ralbag; B5 Ramban
  Sefer ha-Geulah; D1 Metzudat David; D2 Metzudat Zion; D3 Minchat Shai;
  C6 wider midrashic surface. (Codex flagged the prior "9 voices" count as
  inconsistent — the actual list it had was 11; D-1.6 surfaces all 11.)

---

## 4. Backend implications

### 4.1 `external-sefaria` (existing — kind shipped in WS0c-C, tightened in C-2/C-3)

Voices served by the existing Sefaria backend (D-1.6: D1–D3 are
*planned-Sefaria* — index-confirmed, not yet content-fetched per codex
CRITICAL-1):

- A1 Rashi, A2 Ibn Ezra, A3 ibn Yahya, A4 Malbim, A5 Steinsaltz (license-aware
  storage; A5 LR — license-restricted)
- C1–C3 Bavli Sanhedrin 96b, 98a + Hagigah 14a (OL-MF, CC-BY-NC; not PD)
- C4 Vayikra Rabbah 13, C5 Yalkut Shimoni on Nach §1066 (license-pending
  adjudication)
- D1 Metzudat David, D2 Metzudat Zion, D3 Minchat Shai (D-1.6: index-confirmed,
  ch-7 content-fetch pending)
- B5 (partial) Ramban-on-Torah cross-references

URL pattern: `https://www.sefaria.org/api/v3/texts/<title>.<chapter>?version=<lang>`.

The existing backend already handles Hebrew NFC normalization and verse-anchored
quote storage. **Two new requirements** would surface in surveying these voices:

1. **License-aware storage.** `version.license` field must be stored in
   `citations[].backend.license` so corpus-level audits can flag CC-BY-NC vs.
   "Copyright: Steinsaltz Center" vs. "unknown" vs. "Public Domain". The existing
   schema does not have a `license` field; either add it or store under
   `backend.note`.
2. **Aramaic + Hebrew dual rendering.** For the Talmud passages, the William
   Davidson "Vocalized Aramaic" Hebrew-script Aramaic and the William Davidson
   English are the two primary forms. The verifier must accept either as
   matching (NFC + whitespace normalization is sufficient if matching against
   the exact-version-fetched text).

### 4.2 `external-pdf` / planned `external-ocr` (per D-2 / Wave J generalization)

Voices that require a HebrewBooks-PDF or PDF-from-archive.org backend:

- B1 Abrabanel *Ma'yanei ha-Yeshuah* — HebrewBooks #23900 PDF; needs Cloudflare-
  aware fetcher OR manual download by Bryan and storage as `external-resources/
  pdfs/abarbanel-mayyenei-hayeshuah-amsterdam-1647.pdf`, then OCR pass.
- B3 Yefet ben Eli on Daniel 1–12 (D-1.6: full book per codex IMPORTANT-1
  reversal) — archive.org PDF `commentaryonbook00japhuoft.pdf` is direct-fetchable;
  OCR plain-text already available as the `_djvu.txt` file at archive.org. This
  can be stored as a raw text file and indexed; Margoliouth's facing English
  translation is PD and provides the verifier's quote-text surface for any
  Yefet citation across chs 1–12.
- B4 Ralbag on Daniel — Mikraot Gedolot 1525 vol 4 OR Qehillot Mosheh 1724
  scan; needs identification of the page range covering Daniel 7. Likely
  HebrewBooks-borne if Frankfurter MG is hosted there.
- B5 Sefer ha-Geulah Lipschitz 1909 — likely scanned somewhere (HebrewBooks
  candidate); not located this session.
- B2 Saadia / Hurvitz YU thesis — DSpace direct-link; likely fetchable in
  browser by Bryan even if scripted access is blocked.

**Generalization recommended:** The planned `external-ocr` backend (D-2) should
accept a stored-locally text file or PDF as input, OCR (or use the source's
included plain-text), and verify quote presence by NFC + whitespace
normalization. This is the same pattern Bryan already uses for the Theodoret PG 81
OCR'd files in `external-resources/greek/`.

### 4.3 Possible new backend `external-archive-org`

Optional thin wrapper around archive.org's `_djvu.txt` plain-text URLs (e.g.,
`archive.org/stream/<id>/<id>_djvu.txt`). Less critical: archive.org supports
direct URL fetch, so the existing `external-pdf` / `external-ocr` pattern with
URL acquisition is sufficient. **Recommendation: do not add a new backend
kind**; treat archive.org URLs as inputs to the existing OCR-backed flow.

### 4.4 `external-html` / Wikisource fallback

For voices where Sefaria sources from Wikisource (Malbim — Sefaria's text is
explicitly "Malbim on Daniel -- Wikisource") and where the primary Sefaria URL
is preferred, no new backend is needed. The Wikisource pages exist as backup
mirrors but adding a separate Wikisource backend is unnecessary complexity.

### 4.5 NLI / YU access — Bryan-side manual verification

Both NLI and YU repository pages return 403 to scripted requests this session,
likely behind Cloudflare or DSpace bot-blocks. Browser access is presumably
unblocked. For voices where YU/NLI is the only known free path (B2 Saadia,
possibly B5 Sefer ha-Geulah), Bryan should manually download the PDF/text and
stage it under `external-resources/pdfs/` for the OCR backend to ingest.
**No backend change needed**; this is a process step.

---

## 5. Honest gaps

After this multilingual reframe + D-1.6 corrections, the genuinely unrecoverable
gaps for Daniel 7 Jewish reception are:

1. **(REMOVED in D-1.6 per codex IMPORTANT-1.)** D-1J originally listed
   "Yefet ben Eli on Daniel 7–12 in any free original-language form" as a
   genuine gap. D-1.6 re-fetched Margoliouth's djvu plain-text and confirmed
   via running page-headers (`[VII. 4.]`–`[XII. 13.]`) that Margoliouth covers
   the entire book of Daniel, chapters 1–12. **Yefet on Dan 7 is freely
   available** in Judeo-Arabic + PD English via `archive.org/details/commentaryonbook00japhuoft`
   pp. 33-43 of the English translation. The honest-gap entry is therefore
   removed.

2. **Targum on Daniel** (narrowed in D-1.6 per codex MINOR finding 1).
   Confirmed structural gap *for the classical canonical Targumim* (Onkelos
   covers the Pentateuch; Jonathan covers the Prophets but not Daniel, since
   Daniel sits in Ketuvim). Daniel itself contains long Aramaic sections
   (2:4b–7:28) and the rabbinic period did not produce a separate canonical
   Targum to Daniel. Possible non-classical / fragmentary Aramaic reception
   witnesses are not in scope of this rabbinic-canonical claim. Should be
   acknowledged in `method-and-limits.md`.

3. **Pre-Saadia rabbinic Daniel reception** beyond what's in Talmud + Midrash.
   No "Midrash on Daniel" qua standalone volume survives; reception is scattered
   through Bavli (Sanhedrin, Hagigah), Yerushalmi, midrashim (Rabbah, Yalkut),
   Pirkei DeRabbi Eliezer. The Yalkut Shimoni §1066 + Sanhedrin 96b/98a + Hagigah
   14a together represent the principal classical-rabbinic engagement; this
   audit verifies them as available, but the *survey* itself is non-trivial
   work (anthology-shape, like the planned ACCS/RCS work in §8 of the
   sufficiency map).

4. **Hassidic and yeshiva-tradition Daniel material** (e.g., Vilna Gaon
   marginalia, hasidic homilies). HebrewBooks likely hosts representative
   material; not surveyed this pass. Low priority for the M7 dossier.

5. **Modern Israeli academic Hebrew Daniel commentaries** (e.g., Rofé;
   Mosad Bialik / Olam HaTanakh series) — **not** audited this session.
   Low priority (these are descriptively-historical-critical, overlapping with
   the existing critical-modern cluster Bryan already has Goldingay/Collins/
   Newsom for).

---

## 6. Recommended Wave 6 expansion

The Wave 6 plan in `gap-mapping §6 Wave E` and `sufficiency-map §8 Wave 6`
is **5 voices**: Rashi, Ibn Ezra, ibn Yahya, Malbim, Steinsaltz. This audit
recommends growing Wave 6 to **N = 8–11 voices**, dispatched in three
sub-waves:

### Wave 6.1 — Sefaria-borne, English-or-Hebrew-already-on-Sefaria (5 voices, no schema work beyond `external-sefaria`)

Bryan can dispatch these in parallel. Each is a single Sefaria title with
direct Hebrew + (where present) English at the verse-anchored level.

| dispatch | voice | rationale |
|---|---|---|
| 6.1.1 | **Rashi on Daniel** | Hebrew + Rosenberg-CC-BY English; the foundational rabbanite plain-meaning voice |
| 6.1.2 | **Ibn Ezra on Daniel** | Hebrew only; needs LLM-translation; grammatical-philological cluster |
| 6.1.3 | **Joseph ibn Yahya on Daniel** | Hebrew only; LLM-translation; post-expulsion Sephardic |
| 6.1.4 | **Malbim on Daniel** | Hebrew only; LLM-translation; modern Hebrew anti-Haskalah |
| 6.1.5 | **Steinsaltz on Daniel** | Hebrew + English Steinsaltz Center; license-restricted but free-to-read; modern Orthodox |

### Wave 6.2 — Talmud + midrash reception-event surveys (3 surveys, anthology-shape)

These are reception-event surveys analogous to the existing
`1-enoch-parables-nickelsburg-vanderkam.json`. One JSON file per Talmud or
midrash collection covering the Dan 7 references within it.

| dispatch | voice / collection | content anchor |
|---|---|---|
| 6.2.1 | **Bavli on Daniel 7** (Sanhedrin 96b, 98a; Hagigah 14a; minor parallels) | thrones-plural + son-of-man + clouds-of-heaven; foundational Christian-period Jewish reception |
| 6.2.2 | **Midrash Rabbah on Dan 7 themes** (Vayikra Rabbah 13:5; Bereshit Rabbah parallels; Pirkei DeRabbi Eliezer 30) | four-kingdoms; needs license clarification on "Midrash Rabbah -- TE" version |
| 6.2.3 | **Yalkut Shimoni Nach §1066** (and 1067 if relevant) | 13c. anthology of earlier rabbinic Dan 7 reception; license unclear |

These three surveys close the **rabbinic-classical** subset of M7 and are
high-value for showing Jewish reception is multivocal (peshat, midrash, Talmud,
philosophical, mystical).

### Wave 6.3 — HebrewBooks / archive.org / DSpace voices (3 voices, requires `external-ocr` backend [D-2])

Prerequisite: Bryan must ratify D-2's planned `external-ocr` extension; OR
Bryan manually downloads the PDFs and stages them under `external-resources/`.

| dispatch | voice | source | priority |
|---|---|---|---|
| 6.3.1 | **Abrabanel, *Ma'yanei ha-Yeshuah*** | hebrewbooks.org/23900 (Amsterdam 1647) — needs manual download or Cloudflare-aware fetcher | high (single largest Jewish Daniel commentary; missing by gap-mapping's framing) |
| 6.3.2 | **Yefet ben Eli on Daniel 1–12** (D-1.6 reversal) | archive.org/details/commentaryonbook00japhuoft (Margoliouth 1889) — direct fetch; full book including Dan 7 | high (D-1.6 promotion: Karaite voice with full Dan 7 coverage including bar-enash + four-kingdoms; PD English ET + Judeo-Arabic facing) |
| 6.3.3 | **Saadia Gaon on Daniel** (Aramaic portion only) | repository.yu.edu/items/f04a17f7-cc80-422c-8f75-cd5132521785 (Hurvitz YU 1977 thesis) — needs manual download | medium-high (foundational Geonic; **scope: chs 2:4b–7:28 only** per codex IMPORTANT-3; chs 1, 8–12 not in this candidate; Dan 7 is in scope) |

### Wave 6.4 — deferred / not-recommended for this pass

- **Ralbag on Daniel** — INFERRED location in 1525 MG vol 4 / Qehillot Mosheh
  1724; specific page-anchor not yet identified. Defer until Bryan has time
  to locate the specific scan or until a HebrewBooks-search route opens.
- **Sefer ha-Geulah (Ramban)** — INFERRED Hebrew availability; specific PDF
  not located. Ramban's Torah cross-references are already accessible on
  Sefaria and could supplement at minimal cost. Defer the standalone
  Sefer ha-Geulah survey.
- **Metzudat David / Zion / Minchat Shai** — Sefaria-borne, low-effort
  add-ons; could be bundled in Wave 6.1.6–6.1.8 if Bryan wants comprehensive
  Sefaria-Daniel coverage. Low Dan-7-thematic yield (these are mostly
  plain-meaning + lexical glosses).

### Cumulative effect on M7

- **Currently:** 0 JSON-backed Jewish-reception voices → M7 = FAIL.
- **After Wave 6.1 (5 voices):** 5 voices (Rashi / Ibn Ezra / ibn Yahya /
  Malbim / Steinsaltz). Tradition diversity: rabbanite plain-meaning + grammatical
  + post-expulsion Sephardic + modern Hebrew + modern Orthodox. **M7 → PASS at
  pastor + scholar tier**, with ≥3 axis representations confirmed.
- **After Wave 6.2 (+3 surveys):** classical rabbinic / Talmud + Midrash
  layer added. **M7 → strong PASS**, plus closure of the Second Temple →
  classical rabbinic gap.
- **After Wave 6.3 (+3 voices):** Abrabanel + Yefet + Saadia. Coverage now
  spans Geonic (Saadia 10c.) → Karaite (Yefet 10c.) → Rashi (11c.) → Ibn Ezra
  (12c.) → Ramban Torah cross-refs (13c.) → ibn Yahya (16c.) → Abrabanel (15–16c.,
  long form) → Metzudat David / Minchat Shai (17–18c.) → Malbim (19c.) →
  Steinsaltz (20–21c.) → Talmud + Midrash anthology coverage.
  **Total: 11 voices** on M7 — exceeds the §2.3 minimum (≥2 JSON-backed primary
  voices per live tradition cluster) by a comfortable margin.

---

## 7. Risks / open questions

1. **License clarity on Sefaria's midrashim.** "Midrash Rabbah -- TE" and
   "Yalkut Shimoni on Nach" both report `license: unknown`. Before storing
   quote-text from these in the corpus, Bryan should adjudicate (Sefaria's
   "digitized-by-Sefaria" page is the authoritative source). If license =
   public domain, treat as unrestricted; if not, store with attribution and
   a `licenseRestricted: true` flag.
2. **Steinsaltz license.** "Copyright: Steinsaltz Center" applies to both the
   Hebrew Tanakh HaMevoar AND the English Steinsaltz Tanakh on Sefaria. Short
   quotations under fair-use are presumably OK for the corpus, but the survey
   workflow must store them without bulk redistribution.
3. **HebrewBooks Cloudflare (D-1.6 narrowed per codex IMPORTANT-4).** The
   specific HebrewBooks endpoints tested this session returned 403 under
   WebFetch / scripted access — not a repository-wide claim. Without a
   Cloudflare-aware fetcher (or manual-download workflow), 3+ voices in
   Priority B remain INFERRED rather than VERIFIED on the tested-endpoint
   evidence; alternate paths (browser direct fetch under different UA;
   archive.org-hosted HebrewBooks scans where they exist; mirror sites)
   were not exhaustively probed. Recommendation: Bryan does the one-time
   manual download for Abrabanel + (if locatable) Sefer ha-Geulah +
   (if locatable) Ralbag-Daniel, stages them in `external-resources/pdfs/`,
   and the `external-ocr` backend handles the rest.
4. **NLI / YU 403.** Browser access likely unblocked. Same workflow as #3:
   Bryan downloads, stages, OCR backend ingests. The Hurvitz thesis at YU
   is the most important single file in this category.
5. **(REMOVED in D-1.6 per codex IMPORTANT-1.)** Prior framing claimed Yefet
   on Daniel 7–12 was a structural gap. Re-fetching Margoliouth's djvu in
   D-1.6 confirmed the edition covers Daniel 1–12 in full; Yefet on Dan 7
   is freely available. No gap.
6. **Targum on Daniel** is a confirmed structural gap (no rabbinic Targum
   exists for Daniel). Document in `method-and-limits.md`.
7. **Bereshit Rabbah / wider midrashic surface** was not adequately probed
   this session. The Wave 6.2.2 survey will need to do a targeted
   midrash-by-midrash search rather than relying on this audit's preliminary
   sweep.

---

## 8. Methodology audit-trail (what was actually checked)

For verification (D-1.6 corrected): every URL or API endpoint claimed VERIFIED
in §2 has been fetched directly with the returned JSON or HTML inspected for
Daniel-7-specific content. No URL in the VERIFIED column is listing-only after
D-1.6 — D1, D2, D3 (Metzudat David, Metzudat Zion, Minchat Shai) were
index-confirmed via Sefaria's title list this audit but their chapter-7 content
was not directly fetched, so they are now classified INFERRED, not VERIFIED
(per codex CRITICAL-1).

INFERRED entries: either (a) pages exist per Google's indexed search-result
snippet and (where applicable) cross-referenced library catalog records, with
direct fetch returning 403 on the tested endpoints (HebrewBooks, NLI, YU
repository — D-1.6 narrowed: tested-endpoints-only claim, not repository-wide,
per codex IMPORTANT-4); or (b) the Sefaria index resolved the work but
chapter-7 content was not separately fetched (D1, D2, D3); or (c) the specific
page-anchor within a multi-volume scan (e.g., Mikraot Gedolot) was not pinned.

GAP entries: explicit failure to find a free original-language source after
multiple search-engine and direct-API probes.

The `tools/citations.py:verify_citation` discipline is unaffected by this
audit — quotes will still need to be stored with `sha256`, NFC-normalized,
and verified at survey-time.

---

## Codex review (advisory; NOT applied)

Run: `codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high < prompt.txt > log.txt 2>&1` (codex-cli 0.125.0, model gpt-5.5, reasoning effort: high). Two passes were run: the first stalled mid-investigation while reading file contents (cleared its context budget before producing structured output). The second pass with a tighter prompt (avoiding redundant file reads, demanding the structured verdict directly) produced the complete review below. Output is reproduced verbatim under the discipline that codex's findings are advisory and NOT to be applied during this session.

```
## CRITICAL findings
1. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:54` / `:553` / `:587` — VERIFIED status integrity is broken. The audit defines VERIFIED as direct-fetched, visible content, and §8 says every VERIFIED URL was fetched and inspected for Daniel-7 content. But D1 explicitly says only a Sefaria index walk was done and chapter 7 was "not API-tested" (`:522-525`), while D2/D3 provide only URLs (`:527-535`). Counting D1-D3 inside "V (verified, fetched, content confirmed)" (`:587-590`) is inconsistent. Under the audit's own rules, D1-D3 should be INFERRED or a separate "index-confirmed only" status, not V.

2. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:585-598` — The status counts are not internally reliable. A5 is included in the 12 verified voices (`:587`) and then separately counted again as "V (license-restricted)" (`:593-594`). The table has 21 rows if B3/B3′ and D1-D3 are counted, not the implied additive total of 22. The PD-ET count is also wrong: "No PD ET: 9 voices" lists 11 voices (`:615-618`). This makes the summary unsuitable as an audit control.

## IMPORTANT findings
1. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:307-313` — The Yefet chs. 7-12 gap conclusion is overstated for the evidence described. Chapter-marker inspection plus Belshazzar/Darius/lions'-den keyword density supports "chapters 1-6 are present," but does not by itself prove chapters 7+ are absent. OCR could omit distinctive headings, and later content could lack the searched markers. The claim needs a page-range/table-of-contents/end-of-text basis before "no chapter 7 or later content" is fully supported.

2. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:611-612` — The license/quality taxonomy is misleading. William Davidson Talmud is correctly identified elsewhere as CC-BY-NC (`:431-434`), but it is listed under "Modern faithful PD ET available" with a caveat that it is "not pure PD." CC-BY-NC is not public domain and carries a noncommercial restriction. "MF" can remain a quality label, but it should not be grouped as PD-ET availability.

3. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:250-266` / `:281-289` — The Saadia/Hurvitz scope is too easy to misread as whole-book recoverability. The document says Saadia's Daniel volume covers the whole book, but the free candidate actually identified is Hurvitz on the Aramaic portion only, Dan 2:4b-7:28. Since Daniel 7 is inside that scope, the M7-specific point is valid; the audit should not let B2 imply that chs. 1 and 8-12 are equally free-online-confirmed.

4. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:216-219` / `:833-835` — The HebrewBooks 403 claim is broader than the tested evidence. The audit lists several blocked patterns, but "all HebrewBooks endpoints" is too strong without testing alternate host/static-download patterns or mirrors such as archive.org-hosted HebrewBooks scans. The evidence supports "tested HebrewBooks endpoints returned 403," not a repository-wide access conclusion.

## MINOR findings
1. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:503-512` — The Targum-on-Daniel claim is basically correct if limited to classical rabbinic Targumim: Onkelos and Jonathan do not cover Daniel, and Daniel has no standard classical Targum. The wording "no separate Targum" / "never targumized in the surviving tradition" is broad enough that it should be narrowed to "no classical canonical Targum," leaving aside possible fragmentary or non-classical Aramaic reception witnesses.

2. `docs/research/2026-04-28-jewish-reception-multilingual-audit.md:747-785` — Wave 6 sub-wave sizing is acceptable against a 4-5 concurrent ceiling: 6.1 has 5, 6.2 has 3, and 6.3 has 3. No sizing defect found.

## Overall verdict
FAIL — The document has useful research, but its audit-control layer is not dependable yet. The main blocker is the VERIFIED-status breach: D1-D3 are counted as fetched/content-confirmed despite the document admitting they were only index-confirmed. The summary counts and PD-ET taxonomy also contain arithmetic and category errors. Several substantive claims are plausible, but the audit needs status downgrades and summary repair before it can be used as a reliable planning basis.
```

(End of codex output. Tokens used: 29,414. Codex's findings are NOT applied during this session per the brief — they are surfaced for PM follow-up.)

### PM-applied corrections (D-1.6, 2026-04-28)

PM session D-1.6 applied each of codex's 2 CRITICAL + 4 IMPORTANT findings to this audit. After this session, the audit is called **final** for D-2 planning purposes regardless of further codex findings; pass-3 below is advisory and NOT applied. Codex's MINOR findings are acknowledged inline with light edits where pertinent.

- **C-1J/CRITICAL-1 — D1, D2, D3 demoted V → I.** §2.4 + §3 table + §3 counts revised: Metzudat David (D1), Metzudat Zion (D2), Minchat Shai (D3) reclassified from VERIFIED to INFERRED on the consistent rule "Sefaria index confirms work exists for the Daniel range; chapter-7 content fetch pending verification." Each is promotable to V via a single Sefaria `/api/v3/texts/<title>.7?version=hebrew` content-fetch call. §3 V count drops accordingly (12→9).
- **C-1J/CRITICAL-2 — Arithmetic recompute; A5 single-counted; "9 voices" = 11 surfaced; total = 20.** §3 Counts block rebuilt with explicit unit ("one row per voice / collection"; total rows = 20 after dropping B3' per IMPORTANT-1 reversal). A5 Steinsaltz now counted once in V with a license-restricted annotation, not double-counted in a separate V-LR bloc. The "No PD ET: 9 voices" claim corrected — actual list contains 11 voices, all surfaced explicitly. New buckets sum cleanly to row count: V 9 + V-license-pending 2 + I 7 + G 2 = **20**. ✓
- **C-1J/IMPORTANT-1 — Yefet 7-12 evidence: STRENGTHENED in opposite direction (empirical reversal).** §2.3 row B3 + table + §5 + §6 revised. Re-fetched Margoliouth's djvu plain-text and grepped for running page-headers ("[CHAPTER. VERSE.] COMMENTARY ON DANIEL. PAGE"). Headers progress unbroken: `[VII. 4.]`→`[VII. 26.]`, `[VIII. 7.]`→`[VIII. 27.]`, `[IX. 1.]`→`[IX. 25.]`, `[X. 2.]`→`[X. 21.]`, `[XI. 1.]`→`[XI. 40.]`, `[XII. 2.]`→`[XII. 13.]`. English translation ends p. 87 at "XII. 13.] COMMENTARY ON DANIEL. 87". Margoliouth covers Daniel 1–12 in full; the prior "chs 1–6 only" claim was an OCR-marker-format misread. Yefet on Dan 7 is freely available in Judeo-Arabic + PD English at `archive.org/details/commentaryonbook00japhuoft` pp. 33-43. B3' (separate Yefet 7-12 GAP row) deleted; B3 row promoted to "Daniel 1-12 full".
- **C-1J/IMPORTANT-2 — CC-BY-NC reclassified as open-license-modern-faithful (not PD).** §3 PD-ET legend rebuilt as a three-state taxonomy (PD / OL-MF / LR), with quality labels (MF, W) treated as orthogonal. Table rows updated: A1 Rashi (Rosenberg, CC-BY) → OL-MF; C1, C2, C3 Talmud (William Davidson, CC-BY-NC) → OL-MF. Prior "Modern faithful PD ET available: 4" claim corrected — only Margoliouth 1889 (B3 Yefet) is pure PD; the others are open-licensed. New count: PD = 1; OL-MF = 4; LR = 1; license-pending = 2; None = 11.
- **C-1J/IMPORTANT-3 — Saadia/Hurvitz scope clarified.** §2.3 row B2 + §6.3.3 row + table rationale revised: Hurvitz 1977 thesis covers Saadia's Tafsir on **the Aramaic portion of Daniel only (Dan 2:4b-7:28)**. Daniel 7 sits inside that scope, so the M7-specific recoverability claim holds; chapters 1, 8–12 of Saadia's whole-book Tafsir remain a structural gap for free original-language recoverability in this audit. The audit no longer implies whole-book Saadia coverage from the Hurvitz candidate.
- **C-1J/IMPORTANT-4 — HebrewBooks 403 claim narrowed to tested-endpoints-only.** §1.2 (method) + §2.3 row B1 (Abrabanel) + §7 risks revised. "All HebrewBooks endpoints return 403" → "the specific HebrewBooks endpoints tested in this session (`/<id>`, `/pdf.aspx?req=<id>`, `/pdfpager.aspx?req=<id>&pgnum=N`, `/downloadhandler.ashx?req=<id>`) returned 403 under scripted-request / WebFetch." Repository-wide access conclusion withdrawn; alternate paths (browser direct-fetch, archive.org-hosted HebrewBooks scans, mirror sites, alternate UA strings) are explicitly noted as not exhaustively probed.

**Codex's MINOR findings (acknowledged; light edits where pertinent):**

- **MINOR 1 (Targum scope).** Adopted in §5 honest-gaps wording: narrowed to "classical canonical Targumim (Onkelos covers the Pentateuch; Jonathan covers the Prophets but not Daniel since Daniel sits in Ketuvim)" rather than the broader "no separate Targum / never targumized in the surviving tradition." Possible non-classical / fragmentary Aramaic reception witnesses are not in scope of the rabbinic-canonical claim.
- **MINOR 2 (Wave 6 sizing).** Codex confirmed sizing is acceptable; no change needed.

### Codex review pass 3 (advisory; NOT applied)

*Run: `codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high < prompt.txt > log.txt 2>&1` (codex-cli 0.125.0, model gpt-5.5, reasoning effort: high). Tokens used: 85,867. Codex was scoped to whether the D-1.6 corrections actually closed the codex pass-1 (D-1J) CRITICAL + IMPORTANT items and the D-1.5 codex pass-2 must-fix items, not a third pass on the underlying audit. Output is reproduced verbatim under the discipline that codex's findings are advisory and NOT applied during this session — PM is calling the audit final per the D-1.6 brief.*

```
## D-1.5 must-fix closure check
- M-1.5/A arithmetic: partial — §3 now sums cleanly at 5+3+2+3=13, but §6 still says "8 / 10 voices that actually wrote Daniel-engaging material" while including Lambert before Daniel engagement is verified.
- M-1.5/B Lambert demote: partial — §2.7/table/tally demote Lambert to INFERRED, but §4/§6 still treat Lambert too much like a normal Latin OCR/survey voice.
- M-1.5/C PG 70 listing-verified: partial — §2.2 and §3 label PG 70 listing-only, but line 337 still says "Mai vol. 2 + PG 70" is the load-bearing Greek primary path without the listing-only qualifier.
- M-1.5/D Lambert URL: closed — D-1.6 explicitly records a direct re-fetch confirming `GKtkAAAAcAAJ` as Lambert 1528 and keeps `bupgAAAAcAAJ` as the 1539 alternate.
- M-1.5/E Luther WA-DB-11/II: closed — §2.11 and table row 11 promote WA DB 11/II as canonical critical surface and reframe 1545 Wittenberg as witness/acquisition.

## D-1J critical + important closure check
- C-1J/CRITICAL-1 D1-D3 demote: closed — §2.4, §3 table/counts, backend notes, and §8 all classify D1-D3 as INFERRED/index-confirmed, not VERIFIED.
- C-1J/CRITICAL-2 arithmetic: closed — the table has 20 rows, and primary status buckets sum correctly: V 9 + V-license-pending 2 + I 7 + G 2 = 20.
- C-1J/IMPORTANT-1 Yefet 7-12: closed — the live sections now consistently say Margoliouth covers Daniel 1–12; remaining "1–6 only" references are historical/correction-context only.
- C-1J/IMPORTANT-2 CC-BY-NC: closed — C1-C3 are now OL-MF / CC-BY-NC and explicitly not PD; see new issue below for a separate PD count mismatch.
- C-1J/IMPORTANT-3 Saadia scope: closed — §2.3, table, language summary, and Wave 6.3 all limit Hurvitz/Saadia to Dan 2:4b–7:28.
- C-1J/IMPORTANT-4 HebrewBooks 403: closed — §1.2, B1, §7, and §8 narrow the claim to tested endpoints only, not repository-wide failure.

## Propagation check
- Patristic audit line 337 still treats "Mai vol. 2 + PG 70" together as the load-bearing Greek path, despite PG 70 being only listing-verified.
- Patristic audit lines 280/285 include Lambert in the Latin OCR backend map without an engagement-inferred qualifier; line 285 also says "6 voices" while listing 7.
- Patristic audit line 360 still says to "surface the canonical WA DB 11/II archive.org id" as an alternative future step, although D-1.6 already surfaced it.
- Jewish audit lines 913-918 say post-Wave 6.3 coverage includes "Metzudat David / Minchat Shai" and Ramban cross-refs, but those are not in Wave 6.1–6.3 and D1/D3 are deferred/INFERRED.

## Any NEW issues introduced by the D-1.6 corrections
- Jewish audit lines 691-693: "PD … 2 rows" includes C7 "N/A (no Targum exists)," then immediately says "Strictly: 1 actual PD ET"; this contradicts the D-1.6 correction log line 1026, which says PD = 1.
- Patristic audit line 285: "6 voices benefit" lists 7 names: Gregory, Bullinger, Œcolampadius, Lambert, Pellican, Melanchthon, Mede.
- Jewish audit lines 913-918: the "Total: 11 voices" narrative lists voices outside the stated waves, making the cumulative-effect prose unreliable even though the §3 audit-control arithmetic is fixed.

## Overall verdict
PASS-WITH-CONDITIONS — the main codex D-1.5 and D-1J blockers are materially closed in the audit-control sections, especially the core status tables and primary arithmetic. The remaining problems are propagation/stale-prose issues: a few backend/wave-planning surfaces still overstate or miscount after the D-1.6 corrections, and D-1J's ET availability count has one clear PD/N/A mismatch.
```

(End of codex pass-3 output. All 6 D-1J CRITICAL + IMPORTANT findings are at **closed** status; the new issue codex flags (PD count narrative inconsistency in §3 lines 691-693 and Wave-6 cumulative-effect narrative in §6 lines 913-918) is NOT applied per the D-1.6 brief — surfaced for D-2 PM follow-up. Audit is called final.)
