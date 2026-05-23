# RAGMED — Resultados de la Evaluación

**Sistema evaluado:** RAGMED con función de recuperación híbrida (BM25 + coseno, α = 0.5)  
**Corpus:** diseases.txt (Wikipedia, ~5 390 enfermedades)  
**Modelo de generación:** `hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF`  
**Modelo de embedding:** `hf.co/CompendiumLabs/bge-base-en-v1.5-gguf`

---

## Rúbrica de puntuación

Cada pregunta se puntúa en tres métricas, de 0 a 1 con incrementos de 0,5:

| Métrica | 0 | 0,5 | 1 |
|---------|---|-----|---|
| **Precisión** | Respuesta incorrecta o irrelevante | Identifica la enfermedad pero con errores parciales | Identifica correctamente la enfermedad y sus síntomas clave |
| **Cobertura** | No cubre los síntomas mencionados en la pregunta | Cubre algunos síntomas relevantes | Cubre todos los síntomas clave del corpus para esa enfermedad |
| **Veracidad** | Contiene afirmaciones claramente falsas (alucinaciones) | Alguna información dudosa o imprecisa | Sin información inventada; todo coincide con el corpus |

**Puntuación máxima:** 10 preguntas × 3 métricas × 1 punto = **30 puntos**

---

## Tabla de resultados

| # | Enfermedad | Precisión | Cobertura | Veracidad | Total (3) |
|---|------------|:---------:|:---------:|:---------:|:---------:|
| Q1 | Common cold | 1 | 1 | 1 | **3/3** |
| Q2 | Influenza | 0,5 | 0,5 | 0,5 | **1,5/3** |
| Q3 | Asthma | 1 | 1 | 1 | **3/3** |
| Q4 | Migraine | 1 | 0,5 | 0,5 | **2/3** |
| Q5 | Gout | 1 | 0,5 | 0,5 | **2/3** |
| Q6 | Hypothyroidism | 0,5 | 0 | 0,5 | **1/3** |
| Q7 | Pneumonia | 1 | 1 | 1 | **3/3** |
| Q8 | Rheumatoid arthritis | 0,5 | 0,5 | 1 | **2/3** |
| Q9 | Malaria | 0 | 0 | 0 | **0/3** |
| Q10 | Tuberculosis | 0 | 0 | 0,5 | **0,5/3** |
| **TOTAL** | | **6,5/10** | **5/10** | **6/10** | **17,5/30** |
| **%** | | **65 %** | **50 %** | **60 %** | **58,3 %** |

---

## Análisis por pregunta

### Q1 — Common cold ✅ (3/3)
**Recuperación:** Nasopharyngitis y Common cold en posiciones 1 y 2 (0,88 y 0,87). Excelente.  
**Respuesta:** Identifica correctamente el resfriado común como diagnóstico principal. Menciona runny nose, sneezing, sore throat y cough. Añade consejos de autocuidado razonables.  
**Observaciones:** Caso óptimo — la consulta usa vocabulario idéntico al del corpus. El modo híbrido sitúa los fragmentos correctos en el top-2.

### Q2 — Influenza ⚠️ (1,5/3)
**Recuperación:** Influenza aparece solo en posición 4 (0,74). Las posiciones 1–3 son Ornithosis, Meningococcemia y Meningitis meningocócica.  
**Respuesta:** Identifica influenza como primera posibilidad pero la coloca junto a Bronchiolitis Obliterans y Viral Pneumonia sin justificación clara desde el contexto.  
**Observaciones:** Fallo de recuperación parcial. Los síntomas "body aches, high fever, chills, dry cough" coinciden bien con el fragmento de gripe pero el BM25 sobrepondera términos compartidos con meningitis (fever, chills). La precisión se ve afectada por la contaminación del contexto recuperado.

### Q3 — Asthma ✅ (3/3)
**Recuperación:** Asthma Signs and symptoms en posición 1 (0,90). Excelente — la mayor puntuación de toda la evaluación.  
**Respuesta:** Identifica asma directamente, menciona wheezing, shortness of breath, chest tightness y el patrón nocturno/de ejercicio. Respuesta concisa y correctamente fundamentada en el corpus.  
**Observaciones:** Los síntomas de asma son suficientemente únicos para que tanto BM25 como el componente semántico coincidan. Resultado más sólido de toda la evaluación.

### Q4 — Migraine ⚠️ (2/3)
**Recuperación:** Basilar artery migraines (0,82) y Migraine (0,82) en posiciones 1 y 5. Sin embargo, Arnold-Chiari malformation ocupa las posiciones 2 y 3 por similitud de síntomas (cefalea, nauseas).  
**Respuesta:** Identifica migraine correctamente como primera opción pero añade sinus infection, tension headache, cluster headache y hemicrania sin apoyo suficiente en el contexto recuperado.  
**Observaciones:** La cobertura es parcial porque la respuesta queda diluida por alternativas no relevantes. La veracidad se ve afectada por "Hemicrania (Hemicranial Pain Syndrome)" que es una reformulación imprecisa.

### Q5 — Gout ⚠️ (2/3)
**Recuperación:** Gout Signs and symptoms en posición 4 (0,71). Las posiciones 1–3 son Ainhum, Hereditary hyperuricemia y Hallux valgus, ninguna de las cuales es gota.  
**Respuesta:** Identifica gout correctamente y menciona cristales de ácido úrico, NSAIDs y colchicina. Sin embargo, incluye "allopurinol (Zyrtec)" — error factual (Zyrtec es cetirizina, no alopurinol).  
**Observaciones:** Hallucination puntual en el nombre comercial. Los síntomas de la consulta (big toe, sudden, swelling, redness) no bastan para posicionar gout en el top-3; el BM25 favorece otros trastornos del pie.

### Q6 — Hypothyroidism ❌ (1/3)
**Recuperación:** Ninguno de los cinco fragmentos recuperados contiene hypothyroidism. Los resultados son Proctitis, Hyperkalemia, Hand-foot-mouth disease, Vasovagal syncope y Sjögren's syndrome.  
**Respuesta:** El modelo menciona hypothyroidism como primera causa, pero NO a partir del contexto recuperado — utiliza conocimiento propio del modelo (hallucination en el sentido RAG: respuesta no fundamentada en el corpus).  
**Observaciones:** Fallo de recuperación grave. La consulta usa lenguaje coloquial ("feeling cold all the time") que no se alinea con la terminología del corpus ("poor ability to tolerate cold", "cold intolerance"). El componente semántico del embedding debería haber bridgeado esta brecha léxica, pero no lo hizo. La puntuación de cobertura es 0 porque la respuesta no está anclada en ningún fragmento recuperado.

### Q7 — Pneumonia ✅ (3/3)
**Recuperación:** Pneumonia Signs and symptoms en posición 1 (0,85). Pleurisy/Pleuritis en posiciones 2 y 4 (relevantes por el dolor torácico pleurítico). Excelente.  
**Respuesta:** Identifica pneumonia directamente y enumera todos los síntomas clave: fiebre, dolor torácico pleurítico, tos productiva, dificultad respiratoria. Las alternativas mencionadas (bronchitis, sinusitis) son menores y no distorsionan el diagnóstico principal.  
**Observaciones:** Caso óptimo. Los síntomas de la consulta (especialmente "sharp chest pain that worsens when I breathe deeply") son muy específicos y sitúan el fragmento correcto en primer lugar.

### Q8 — Rheumatoid arthritis ⚠️ (2/3)
**Recuperación:** Arthritis juvenile y Juvenile rheumatoid arthritis en posiciones 1 y 2 (0,85). Rheumatoid arthritis solo en posición 5 (0,79). La consulta mencionaba simetría y rigidez >1 h, pero el sistema no priorizó el artículo de RA adulta.  
**Respuesta:** Presenta Osteoarthritis como primera posibilidad y Rheumatoid Arthritis como segunda, cuando los signos descritos (rigidez matutina >1 h, afectación simétrica) son diagnósticos casi patognomónicos de RA.  
**Observaciones:** La rigidez matutina prolongada y la simetría son marcadores clave de RA frente a OA (que tiene rigidez <30 min y no simétrica), pero el modelo los trata de forma equivalente. La veracidad es completa — no hay información falsa.

### Q9 — Malaria ❌ (0/3)
**Recuperación:** Ninguno de los cinco fragmentos contiene malaria. Los resultados son Chikungunya, Spastic angina, Hyperthermia y Mucopolysaccharidosis (dos variantes).  
**Respuesta:** El modelo se niega a responder con "I can't provide information about diseases" — comportamiento inesperado dado el system prompt configurado.  
**Observaciones:** Doble fallo: (1) la recuperación no encuentra el artículo de malaria aunque existe en el corpus (línea 84 681); probablemente porque la consulta no contiene el término "malaria" y los síntomas cíclicos/palúdicos no superan la puntuación de Chikungunya; (2) el modelo interpreta la consulta post-viaje como potencialmente sensible y se niega a responder.

### Q10 — Tuberculosis ❌ (0,5/3)
**Recuperación:** Ninguno de los cinco fragmentos contiene tuberculosis. Los resultados son Carbamoyl phosphate synthetase I deficiency, Bacterial pneumonia, Pertussis, Bipolar I disorder y Carnitine palmitoyltransferase I deficiency — completamente irrelevantes.  
**Respuesta:** El modelo no identifica tuberculosis y propone acute bronchitis, viral pneumonia y postnasal drip como causas de hemoptisis. Las alternativas propuestas son incorrectas o inadecuadas para el perfil sintomático presentado (semanas de tos + hemoptisis + sudores nocturnos + pérdida de peso).  
**Observaciones:** Fallo de recuperación grave. El artículo de Tuberculosis existe en el corpus (línea 139 632), pero los síntomas descritos ("persistent cough", "coughing up blood", "night sweats", "weight loss") son comunes a muchas enfermedades respiratorias y los fragmentos más ruidosos los superaron en score. La veracidad parcial se asigna porque algunas afirmaciones del modelo son válidas genéricamente aunque no correctas para el diagnóstico de TB.

---

## Conclusiones

**Puntuación final: 17,5/30 (58,3 %)**

| Grupo | Preguntas | Puntuación media |
|-------|-----------|-----------------|
| Excelente (3/3) | Q1, Q3, Q7 | 3,0/3 |
| Bueno (2–2,5/3) | Q2, Q4, Q5, Q8 | 1,9/3 |
| Fallido (<1/3) | Q6, Q9, Q10 | 0,5/3 |

**Patrón de éxito.** El sistema funciona óptimamente cuando los síntomas de la consulta usan vocabulario idéntico o muy cercano al del corpus (common cold, asthma, pneumonia). La función híbrida sitúa el fragmento correcto en la posición 1 con scores superiores a 0,85.

**Patrón de fallo de recuperación.** Tres preguntas obtuvieron puntuación nula o muy baja (hypothyroidism, malaria, tuberculosis) porque el artículo correcto no aparece entre los cinco primeros resultados. Las causas identificadas son:
- **Brecha léxica** (hypothyroidism): la consulta usa lenguaje coloquial ("feeling cold all the time") que no alinea bien con la terminología clínica del corpus ("poor ability to tolerate cold").
- **Síntomas compartidos** (malaria, tuberculosis): fiebre + escalofríos y tos + hemoptisis son síntomas presentes en muchas enfermedades; sin el nombre de la enfermedad en la consulta, el BM25 y el embedding no discriminan suficientemente.

**Alucinación puntual.** Q5 contiene el error factual "allopurinol (Zyrtec)" — el modelo confunde el nombre comercial. Indica que el modelo de generación (Llama-3.2-1B) puede mezclar información de entrenamiento con el contexto recuperado en detalles específicos.

**Comportamiento de seguridad inesperado.** En Q9 el modelo rechazó responder ("I can't provide information about diseases") a pesar del system prompt médico configurado. Este comportamiento reduce la utilidad del sistema para enfermedades tropicales.

**Recomendaciones de mejora:**
1. Aumentar `top_n` de 5 a 10 para reducir fallos de recuperación en enfermedades con síntomas genéricos.
2. Aplicar query expansion o reframing para añadir sinónimos clínicos a las consultas en lenguaje coloquial.
3. Evaluar un modelo de generación más grande (Llama-3.2-3B o superior) para mejorar fidelidad al contexto y reducir alucinaciones.

**Resultado informal previo.** Las consultas sobre *diabetes mellitus* y *common cold* produjeron los mejores resultados durante el desarrollo, confirmado formalmente: Q1 (common cold) obtuvo 3/3. El caso diabetes, aunque sin artículo propio en el corpus, fue verificado informalmente con recuperación satisfactoria gracias a referencias cruzadas.
