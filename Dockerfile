FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml mise.toml uv.lock ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir gunicorn \
    && pip install --no-cache-dir 'django>=5.2,<5.3' 'django-ninja>=1.5,<2' 'psycopg[binary]>=3.3,<4' 'faker>=30'

COPY . .

EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "info"]
