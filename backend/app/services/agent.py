import pandas as pd


def evaluar_talento_it(
    df: pd.DataFrame,
    tecnologia: str,
    sueldo_maximo: float,
    experiencia_minima: int,
) -> pd.DataFrame:
    """Puntúa candidatos IT y agrega justificación para la UI."""
    df_evaluado = df.copy()
    scores = []
    match_tecnico_porcentaje = []
    ajuste_salarial_porcentaje = []
    juicios = []
    justificaciones = []
    tecnologia_clean = tecnologia.lower().strip()

    for _, row in df_evaluado.iterrows():
        match_tecnico_score = 0
        resume_texto = str(row.get("Resume", "")).lower()
        roles_texto = str(row.get("Job Roles", "")).lower()

        if tecnologia_clean in resume_texto or tecnologia_clean in roles_texto:
            match_tecnico_score += 40
            tiene_tech = True
        else:
            tiene_tech = False

        años_cand = row.get("años de experiencia", 0)
        if años_cand >= experiencia_minima:
            match_tecnico_score += 20
        elif experiencia_minima > 0:
            match_tecnico_score += int((años_cand / experiencia_minima) * 20)

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

        if score_total >= 80 and tiene_tech:
            juicio = "Recomendar"
        elif score_total >= 55:
            juicio = "Evaluar"
        else:
            juicio = "Descartar"

        detalles = []
        if tiene_tech:
            detalles.append(
                f"Match técnico sólido para {tecnologia} con {años_cand} años de experiencia."
            )
        else:
            detalles.append(f"No menciona explícitamente la tecnología {tecnologia} en el CV.")

        if row.get("sueldo_estimado_por_IA") is True:
            detalles.append(
                f"Nota: el salario no estaba explícito; nuestra IA estimó una pretensión de ${sueldo_cand:,.2f} basada en su nivel."
            )
        elif sueldo_cand <= sueldo_maximo:
            detalles.append(f"Su pretensión salarial de ${sueldo_cand:,.2f} se ajusta al presupuesto.")
        else:
            detalles.append(f"Su pretensión de ${sueldo_cand:,.2f} supera el presupuesto máximo.")

        scores.append(score_total)
        juicios.append(juicio)
        justificaciones.append(" ".join(detalles))

    df_evaluado["Score"] = scores
    df_evaluado["MatchTecnico"] = match_tecnico_porcentaje
    df_evaluado["AjusteSalarial"] = ajuste_salarial_porcentaje
    df_evaluado["Juicio"] = juicios
    df_evaluado["Justificacion"] = justificaciones
    return df_evaluado


def obtener_top_candidatos(
    df: pd.DataFrame,
    tecnologia: str,
    sueldo_maximo: float,
    experiencia_minima: int,
    top_n: int = 10,
) -> list:
    """Devuelve el Top N de candidatos ordenados por score del agente."""
    df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
    top_df = df_procesado.sort_values(by="Score", ascending=False).head(top_n)
    return top_df.to_dict(orient="records")
