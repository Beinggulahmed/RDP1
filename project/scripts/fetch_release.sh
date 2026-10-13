#!/usr/bin/env bash
# Download every asset of a GitHub release of this (public) repository.
# Usage: fetch_release.sh <tag> <dest_dir>
set -euo pipefail
TAG="$1"; DEST="$2"
REPO="${REPO:-Beinggulahmed/RDP1}"
mkdir -p "$DEST"
curl -sS "https://api.github.com/repos/$REPO/releases/tags/$TAG" -o "$DEST/.release.json"
python3 -I - "$DEST/.release.json" <<'PY' > "$DEST/.assets.txt"
import json, sys
d = json.load(open(sys.argv[1]))
if 'assets' not in d:
    sys.exit('release not found: ' + json.dumps(d)[:200])
for a in d['assets']:
    print(a['name'], a['browser_download_url'], a['size'])
PY
while read -r name url size; do
  if [ -f "$DEST/$name" ] && [ "$(stat -c %s "$DEST/$name")" = "$size" ]; then echo "have  $name"; continue; fi
  echo "fetch $name ($size bytes)"
  curl -sSL --retry 5 --retry-all-errors -o "$DEST/$name" "$url"
done < "$DEST/.assets.txt"
ls -la "$DEST"
