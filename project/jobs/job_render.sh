#!/usr/bin/env bash
# Job 3: render the deliverables on a GitHub-hosted runner (the production
# container cannot upload large files anywhere reachable). Uses the committed
# EDL, cues/ASS, narration stems; re-downloads the source film and the music
# bed; renders the 4K master and the 1080p preview; runs QC; publishes all.
set -euo pipefail
IA_ID=DatingDo1949
OUT_ROOT="${GITHUB_WORKSPACE:-$(pwd)}/out"; mkdir -p "$OUT_ROOT"
cd project
mkdir -p source audio music work out
echo "== Fonts"
(sudo apt-get install -y -qq fonts-inter > /dev/null && echo "fonts-inter installed") || true
if ! fc-list | grep -qi "Inter"; then
  mkdir -p ~/.fonts && curl -sSL -o /tmp/inter.zip "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip" \
    && unzip -qo /tmp/inter.zip -d /tmp/inter && find /tmp/inter -name "*.ttf" -path "*extras*" -prune -o -name "Inter*.ttf" -print | head -50 | xargs -I{} cp {} ~/.fonts/ && fc-cache -f
fi
fc-list | grep -i "Inter" | head -3
echo "== Source"
curl -sSL --retry 8 --retry-all-errors "https://archive.org/download/$IA_ID/$IA_ID.mpeg" -o "source/$IA_ID.mpeg"
ffmpeg -v error -y -i "source/$IA_ID.mpeg" -vn -ac 1 -ar 48000 -c:a pcm_s16le audio/original_audio_48k.wav
echo "== Music (Kevin MacLeod, CC BY 4.0)"
curl -sSL -f --retry 3 -A "Mozilla/5.0" "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sincerely.mp3" -o music/background.mp3
ls -la source audio music
echo "== Render 4K master + 1080p preview"
python3 scripts/build_documentary.py edit/edl.json --out-dir work/build --w 3840 --h 2160 --stage all \
  --final out/FINAL_DOCUMENTARY_4K.mp4 --preview out/PREVIEW_1080P.mp4
echo "== QC"
bash scripts/qc.sh out/FINAL_DOCUMENTARY_4K.mp4 3840 2160 > out/QC_REPORT.txt 2>&1 || true
echo "===== PREVIEW =====" >> out/QC_REPORT.txt
bash scripts/qc.sh out/PREVIEW_1080P.mp4 1920 1080 >> out/QC_REPORT.txt 2>&1 || true
cat out/QC_REPORT.txt
echo "== Contact sheets (one frame every 10 s) and sample 4K frames"
ffmpeg -v error -y -i out/PREVIEW_1080P.mp4 -vf "fps=1/10,scale=480:-1,tile=6x5" out/contact_sheet_preview.jpg
for t in 10 30 75 100 130 160 210 250 280; do ffmpeg -v error -y -ss $t -i out/FINAL_DOCUMENTARY_4K.mp4 -frames:v 1 -q:v 3 out/frame4k_${t}s.jpg; done
echo "== Stems (FLAC)"
mkdir -p out/stems
for f in work/build/audio/*.wav; do ffmpeg -v error -y -i "$f" -c:a flac "out/stems/$(basename "${f%.wav}").flac"; done
cp subs/documentary.ass SUBTITLES.srt edit/edl.json edit/timeline.txt out/
ls -la out out/stems
(cd out && sha256sum *.mp4 > SHA256SUMS.txt && cat SHA256SUMS.txt)
echo "== Copy results to $OUT_ROOT"
cp -a out/. "$OUT_ROOT/"
ls -la "$OUT_ROOT"
