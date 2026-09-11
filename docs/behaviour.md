# Эталонное поведение (baseline)

Снято на исходном коде (коммит `bc4cb29`) на живом стенде `docker compose -f docker-compose.dev.yml up`
+ `docker exec -it backend alembic upgrade head`. Дата снятия: 2026-09-04.

Этот документ — контракт рефакторинга: после любых изменений поведение из таблиц ниже
должно сохраниться (кроме строк, помеченных «дефект» — их чиним осознанно и фиксируем в
[audit.md](audit.md)).

## 1. Конвейер обработки: вход → выход

Загрузка файла запускает цепочку `scan_file_for_threats` → `extract_file_metadata` → `send_file_alert`.
Проверено фактически, значения — из `GET /files` и `GET /alerts` после завершения обработки.

| Вход | `scan_status` | `scan_details` | `processing_status` | `requires_attention` | `metadata_json` | Алерт |
|---|---|---|---|---|---|---|
| `sample.txt` (29 B, `text/plain`) | `clean` | `no threats found` | `processed` | `false` | `extension`, `size_bytes`, `mime_type`, `line_count=3`, `char_count=29` | `info` — «File processed successfully» |
| `sample.exe` (28 B, `application/octet-stream`) | `suspicious` | `suspicious extension .exe` | `processed` | `true` | `extension`, `size_bytes`, `mime_type` | `warning` — «File requires attention: suspicious extension .exe» |
| `sample.pdf` (123 B, `application/pdf`) | `clean` | `no threats found` | `processed` | `false` | + `approx_page_count=1` | `info` |
| `big.bin` (11 000 000 B, `application/octet-stream`) | `suspicious` | `file is larger than 10 MB` | `processed` | `true` | `extension`, `size_bytes`, `mime_type` | `warning` — «File requires attention: file is larger than 10 MB» |

Правила детекта, зашитые в `tasks.py`:

- расширение из множества `.exe .bat .cmd .sh .js` → `suspicious extension {ext}`;
- размер > 10 МБ (`10 * 1024 * 1024`) → `file is larger than 10 MB`;
- расширение `.pdf` и `mime_type` не в `{application/pdf, application/octet-stream}` → `pdf extension does not match mime type`;
- причин нет → `scan_status = clean`, `scan_details = no threats found`.

Метаданные:

- всегда: `extension`, `size_bytes`, `mime_type`;
- `mime_type` начинается с `text/` → `line_count`, `char_count`;
- `mime_type == application/pdf` → `approx_page_count = max(count(b"/Type /Page"), 1)`;
- файла нет на диске → `processing_status = failed`, `scan_details = stored file not found during metadata extraction`, алерт `critical`.

Уровни алертов: `critical` при `processing_status == failed`, иначе `warning` при
`requires_attention`, иначе `info`.

## 2. HTTP-контракт

| Сценарий | Запрос | Факт |
|---|---|---|
| Список файлов | `GET /files` | `200`, массив, сортировка `created_at desc`, без пагинации |
| Список алертов | `GET /alerts` | `200`, массив, сортировка `created_at desc`, без пагинации |
| Загрузка | `POST /files` (multipart: `title`, `file`) | `201`, объект файла в статусе `uploaded`, `scan_status=null` |
| Пустой файл | `POST /files` с файлом 0 байт | `400` `{"detail":"File is empty"}` |
| Карточка файла | `GET /files/{id}` | `200` |
| Несуществующий файл | `GET /files/{id}` | `404` `{"detail":"File not found"}` |
| Переименование | `PATCH /files/{id}` `{"title":"..."}` | `200`, обновлённый объект, `updated_at` меняется |
| Скачивание | `GET /files/{id}/download` | `200`, `Content-Type` из `mime_type`, имя = `original_name` |
| Скачивание при отсутствии файла на диске | `GET /files/{id}/download` | `404` `{"detail":"Stored file not found"}` |
| Удаление файла **без** алертов | `DELETE /files/{id}` | `204` |
| Удаление файла **с** алертом | `DELETE /files/{id}` | **`500`** — дефект A1, см. ниже |

## 3. Наблюдения, зафиксированные как дефекты

Проверены на стенде, воспроизводятся; чиним на этапе 3, каждый — со ссылкой на строку таблицы:

- **A1.** `DELETE /files/{id}` для обработанного файла → `500`.
  В логах: `asyncpg.exceptions.ForeignKeyViolationError: update or delete on table "files"
  violates foreign key constraint "alerts_file_id_fkey" on table "alerts"`.
  Так как алерт создаётся для **любого** файла, удалить можно только необработанный.
- **A8.** При этом же `500` файл **уже удалён с диска**, а строка в БД осталась:
  последующий `GET /files/{id}` → `200`, `GET /files/{id}/download` → `404`. Рассинхрон диска и БД.
- **A2.** `processing_status = processing` виден снаружи, но семантика сломана: он коммитится
  **вместе** с результатом скана, то есть означает не «идёт проверка», а «проверка закончена,
  идёт извлечение метаданных». Первая фаза конвейера снаружи не наблюдаема.
- **A7.** При остановленном Redis `POST /files` возвращает `500`, но файл **создан** в БД и на диске
  и навсегда остаётся в статусе `uploaded` (проверено: количество файлов выросло с 7 до 8).
- **A9.** `mime_type` берётся из заголовка клиента. `sample.pdf`, отправленный с
  `Content-Type: text/plain`, помечается `suspicious` («pdf extension does not match mime type»)
  и **читается как текст** — в метаданных `line_count=12`, `char_count=123` вместо `approx_page_count`.
  Обратный обход тоже работает: `.exe` под видом `text/plain` проходит по mime-проверке
  (ловится только по расширению).
- **A11.** `approx_page_count` считает подстроку `/Type /Page` с пробелом. В PDF, где страницы
  записаны как `/Type/Page` (частый вариант), в файле с двумя страницами получается `1`.
- **A10.** Лимита на размер загрузки нет: файл 11 МБ принимается (`201`), просто помечается
  подозрительным.
- **И1.** `docker compose build frontend` падает: `Dockerfile` копирует `.env.production`,
  которого нет в репозитории.

## 3a. Что в поведении изменилось осознанно

Всё остальное сохранено дословно, включая формулировки `scan_details` и набор ключей
`metadata_json`. Изменилось ровно следующее, и каждое изменение — следствие починки дефекта:

| Что | Было | Стало | Почему |
|---|---|---|---|
| `mime_type` | заголовок `Content-Type` от клиента | тип по сигнатуре в первых байтах, заголовок — подсказка | A9: проверка не может доверять проверяемому. Побочный эффект: `.exe`, который curl отправлял как `application/octet-stream`, теперь определяется как `application/x-msdownload` |
| `approx_page_count` | подстрока `/Type /Page` только с пробелом | оба варианта записи, `/Type /Pages` не считается страницей | A11: на обычном PDF счётчик всегда давал 1 |
| Загрузка больше лимита | принималась любая | `413`, файл не сохраняется | A10 |
| `DELETE` файла с алертом | `500` | `204`, алерты удаляются каскадом | A1 |

## 4. Замер производительности «до»

Стенд: Docker Desktop, backend в одном процессе uvicorn. Команда:
`./scripts/bench_upload.sh 8 20` — 8 параллельных загрузок файла 20 МБ, одновременно
15 последовательных `GET /files`.

| Условие | avg | max |
|---|---|---|
| `GET /files` без нагрузки | 0.006 s | 0.009 s |
| `GET /files` во время 8 параллельных загрузок | 0.178 s | **1.715 s** |

Лёгкий запрос к списку тормозит в тридцать раз, потому что запись файла на диск
(`stored_path.write_bytes`) синхронная и блокирует event loop целиком. Повтор замера
после оптимизации — на этапе 4.

Соединения к Postgres под нагрузкой (`pg_stat_activity`): backend — 5, celery-воркер — **10**
при 16 форках, то есть каждый форк открывает собственное соединение и пул между задачами
фактически не переиспользуется.
