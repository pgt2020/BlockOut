#!/bin/bash
cd "$(dirname "$0")"
PORT=8800
if ! lsof -i :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  python3 -m http.server $PORT &
  sleep 0.6
fi
open "http://127.0.0.1:$PORT/game.html"
