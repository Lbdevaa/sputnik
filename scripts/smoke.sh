#!/usr/bin/env bash
# Прогон сценариев из docs/behaviour.md по живому стенду.
#
# Запускается после каждого шага рефакторинга: поведение конвейера и HTTP-контракт
# должны остаться прежними. Проверки помечены [A1], [A8]… — это номера дефектов из
# docs/audit.md; такие проверки красные на исходном коде и обязаны позеленеть после
# соответствующего шага.
#
# Использование: ./scripts/smoke.sh

set -uo pipefail

API="${API:-http://localhost:8000}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASSED=0
FAILED=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  ok   %-58s %s\n' "$name" "$actual"
    PASSED=$((PASSED + 1))
  else
    printf '  FAIL %-58s ожидалось %s, получено %s\n' "$name" "$expected" "$actual"
    FAILED=$((FAILED + 1))
  fi
}

field() { # field <json> <ключ через точку>
  python -c "
import json, sys
try:
    data = json.loads(sys.argv[1])
except ValueError:
    print('не JSON: ' + (sys.argv[1][:60] or 'пустой ответ'))
    raise SystemExit
for key in sys.argv[2].split('.'):
    data = (data or {}).get(key) if isinstance(data, dict) else None
print(json.dumps(data) if isinstance(data, (dict, list)) else data)
" "$1" "$2"
}

# Под Git Bash curl нативный и msys-путей вида /tmp/... не понимает.
native_path() {
  if command -v cygpath > /dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi
}

upload() { # upload <файл> <заголовок> [content-type]
  local path title ctype spec
  path="$(native_path "$1")"
  title="$2"
  ctype="${3:-}"
  spec="file=@$path"
  [ -n "$ctype" ] && spec="file=@$path;type=$ctype"
  curl -s -X POST "$API/files" -F "title=$title" -F "$spec"
}

await_processed() { # await_processed <id>; ждёт терминального статуса
  local id="$1"
  for _ in $(seq 40); do
    local body status
    body="$(curl -s "$API/files/$id")"
    status="$(field "$body" processing_status)"
    if [ "$status" = "processed" ] || [ "$status" = "failed" ]; then
      echo "$body"
      return 0
    fi
    sleep 0.25
  done
  echo "$body"
}

printf '%%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n2 0 obj\n<< /Type/Page >>\nendobj\n3 0 obj\n<< /Type/Page >>\nendobj\ntrailer\n%%%%EOF\n' > "$TMP/two_pages.pdf"
printf 'line one\nline two\nline three\n' > "$TMP/sample.txt"
printf 'MZ\x90\x00fake executable payload\n' > "$TMP/sample.exe"
head -c 11000000 /dev/urandom > "$TMP/big.bin"
: > "$TMP/empty.txt"

echo "== текстовый файл =="
body="$(await_processed "$(field "$(upload "$TMP/sample.txt" 'smoke txt')" id)")"
check "scan_status" "clean" "$(field "$body" scan_status)"
check "scan_details" "no threats found" "$(field "$body" scan_details)"
check "processing_status" "processed" "$(field "$body" processing_status)"
check "requires_attention" "False" "$(field "$body" requires_attention)"
check "metadata.line_count" "3" "$(field "$body" metadata_json.line_count)"
check "metadata.char_count" "29" "$(field "$body" metadata_json.char_count)"
txt_id="$(field "$body" id)"

echo "== исполняемый файл =="
body="$(await_processed "$(field "$(upload "$TMP/sample.exe" 'smoke exe')" id)")"
check "scan_status" "suspicious" "$(field "$body" scan_status)"
check "scan_details" "suspicious extension .exe" "$(field "$body" scan_details)"
check "requires_attention" "True" "$(field "$body" requires_attention)"

echo "== файл больше 10 МБ =="
body="$(await_processed "$(field "$(upload "$TMP/big.bin" 'smoke big')" id)")"
check "scan_status" "suspicious" "$(field "$body" scan_status)"
check "scan_details" "file is larger than 10 MB" "$(field "$body" scan_details)"

echo "== pdf =="
body="$(await_processed "$(field "$(upload "$TMP/two_pages.pdf" 'smoke pdf')" id)")"
check "scan_status" "clean" "$(field "$body" scan_status)"
check "[A11] approx_page_count (в файле две страницы)" "2" "$(field "$body" metadata_json.approx_page_count)"

echo "== подмена mime-типа =="
body="$(await_processed "$(field "$(upload "$TMP/two_pages.pdf" 'smoke pdf spoof' 'text/plain')" id)")"
check "[A9] pdf под видом text/plain: тип определён по содержимому" "application/pdf" "$(field "$body" mime_type)"

echo "== алерты =="
alerts="$(curl -s "$API/alerts")"
check "алерт для текстового файла" "info" \
  "$(python -c "
import json, sys
items = json.loads(sys.argv[1])
items = items.get('items', items) if isinstance(items, dict) else items
print(next((a['level'] for a in items if a['file_id'] == sys.argv[2]), 'нет алерта'))
" "$alerts" "$txt_id")"

echo "== HTTP-контракт =="
check "GET /files" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/files")"
check "GET /alerts" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/alerts")"
check "GET несуществующего файла" "404" "$(curl -s -o /dev/null -w '%{http_code}' "$API/files/no-such-id")"
check "пустой файл" "400" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/files" -F 'title=empty' -F "file=@$(native_path "$TMP/empty.txt")")"
check "PATCH названия" "200" "$(curl -s -o /dev/null -w '%{http_code}' -X PATCH "$API/files/$txt_id" -H 'Content-Type: application/json' --data-binary '{"title":"renamed"}')"
check "скачивание" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/files/$txt_id/download")"
check "[A1] удаление файла, по которому есть алерт" "204" "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$API/files/$txt_id")"
check "[A8] после удаления файла его карточка недоступна" "404" "$(curl -s -o /dev/null -w '%{http_code}' "$API/files/$txt_id")"

echo
echo "пройдено: $PASSED, провалено: $FAILED"
[ "$FAILED" -eq 0 ]
