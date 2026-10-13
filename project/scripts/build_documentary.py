#!/usr/bin/env python3
"""Assemble the documentary from an edit decision list (EDL) with FFmpeg.

Usage: build_documentary.py edl.json --out-dir work/build --w 3840 --h 2160 [--stage video|audio|final|all]

EDL format (JSON):
{
  "source": "source/DatingDo1949.mpeg",          # restored clips are cut from here
  "source_audio": "audio/original_audio_48k.wav", # clean original soundtrack
  "fps": "24000/1001",
  "segments": [                                   # played back-to-back
    {"id": "s01", "type": "clip", "src_start": 12.0, "dur": 8.0,
     "orig_audio": true, "zoom": [1.0, 1.06], "fade_in": 0.4, "fade_out": 0.4},
    {"id": "t01", "type": "card", "dur": 5.0, "still_from": 40.0, "blur": 24, "dark": 0.35}
  ],
  "narration": [{"id": "n01", "file": "audio/narration/n01.mp3", "at": 30.0}],
  "music": {"file": "music/Wholesome.mp3", "gain_db": -20, "fade_out": 6},
  "subtitles": "subs/documentary.ass"
}
Timeline positions of segments are derived from the cumulative durations.
"""
import argparse
import json
import os
import subprocess
import sys

SEG_PRESET = os.environ.get("X264_PRESET_SEG", "fast")
FINAL_PRESET = os.environ.get("X264_PRESET_FINAL", "medium")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def ffprobe_dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out.decode().strip())


def seg_starts(segments):
    t = 0.0
    starts = {}
    for s in segments:
        starts[s["id"]] = t
        t += float(s["dur"])
    return starts, t


def render_clip(edl, seg, out, w, h):
    inner_h = h
    inner_w = (inner_h * 4 // 3) // 2 * 2
    dur = float(seg["dur"])
    vf = []
    vf.append(edl.get("deinterlace", "fieldmatch=order=tff:combmatch=full,yadif=deint=interlaced"))
    crop = seg.get("crop", edl.get("crop"))
    if crop:
        vf.append(crop)
    vf.append("deflicker=size=7:mode=am")
    vf.append(seg.get("denoise", edl.get("denoise", "hqdn3d=1.2:1.0:5:5")))
    if seg.get("stabilize", edl.get("stabilize", True)):
        vf.append("deshake=rx=16:ry=16:edge=mirror:blocksize=8")
    vf.append(seg.get("color", edl.get("color", "eq=contrast=1.02:saturation=1.06:gamma=1.12")))
    vf.append(seg.get("curves", edl.get("curves", "curves=master='0/0 0.08/0.11 0.5/0.54 0.92/0.95 1/1'")))
    # Lanczos upscale to a working size a little larger than the frame for the zoom
    z0, z1 = seg.get("zoom", [1.0, 1.0])
    vf.append(f"scale={inner_w}:{inner_h}:flags=lanczos")
    if (z0, z1) != (1.0, 1.0):
        fps = edl.get("fps", "30000/1001")
        nframes = dur * eval(fps)
        vf.append(f"zoompan=z='{z0}+({z1}-{z0})*in/{nframes:.2f}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={inner_w}x{inner_h}:fps={fps}")
    vf.append(seg.get("sharpen", edl.get("sharpen", "unsharp=5:5:0.5:3:3:0.0")))
    bg = edl.get("pillar_bg", "0x0d0b09")
    vf.append(f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg}")
    fi, fo = float(seg.get("fade_in", 0)), float(seg.get("fade_out", 0))
    if fi > 0:
        vf.append(f"fade=t=in:st=0:d={fi}")
    if fo > 0:
        vf.append(f"fade=t=out:st={dur - fo:.3f}:d={fo}")
    vf.append("format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(seg["src_start"]), "-i", edl["source"], "-t", str(dur), "-an",
         "-vf", ",".join(vf), "-r", edl.get("fps", "30000/1001"),
         "-c:v", "libx264", "-preset", SEG_PRESET, "-crf", "13", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out])


def render_card(edl, seg, out, w, h):
    dur = float(seg["dur"])
    fps = edl.get("fps", "30000/1001")
    fi, fo = float(seg.get("fade_in", 0.6)), float(seg.get("fade_out", 0.6))
    fades = (f",fade=t=in:st=0:d={fi}" if fi > 0 else "") + (f",fade=t=out:st={dur - fo:.3f}:d={fo}" if fo > 0 else "")
    if "still_from" in seg:
        blur = seg.get("blur", 20)
        dark = seg.get("dark", 0.4)
        z0, z1 = seg.get("zoom", [1.0, 1.08])
        # take one frame and loop it
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(seg["still_from"]), "-i", edl["source"], "-frames:v", "1",
             "-vf", f"bwdif=mode=send_frame,scale={w}:{h}:flags=lanczos:force_original_aspect_ratio=increase,crop={w}:{h},gblur=sigma={blur},eq=brightness=-{dark}:saturation=0.8",
             out + ".still.png"])
        nframes = dur * eval(fps)
        vf2 = f"zoompan=z='{z0}+({z1}-{z0})*in/{nframes:.2f}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={fps}{fades},format=yuv420p"
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", fps, "-i", out + ".still.png", "-t", str(dur),
             "-vf", vf2, "-r", fps, "-c:v", "libx264", "-preset", SEG_PRESET, "-crf", "13", "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out])
    else:
        colour = seg.get("colour", "0x0d0b09")
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={colour}:s={w}x{h}:r={fps}:d={dur}",
             "-vf", f"format=yuv420p{fades}", "-c:v", "libx264", "-preset", SEG_PRESET, "-crf", "13", "-pix_fmt", "yuv420p",
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out])


def build_video(edl, out_dir, w, h):
    seg_dir = os.path.join(out_dir, "segments")
    os.makedirs(seg_dir, exist_ok=True)
    paths = []
    for seg in edl["segments"]:
        key = json.dumps({k: v for k, v in seg.items()}, sort_keys=True) + f"{w}x{h}"
        out = os.path.join(seg_dir, f"{seg['id']}_{w}.mp4")
        stamp = out + ".key"
        if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
            print("cached", out)
        else:
            if seg["type"] == "clip":
                render_clip(edl, seg, out, w, h)
            else:
                render_card(edl, seg, out, w, h)
            open(stamp, "w").write(key)
        actual = ffprobe_dur(out)
        if abs(actual - float(seg["dur"])) > 0.15:
            print(f"WARNING segment {seg['id']} duration {actual:.3f} vs planned {seg['dur']}")
        paths.append(out)
    lst = os.path.join(out_dir, f"concat_{w}.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in paths))
    out = os.path.join(out_dir, f"video_{w}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return out


def build_audio(edl, out_dir):
    starts, total = seg_starts(edl["segments"])
    os.makedirs(out_dir, exist_ok=True)
    inputs, filt, orig_labels, narr_labels = [], [], [], []
    idx = 0
    # original soundtrack pieces
    for seg in edl["segments"]:
        if seg["type"] != "clip" or not seg.get("orig_audio"):
            continue
        gain = -12 if seg.get("orig_audio") == "low" else 0
        inputs += ["-i", edl["source_audio"]]
        fi, fo = float(seg.get("afade_in", 0.15)), float(seg.get("afade_out", 0.25))
        a0, a1 = float(seg["src_start"]), float(seg["src_start"]) + float(seg["dur"])
        filt.append(f"[{idx}:a]atrim={a0:.3f}:{a1:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,lowpass=f=7500,afftdn=nf=-28:nr=12,"
                    f"afade=t=in:st=0:d={fi},afade=t=out:st={float(seg['dur']) - fo:.3f}:d={fo},"
                    f"volume={gain}dB,adelay={int(starts[seg['id']] * 1000)}|{int(starts[seg['id']] * 1000)},asetpts=PTS-STARTPTS[o{idx}]")
        orig_labels.append(f"[o{idx}]")
        idx += 1
    for n in edl.get("narration", []):
        inputs += ["-i", n["file"]]
        filt.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
                    f"loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,adelay={int(float(n['at']) * 1000)}|{int(float(n['at']) * 1000)},asetpts=PTS-STARTPTS[n{idx}]")
        narr_labels.append(f"[n{idx}]")
        idx += 1
    m = edl.get("music")
    music_label = None
    if m:
        inputs += ["-stream_loop", "-1", "-i", m["file"]]
        fo = float(m.get("fade_out", 6))
        filt.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},"
                    f"loudnorm=I=-18:TP=-2:LRA=11,aresample=48000,volume={m.get('gain_db', -14)}dB,"
                    f"afade=t=in:st=0:d=3,afade=t=out:st={total - fo:.3f}:d={fo}[m]")
        music_label = "[m]"
        idx += 1
    # stems
    def mixsum(labels, name):
        if not labels:
            filt.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.3f}[{name}]")
        elif len(labels) == 1:
            filt.append(f"{labels[0]}apad=whole_dur={total:.3f},atrim=0:{total:.3f}[{name}]")
        else:
            filt.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,asetpts=PTS-STARTPTS,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[{name}]")
    mixsum(orig_labels, "orig")
    mixsum(narr_labels, "narr")
    filt.append("[orig]asplit=2[orig_out][orig_mix]")
    filt.append("[narr]asplit=2[narr_out][narr_mix]")
    filt.append("[orig_mix][narr_mix]amix=inputs=2:normalize=0:dropout_transition=0[speech]")
    filt.append("[speech]asplit=2[speech_a][speech_sc]")
    if music_label:
        filt.append(f"{music_label}[speech_sc]sidechaincompress=threshold=0.015:ratio=10:attack=40:release=900:makeup=1:level_sc=1[mduck]")
        filt.append("[mduck]asplit=2[music_out][music_mix]")
        filt.append("[speech_a][music_mix]amix=inputs=2:normalize=0:dropout_transition=0[pre]")
    else:
        filt.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.3f}[music_out]")
        filt.append("[speech_sc]anullsink")
        filt.append("[speech_a]acopy[pre]")
    filt.append("[pre]loudnorm=I=-14:TP=-1.5:LRA=11:linear=true,aresample=48000[mix]")
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt),
           "-map", "[mix]", "-c:a", "pcm_s16le", os.path.join(out_dir, "mix.wav"),
           "-map", "[orig_out]", "-c:a", "pcm_s16le", os.path.join(out_dir, "track_original_narrator.wav"),
           "-map", "[narr_out]", "-c:a", "pcm_s16le", os.path.join(out_dir, "track_new_narration.wav"),
           "-map", "[music_out]", "-c:a", "pcm_s16le", os.path.join(out_dir, "track_music_ducked.wav")]
    run(cmd)
    return os.path.join(out_dir, "mix.wav")


def build_final(edl, out_dir, w, h, video, audio, out, preview=None):
    ass = edl.get("subtitles")
    vf = f"ass={ass}" if ass else "null"
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-vf", vf, "-c:v", "libx264", "-preset", FINAL_PRESET, "-crf", "16", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out])
    if preview:
        run(["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
             "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", preview])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--out-dir", default="work/build")
    ap.add_argument("--w", type=int, default=3840)
    ap.add_argument("--h", type=int, default=2160)
    ap.add_argument("--stage", default="all", choices=["video", "audio", "final", "all", "timeline"])
    ap.add_argument("--final", default=None)
    ap.add_argument("--preview", default=None)
    a = ap.parse_args()
    edl = json.load(open(a.edl))
    os.chdir(ROOT)
    starts, total = seg_starts(edl["segments"])
    if a.stage == "timeline":
        for s in edl["segments"]:
            print(f"{starts[s['id']]:7.2f}  {s['id']:6s} {s['type']:5s} {s['dur']:6.2f}  {s.get('note', '')}")
        print(f"total {total:.2f}s")
        return
    video = audio = None
    if a.stage in ("video", "all"):
        video = build_video(edl, a.out_dir, a.w, a.h)
    if a.stage in ("audio", "all"):
        audio = build_audio(edl, os.path.join(a.out_dir, "audio"))
    if a.stage in ("final", "all"):
        video = video or os.path.join(a.out_dir, f"video_{a.w}.mp4")
        audio = audio or os.path.join(a.out_dir, "audio", "mix.wav")
        build_final(edl, a.out_dir, a.w, a.h, video, audio, a.final or os.path.join(a.out_dir, f"final_{a.w}.mp4"), a.preview)


if __name__ == "__main__":
    main()
