# The full python:3.11 image is ~900MB. The -slim variant strips documentation, test files, and compilers — 
# it's ~50MB and enough for running Python apps. 
# We add back only the two system libs we actually need (libpq-dev for Postgres, gcc to compile it).
FROM python:3.11-slim

WORKDIR /app

# libpq-dev + gcc are needed to compile psycopg (the async Postgres driver).
# --no-install-recommends keeps the layer lean; cleanup removes the apt cache.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements before code so Docker can cache the pip layer separately.
# pip install only re-runs when requirements.txt changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# workers=1 is REQUIRED, not a tuning choice. Session state lives in an
# in-process MemorySaver (no database, by design), so a second worker would
# not see sessions started by the first and roughly half of all
# answers/finalize/export calls would 404. Scale by adding container
# instances only if the load balancer has session affinity.
# Shell form (not exec/JSON) so $PORT expands. Railway injects $PORT at runtime;
# falls back to 8000 for local `docker run`.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1