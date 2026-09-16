# Ported from teammate feature-lavanya's branch and adapted for this repo's
# layout: her version only needed `backend/` (raw-SQL migrations ran inside
# the Postgres container itself, see docker-init.sh on her branch). This repo
# uses Alembic instead - migrations live in database/migrations and
# alembic.ini's `script_location`/`prepend_sys_path` are relative to the repo
# root, so this image needs the repo root as build context (see
# docker-compose.yml's `context: .` / `dockerfile: backend/Dockerfile`) and
# copies alembic.ini + database/ alongside backend/app.

FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app backend/app
# AI Assistant feature's reference documents (chunked into the DB by
# seed_assistant_documents.py below) - not under backend/app, so it needs
# its own COPY or the assistant would have nothing to retrieve from.
COPY backend/documents backend/documents
COPY alembic.ini alembic.ini
COPY database database

EXPOSE 8000

# Runs once per container start: apply migrations, seed demo lease data,
# seed AI Assistant reference documents (all three idempotent - see
# database/seed/*.py's per-record _ensure/skip-if-exists checks and
# Alembic's own version tracking), then serve. Migrations/seeding run from
# /app (where alembic.ini and database/ live); the app runs from
# /app/backend (where the `app` package lives).
CMD ["sh", "-c", "alembic upgrade head && python database/seed/seed_lease_story.py && python database/seed/seed_assistant_documents.py && cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
