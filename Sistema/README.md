# RAGMED — Sistema de Recuperación y Generación Aumentada para Diagnóstico de Enfermedades

Sistema RAG que, dado un conjunto de síntomas, sugiere posibles enfermedades usando Wikipedia como corpus y un LLM local servido mediante Ollama.

---

## Requisitos

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (gestor de paquetes)
- **[Ollama](https://ollama.com/)** instalado y en ejecución

---

## Instalación

### 1. Instalar dependencias Python

Desde la raíz del repositorio:

```bash
uv sync
```

O con pip estándar:

```bash
pip install ollama requests beautifulsoup4 rank-bm25 lxml
```

### 2. Descargar modelos de Ollama

```bash
ollama pull hf.co/CompendiumLabs/bge-base-en-v1.5-gguf
ollama pull hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF
```

Asegúrate de que el servicio Ollama está activo antes de ejecutar el sistema (`ollama serve` si no arranca automáticamente).

---

## Ejecutar el sistema

Desde la raíz del repositorio (el `pyproject.toml` está ahí):

```bash
# Corpus completo A–Z (tarda varios minutos por el límite de velocidad de Wikipedia):
uv run python Sistema/ragmed_main.py

# Muestra aleatoria de 50 enfermedades de todo el alfabeto:
uv run python Sistema/ragmed_main.py --max-diseases 50 --shuffle

# Prueba rápida — 20 enfermedades aleatorias, solo letras A y B:
uv run python Sistema/ragmed_main.py --max-diseases 20 --letters A B --shuffle

# Saltar la descarga si el corpus ya existe:
uv run python Sistema/ragmed_main.py --skip-crawler
```

### Opciones de línea de comandos

| Flag | Por defecto | Descripción |
|---|---|---|
| `--max-diseases N` | todas | Limita el número de enfermedades a descargar |
| `--letters A B …` | A–Z | Restringe la descarga a esas letras del índice |
| `--shuffle` | desactivado | Aleatoriza la lista antes de aplicar `--max-diseases` |
| `--corpus-file PATH` | `diseases.txt` | Ruta del corpus consolidado de salida |
| `--list-file PATH` | `disease_list.txt` | Ruta de la lista de nombres de enfermedades |
| `--skip-crawler` | desactivado | Omite la descarga y usa el corpus existente |

En Phase 1, el programa ejecuta el crawler y termina. En Phase 2 añadirá el bucle interactivo del chatbot.

---

## Estructura de ficheros

```
Sistema/
  _helpers.py          # Utilidades compartidas (parse_sections, find_section, safe_filename)
  ragmed_crawler.py    # Módulo de adquisición de datos (Wikipedia)
  ragmed_rag.py        # Módulo de recuperación + generación (BM25 híbrido + Ollama)
  ragmed_main.py       # Punto de entrada principal
  diseases/            # Ficheros intermedios por enfermedad (generado en ejecución)
  disease_list.txt     # Lista de nombres de enfermedades (generado en ejecución)
  diseases.txt         # Corpus consolidado (generado en ejecución)
```

Los ficheros `diseases/`, `disease_list.txt` y `diseases.txt` están en `.gitignore` porque se regeneran con el crawler.

---

## Ejecutar los tests

El proyecto incluye una suite de tests unitarios que no requieren red ni Ollama. Se ejecutan desde la raíz del repositorio:

```bash
uv run pytest
# Con salida detallada:
uv run pytest -v
```

Los tests cubren:
- `_helpers.py`: `safe_filename`, `parse_sections`, `find_section`
- `ragmed_crawler.py`: pipeline completo con un `InMemoryDiseaseSource` (sin peticiones HTTP)

---

## Referencia: código base

El directorio `src/` contiene el sistema RAG de referencia sobre Pokémon (`SINE_Pract_2025_2026.py`), proporcionado por el equipo docente. No se debe modificar.
