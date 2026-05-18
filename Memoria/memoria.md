# RAGMED: Sistema de Recuperación y Generación Aumentada para Diagnóstico de Enfermedades

**Asignatura:** Sistemas de Información No Estructurada (SINE)  
**Curso:** 2025–2026

---

## 1. Introducción

Los sistemas de recuperación aumentada por generación (RAG, del inglés *Retrieval-Augmented Generation*) representan un paradigma de arquitectura que combina tres componentes fundamentales: un módulo de recopilación y almacenamiento de datos (crawler e indexador), un módulo de recuperación de información relevante, y un módulo de generación de texto mediante un modelo de lenguaje de gran escala (LLM) [1]. A diferencia de los sistemas basados únicamente en LLMs, los sistemas RAG anclan las respuestas generadas en un corpus documental específico, reduciendo las alucinaciones y permitiendo actualizar el conocimiento del sistema sin necesidad de reentrenar el modelo.

Como punto de partida, la práctica proporcionó un sistema RAG de referencia implementado sobre información de Pokémon, extraída de WikiDex mediante scraping HTML con BeautifulSoup [4]. Este sistema base ilustra el flujo completo del pipeline RAG: el crawler descarga páginas web y construye un corpus de texto plano; el módulo de recuperación localiza los fragmentos más relevantes para una consulta dada; y el LLM —servido localmente a través de Ollama [5]— genera una respuesta coherente a partir de esos fragmentos.

Para esta práctica, el dominio elegido es el de las enfermedades médicas. Esta elección se justifica por tres razones. En primer lugar, las enfermedades presentan una estructura semántica clara y consistente: cada artículo incluye habitualmente una descripción general, síntomas, causas y tratamiento, lo que facilita tanto la extracción estructurada de información como su aprovechamiento en la fase de recuperación. En segundo lugar, Wikipedia dispone de miles de artículos médicos bien documentados y actualizados, que constituyen un corpus de alta calidad y de acceso libre. En tercer lugar, la aplicación tiene utilidad práctica real: un sistema capaz de sugerir posibles enfermedades a partir de una lista de síntomas puede ser de ayuda en contextos de triaje o de orientación médica general, siempre como complemento y nunca como sustituto del criterio clínico.

El sistema implementado —denominado RAGMED— recibe como entrada una lista de síntomas introducida por el usuario y devuelve una lista de posibles enfermedades acompañada de una explicación generada por el LLM. Para ello se desarrollaron los siguientes componentes: (1) un crawler personalizado que descarga y estructura artículos de Wikipedia sobre enfermedades, (2) un módulo de recuperación de información mejorado respecto al código base (descrito en la sección 3), y (3) una evaluación cuantitativa de la calidad del sistema (sección 4).

El resto del documento se organiza del siguiente modo. La sección 2 describe en detalle el módulo crawler: fuente de datos, estrategia de extracción, problemas encontrados y soluciones adoptadas. La sección 3 presenta el módulo de recuperación de información. La sección 4 recoge los resultados de la evaluación. La sección 5 concluye el trabajo.

---

## 2. Módulo Crawler

### 2.1 Descripción general y rol en el sistema RAG

Un crawler web es un programa automatizado que recorre páginas de internet siguiendo enlaces y extrae su contenido para construir un corpus de texto [1]. En el contexto de un sistema RAG, el crawler constituye la etapa de adquisición de datos: sin un corpus de calidad, los módulos de recuperación y generación no pueden ofrecer respuestas fundamentadas. La calidad del corpus —en términos de cobertura, limpieza y estructura— condiciona directamente la calidad de las respuestas finales del sistema.

Para RAGMED se implementó la clase `RAGMED_crawler` en el fichero `src/ragmed_crawler.py`. El crawler cubre dos etapas: la descarga de la lista de enfermedades y la descarga del contenido individual de cada artículo.

<!-- TODO: add figure here — diagrama de flujo del crawler con las dos etapas -->

### 2.2 Fuente de datos: Wikipedia mediante la API REST

La fuente de datos elegida es la Wikipedia en inglés, accedida a través de su API REST oficial (MediaWiki API) [2]. Se optó por Wikipedia porque reúne varias características que la hacen idónea para este dominio: es la mayor enciclopedia en línea de libre acceso, cubre miles de enfermedades con artículos de extensión y calidad variables pero generalmente aceptables, y su estructura de secciones es consistente entre artículos de la misma tipología.

La decisión de utilizar la API en lugar de scraping directo del HTML fue determinante para simplificar el pipeline. El parámetro `explaintext=true` de la API hace que el servidor devuelva el texto del artículo ya en formato plano, con los encabezados de sección marcados mediante la convención `== Nombre de sección ==`. Esto elimina la necesidad de eliminar manualmente infoboxes, navboxes, superíndices de citas y otros elementos HTML ruidosos que sí habrían de tratarse en un scraping convencional. Además, el uso de la API respeta los términos de servicio de Wikimedia para usos no comerciales y académicos.

La URL del endpoint utilizado es la siguiente:

```
https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true
    &titles={nombre_enfermedad}&format=json&redirects=1
```

El parámetro `redirects=1` permite que la API resuelva automáticamente los redireccionamientos de Wikipedia, de modo que nombres alternativos de una enfermedad apunten correctamente al artículo canónico.

Para construir la lista de enfermedades a descargar, el crawler recorre las páginas de índice alfabético de Wikipedia [3], desde la letra A hasta la Z:

```
https://en.wikipedia.org/wiki/List_of_diseases_(A)
...
https://en.wikipedia.org/wiki/List_of_diseases_(Z)
```

Estas páginas índice sí se accedieron mediante scraping HTML con BeautifulSoup [4], ya que la API no ofrece un endpoint equivalente para listar artículos de una categoría con la misma comodidad. De cada página índice se extraen los enlaces a artículos individuales (`<li>` con `<a href="/wiki/...">`) filtrando aquellos que contienen dos puntos en la ruta (que corresponden a páginas especiales como categorías o archivos) y los que no apuntan al espacio de nombres principal de Wikipedia.

### 2.3 Extracción y estructura del corpus

#### 2.3.1 Selección de secciones

De cada artículo de enfermedad se extrajeron cuatro fragmentos:

- **Párrafo inicial (lead):** el texto antes del primer encabezado de sección, que constituye el resumen general de la enfermedad.
- **Signs and symptoms** (síntomas y signos): es la sección que describe las manifestaciones clínicas, directamente relevante para la tarea de diagnóstico a partir de síntomas.
- **Causes** (causas): explica la etiología de la enfermedad, lo que complementa la descripción clínica.
- **Treatment / Management / Prevention** (tratamiento): se busca en ese orden de prioridad, dado que distintos artículos emplean denominaciones diferentes para la misma sección temática.

Estas tres secciones se seleccionaron porque responden directamente a la pregunta que el sistema debe resolver: dado un conjunto de síntomas, ¿qué enfermedad puede ser y cómo se trata? El párrafo inicial aporta el contexto general, los síntomas permiten la recuperación por similitud con la consulta del usuario, las causas enriquecen la explicación, y el tratamiento completa la información clínicamente relevante.

La extracción de secciones a partir del texto plano devuelto por la API se realizó mediante una expresión regular que divide el texto en el patrón `== Sección ==`:

```python
_H2_PATTERN = re.compile(r"^== (.+?) ==$", re.MULTILINE)
```

La función `_parse_sections` divide el texto completo en un par (párrafo inicial, diccionario de secciones), y `_find_section` recorre una lista de nombres candidatos en orden de prioridad hasta encontrar una coincidencia.

#### 2.3.2 Formato de salida

El corpus final se almacena en un fichero `diseases.txt` donde cada enfermedad ocupa un bloque con el siguiente formato:

```
Nombre de la enfermedad
=======================
Lead: [descripción general]

Signs and symptoms
==================
[texto]

Causes
======
[texto]

Treatment
=========
[texto]
```

Cuando una sección no está disponible en el artículo de Wikipedia, se escribe el literal `(No information available.)` para que el bloque mantenga siempre la misma estructura y sea fácilmente parseable por el módulo de recuperación. Además de este fichero consolidado, el crawler genera ficheros intermedios por enfermedad (`diseases/{nombre}.txt` para el extracto bruto y `diseases/{nombre}_clean.txt` para el extracto estructurado), lo que facilita la depuración y la reanudación de ejecuciones interrumpidas.

<!-- TODO: add figure here — ejemplo de bloque de diseases.txt para una enfermedad bien documentada (p. ej. Abdominal aortic aneurysm) -->

#### 2.3.3 Problemas encontrados y soluciones

Durante el desarrollo del crawler se identificaron tres categorías de problemas:

**Ruido en las páginas índice.** Las páginas `List_of_diseases_(X)` contienen, además de los enlaces a artículos de enfermedades, elementos de navegación como navboxes, tablas de contenidos y hatnotes. Al iterar sobre todos los elementos `<a>` del contenido principal, algunos de estos enlaces de navegación se colaban en la lista. La solución adoptada fue eliminar explícitamente los nodos de ruido (`navbox`, `toc`, `mw-references-wrap`, `hatnote`) antes de recorrer los `<li>`, y además filtrar cualquier href que contuviera dos puntos o que no comenzara por `/wiki/`.

**Limitación de tasa de peticiones (HTTP 429).** La Wikipedia impone límites de velocidad a los clientes que realizan peticiones rápidas. Cuando el servidor devuelve un código 429 (*Too Many Requests*) o 503, el crawler implementa una estrategia de reintento con espera exponencial: 2 segundos tras el primer intento fallido, 4 tras el segundo y 8 tras el tercero (`wait = 2 ** attempt`). Adicionalmente, entre cada petición a la API se introduce una espera fija de 1,5 segundos. La cabecera `User-Agent` se configura con el valor `RAGMED-Crawler/1.0 (university homework)` para identificar el cliente de forma transparente, tal como recomienda la política de uso de la API de Wikimedia [2].

**Inconsistencia en los nombres de sección.** Wikipedia no normaliza de forma estricta los títulos de las secciones entre artículos. Por ejemplo, mientras que Influenza usa la sección `Treatment`, Diabetes mellitus emplea `Management`. El crawler maneja esta variabilidad buscando los nombres candidatos en orden de prioridad: `["Treatment", "Management", "Prevention"]`. Esta lista se define como constante en el módulo y puede ampliarse fácilmente si se identifican otras denominaciones en el corpus.

Toda la actividad del crawler se registra mediante el módulo estándar `logging` de Python, con nivel `INFO` para el progreso normal y `WARNING`/`ERROR` para situaciones de fallo. Se evitó el uso de sentencias `print` directas para facilitar la integración futura del módulo con sistemas de orquestación que capturen logs estructurados.

#### 2.3.4 Resultados de la ejecución de prueba

Se realizó una ejecución de prueba con los primeros 20 nombres de la letra A (`max_diseases=20`). De estas 20 enfermedades, **17 se descargaron correctamente** con al menos uno de los cuatro campos completos. Las 3 restantes se omitieron por agotamiento del número máximo de reintentos ante respuestas 429 persistentes; en los tres casos se trataba de síndromes raros con artículos de Wikipedia muy breves o prácticamente vacíos, por lo que su exclusión no supone una pérdida significativa para el corpus.

El contraste de calidad entre artículos es notable. Una enfermedad bien documentada como Aarskog syndrome dispone de párrafo inicial detallado, sección de síntomas extensa con subsecciones, y sección de tratamiento; el bloque resultante en `diseases.txt` es rico y directamente útil para la recuperación. En cambio, un síndrome raro como Aagenaes syndrome solo tiene información en el párrafo inicial y en la sección de tratamiento, quedando los campos de síntomas y causas marcados como `(No information available.)`. Esta heterogeneidad es inherente a la fuente de datos y deberá tenerse en cuenta en la evaluación del sistema completo.

### 2.4 Referencias de sección

<!-- Referencias globales al final del documento -->

---

## 3. Módulo de Recuperación de Información

> *[Sección pendiente de redacción — T1.2]*

---

## 4. Evaluación

> *[Sección pendiente de redacción — T1.3]*

---

## 5. Conclusiones

> *[Sección pendiente de redacción]*

---

## Referencias

[1] W. B. Croft, D. Metzler, and T. Strohman, *Search Engines: Information Retrieval in Practice*, Pearson Education, 2015.

[2] Wikimedia Foundation, "MediaWiki API," Wikipedia. [Online]. Available: https://www.mediawiki.org/wiki/API:Main_page. [Accessed: May 2026].

[3] Wikipedia contributors, "List of diseases," Wikipedia, The Free Encyclopedia. [Online]. Available: https://en.wikipedia.org/wiki/List_of_diseases_(A). [Accessed: May 2026].

[4] L. Richardson, "Beautiful Soup Documentation," Crummy.com. [Online]. Available: https://www.crummy.com/software/BeautifulSoup/bs4/doc/. [Accessed: May 2026].

[5] Ollama, "Ollama — Get up and running with large language models." [Online]. Available: https://ollama.com/. [Accessed: May 2026].
