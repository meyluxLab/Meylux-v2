FROM python:3.12.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .python-version ./
COPY src ./src

RUN pip install --no-cache-dir --no-compile --disable-pip-version-check .

USER 65532:65532

ENTRYPOINT ["python", "-m", "meylux.runtime.service"]
