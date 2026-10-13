#!/usr/bin/env python3
"""Generate the edit decision list (edl.json), subtitle cues (cues.json) and a
plain SRT from the segment plan below plus measured narration durations.

Usage: make_edl.py [--narration-dir audio/narration] [--transcript source/transcript.json]
Outputs: edit/edl.json, edit/cues.json, edit/timeline.txt
"""
import argparse
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SOURCE = "source/DatingDo1949.mpeg"
SOURCE_AUDIO = "audio/original_audio_48k.wav"

# Hand-corrected text for original-narrator lines (keyed by whisper segment start, seconds).
# Words in *asterisks* are highlighted on screen.
CORRECTIONS = {
    50.68: "*One couple.*",
    53.00: "That means a *date*.",
    56.04: "Not like just going around with the crowd.",
    59.58: "Just me and the girl.",
    62.28: "Well, that's all right.",
    65.66: "Only... *what girl?*",
    68.76: "Who?",
    71.34: "*How do you choose a date?*",
    74.64: "Whose company would you enjoy?",
    77.36: "Well, one thing you can consider is *looks*.",
    82.18: "Woody thought of Janice and how good-looking she was.",
    85.46: "He'd really have to *rate* to date somebody like her.",
    120.64: "What about Ann?",
    122.56: "She knows how to have a good time, and how to make the fellow with her *relax*.",
    126.54: "Have fun, too.",
    128.86: "Yes, that's what a boy likes.",
    131.20: "He wants to know he's *appreciated*.",
    133.70: "Ann would be fun on a date.",
    206.10: "Well, if you don't *overdo* on dating...",
    210.26: "Ed knows what I mean. *Weekends only*, and not too late.",
    319.88: "Ann? This is Woody.",
    322.92: "Well, I have a ticket for the Hi-Teen Carnival Saturday, and...",
    327.48: "Well, would you like to go?",
    329.90: "Why, yes, Woody.",
    331.48: "I'll have to talk to *my folks* about it.",
    333.28: "But I think I can go. That'll be fine.",
    412.68: "I think the important thing about a date is to *have a good time*.",
    416.94: "You don't need to spend a lot of money to do that.",
    419.94: "You just enjoy whatever you do, whether it's movies or parties or anything.",
    426.52: "And you leave your boyfriend *enough money*, so he'll ask you again.",
    509.88: "Any girl who can't be *ready on time* for a date isn't good enough for my boy.",
    647.28: "But *how do you say good night?*",
    652.42: "Perhaps...",
    654.94: "Don't leave!",
    659.44: "*1 a.m.*",
    680.26: "Well, so long.",
    684.24: "Just like that.",
    686.96: "After all, a girl likes to know you've had a *good time*.",
    698.16: "Well, it's getting late.",
    700.82: "Yes, it is.",
    702.30: "I'd ask you in for a bite to eat if it weren't so late.",
    706.00: "Let's plan to get home in time for a *sandwich* or something next time.",
    709.90: "Say, that sounds good.",
    711.80: "I'll *call you* next week.",
    713.18: "Will you?",
    714.42: "Well, thanks so much.",
    717.02: "I had a nice time.",
    718.82: "So did I.",
    719.94: "Good night, Woody.",
    721.18: "Night, Ann.",
}

# Highlight words for the new narration (matched case-insensitively, whole words).
NARR_HIGHLIGHTS = {
    "n01": ["1949", "color", "classrooms", "date", "taught", "anxious"],
    "n02": ["rule", "appreciated", "relaxed", "inferior", "Reuben Hill", "scores", "morality offensive"],
    "n03": ["code", "initiates", "veto", "popularity", "going steady", "twenty", "twenty-two", "youngest"],
    "n04": ["economics", "pays", "wallet", "curfew", "schedule", "teenager", "1940s", "Seventeen", "1944", "front porch"],
    "n05": ["order", "early", "Kinsey", "best seller", "thirty", "twenty-eight", "public domain", "manners", "decide"],
}

# ---- Segment plan --------------------------------------------------------------
# type clip: archival footage. orig_audio True = original soundtrack plays.
# type card: title/credit card (text comes from the cue list).
# "narr": narration id that starts at this segment; B-roll segments get their
# duration from the measured narration length (+ tail).
PLAN = [
    {"id": "open", "type": "clip", "src_start": 50.3, "dur": 19.2, "orig_audio": True, "zoom": [1.0, 1.05], "fade_in": 0.8, "fade_out": 0.5,
     "note": "Cold open: 'One couple. That means a date... Only what girl?'"},
    {"id": "title", "type": "card", "still_from": 13.5, "dur": 6.0, "blur": 28, "dark": 0.62, "fade_in": 0.5, "fade_out": 0.4,
     "narr": "n01", "note": "Title card over blurred ticket close-up; narration n01 begins"},
    {"id": "b01", "type": "clip", "src_start": 12.0, "orig_audio": False, "zoom": [1.0, 1.08], "fade_in": 0.4, "fade_out": 0.5,
     "broll_for": "n01", "note": "B-roll: ticket close-up and Woody reading the note"},
    {"id": "s1a", "type": "clip", "src_start": 71.1, "dur": 11.0, "orig_audio": True, "zoom": [1.0, 1.04], "fade_in": 0.4, "fade_out": 0.3,
     "chapter": "I. Choosing the girl", "note": "'How do you choose a date?' - looks, Janice"},
    {"id": "s1b", "type": "clip", "src_start": 120.4, "dur": 15.4, "orig_audio": True, "zoom": [1.03, 1.0], "fade_in": 0.3, "fade_out": 0.5,
     "note": "'What about Ann? ... He wants to know he's appreciated.'"},
    {"id": "b02a", "type": "clip", "src_start": 102.8, "dur": 17.6, "orig_audio": False, "zoom": [1.0, 1.06], "fade_in": 0.4, "fade_out": 0.0,
     "narr": "n02", "note": "B-roll: Woody weighs Betty; narration n02"},
    {"id": "b02b", "type": "clip", "src_start": 137.6, "orig_audio": False, "zoom": [1.06, 1.0], "fade_in": 0.0, "fade_out": 0.5,
     "broll_for": "n02", "after": "b02a", "note": "B-roll: Woody decides to ask Ann"},
    {"id": "s2", "type": "clip", "src_start": 319.6, "dur": 17.0, "orig_audio": True, "zoom": [1.0, 1.05], "fade_in": 0.4, "fade_out": 0.5,
     "chapter": "II. Asking for a date", "note": "The approved phone call"},
    {"id": "b03", "type": "clip", "src_start": 566.0, "orig_audio": False, "zoom": [1.0, 1.07], "fade_in": 0.4, "fade_out": 0.5,
     "narr": "n03", "broll_for": "n03", "note": "B-roll: the Hi-Teen Carnival; narration n03"},
    {"id": "s3a", "type": "clip", "src_start": 205.9, "dur": 8.0, "orig_audio": True, "zoom": [1.0, 1.03], "fade_in": 0.4, "fade_out": 0.3,
     "chapter": "III. The rules at home", "note": "Mother: weekends only, and not too late"},
    {"id": "s3b", "type": "clip", "src_start": 412.4, "dur": 17.2, "orig_audio": True, "zoom": [1.0, 1.04], "fade_in": 0.3, "fade_out": 0.3,
     "note": "Ann: have a good time, leave your boyfriend enough money"},
    {"id": "s3c", "type": "clip", "src_start": 509.6, "dur": 4.6, "orig_audio": True, "zoom": [1.02, 1.0], "fade_in": 0.3, "fade_out": 0.5,
     "note": "Father: ready on time"},
    {"id": "b04a", "type": "clip", "src_start": 437.5, "dur": 14.5, "orig_audio": False, "zoom": [1.0, 1.06], "fade_in": 0.4, "fade_out": 0.0,
     "narr": "n04", "note": "B-roll: Ann getting ready; narration n04"},
    {"id": "b04b", "type": "clip", "src_start": 514.8, "orig_audio": False, "zoom": [1.06, 1.0], "fade_in": 0.0, "fade_out": 0.5,
     "broll_for": "n04", "after": "b04a", "note": "B-roll: Woody at the mirror"},
    {"id": "s4a", "type": "clip", "src_start": 647.0, "dur": 14.4, "orig_audio": True, "zoom": [1.0, 1.04], "fade_in": 0.4, "fade_out": 0.4,
     "chapter": "IV. Saying good night", "note": "'How do you say good night?' - the 1 a.m. ending"},
    {"id": "s4c", "type": "clip", "src_start": 697.9, "dur": 24.2, "orig_audio": True, "zoom": [1.0, 1.05], "fade_in": 0.3, "fade_out": 0.6,
     "note": "The approved good night"},
    {"id": "b05a", "type": "clip", "src_start": 603.0, "dur": 22.5, "orig_audio": False, "zoom": [1.0, 1.06], "fade_in": 0.5, "fade_out": 0.0,
     "narr": "n05", "note": "B-roll: carnival; narration n05"},
    {"id": "b05b", "type": "clip", "src_start": 722.0, "orig_audio": False, "zoom": [1.0, 1.05], "fade_in": 0.0, "fade_out": 1.0,
     "broll_for": "n05", "after": "b05a", "max_dur": 23.2, "note": "B-roll: Woody walks home; The End card"},
    {"id": "credits", "type": "card", "dur": 10.0, "colour": "0x0b0a09", "fade_in": 0.6, "fade_out": 1.2, "note": "Credits and rights card"},
]

NARR_TAIL = 1.3  # seconds of picture after narration ends


def ffprobe_dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode().strip())


def parse_vtt_words(path):
    """edge-tts word-boundary VTT -> list of (start, end, word)."""
    words = []
    if not os.path.exists(path):
        return words
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r"(\d+:\d+:\d+\.\d+) --> (\d+:\d+:\d+\.\d+)\n(.+)", txt)
    def ts(s):
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(sec)
    for a, b, w in blocks:
        words.append((ts(a), ts(b), w.strip()))
    return words


def align_script(script_text, whisper_words):
    """Give every script word a time by aligning it to the Whisper words of the
    synthesised clip (same word order; Whisper may mis-hear a few words)."""
    import difflib
    sw = script_text.split()
    norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    a = [norm(w) for w in sw]
    b = [norm(w[2]) for w in whisper_words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(sw)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (whisper_words[j1 + k][0], whisper_words[j1 + k][1])
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                times[i1 + k] = (whisper_words[j1 + k][0], whisper_words[j1 + k][1])
    # interpolate gaps
    n = len(sw)
    for i in range(n):
        if times[i] is None:
            prev = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), 0.0)
            nxt_i = next((j for j in range(i + 1, n) if times[j]), None)
            nxt = times[nxt_i][0] if nxt_i is not None else prev + 0.4 * (n - i)
            span_n = (nxt_i if nxt_i is not None else n) - i
            step = max(0.05, (nxt - prev) / (span_n + 1))
            times[i] = (prev + step * 0.2, prev + step)
            times[i] = (round(times[i][0], 3), round(times[i][1], 3))
    return [(t[0], t[1], w) for t, w in zip(times, sw)]


def group_words(words, max_chars=56, max_gap=0.8):
    """Group timed words into subtitle lines, breaking at punctuation."""
    lines, cur = [], []
    def cur_len():
        return len(" ".join(x[2] for x in cur))
    for w in words:
        if cur and (cur_len() + len(w[2]) + 1 > max_chars or w[0] - cur[-1][1] > max_gap):
            lines.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.!?]$", w[2]) and cur_len() > 18:
            lines.append(cur); cur = []
        elif re.search(r"[,;:]$", w[2]) and cur_len() > 36:
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    return lines


def highlight(text, terms):
    for t in sorted(terms, key=len, reverse=True):
        text = re.sub(r"(?<![\w*])(" + re.escape(t) + r")(?![\w*])", r"*\1*", text, count=1, flags=re.I)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration-dir", default="audio/narration")
    ap.add_argument("--transcript", default="source/transcript.json")
    a = ap.parse_args()

    # narration durations
    ndur = {}
    for n in ["n01", "n02", "n03", "n04", "n05"]:
        p = os.path.join(a.narration_dir, n + ".48k.wav")
        ndur[n] = ffprobe_dur(p) if os.path.exists(p) else {"n01": 19, "n02": 27, "n03": 30, "n04": 29, "n05": 40}[n]

    # resolve B-roll durations
    segs = [dict(s) for s in PLAN]
    by_id = {s["id"]: s for s in segs}
    for s in segs:
        if "broll_for" in s and "dur" not in s:
            need = ndur[s["broll_for"]] + NARR_TAIL
            if "after" in s:
                need -= by_id[s["after"]]["dur"]
            if s["broll_for"] == "n01":
                need -= by_id["title"]["dur"]
            need = max(3.0, need)
            if "max_dur" in s:
                need = min(need, s["max_dur"])
            s["dur"] = round(need, 2)
    # timeline
    t = 0.0
    for s in segs:
        s["t0"] = round(t, 3)
        t += s["dur"]
    total = t

    narration = []
    for s in segs:
        if "narr" in s:
            narration.append({"id": s["narr"], "file": os.path.join(a.narration_dir, s["narr"] + ".48k.wav"), "at": round(s["t0"] + 0.6, 3)})

    edl = {
        "source": SOURCE, "source_audio": SOURCE_AUDIO, "fps": "30000/1001",
        "segments": [{k: v for k, v in s.items() if k not in ("t0", "narr", "broll_for", "after", "max_dur", "chapter")} for s in segs],
        "narration": narration,
        "music": {"file": "music/background.mp3", "gain_db": -16, "fade_out": 8},
        "subtitles": "subs/documentary.ass",
    }
    os.makedirs("edit", exist_ok=True)
    json.dump(edl, open("edit/edl.json", "w"), indent=1)

    # ---- cues ----
    cues = []
    tr = json.load(open(a.transcript))
    tsegs = tr["segments"] if "segments" in tr else tr["data"]["segments"]
    for s in segs:
        if s["type"] != "clip" or not s.get("orig_audio"):
            continue
        a0, a1 = s["src_start"], s["src_start"] + s["dur"]
        for ts_ in tsegs:
            if ts_["end"] <= a0 + 0.2 or ts_["start"] >= a1 - 0.2:
                continue
            key = min(CORRECTIONS, key=lambda k: abs(k - ts_["start"]))
            text = CORRECTIONS[key] if abs(key - ts_["start"]) < 0.6 else ts_["text"].strip()
            st = max(ts_["start"], a0) - a0 + s["t0"]
            en = min(ts_["end"], a1) - a0 + s["t0"]
            if en - st < 0.4:
                en = st + 1.0
            cues.append({"start": round(st, 3), "end": round(min(en, s["t0"] + s["dur"]), 3), "text": text, "style": "ORIG"})
    script = {it["id"]: it["text"] for it in json.load(open("edit/narration.json"))}
    for n in narration:
        wwords = parse_vtt_words(os.path.join(a.narration_dir, n["id"] + ".vtt"))
        if not wwords:
            continue
        words = align_script(script[n["id"]], wwords)
        groups = group_words(words)
        for gi, grp in enumerate(groups):
            text = " ".join(w[2] for w in grp)
            text = highlight(text, NARR_HIGHLIGHTS.get(n["id"], []))
            st = n["at"] + grp[0][0]
            en = n["at"] + grp[-1][1] + 0.4
            if gi + 1 < len(groups):
                en = min(en, n["at"] + groups[gi + 1][0][0] - 0.04)
            cues.append({"start": round(st, 3), "end": round(en, 3), "text": text, "style": "NARR"})
    # title and credits
    tt = by_id["title"]["t0"]
    cues.append({"start": tt + 0.3, "end": tt + by_id["title"]["dur"] - 0.1, "text": "The Strange Dating Rules\\NAmerican Schools Taught in 1949", "style": "TITLE"})
    cues.append({"start": tt + 1.2, "end": tt + by_id["title"]["dur"] - 0.1, "text": "\\N\\N\\N\\N\\N\\NAn AI-restored archival documentary demo", "style": "SUBTITLE"})
    # chapters
    for s in segs:
        if "chapter" in s:
            cues.append({"start": s["t0"] + 0.4, "end": s["t0"] + 4.5, "text": s["chapter"], "style": "CHAPTER"})
    # annotations (lower-third fact cards)
    ann = [
        ("b01", 1.6, 10.0, "Dating: Do's and Don'ts (1949)\\NCoronet Instructional Films · Glenview, Illinois · Kodachrome print"),
        ("b02b", 0.2, 9.0, "Educational collaborator: Reuben Hill\\NResearch Professor of Family Life, University of North Carolina"),
        ("b03", 14.0, 27.0, "Median age at first marriage, 1950\\Nwomen 20.3 · men 22.8   (U.S. Census Bureau, table MS-2)"),
        ("b04a", 9.5, 19.0, "\"Teenager\" enters common use in the 1940s\\NSeventeen magazine founded 1944"),
        ("b05a", 11.0, 20.0, "Median age at first marriage, 2024\\Nwomen 28.6 · men 30.5   (NCFMR / American Community Survey)"),
        ("b05b", 2.0, 11.0, "Copyright registered 1949 (MP5069)\\NNo renewal found in the 1976–1977 Catalog of Copyright Entries"),
    ]
    for sid, o0, o1, text in ann:
        s = by_id[sid]
        cues.append({"start": round(s["t0"] + o0, 3), "end": round(min(s["t0"] + o1, s["t0"] + s["dur"] + 6), 3), "text": text, "style": "ANNOT"})
    # archival label (merged across back-to-back original clips)
    label_runs = []
    for s in segs:
        if s["type"] == "clip" and s.get("orig_audio"):
            if label_runs and abs(label_runs[-1][1] - s["t0"]) < 0.01:
                label_runs[-1][1] = s["t0"] + s["dur"]
            else:
                label_runs.append([s["t0"], s["t0"] + s["dur"]])
    for a0, a1 in label_runs:
        cues.append({"start": round(a0 + 0.2, 3), "end": round(a1 - 0.2, 3), "text": "ORIGINAL AUDIO · 1949", "style": "LABEL"})
    cr = by_id["credits"]
    credit_text = ("Archival film: Dating: Do's and Don'ts (Coronet Instructional Films, 1949)\\N"
                   "Prelinger Archives / Internet Archive · public domain (copyright not renewed)\\N\\N"
                   "Music: Kevin MacLeod (incompetech.com) · Licensed under Creative Commons: By Attribution 4.0\\N"
                   "Narration: synthetic voice (Kokoro-82M open-source TTS) · Restoration and edit: FFmpeg pipeline\\N\\N"
                   "Sources: Bailey, From Front Porch to Back Seat (1988) · Smith, Mental Hygiene (1999) · U.S. Census Bureau MS-2 · NCFMR\\N"
                   "Full citations in SOURCES.md and COPYRIGHT_REPORT.md")
    cues.append({"start": cr["t0"] + 0.5, "end": cr["t0"] + cr["dur"] - 0.8, "text": credit_text, "style": "CREDIT"})
    cues.sort(key=lambda c: c["start"])
    json.dump(cues, open("edit/cues.json", "w"), indent=1)

    # plain SRT (speech only)
    def srt_ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"
    speech = [c for c in cues if c["style"] in ("ORIG", "NARR")]
    with open("SUBTITLES.srt", "w") as f:
        for i, c in enumerate(speech, 1):
            txt = c["text"].replace("*", "").replace("\\N", "\n")
            if c["style"] == "ORIG":
                txt = "[1949 film] " + txt
            f.write(f"{i}\n{srt_ts(c['start'])} --> {srt_ts(c['end'])}\n{txt}\n\n")

    with open("edit/timeline.txt", "w") as f:
        for s in segs:
            f.write(f"{s['t0']:7.2f}  {s['id']:8s} {s['type']:5s} {s['dur']:6.2f}  {'orig' if s.get('orig_audio') else '    '}  {s.get('note','')}\n")
        f.write(f"total {total:.2f} s  ({int(total//60)}:{total%60:05.2f})\n")
        for n in narration:
            f.write(f"narration {n['id']} at {n['at']:.2f} for {ndur[n['id']]:.2f}s\n")
    print(open("edit/timeline.txt").read())


if __name__ == "__main__":
    main()
