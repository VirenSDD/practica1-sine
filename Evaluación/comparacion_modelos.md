# T4.1 — Comparación de modelos de generación

**Configuración de recuperación:** hybrid, α = 0.5, top-N = 5 (idéntica en ambos casos)  
**Corpus:** diseases.txt  
**Embeddings:** compartidos (caché reutilizada)

| Parámetro | Modelo 1 (baseline) | Modelo 2 |
|-----------|---------------------|----------|
| Nombre | `Llama-3.2-1B-Instruct-GGUF` | `llama3.2:3b` |
| Parámetros | 1,24 B | 3 B |
| Tamaño en disco | 807 MB | 2,0 GB |
| Respuestas en | `respuestas_sistema.md` | `respuestas_llama3b.md` |

---

## Tabla comparativa de puntuación

| # | Enfermedad | 1B — P/C/V | 1B Total | 3B — P/C/V | 3B Total |
|---|------------|:----------:|:--------:|:----------:|:--------:|
| Q1 | Common cold | 1/1/1 | 3/3 | 1/1/1 | 3/3 |
| Q2 | Influenza | 0,5/0,5/0,5 | 1,5/3 | 0,5/0,5/0,5 | 1,5/3 |
| Q3 | Asthma | 1/1/1 | 3/3 | 1/1/1 | 3/3 |
| Q4 | Migraine | 1/0,5/0,5 | 2/3 | 1/1/0,5 | 2,5/3 |
| Q5 | Gout | 1/0,5/0,5 | 2/3 | 1/1/1 | 3/3 |
| Q6 | Hypothyroidism | 0,5/0/0,5 | 1/3 | 1/1/0,5 | 2,5/3 |
| Q7 | Pneumonia | 1/1/1 | 3/3 | 1/1/1 | 3/3 |
| Q8 | Rheumatoid arthritis | 0,5/0,5/1 | 2/3 | 1/0,5/1 | 2,5/3 |
| Q9 | Malaria | 0/0/0 | 0/3 | 0/0/0,5 | 0,5/3 |
| Q10 | Tuberculosis | 0/0/0,5 | 0,5/3 | 0/0/0,5 | 0,5/3 |
| **TOTAL** | | **6,5 / 5 / 6** | **17,5/30** | **7,5 / 7 / 7,5** | **22/30** |

*P = Precisión, C = Cobertura, V = Veracidad*

---

## Análisis por pregunta

### Mejoras del modelo 3B sobre el 1B

**Q5 Gout (1B: 2/3 → 3B: 3/3)**  
El modelo 1B generó la alucinación "allopurinol (Zyrtec)", confundiendo dos fármacos completamente distintos. El modelo 3B no comete este error: identifica el gout correctamente, menciona el metatarsophalangeal joint, y sugiere alternativas razonables (bursitis, bunion) sin halucinar nombres de medicamentos.

**Q6 Hypothyroidism (1B: 1/3 → 3B: 2,5/3)**  
Este es el caso más revelador. El sistema de recuperación falla en ambos casos (los chunks recuperados hablan de proctitis, hyperkalemia, HFMD, etc.) porque los síntomas de hipotiroidismo ("tired", "cold", "weight gain") son demasiado genéricos. Sin embargo, el modelo 3B identifica correctamente hipotiroidismo como primera hipótesis apoyándose en conocimiento paramétrico propio, mientras que el 1B no llega a nombrarlo. Esto demuestra que un modelo más grande compensa mejor los fallos de recuperación.

**Q4 Migraine (1B: 2/3 → 3B: 2,5/3)**  
Ambos modelos reciben chunks de Arnold–Chiari malformation entre los top-5. El 1B se confunde más con este ruido, reduciendo cobertura y veracidad. El 3B menciona Arnold–Chiari como alternativa pero mantiene migraine como diagnóstico principal y cubre correctamente todos los síntomas clave.

**Q8 Rheumatoid arthritis (1B: 2/3 → 3B: 2,5/3)**  
El 3B ofrece la respuesta más concisa y correcta del experimento completo: *"I can't provide a diagnosis, but based on your symptoms, it's possible that you may have rheumatoid arthritis (RA)."* Identifica RA directamente a pesar de que el chunk de RA está en la posición 5 del ranking y los cuatro primeros hablan de JIA y OA. El 1B diluye más la respuesta con múltiples alternativas.

### Fallos persistentes (ambos modelos)

**Q9 Malaria (ambos ≤ 0,5/3)**  
El chunk de Malaria no está entre los 5 recuperados. El mejor resultado es Chikungunya (0,786). El 1B rechaza responder con una negativa de seguridad; el 3B responde con Chikungunya de forma convincente, lo que le da V: 0,5 pero no resuelve el fallo de recuperación. La solución requeriría mejorar la indexación o añadir metadatos geográficos.

**Q10 Tuberculosis (ambos = 0,5/3)**  
El corpus no recupera el artículo de tuberculosis entre los top-5. Los chunks recuperados incluyen "Bipolar I disorder" y "Carbamoyl phosphate synthetase I deficiency". El 3B genera una lista donde aparece Pertussis y Pneumonia junto a Bipolar disorder, ninguno correcto. Ambos modelos reciben V: 0,5 por no alucinar en exceso pero sin dar la respuesta correcta.

### Conclusión

El modelo 3B mejora **+4,5 puntos** (del 58,3% al 73,3%). Las ganancias se concentran en preguntas donde la recuperación es mediocre pero el diagnóstico es reconocible por conocimiento general médico (Gout, Hypothyroidism, Migraine, RA). Los fallos de recuperación severos (Q9, Q10) persisten en ambos modelos, confirmando que el cuello de botella es el indexado, no la capacidad generativa.
