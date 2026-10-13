#!/usr/bin/env bash
# Job 2 (rev 3): synthesise the documentary narration from project/edit/narration.json
# with Kokoro-82M (Apache-2.0, runs on CPU) and align every clip with Whisper to get
# word timestamps for subtitles. Piper is kept as a fallback engine.
# Microsoft's edge-tts endpoint rejects GitHub runner IPs (HTTP 403), so it is not used.
set -euo pipefail
mkdir -p out/narration
sudo apt-get install -y -qq espeak-ng > /dev/null
python -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install --quiet kokoro soundfile piper-tts
VOICE="${VOICE:-af_heart}"
python3 - <<'PY'
import json, os, subprocess, numpy as np, soundfile as sf
items = json.load(open('project/edit/narration.json'))
voice = os.environ.get('VOICE', 'af_heart')
from kokoro import KPipeline
pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
def synth(text, v, speed, path):
    chunks = []
    for r in pipe(text, voice=v, speed=speed, split_pattern=r'\n+'):
        chunks.append(np.asarray(r.audio))
        chunks.append(np.zeros(int(24000 * 0.25), dtype=np.float32))  # breath between sentences/chunks
    audio = np.concatenate(chunks)
    sf.write(path, audio, 24000)
    return len(audio) / 24000
for it in items:
    d = synth(it['text'], voice, 0.96, f"out/narration/{it['id']}.wav")
    print(it['id'], f"{d:.2f}s", flush=True)
# alternates of the first paragraph for voice review
for v in ['am_michael', 'bm_george', 'af_bella']:
    synth(items[0]['text'], v, 0.96, f"out/narration/sample_{v}.wav")
PY
echo "== Word alignment with Whisper"
python3 - <<'PY'
import json, glob, re
from faster_whisper import WhisperModel
model = WhisperModel('medium.en', device='cpu', compute_type='int8')
def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"
for wav in sorted(glob.glob('out/narration/n0*.wav')):
    segs, info = model.transcribe(wav, beam_size=5, word_timestamps=True, vad_filter=False)
    words = [w for s in segs for w in (s.words or [])]
    base = wav[:-4]
    with open(base + '.vtt', 'w') as f:
        f.write('WEBVTT\n\n')
        for w in words:
            f.write(f"{fmt(w.start)} --> {fmt(w.end)}\n{w.word.strip()}\n\n")
    json.dump([{'word': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)} for w in words], open(base + '.words.json', 'w'))
    print(base, len(words), 'words', 'last end', words[-1].end if words else None)
PY
for f in out/narration/*.wav; do ffmpeg -v error -y -i "$f" -ar 48000 -ac 1 -c:a pcm_s16le "${f%.wav}.48k.wav"; done
ls -la out/narration
