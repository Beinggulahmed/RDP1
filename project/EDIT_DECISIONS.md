# EDIT_DECISIONS.md — "The Strange Dating Rules American Schools Taught in 1949"

Pilot of the automated archival-documentary pipeline. Everything below was
produced by the scripts in `scripts/` and `jobs/`; this file records *why* each
choice was made so the next film can reuse or override them.

## 1. Source and inspection

| | |
|---|---|
| Item | Internet Archive `DatingDo1949` (Prelinger Archives) |
| File used | `DatingDo1949.mpeg` — the item's original upload, 344 MB |
| Container / codec | MPEG-PS, MPEG-2 video (Main), MP2 audio |
| Resolution | 368 × 480, SAR 40:23 → DAR 4:3 (anamorphic half-D1 scan) |
| Frame rate | 29.97 fps, **interlaced TFF** (telecined Kodachrome 16 mm print) |
| Bitrate | 3,694 kb/s total (video 3,500 kb/s) |
| Audio | mono, 44.1 kHz, 112 kb/s MP2 (optical track; band-limited ≈ 70 Hz–7 kHz) |
| Duration | 12:25.41 |
| Condition | dense, slightly cyan-shifted Kodachrome; mild flicker; gate weave; MPEG noise; head titles missing on this print |

Other files on the item (`_512kb.mp4`, `.avi`, `_edit.mp4`, RealMedia) are 320×240
derivatives or worse and were not used. Inverse telecine (`fieldmatch+decimate`
to 23.976p) was tested and rejected: the cadence is irregular and a 60 s test
drifted +0.5 s against the audio. Field-matched deinterlacing at the native 29.97
fps keeps audio sync exact.

## 2. Selection of original excerpts (why these)

| Film TC | Used as | Reason |
|---|---|---|
| 0:50–1:09 | cold open, original audio | The narrator's "One couple. That means a date… Only what girl? Who?" states the film's premise in 19 s and is the hook. |
| 1:11–1:22, 2:00–2:16 | Ch. I | The film's explicit criterion for choosing a girl (looks → "rate" → make the fellow relax / feel appreciated) is the clearest "strange rule". |
| 5:20–5:37 | Ch. II | The *approved* phone call: concrete plan, time, parental approval ("my folks"). The two rejected calls were cut for length; their lesson is summarised in narration. |
| 3:26–3:34, 6:52–7:09, 8:30–8:34 | Ch. III | Three adults/peers stating rules: weekends only; "leave your boyfriend enough money so he'll ask you again"; "ready on time". Shows the gendered economics and parental authority. |
| 10:47–11:01, 11:38–12:02 | Ch. IV | The famous good-night alternatives: the attempted kiss ending at "1 a.m." and the approved "sandwich next time" ending. The abrupt "Well, so long" variant was cut to keep the film under five minutes. |
| 0:12–0:26, 1:43–2:00, 2:18–2:30, 9:26–9:56, 7:17–7:32, 8:35–8:50, 10:03–10:26, 12:02–12:25 | muted B-roll | Carry the narration without two speakers overlapping; the carnival and the walk home are the film's most visual passages. |

Clip boundaries were set from the Whisper word timestamps (`source/transcript_medium.json`,
`source/transcript.json`) so cuts fall in pauses.

## 3. Structure and running time

```
0:00  cold open (orig)           19.2 s
0:19  title card + narration n01   6.0 + 14.4 s
0:40  Ch. I  (orig)              26.4 s
1:06  narration n02 over B-roll  28.9 s
1:35  Ch. II (orig)              17.0 s
1:52  narration n03 over B-roll  29.8 s
2:22  Ch. III (orig)             29.8 s
2:51  narration n04 over B-roll  29.9 s
3:21  Ch. IV (orig)              38.6 s
4:00  narration n05 over B-roll  45.0 s
4:45  credits card               10.0 s
total 4:54.97
```
Original audio on screen: ≈ 2 min 11 s. New narration: 2 min 27 s. Music only / cards: ≈ 16 s.

## 4. Restoration settings (FFmpeg 6.1, CPU)

Filter chain per clip (`scripts/build_documentary.py::render_clip`):

1. `fieldmatch=order=tff:combmatch=full,yadif=deint=interlaced` — recovers the
   original film frames where the telecine cadence allows and deinterlaces only
   combed frames; frame rate unchanged (29.97).
2. `deflicker=size=7:mode=am` — 7-frame arithmetic-mean luminance smoothing for
   lamp/print flicker.
3. `hqdn3d=1.2:1.0:5:5` — light spatial, stronger temporal denoise. Stronger
   spatial values (2.5) visibly softened faces at this resolution and were rejected.
4. `deshake=rx=16:ry=16:edge=mirror:blocksize=8` — stabilises gate weave; the
   `vidstab` two-pass filter is not compiled into this FFmpeg.
5. `eq=contrast=1.02:saturation=1.06:gamma=1.12` and
   `curves=master='0/0 0.08/0.11 0.5/0.54 0.92/0.95 1/1'` — lifts the dense
   Kodachrome shadows, keeps highlights, +6 % saturation. The original colour
   balance is preserved; **no AI colourisation** (the film is colour).
6. `scale=2880:2160:flags=lanczos` — 4:3 picture upscaled to full UHD height.
7. `zoompan` — 3–8 % slow push-in / pull-out per clip for documentary motion.
8. `unsharp=5:5:0.5:3:3:0` — gentle luma sharpening after the upscale.
9. `pad=3840:2160` on a near-black warm grey (#0d0b09) — pillarbox; nothing is
   cropped from the 4:3 frame.
10. Fades of 0.3–1.0 s between scenes; title/credit cards use a blurred, darkened
    still from the film.

**Honest limit on "4K":** the source carries about 368×480 of real detail. The
UHD master is a clean, stabilised, de-noised Lanczos upscale with gentle
sharpening — it has no more fine detail than a good 480p transfer. GPU
super-resolution models (Real-ESRGAN, etc.) were not run: the production
container has no GPU and cannot reach model hosts, and CPU inference on ~9,000
frames was infeasible in the time budget. The pipeline is structured so an
AI upscaler can be dropped in at step 6 on the user's Mac.

## 5. Audio

Three stems are rendered separately (`work/build/audio/`):

- `track_original_narrator.wav` — excerpts of the 1949 soundtrack:
  `highpass=70`, `lowpass=7500`, `afftdn` (−28 dB noise floor, 12 dB reduction)
  for optical-track hiss, 0.15/0.25 s fades at cut points.
- `track_new_narration.wav` — Kokoro-82M voice `af_heart` (speed 0.96), each
  clip `loudnorm` to −16 LUFS. Alternative voice samples (`am_michael`,
  `bm_george`, `af_bella`) are in `audio/narration/` for review. Microsoft
  edge-tts and the vidIQ/Higgsfield voice tools were unavailable (403 from
  GitHub runners; zero credits respectively), so no paid service was used.
- `track_music_ducked.wav` — Kevin MacLeod, *Sincerely* (CC BY 4.0), −18 LUFS
  then −16 dB, side-chain compressed under all speech (threshold 0.015, ratio
  10:1, 40 ms attack, 900 ms release), 3 s fade in, 8 s fade out.

The two narrators never overlap: original audio only plays on "orig" clips,
narration only over muted B-roll or cards. Final mix `loudnorm` to −14 LUFS /
−1.5 dBTP (streaming standard). AAC 256 kb/s stereo 48 kHz in the deliverables.

## 6. Subtitles and graphics (`subs/documentary.ass`, `SUBTITLES.srt`)

- Original lines: timings from Whisper, text hand-corrected (e.g. "Hi-Teen
  Carnival"), italic cream style, highlighted key phrases in amber.
- Our narration: script text aligned word-by-word to the synthesised audio with
  Whisper, white style, key words in gold.
- Lower-third fact cards (source, collaborator, census figures, copyright record),
  chapter titles, an "ORIGINAL AUDIO · 1949" badge on archival-audio passages,
  title and credits cards. Typeface Inter (OFL).

## 7. Deliverables and QC

See `QC_REPORT.txt` (output of `scripts/qc.sh`) and `DELIVERABLES.md` for the
release links of `FINAL_DOCUMENTARY_4K.mp4` and `PREVIEW_1080P.mp4`.
