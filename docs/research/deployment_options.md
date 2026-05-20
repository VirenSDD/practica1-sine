# RAGMED — Cloud Deployment Options

The core challenge: the RAG pipeline requires **Ollama** (embedding + LLM), which needs
to run on a server that can serve the models. This means two components must be reachable:
the Gradio web app and an Ollama endpoint.

---

## Option A — Hugging Face Spaces (Gradio native)

| | |
|---|---|
| **Cost** | Free CPU tier (slow inference), GPU from ~$0.05/hr |
| **Ollama** | Run separately on a VPS; point `OLLAMA_HOST` env var at it |
| **Deploy command** | `gradio deploy` (from `Sistema/`) |
| **Verdict** | Easiest path for a demo; free tier may timeout on cold embedding |

Steps:
1. Set up a $5–6/mo VPS (DigitalOcean, Hetzner) with Ollama + models
2. Expose port 11434 (or proxy via nginx with basic auth)
3. In HF Space secrets: `OLLAMA_HOST=http://<vps-ip>:11434`
4. `gradio deploy` — done

---

## Option B — fly.io

| | |
|---|---|
| **Cost** | ~$5–10/mo for 1 GB RAM machine (free tier available) |
| **Ollama** | Run as a second fly.io Machine in the same app, or on a VPS |
| **Deploy command** | `fly launch` → `fly deploy` |
| **Verdict** | Good if you want everything in one cloud; Ollama Machine needs ~2 GB RAM |

fly.io supports GPU Machines (beta, pricier) if faster inference is needed.

---

## Option C — Self-hosted VPS (Docker Compose)

| | |
|---|---|
| **Cost** | ~$6/mo (Hetzner CX22, 2 vCPU, 4 GB RAM) |
| **Ollama** | Runs in the same `docker-compose.yml` as the web app |
| **Deploy command** | `git pull && docker compose up -d` |
| **Verdict** | Best value; identical to local Docker setup; full control |

Use a reverse proxy (Caddy or nginx) with HTTPS for public access.

---

## Summary

| Option | Effort | Cost/mo | Ollama location | Best for |
|--------|--------|---------|-----------------|----------|
| HF Spaces | Low | Free–$3 | Separate VPS | Quick demo |
| fly.io | Medium | $5–10 | fly Machine or VPS | All-in-one cloud |
| Self-hosted VPS | Low | $6 | Same server | Full control, cheapest |

**Recommended:** HF Spaces + Hetzner VPS ($0 + $6 = $6/mo) for a production-quality demo
with minimal ops overhead.
