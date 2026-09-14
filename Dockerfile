# AutoTest Orchestrator - runs the FastAPI backend + web dashboard.
# One-command demo: `docker compose up` (see docker-compose.yml), or build
# and run this image directly - see the "Run with Docker" section in README.md.

FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so this layer is cached across rebuilds that
# only change application code, not requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project.
COPY . .

# results/ holds run history and the latest-run JSON files - created here so
# it exists even before the first test run. Left writable by the container's
# default root user deliberately: docker-compose.yml bind-mounts this
# directory to the host so results persist across rebuilds, and a non-root
# user here would risk permission mismatches against the host-owned
# directory on some setups. This container isn't exposed to the internet -
# it's a local dev/demo tool - so that trade-off is fine.
RUN mkdir -p results

EXPOSE 8000

# Basic liveness check - fails the container health status if the API stops
# responding (useful with `docker compose up` / orchestrators alike).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/summary', timeout=2)" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
