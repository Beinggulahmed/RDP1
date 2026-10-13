#!/usr/bin/env bash
# Restore and upscale one archival clip with FFmpeg.
#
# Usage: restore_clip.sh <source> <start_sec> <duration_sec> <out.mp4> [width height] [extra_vf]
#
# Pipeline (all FFmpeg, CPU only, no AI colourisation - the film is already colour):
#   1. bwdif      - deinterlace the MPEG-2 telecine/interlaced source (frame-rate preserving)
#   2. crop       - remove the dark frame-line borders of the 4:3 scan (set via CROP env)
#   3. deflicker  - average luminance across 7 frames to tame film flicker
#   4. hqdn3d     - mild spatial + stronger temporal denoise (grain, dust, compression noise)
#   5. deshake    - stabilise small gate weave / camera shake
#   6. eq/curves  - exposure, contrast, saturation; lift faded blacks, recover highlights
#   7. scale      - Lanczos upscale to the target height (4:3 kept, no stretching)
#   8. unsharp    - gentle sharpen after upscale (luma only, small radius)
#   9. pad        - pillarbox into 16:9 on a dark gradient (documentary framing)
#
# The result is an intermediate: high-quality H.264 (crf 12) in the target frame size.
set -euo pipefail
SRC="$1"; START="$2"; DUR="$3"; OUT="$4"
W="${5:-3840}"; H="${6:-2160}"; EXTRA_VF="${7:-}"
CROP="${CROP:-crop=iw-16:ih-8:8:4}"       # trim scan borders; override per source
FPS="${FPS:-24000/1001}"
INNER_H=$H
INNER_W=$(( (INNER_H * 4 / 3) / 2 * 2 ))  # 4:3 inner picture, even width
PILLAR_BG="${PILLAR_BG:-0x0d0b09}"

VF="bwdif=mode=send_frame:parity=auto:deint=all,${CROP},deflicker=size=7:mode=am,hqdn3d=2.5:2.0:6:6,deshake=rx=16:ry=16:edge=mirror:blocksize=8,eq=contrast=1.06:brightness=0.01:saturation=1.08:gamma=1.02,curves=master='0/0 0.06/0.03 0.5/0.52 0.94/0.97 1/1',scale=${INNER_W}:${INNER_H}:flags=lanczos,unsharp=5:5:0.45:3:3:0.0,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=${PILLAR_BG},format=yuv420p"
if [ -n "$EXTRA_VF" ]; then VF="${VF},${EXTRA_VF}"; fi

ffmpeg -v error -y -ss "$START" -i "$SRC" -t "$DUR" -an \
  -vf "$VF" -r "$FPS" \
  -c:v libx264 -preset medium -crf 12 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -movflags +faststart "$OUT"
echo "restored: $OUT"
