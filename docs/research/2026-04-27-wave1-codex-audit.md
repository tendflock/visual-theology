# Wave 1 supportStatus Codex Audit

## 1. Overview

Date: 2026-04-27.

Scope: independent Codex adversarial review of Wave 1 scholar JSONs, focused only
on citations currently labeled `supportStatus: "directly-quoted"`. The audit rule
was the same as the WS0c corpus audit: the quote alone must prove the rationale's
relevant sub-claim. Verified quote existence is not enough.

Files reviewed:

- `docs/PM-CHARTER.md`
- `docs/schema/citation-schema.md`
- `docs/research/2026-04-26-ws0c-corpus-audit.md`
- `docs/research/scholars/4-ezra-stone-hermeneia.json`
- `docs/research/scholars/wright-jesus-victory-of-god.json`
- `docs/research/scholars/augustine-city-of-god-book-20.json`
- `docs/research/scholars/hippolytus-anf5-daniel.json`
- `docs/research/scholars/newsom-breed-otl-daniel.json`

Codex command:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  -c model_reasoning_effort=high < /tmp/session-f-codex-prompt.txt \
  > /tmp/session-f-codex-log.txt 2>&1
```

Distribution reviewed:

| file | directly-quoted | paraphrase-anchored | summary-inference | dq flagged |
|---|---:|---:|---:|---:|
| `newsom-breed-otl-daniel.json` | 26 | 10 | 3 | 2 |
| `hippolytus-anf5-daniel.json` | 47 | 1 | 0 | 6 |
| `augustine-city-of-god-book-20.json` | 61 | 1 | 1 | 2 |
| `4-ezra-stone-hermeneia.json` | 38 | 0 | 0 | 5 |
| `wright-jesus-victory-of-god.json` | 35 | 0 | 0 | 2 |
| **Total** | **207** | **12** | **4** | **17** |

Codex verdict: 17 citation-level `directly-quoted` over-applications. Stone's
100% distribution is suspicious because several broad synthetic axes are anchored
by narrow quotes. Wright's 100% distribution is less suspicious; most direct
labels hold, with two synthetic/cross-book overreaches.

## 2. Per-citation relabel recommendations

### `4-ezra-stone-hermeneia.json`

`4-ezra-stone-hermeneia.json#L`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote proves Flavian identification, but not Stone's whole critical-historical method, source/redaction analysis, comparative apocalyptic method, or Hermeneia-style synthesis.
quote=`Therefore, the three heads should be regarded as the three Flavian emperors`
rationale_outrun=`Stone explicitly engages the principal methodological alternatives... source theory... dialogical-source theory... allegory-vs.-symbolic-structure`
```

`4-ezra-stone-hermeneia.json#L`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote proves Domitian dating for the vision, not the broader methodological profile claimed for Stone.
quote=`the date of the composition of the vision in the time of Domitian`
rationale_outrun=`standard Hermeneia historical-critical synthesis`
```

`4-ezra-stone-hermeneia.json#L`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote proves the Domitian date, but the rationale claims a broad adjudication of source, redaction, tradition-history, and literary-structural method.
quote=`composed in the time of Domitian`
rationale_outrun=`adjudicates among them by close attention to the book's literary structure and the comparative material`
```

`4-ezra-stone-hermeneia.json#C`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote only supports an eschatological pride motif; it does not prove the Dan 7:8/11/25 little-horn mapping, antichrist associations, collective-Rome reading, or resistance to a single-individual identification.
quote=`The pride of sinners recurs in the book in an eschatological context`
rationale_outrun=`Dan 7:8, 11, 25 as the loci classici... the antichrist associations... plural "them"... Roman emperors in general`
```

`4-ezra-stone-hermeneia.json#H`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote directly proves only that the messianic kingdom is temporary; the rationale synthesizes a multi-stage eschatological sequence across several sections.
quote=`The messianic kingdom will come to an end; it is not eternal.`
rationale_outrun=`present age... messianic woes... destruction of Rome... temporary messianic kingdom... death of the Messiah... resurrection... final judgment`
```

### `wright-jesus-victory-of-god.json`

`wright-jesus-victory-of-god.json#N`:

```text
current=directly-quoted
recommended=paraphrase-anchored
reason=The quote says only that three Daniel passages stand behind the argument; it does not identify Dan 7:25, 11:31, and 9:26-27 or prove the full Mark 13 / Mark 14 / Daniel / Psalm 110 integration.
quote=`Behind this in turn, of course, there stand three passages in Daniel`
rationale_outrun=`Dan 7:25, 11:31, and 9:26-27 as overlapping vindication/desolation texts`
```

`wright-jesus-victory-of-god.json#crossBook: Matt 24`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports Wright's anti-literalist reading of cosmic-collapse language, but it does not by itself prove the Matt 24 parousia-language, abomination citation, AD 70 setting, or Mark/Matthew synthesis.
quote=`It is crass literalism... to insist that this time the words must refer to the physical collapse`
rationale_outrun=`Matthew's Olivet Discourse... parousia-language... abomination-of-desolation citation... AD 70 vindication`
```

### `augustine-city-of-god-book-20.json`

`augustine-city-of-god-book-20.json#crossBook: Rev 13`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports Augustine's corporate-or-personal Antichrist option from 2 Thessalonians, not a direct Rev 13 reading.
quote=`Antichrist means not the prince himself alone, but his whole body`
rationale_outrun=`Revelation 13 beast imagery is folded into the broader Antichrist account but not given dedicated exegesis`
```

`augustine-city-of-god-book-20.json#crossBook: Rev 13`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports a possible Roman-empire restrainer reading in 2 Thessalonians, but not Rev 13 beast exegesis.
quote=`refer to the Roman empire`
rationale_outrun=`This citation cluster therefore points at how Augustine's Antichrist-doctrine functions for Rev 13`
```

### `hippolytus-anf5-daniel.json`

`hippolytus-anf5-daniel.json#F`:

```text
current=directly-quoted
recommended=paraphrase-anchored
reason=The quote names Christ's passion typology, but it does not prove the 6,000-year chronology, Christ-at-year-5,500 calculation, or Sabbath-millennium structure.
quote=`By the stretching forth of His two hands He signified His passion`
rationale_outrun=`places Christ incarnation at year 5,500... giving 500 years until the millennial Sabbath`
```

`hippolytus-anf5-daniel.json#N`:

```text
current=directly-quoted
recommended=paraphrase-anchored
reason=The quote is only the opening of 2 Thessalonians 2; it does not prove the Daniel/Revelation/Paul/Matthew synthesis.
quote=`Now we beseech you, brethren, concerning the coming of our Lord Jesus Christ`
rationale_outrun=`Daniel fourth beast = Revelation beast = Paul man of sin = Christ abomination of desolation`
```

`hippolytus-anf5-daniel.json#crossBook: Rev 17`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote reproduces Rev 17 whore imagery but does not prove Hippolytus's Rome/Babylon identification, Dan 7 overlay, or later reception significance.
quote=`the great whore that sitteth upon many waters`
rationale_outrun=`read against contemporary Rome... ten horns overlap Dan 7... foundational fusion`
```

`hippolytus-anf5-daniel.json#crossBook: Rev 17`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote proves the seven-heads/seven-mountains text, but not the broader Dan 7 + Rev 17 synthesis stated in the summary.
quote=`The seven heads are seven mountains`
rationale_outrun=`ten future kings overlap Dan 7 ten horns of the fourth beast`
```

`hippolytus-anf5-daniel.json#crossBook: Rev 20`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports a future Sabbath-kingdom motif, but the rationale itself admits Hippolytus does not cite Rev 20 directly and infers the Rev 20 link from the whole schema.
quote=`the Sabbath is the type and emblem of the future kingdom of the saints`
rationale_outrun=`unintelligible without a Rev 20 millennial reading`
```

`hippolytus-anf5-daniel.json#crossBook: Rev 20`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote proves the thousand-years-as-day premise, but not a direct Rev 20 millennium reading.
quote=`a day with the Lord is as a thousand years`
rationale_outrun=`the millennium of Rev 20 is read as the cosmic Sabbath`
```

### `newsom-breed-otl-daniel.json`

`newsom-breed-otl-daniel.json#crossBook: 1 En 37-71`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports a throne-scene parallel with 1 Enoch 14, not the Similitudes' messianic Son-of-Man trajectory or Animal Apocalypse judgment parallel.
quote=`1 En. 14:18-23 and Dan 7:9-10 provide details concerning the divine throne`
rationale_outrun=`Similitudes... develop Dan 7 humanlike-one figure into an eschatological messianic figure... Animal Apocalypse`
```

`newsom-breed-otl-daniel.json#crossBook: Rev 1; Rev 13`:

```text
current=directly-quoted
recommended=summary-inference
reason=The quote supports medieval Christ/Ancient-of-Days conflation from the OG variant, but not Rev 13 and only indirectly supports the Rev 1 reception summary.
quote=`Christ and the Ancient of Days are often conflated in medieval theology and iconography`
rationale_outrun=`Rev 1:13-14... Newsom does not engage Rev 13 beasts directly... Breed cites Rev 1:7`
```

## 3. Notes on overall distribution shape

Stone's 100% `directly-quoted` distribution is genuinely suspicious after audit.
The core Daniel/4 Ezra intertext citations mostly hold, but broad synthetic axes
L, C, and H are over-labeled. Axis L is the closest soft-edge case and Codex
recommended downgrading all three Domitian/Flavian-method citations to
`summary-inference`, because the quotes prove date or imperial identification but
not the broader methodological profile.

Wright's 100% `directly-quoted` distribution is not broadly suspicious. Most
quotes are unusually explicit and directly prove the stated subclaims. The weak
points are the synthetic axis N integration row and the Matthew 24 row, where one
quote anchors a wider Synoptic argument.

Across all five files, Codex recommended 17 citation-level relabels:

| recommended label | count |
|---|---:|
| `paraphrase-anchored` | 3 |
| `summary-inference` | 14 |

The flagged pattern largely matches the prior WS0c audit's risk class:
cross-book rows, reception synthesis, and broad method/system summaries are more
likely to outrun a single quote than narrow exegetical claims.

## 4. Items not flagged

Stone Axis B holds up well: quotes explicitly say Daniel's fourth kingdom is
Greek "but here it is Rome," and that the verse sets up `eagle/fourth
empire/Rome`.

Stone Axis J holds up: the quotes directly support Daniel 7 dependence, clouds
imagery, Son-of-Man language, divine-warrior imagery, and the
dream/interpretation gap.

Wright Axis J and O hold up: the quotes directly state earth-to-heaven
vindication, Mark 13's Temple-destruction fulfillment, Jesus' Danielic
representative role, and within-a-generation vindication.

Augustine Rev 20 holds up despite its density: the citations directly cover the
thousand years, Satan's binding, first resurrection, present reign, and final
judgment.

Newsom Axis J holds up: the quotes directly support the Michael/angelic-being
identification, the holy-ones-as-angels argument, and the Qumran War Scroll
comparison.

Recommendation status: not applied. This document is a PM dispatch artifact only.
