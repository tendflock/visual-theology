# Open Empirical Homiletics

## An Open Invitation to Build the First Distributed Research Collaborative on Sermon Effectiveness

**Author:** Bryan Schneider, an independent non-institutional Reformed Presbyterian pastor
**Date:** 17 April 2026
**Version:** 0.1 (invitation draft, seeking adoption)
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
**Contact:** `empirical.homiletics@gmail.com`
**Repository:** *see GitHub link*
**DOI:** *to be minted on SocArXiv publication*

---

## Abstract

"What makes a sermon great?" is one of the oldest questions in Christian practice and one of the least empirically studied. Historical homiletics (Aristotle, Quintilian, Augustine, Chrysostom, the Puritans, Robinson, Chapell, Beeke) offers a rich library of asserted but untested claims. Modern empirical work in communication, computational rhetoric, and narrative persuasion has developed methodologies that could test those claims but has rarely been applied to sermons. This document proposes an open, pre-registered, multi-denominational, distributed research collaborative — modeled on the Psychological Science Accelerator and ManyBabies — to empirically identify what measurable properties of sermons predict hearer-centered outcomes (comprehension, encoding, activation) across traditions. It sets out the research question, the landscape of prior work, a scientifically defensible methodology, a concrete first study, a governance model, named candidate collaborators, IRB and funding paths, and honest failure modes. The author does not intend to lead this work; he lacks the time, credentials, and institutional position. The design is released under CC BY 4.0 so that anyone with the right combination of training, time, and network can adopt it, adapt it, and run with it. If that's you, please reach out.

---

## Preamble: What This Document Is And Isn't

This is an invitation. It is not a claim to have done the research it describes, and it is not a plan the author intends to execute.

The author is a Reformed Presbyterian pastor preaching weekly to a congregation of roughly eighty people. He has ADHD, limited research time, no academic credentials in homiletics or communication research, and no institutional affiliation capable of hosting IRB review. He originally began investigating these questions to build a personal sermon-analysis tool. Through three months of research — including adversarial and associate-mode consultation with frontier AI research agents (Claude Opus, OpenAI Codex) and extensive literature review — it became clear that the scientifically solid version of this project is a multi-year distributed research program requiring institutional backing, funding, formal ethics review, and a methodologist co-lead. None of those are within the author's realistic reach.

Rather than abandon the research design, the author has chosen to release it as an open invitation. The research question is real. The gap is real. The design is credible. The methodology is publishable. What is missing is a credentialed, time-rich convener with a network in empirical homiletics, communication research, or practical theology.

The goal of this document is adoption, not collaboration on execution. If you are interested in picking this up, the author's explicit intent is to cede direction. If you are interested in partial collaboration (e.g., as a contributor to a first study) the author welcomes that too. If you know someone who should read this, please forward it.

---

## 1. The Research Question and Why It Matters

**What measurable properties of sermons actually correlate with hearer-centered outcomes, across traditions and contexts?**

The question decomposes into two halves:

1. What are hearer-centered outcomes? (comprehension, encoding, activation, recall at 48-72 hours, perceived relevance, felt emotional force, behavioral intention)
2. What properties — rhetorical, structural, linguistic, prosodic, theological — predict which outcomes?

The question is old. Aristotle proposed ethos, pathos, and logos. Augustine proposed teaching, delighting, and moving. The Puritans proposed plain-style exposition. Robinson proposed the "Big Idea." Chapell proposed the Fallen Condition Focus. Beeke proposed experiential application. Each of these is a *falsifiable claim* about what makes preaching effective. Each has been asserted, debated, and taught for decades or centuries. Almost none has been empirically tested.

Meanwhile, sermons are one of the most-delivered forms of public address in human history. In the United States alone, a Pew Research study (2019) estimates tens of thousands of sermons are delivered each weekend, reaching roughly a third of adults. Sermon effectiveness matters for pastoral formation, for lay spiritual life, and for church health. It matters to seminaries teaching preaching and to pastors refining their craft. And yet no one has published a defensible empirical methodology for measuring it.

The stakes of the question are not purely pastoral. There is a genuine methodological gap in rhetoric and communication research. Sermons are a particularly clean testbed for questions about oral persuasion: they are long-form, repeated weekly by the same speaker to the same audience, recorded and archived at scale, and delivered with an explicitly stated intent to change belief, affect, and behavior. If any genre of public speech permits rigorous empirical analysis of effectiveness, sermons do.

---

## 2. Landscape: What's Been Done

### 2.1 Empirical Homiletics as an Established Subfield

There is a small, mostly European tradition of empirical homiletics research. The most methodologically self-aware contributions are:

- **H.J.C. Pieterse** (University of South Africa) — beginning in 1983-84 with quantitative content analysis of sermons paired with listener response data. Pieterse's 2020 retrospective in *Acta Theologica* ("A short history of empirical homiletics in South Africa") is the best single overview of the field's methodological evolution.
- **Theo Pleizier** (Protestant Theological University, Netherlands) — his 2010 dissertation *Religious Involvement in Hearing Sermons: A Grounded Theory Study in Empirical Theology and Homiletics* is the most rigorous published listener-reception study to date. Pleizier deliberately chose grounded-theory qualitative methods over quantitative measurement.
- **F. Gerrit Immink** and students (Groningen/Utrecht) — further qualitative reception work.
- **Allen, Andrews, Bond, Moseley, Ramsey, McClure** — the Lilly-funded *Listening to Listeners: Homiletical Case Studies* (Chalice, 2004), 263 interviews across 28 congregations. Its central finding: listeners process sermons through a dominant ethos, pathos, or logos "setting," and perceived relationship with the preacher outweighs rhetorical technique.
- **Societas Homiletica's seven-country "Preaching in Times of the European Refugee Crisis" study** (Lorensen, Kaufman, Deeg et al.) — the closest existing precedent for distributed, multi-site, cross-tradition empirical homiletics. One-off, grant-funded, institutionally hosted.

### 2.2 Computational Corpus Work

- **Pew Research "Digital Pulpit"** (2019): 49,719 sermons from 6,431 U.S. congregations, machine-transcribed over an eight-week scrape. Full methodology public; raw corpus not released. Proves corpus-scale analysis is tractable.
- **Baylor Historical Sermon Corpus** (Gale Digital Scholar Lab): ~8,000 sermons 1652-1819, publicly accessible, Voyant-compatible.
- **TCNSpeech**: 24 hours of Nigerian English sermon audio released for ASR research.

None of these corpora are linked to reception outcomes.

### 2.3 Adjacent-Field Methodologies Directly Transferable to Sermons

These are not homiletics papers, but their methods apply:

- **Danescu-Niculescu-Mizil, Cheng, Kleinberg, Lee** (2012), "You Had Me at Hello: How Phrasing Affects Memorability," ACL. Methodological template: compare memorable quotes with same-character same-scene non-memorable quotes. Finding: memorable lines combine lexical distinctiveness with common syntactic scaffolding and portability. Human validation accuracy ~78%.
- **Gennaro & Ash** (2025), "Computational analysis of US congressional speeches reveals a shift from evidence to intuition," *Nature Human Behaviour*. Operationalizes an Evidence-Minus-Intuition score via word-list dictionaries over embeddings. Code open at `github.com/saroyehun/EvidenceMinusIntuition`. Directly adaptable to sermon rhetoric.
- **Green & Brock** (2000), "The Role of Transportation in the Persuasiveness of Public Narratives," *JPSP*. Validated Transportation Scale. Short form (TS-SF, six items) available (Appel et al.).
- **Bullock, Shulman, Huskey** (2021), preregistered finding that narrative persuasion operates partly through processing fluency rather than identification alone.
- **Mar, Li, Nguyen, Ta** (2021), "Memory and comprehension of narrative versus expository texts," *Psychonomic Bulletin & Review*. Meta-analysis of ~75 samples. Stories recalled and understood better; the effect is robust. Note: the popular "stories are remembered 6x better than propositions" figure traces to a 1969 word-list mnemonic study and is not sermon-specific folklore.
- **Kiritchenko & Mohammad** (2017), "Best-Worst Scaling More Reliable than Rating Scales," ACL. BWS dominates Likert at equal annotation budget.
- **McCroskey & Teven** (1999), validated Source Credibility Scale (18 items, three factors).

### 2.4 Commercial Products

- **SermonScore.ai** markets sermon analysis "calibrated against elite communicators" across 14 categories. Methodology is closed. Reference corpus is undisclosed.
- **Pulpit AI**, **Sermonly**, **SermonAi** — repurposing and drafting tools; no benchmark-quality measurement claim.

None of these publish validation evidence. A transparent, pre-registered, open-methodology alternative would by construction be a contribution the commercial products cannot make.

---

## 3. The Gap

Despite the activity above, no one has:

1. Published a defensible methodology for operationalizing sermon effectiveness as one or more measurable constructs.
2. Empirically tested historical homiletical claims (Big Idea, FCF, experiential preaching, ethos/pathos/logos ratios) against modern reception data.
3. Built an open, pre-registered, multi-tradition sermon corpus with linked reception outcome labels.
4. Validated a sermon-listening measurement instrument. (The *Homiletic* journal's 2018 review explicitly notes this absence.)
5. Applied computational memorability or persuasion methodology to sermons at scale.

This is the gap this collaborative would fill.

---

## 4. Proposed Research Design

What follows is a design framework, not a finalized protocol. The first serious Phase 0 work is to narrow it to a single pre-registered study.

### 4.1 Construct Decomposition

"Greatness" is not one construct. Any attempt to collapse it will fail. The design proposes four separable constructs, with the fourth demoted to a secondary descriptive layer:

1. **Rhetorical craft** — degree to which a sermon is organized, intelligible, stylistically effective, and orally processable in real time.
2. **Immediate reception efficacy** — degree to which listeners can follow the sermon, remain engaged, and accurately encode its central claims during and shortly after exposure.
3. **Transformative activation** — degree to which the sermon produces short-run movement in belief salience, affect, intention, or self-reported motivation.
4. **Historical-cultural influence** — degree of persistence, diffusion, citation, anthologization, or reuse. This is heavily confounded by preacher fame, publishing institutions, and historical contingency. It should be treated as a secondary external-validity variable, not as primary ground truth.

### 4.2 Dependent Variables

Multi-DV convergence should be required. For each primary construct, collect multiple independent measures and require agreement across at least two.

Two independent rater panels:

- **Homiletics expert panel** — 8-12 trained raters, balanced across four or more traditions. Evaluate rhetorical craft only.
- **Lay listener panel** — 80-150 adult listeners, stratified by age, sex, denomination familiarity, education, and tradition. Evaluate reception and activation only.

Measurement instruments:

- Craft: custom behaviorally-anchored 1-7 rubric (5-7 dimensions). Pre-register before data collection.
- Reception: comprehension items (6-10 MCQ or short answer), immediate free recall (idea units, coded), delayed recall at 48-72 hours.
- Activation: pre/post belief-salience items, short PANAS or PAD affect, behavioral intention, optional one-week follow-up on action.
- Panel-rating preference: **Best-Worst Scaling** (Kiritchenko & Mohammad 2017) over Likert at same annotation budget.

### 4.3 Sampling Frame

Target population recommended: *contemporary English-language Christian sermons delivered orally to adult congregational audiences in North America, 2005-present, 18-50 minutes.* This keeps language, register, and audience sufficiently stable for inference.

Stratification variables:
- Tradition (Reformed/Presbyterian, Baptist, Anglican, Methodist/Wesleyan, Pentecostal/Charismatic, non-denominational evangelical, Black Protestant, liturgical/Catholic as scope permits).
- Format (expository, topical, narrative, liturgical).
- Sermon length bands.
- Preacher sex.
- Congregation size bands (where known).
- Era band (2005-2014, 2015-present).

Inclusion: full audio, producible transcript, adult congregational context. Exclusion: youth talks, conference keynotes, heavily edited broadcast material, multi-speaker services.

### 4.4 Feature Operationalization

Three classes with strict rules:

- **Automatic features** (open-source NLP): lexical diversity, concreteness (Brysbaert norms or Yeomans measure), readability, syntactic depth, type-token ratio, repetition metrics, discourse-marker counts, story/exposition proportions, surprisal from a small language model, prosody proxies (speech rate, pause distribution, pitch variance) from audio.
- **Human-coded features**: Big Idea clarity, explicit proposition statement, application specificity, Christological integration, fallen-condition-focus framing, theological density, transition explicitness, call-to-response specificity. Coding by three independent raters minimum. Inter-rater reliability threshold: **Krippendorff's α ≥ 0.67** minimum usable, **≥ 0.80** target for any feature entering confirmatory tier.
- **Panel-rated features**: ethos, sincerity, burden clarity, relevance, oral naturalness, emotional force.

Hard rule for LLM-derived features: **no purely LLM-derived feature may appear in confirmatory analysis unless it has been human-validated against manual coding on a held-out subset.** Otherwise exploratory only.

### 4.5 Pre-registration and Falsification

- OSF pre-registration required. Template hybrid of AsPredicted 9-question format + STROBE 22-item observational checklist + Biber-style corpus-design documentation.
- Campbell-Fiske Multitrait-Multimethod (MTMM) matrix for construct validity: pre-specify convergent and discriminant validity predictions before data collection.
- **Maximum 10-15 confirmatory hypotheses**; remaining claims become tier-2 exploratory.
- "Supported": directional consistency + multiplicity-adjusted significance + standardized β ≥ 0.10 + convergence across ≥ 2 independent DVs.
- "Falsified": CI tight enough to exclude the Smallest Effect Size of Interest (SESOI, proposed r ≈ 0.10-0.15), or sign opposite prediction with adjusted significance.
- **Specification-curve analysis** (Simonsohn-Simmons-Nelson 2020; `specr` R package) as robustness supplement against the garden of forking paths (Gelman & Loken 2013).

### 4.6 Statistical Analysis Plan

- **Primary model**: multilevel regression, listeners nested in sermons nested in preachers. Fixed effects for tradition, length, era, delivery medium, topic/text category. Random intercepts for preacher and sermon.
- **Multiplicity correction**: Holm for the 10-15 confirmatory hypotheses; Benjamini-Hochberg FDR for exploratory branches.
- **Effect-size metrics**: standardized β for continuous predictors, odds ratios for binary outcomes, incidence-rate ratios for count outcomes.
- **Feature-family handling**: cluster correlated features into conceptual families (fluency, narrative, rhetorical structure, application, delivery); within confirmatory testing, use one preregistered representative feature per family per DV. Penalized regression or Bayesian shrinkage on the exploratory side.
- **Benchmark baseline**: every feature must demonstrate predictive value over a metadata-only model (preacher + length + tradition + topic). Features that do not beat this baseline do not go in the engine.

### 4.7 Validation and Replication

- **Three-step out-of-sample strategy**:
  1. Development set (build and tune operationalizations).
  2. Locked hold-out set (untouched until confirmatory analysis is finalized).
  3. Cross-corpus replication (distinct source mix, distinct preachers, ideally distinct tradition balance).
- **Temporal hold-out validation** is mandatory given replicated failure modes in hit-song and TED engagement prediction. Train on pre-2015 sermons; test on 2015-present, or vice versa.
- **Accuracy metrics**: variance explained in primary DVs, calibration of predicted outcome scores, rank-order agreement, improvement over baseline.
- **For 2-3 marquee claims**: a prospective experimental manipulation (e.g., rewriting a sermon excerpt in dense-exegetical vs. narratively-framed-with-refrain versions; measuring causal effect on comprehension and recall) to move beyond observational inference.

### 4.8 Repeatability

- Open code (preprocessing, feature extraction, modeling, figures).
- Open codebook, coder-training documentation, rating instruments.
- Open derived feature tables at sermon level.
- De-identified panel ratings and outcome data.
- Pre-registration and deviations log.
- Raw sermon audio/video stays closed unless licensing is explicit.
- Reproducibility stack: OSF + GitHub + Docker + Snakemake (or equivalent workflow manager).

---

## 5. Candidate First Study

Per the precedent of ManyBabies, ManyPrimates, and PSA, the first study should be aggressively narrow. A recommended candidate:

- **N = 20 sermons**, stratified across 5 traditions (Reformed, Baptist, Methodist, Pentecostal, Black Protestant).
- **400 lay raters** via Best-Worst Scaling on 90-second excerpts (5 hearer-centered questions per excerpt).
- **8-12 expert raters** on full sermons, craft rubric only.
- **One primary outcome**: immediate comprehension, measured by 6-item MCQ.
- **Secondary outcomes**: 48-72h recall, perceived relevance, transportation.
- **Target venue**: **PCI Registered Reports** (humanities-accepting, routes to partner journals) or **PLOS ONE RR**. Backup: pitch *Journal of the Evangelical Homiletics Society* or *Homiletic* to become the first homiletics journal to accept Registered Reports.
- **Timeline**: 18 months Stage 1 pre-registration through Stage 2 publication.

This is enough to publish a credible methods+findings paper, validate or refute a handful of specific historical claims (Big Idea clarity → comprehension being the most obvious candidate), and build the infrastructure for a larger Phase 2 study.

---

## 6. Governance

Governance is borrowed directly from Psychological Science Accelerator and ManyBabies, and scaled by phase.

### Phase 0 (2-4 founding builders)

- Founding convener
- Three-person steering group
- Named methods lead
- Named data/ethics custodian

No formal advisory board. Two or three informal senior advisors welcome.

### Phase 3 (50+ contributors, if and when reached)

- Elected steering committee of 5-7
- Standing methods/protocol committee
- Ethics and data-governance committee
- Authorship/publication committee (CRediT taxonomy per project)
- Recruitment/outreach committee
- Optional advisory board of 4-6 senior figures

### Decisions That Need Explicit Governance From Day One

- Mission and scope.
- Primary study question.
- Protocol freeze / pre-registration sign-off.
- Protocol changes (rare after data collection; require supermajority and public change log).
- Authorship rules (PSA and ManyBabies both formalized these; do not leave fuzzy).
- Data custody and access to raw identifiable data (one custodian, never "everyone in the Slack").
- New claims and secondary analyses (open proposal process; analysis lead checks overlap with pre-registration).
- Disputes, conduct, and removals (code of conduct from day one).

---

## 7. Candidate Collaborators

Named below are individuals with publicly-stated interests suggesting they might be sympathetic to this project. Inclusion is *not* a commitment. None has been approached. These are suggestions for whoever adopts the project to consider, not assumptions of availability.

### Tier 1 — highest prior probability given public signals

- **Theo Pleizier** (Protestant Theological University, Netherlands). President of Societas Homiletica (2022-). Author of the only grounded-theory empirical homiletics PhD. Maintains a public GitHub account (`github.com/ttjpleizier`) — an unusually strong technical-fluency signal for a homiletician. Leads the one existing empirical-homiletics network in Europe. If any single person can turn this from "random pastor's Facebook idea" into "official Societas initiative" overnight, it is Pleizier.
- **Tone Stangeland Kaufman** (MF Norwegian School of Theology). Co-author on the Societas seven-country refugee preaching study. Self-describes as focused on "methodological issues related to empirical research in theology."
- **David Schnasa Jacobsen** (Boston University School of Theology). 2025 Academy of Homiletics lifetime achievement recipient. Directs the multi-year Homiletical Theology Project — already runs consultation-based collaborative research.

### Tier 2 — strong bridge value, would likely take the meeting

- **Jared Alcántara** and **Matthew Kim** (Baylor/Truett). Direct Baylor's PhD in Preaching. Alcántara's framework in *Practices of Christian Preaching* is skill-competency-based, which maps onto rating instruments. Kim has published empirical ethnographic fieldwork on Korean American preaching.
- **Frank A. Thomas** (Christian Theological Seminary, Indianapolis). Runs the Mixed Methods Preaching Conference — the most methods-forward event in North American homiletics.
- **Sunggu Yang** (George Fox Evangelical Seminary). Former *Homiletic* managing editor; publishes on digital homiletics.

### Tier 3 — advisory tier, prestige magnets

- Luke Powery (Duke Chapel and Divinity School)
- Hershael York (Southern Baptist Theological Seminary; dean)
- Alexander Deeg (Leipzig; prior president of Societas Homiletica)
- Cleophus LaRue (Princeton Theological Seminary, emeritus)

### Tier 4 — the people who will actually do the work

Current PhD students and ABDs in homiletics and practical theology. Specifically worth targeting:
- Christian Theological Seminary's African American Preaching and Sacred Rhetoric program.
- Baylor Truett PhD in Preaching cohort.
- Princeton Theological Seminary practical theology.
- Duke Divinity homiletics and liturgics.
- Vanderbilt Homiletics and Liturgics program.
- Protestant Theological University (Netherlands) homiletics PhD pipeline.
- Academy of Homiletics recent workgroup papers with "empirical," "quantitative," "reception," or "ethnography" in their abstracts.

Tenured faculty sign on late; ABDs and recent PhDs are the ones who will do the work. Any adoption strategy that neglects Tier 4 will stall.

---

## 8. IRB Path and Funding

### IRB

A listener-rating study with identifiable participant data is human-subjects research. Self-certification of exemption is not permitted under 45 CFR 46.

- **Advarra IRB** explicitly accepts non-institutional submissions for online minimal-risk research. Typical cost for initial minimal-risk review: $1,500-3,500. Turnaround: 2-4 weeks after complete materials. Budget $3,000-5,000 year one.
- **Solutions IRB**: $1,200 initial exempt, $2,100 initial expedited social-behavioral; advertised 24-hour turnaround on complete submissions; free 15-minute consultation.
- **Better still**: a co-PI at a seminary or university can submit to their institutional IRB at zero cost. Duke's campus IRB covers Divinity School research; Vanderbilt has a dedicated SBER IRB. This is one more reason co-founder recruitment is the first real task.

### Funding

- **Louisville Institute Pastoral Study Project Grant** ($20,000). Explicitly includes "independent researchers and writers." Viable bridge funding for Phase 0.
- **Templeton Foundation Religion, Science, and Society small grants** (up to $260,000). Year-2 or Year-3 target.
- **Calvin Institute of Christian Worship Vital Worship, Vital Preaching Grants**. Institutional applicants only.
- **Lilly Endowment Compelling Preaching Initiative** ($95M program, 81 institutional grantees). Institutional co-applicant required; not available to independent researchers alone.
- **Experiment.com** or small crowdfunding for pilot-stage expenses.

### Cost Envelope (Rough)

- Phase 0 (6 months): ~$500 (domain, OSF is free, small design consulting, modest outreach). Mostly time.
- Phase 1 pilot (Study 1, 18 months): $15,000-30,000. IRB $3,000-5,000. Lay panel on Prolific for 400 raters × $3-5 per 30-minute task ≈ $5,000-10,000. Expert rater honoraria (optional) $2,000-4,000. Software/infrastructure minimal. Reserve for unexpected $3,000-5,000.
- Phase 2 (scaling to 120-180 sermons with full listener study): $75,000-150,000. Grant-scale funding required.

---

## 9. Failure Modes

Every failure mode below has been documented in comparable collaboratives. Plan for each.

1. **Construct failure.** "Great sermon" is too broad. If the first study tries to operationalize the whole phrase, the project dissolves into theology. Narrow to separately-rated outcomes: clarity, relevance, emotional engagement, memorability, theological depth.
2. **Confessional capture.** Reformed, Pentecostal, Black Church, and Catholic listeners may not mean the same thing by "faithful," "powerful," or "anointed." Stratify by tradition or confuse disagreement with noise.
3. **Halo effects.** Ratings track preacher attractiveness, celebrity, audio quality, race, gender, or doctrinal agreement more than sermon quality. Acharyya et al. (2020) documented this for TED ratings. Build in demographic covariates and sensitivity analyses.
4. **Training burden.** Humanities ratings are not like labeling galaxies. The 2026 citizen social science review (Matthes & Freiling) stresses that theory, measurement, interpretation, and dissemination all demand rater training. Simplified methods compromise data quality.
5. **Volunteer exhaustion.** Long horizons kill projects. ~75% of citizen-science projects produce no peer-reviewed paper; median time to publication exceeds 9 years.
6. **Founder bottleneck and solo-PI fragility.** Well-documented in digital humanities. Mitigation: recruit a methodologist co-lead by month three of Phase 0, not later.
7. **Authorship disputes.** Mitigation: CRediT taxonomy in written collaboration agreements signed before data collection, per ManyBabies and PSA.
8. **Protocol drift across sites.** A rolling corpus across U.S. traditions will drift without rigorous coordination. Mitigation: operating manual, site-coordinator training videos, pre-registered deviation-reporting protocol.
9. **Journal apathy.** No homiletics journal currently accepts Registered Reports. Mitigation: publish via PCI Registered Reports or PLOS ONE first; build homiletics-journal uptake later.
10. **Ownership resentment.** Churches submitting recordings, faculty designing the study, and lay listeners doing rating labor will all feel ownership differently. Mitigation: explicit, early, written attribution policy.

---

## 10. Why The Author Can't Lead This

Honest disclosure from the author: I am a Reformed Presbyterian pastor preaching weekly to approximately eighty people. I have ADHD. I have limited discretionary research time. I hold no graduate degree in homiletics, communication studies, or a quantitative discipline. I have no institutional affiliation capable of hosting IRB review, and no existing network within the empirical homiletics community.

I started investigating these questions because I wanted a sermon-analysis tool for my own preparation. Over several weeks of iterated research, it became clear that the scientifically defensible version of this question is a multi-year distributed research program requiring institutional partners, grant funding, formal ethics review, and a methodologist co-lead. None of those are within my reach, and pretending otherwise would be dishonest. The most-documented failure mode of projects like this one is a founder investing months of infrastructure work as a productive-feeling substitute for the hard task of recruiting credentialed collaborators. I am choosing not to fail that way.

What I can offer is this document, the time I've already spent thinking it through, an open GitHub repository, and a willingness to answer questions or make connections. What I cannot offer is ongoing leadership.

---

## 11. How To Take This Forward

If you are considering adopting this project, the concrete Phase 0 is roughly:

1. **Fork or clone the repository**. Add yourself as maintainer. The CC BY 4.0 license permits this.
2. **Refine the first-study protocol**. Narrow to exactly one primary outcome. Tighten exclusions. Draft the coding manual for any human-coded features.
3. **Pre-register on OSF** as a draft.
4. **Send Pleizier the email template** in the repo. Ask whether Societas Homiletica would formally host this as a working group. A yes there changes the project's institutional footing overnight.
5. **Recruit a methodologist co-lead** — communication research, rhetoric, linguistics, quantitative psychology, or corpus linguistics. The homiletics community will not legitimize quantitative claims without this.
6. **Secure IRB home**. Best: via institutional co-PI. Fallback: Advarra or Solutions IRB.
7. **Post the signal test**. Academy of Homiletics listserv + Reformed preaching communities + a Google Form collecting qualified interest. Measure response at 30 days. Fewer than 10 qualified responses = wind down gracefully and publish the protocol as a standalone proposal. 30+ = proceed to Phase 1.
8. **Apply for Louisville Institute Pastoral Study Project** (or equivalent independent-researcher bridge funding) as Phase 1 support.

### Gate Structure

Success in the next 6-12 months is not "solve what makes a sermon great." Success is:

- **Gate 1 (month 3)**: methodologist co-lead secured, Societas or Academy umbrella confirmed.
- **Gate 2 (month 6)**: 30+ qualified signups from the signal-test posting.
- **Gate 3 (month 9)**: Registered Report Stage 1 accepted at PCI RR or PLOS ONE.

If any gate fails, wind down gracefully and publish the protocol as a standalone proposal. That alone is a contribution.

---

## 12. Contact and Adoption Pathway

- **Email**: `empirical.homiletics@gmail.com`
- **Repository**: *GitHub link to be added on publication*
- **Preprint DOI**: *SocArXiv DOI to be added on publication*

If you want to adopt, fork the repository, email the address above, and introduce yourself. The author will respond, help with handoff, and step back.

If you want to contribute partially rather than lead, say so in your email; the author will connect you with the adopter if one emerges.

If you want to simply comment, critique, or push back on the design, open an issue on the repository.

---

## References (selected)

- Acharyya, R., et al. (2020). Bias analysis of the Ted talk ratings dataset. *arXiv*:2003.00683.
- Allen, R. J., Andrews, D., Bond, L. S., Moseley, D., Ramsey, G. L., & McClure, J. S. (2004). *Listening to listeners: Homiletical case studies*. Chalice Press.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. *Journal of the Royal Statistical Society: Series B*, 57(1), 289-300.
- Biber, D. (1993). Representativeness in corpus design. *Literary and Linguistic Computing*, 8(4), 243-257.
- Bradbury, N. A. (2016). Attention span during lectures: 8 seconds, 10 minutes, or more? *Advances in Physiology Education*, 40(4), 509-513.
- Bullock, O. M., Shulman, H. C., & Huskey, R. (2021). Narratives are persuasive because they are easier to understand. *Frontiers in Communication*, 6, 719615.
- Campbell, D. T., & Fiske, D. W. (1959). Convergent and discriminant validation by the multitrait-multimethod matrix. *Psychological Bulletin*, 56(2), 81-105.
- Danescu-Niculescu-Mizil, C., Cheng, J., Kleinberg, J., & Lee, L. (2012). You had me at hello: How phrasing affects memorability. *Proceedings of ACL 2012*.
- Gelman, A., & Loken, E. (2013). The garden of forking paths. Unpublished manuscript, Columbia University.
- Gennaro, G., & Ash, E. (2025). Computational analysis of US congressional speeches reveals a shift from evidence to intuition. *Nature Human Behaviour*.
- Green, M. C., & Brock, T. C. (2000). The role of transportation in the persuasiveness of public narratives. *JPSP*, 79(5), 701-721.
- Kiritchenko, S., & Mohammad, S. M. (2017). Best-worst scaling more reliable than rating scales. *Proceedings of ACL 2017*.
- Krippendorff, K. (2018). *Content analysis: An introduction to its methodology* (4th ed.). SAGE.
- Mar, R. A., Li, J., Nguyen, A. T. P., & Ta, C. P. (2021). Memory and comprehension of narrative versus expository texts: A meta-analysis. *Psychonomic Bulletin & Review*, 28(3), 732-749.
- McCroskey, J. C., & Teven, J. J. (1999). Goodwill: A reexamination of the construct. *Communication Monographs*, 66(1), 90-103.
- Moshontz, H., et al. (2018). The Psychological Science Accelerator: Advancing psychology through a distributed collaborative network. *AMPPS*, 1(4), 501-515.
- Pew Research Center. (2019). *The digital pulpit: A nationwide analysis of online sermons*.
- Pieterse, H. J. C. (2020). A short history of empirical homiletics in South Africa. *Acta Theologica*, 40(2), 259-279.
- Pleizier, T. (2010). *Religious involvement in hearing sermons: A grounded theory study in empirical theology and homiletics*. Boekencentrum.
- Simonsohn, U., Simmons, J. P., & Nelson, L. D. (2020). Specification curve analysis. *Nature Human Behaviour*, 4, 1208-1214.

Additional references are included inline throughout the document and in the repository.

---

## License

This document and the accompanying repository materials are released under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**. Any person may adapt, extend, rename, or execute this research design in whole or in part. Attribution requested: *Schneider, B. (2026). Open Empirical Homiletics: An open invitation to build the first distributed research collaborative on sermon effectiveness. [DOI]*.

---

*Thank you for reading. If you are the person who can carry this forward, please be in touch.*
