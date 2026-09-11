FROM python:3.14-slim

# UV_NO_DEV=1 при сборке — образ без dev-зависимостей (pytest и т.п.).
ARG UV_NO_DEV=0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=${UV_NO_DEV} \
    UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /backend

COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv sync --locked

# Миграции и alembic.ini — часть образа, а не только bind-mount'а (И2):
# иначе `alembic upgrade head` в чистом контейнере не находит конфигурацию.
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
