# Multimodal Sermon Presentation Analysis

**Date captured:** 2026-04-14
**Status:** Future idea — deferred from the sermon coach MVP
**Related:** `docs/superpowers/specs/2026-04-14-sermon-coach-design.md` (MVP spec — text-only analysis)

## The idea (Bryan's words, 2026-04-14)

> "Eventually I want to use some type of tool to not only review the text of the sermon but to have a way to see the time stamps for the transcript and the audio and be able to analyze the homiletical and rhetorical impact of the pitch, tone, cadence, hand movements, body posture, etc. of the sermon presentation for evaluation."

## Why this matters

The current sermon coach MVP analyzes the **text** of each sermon — burden clarity, movement, application specificity, ethos markers *inferred from transcript text*, concreteness, Christ thread, density. Text analysis covers a lot of what makes a sermon land, but it misses the **embodied delivery** layer that rhetoric and persuasion research identifies as a major impact predictor.

From the consultant's Tier 1 framing:

> "Delivery and nonverbal/vocal embodiment. Homileticians sometimes under-measure this because it feels less 'textual,' but persuasion research does not ignore it. Nonverbal behavior affects both credibility and persuasiveness, and vocal features influence how confidence and authority are perceived. In plain English: monotone, uncertainty in cadence, poor pacing, and weak embodied presence can blunt a good manuscript; steady confident delivery can strengthen one."

For Bryan specifically — a Reformed Presbyterian pastor whose known weak spots include length and density — the embodied dimension is exactly where feedback is hardest to self-assess. You can read your own manuscript critically. You cannot, in the pulpit, see your own body language or hear your own pitch contour as a hearer does.

## What's in the MVP

- Transcript text from SermonAudio AI transcription
- Inferred ethos markers from the text (direct 2nd-person address, personal confession, etc.)
- Duration, section timings, density hotspots from text + timestamps
- Coach reads the transcript and narrates

**Notably NOT in the MVP:**
- Synchronized timestamp playback (text ↔ audio position)
- Audio waveform analysis (pitch, volume, pace, pauses)
- Video analysis (posture, gesture, eye contact, facial expression)
- Cross-modal impact correlation (e.g., "your pitch flattened at 14:22 exactly when the application was supposed to land")

## The future vision

### 1. Timestamp-synchronized transcript + audio

**What Bryan sees:** The sermon review page adds an audio player at the top. Clicking any line of the transcript jumps the audio to that timestamp. Conversely, the audio's current position highlights the matching transcript line in real time. Coach flags become clickable "play this moment" triggers.

**What's needed:**
- SermonAudio API likely exposes transcript word-level or sentence-level timings alongside the raw text. Need to verify and pull them.
- A `sermon_transcript_segments` table keyed on `(sermon_id, start_ms, end_ms, text)` — fine-grained alignment between text and audio.
- Waveform UI component (peaks.js, wavesurfer.js, or similar).
- Extension to existing `sermon_flags` to reference precise millisecond timestamps.

### 2. Audio analysis — pitch, tone, cadence

**Metrics to extract:**
- **Pitch contour** per phrase — flat monotone vs dynamic range vs strained
- **Volume envelope** — whispered intimate moments vs full-voiced proclamation vs drop-outs
- **Pace (words per minute)** rolling average — where he slowed down for emphasis, where he rushed
- **Pause distribution** — dramatic pauses vs stumbling pauses vs dead air
- **Pitch stress patterns** — which words carried intonational weight
- **Cadence rhythm** — did he find oral rhythm (refrain, parallelism, acceleration toward climax) or plod?

**Technical approach:**
- Librosa (Python) for fundamental frequency estimation, onset detection, tempo tracking
- Whisper or similar for word-level alignment if SermonAudio doesn't expose it
- Optional: OpenSMILE for paralinguistic features (jitter, shimmer, voice quality)
- Run locally on the audio file; results feed into the analyzer pipeline as another deterministic stage

**Coach output becomes:**
- *"Your pitch went flat in §2 for 3 minutes — right as you were holding the Greek genitive. Listeners heard monotone and exegetical density at the same time."*
- *"You found cadence at 24:15 with the repeated 'no condemnation' — that's where your ethos rating locked in."*
- *"Application at 31:00 arrived with a quieter, more private tone. Contrast with §2's public declamation. Your body shifted modes — that's why it landed."*

### 3. Video analysis — body, gesture, eye contact

**Metrics to extract:**
- **Gesture frequency and breadth** — expansive gestures vs hands-glued-to-podium
- **Gesture alignment with text** — did the gesture reinforce the argument or was it decorative?
- **Body stance** — open vs closed, planted vs wandering, forward vs retreating
- **Eye contact distribution** — sweeping the room vs locked on notes vs avoiding congregation
- **Facial affect** — did the face match the burden? Joy where joy was called for? Gravity where gravity?
- **Posture over time** — energy curve across the sermon, fatigue markers

**Technical approach:**
- MediaPipe Holistic for pose + hand + face landmarks (runs in browser or Python)
- OpenPose / Movenet as alternatives
- Gaze tracking via face landmarks
- Temporal gesture classification (reaching, pointing, open palm, fist, clasped, etc.)
- Video source: SermonAudio may host video in addition to audio, OR Bryan films his own (phone on a tripod works for this purpose)

**Coach output becomes:**
- *"You found your feet at 12:00 — you'd been behind the podium, you stepped out and gestured directly at the congregation when you stated the FCF. That's when ethos spiked."*
- *"Hands stayed clasped through §2's exegetical block — the gesture stayed neutral while the words got technical. The congregation had no embodied handle to follow you."*
- *"You looked at your notes 70% of the time in the first 10 minutes, then 15% in the final 10 minutes. Your delivery opened up as the content moved from exegesis to application."*

### 4. Cross-modal impact correlation

The highest-value feature: **combine text, audio, and video into one synchronized analysis**.

- *"At 14:22, your text was landing the 'so what' (transcript shows clear application language). But your pitch dropped to monotone and your posture closed. The words tried to land; your body refused to carry them. That's why the application felt late even though it technically arrived on time."*
- *"Your best moment was 24:15: cadence + open gesture + eye contact + pitched declamation + personal confession all converged. The hearers heard a man seized. Protect that moment — it's why this sermon worked."*

This is the dimension where text-only analysis physically cannot reach. It's also what separates "analyzes sermons" from "coaches preachers."

## Integration with the MVP

**Most of the MVP carries over unchanged.** The five-layer architecture (Ingest → Match → Analyze → Coach → UI) still holds. Multimodal analysis adds:

- **New ingest fields** on `sermons`: `audio_local_path`, `video_local_path`, `transcript_word_timings` (JSON), `audio_features_path`, `video_features_path`
- **New analyzer stages** (parallel to existing stages 1-4): `analyze_audio_features`, `analyze_video_features`, `correlate_modalities`
- **Extended rubric** on `sermon_reviews`: pitch dynamics, cadence score, gesture breadth, eye contact distribution, cross-modal alignment
- **New coach tools**: `get_audio_moment(start_sec, end_sec)` returning pitch/volume/pace, `get_video_moment(start_sec, end_sec)` returning landmarks + gesture classification
- **UI upgrade**: the Review page gets an audio player with synced transcript highlighting, and a "moment" drawer showing pitch/volume/gesture snapshots when a flag is clicked

**What needs to happen first in the MVP** before this is even possible:
1. Reliable timestamp data in the transcript (MVP has duration but not word-level sync — need to check SermonAudio API)
2. Storage of the audio file locally (MVP streams from SermonAudio URL, doesn't download)
3. Optional video handling (MVP ignores video entirely)

## Research grounding

- **Pitch / tone impact**: Scherer, K. (2003) *Vocal communication of emotion.* Speech Communication, 40, 227-256. Shows vocal features reliably influence perceived credibility and emotional impact.
- **Gesture and persuasion**: Hostetter, A. (2011) *When do gestures communicate? A meta-analysis.* Psychological Bulletin, 137(2), 297-315. Beat gestures align with stressed speech and reinforce message.
- **Body posture and ethos**: Peters, E. & Hoetjes, M. (2017) *The effect of gesture on persuasion.* Metaphor and Symbol, 32, 243-256.
- **Preaching-specific**: Gaarden, M. (2016) *The preaching presence: The engaged preacher.* Homiletic, 41(2). Found that listeners perceive authenticity through embodied markers — not just words.
- **Cadence and memorability**: studies on repetition, parallelism, and rhythmic patterning in oratory (MLK, Spurgeon, Edwards all remembered as much for oral cadence as for content).

## Phased path from MVP to multimodal

**Phase 2 (post-MVP, next ~3 months):** Audio sync + basic pitch/pace analysis.
- Pull word-level timestamps from SermonAudio if available
- Add audio player to Review page with synced transcript highlighting
- Run librosa pitch + pace extraction in a new analyzer stage
- Surface 1-2 simple audio metrics (average pitch, pace variance, long pause count)

**Phase 3 (~6 months):** Full audio rubric.
- OpenSMILE paralinguistic features
- Cadence / rhythm pattern detection
- Pitch contour alignment with section structure
- New coach tools for audio moments

**Phase 4 (~12 months):** Video analysis.
- Require Bryan to add a phone-on-tripod or use SermonAudio video if available
- MediaPipe Holistic for pose + hand + face
- Gesture classification pipeline
- Eye contact distribution over time
- Cross-modal correlation

**Phase 5:** The unified multimodal coach.
- Coach's rubric expands to include embodied dimensions
- Review page UI shows synchronized text + audio + video + analysis overlays
- Longitudinal tracking of embodied metrics

## What to remember when picking this up

1. **The MVP's text-only Tier 1 impact metrics (burden, movement, application, ethos, concreteness) are NOT wrong or incomplete — they're the textual proxy for what audio+video will measure directly.** When multimodal lands, expect the scores to get sharper, not fundamentally different.

2. **The hardest engineering problem is not the ML — it's the synchronization.** Word-level timestamp alignment across transcript + audio + video is the plumbing that makes everything else possible.

3. **Don't let multimodal delay the core weekly loop.** The consultant's correction stands: ship the text-only weekly coaching report first, let Bryan use it, then add dimensions as they earn their place.

4. **The video pipeline is optional, not required.** Audio-only multimodal is already a huge upgrade over text-only. Video is the ceiling, not the floor.

5. **Cost scales differently.** Audio analysis is cheap (local ML, no LLM cost). Video analysis is moderate (local ML, heavier compute). Cross-modal LLM correlation calls get expensive if not scoped — they should read already-extracted features, not raw media.

## Pointer for future sessions

This file is intentionally kept at `docs/superpowers/ideas/` next to the specs and plans so that any future Claude session on this project will find it when listing the superpowers tree. When the MVP is running reliably and Bryan starts feeling the ceiling of text-only analysis, grab this file and start the Phase 2 design cycle.
