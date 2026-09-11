"""Правило зависимостей из docs/architecture.md, проверенное кодом.

``domain/`` не знает ни про веб-фреймворк, ни про ORM, ни про брокер, ни про диск.
Если этот тест покраснел — граница слоёв нарушена, и тесты домена перестали быть
«за секунды и без докера».
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
DOMAIN = SRC / "domain"

FORBIDDEN_IN_DOMAIN = ("fastapi", "starlette", "sqlalchemy", "celery", "aiofiles", "src.")
FORBIDDEN_OUTSIDE_API = ("fastapi", "starlette")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("module", sorted(DOMAIN.glob("*.py")), ids=lambda p: p.name)
def test_domain_imports_only_stdlib_and_itself(module: Path):
    for name in imported_modules(module):
        if name.startswith("src.domain"):
            continue
        assert not name.startswith(FORBIDDEN_IN_DOMAIN), f"{module.name} imports {name}"


@pytest.mark.parametrize(
    "module",
    sorted(p for p in SRC.rglob("*.py") if "api" not in p.parts and p.name != "main.py"),
    ids=lambda p: str(p.relative_to(SRC)),
)
def test_http_framework_lives_only_in_api(module: Path):
    for name in imported_modules(module):
        assert not name.startswith(FORBIDDEN_OUTSIDE_API), (
            f"{module.relative_to(SRC)} imports {name}"
        )
