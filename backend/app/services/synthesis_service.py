import datetime
import os
import sys
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

# Ajustar path para importaciones del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_services import AzureServices


# Modelos para el endpoint de síntesis
class SynthesisRequest(BaseModel):
    query: str
    chunks: list[dict[str, Any]]


class SynthesisResponse(BaseModel):
    model: str
    synthesized_text: str


# ======================================================================================
#  PIPELINE DE SÍNTESIS FINAL
# ======================================================================================
class SynthesisCategoryChunks:
    def __init__(self):
        self.aoai_client = AzureServices.AzureOpenAI()
        self.search_client = AzureServices.AzureIASearch()

    def extract_year_from_docname(self, doc_name: str):
        """
        Extrae el año más reciente de un nombre de documento buscando cualquier año de los últimos 100.
        """
        if not doc_name:
            return None

        # 1. Genera una lista de años para buscar, del más reciente al más antiguo.
        current_year = datetime.datetime.now().year
        years_to_check = range(current_year, current_year - 100, -1)

        # 2. Itera y devuelve la primera coincidencia (que será la más reciente).
        for year in years_to_check:
            if str(year) in doc_name:
                return year

        # 3. Si el bucle termina sin encontrar un año, devuelve el texto.
        return "s.f."

    def prepare_chunks_for_synthesis(self, chunks: list[dict]) -> list[dict]:
        """
        Pre-procesa los chunks para generar etiquetas de cita APA y referencias completas.
        Esta es la función clave para asegurar citas consistentes.
        """
        prepared_chunks = []
        # Agrupamos por (autor, año) para asignar letras (a, b, c...)
        author_year_groups = defaultdict(list)

        for chunk in chunks:
            year = self.extract_year_from_docname(chunk.get("document_name", ""))
            author = chunk.get("folder", "Fuente Desconocida")  # 'folder' es la colección
            author_year_groups[(author, year)].append(chunk)

        # Asignamos las letras y creamos las etiquetas y referencias
        processed_ids = set()
        for (author, year), group_chunks in author_year_groups.items():
            use_letters = len(group_chunks) > 1
            for i, chunk in enumerate(group_chunks):
                letter = chr(ord("a") + i) if use_letters else ""

                # 1. Etiqueta de cita para el cuerpo del texto
                chunk["apa_citation_tag"] = f"({author}, {year}{letter})"

                # 2. Referencia completa para la bibliografía
                doc_title = chunk.get("document_name", "Título Desconocido").replace(".pdf", "")
                first_page = chunk.get("page_numbers", [0])[0]
                chunk["full_reference_string"] = f"{author}. ({year}{letter}). {doc_title}. [Página: {first_page}]."
                prepared_chunks.append(chunk)
                processed_ids.add(id(chunk))

        # Asegurarse de que no se haya perdido ningún chunk
        for chunk in chunks:
            if id(chunk) not in processed_ids:
                chunk["apa_citation_tag"] = f"({chunk.get('folder', 'Fuente Desconocida')}, 2024)"
                chunk["full_reference_string"] = "Referencia no pudo ser formateada."
                prepared_chunks.append(chunk)

        return prepared_chunks

    def format_references_for_prompt(self, prepared_chunks: list[dict]) -> str:
        """Formatea la lista de chunks pre-procesados en una cadena para el prompt del LLM."""
        references_str = ""
        for chunk in prepared_chunks:
            references_str += f"Etiqueta de Cita: {chunk['apa_citation_tag']}\n"
            references_str += f"Referencia Completa APA: {chunk['full_reference_string']}\n"
            # references_str += f"Clasificación: {chunk.get('categoria', 'N/A')}\n"
            references_str += f"Resumen LLM Previo: {chunk.get('resumen_llm', 'N/A')}\n"
            references_str += f'Contenido Original: "{chunk.get("content", "")}"\n'
            references_str += "---\n\n"
        return references_str

    def synthesis_pipeline_endpoint(self, query, chunks):
        """
        Orquestador que toma chunks clasificados y genera una síntesis académica unificada.
        """

        # --- Paso 1: Pre-procesar Chunks para generar citas APA ---
        print("📝 Pre-procesando chunks para generar citas APA...")
        prepared_chunks = self.prepare_chunks_for_synthesis(chunks)

        # --- Paso 2: Formatear el contexto para el prompt ---
        references_for_prompt = self.format_references_for_prompt(prepared_chunks)

        # --- Paso 3: Construir los Prompts Finales ---
        system_prompt = (
            "Eres un experto en redacción académica con conocimientos en formato APA. "
            "Integra múltiples resúmenes y produce un texto final unificado, estilo artículo científico, "
            "basado exclusivamente en estos chunks para responder a la pregunta. "
            "Prioriza el contenido de los chunks para construir la respuesta principal y usa los metadatos "
            "asociados para enriquecer y complementar. "
            "Utiliza tanto el contenido original de los chunks como sus resúmenes LLM para elaborar el texto. "
            "No te cierres a los resumenes LLM, si ves que no son correctos o puedes entender que en el contenido "
            "del chunk es mas coherente, tu puedes decidir si omitirlos o no. "
            "Cita cada idea usando la etiqueta de referencia pre-calculada (e.g., (Bloque Catatumbo, 2014a)). "
            "Al final del texto, crea una sección titulada 'Referencias Analizadas'. Para construir esta sección, "
            "**copia textualmente la 'Referencia Completa APA' de cada fuente y organízalas** listando las "
            "referencias completas que se te han proporcionado. \n\n"
        )

        user_prompt = (
            f"La pregunta original es: {query}\n\n"
            f"A continuación, se presenta la información de cada fuente:\n\n"
            f"{references_for_prompt}\n"
            "Elabora el texto final unificado y la sección de 'Referencias Analizadas' siguiendo todas las "
            "instrucciones al pie de la letra."
        )

        # --- Paso 4: Llamar al LLM para la Síntesis ---
        print("🤖 Llamando al LLM para la síntesis final...")
        try:
            llm_answer, model = self.aoai_client.model_response(user_prompt, system_prompt)
            return SynthesisResponse(model=model, synthesized_text=llm_answer)
        except Exception as e:
            print(f"❌ Error durante la síntesis con el LLM: {e}")


if __name__ == "__main__":
    query = "¿Qué argumentos presentó la defensa de Jorge Barney Veloza García en la apelación?"

    chunks = [
        {
            "chunk id": "33f6a04d3f4f0c0539c7e5c589d82f3f5a20cefb660f2c69d566af3cac149389",
            "content": '452. Contra la presente decisión procede el recurso de apelación ante la Sala Penal de Corte Suprema de Justicia. 453. En mérito de lo expuesto, la Sala de Justicia y Paz del Tribunal Superior del Distrito Judicial de Bogotá, administrando justicia en nombre de la República y por autoridad de la ley, RESUELVE: PRIMERO: Condenar a JOSE BARNEY VELOZA GARCÍA, conocido con el alias de "El Flaco", con Cédula de Ciudadanía número 7.842.982 de Cubarral 164 Tribunal Superior de Begeta Proceso 2006 80585 José Barnery Veloza García Homicidio en persona protegida y otros Meta, nació el 12 de septiembre de 1962 en Trujillo (Valle del Cauca) a la pena de QUINIENTOS TREINTA Y SIETE (537) meses de prisión y multa de SIETE MIL QUINIENTOS (7500) SALARIOS MINIMOS LEGALES MENSUALES VIGENTES, como autor del delito de concierto para delinquir agravado, autor de homicidio en persona protegida, coautor de hurto agravado en concurso homogéneo y sucesivo y autor y coautor de falsedad material de particular en documento público agravado por el uso, en concurso homogéneo, conforme a lo expuesto en la motivación de esta decisión. SEGUNDO: Condenar a JOSE BARNEY VELOZA GARCÍA a la pena accesoria de inhabilidad para el ejercicio de derechos y funciones públicas por un lapso de 20 años. TERCERO: Suspender al condenado JOSE BARNEY VELOZA GARCÍA la ejecución de la pena de prisión, y en su lugar imponer, la pena alternativa de prisión equivalente a ocho (8) años de prisión que se hará efectiva en el centro de reclusión en los términos y bajo las condiciones expuestas en la parte motiva. CUARTO. Condenar al postulado JOSE BARNEY VELOZA GARCÍA de manera solidaria con los demás integrantes del bloque Bananero de las Autodefensas Unidas de Colombia, al pago de los daños y perjuicios materiales y morales, ocasionados con el homicidio del señor José Adalberto Guerra Galván, en los montos y condiciones establecidos en la parte motiva de la providencia. QUINTO: ordenar, como medida de satisfacción que JOSE BARNEY VELOZA GARCÍA ofrezca disculpas públicas a los familiares del señor Jorge Adalberto Guerra Galván sin disminuir su responsabilidad o esgrimir justificaciones por el 165 Tribunal Superior de Begeta Sala de Justicia y Pax Proceso 2006 80585 José Barnery Veloza García Homicidio en persona protegida y otros hecho. Ello deberá realizarse en el marco de una conmemoración en la que el comandante del Bloque Bananero actúe de la misma manera por las agresiones y violaciones a los derechos humanos cometidos en esta región.',
            "page_numbers": [163, 164, 165],
            "folder": "Bloque Bananero",
            "document_name": "Sentencia-José-Barney-Veloza-García-2012.pdf",
            "hybrid_score": 0.0320020467042923,
            "reranker_score": 2.9031872749328613,
            "highlights": {
                "content": [
                    "SEGUNDO: Condenar a JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA a la pena accesoria de inhabilidad para el ejercicio de derechos y funciones públicas por un lapso de 20 años.",
                    "TERCERO: Suspender al condenado JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA la ejecución de la pena de prisión, y en su lugar imponer, la pena alternativa de prisión equivalente a ocho (8) años de prisión que se hará efectiva en el centro de reclusión en los términos y bajo las condiciones expuestas en la parte motiva.",
                    "Condenar al postulado JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA de manera solidaria con los demás integrantes del bloque Bananero de las Autodefensas Unidas de Colombia, al pago de los daños y perjuicios materiales y morales, ocasionados con el homicidio del señor José Adalberto Guerra Galván, en los montos y condiciones establecidos en la parte motiva de la providencia.",
                    "QUINTO: ordenar, como medida de satisfacción que JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA ofrezca disculpas públicas a los familiares del señor <em>Jorge</em> Adalberto Guerra Galván sin disminuir su responsabilidad o esgrimir justificaciones por el 165 Tribunal Superior de Begeta Sala de Justicia y Pax Proceso 2006 80585 José Barnery <em>Veloza</em> García Homicidio en persona protegida y otros hecho.",
                    "Ello deberá realizarse en el marco de una conmemoración en la que el comandante del Bloque Bananero actúe de la misma manera por las agresiones y violaciones a los derechos humanos cometidos en esta región.",
                ]
            },
            "content_highlighted": '452. Contra la presente decisión procede el recurso de apelación ante la Sala Penal de Corte Suprema de Justicia. 453. En mérito de lo expuesto, la Sala de Justicia y Paz del Tribunal Superior del Distrito Judicial de Bogotá, administrando justicia en nombre de la República y por autoridad de la ley, RESUELVE: PRIMERO: Condenar a JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA, conocido con el alias de "El Flaco", con Cédula de Ciudadanía número 7.842.982 de Cubarral 164 Tribunal Superior de Begeta Proceso 2006 80585 José Barnery <em>Veloza</em> García Homicidio en persona protegida y otros Meta, nació el 12 de septiembre de 1962 en Trujillo (Valle del Cauca) a la pena de QUINIENTOS TREINTA Y SIETE (537) meses de prisión y multa de SIETE MIL QUINIENTOS (7500) SALARIOS MINIMOS LEGALES MENSUALES VIGENTES, como autor del delito de concierto para delinquir agravado, autor de homicidio en persona protegida, coautor de hurto agravado en concurso homogéneo y sucesivo y autor y coautor de falsedad material de particular en documento público agravado por el uso, en concurso homogéneo, conforme a lo expuesto en la motivación de esta decisión. SEGUNDO: Condenar a JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA a la pena accesoria de inhabilidad para el ejercicio de derechos y funciones públicas por un lapso de 20 años. TERCERO: Suspender al condenado JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA la ejecución de la pena de prisión, y en su lugar imponer, la pena alternativa de prisión equivalente a ocho (8) años de prisión que se hará efectiva en el centro de reclusión en los términos y bajo las condiciones expuestas en la parte motiva. CUARTO. Condenar al postulado JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA de manera solidaria con los demás integrantes del bloque Bananero de las Autodefensas Unidas de Colombia, al pago de los daños y perjuicios materiales y morales, ocasionados con el homicidio del señor José Adalberto Guerra Galván, en los montos y condiciones establecidos en la parte motiva de la providencia. QUINTO: ordenar, como medida de satisfacción que JOSE <em>BARNEY</em> <em>VELOZA</em> GARCÍA ofrezca disculpas públicas a los familiares del señor <em>Jorge</em> Adalberto Guerra Galván sin disminuir su responsabilidad o esgrimir justificaciones por el 165 Tribunal Superior de Begeta Sala de Justicia y Pax Proceso 2006 80585 José Barnery <em>Veloza</em> García Homicidio en persona protegida y otros hecho. Ello deberá realizarse en el marco de una conmemoración en la que el comandante del Bloque Bananero actúe de la misma manera por las agresiones y violaciones a los derechos humanos cometidos en esta región.',
            "categoria": "No Relevante",
            "resumen_llm": "El fragmento describe la sentencia condenatoria contra JOSE BARNEY VELOZA GARCÍA, incluyendo los delitos imputados, las penas impuestas y algunas medidas accesorias, pero no menciona ni aborda los argumentos presentados por la defensa en la apelación. No hay información sobre la apelación ni sobre los fundamentos de la defensa.",
        },
        {
            "chunk id": "e58c55cfbdb65744d6ee51d9363d26b18a0c2b62d3d8ea30fcf5b56a3e9c1e42",
            "content": "En tercer lugar, el impugnante señala que la sentencia de primera instancia incurrió en error, al desconocer la obligatoriedad de la acumulación jurídica de penas que debía ser realizada en la sentencia. Por último, el impugnante manifiesta no estar de acuerdo con el monto de la pena alternativa impuesta, al considerarla excesiva, por ser esta igual a la de otros postulados de la Ley 975 que en su parecer cometieron delitos más graves, y no conforme con lo dispuesto en el artículo 29 de la Ley 975 y 8º del Decreto Reglamentario 4760 de 2005, toda vez que, el Tribunal confundió los requisitos exigidos para conceder la pena alternativa. Consideraciones Segunda instancia 38381 Jorge Barney Veloza García Justicia y Paz República de Colombia Corte Suprema de Justicia Frente al primer aspecto de la impugnación le asiste razón al apelante en tanto se aplicó una norma posterior a los actos por los cuales se impuso la condena, esto es, los artículos 31 y 37 de la Ley 599 de 2000, aumentados por la Ley 890 de 2004, para situaciones posteriores a su entrada en vigencia. Por tanto, la pena de prisión se reducirá a la de cuarenta años de privación de la libertad, con lo cual además se supera la confusión aludida. Frente a la queja del impugnante según la cual se omitió la acumulación de la sentencia impuesta a JORGE BARNEY VELOZA GARCÍA por el Juzgado Penal del Circuito de Cáqueza, también se accederá, en cumplimiento de lo dispuesto en el artículo 20 de la Ley 975 de 2005. En efecto, el inciso segundo de dicho precepto prevé que cuando el desmovilizado haya sido previamente condenado por hechos delictivos cometidos durante y con ocasión de su pertenencia a un grupo armado organizado al margen de República de Colombia Corte Suprema de Justicia la ley, se tendrá en cuenta lo dispuesto en el Código Penal sobre acumulación jurídica de penas. Mediante sentencia proferida el 4 de agosto de 1999 el Juzgado Penal del Circuito de Cáqueza condenó a JORGE BARNEY VELOZA GARCÍA -y a William Rentería- por el homicidio agravado de José Heber Pulgarín Marulanda en concurso con hurto calificado y agravado y porte ilegal de armas de defensa personal, a una pena de 42 años y seis meses de prisión -según se aprecia en la sentencia que obra en el proceso -. En efecto, aplicando el principio de favorabilidad de raigambre constitucional, y en acatamiento de la norma favorable vigente, esto es, el artículo 31 de la Ley 599 de 2000, se acumula la condena en mención con la impuesta en este proceso transicional, a una pena final de cuarenta años de prisión; y en este sentido se modificará la parte resolutiva del fallo apelado. La queja del apelante según la cual la pena alternativa de ocho años no responde a la gravedad de las conductas cometidas por VELOZA GARCÍA carece de cualquier posibilidad de éxito, por cuanto se trata de dos homicidios, Segunda instancia 38381 Jorge Barney Veloza García Justicia y Paz República de Colombia Corte Suprema de Justicia de una pena que de no ser por las normas que limitan la acumulación jurídica de penas, oscilaría en ochenta años de prisión; pero sobre todo atentatorias del orden jurídico y de la convivencia pacífica, en tales niveles de intensidad que el solo reclamo en torno de la pena alternativa ofende la generosidad con que la Ley 975 de 2005 atendió situaciones como las que aquí se evalúan. Por lo tanto, esta inconformidad no será atendida.",
            "page_numbers": [11, 12, 13, 14],
            "folder": "Bloque Bananero",
            "document_name": "Sentencia-Jorge-Barney-Veloza-García.pdf",
            "hybrid_score": 0.0314980149269104,
            "reranker_score": 2.8868818283081055,
            "highlights": {
                "content": [
                    "En tercer lugar, el impugnante señala que la sentencia de primera instancia incurrió en error, al desconocer la obligatoriedad de la acumulación jurídica de penas que debía ser realizada en la sentencia.",
                    "Consideraciones Segunda instancia 38381 <em>Jorge</em> <em>Barney</em> <em>Veloza</em> García Justicia y Paz República de Colombia Corte Suprema de Justicia Frente al primer aspecto de la impugnación le asiste razón al apelante en tanto se aplicó una norma posterior a los actos por los cuales se impuso la condena, esto es, los artículos 31 y 37 de la Ley 599 de 2000, aumentados por la Ley 890 de 2004, para situaciones posteriores a su entrada en vigencia.",
                    "Frente a la queja del impugnante según la cual se omitió la acumulación de la sentencia impuesta a <em>JORGE</em> <em>BARNEY</em> <em>VELOZA</em> GARCÍA por el Juzgado Penal del Circuito de Cáqueza, también se accederá, en cumplimiento de lo dispuesto en el artículo 20 de la Ley 975 de 2005.",
                    "Mediante sentencia proferida el 4 de agosto de 1999 el Juzgado Penal del Circuito de Cáqueza condenó a <em>JORGE</em> <em>BARNEY</em> <em>VELOZA</em> GARCÍA -y a William Rentería- por el homicidio agravado de José Heber Pulgarín Marulanda en concurso con hurto calificado y agravado y porte ilegal de armas de <em>defensa</em> personal, a una pena de 42 años y seis meses de prisión -según se aprecia en la sentencia que obra en el proceso -.",
                    "La queja del apelante según la cual la pena alternativa de ocho años no responde a la gravedad de las conductas cometidas por <em>VELOZA</em> GARCÍA carece de cualquier posibilidad de éxito, por cuanto se trata de dos homicidios, Segunda instancia 38381 <em>Jorge</em> <em>Barney</em> <em>Veloza</em> García Justicia y Paz República de Colombia Corte Suprema de Justicia de una pena que de no ser por las normas que limitan la acumulación jurídica de penas, oscilaría en ochenta años de prisión; pero sobre todo atentatorias del orden jurídico y de la convivencia pacífica, en tales niveles de intensidad que el solo reclamo en torno de la pena alternativa ofende la generosidad con que la Ley 975 de 2005 atendió situaciones como las que aquí se evalúan.",
                ]
            },
            "content_highlighted": "En tercer lugar, el impugnante señala que la sentencia de primera instancia incurrió en error, al desconocer la obligatoriedad de la acumulación jurídica de penas que debía ser realizada en la sentencia. Por último, el impugnante manifiesta no estar de acuerdo con el monto de la pena alternativa impuesta, al considerarla excesiva, por ser esta igual a la de otros postulados de la Ley 975 que en su parecer cometieron delitos más graves, y no conforme con lo dispuesto en el artículo 29 de la Ley 975 y 8º del Decreto Reglamentario 4760 de 2005, toda vez que, el Tribunal confundió los requisitos exigidos para conceder la pena alternativa. Consideraciones Segunda instancia 38381 <em>Jorge</em> <em>Barney</em> <em>Veloza</em> García Justicia y Paz República de Colombia Corte Suprema de Justicia Frente al primer aspecto de la impugnación le asiste razón al apelante en tanto se aplicó una norma posterior a los actos por los cuales se impuso la condena, esto es, los artículos 31 y 37 de la Ley 599 de 2000, aumentados por la Ley 890 de 2004, para situaciones posteriores a su entrada en vigencia. Por tanto, la pena de prisión se reducirá a la de cuarenta años de privación de la libertad, con lo cual además se supera la confusión aludida. Frente a la queja del impugnante según la cual se omitió la acumulación de la sentencia impuesta a <em>JORGE</em> <em>BARNEY</em> <em>VELOZA</em> GARCÍA por el Juzgado Penal del Circuito de Cáqueza, también se accederá, en cumplimiento de lo dispuesto en el artículo 20 de la Ley 975 de 2005. En efecto, el inciso segundo de dicho precepto prevé que cuando el desmovilizado haya sido previamente condenado por hechos delictivos cometidos durante y con ocasión de su pertenencia a un grupo armado organizado al margen de República de Colombia Corte Suprema de Justicia la ley, se tendrá en cuenta lo dispuesto en el Código Penal sobre acumulación jurídica de penas. Mediante sentencia proferida el 4 de agosto de 1999 el Juzgado Penal del Circuito de Cáqueza condenó a <em>JORGE</em> <em>BARNEY</em> <em>VELOZA</em> GARCÍA -y a William Rentería- por el homicidio agravado de José Heber Pulgarín Marulanda en concurso con hurto calificado y agravado y porte ilegal de armas de <em>defensa</em> personal, a una pena de 42 años y seis meses de prisión -según se aprecia en la sentencia que obra en el proceso -. En efecto, aplicando el principio de favorabilidad de raigambre constitucional, y en acatamiento de la norma favorable vigente, esto es, el artículo 31 de la Ley 599 de 2000, se acumula la condena en mención con la impuesta en este proceso transicional, a una pena final de cuarenta años de prisión; y en este sentido se modificará la parte resolutiva del fallo apelado. La queja del apelante según la cual la pena alternativa de ocho años no responde a la gravedad de las conductas cometidas por <em>VELOZA</em> GARCÍA carece de cualquier posibilidad de éxito, por cuanto se trata de dos homicidios, Segunda instancia 38381 <em>Jorge</em> <em>Barney</em> <em>Veloza</em> García Justicia y Paz República de Colombia Corte Suprema de Justicia de una pena que de no ser por las normas que limitan la acumulación jurídica de penas, oscilaría en ochenta años de prisión; pero sobre todo atentatorias del orden jurídico y de la convivencia pacífica, en tales niveles de intensidad que el solo reclamo en torno de la pena alternativa ofende la generosidad con que la Ley 975 de 2005 atendió situaciones como las que aquí se evalúan. Por lo tanto, esta inconformidad no será atendida.",
            "categoria": "Relevante",
            "resumen_llm": "El fragmento aborda explícitamente los argumentos presentados por la defensa de Jorge Barney Veloza García en la apelación, incluyendo la queja sobre la no acumulación jurídica de penas y la inconformidad con el monto de la pena alternativa impuesta. Se menciona el nombre completo de Jorge Barney Veloza García y se detallan los fundamentos jurídicos y hechos específicos relacionados con su caso, como la condena previa y los delitos cometidos. Por tanto, el contenido es directamente relevante para la consulta.",
        },
        {
            "chunk id": "60993c43453c59ae6084fd0e2e4063a917d368e17511e96f094d2a9ab5be7c81",
            "content": 'República de Colombia Corte Suprema de Justicia CORTE SUPREMA DE JUSTICIA SALA DE CASACIÓN PENAL Magistrado Ponente JOSÉ LEONIDAS BUSTOS MARTÍNEZ Aprobado acta Nº 458 Bogotá D.C., doce de diciembre de dos mil doce VISTOS La Corte resuelve el recurso de apelación interpuesto contra la sentencia proferida por una Sala de Conocimiento de Justicia y Paz del Tribunal Superior de Bogotá, mediante la cual condenó al desmovilizado JOSÉ BARNEY VELOZA GARCÍA, por los delitos de concierto para delinquir agravado en concurso con homicidio en persona protegida - de Jorge Alberto Guerra Galván-, hurto agravado -de hidrocarburos- y falsedad material de particular en documento público -toda vez que al momento de su captura se identificó con una cédula de ciudadanía confeccionada para su uso -. República de Colombia Corte Suprema de Justicia ANTECEDENTES PROCESALES El señor JOSÉ BARNEY VELOZA GARCÍA, alias "El Flaco", ingresó a las Autodefensas Unidas de Colombia en enero de 1995, de donde se desmovilizó el 25 de noviembre de 2004, junto con el Bloque Bananero, luego de haber hecho parte también de los Bloques Calima y Centauros. Después de adelantarse los trámites y exigencias legales correspondientes, VELOZA GARCÍA fue escuchado en versión libre los días 18 y 19 de octubre de 2007, 21 de abril, y 14 y 15 de octubre de 2008; en desarrollo de la cual confesó varios hechos, lo que condujo a que le fuera impuesta medida de aseguramiento de detención preventiva en establecimiento carcelario, por parte del Magistrado con función de Control de Garantías de la Sala de Justicia y Paz del Tribunal Superior de Medellín.',
            "page_numbers": [1, 2],
            "folder": "Bloque Bananero",
            "document_name": "Sentencia-Jorge-Barney-Veloza-García.pdf",
            "hybrid_score": 0.031054403632879257,
            "reranker_score": 2.6323728561401367,
            "highlights": {
                "content": [
                    "República de Colombia Corte Suprema de Justicia CORTE SUPREMA DE JUSTICIA SALA DE CASACIÓN PENAL Magistrado Ponente JOSÉ LEONIDAS BUSTOS MARTÍNEZ Aprobado acta Nº 458 Bogotá D.C., doce de diciembre de dos mil doce VISTOS La Corte resuelve el recurso de apelación interpuesto contra la sentencia proferida por una Sala de Conocimiento de Justicia y Paz del Tribunal Superior de Bogotá, mediante la cual condenó al desmovilizado JOSÉ <em>BARNEY</em> <em>VELOZA</em> GARCÍA, por los delitos de concierto para delinquir agravado en concurso con homicidio en persona protegida - de <em>Jorge</em> Alberto Guerra Galván-, hurto agravado -de hidrocarburos- y falsedad material de particular en documento público -toda vez que al momento de su captura se identificó con una cédula de ciudadanía confeccionada para su uso -.",
                    'República de Colombia Corte Suprema de Justicia ANTECEDENTES PROCESALES El señor JOSÉ <em>BARNEY</em> <em>VELOZA</em> GARCÍA, alias "El Flaco", ingresó a las Autodefensas Unidas de Colombia en enero de 1995, de donde se desmovilizó el 25 de noviembre de 2004, junto con el Bloque Bananero, luego de haber hecho parte también de los Bloques Calima y Centauros.',
                    "Después de adelantarse los trámites y exigencias legales correspondientes, <em>VELOZA</em> GARCÍA fue escuchado en versión libre los días 18 y 19 de octubre de 2007, 21 de abril, y 14 y 15 de octubre de 2008; en desarrollo de la cual confesó varios hechos, lo que condujo a que le fuera impuesta medida de aseguramiento de detención preventiva en establecimiento carcelario, por parte del Magistrado con función de Control de Garantías de la Sala de Justicia y Paz del Tribunal Superior de Medellín.",
                ]
            },
            "content_highlighted": 'República de Colombia Corte Suprema de Justicia CORTE SUPREMA DE JUSTICIA SALA DE CASACIÓN PENAL Magistrado Ponente JOSÉ LEONIDAS BUSTOS MARTÍNEZ Aprobado acta Nº 458 Bogotá D.C., doce de diciembre de dos mil doce VISTOS La Corte resuelve el recurso de apelación interpuesto contra la sentencia proferida por una Sala de Conocimiento de Justicia y Paz del Tribunal Superior de Bogotá, mediante la cual condenó al desmovilizado JOSÉ <em>BARNEY</em> <em>VELOZA</em> GARCÍA, por los delitos de concierto para delinquir agravado en concurso con homicidio en persona protegida - de <em>Jorge</em> Alberto Guerra Galván-, hurto agravado -de hidrocarburos- y falsedad material de particular en documento público -toda vez que al momento de su captura se identificó con una cédula de ciudadanía confeccionada para su uso -. República de Colombia Corte Suprema de Justicia ANTECEDENTES PROCESALES El señor JOSÉ <em>BARNEY</em> <em>VELOZA</em> GARCÍA, alias "El Flaco", ingresó a las Autodefensas Unidas de Colombia en enero de 1995, de donde se desmovilizó el 25 de noviembre de 2004, junto con el Bloque Bananero, luego de haber hecho parte también de los Bloques Calima y Centauros. Después de adelantarse los trámites y exigencias legales correspondientes, <em>VELOZA</em> GARCÍA fue escuchado en versión libre los días 18 y 19 de octubre de 2007, 21 de abril, y 14 y 15 de octubre de 2008; en desarrollo de la cual confesó varios hechos, lo que condujo a que le fuera impuesta medida de aseguramiento de detención preventiva en establecimiento carcelario, por parte del Magistrado con función de Control de Garantías de la Sala de Justicia y Paz del Tribunal Superior de Medellín.',
            "categoria": "No Relevante",
            "resumen_llm": "El fragmento describe el contexto procesal y los delitos imputados a JOSÉ BARNEY VELOZA GARCÍA, así como su ingreso y desmovilización de las Autodefensas Unidas de Colombia y su confesión en versión libre. Sin embargo, no menciona ni aborda los argumentos presentados por la defensa en la apelación, que es el tema específico de la consulta.",
        },
    ]

    # Iniciar el pipeline
    synthesis_category_chunks = SynthesisCategoryChunks()
    final_response = synthesis_category_chunks.synthesis_pipeline_endpoint(query, chunks)

    print(final_response)
