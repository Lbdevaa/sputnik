"""Извлечение метаданных файла.

Метаданные считаются накопителями, которым скармливают файл по кускам, а не функциями над
целиком прочитанным содержимым. Причина та же, что и у потоковой записи: раньше задача
делала ``read_text()`` или ``read_bytes()`` и держала в памяти весь файл — второй раз после
загрузки (В2).

Накопители — чистая логика: ни файловой системы, ни базы. В тестах в них подаётся список
байтовых кусков, в том числе с разрезами в неудобных местах.
"""

import codecs
import re
from typing import Any, Protocol

from src.domain.media_type import TEXT_MEDIA_TYPE

# Страницы в PDF записывают и как «/Type /Page», и как «/Type/Page». Исходный код искал
# только первый вариант, поэтому на обычном документе счётчик всегда давал 1 (A11).
# Отрицательный просмотр вперёд отсекает «/Type /Pages» — это узел дерева страниц,
# а не страница.
PDF_PAGE_PATTERN = re.compile(rb"/Type\s{0,8}/Page(?![a-zA-Z])")
# Разрез чанка не должен разрывать искомую подстроку: хвост предыдущего куска
# приклеивается к следующему.
_PDF_OVERLAP = 32


class MetadataCollector(Protocol):
    def feed(self, chunk: bytes) -> None: ...

    def result(self) -> dict[str, Any]: ...


class NullCollector:
    """Для типов, о которых нечего сказать, кроме размера и расширения."""

    def feed(self, chunk: bytes) -> None:
        return None

    def result(self) -> dict[str, Any]:
        return {}


class TextCollector:
    """Число строк и символов.

    Декодирование инкрементальное: многобайтовый символ, разрезанный границей чанка,
    не должен ни ломаться, ни считаться дважды.
    """

    def __init__(self) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="ignore")
        self._chars = 0
        self._line_breaks = 0
        self._last_char = ""

    def feed(self, chunk: bytes) -> None:
        text = self._decoder.decode(chunk)
        if not text:
            return
        self._chars += len(text)
        for char in text:
            if char == "\n":
                self._line_breaks += 1
            elif self._last_char == "\r":
                # Одиночный \r — тоже перевод строки (так же считает str.splitlines).
                self._line_breaks += 1
            self._last_char = char

    def result(self) -> dict[str, Any]:
        tail = self._decoder.decode(b"", final=True)
        if tail:
            self._chars += len(tail)
            for char in tail:
                if char == "\n":
                    self._line_breaks += 1
                elif self._last_char == "\r":
                    self._line_breaks += 1
                self._last_char = char
        if self._last_char == "\r":
            self._line_breaks += 1

        lines = self._line_breaks
        if self._chars and self._last_char not in {"\n", "\r"}:
            lines += 1
        return {"line_count": lines, "char_count": self._chars}


class PdfCollector:
    """Приблизительное число страниц.

    Две ловушки потокового поиска, обе решаются позициями в абсолютных координатах файла:
    совпадение, разрезанное границей чанка, нужно найти, а найденное дважды (в хвосте и в
    следующем буфере) — не посчитать второй раз. Плюс совпадение, упирающееся в конец
    буфера, откладывается: следующий байт может оказаться «s» из «/Type /Pages».
    """

    def __init__(self) -> None:
        self._pages = 0
        self._tail = b""
        self._tail_start = 0  # позиция начала хвоста в файле
        self._counted_until = 0  # всё, что кончается до этой позиции, уже посчитано

    def _scan(self, buffer: bytes, final: bool) -> None:
        limit = len(buffer) if final else len(buffer) - 1
        for match in PDF_PAGE_PATTERN.finditer(buffer):
            end = self._tail_start + match.end()
            if match.end() > limit or end <= self._counted_until:
                continue
            self._pages += 1
            self._counted_until = end

    def feed(self, chunk: bytes) -> None:
        buffer = self._tail + chunk
        self._scan(buffer, final=False)
        tail = buffer[-_PDF_OVERLAP:]
        self._tail_start += len(buffer) - len(tail)
        self._tail = tail

    def result(self) -> dict[str, Any]:
        self._scan(self._tail, final=True)
        return {"approx_page_count": max(self._pages, 1)}


def collector_for(media_type: str) -> MetadataCollector:
    if media_type.startswith("text/") or media_type == TEXT_MEDIA_TYPE:
        return TextCollector()
    if media_type == "application/pdf":
        return PdfCollector()
    return NullCollector()


def base_metadata(extension: str, size: int, media_type: str) -> dict[str, Any]:
    return {"extension": extension, "size_bytes": size, "mime_type": media_type}
