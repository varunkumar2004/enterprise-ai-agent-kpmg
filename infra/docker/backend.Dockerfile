# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --create-home --shell /usr/sbin/nologin assistant

WORKDIR /service

COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

USER assistant

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
