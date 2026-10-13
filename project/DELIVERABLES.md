# DELIVERABLES.md

Large media files are published as GitHub release assets (the repository itself
only holds scripts, documents, subtitles and the small narration stems).

## Final video (rendered by `project/jobs/job_render.sh` on GitHub Actions)

Release: https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38404439119

| Asset | Description |
|---|---|
| `FINAL_DOCUMENTARY_4K.mp4` | 3840×2160, 29.97 fps, H.264 (crf 16), AAC 256 kb/s, ≈ 4:55 |
| `PREVIEW_1080P.mp4` | 1920×1080 review copy (crf 20), AAC 192 kb/s |
| `QC_REPORT.txt` | output of `scripts/qc.sh` for both files |
| `contact_sheet_preview.jpg`, `frame4k_*s.jpg` | visual QC frames |
| `stems.zip` | `track_original_narrator.flac`, `track_new_narration.flac`, `track_music_ducked.flac`, `mix.flac` |
| `documentary.ass`, `SUBTITLES.srt`, `edl.json`, `timeline.txt` | subtitles/graphics and the edit decision list used for the render |
| `job_log.txt` | full render log |

Checksums and the QC summary are appended below once the render completes.

## Source material

Release: https://github.com/Beinggulahmed/RDP1/releases/tag/source-DatingDo1949-38399070255

- `DatingDo1949.mpeg` — original MPEG-2 upload from the Internet Archive (344 MB)
- `DatingDo1949_512kb.mp4`, `DatingDo1949.avi`, `DatingDo1949_edit.mp4` — derivatives (not used)
- `ia_metadata.json`, `rights_evidence.zip` — metadata, ffprobe reports, head/tail frames, rights pages, Catalog of Copyright Entries search results

## Transcription, music candidates and narration

- https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38400020459 — Whisper medium.en transcript (JSON/SRT/TXT with word timestamps), 48 kHz original soundtrack, nine Kevin MacLeod CC BY tracks with licence text, Wikimedia Commons file page
- https://github.com/Beinggulahmed/RDP1/releases/tag/job-current-38401472887 — Kokoro narration clips (`n01`–`n05`), Whisper word alignments, alternative voice samples
