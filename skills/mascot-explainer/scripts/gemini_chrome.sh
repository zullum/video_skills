#!/usr/bin/env bash
# The Chrome that gemini_web.cjs draws in: CDP on port 9003 with its own profile in ~/chrome-debug-9003, opened on
# the Gemini web app. Log in to the Google account with the Gemini plan once by hand; the session stays in the profile.
#   bash gemini_chrome.sh [url]      (a no-op when something already listens on 9003)
set -u
PORT=9003
DST="$HOME/chrome-debug-9003"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

if curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null; then
  echo "Already listening on $PORT"; exit 0
fi
[ -x "$CHROME" ] || { echo "Chrome not found at $CHROME (set CHROME=...)" >&2; exit 1; }

mkdir -p "$DST"
"$CHROME" --user-data-dir="$DST" --remote-debugging-port="$PORT" --no-first-run --no-default-browser-check \
  "${1:-https://gemini.google.com/app}" > /tmp/chrome-$PORT.log 2>&1 &

for _ in $(seq 1 30); do
  sleep 0.5
  curl -s --max-time 2 "http://127.0.0.1:$PORT/json/version" >/dev/null && { echo "Chrome on $PORT"; exit 0; }
done
echo "Chrome did not open CDP on $PORT (see /tmp/chrome-$PORT.log)" >&2; exit 1
