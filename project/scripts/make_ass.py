#!/usr/bin/env python3
"""Build an ASS subtitle/graphics file from a cue list.

Usage: make_ass.py cues.json out.ass [--w 3840 --h 2160]

cues.json: list of {"start": s, "end": s, "text": "...", "style": "NARR|ORIG|ANNOT|TITLE|CHAPTER"}
Words wrapped in *asterisks* are rendered as highlighted key words.
Optional "words": [{"word","start","end"}] enables word-by-word reveal for
NARR/ORIG cues (each word fades in at its own time).
"""
import argparse
import json
import re

ACCENT = "&H00E8C65A&"      # warm gold (BGR order in ASS)
ACCENT_ORIG = "&H0088D8F5&"  # soft amber for original narrator highlights


def ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def esc(s: str) -> str:
    return s.replace("{", "(").replace("}", ")").replace("\n", "\\N")


def mark_highlights(text: str, colour: str) -> str:
    def rep(m):
        return "{\\b1\\c" + colour + "}" + m.group(1) + "{\\b0\\c&H00FFFFFF&}"
    return re.sub(r"\*([^*]+)\*", rep, text)


def header(w: int, h: int) -> str:
    fs = int(h * 0.040)   # ~86px at 2160
    fs_small = int(h * 0.030)
    fs_title = int(h * 0.085)
    fs_chap = int(h * 0.055)
    mv = int(h * 0.075)
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NARR,Inter,{fs},&H00FFFFFF,&H000000FF,&H00141414,&H96000000,0,0,0,0,100,100,0.5,0,1,{max(2,fs//22)},{max(2,fs//16)},2,{int(w*0.12)},{int(w*0.12)},{mv},1
Style: ORIG,Inter,{fs},&H00F2EBDD,&H000000FF,&H00141414,&H96000000,0,0,0,0,100,100,0.5,0,1,{max(2,fs//22)},{max(2,fs//16)},2,{int(w*0.12)},{int(w*0.12)},{mv},1
Style: ANNOT,Inter,{fs_small},&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,1,0,3,{max(2,fs_small//10)},0,7,{int(w*0.05)},{int(w*0.05)},{int(h*0.07)},1
Style: TITLE,Inter,{fs_title},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,5,{int(w*0.08)},{int(w*0.08)},0,1
Style: SUBTITLE,Inter,{fs_small},&H00E8C65A,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,{int(w*0.08)},{int(w*0.08)},0,1
Style: CHAPTER,Inter,{fs_chap},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,3,0,1,{max(2,fs_chap//18)},{max(2,fs_chap//14)},7,{int(w*0.05)},{int(w*0.05)},{int(h*0.07)},1
Style: CREDIT,Inter,{fs_small},&H00DDDDDD,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0.5,0,1,0,0,5,{int(w*0.1)},{int(w*0.1)},0,1
Style: LABEL,Inter,{int(h*0.026)},&H00FFFFFF,&H000000FF,&H00000000,&H90000000,1,0,0,0,100,100,3,0,3,{max(2,fs_small//10)},0,9,{int(w*0.03)},{int(w*0.03)},{int(h*0.04)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cues")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=3840)
    ap.add_argument("--h", type=int, default=2160)
    a = ap.parse_args()
    cues = json.load(open(a.cues))
    lines = [header(a.w, a.h)]
    for c in cues:
        style = c.get("style", "NARR")
        colour = ACCENT_ORIG if style == "ORIG" else ACCENT
        text = mark_highlights(esc(c["text"]), colour)
        fx = ""
        if style in ("NARR", "ORIG"):
            fx = "{\\fad(120,120)}"
        elif style == "ANNOT":
            fx = "{\\fad(250,250)}"
        elif style in ("TITLE", "SUBTITLE", "CHAPTER", "CREDIT"):
            fx = "{\\fad(600,600)}"
        elif style == "LABEL":
            fx = "{\\fad(200,200)}"
        layer = 1 if style in ("ANNOT", "LABEL") else 0
        lines.append(f"Dialogue: {layer},{ts(c['start'])},{ts(c['end'])},{style},,0,0,0,,{fx}{text}")
    open(a.out, "w").write("\n".join(lines) + "\n")
    print(f"wrote {a.out}: {len(cues)} cues")


if __name__ == "__main__":
    main()
