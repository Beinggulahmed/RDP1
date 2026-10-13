#!/usr/bin/env bash
# Job 4: re-mix the audio (stereo fix) and re-mux it into the already rendered
# 4K master and 1080p preview from a previous render release, without
# re-encoding video. Set RENDER_TAG to the release that holds the renders.
set -euo pipefail
RENDER_TAG="${RENDER_TAG:-job-current-38404439119}"
IA_ID=DatingDo1949
cd project
mkdir -p source audio music work out prev
echo "== Previous renders"
REPO="Beinggulahmed/RDP1" bash scripts/fetch_release.sh "$RENDER_TAG" prev
echo "== Source audio + music"
curl -sSL --retry 8 --retry-all-errors "https://archive.org/download/$IA_ID/$IA_ID.mpeg" -o "source/$IA_ID.mpeg"
ffmpeg -v error -y -i "source/$IA_ID.mpeg" -vn -ac 1 -ar 48000 -c:a pcm_s16le audio/original_audio_48k.wav
curl -sSL -f --retry 3 -A "Mozilla/5.0" "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sincerely.mp3" -o music/background.mp3
echo "== Re-mix (stereo)"
python3 scripts/build_documentary.py edit/edl.json --out-dir work/build --stage audio
ffprobe -v error -show_entries stream=channels,sample_rate -of csv=p=0 work/build/audio/mix.wav
echo "== Re-mux"
for f in FINAL_DOCUMENTARY_4K PREVIEW_1080P; do
  br=256k; [ "$f" = PREVIEW_1080P ] && br=192k
  ffmpeg -v error -y -i "prev/$f.mp4" -i work/build/audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a $br -ar 48000 -movflags +faststart -shortest "out/$f.mp4"
done
echo "== QC"
bash scripts/qc.sh out/FINAL_DOCUMENTARY_4K.mp4 3840 2160 > out/QC_REPORT.txt 2>&1 || true
echo "===== PREVIEW =====" >> out/QC_REPORT.txt
bash scripts/qc.sh out/PREVIEW_1080P.mp4 1920 1080 >> out/QC_REPORT.txt 2>&1 || true
grep -vE "^\+|frame=" out/QC_REPORT.txt
ffmpeg -v error -y -i out/PREVIEW_1080P.mp4 -vf "fps=1/10,scale=480:-1,tile=6x5" out/contact_sheet_preview.jpg
for t in 10 30 75 100 130 160 210 250 280; do ffmpeg -v error -y -ss $t -i out/FINAL_DOCUMENTARY_4K.mp4 -frames:v 1 -q:v 3 out/frame4k_${t}s.jpg; done
mkdir -p out/stems
for f in work/build/audio/*.wav; do ffmpeg -v error -y -i "$f" -c:a flac "out/stems/$(basename "${f%.wav}").flac"; done
cp subs/documentary.ass SUBTITLES.srt edit/edl.json edit/timeline.txt out/
(cd out && sha256sum *.mp4 > SHA256SUMS.txt && cat SHA256SUMS.txt)
ls -la out out/stems
