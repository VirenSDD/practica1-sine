# RAGMED — Preguntas de Evaluación con Ground Truth

**Sistema evaluado:** RAGMED con función de recuperación híbrida (BM25 + coseno, α = 0.5)  
**Corpus:** diseases.txt (Wikipedia, ~5 390 enfermedades)  
**Top-N recuperados:** 5 fragmentos por pregunta

Las preguntas están redactadas en inglés para maximizar la calidad de la recuperación (el corpus está en inglés). El análisis y la puntuación se presentan en español.

---

## Q1 — Common cold

**Pregunta (query):** I have a runny nose, sore throat, sneezing, and a mild cough. What illness might I have?

**Enfermedad esperada:** Common cold

**Pasaje relevante en corpus:**
> Common cold — Signs and symptoms: The typical symptoms of a cold include cough, runny nose, sneezing, nasal congestion, and a sore throat, sometimes accompanied by muscle ache, fatigue, headache, and loss of appetite.

**Criterio de respuesta correcta:** El sistema debe identificar *common cold* y mencionar al menos 3 de los siguientes síntomas: runny nose, sneezing, sore throat, cough.

---

## Q2 — Influenza

**Pregunta (query):** I suddenly developed a high fever, severe body aches, chills, and a dry cough. What could this be?

**Enfermedad esperada:** Influenza

**Pasaje relevante en corpus:**
> Influenza — Signs and symptoms: The symptoms of influenza are similar to those of a cold, although usually more severe and less likely to include a runny nose. The onset of symptoms is sudden, and initial symptoms are predominantly non-specific, including fever, chills, headaches, muscle pain, malaise, loss of appetite, lack of energy, and confusion. These are usually accompanied by respiratory symptoms such as a dry cough, sore or dry throat, hoarse voice, and a stuffy or runny nose.

**Criterio de respuesta correcta:** El sistema debe identificar *influenza* y mencionar inicio súbito y al menos 2 de: fever, body aches/muscle pain, chills, dry cough.

---

## Q3 — Asthma

**Pregunta (query):** I get recurring episodes of wheezing, shortness of breath, and chest tightness, especially at night and during exercise. What condition might this be?

**Enfermedad esperada:** Asthma

**Pasaje relevante en corpus:**
> Asthma — Signs and symptoms: Asthma causes recurrent episodes of wheezing, shortness of breath, chest tightness, and coughing. Symptoms are usually worse at night and in the early morning or in response to exercise or cold air.

**Criterio de respuesta correcta:** El sistema debe identificar *asthma* y mencionar al menos 2 de: wheezing, shortness of breath, chest tightness, y el patrón nocturno o relacionado con el ejercicio.

---

## Q4 — Migraine

**Pregunta (query):** I have a severe throbbing headache on one side of my head, along with nausea and sensitivity to light and sound. What might I have?

**Enfermedad esperada:** Migraine

**Pasaje relevante en corpus:**
> Migraine — Lead: Migraine is a neurological disorder that causes moderate-to-severe headaches. The pain usually affects one side of the head. It is generally associated with nausea, light sensitivity and sound sensitivity.

**Criterio de respuesta correcta:** El sistema debe identificar *migraine* y mencionar: headache unilateral, nausea, y al menos una de: light sensitivity, sound sensitivity.

---

## Q5 — Gout

**Pregunta (query):** I woke up with sudden, intense pain, swelling, and redness in my big toe joint. What could be causing this?

**Enfermedad esperada:** Gout

**Pasaje relevante en corpus:**
> Gout — Signs and symptoms: Gout can present in several ways, although the most common is a recurrent attack of acute inflammatory arthritis (a red, tender, hot, swollen joint). The metatarsophalangeal joint at the base of the big toe is affected most often, accounting for half of cases. Joint pain usually begins during the night and peaks within 24 hours of onset.

**Criterio de respuesta correcta:** El sistema debe identificar *gout* y mencionar: joint inflammation (red/swollen/painful), big toe, y la naturaleza súbita del ataque.

---

## Q6 — Hypothyroidism

**Pregunta (query):** I have been feeling extremely tired, gaining weight, feeling cold all the time, and experiencing constipation. What might I have?

**Enfermedad esperada:** Hypothyroidism

**Pasaje relevante en corpus:**
> Hypothyroidism — Lead: Hypothyroidism is an endocrine disease in which the thyroid gland does not produce enough thyroid hormones. It can cause a number of symptoms, such as poor ability to tolerate cold, extreme fatigue, muscle aches, constipation, slow heart rate, depression, and weight gain.

**Criterio de respuesta correcta:** El sistema debe identificar *hypothyroidism* y mencionar al menos 3 de: fatigue, weight gain, cold intolerance, constipation.

---

## Q7 — Pneumonia

**Pregunta (query):** I have a fever, sharp chest pain that worsens when I breathe deeply, a productive cough, and difficulty breathing. What illness might this be?

**Enfermedad esperada:** Pneumonia

**Pasaje relevante en corpus:**
> Pneumonia — Signs and symptoms: People with infectious pneumonia often have a productive cough, fever accompanied by shaking chills, shortness of breath, sharp or stabbing chest pain during deep breaths, and an increased rate of breathing.

**Criterio de respuesta correcta:** El sistema debe identificar *pneumonia* y mencionar al menos 3 de: productive cough, fever, chest pain (pleuritic), shortness of breath.

---

## Q8 — Rheumatoid arthritis

**Pregunta (query):** My joints are swollen and painful, especially in the mornings, and the morning stiffness lasts for more than an hour. The same joints on both sides of my body are affected. What could I have?

**Enfermedad esperada:** Rheumatoid arthritis

**Pasaje relevante en corpus:**
> Rheumatoid arthritis — Signs and symptoms (Joints): RA typically manifests with signs of inflammation, with the affected joints being swollen, warm, painful, and stiff, particularly early in the morning on waking or following prolonged inactivity. Increased stiffness early in the morning is often a prominent feature of the disease and typically lasts for more than an hour. The joints are often affected in a fairly symmetrical fashion.

**Criterio de respuesta correcta:** El sistema debe identificar *rheumatoid arthritis* y mencionar: morning stiffness (>1 h), joint swelling/pain, y afectación simétrica.

---

## Q9 — Malaria

**Pregunta (query):** After returning from sub-Saharan Africa, I am experiencing cyclic fevers with chills and sweating, headaches, nausea, and muscle pain. What might I have?

**Enfermedad esperada:** Malaria

**Pasaje relevante en corpus:**
> Malaria — Signs and symptoms: Symptoms during the early stages of malaria infection are fever, chills, headache, nausea, and vomiting and diarrhea; more serious cases may show enlarged spleen or liver, and mild jaundice. Without treatment, symptoms — particularly the fever — can settle into a regular pattern, recurring every two or three days (paroxysmal attacks).

**Criterio de respuesta correcta:** El sistema debe identificar *malaria* y mencionar: cyclic/recurrent fever, chills, headache, y el contexto de viaje tropical.

---

## Q10 — Tuberculosis

**Pregunta (query):** I have had a persistent cough for several weeks, I am coughing up blood, I experience night sweats, and I have lost weight without trying. What illness could this be?

**Enfermedad esperada:** Tuberculosis

**Pasaje relevante en corpus:**
> Tuberculosis — Lead: Typical symptoms of active TB are chronic cough with blood-containing mucus, fever, night sweats, and weight loss.
>
> Tuberculosis — Signs and symptoms: General signs and symptoms include fever, chills, night sweats, loss of appetite, weight loss, and fatigue. If a tuberculosis infection does become active, it most commonly involves the lungs. Symptoms may include chest pain, a prolonged cough producing sputum which may be bloody, tiredness, temperature, loss of appetite, wasting and general malaise.

**Criterio de respuesta correcta:** El sistema debe identificar *tuberculosis* y mencionar al menos 3 de: chronic cough, hemoptysis (bloody sputum), night sweats, weight loss.

---

## Nota sobre Diabetes mellitus

Durante las pruebas informales previas a la evaluación formal, se comprobó que el sistema proporciona respuestas relevantes a consultas sobre síntomas de diabetes (poliuria, polidipsia, fatiga, visión borrosa) **a pesar de que el corpus no contiene un artículo dedicado a Diabetes mellitus** como entrada principal. Los fragmentos recuperados proceden de otras enfermedades que mencionan la diabetes como comorbilidad. Este comportamiento demuestra la capacidad del sistema de sintetizar información distribuida en el corpus, y se comenta en la sección 4.4 de la memoria.
