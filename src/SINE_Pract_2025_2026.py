'''
Es importante tener el entorno de desarrollo configurado para utf-8 
o puede dar problemas al leer ciertos caracteres

@author: Jorge Carrillo de Albornoz
'''
 
import ollama
import os
import requests
import re
from bs4 import BeautifulSoup

class SINE_crawler:
    def __init__(self, base_url="https://www.wikidex.net/wiki/", max_pokemons=None):
        """
        Inicializa el crawler que obtiene información de Pokémon desde WikiDex.

        :param base_url: URL base del sitio web WikiDex.
        :param max_pokemons: Número máximo de Pokémon a descargar. Si es None, se descargan todos.
        """
        self.base_url = base_url
        self.max_pokemons = max_pokemons
        self.pokemon_list = []  # Lista donde se almacenarán los nombres de los Pokémon.

    def download_pokemon_list(self, url, output_file="pokemon_list.txt"):
        """
        Descarga la lista de Pokémon desde WikiDex y la guarda en un archivo de texto.

        :param url: URL de la página con la lista de Pokémon.
        :param output_file: Nombre del archivo donde se guardará la lista.
        :return: Lista de nombres de Pokémon descargados.
        """
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al descargar {url}")
            return
        
        page_text = response.text

        # Extraer los nombres de los Pokémon utilizando expresiones regulares.
        pokemon_pattern = re.findall(r'<td.*?>.*?<a.*?title="(.*?)"', page_text)
        self.pokemon_list = list(dict.fromkeys(pokemon_pattern))  # Eliminar duplicados.

        # Si hay un límite de Pokémon a descargar, aplicar el recorte.
        if self.max_pokemons is not None:
            self.pokemon_list = self.pokemon_list[:self.max_pokemons]

        # Guardar la lista en un archivo de texto.
        with open(output_file, "w", encoding="utf-8") as file:
            file.writelines(name + "\n" for name in self.pokemon_list)
        
        print(f"Lista de Pokémon guardada en {output_file} ({len(self.pokemon_list)} Pokémon descargados)")
        return self.pokemon_list

    def download_pokemon_info(self):
        """
        Descarga la información de cada Pokémon en formato HTML y la guarda en archivos individuales.
        """
        os.makedirs("pokemons", exist_ok=True)  # Crear carpeta para almacenar los archivos si no existe.

        for name in self.pokemon_list:
            safe_name = name.replace(" ", "_")  # Reemplazar espacios por guiones bajos para formar la URL.
            pokemon_url = self.base_url + safe_name  # Construir la URL de la página del Pokémon.
            response = requests.get(pokemon_url)

            if response.status_code == 200:
                with open(f"pokemons/{safe_name}.html", "w", encoding="utf-8") as file:
                    file.write(response.text)
                print(f"Información de {name} guardada en pokemons/{safe_name}.html")
                
                # Limpiar la página descargada para extraer solo la información relevante.
                self.clean_pokemon_page(safe_name)
            else:
                print(f"No se pudo descargar la información de {name}")

    def clean_pokemon_page(self, pokemon_name):
        """
        Extrae y limpia la información relevante de la página HTML del Pokémon.
        Solo se mantienen las secciones 'Biología' y 'Evolución'.

        :param pokemon_name: Nombre del Pokémon cuyo archivo HTML se limpiará.
        """
        input_file = f"pokemons/{pokemon_name}.html"
        output_file = f"pokemons/{pokemon_name}.txt"

        with open(input_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")  # Parsear el HTML con BeautifulSoup.

        # Extraer la sección "Biología".
        biologia_section = soup.find(id="Biología")
        biologia_text = ""
        if biologia_section:
            biologia_text = self.extract_section_text(biologia_section)

        # Extraer la sección "Evolución".
        evolucion_section = soup.find(id="Evolución")
        evolucion_text = ""
        if evolucion_section:
            evolucion_text = self.extract_section_text(evolucion_section)
            evolucion_text = self.clean_evolution_text(evolucion_text)  # Convertir a una sola frase sin puntuación.

        # Crear el contenido final con formato.
        final_text = ""
        if biologia_text:
            final_text += "Biología\n" + "=" * 8 + "\n" + biologia_text + "\n\n"
        if evolucion_text:
            final_text += "Evolución\n" + "=" * 9 + "\n" + evolucion_text + "\n"

        # Guardar el resultado en un archivo de texto.
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(final_text)
        
        print(f"Página de {pokemon_name} limpiada y guardada en {output_file}")

    def extract_section_text(self, section):
        """
        Extrae el texto de una sección HTML, ignorando encabezados y elementos innecesarios.

        :param section: Elemento HTML que representa una sección de la página.
        :return: Texto limpio de la sección.
        """
        text_lines = []
        for sibling in section.find_all_next():
            if sibling.name and sibling.name.startswith("h2"):  # Detenerse en el siguiente encabezado principal.
                break
            if sibling.name in ["p", "ul", "ol"]:  # Solo extraer párrafos y listas.
                text_lines.append(sibling.get_text(" ", strip=True))  # Obtener texto limpio.
        
        return "\n".join(text_lines)

    def clean_evolution_text(self, text):
        """
        Limpia y reestructura la información de la evolución del Pokémon en una sola frase sin puntuación.

        :param text: Texto original de la sección "Evolución".
        :return: Texto formateado sin puntuación y con espacios normalizados.
        """
        text = re.sub(r"[^\w\s]", "", text)  # Eliminar puntuación.
        text = re.sub(r"\s+", " ", text)  # Eliminar espacios extra.
        return text.strip()
    
    def generate_pokemon_summary(self, output_file="pokemons.txt"):
        """
        Genera un resumen de la información de todos los Pokémon descargados,
        unificando los datos en un solo archivo.

        :param output_file: Nombre del archivo donde se guardará el resumen.
        """
        pokemon_dir = "pokemons"
        pokemon_files = [f for f in os.listdir(pokemon_dir) if f.endswith(".txt")]

        with open(output_file, "w", encoding="utf-8") as summary_file:
            for file_name in pokemon_files:
                pokemon_name = file_name.replace(".txt", "").replace("_", " ")
                
                # Leer el contenido de cada archivo individual.
                with open(os.path.join(pokemon_dir, file_name), "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Escribir el contenido en el archivo resumen con formato.
                summary_file.write(f"{pokemon_name}\n{'=' * len(pokemon_name)}\n{content}\n\n")

        print(f"Resumen de Pokémon generado en {output_file}")




class SINE_rag(object):
    # Clase que implementa un sistema RAG (Retrieval-Augmented Generation) sencillo.
    # Utiliza embeddings para almacenar y recuperar información relevante basada en similitud semántica.
    
    # Modelos de vectores de embeddings y modelo de lenguaje
    EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'  # Modelo de embeddings utilizado para representar los textos como vectores.
    LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'   # Modelo de lenguaje utilizado para responder preguntas basadas en la información recuperada.
    
    # Base de datos vectorial donde se almacenan los fragmentos de texto y sus embeddings correspondientes.
    VECTOR_DB = []

    def __init__(self, dataset_file):
        """
        Constructor de la clase SINE_rag.
        Carga un conjunto de datos desde un archivo y lo almacena en la base de datos vectorial.
        
        :param dataset_file: Ruta del archivo que contiene los datos a cargar.
        """
        self.dataset = []
        self.load_dataset(dataset_file)
        
    def load_dataset(self, dataset_file):
        """
        Carga el contenido de un archivo en la variable dataset y lo almacena en la base de datos vectorial.
        
        :param dataset_file: Ruta del archivo que contiene los datos a cargar.
        """
        with open(dataset_file, 'r', encoding='utf-8') as file:
            self.dataset = file.readlines()  # Leer todas las líneas del archivo como una lista de strings.
            print(f'Loaded {len(self.dataset)} entries')
            
        # Procesar cada fragmento de texto y agregarlo a la base de datos.
        for i, chunk in enumerate(self.dataset):
            self.add_chunk_to_database(chunk)
            print(f'Added chunk {i+1}/{len(self.dataset)} to the database')
            
    def add_chunk_to_database(self, chunk):
        """
        Convierte un fragmento de texto en un embedding y lo almacena en la base de datos vectorial.
        
        :param chunk: Fragmento de texto a agregar.
        """
        embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=chunk)['embeddings'][0]  # Obtener el embedding del fragmento.
        self.VECTOR_DB.append((chunk, embedding))  # Guardar la tupla (texto, embedding).

    def cosine_similarity(self, a, b):
        """
        Calcula la similitud coseno entre dos vectores.
        
        :param a: Primer vector.
        :param b: Segundo vector.
        :return: Valor de similitud coseno entre los vectores a y b.
        """
        dot_product = sum([x * y for x, y in zip(a, b)])  # Producto punto de los dos vectores.
        norm_a = sum([x ** 2 for x in a]) ** 0.5  # Norma (magnitud) del primer vector.
        norm_b = sum([x ** 2 for x in b]) ** 0.5  # Norma (magnitud) del segundo vector.
        return dot_product / (norm_a * norm_b)  # Fórmula de similitud coseno.

    def retrieve_function(self, query, top_n=3):
        """
        Busca en la base de datos los fragmentos más relevantes en función de una consulta.
        
        :param query: Texto de la consulta.
        :param top_n: Número de fragmentos más relevantes a devolver.
        :return: Lista con los fragmentos más similares a la consulta.
        """
        query_embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=query)['embeddings'][0]  # Obtener embedding de la consulta.
        
        # Lista para almacenar las similitudes entre la consulta y cada fragmento en la base de datos.
        similarities = []
        for chunk, embedding in self.VECTOR_DB:
            similarity = self.cosine_similarity(query_embedding, embedding)  # Calcular similitud con cada fragmento.
            similarities.append((chunk, similarity))
        
        # Ordenar los fragmentos por similitud en orden descendente (mayor similitud primero).
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_n]  # Devolver los N fragmentos más relevantes.

    def ask_question(self, query, max_results_ranking):
        """
        Responde a una pregunta basada en los fragmentos más relevantes encontrados en la base de datos.
        
        :param query: Pregunta del usuario.
        :param max_results_ranking: Número de fragmentos relevantes a considerar en la respuesta.
        """
        retrieved_knowledge = self.retrieve_function(query, max_results_ranking)  # Recuperar información relevante.
        
        print('Retrieved knowledge:')
        for chunk, similarity in retrieved_knowledge:
            print(f' - (similarity: {similarity:.2f}) {chunk}')     
        
        # Crear el prompt con la información recuperada
        instruction_prompt = f"""Eres un chatbot útil. Usa solo las siguientes partes del contexto para responder la pregunta.  
        No inventes información nueva:  
        {chr(10).join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}""" 
        
        # Enviar la consulta al modelo de lenguaje con el contexto recuperado.
        stream = ollama.chat(
            model=self.LANGUAGE_MODEL,
            messages=[
                {'role': 'system', 'content': instruction_prompt},  # Mensaje del sistema con las instrucciones.
                {'role': 'user', 'content': query},  # Pregunta del usuario.
            ],
            stream=True,
        )
        
        # Mostrar la respuesta del chatbot en tiempo real.
        print('Respuesta del Chatbot:')
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)

def preguntar_pokemon():
    """
    Función que ejecuta un flujo de preguntas y respuestas sobre Pokémon.
    Utiliza un crawler para obtener información y un sistema RAG para responder preguntas.
    """
    url = "https://www.wikidex.net/wiki/Lista_de_Pok%C3%A9mon"
    
    # Crear una instancia del crawler para obtener la lista de Pokémon.
    crawler = SINE_crawler(max_pokemons=10)
    pokemon_names = crawler.download_pokemon_list(url)
    
    if pokemon_names:
        # Descargar información de los Pokémon y generar un resumen.
        crawler.download_pokemon_info() 
        crawler.generate_pokemon_summary()   
    
    # Crear una instancia del sistema RAG con los datos obtenidos.
    rag = SINE_rag("pokemons.txt")
    
    # Iniciar un bucle de preguntas y respuestas.
    while True:
        pregunta = input("Haz una pregunta sobre Pokémon (o escribe 'stop' para salir): ")
        if pregunta.lower() == "stop":
            print("Saliendo del bucle...")
            break
        respuesta = rag.ask_question(pregunta, max_results_ranking=10)
        print(respuesta)
        
# Ejecutar la función de preguntas sobre Pokémon.
preguntar_pokemon()




















