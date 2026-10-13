# Archival documentary pipeline — pilot: *Dating: Do's and Don'ts* (1949)

This folder is the reusable automation for turning a public-domain archival film
into a short, restored, narrated documentary. The pilot output is
**"The Strange Dating Rules American Schools Taught in 1949"** (≈5 min, 4K).

## Deliverables

| File | What it is |
|---|---|
| `deliverables/FINAL_DOCUMENTARY_4K.mp4` | 3840×2160, H.264, AAC — published as a GitHub release asset (see DELIVERABLES.md) |
| `deliverables/PREVIEW_1080P.mp4` | 1920×1080 review copy |
| `COPYRIGHT_REPORT.md` | rights verification with evidence |
| `SCRIPT.md` | full script: original excerpts + new commentary with source tags |
| `SOURCES.md` | numbered research and rights sources |
| `SUBTITLES.srt` | speech subtitles (original film lines tagged `[1949 film]`) |
| `EDIT_DECISIONS.md` | the edit, restoration settings, audio mix and QC results |
| `source/` | original Internet Archive files, metadata and rights evidence |
| `audio/`, `music/`, `subs/`, `edit/` | production assets (stems, narration, music, ASS graphics, EDL) |

Large media (source film, stems, renders) is **not committed** to git; it is published
as release assets by the workflows and listed in `DELIVERABLES.md`.

## Pipeline (all automated)

```
.github/workflows/fetch-archival-source.yml   # 1. download film + rights evidence on a runner with open internet
project/jobs/job_transcribe.sh  (remote-job)  # 2. Whisper medium.en transcript w/ word timestamps, music, Commons page
project/edit/narration.json                   # 3. new commentary (written + fact-checked, see SCRIPT.md)
project/jobs/job_tts.sh         (remote-job)  # 4. Kokoro TTS narration + Whisper word alignment
project/scripts/make_edl.py                   # 5. segment plan -> edl.json, cues.json, SUBTITLES.srt, timeline
project/scripts/make_ass.py                   # 6. cues -> ASS subtitles/graphics with key-word highlights
project/scripts/build_documentary.py          # 7. restore/upscale segments, mix audio stems, render 4K + 1080p
project/scripts/qc.sh                         # 8. validation (resolution, sync, black frames, loudness)
```

`scripts/fetch_release.sh <tag> <dir>` pulls a workflow's release assets into the
production environment; `scripts/restore_clip.sh` is the stand-alone restoration
filter chain for one clip.

### Restoration chain (FFmpeg, CPU)

`fieldmatch+yadif` (field-matched deinterlace of the telecined MPEG-2 scan, frame
rate preserved for exact A/V sync) → `deflicker` (7-frame luminance smoothing) →
`hqdn3d` (light spatial / stronger temporal denoise for grain, dust and MPEG
noise) → `deshake` (gate-weave stabilisation) → `eq` + `curves` (lift the dense
Kodachrome shadows, +6 % saturation, gentle S-curve) → Lanczos upscale of the 4:3
picture to 2880×2160 → slow `zoompan` push-in → `unsharp` (luma only) → pillarbox
to 3840×2160. No AI colourisation is applied: the print is already colour.

### Why GitHub Actions is in the loop

The production container's network policy blocks archive.org, Wikimedia, Hugging
Face and the Microsoft TTS endpoint. GitHub-hosted runners have open internet, so
downloads, transcription and narration synthesis run there and come back as
release assets. On a Mac with normal internet access the same scripts run locally
(`bash project/jobs/job_transcribe.sh`, `bash project/jobs/job_tts.sh`).

## Re-running for a different film

1. Change the identifier in `fetch-archival-source.yml` (or dispatch it with an input).
2. Update `IA_ID` in `jobs/job_transcribe.sh`.
3. Write the segment `PLAN` and `CORRECTIONS` in `scripts/make_edl.py` and the
   narration in `edit/narration.json`.
4. Run `make_edl.py`, `make_ass.py`, `build_documentary.py`, `qc.sh`.
