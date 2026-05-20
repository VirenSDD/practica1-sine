FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.7.6

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock* ./

# Install production deps only
RUN uv sync --no-dev

# Copy application source
COPY Sistema/ Sistema/

ENV PYTHONPATH=/app/Sistema
ENV RAGMED_CORPUS=/data/diseases.txt

EXPOSE 7860

CMD ["uv", "run", "python", "Sistema/ragmed_web.py"]
