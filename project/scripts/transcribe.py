#!/usr/bin/env python3
"""Transcribe an audio file with faster-whisper, emitting word-level timestamps.

Usage: transcribe.py <audio.wav> <output_prefix> [model]

Writes <prefix>.json (segments + words), <prefix>.srt and <prefix>.txt.
"""
import json
import sys


def fmt_ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    audio, prefix = sys.argv[1], sys.argv[2]
    model_name = sys.argv[3] if len(sys.argv) > 3 else "medium.en"
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
    )
    out = {"model": model_name, "language": info.language, "duration": info.duration, "segments": []}
    srt_lines, txt_lines = [], []
    for i, seg in enumerate(segments, 1):
        words = [
            {"word": w.word, "start": round(w.start, 3), "end": round(w.end, 3), "prob": round(w.probability, 3)}
            for w in (seg.words or [])
        ]
        out["segments"].append(
            {"id": i, "start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip(), "words": words}
        )
        srt_lines += [str(i), f"{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}", seg.text.strip(), ""]
        txt_lines.append(f"[{seg.start:7.2f} - {seg.end:7.2f}] {seg.text.strip()}")
        print(txt_lines[-1], flush=True)
    json.dump(out, open(prefix + ".json", "w"), indent=1)
    open(prefix + ".srt", "w").write("\n".join(srt_lines))
    open(prefix + ".txt", "w").write("\n".join(txt_lines) + "\n")


if __name__ == "__main__":
    main()
