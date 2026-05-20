# RAGMED — Global Task Checklist

Topic: **Disease RAG system** — given symptoms, suggest possible diseases (patient-facing).
Base code: `src/SINE_Pract_2025_2026.py` (Pokémon example, read-only reference).

Mark tasks `[x]` when done. Work **one task at a time**.

---

## Phase 0 — Setup
- [x] **T0.1** [Executor] Create `docs/agents/` and write all four agent context files
- [x] **T0.2** [Executor] Create this `TASKS.md` file

## Phase 1 — Crawler
- [x] **T1.1** [Researcher] Identify Wikipedia disease list URLs and confirm which sections to scrape (symptoms, causes, treatment). Write findings in `docs/research/crawler_sources.md`.
- [x] **T1.2** [Executor] Implement `RAGMED_crawler` in `src/ragmed_crawler.py`
- [x] **T1.3** [Executor] Run crawler with `max_diseases=20`, inspect `diseases.txt`, fix quality issues

## Phase 2 — Information Retrieval
- [x] **T2.1** [Researcher] Compare IR options (BM25, TF-IDF, Jaccard, hybrid). Write findings in `docs/research/ir_comparison.md`.
- [x] **T2.2** [Executor] Implement `RAGMED_rag` in `src/ragmed_rag.py` with hybrid retrieval
- [x] **T2.3** [Executor] Create `src/ragmed_main.py` and test with 3 symptom queries

## Phase 3 — Evaluation
- [ ] **T3.1** [Researcher + PO] Design 10 evaluation questions with ground-truth answers. Save to `Evaluación/preguntas_ground_truth.md`.
- [ ] **T3.2** [Executor] Run 10 questions through the system, capture outputs
- [ ] **T3.3** [PO] Score answers (precisión, cobertura, veracidad). Save results to `Evaluación/evaluacion.md`.

## Phase 4 — Optional (+1 point)
- [ ] **T4.1** [Executor] Test a second Ollama LLM, compare results on the 10 questions
- [ ] **T4.2** [Executor] Test 2 different chunk sizes, compare retrieval quality

## Phase 5 — Report (Memoria)
- [x] **T5.1** [Writer] Draft Section 1: Introducción
- [x] **T5.2** [Writer] Draft Section 2: Módulo Crawler
- [x] **T5.3** [Writer] Draft Section 3: Sistema de Recuperación de Información
- [ ] **T5.4** [Writer] Draft Section 4: Evaluación
- [ ] **T5.5** [Writer] Draft Section 5 (optional): Experimentos adicionales
- [ ] **T5.6** [Writer] Compile IEEE references in `Memoria/referencias.md`
- [ ] **T5.7** [Writer] Final review and export to PDF (≤10 pages)

## Phase 7 — Web UI (optional)
- [x] **T7.1** [Executor] Add `gradio` to pyproject.toml, create `Sistema/ragmed_web.py`
- [ ] **T7.2** [Executor] Test web UI locally with existing corpus
- [x] **T7.3** [Executor] Write `Dockerfile` + `docker-compose.yml` for containerised local run
- [x] **T7.4** [Researcher] Document cloud deployment options in `docs/research/deployment_options.md`
- [x] **T7.5** [Writer] Add `DEPLOYMENT.md` with local + cloud run instructions

## Phase 6 — Packaging
- [x] **T6.1** [Executor] Write `Sistema/README.md`
- [ ] **T6.2** [Executor] Create final `.zip` with `Sistema/`, `Memoria/`, `Evaluación/`

---

## Agent Quick Reference

To invoke an agent in a new conversation, say:
> "Act as the [Agent Name] agent for the RAGMED project. Read your context from `docs/agents/[file].md`."

| Agent | File | Invoke for |
|---|---|---|
| PO Agent | `docs/agents/po_agent.md` | Scope questions, evaluation scoring |
| Researcher Agent | `docs/agents/researcher_agent.md` | T1.1, T2.1, T3.1 |
| Writer Agent | `docs/agents/writer_agent.md` | T5.x |
| Executor Agent | `docs/agents/executor_agent.md` | T1.2, T1.3, T2.2, T2.3, T3.2, T4.x, T6.x |
