# Encrypted Volume Database Schemas

Discovered 2026-03-22 via `query-db` commands against each `.lbs*` file.

## Reference Encoding

### Two numbering systems:

1. **BIBLEXREFS** (text): `bible.{book}.{chapter}.{verse}` — Logos canonical numbering (same as binary)
2. **All binary databases**: Blob refs with Logos canonical numbering
   - OT 1-39: same as Protestant
   - NT: Protestant + 21 (Matthew=61, Romans=66, Revelation=87)
   - Apocryphal/Deuterocanonical: books 40-60

### Binary reference format:
- Single verse: `60 {book_hex} {chapter_hex} {verse_hex}` (4 bytes)
- Range: `61 {book1} {ch1} {v1} 60 {book2} {ch2} {v2}` (8 bytes)

### Sort key format:
- Binary, orderable. Book prefix (2 bytes) + chapter/verse encoding.
- Chapter byte ≈ `0x10 + chapter * 0x40`, verse byte = `verse * 0x10`

### Query pattern for binary databases:
```sql
WHERE hex(Reference) LIKE '60{book:02X}{chapter:02X}%'
   OR hex(Reference) LIKE '61{book:02X}{chapter:02X}%'
```

---

## BIBLEXREFS.lbslcr / bxrefs.db

Tables: Reasons, BibleReferences, CrossReferences, CrossReferenceReasons

**BibleReferences**: `Reference text` (e.g. "bible.45.1.8"), `StartSortKey blob`, `PastEndSortKey blob`
**CrossReferences**: `SourceReferenceId`, `TargetReferenceId`, `Score float`
**CrossReferenceReasons**: `ReasonId`, `ReasonData text`
**Reasons**: `Reason text`

Query pattern:
```sql
SELECT cr.Score, src.Reference, tgt.Reference, rsn.Reason
FROM CrossReferences cr
JOIN BibleReferences src ON cr.SourceReferenceId = src.ReferenceId
JOIN BibleReferences tgt ON cr.TargetReferenceId = tgt.ReferenceId
LEFT JOIN CrossReferenceReasons crr ON cr.CrossReferenceId = crr.CrossReferenceId
LEFT JOIN Reasons rsn ON crr.ReasonId = rsn.ReasonId
WHERE src.Reference LIKE 'bible.{book}.{chapter}.%'
ORDER BY cr.Score DESC
```

---

## THEOLOGY-XREFS.lbsxrf / CrossReferences.db
(Same schema for BIBLICAL-THEOLOGY-XREFS, CREEDS-COUNCILS-XREFS, GRAMMAR-XREFS)

Tables: CrossReferences, DataTypeReferences, Groups, GroupExpressions, Types, TypeExpressions

**CrossReferences**: `ArticleName text`, `ArticleTitle text`, `ResourceId text`, `TextRange text`, `CanonReferenceId` → DataTypeReferences, `GroupId` → Groups, `TypeId` → Types
**DataTypeReferences**: `Reference blob` (binary, Logos canonical), `DataType text` (e.g. "bible+lxx"), `StartSortKey blob`
**GroupExpressions**: `Label text` (e.g. "Reformed", "Lutheran", "Anglican")
**TypeExpressions**: `Label text` (e.g. "Theology Proper", "Christology")

Query pattern:
```sql
SELECT cr.ArticleName, cr.ResourceId, ge.Label as Tradition, te.Label as Topic
FROM CrossReferences cr
JOIN DataTypeReferences dtr ON cr.CanonReferenceId = dtr.DataTypeReferenceId
LEFT JOIN GroupExpressions ge ON cr.GroupId = ge.GroupId AND ge.Language = 'en'
LEFT JOIN TypeExpressions te ON cr.TypeId = te.TypeId AND te.Language = 'en'
WHERE hex(dtr.Reference) LIKE '60{logos_book:02X}{chapter:02X}%'
   OR hex(dtr.Reference) LIKE '61{logos_book:02X}{chapter:02X}%'
```

---

## PreachingThemes.lbsptd / preachingthemes.db

Tables: Theme, ThemeTitle, AlternateTerm, Reference, KeyPassage, Pericope, PericopeTheme, PericopeTitle, ThemeCategory, Category, Concept, ThemeConcept, Resource, TitleWord, AlternateTermWord

**ThemeTitle**: `Label text`, `Name text`, `Description text` (Language-filtered)
**Pericope** → Reference (blob, Logos canonical)
**PericopeTitle**: `Title text`
**PericopeTheme**: links Pericope → Theme

Query pattern:
```sql
SELECT pt.Title as Pericope, tt.Label as Theme, tt.Description
FROM Pericope p
JOIN Reference r ON p.ReferenceId = r.ReferenceId
JOIN PericopeTitle pt ON p.PericopeId = pt.PericopeId
JOIN PericopeTheme pth ON p.PericopeId = pth.PericopeId
JOIN ThemeTitle tt ON pth.ThemeId = tt.ThemeId
WHERE pt.Language='en' AND tt.Language='en'
  AND (hex(r.Reference) LIKE '60{logos_book:02X}{chapter:02X}%'
   OR hex(r.Reference) LIKE '61{logos_book:02X}{chapter:02X}%')
```

---

## BiblicalPlaces.lbsplc / biblicalplaces.db
(BiblicalPeople.lbsbpd, BiblicalThings.lbsthg use same entity schema)

Tables: Entities, EntityTitles, BibleReferences, EntityLemmaPhrases, EntityLemmaPhraseReferences, Regions, Names, NameLabels, etc.

**Entities**: `EntityReference text`, `Kind text`, `Rank double`, `Icon text`
**EntityTitles**: `Title text`, `Description text` (XML-formatted with embedded Bible refs)
**BibleReferences**: `Reference blob` (Logos canonical), `DataType text`, `StartSortKey blob`

Query pattern:
```sql
SELECT et.Title, et.Description, e.Kind, e.EntityReference
FROM EntityLemmaPhraseReferences elpr
JOIN EntityLemmaPhrases elp ON elpr.EntityId = elp.EntityId AND elpr.LemmaPhraseId = elp.LemmaPhraseId
JOIN Entities e ON elp.EntityId = e.EntityId
JOIN EntityTitles et ON e.EntityId = et.EntityId
JOIN BibleReferences br ON elpr.BibleReferenceId = br.BibleReferenceId
WHERE et.LanguageId = 2
  AND (hex(br.Reference) LIKE '60{logos_book:02X}{chapter:02X}%'
   OR hex(br.Reference) LIKE '61{logos_book:02X}{chapter:02X}%')
```
Note: LanguageId=2 appears to be English (1=German based on sample data).

---

## SupplementalData (.lbssd) — Figurative Language, Constructions, Literary Typing, etc.

Tables: DataTypeReferences, Extras, Resources, ReferenceAttachments, TextRangeAttachments, WordNumbers, WordNumberSetAttachments, WordNumberSets, SupportedBibleDataTypes, LocalizedStringKeys, LabelStrings

**DataTypeReferences**: Stores figure/construction category references (NOT Bible refs)
- DataType blob: "label", "flcat", "fltype", "flterm" (figurative language)
- Reference blob: encoded category/type identifiers

**WordNumbers**: `Reference blob` — encoded as `{length_prefix}gnt/{word_number}` or `{length_prefix}bhs/{word_number}`
**WordNumberSets** → WordNumberSetAttachments → DataTypeReferences: Links word ranges to categories
**LabelStrings**: Human-readable labels per language

**NOTE**: Querying by Bible passage requires knowing the GNT/BHS word number range for that passage. This mapping is not stored in the SupplementalData databases themselves — it must be derived from the interlinear data or an external word number index. DEFERRED for v2.

---

## ImportantWords.lbsiw / importantwords.db

Tables: Pericopes, Lemmas, Words, PericopeWordRelationships, BookScaleFactors

Schema columns truncated in CREATE TABLE output — needs further investigation.

---

## Book Number Reference

| Protestant # | Logos Canonical # | Book |
|---|---|---|
| 1-39 | 1-39 | Genesis–Malachi |
| 40 | 61 (0x3D) | Matthew |
| 41 | 62 (0x3E) | Mark |
| 42 | 63 (0x3F) | Luke |
| 43 | 64 (0x40) | John |
| 44 | 65 (0x41) | Acts |
| 45 | 66 (0x42) | Romans |
| 46 | 67 (0x43) | 1 Corinthians |
| ... | ... | ... |
| 66 | 87 (0x57) | Revelation |

Formula: `logos_book = protestant_book + 21` for NT (protestant_book >= 40)
