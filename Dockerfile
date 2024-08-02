FROM python:3.12-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.2.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    PATH="$PATH:/root/.local/bin"

WORKDIR /usr/local/src/async-fastapi-s3

RUN apt-get update && apt-get install -y curl make

RUN curl -sSL https://install.python-poetry.org | python3 -
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY s3_api/main.py .
COPY . .

CMD ["poetry", "run", "python3", "main.py"]