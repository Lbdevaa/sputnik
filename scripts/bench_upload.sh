#!/usr/bin/env bash
# Замер блокировки event loop.
#
# Пока идут параллельные загрузки крупного файла, меряем latency лёгкого GET /files.
# Если запись файла синхронная, лёгкий запрос ждёт освобождения event loop.
#
# Использование: ./scripts/bench_upload.sh [число_параллельных_загрузок] [размер_МБ]

set -euo pipefail

API="${API:-http://localhost:8000}"
N="${1:-6}"
SIZE_MB="${2:-11}"
PAYLOAD="$(mktemp -t bench_upload_XXXXXX).bin"
trap 'rm -f "$PAYLOAD"' EXIT

head -c "$((SIZE_MB * 1000 * 1000))" /dev/urandom > "$PAYLOAD"

measure() {
  local runs="$1"
  for _ in $(seq "$runs"); do
    curl -s -o /dev/null -w "%{time_total}\n" "$API/files"
  done | awk '{s+=$1; if($1>m) m=$1} END {printf "avg=%.3fs max=%.3fs\n", s/NR, m}'
}

echo "== GET /files без нагрузки =="
measure 5

echo "== $N параллельных загрузок по ${SIZE_MB} МБ =="
for i in $(seq "$N"); do
  curl -s -o /dev/null -X POST "$API/files" \
    -F "title=bench $i" -F "file=@$PAYLOAD" &
done

sleep 0.2
echo "== GET /files во время загрузок =="
measure 15

wait
echo "== загрузки завершены =="
