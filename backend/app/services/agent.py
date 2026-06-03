import pandas as pd
import chromadb
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.services.tech_knowledge import get_tech_kb

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

PROJECT_DIR = Path(__file__).resolve().parents[3]
CHROMA_DIR = PROJECT_DIR / "data" / "chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    return _embedding_model


def _build_query_text(tecnologia: str, experiencia_minima: int) -> str:
    return (
        f"Candidate resume for {tecnologia}. "
        f"Technical stack: {tecnologia}. "
        f"Minimum experience: {experiencia_minima} years."
    )


def _buscar_indices_en_chroma(
    tecnologia: str,
    experiencia_minima: int,
    total_candidatos: int,
    n_results: int,
) -> tuple[list[int], dict[int, float]]:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name="candidates", embedding_function=None)

    query_text = _build_query_text(tecnologia, experiencia_minima)
    query_embedding = _get_embedding_model().encode([query_text], convert_to_numpy=True)[0]

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=min(n_results, total_candidatos),
        include=["distances", "metadatas"],
    )

    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    indices = []
    similarities = {}
    for position, candidate_id in enumerate(ids):
        metadata = metadatas[position] if position < len(metadatas) else {}
        raw_index = metadata.get("index") if isinstance(metadata, dict) else None
        if raw_index is None and isinstance(candidate_id, str) and candidate_id.startswith("cand_"):
            raw_index = candidate_id.split("_", 1)[1]

        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            continue

        if 0 <= index < total_candidatos:
            distance = float(distances[position]) if position < len(distances) else 1.0
            indices.append(index)
            similarities[index] = max(0.0, 1.0 - distance)

    return indices, similarities


def evaluar_talento_it(
    df: pd.DataFrame,
    tecnologia: str,
    sueldo_maximo: float,
    experiencia_minima: int,
) -> pd.DataFrame:
    """
    Puntúa candidatos IT con comprensión semántica de tecnologías.
    
    Utiliza ChromaDB para entender relaciones entre tecnologías:
    - React ≈ Next.js (match 0.95)
    - JavaScript ≈ TypeScript (match 0.85)
    - Usa embeddings precomputados (sin recalcular en cada query)
    """
    df_evaluado = df.copy()
    scores = []
    match_tecnico_porcentaje = []
    ajuste_salarial_porcentaje = []
    juicios = []
    justificaciones = []
    
    try:
        tech_kb = get_tech_kb()
    except Exception as exc:
        print(f"Tech knowledge unavailable: {exc}. Using lexical/vector fallback.")
        tech_kb = None

    for idx, row in df_evaluado.iterrows():
        # --- MATCHING TÉCNICO SEMÁNTICO ---
        resume_texto = " ".join(
            [
                str(row.get("Resume", "")),
                str(row.get("Job Roles", "")),
                str(row.get("Job Description", "")),
            ]
        )
        
        if tech_kb is not None:
            try:
                similitud_semantica, razon_tecnica = tech_kb.calculate_semantic_match(
                    cv_text=resume_texto,
                    required_tech=tecnologia,
                    threshold=0.6
                )
            except Exception as exc:
                similitud_semantica = 0.0
                razon_tecnica = f"base semantica no disponible ({exc})"
        else:
            similitud_semantica = 0.0
            razon_tecnica = "base semantica no disponible"

        texto_normalizado = resume_texto.lower()
        tecnologia_normalizada = tecnologia.lower().strip()
        vector_similarity = float(row.get("VectorSimilarity", 0) or 0) / 100

        if tecnologia_normalizada and tecnologia_normalizada in texto_normalizado:
            similitud_semantica = 1.0
            razon_tecnica = f"match exacto: {tecnologia} aparece en el perfil del candidato"
        elif vector_similarity >= 0.5 and vector_similarity > similitud_semantica:
            similitud_semantica = vector_similarity
            razon_tecnica = f"match vectorial con el perfil del candidato ({vector_similarity*100:.0f}% similar)"
        
        # Convertir similitud (0-1) a score (0-40)
        match_tecnico_score = int(similitud_semantica * 40)
        
        # Bonus por experiencia
        años_cand = row.get("años de experiencia", 0)
        if años_cand >= experiencia_minima:
            match_tecnico_score += 20
        elif experiencia_minima > 0:
            match_tecnico_score += int((años_cand / experiencia_minima) * 20)

        # --- MATCHING ECONÓMICO (sin cambios) ---
        match_economico_score = 0
        sueldo_cand = row.get("sueldo pretendido", 0)

        if sueldo_cand <= sueldo_maximo:
            match_economico_score = 40
        else:
            exceso = (sueldo_cand - sueldo_maximo) / sueldo_maximo
            if exceso <= 0.15:
                match_economico_score = int(40 * (1 - (exceso / 0.15)))

        score_total = match_tecnico_score + match_economico_score
        match_tecnico_porcentaje.append(round((match_tecnico_score / 60) * 100))
        ajuste_salarial_porcentaje.append(round((match_economico_score / 40) * 100))

        # --- JUICIO Y JUSTIFICACIÓN ---
        if score_total >= 80 and similitud_semantica >= 0.7:
            juicio = "Recomendar"
        elif score_total >= 55:
            juicio = "Evaluar"
        else:
            juicio = "Descartar"

        detalles = []
        
        # Explicación técnica semántica
        detalles.append(f"Match semantico: {razon_tecnica}")
        detalles.append(f"Similitud tecnica: {similitud_semantica*100:.0f}%")
        
        # Experiencia
        if años_cand >= experiencia_minima:
            detalles.append(f"OK Experiencia: {años_cand} años (requería {experiencia_minima})")
        else:
            detalles.append(f"Atencion Experiencia: {años_cand} años (requería {experiencia_minima})")

        # Sueldo
        if row.get("sueldo_estimado_por_IA") is True:
            detalles.append(
                f"Salario estimado: ${sueldo_cand:,.0f} (presupuesto: ${sueldo_maximo:,.0f}) - IA estimó"
            )
        elif sueldo_cand <= sueldo_maximo:
            detalles.append(f"OK Salario: ${sueldo_cand:,.0f} (presupuesto: ${sueldo_maximo:,.0f})")
        else:
            diferencia = sueldo_cand - sueldo_maximo
            detalles.append(f"Atencion Salario: ${sueldo_cand:,.0f} (excede ${diferencia:,.0f})")

        scores.append(score_total)
        juicios.append(juicio)
        justificaciones.append("\n".join(detalles))

    df_evaluado["Score"] = scores
    df_evaluado["MatchTecnico"] = match_tecnico_porcentaje
    df_evaluado["AjusteSalarial"] = ajuste_salarial_porcentaje
    df_evaluado["Juicio"] = juicios
    df_evaluado["Justificacion"] = justificaciones
    return df_evaluado


def _obtener_top_candidatos_legacy(
    df: pd.DataFrame,
    tecnologia: str,
    sueldo_maximo: float,
    experiencia_minima: int,
    top_n: int = 10,
) -> list:
    """
    OPTIMIZADO: Usa ChromaDB para búsqueda semántica rápida (v2).
    
    Estrategia:
    1. Consulta ChromaDB para obtener 50 candidatos similares (~300ms)
    2. Evalúa solo esos 50 (~2.2s)
    3. Ordena y devuelve top_n
    
    Total esperado: ~2.5-3s en lugar de 40s
    """
    # 1. Consulta ChromaDB para obtener candidatos similares
    try:
        client = chromadb.PersistentClient(path="./data/chroma_db")
        collection = client.get_collection(name="candidates")
        
        # Construir query: tecnología + experiencia + sueldo
        query_text = f"{tecnologia} {experiencia_minima} years experience ${sueldo_maximo}"
        
        # Buscar top 50 candidatos similares (filtro inicial muy rápido)
        results = collection.query(
            query_texts=[query_text],
            n_results=min(50, len(df)),  # ← OPTIMIZADO: 50 en lugar de 100
            where=None
        )
        
        if not results["ids"] or not results["ids"][0]:
            # Fallback: si ChromaDB no devuelve resultados, procesar todos
            df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
            top_df = df_procesado.sort_values(by="Score", ascending=False).head(top_n)
            return top_df.to_dict(orient="records")
        
        # 2. Extraer IDs de ChromaDB (formato: "cand_0", "cand_1", etc.)
        candidate_ids = [int(cid.split("_")[1]) for cid in results["ids"][0]]
        
        # 3. Evaluar solo los candidatos recuperados
        df_subset = df.iloc[candidate_ids].copy()
        df_evaluado = evaluar_talento_it(df_subset, tecnologia, sueldo_maximo, experiencia_minima)
        
        # 4. Ordenar por score y devolver top_n
        top_df = df_evaluado.sort_values(by="Score", ascending=False).head(top_n)
        return top_df.to_dict(orient="records")
    
    except Exception as e:
        # Fallback: si algo falla con ChromaDB, procesar todos (lento pero funcional)
        print(f"ChromaDB query failed: {e}. Falling back to full evaluation...")
        df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
        top_df = df_procesado.sort_values(by="Score", ascending=False).head(top_n)
        return top_df.to_dict(orient="records")


def obtener_top_candidatos(
    df: pd.DataFrame,
    tecnologia: str,
    sueldo_maximo: float,
    experiencia_minima: int,
    top_n: int = 10,
) -> list:
    """Devuelve el Top N usando ChromaDB como preseleccion vectorial."""
    try:
        candidate_pool_size = max(50, top_n * 10)
        candidate_ids, vector_similarities = _buscar_indices_en_chroma(
            tecnologia=tecnologia,
            experiencia_minima=experiencia_minima,
            total_candidatos=len(df),
            n_results=candidate_pool_size,
        )

        if not candidate_ids:
            df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
            top_df = df_procesado.sort_values(by="Score", ascending=False).head(top_n)
            return top_df.to_dict(orient="records")

        df_subset = df.iloc[candidate_ids].copy()
        df_subset["VectorSimilarity"] = [
            round(vector_similarities.get(index, 0.0) * 100, 2)
            for index in candidate_ids
        ]
        df_evaluado = evaluar_talento_it(df_subset, tecnologia, sueldo_maximo, experiencia_minima)

        top_df = df_evaluado.sort_values(
            by=["Score", "VectorSimilarity"],
            ascending=[False, False],
        ).head(top_n)
        return top_df.to_dict(orient="records")

    except Exception as e:
        print(f"ChromaDB query failed: {e}. Falling back to full evaluation...")
        df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
        top_df = df_procesado.sort_values(by="Score", ascending=False).head(top_n)
        return top_df.to_dict(orient="records")
