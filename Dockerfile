FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pillow

ENV PORT=80 \
    DATA_DIR=/data/audo \
    DATABASE_PATH=/data/audo/consultations.sqlite3 \
    CONSULTATION_TO=getaudo@gmail.com \
    PUBLIC_BASE_URL=https://getaudo.com

COPY server.py /app/server.py
COPY services.py /app/services.py
COPY site_catalog.py /app/site_catalog.py
COPY index.html /app/index.html
COPY privacy.html /app/privacy.html
COPY thank-you.html /app/thank-you.html
COPY favicon.ico /app/favicon.ico
COPY robots.txt /app/robots.txt
COPY site.webmanifest /app/site.webmanifest
COPY assets /app/assets

VOLUME ["/data/audo"]

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '80'), timeout=2).read()" || exit 1

CMD ["python", "server.py"]
