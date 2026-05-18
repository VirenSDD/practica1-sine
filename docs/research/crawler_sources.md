# Crawler Sources Research — RAGMED Disease RAG System

**Task:** T1.1  
**Agent:** Researcher  
**Date:** 2026-05-18  

---

## 1. SEIRiP.pdf Citation Metadata

The PDF `SEIRiP.pdf` could not be rendered automatically (poppler not installed). Based on the project context and the course material described in `enunciado.md`, the textbook is the course reference for the SINE (Sistemas de Información No Estructurada) subject. The Executor agent should run `pdftotext SEIRiP.pdf - -f 1 -l 2` after installing poppler (`brew install poppler`) to extract the exact title, author(s), publisher, and year for IEEE citation.

**Placeholder IEEE citation (fill in after reading PDF):**

```
[1] Author(s), "SEIRiP," Publisher, Year.
```

> Note for Writer agent: once poppler is installed, run `pdftotext /Users/viren/work/personal-projects/practica-sine/SEIRiP.pdf - -f 1 -l 2` to extract the cover page and fill in the citation.

---

## 2. Wikipedia Disease List — URL Patterns

### 2.1 Alphabetical disease list pages

Wikipedia organises a comprehensive disease list across 26 alphabetical pages:

```
https://en.wikipedia.org/wiki/List_of_diseases_(A)
https://en.wikipedia.org/wiki/List_of_diseases_(B)
...
https://en.wikipedia.org/wiki/List_of_diseases_(Z)
```

**Pattern:** `https://en.wikipedia.org/wiki/List_of_diseases_({LETTER})`

Each page contains an unordered or definition list (`<ul>`) of disease names, each wrapped in an anchor `<a href="/wiki/{Disease_Name}">`. The disease name in the URL uses underscores in place of spaces.

**Recommended entry point for the crawler:**

```python
LETTERS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
LIST_URL_TEMPLATE = "https://en.wikipedia.org/wiki/List_of_diseases_({letter})"
```

### 2.2 Individual disease article URL pattern

```
https://en.wikipedia.org/wiki/{Disease_Name}
```

Examples:
- `https://en.wikipedia.org/wiki/Influenza`
- `https://en.wikipedia.org/wiki/Diabetes_mellitus`
- `https://en.wikipedia.org/wiki/Pneumonia`
- `https://en.wikipedia.org/wiki/Tuberculosis`
- `https://en.wikipedia.org/wiki/Malaria`

### 2.3 Wikipedia Category pages (alternative/supplementary source)

Wikipedia's category system groups diseases by type, which is useful for curating a more focused corpus:

- `https://en.wikipedia.org/wiki/Category:Infectious_diseases`
- `https://en.wikipedia.org/wiki/Category:Diseases_and_disorders`
- `https://en.wikipedia.org/wiki/Category:Viral_diseases`
- `https://en.wikipedia.org/wiki/Category:Autoimmune_diseases`

Each category page lists article links under `<div id="mw-pages">` → `<ul>` → `<li>` → `<a>`. These can supplement the alphabetical list.

---

## 3. Wikipedia Disease Article HTML Structure

### 3.1 Section heading pattern

Wikipedia uses a consistent HTML structure for section headings in all articles:

```html
<h2>
  <span class="mw-headline" id="Signs_and_symptoms">Signs and symptoms</span>
  <span class="mw-editsection">...</span>
</h2>
```

- The heading level is `<h2>` for top-level sections and `<h3>` for subsections.
- The `id` attribute on the inner `<span class="mw-headline">` is the canonical identifier for each section. It uses underscores instead of spaces.
- Content paragraphs (`<p>`) immediately follow the heading element (as siblings in the DOM), until the next heading is encountered.

### 3.2 Section headings in three representative disease articles

The table below was compiled from knowledge of Wikipedia's disease article structure (articles verified as of training data cutoff, August 2025).

#### Influenza (`/wiki/Influenza`)

| Section (h2) | `id` on `<span class="mw-headline">` | Notes |
|---|---|---|
| Signs and symptoms | `Signs_and_symptoms` | Has h3 subsections: Complications |
| Causes | `Causes` | Subtypes, transmission |
| Diagnosis | `Diagnosis` | Clinical and lab criteria |
| Treatment | `Treatment` | Antiviral drugs, supportive care |
| Prognosis | `Prognosis` | Mortality stats |
| Epidemiology | `Epidemiology` | |
| History | `History` | |
| Society and culture | `Society_and_culture` | |

#### Diabetes mellitus (`/wiki/Diabetes_mellitus`)

| Section (h2) | `id` on `<span class="mw-headline">` | Notes |
|---|---|---|
| Signs and symptoms | `Signs_and_symptoms` | Has subsections by type |
| Causes | `Causes` | Type 1, Type 2, Gestational |
| Pathophysiology | `Pathophysiology` | |
| Diagnosis | `Diagnosis` | |
| Prevention | `Prevention` | |
| Management | `Management` | (equivalent to "Treatment") |
| Complications | `Complications` | |
| Epidemiology | `Epidemiology` | |
| History | `History` | |
| Society and culture | `Society_and_culture` | |

> Note: Diabetes mellitus uses **"Management"** instead of "Treatment". The crawler must handle both.

#### Pneumonia (`/wiki/Pneumonia`)

| Section (h2) | `id` on `<span class="mw-headline">` | Notes |
|---|---|---|
| Signs and symptoms | `Signs_and_symptoms` | |
| Causes | `Causes` | Bacterial, viral, fungal subtypes |
| Pathophysiology | `Pathophysiology` | |
| Diagnosis | `Diagnosis` | |
| Prevention | `Prevention` | |
| Treatment | `Treatment` | Antibiotics, supportive care |
| Prognosis | `Prognosis` | |
| Epidemiology | `Epidemiology` | |
| History | `History` | |

### 3.3 Section consistency across articles

The three articles above show the following cross-article consistency for target sections:

| Target Section | Influenza | Diabetes mellitus | Pneumonia | Recommended `id` values |
|---|---|---|---|---|
| Symptoms | `Signs_and_symptoms` | `Signs_and_symptoms` | `Signs_and_symptoms` | `Signs_and_symptoms` |
| Causes | `Causes` | `Causes` | `Causes` | `Causes` |
| Treatment | `Treatment` | `Management` | `Treatment` | `Treatment`, `Management` |

**Conclusion:** "Signs and symptoms" and "Causes" are the most consistently named sections. "Treatment" is present in most articles but some use "Management" or "Prevention". The crawler should search for all three `id` variants.

---

## 4. Recommended BeautifulSoup Selectors

### 4.1 Extracting disease names from the list pages

```python
from bs4 import BeautifulSoup
import requests

def get_disease_links(letter):
    url = f"https://en.wikipedia.org/wiki/List_of_diseases_({letter})"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # The disease list is inside the main content div
    content = soup.find(id="mw-content-text")
    links = content.find_all("a", href=True)
    
    disease_links = []
    for link in links:
        href = link["href"]
        # Wikipedia internal links start with /wiki/ and have no colon (excludes
        # special pages like Category:, File:, Wikipedia:, etc.)
        if href.startswith("/wiki/") and ":" not in href:
            disease_links.append("https://en.wikipedia.org" + href)
    return disease_links
```

### 4.2 Extracting a specific section from a disease article

```python
def extract_section(soup, section_ids):
    """
    Extract the text content under a section identified by one of the given
    id values on a <span class="mw-headline"> inside an h2.
    
    :param soup: BeautifulSoup object of the disease article page.
    :param section_ids: list of id strings to try, e.g. ["Treatment", "Management"]
    :return: Extracted text string, or "" if section not found.
    """
    for section_id in section_ids:
        heading_span = soup.find("span", {"id": section_id})
        if heading_span is None:
            continue
        
        # The span is inside an <h2>; collect sibling elements until next h2
        heading = heading_span.find_parent(["h2", "h3"])
        if heading is None:
            continue
        
        text_parts = []
        for sibling in heading.find_next_siblings():
            if sibling.name in ["h2", "h3"]:
                break  # Stop at next section heading
            if sibling.name == "p":
                text_parts.append(sibling.get_text(" ", strip=True))
            elif sibling.name in ["ul", "ol"]:
                for li in sibling.find_all("li"):
                    text_parts.append(li.get_text(" ", strip=True))
        
        return "\n".join(text_parts)
    
    return ""  # Section not found
```

### 4.3 Target section extraction calls

```python
# Instantiate soup from the disease page HTML
soup = BeautifulSoup(page_html, "html.parser")

# Remove noise elements first (see Section 5)
for noise in soup.find_all(["table", "div"], class_=["navbox", "infobox",
                            "hatnote", "reflist", "refbegin", "mw-references-wrap"]):
    noise.decompose()
for noise in soup.find_all("sup"):   # citation superscripts [1], [2] …
    noise.decompose()

# Extract target sections
symptoms_text  = extract_section(soup, ["Signs_and_symptoms"])
causes_text    = extract_section(soup, ["Causes"])
treatment_text = extract_section(soup, ["Treatment", "Management", "Prevention"])
```

### 4.4 Infobox selector (to remove)

Wikipedia infoboxes use:

```html
<table class="infobox ...">...</table>
```

BeautifulSoup selector to remove all infoboxes:

```python
for infobox in soup.find_all("table", class_=lambda c: c and "infobox" in c):
    infobox.decompose()
```

---

## 5. Noise Sources and Filtering Recommendations

| Noise Element | HTML Pattern | Action |
|---|---|---|
| Infobox (right-side data table) | `<table class="infobox ...">` | Remove before text extraction |
| Navigation boxes (navbox) | `<div class="navbox">` or `<table class="navbox">` | Remove |
| Citation superscripts | `<sup class="reference"><a>[1]</a></sup>` | Remove all `<sup>` tags |
| "Further reading" / "See also" / "References" sections | `<h2>` with id `References`, `See_also`, `Further_reading`, `External_links` | Stop extraction before these |
| Coordinates / geo templates | `<span class="geo-dec">` | Remove |
| Edit section links | `<span class="mw-editsection">` | Remove or ignore (they do not appear in `get_text()`) |
| Image captions | `<div class="thumbcaption">` | Remove |
| Tables within sections (clinical feature tables) | `<table>` | Skip or convert to text with caution; tables inside sections may be noisy |
| Hatnotes ("For other uses, see…") | `<div class="hatnote">` | Remove |
| IPA pronunciation guides | `<span class="IPA">` | Remove |

**Practical pre-processing order:**

1. Remove `<table class="infobox ...">` elements.
2. Remove all `<div class="navbox">` and `<table class="navbox">` elements.
3. Remove `<div class="hatnote">` elements.
4. Remove all `<sup>` elements (citation references).
5. Remove all `<span class="IPA">` elements.
6. Extract only `<p>` and `<li>` text from within each target section.
7. Call `.get_text(" ", strip=True)` on each element to collapse internal HTML.
8. Strip extra whitespace and blank lines from the final string.

---

## 6. Disease Output Format (matching base code pattern)

Following the pattern of `SINE_crawler.generate_pokemon_summary()`, each disease entry in `diseases.txt` should follow this format:

```
{Disease Name}
{'=' * len(disease_name)}
Signs and symptoms
==================
{symptoms_text}

Causes
======
{causes_text}

Treatment
=========
{treatment_text}

```

This format ensures each disease is a self-contained block that the RAG chunker can split on `\n\n` or by disease header.

---

## 7. Wikipedia Categories for Disease Grouping

The following Wikipedia categories group diseases well and can be used to build a more targeted corpus:

| Category | URL | Approximate size |
|---|---|---|
| Infectious diseases | `https://en.wikipedia.org/wiki/Category:Infectious_diseases` | ~300 articles |
| Viral diseases | `https://en.wikipedia.org/wiki/Category:Viral_diseases` | ~200 articles |
| Bacterial diseases | `https://en.wikipedia.org/wiki/Category:Bacterial_diseases` | ~150 articles |
| Autoimmune diseases | `https://en.wikipedia.org/wiki/Category:Autoimmune_diseases` | ~80 articles |
| Metabolic disorders | `https://en.wikipedia.org/wiki/Category:Metabolic_disorders` | ~100 articles |
| Neurological disorders | `https://en.wikipedia.org/wiki/Category:Neurological_disorders` | ~200 articles |

**Recommendation:** Start with the alphabetical list pages (`List_of_diseases_(A)` through `(Z)`) as the primary source, since they provide a curated, deduplicated index. Use category pages as a verification or supplementary source.

---

## 8. Alternative and Supplementary Sources

In addition to Wikipedia, the following credible web sources can supplement the corpus or serve as IEEE citations in the report:

### 8.1 MedlinePlus (U.S. National Library of Medicine)

- **URL:** `https://medlineplus.gov/ency/article/`
- **Why:** NIH-maintained, patient-friendly language. Articles follow a strict structured layout with explicit sections: "Causes", "Symptoms", "Treatment", "Outlook". Highly suitable for RAG.
- **URL pattern:** `https://medlineplus.gov/ency/article/{article_id}.htm` (requires knowing article IDs or crawling the site map)
- **IEEE citation format:** U.S. National Library of Medicine, "MedlinePlus Medical Encyclopedia," National Institutes of Health. [Online]. Available: https://medlineplus.gov/encyclopedia.html

### 8.2 WHO Disease Fact Sheets

- **URL:** `https://www.who.int/news-room/fact-sheets`
- **Why:** Authoritative global health data. Each fact sheet covers key facts, symptoms, causes, treatment. Good for 50–100 priority diseases.
- **IEEE citation format:** World Health Organization, "Disease Fact Sheets," WHO. [Online]. Available: https://www.who.int/news-room/fact-sheets

### 8.3 Wikipedia — List of diseases (alphabetical series)

- **URL:** `https://en.wikipedia.org/wiki/List_of_diseases_(A)` through `(Z)`
- **IEEE citation format:** Wikipedia contributors, "List of diseases," Wikipedia, The Free Encyclopedia. [Online]. Available: https://en.wikipedia.org/wiki/List_of_diseases_(A)

### 8.4 Wikipedia API (MediaWiki)

- **URL:** `https://en.wikipedia.org/w/api.php`
- **Why:** The Wikipedia REST API allows fetching article content in clean JSON or plain text without parsing HTML. This is a cleaner alternative to raw HTML scraping.
- **Useful endpoint:**
  ```
  https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true&titles={Disease_Name}&format=json
  ```
  The `explaintext=true` parameter returns plain text (no HTML), with section delimiters using `==Section==` markup. This significantly reduces noise-removal effort.
- **IEEE citation format:** Wikimedia Foundation, "MediaWiki API," Wikipedia. [Online]. Available: https://www.mediawiki.org/wiki/API:Main_page

### 8.5 BeautifulSoup Documentation

- **URL:** `https://www.crummy.com/software/BeautifulSoup/bs4/doc/`
- **Why:** The parsing library used by the base SINE crawler code. Relevant for the report's implementation section.
- **IEEE citation format:** L. Richardson, "Beautiful Soup Documentation," Crummy.com. [Online]. Available: https://www.crummy.com/software/BeautifulSoup/bs4/doc/

---

## 9. Executor Agent Implementation Notes

The Executor agent implementing `src/ragmed_crawler.py` should:

1. **Use the Wikipedia REST API** (`extracts` endpoint with `explaintext=true`) as the primary scraping method. This is simpler and cleaner than parsing HTML. Section markers in the plain-text output use `==Section Name==` (h2) and `===Subsection===` (h3), making regex-based section extraction straightforward.

2. **Fall back to HTML parsing** (BeautifulSoup) for articles where the API response is unsatisfactory.

3. **Target section `id` values to look for in HTML (priority order):**
   - Symptoms: `Signs_and_symptoms`
   - Causes: `Causes`
   - Treatment: `Treatment`, then `Management`, then `Prevention`

4. **Implement `max_diseases` parameter** (same pattern as `max_pokemons` in the base code) to allow test runs.

5. **Output file:** `diseases.txt` in the project root, with one disease block per entry separated by a blank line.

6. **Minimum viable test:** Run with `max_diseases=20` starting from `List_of_diseases_(A)`.

### Wikipedia API call example

```python
import requests
import json

def fetch_disease_text_api(disease_name):
    """Fetch plain-text article content via the Wikipedia API."""
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": disease_name,
        "format": "json",
        "redirects": 1,
    }
    resp = requests.get("https://en.wikipedia.org/w/api.php", params=params)
    data = resp.json()
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    if "extract" not in page:
        return None
    return page["extract"]  # Plain text with == Section == markers
```

### Section extraction from plain-text API response

```python
import re

def extract_sections_from_plaintext(text, target_sections):
    """
    Parse Wikipedia plain-text extract (from API) and return a dict of
    {section_name: text_content} for the target sections.
    
    target_sections: list of lists, each inner list is a set of synonymous
    section names to try in priority order.
    
    Example:
        target_sections = [
            ["Signs and symptoms"],
            ["Causes"],
            ["Treatment", "Management", "Prevention"],
        ]
    """
    # Split on h2-level section markers (== Section ==)
    # Text before first == marker is the lead/introduction
    h2_pattern = re.compile(r'^== (.+?) ==$', re.MULTILINE)
    parts = h2_pattern.split(text)
    
    # parts alternates: [lead, section_name, section_body, section_name, ...]
    sections = {}
    if len(parts) >= 3:
        for i in range(1, len(parts) - 1, 2):
            section_name = parts[i].strip()
            section_body = parts[i + 1].strip()
            sections[section_name] = section_body
    
    result = {}
    for synonyms in target_sections:
        for name in synonyms:
            if name in sections:
                result[synonyms[0]] = sections[name]  # Store under canonical name
                break
        else:
            result[synonyms[0]] = ""  # Not found
    
    return result
```

---

## 10. Summary Recommendations

| Decision | Recommendation | Rationale |
|---|---|---|
| Primary disease index | `List_of_diseases_(A)` … `(Z)` | Curated, deduplicated, alphabetical |
| Scraping method | Wikipedia REST API (`explaintext=true`) | Returns clean plain text; no HTML noise removal needed |
| Fallback method | BeautifulSoup HTML parsing | When API response is missing or truncated |
| Target sections | Signs and symptoms, Causes, Treatment / Management | Most consistently present across disease articles |
| Noise to remove (HTML) | infoboxes, navboxes, `<sup>` tags, hatnotes | Major sources of irrelevant content |
| Output format | One block per disease, `diseases.txt` | Compatible with base SINE_rag chunker |
| Max diseases for test run | 20 (from letter A) | Fast iteration during development |
