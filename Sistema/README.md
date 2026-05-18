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

## Generar el corpus de enfermedades

El crawler descarga artículos de Wikipedia y los estructura en `diseases.txt`. Ejecutar desde `Sistema/`:

```bash
cd Sistema
uv run python -c "
from ragmed_crawler import RAGMED_crawler
c = RAGMED_crawler(max_diseases=50)   # ajustar según necesidad
c.download_disease_list(output_file='disease_list.txt')
c.download_disease_info()
for name in c.disease_list:
    c.clean_disease_page(name)
c.generate_disease_summary(output_file='diseases.txt')
"
```

Para el corpus completo (A–Z), eliminar el argumento `max_diseases`. El proceso tarda varios minutos por el límite de velocidad de la API de Wikipedia.

---

## Ejecutar el sistema

```bash
cd Sistema
uv run python ragmed_main.py
```

El sistema entra en un bucle interactivo. Introduce síntomas separados por comas:

```
Introduce síntomas (o 'stop' para salir): fever, stiff neck, headache
```

El sistema recuperará los fragmentos de `diseases.txt` más relevantes y generará una respuesta con el LLM.

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

## Referencia: código base

El directorio `src/` contiene el sistema RAG de referencia sobre Pokémon (`SINE_Pract_2025_2026.py`), proporcionado por el equipo docente. No se debe modificar.
