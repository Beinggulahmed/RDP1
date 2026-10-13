#!/usr/bin/env bash
# Quality-control report for a rendered documentary.
# Usage: qc.sh <final.mp4> [expected_width expected_height] > QC_REPORT.txt
set -uo pipefail
F="$1"; EW="${2:-3840}"; EH="${3:-2160}"
echo "== File: $F"
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 "$F"
echo "== Streams"
ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,pix_fmt,color_space -of csv=p=0 "$F"
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$F")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$F")
[ "$W" = "$EW" ] && [ "$H" = "$EH" ] && echo "RESOLUTION OK ${W}x${H}" || echo "RESOLUTION MISMATCH ${W}x${H} (expected ${EW}x${EH})"
VD=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$F")
AD=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$F")
python3 -c "v=float('$VD');a=float('$AD');print(f'video {v:.3f}s audio {a:.3f}s diff {abs(v-a)*1000:.0f} ms -> ' + ('SYNC LENGTH OK' if abs(v-a)<0.1 else 'CHECK A/V LENGTH'))"
echo "== Frame count vs duration"
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames,avg_frame_rate -of csv=p=0 "$F"
echo "== Black frames (>0.5 s of black = problem)"
ffmpeg -v info -i "$F" -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null - 2>&1 | grep black_start || echo "none"
echo "== Frozen video (>2 s)"
ffmpeg -v info -i "$F" -vf "freezedetect=n=0.001:d=2" -an -f null - 2>&1 | grep -E "freeze_start|freeze_end" || echo "none"
echo "== Loudness (EBU R128, target -14 LUFS, TP <= -1.5)"
ffmpeg -v info -i "$F" -af "ebur128=peak=true" -vn -f null - 2>&1 | grep -A8 "Summary" | sed 's/^ *//'
echo "== Silence longer than 3 s in the mix"
ffmpeg -v info -i "$F" -af "silencedetect=n=-45dB:d=3" -vn -f null - 2>&1 | grep silence_ || echo "none"
echo "== Decode check (errors below, if any)"
ffmpeg -v error -i "$F" -f null - 2>&1 | head -5 || true
echo "DECODE DONE"
