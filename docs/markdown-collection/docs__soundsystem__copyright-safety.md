# Copyright Safety Layer

## Safety Philosophy

This layer is designed to prevent obvious misuse, preserve evidence, and force human decisions at the correct moments. It does not guarantee legal clearance.

## Preflight Gates

Reject or require manual override when:

- prompt names a protected artist, song, producer, vocalist, label, or commercial release as a target
- prompt requests voice cloning, impersonation, or "sounds exactly like"
- reference audio lacks rights basis
- adapter provenance is missing or contains unauthorized source material
- lyrics are copied from third-party works
- generation is marked release candidate before human review

## Training Dataset Rules

Allowed:

- owned SCHLUESSELKINDER recordings
- commissioned recordings with written AI training permission
- explicitly licensed datasets that allow the intended use
- public-domain or CC0 material after metadata verification

Blocked:

- commercial masters without permission
- artist discographies used for imitation
- downloaded platform audio
- unofficial scraping
- acapellas, stems, or leaks without rights documentation

## Post-Generation Analysis

Run four classes of checks:

1. Fingerprint: Chromaprint/fpcalc for exact or near-exact recording collisions.
2. Embedding: CLAP and MERT-style neighborhood similarity against internal reference corpus.
3. Melody: pitch contour/chroma/DTW comparison for hooks and vocal top-lines.
4. Metadata: prompt, lyrics, character, adapter, seed, engine, and rights-basis audit.

## Risk Levels

| Level | Meaning | Action |
| --- | --- | --- |
| `PASS` | No obvious risk | Export allowed as internal artifact |
| `REVIEW` | Similarity or provenance needs human review | Export allowed only with review tag |
| `BLOCK` | Clear policy or provenance failure | No Dropbox export, no release candidate |
| `LEGAL` | Unclear rights or high similarity to known work | Escalate before reuse |

## Required Evidence Per Output

- prompt JSON
- compiled prompt
- negative prompt
- engine and model version
- adapter version and dataset hash
- seed
- source/reference hashes
- safety report
- human review notes when applicable

## Release Boundary

The AI engine can produce internal artifacts. It cannot approve release.

Release requires a separate human decision that records:

- what human edited, arranged, selected, or rejected
- whether any source material was used
- whether all generated vocals/lyrics are original or cleared
- whether copyright and likeness risks have been reviewed
