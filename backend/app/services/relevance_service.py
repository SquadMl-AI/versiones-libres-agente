# backend/app/services/relevance_service.py
import concurrent.futures

import numpy as np

from app.model_handlers import summarize_chunk_streaming


def _build_chunk_info(chunk):
    """Construye un diccionario con la información de un chunk para el análisis."""
    return {
        "dataset_name": chunk.get("dataset_name", "Sin Colección"),
        "document_name": chunk.get("document_name", "Sin Documento"),
        "page": chunk.get("page", "N/A"),
        "chunk_id": chunk.get("id", "Sin ID"),
        "score": chunk.get("score", "N/A"),
        "content": chunk.get("content", "Sin contenido")
    }


def _evaluate_interval_relevance(interval, user_query, provider):
    """
    Evalúa si al menos un chunk del intervalo es relevante.
    Retorna True si se encontró algún relevante, False en caso contrario.
    """
    # Tomar hasta los 2 primeros chunks con mayor score
    chunks_to_evaluate = sorted(interval, key=lambda x: x["score"], reverse=True)[:min(2, len(interval))]
    chunk_infos = [_build_chunk_info(chunk) for chunk in chunks_to_evaluate]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk = {
            executor.submit(summarize_chunk_streaming, chunk_info, user_query, provider): chunk_info
            for chunk_info in chunk_infos
        }
        for future in concurrent.futures.as_completed(future_to_chunk):
            try:
                _, classification = future.result()
                if classification == "Relevante":
                    return True
            except Exception as exc:
                # st.error(f"Error al analizar chunk: {exc}")
                print(f"Error al analizar chunk: {exc}")
    return False


def _detailed_analysis(interval, user_query, provider):
    """Analiza todos los chunks de un intervalo para determinar el score mínimo relevante."""
    chunk_infos = [_build_chunk_info(chunk) for chunk in interval]
    relevant_scores = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chunk = {
            executor.submit(summarize_chunk_streaming, chunk_info, user_query, provider): chunk_info
            for chunk_info in chunk_infos
        }
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_info = future_to_chunk[future]
            try:
                _, classification = future.result()
                if classification == "Relevante":
                    relevant_scores.append(chunk_info['score'])
                    print(f"Chunk relevante encontrado con score {chunk_info['score']:.2f}.")
            except Exception as exc:
                print(f"Error al analizar chunk: {exc}")

    if relevant_scores:
        min_relevant_score = min(relevant_scores)
        print(f"Se encontró un score mínimo relevante de {min_relevant_score:.2f} tras analizar todos los chunks.")
    else:
        min_relevant_score = interval[-1]['score']
        print(f"No se encontraron chunks relevantes en el análisis detallado. "
              f"Usando score mínimo del intervalo: {min_relevant_score:.2f}.")
    return min_relevant_score


def determine_dynamic_page_limit(chunks, user_query, max_bins=10, provider="Azure OpenAI (o3-mini)"):
    """
    Determina el límite dinámico de chunks relevantes basado en análisis de relevancia.
    """
    if not chunks:
        msg = "No hay chunks para analizar."
        print(msg)
        # st.warning(msg)
        return chunks, []

    # Ordenar los chunks por score de mayor a menor
    sorted_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
    scores = [chunk["score"] for chunk in sorted_chunks]
    if not scores:
        msg = "No se encontraron puntajes válidos en los chunks."
        print(msg)
        # st.warning(msg)
        return sorted_chunks, []

    print(f"Total de chunks: {len(sorted_chunks)}")
    print(f"Rango de puntajes: {min(scores):.2f} a {max(scores):.2f}")

    # Definir exactamente 10 intervalos si hay al menos 10 chunks, o uno por chunk si hay menos
    num_intervals = 10 if len(sorted_chunks) >= 10 else len(sorted_chunks)
    score_boundaries = np.linspace(min(scores), max(scores), num_intervals + 1)
    intervals = []
    for i in range(len(score_boundaries) - 1):
        lower_bound = score_boundaries[i]
        upper_bound = score_boundaries[i + 1]
        interval_chunks = [
            chunk for chunk in sorted_chunks if lower_bound <= chunk["score"] < upper_bound
        ]
        if i == len(score_boundaries) - 2:  # Último intervalo incluye el máximo
            interval_chunks = [
                chunk for chunk in sorted_chunks if lower_bound <= chunk["score"] <= upper_bound
            ]
        intervals.append(interval_chunks)

    # Filtrar intervalos vacíos y ordenar de mayor a menor
    intervals = [interval for interval in intervals if interval]
    intervals = intervals[::-1]  # Invertir para analizar de mayor a menor

    print("Intervalos (ordenados de mayor a menor puntaje, exactamente 10):")
    for i, interval in enumerate(intervals):
        print(f"Intervalo {i+1}: [{interval[0]['score']:.2f}, {interval[-1]['score']:.2f}] "
              f"- {len(interval)} chunks")

    last_relevant_interval = None
    for idx, interval in enumerate(intervals):
        print(f"Analizando intervalo {idx + 1} de {len(intervals)} "
              f"(puntajes de {interval[0]['score']:.2f} a {interval[-1]['score']:.2f})...")
        print(f"El intervalo tiene {len(interval)} chunks. Evaluando relevancia en paralelo (máximo 2 chunks)...")

        relevant_in_interval = _evaluate_interval_relevance(interval, user_query, provider)

        if relevant_in_interval:
            last_relevant_interval = idx
            print(f"Se encontró un chunk relevante en el intervalo {idx + 1} con score "
                  f"{interval[0]['score']:.2f}.")
        else:
            print(f"No se encontraron chunks relevantes en el intervalo {idx + 1}. Deteniendo el análisis.")
            break

    if last_relevant_interval is None:
        msg = "No se encontraron chunks relevantes en ningún intervalo. Retornando el 10% superior de los chunks."
        print(msg)
        # st.warning(msg)
        cutoff = int(len(sorted_chunks) * 0.1)  # 10% superior
        filtered_chunks = sorted_chunks[:cutoff]
        print(f"Se seleccionaron {len(filtered_chunks)} chunks con puntaje >= "
              f"{filtered_chunks[-1]['score']:.2f}.")
        return filtered_chunks, score_boundaries

    # Análisis detallado del último intervalo relevante
    last_interval = intervals[last_relevant_interval]
    print(f"Último intervalo relevante (índice {last_relevant_interval + 1}) tiene "
          f"{len(last_interval)} chunks. Iniciando análisis detallado...")

    if len(last_interval) <= 20:
        min_relevant_score = _detailed_analysis(last_interval, user_query, provider)
    else:
        # Dividir en subintervalos y repetir el proceso
        sub_num_intervals = 10 if len(last_interval) >= 10 else len(last_interval)
        sub_score_boundaries = np.linspace(
            min([chunk['score'] for chunk in last_interval]),
            max([chunk['score'] for chunk in last_interval]),
            sub_num_intervals + 1
        )
        sub_intervals = []
        for i in range(len(sub_score_boundaries) - 1):
            lower_bound = sub_score_boundaries[i]
            upper_bound = sub_score_boundaries[i + 1]
            sub_interval_chunks = [
                chunk for chunk in last_interval if lower_bound <= chunk["score"] < upper_bound
            ]
            if i == len(sub_score_boundaries) - 2:
                sub_interval_chunks = [
                    chunk for chunk in last_interval if lower_bound <= chunk["score"] <= upper_bound
                ]
            sub_intervals.append(sub_interval_chunks)

        sub_intervals = [interval for interval in sub_intervals if interval]
        sub_intervals = sub_intervals[::-1]

        last_sub_relevant_interval = None
        for sub_idx, sub_interval in enumerate(sub_intervals):
            print(f"Analizando subintervalo {sub_idx + 1} de {len(sub_intervals)} "
                  f"(puntajes de {sub_interval[0]['score']:.2f} a {sub_interval[-1]['score']:.2f})...")
            sub_relevant = _evaluate_interval_relevance(sub_interval, user_query, provider)
            if sub_relevant:
                last_sub_relevant_interval = sub_idx
                print(f"Se encontró un chunk relevante en el subintervalo {sub_idx + 1} con score "
                      f"{sub_interval[0]['score']:.2f}.")
            else:
                print(f"No se encontraron chunks relevantes en el subintervalo {sub_idx + 1}. "
                      "Deteniendo análisis de subintervalos.")
                break

        if last_sub_relevant_interval is not None:
            last_sub_interval = sub_intervals[last_sub_relevant_interval]
            print(f"Último subintervalo relevante (índice {last_sub_relevant_interval + 1}) tiene "
                  f"{len(last_sub_interval)} chunks. Analizando todos los chunks en paralelo...")
            min_relevant_score = _detailed_analysis(last_sub_interval, user_query, provider)
        else:
            min_relevant_score = last_interval[-1]['score']
            print(f"No se encontraron subintervalos relevantes. Usando score mínimo del intervalo: "
                  f"{min_relevant_score:.2f}.")

    # Filtrar los chunks finales usando el score mínimo relevante
    filtered_chunks = [chunk for chunk in sorted_chunks if chunk["score"] >= min_relevant_score]
    print(f"Se determinó un page_limit dinámico de {len(filtered_chunks)} chunks con puntaje >= "
          f"{min_relevant_score:.2f}.")
    return filtered_chunks, score_boundaries
