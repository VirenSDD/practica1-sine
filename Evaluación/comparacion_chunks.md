# T4.2 — Comparación de tamaños de contexto por fragmento

**Configuración de recuperación:** hybrid, α = 0.5, top-N = 5 (idéntica en los tres casos)  
**Modelo de generación:** `Llama-3.2-1B-Instruct-GGUF` (baseline)  
**Corpus:** diseases.txt  
**Embeddings:** compartidos (caché reutilizada)

El parámetro **max-context-chars** controla cuántos caracteres de cada fragmento recuperado se incluyen en el prompt del LLM. El ranking de recuperación es idéntico en los tres casos (mismos embeddings); lo que varía es la cantidad de texto que el modelo de generación puede leer por fragmento.

| Configuración | max-context-chars | Texto aprox. por fragmento | Respuestas en |
|---------------|:-----------------:|---------------------------|---------------|
| Pequeño | 500 | ~75 palabras | `respuestas_chunks_500.md` |
| Baseline (actual) | 1 500 | ~230 palabras | `respuestas_sistema.md` |
| Grande | 3 000 | ~460 palabras | `respuestas_chunks_3000.md` |

---

## Tabla comparativa de puntuación

| # | Enfermedad | 500 — P/C/V | 500 Total | 1500 — P/C/V | 1500 Total | 3000 — P/C/V | 3000 Total |
|---|------------|:-----------:|:---------:|:------------:|:----------:|:------------:|:----------:|
| Q1 | Common cold | 1/1/1 | 3/3 | 1/1/1 | 3/3 | 1/0,5/1 | 2,5/3 |
| Q2 | Influenza | 0,5/0,5/0,5 | 1,5/3 | 0,5/0,5/0,5 | 1,5/3 | 1/0,5/0,5 | 2/3 |
| Q3 | Asthma | 1/1/0,5 | 2,5/3 | 1/1/1 | 3/3 | 1/1/0,5 | 2,5/3 |
| Q4 | Migraine | 1/1/1 | 3/3 | 1/0,5/0,5 | 2/3 | 1/0,5/1 | 2,5/3 |
| Q5 | Gout | 1/1/1 | 3/3 | 1/0,5/0,5 | 2/3 | 1/0,5/0,5 | 2/3 |
| Q6 | Hypothyroidism | 0/0/0 | 0/3 | 0,5/0/0,5 | 1/3 | 0/0/0 | 0/3 |
| Q7 | Pneumonia | 0,5/0,5/1 | 2/3 | 1/1/1 | 3/3 | 1/1/1 | 3/3 |
| Q8 | Rheumatoid arthritis | 0/0/1 | 1/3 | 0,5/0,5/1 | 2/3 | 0/0/1 | 1/3 |
| Q9 | Malaria | 0,5/0,5/0,5 | 1,5/3 | 0/0/0 | 0/3 | 0/0/0 | 0/3 |
| Q10 | Tuberculosis | 0/0/0 | 0/3 | 0/0/0,5 | 0,5/3 | 0/0/0 | 0/3 |
| **TOTAL** | | **5,5 / 5,5 / 6,5** | **17,5/30** | **6,5/5/6** | **17,5/30** | **6 / 4 / 5,5** | **15,5/30** |

---

## Análisis por pregunta

### Por qué 500 chars ≠ baseline a pesar del mismo total

Los dos primeros tamaños obtienen el mismo total (17,5/30) pero por motivos distintos: ganan y pierden en preguntas diferentes.

**Q4 Migraine: 500 gana (3/3 vs 2/3 baseline)**  
Entre los top-5 recuperados hay tres variantes de Arnold–Chiari malformation. Con 1 500 chars el modelo lee suficiente texto de esos chunks para confundirse y mencionarlos como alternativa, reduciendo V. Con 500 chars sólo llega al encabezado ("Findings are due to brainstem...") que no parece una migraña, y el modelo lo ignora: identifica correctamente la migraña sin ruido.

**Q5 Gout: 500 gana (3/3 vs 2/3 baseline)**  
Con 1 500 chars el 1B alucinó "allopurinol (Zyrtec)". Con 500 chars el texto de tratamiento está truncado antes de llegar a los nombres de fármacos, y la respuesta es factualmente correcta.

**Q7 Pneumonia: 500 pierde (2/3 vs 3/3 baseline)**  
Con 1 500 chars el modelo lee suficiente de Pleurisy y Pneumonia para distinguirlos. Con 500 chars el chunk de Pleurisy (rank 2) sólo muestra la primera frase —"sharp chest pain while breathing"— que coincide perfectamente con los síntomas del paciente, llevando al modelo a presentar pleurisy como el diagnóstico principal en lugar de pneumonia.

**Q8 RA: 500 pierde (1/3 vs 2/3 baseline)**  
El chunk de Rheumatoid arthritis está en el rank 5. Con 500 chars el modelo recibe apenas el Lead ("RA is a long-term autoimmune disorder...") sin detalles de síntomas, y los chunks de JIA (ranks 1-2) dominan con síntomas bien descritos → el modelo diagnóstica JIA en lugar de RA.

### Por qué 3 000 chars es peor

**Q6 Hypothyroidism: 3000 retrocede (0/3 vs 1/3 baseline)**  
El chunk de Hyperkalemia (rank 2) tiene 3 000 chars de descripción detallada de síntomas de niveles altos de potasio. El modelo lee todo ese texto y concluye que el paciente tiene "Hypokalemia", llegando incluso a dar P: 0. Con 1 500 chars el mismo chunk quedaba en un texto más breve que el modelo no priorizaba tanto.

**Q8 RA: 3000 igual de malo que 500 (1/3)**  
Con 3 000 chars de texto de JIA en las posiciones 1 y 2 del ranking, el modelo recibe una descripción exhaustiva de JIA que eclipsa completamente el chunk de RA en posición 5. El resultado es una respuesta que identifica "Osteoarthritis o Juvenile Rheumatoid Arthritis" sin mencionar RA. Con 1 500 chars el modelo alcanza a leer algo de RA y lo incluye como alternativa.

**Q1, Q3, Q5 (3000 ligeramente peor)**  
Con 3 000 chars el modelo genera respuestas más largas y añade alternativas innecesarias (Influenza-like illness, Allergies para el resfriado; COPD como subtype del asma; toothache como causa de dolor en el dedo gordo del pie). Estos añadidos reducen C y V sin aportar valor.

### Conclusión

Más contexto no implica mejores respuestas. El tamaño óptimo depende de la calidad del ranking:

- Cuando el ranking es bueno (Q1, Q3, Q7), más contexto añade ruido.
- Cuando el ranking es mediocre (Q8, Q6), más contexto amplifica el señal erróneo.
- El valor de 1 500 chars (baseline) representa un buen equilibrio: suficiente para leer los síntomas clave sin que los falsos positivos del ranking dominen la respuesta.

La mejora real para Q9 y Q10 requiere resolver el fallo de recuperación, no ajustar el contexto.
