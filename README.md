# RAGMED

Práctica de *Sistemas de Información No Estructurada* (SINE) — Curso 2025–2026.

Sistema RAG (Retrieval-Augmented Generation) especializado en enfermedades: dado un conjunto de síntomas, sugiere posibles enfermedades con explicaciones generadas por un LLM local. El corpus proviene de Wikipedia (API REST) y el LLM se sirve localmente mediante [Ollama](https://ollama.com/).

---

## Estructura del proyecto

```
practica-sine/
  src/                        # Código base de referencia (read-only, no modificar)
    SINE_Pract_2025_2026.py   # Sistema RAG de Pokémon proporcionado por el equipo docente
  Sistema/                    # Código del sistema RAGMED (entregable)
    README.md                 # Instrucciones de instalación y ejecución
    _helpers.py               # Utilidades puras compartidas
    ragmed_crawler.py         # Módulo crawler (Wikipedia → corpus)
    ragmed_rag.py             # Módulo de recuperación e información + generación
    ragmed_main.py            # Punto de entrada
  Memoria/                    # Informe académico (entregable)
    memoria.md                # Borrador en Markdown
    referencias.md            # Referencias IEEE
  Evaluación/                 # Evaluación del sistema (entregable)
  docs/
    agents/                   # Contexto de los agentes de desarrollo
    research/                 # Notas de investigación (IR, fuentes de datos)
    homework/                 # Documentación original de la práctica
      enunciado.md
      Enunciado_V.0.4.pdf
      SEIRiP.pdf              # Libro de referencia: Croft, Metzler, Strohman
      diagrama1.png
      diagrama2-flujo_principal_rag.png
  TASKS.md                    # Lista de tareas vivas del proyecto
  pyproject.toml              # Dependencias y configuración de herramientas
```

---

## Quick start

Ver `Sistema/README.md` para instrucciones detalladas de instalación y ejecución.

```bash
uv sync
cd Sistema
uv run python ragmed_main.py
```
