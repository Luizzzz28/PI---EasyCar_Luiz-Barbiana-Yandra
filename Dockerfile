FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências primeiro: aproveita o cache de camadas do Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Arquivos estáticos do admin/Swagger, servidos pelo WhiteNoise
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Não roda como root
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -"]
