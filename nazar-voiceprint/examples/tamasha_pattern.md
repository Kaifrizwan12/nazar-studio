# Worked example: the monologue pattern
**Source:** the central monologue of *Tamasha* (2015, written and directed by Imtiaz Ali), about 415 words of Romanised Hindi-Urdu with English code-switching. The text isn't redistributed here; only short quoted fragments appear, for analysis. Numbers: `tamasha_analysis.json`.

> This is a teaching example of *reading* a pattern from a famous piece. A real voiceprint job profiles **your own** archive, not someone else's.

## Measured (`engine/analyze.py --lang hi-romanized`)
| Feature | Value | Reading |
|---|---|---|
| Sentence length | mean 4.4 words, spread 3.7, max 18 | clipped bursts that break into short run-ons |
| Ellipses | 120 per 1,000 words | the breath *is* the punctuation: thoughts trail off and restart |
| Questions | 48 per 1,000 words | the monologue argues with itself |
| Exclamations / semicolons | 0 / 0 | never shouts, never subordinates |
| Slash breaks | 31 per 1,000 words | a list rhythm used as a mechanical chant |
| Refrains | "walk stop smile please" ×3; "race mein" ×5 | a fixed phrase marks each return to the routine |
| Function-word layer | skipped | no Hindi-Urdu baseline ships yet, so it isn't faked |

## Read (qualitative layer)
1. **Two voices, one mouth.** Quick question-and-answer ping-pong, so the speaker interrogates himself.
2. **A mechanical refrain** (four commands, slash-separated) stands for the conformist routine and lands at every turning point.
3. **English as the system's voice.** Rote phrases like "Fine thank you how are you" and labels like *mediocre / regular / ordinary* arrive in English. Feeling stays in Hindi.
4. **Escalating count.** A list keeps going past where it should stop, until it becomes the point.
5. **A buried fable.** A violent childhood story stands in for killing his own sense of being special.
6. **Frame break at the end.** The narrator turns to the audience, judges the story's ending, and offers to rewrite it.

## The test: write something new in this pattern, then check it
A new, original monologue for a different person: a software-engineering student who secretly loves design, marketing and illustration. Same devices, new everything else: own arc, own images, own refrain ("Compile / Run / Submit"), and the frame break moved mid-scene. File: `3am_scene.txt`.

| | Mean words | Spread | Longest | Rhythm label | Ellipses /1k | Questions /1k |
|---|---|---|---|---|---|---|
| **Pattern** | 4.41 | 3.67 | 18 | mixed bursts | 120 | 48 |
| Pass 1 (draft) | 3.36 | 2.89 | 13 | **short, flat, even** ✗ | 79 | 19 ✗ |
| Pass 2 | 4.09 | 7.01 ✗ | 50 ✗ | mixed bursts | 68 ✗ | 50 |
| **Pass 3** | 3.83 | **3.94** | **21** | **mixed bursts** | 98 | **51** |

- **Pass 1** shows an AI's default pull toward an even cadence and too few questions. The check caught it.
- **Pass 2** overcorrected with one 50-word run-on.
- **Pass 3** converges. Ellipses are still a little low, which is honestly where a human editor takes over.
