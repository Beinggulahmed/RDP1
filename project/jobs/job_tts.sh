#!/usr/bin/env bash
# Job 2: synthesise the new documentary narration with edge-tts (Microsoft
# neural voices, free, no account) from project/edit/narration.json, one MP3
# per paragraph plus word-boundary VTT files used for subtitle timing.
set -euo pipefail
mkdir -p out/narration
VOICE="${VOICE:-en-US-ChristopherNeural}"
RATE="${RATE:--4%}"
PITCH="${PITCH:-+0Hz}"
python3 - <<'PY'
import json, subprocess, os
items = json.load(open('project/edit/narration.json'))
voice = os.environ.get('VOICE', 'en-US-ChristopherNeural')
rate = os.environ.get('RATE', '-4%'); pitch = os.environ.get('PITCH', '+0Hz')
for it in items:
    base = f"out/narration/{it['id']}"
    subprocess.run(['edge-tts', '--voice', voice, '--rate', rate, '--pitch', pitch,
                    '--text', it['text'], '--write-media', base + '.mp3', '--write-subtitles', base + '.vtt'], check=True)
    d = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', base + '.mp3']).decode().strip()
    print(it['id'], d, 's')
# also a short sample of two alternative voices for review
for v in ['en-US-AndrewMultilingualNeural', 'en-US-GuyNeural']:
    subprocess.run(['edge-tts', '--voice', v, '--rate', rate, '--text', items[0]['text'], '--write-media', f'out/narration/sample_{v}.mp3'], check=True)
PY
edge-tts --list-voices | grep -E "en-US" > out/narration/voices_en_US.txt || true
cd out && zip -qr narration.zip narration && ls -la
