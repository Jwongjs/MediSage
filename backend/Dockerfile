# The full python:3.11 image is ~900MB. The -slim variant strips docs, test
# files and compilers. Nothing here needs a compiler any more: psycopg went
# with the database, so no libpq-dev and no gcc.
FROM python:3.11-slim

WORKDIR /app

# Copy requirements before code so Docker can cache the pip layer separately.
# pip install only re-runs when requirements.txt changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The Human Phenotype Ontology is ~11MB and gitignored, so it is NOT in the
# build context. Fetch it here, or load_hpo() returns an empty index: every
# criterion falls back to a LOCAL: key and criteria stop merging across
# candidates. A local build would silently pass by picking up the developer's
# own copy; a CI build from a fresh clone would not.
RUN mkdir -p /app/data && \
    python -c "import urllib.request; urllib.request.urlretrieve('https://purl.obolibrary.org/obo/hp.obo', '/app/data/hp.obo')" && \
    python -c "import pathlib, sys; p = pathlib.Path('/app/data/hp.obo'); sys.exit(0 if p.stat().st_size > 5_000_000 else 'hp.obo download truncated')"

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
