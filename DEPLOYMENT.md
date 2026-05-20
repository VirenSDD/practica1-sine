# RAGMED — Deployment Guide

## Prerequisites

- [Ollama](https://ollama.com/) installed and running
- Models pulled:
  ```bash
  ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
  ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF
  ```
- A generated corpus file (`diseases.txt`)

---

## Option 1 — Local (no Docker)

```bash
# Install deps (including Gradio)
uv sync

# Launch the web UI (defaults to diseases.txt in the current directory)
uv run python Sistema/ragmed_web.py
```

Open [http://localhost:7860](http://localhost:7860).

To point at a different corpus file, set the env var:

```bash
RAGMED_CORPUS=/path/to/diseases.txt uv run python Sistema/ragmed_web.py
```

---

## Option 2 — Docker Compose (local, containerised)

```bash
# Pull required Ollama models into the container on first run
docker compose run --rm ollama ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
docker compose run --rm ollama ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

# Start both services (Ollama + web UI)
docker compose up --build
```

Open [http://localhost:7860](http://localhost:7860).

The `diseases.txt` file in the project root is bind-mounted read-only into the container.
Ollama model weights are persisted in the `ollama_data` Docker volume.

---

## Option 3 — Cloud (Hugging Face Spaces)

Requires a separate machine running Ollama (VPS, home server, etc.) with the models loaded.

1. Expose Ollama publicly (e.g. via nginx reverse proxy or `ollama serve --bind 0.0.0.0:11434`)
2. Set the `OLLAMA_HOST` secret in your HF Space settings
3. From the `Sistema/` directory, run:
   ```bash
   gradio deploy
   ```
   Gradio CLI will prompt for your HF token and create the Space automatically.

See `docs/research/deployment_options.md` for a full comparison of cloud options.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGMED_CORPUS` | `diseases.txt` | Path to the corpus file |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
