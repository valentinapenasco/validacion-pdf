FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY logging.json ./
COPY app ./app

RUN pip install --no-cache-dir uv==0.11.15 \
    && uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# --no-access-log: el acceso lo registra la app con el correlation_id.
# Forma exec: uvicorn es el PID 1 y recibe el SIGTERM de docker stop. Con
# --timeout-graceful-shutdown deja de aceptar conexiones y espera hasta 30 s a que
# terminen las requests en curso antes de salir (contrato 1.2.0, 12-Factor IX).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--timeout-graceful-shutdown", "30"]
