FROM python:3.11-slim as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY pyproject.toml ./poetry.lock* /tmp/
# https://python-poetry.org/docs/cli#export
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim


ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . ./

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt

RUN apt update && apt install -y \
    ffmpeg \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "0", "-k", "uvicorn.workers.UvicornWorker", "doorbell_api:app"]
