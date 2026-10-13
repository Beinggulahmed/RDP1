# DELIVERABLES.md

Large media files are published as GitHub release assets (the repository itself
only holds scripts, documents, subtitles and the small narration stems). Download
them into `project/deliverables/` with
`bash scripts/fetch_release.sh job-current-38417011364 deliverables`.

## Final video (rendered by `project/jobs/job_render.sh` on GitHub Actions, run 38417011364)

Release: https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38417011364

| Asset | Description | SHA-256 |
|---|---|---|
| `FINAL_DOCUMENTARY_4K.mp4` (1,344,967,328 bytes) | 3840×2160, 29.97 fps, H.264 High (crf 16, 36.5 Mb/s), AAC 256 kb/s stereo, 4:54.97 | `5a97828e23522d88005320992a387d75aad27a319a8db63be10b6f46c8159ad1` |
| `PREVIEW_1080P.mp4` (204,123,062 bytes) | 1920×1080, same cut, crf 20 (5.5 Mb/s), AAC 192 kb/s stereo | `5b1bfbdffe32813e6f541585511dbb5a6bffa79c490f89b2e1de37aa398adb26` |
| `QC_REPORT.txt` | output of `scripts/qc.sh` for both files | |
| `contact_sheet_preview.jpg`, `frame4k_*s.jpg` | one frame every 10 s, plus nine full-resolution 4K frames | |
| `stems.zip` | `track_original_narrator.flac`, `track_new_narration.flac`, `track_music_ducked.flac`, `mix.flac` (48 kHz stereo, full-length, aligned to the timeline) | |
| `documentary.ass`, `SUBTITLES.srt`, `edl.json`, `timeline.txt` | subtitles/graphics and the edit decision list used for this render | |
| `job_log.txt` | full render log (every FFmpeg command) | |

### QC summary of the published files (from `QC_REPORT.txt`)

| Check | 4K master | 1080p preview |
|---|---|---|
| Resolution / frame rate | 3840×2160 @ 30000/1001, yuv420p, BT.709 | 1920×1080 @ 30000/1001 |
| Duration video / audio | 294.961 s / 294.970 s (9 ms) | 294.961 s / 294.976 s (15 ms) |
| Audio | AAC 48 kHz stereo | AAC 48 kHz stereo |
| Integrated loudness / LRA | −13.8 LUFS / 8.5 LU | −13.8 LUFS / 8.5 LU |
| Black frames | only the designed fade-out at 293.7–294.9 s | only the fade-out |
| Decode errors | none | none |

## Source material

Release: https://github.com/Beinggulahmed/RDP1/releases/tag/source-DatingDo1949-38399070255

- `DatingDo1949.mpeg` — original MPEG-2 upload from the Internet Archive (344,235,562 bytes)
- `DatingDo1949_512kb.mp4`, `DatingDo1949.avi`, `DatingDo1949_edit.mp4` — derivatives (not used)
- `ia_metadata.json`, `rights_evidence.zip` — metadata, ffprobe reports, head/tail frames, rights pages, Catalog of Copyright Entries search results (copies in `source/evidence/`)

## Transcription, music candidates and narration

- https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38400020459 — Whisper medium.en transcript (JSON/SRT/TXT with word timestamps), 48 kHz original soundtrack, nine Kevin MacLeod CC BY tracks with licence text, Wikimedia Commons file page
- https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38401472887 — Kokoro narration clips (`n01`–`n05`), Whisper word alignments, alternative voice samples (also committed under `audio/narration/`)

## Superseded runs

- `job-current-38404439119` — first 4K render; identical video but the job wrote its
  results outside the workflow's output folder, so only the log was published. Its
  audio was also mono. Superseded by run 38417011364 (stereo, published).
