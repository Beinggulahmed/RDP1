#!/usr/bin/env bash
# Job 1: transcribe the original film audio with word timestamps, fetch
# commercially licensed background-music candidates with their license text,
# and fetch the exact Wikimedia Commons file page for the rights report.
set -euo pipefail
IA_ID=DatingDo1949
mkdir -p out src

echo "== Download original from Internet Archive"
curl -sSL --retry 5 "https://archive.org/metadata/$IA_ID" -o src/ia_metadata.json
ORIG=$(python3 - <<'PY'
import json
d = json.load(open('src/ia_metadata.json'))
cands = [f for f in d['files'] if f.get('source') == 'original' and f['name'].lower().endswith(('.mpeg', '.mpg', '.mp4', '.mov', '.avi'))]
cands.sort(key=lambda f: -int(f.get('size', 0)))
print(cands[0]['name'] if cands else '')
PY
)
if [ -z "$ORIG" ]; then ORIG="${IA_ID}_512kb.mp4"; fi
echo "Original file: $ORIG"
curl -sSL --retry 8 --retry-all-errors "https://archive.org/download/$IA_ID/$ORIG" -o "src/$ORIG"
ls -la src

echo "== Extract audio and transcribe"
ffmpeg -v error -y -i "src/$ORIG" -vn -ac 1 -ar 16000 out/original_audio_16k.wav
ffmpeg -v error -y -i "src/$ORIG" -vn -ac 1 -ar 48000 -c:a pcm_s16le out/original_audio_48k.wav
python3 project/scripts/transcribe.py out/original_audio_16k.wav out/transcript_medium medium.en

echo "== Music candidates (Kevin MacLeod, incompetech.com, CC BY 4.0 / 3.0)"
mkdir -p out/music
for T in "Wholesome" "Sincerely" "Gymnopedie No 1" "Carefree" "Brittle Rille" "Fretless" "Lobby Time" "Dreamer" "Acoustic Meditation 2" "Porch Swing Days - slower"; do
  enc=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$T")
  f="out/music/$(echo "$T" | tr ' ' '_').mp3"
  if curl -sSL -f --retry 3 -A "Mozilla/5.0" "https://incompetech.com/music/royalty-free/mp3-royaltyfree/${enc}.mp3" -o "$f"; then
    echo "ok   $T ($(stat -c %s "$f") bytes)"
  else
    echo "fail $T"; rm -f "$f"
  fi
done
curl -sSL -A "Mozilla/5.0" "https://incompetech.com/music/royalty-free/licenses/" -o out/music/incompetech_license_page.html || true
curl -sSL -A "Mozilla/5.0" "https://incompetech.com/music/royalty-free/faq.html" -o out/music/incompetech_faq.html || true
curl -sSL "https://creativecommons.org/licenses/by/4.0/legalcode.txt" -o out/music/CC-BY-4.0.txt || true

echo "== Wikimedia Commons exact file page"
curl -sSL -G --retry 5 -A "archival-doc-pipeline/1.0 (rights research)" "https://commons.wikimedia.org/w/api.php" \
  --data-urlencode "action=query" --data-urlencode "prop=revisions|imageinfo" --data-urlencode "rvprop=content" \
  --data-urlencode "rvslots=main" --data-urlencode "iiprop=url|size|mime|extmetadata" \
  --data-urlencode "titles=File:Dating Dos and Donts (1949).webm" --data-urlencode "format=json" \
  -o out/commons_file_page.json
python3 -c "import json;d=json.load(open('out/commons_file_page.json'));print(json.dumps(d,indent=1)[:4000])"

echo "== History.com and Open Culture text (research citations)"
curl -sSL -A "Mozilla/5.0" "https://www.history.com/articles/1949-dating-etiquette-school-health-film" -o out/history_com.html || true
python3 - <<'PY'
import re, html
s = open('out/history_com.html', errors='ignore').read()
s = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
t = html.unescape(re.sub(r'<[^>]+>', '\n', s))
t = re.sub(r'\n\s*\n+', '\n', t)
open('out/history_com.txt', 'w').write(t)
print(t[:3000])
PY
ls -la out out/music
