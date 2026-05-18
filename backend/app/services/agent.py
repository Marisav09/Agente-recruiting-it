# Agente de decisión para evaluar talento IT

import pandas as pd

# Este agente toma el dataset enriquecido y aplica reglas para puntuar y justificar candidatos
def evaluar_talento_it(df: pd.DataFrame, tecnologia: str, sueldo_maximo: float, experiencia_minima: int) -> pd.DataFrame:
    """Agente de decisión que puntúa y justifica candidatos."""
    df_evaluado = df.copy()
    scores = []
    juicios = []
    justificaciones = []
    tecnologia_clean = tecnologia.lower().strip()

# Recorremos cada candidato para evaluar su ajuste técnico y económico
    for _, row in df_evaluado.iterrows():
        match_tecnico_score = 0
        resume_texto = str(row.get('Resume', '')).lower()
        roles_texto = str(row.get('Job Roles', '')).lower()

        if tecnologia_clean in resume_texto or tecnologia_clean in roles_texto:
            match_tecnico_score += 40
            tiene_tech = True
        else:
            tiene_tech = False

        anios_cand = row.get('años de experiencia', 0)
        if anios_cand >= experiencia_minima:
            match_tecnico_score += 20
        elif experiencia_minima > 0:
            match_tecnico_score += int((anios_cand / experiencia_minima) * 20)

        match_economico_score = 0
        sueldo_cand = row.get('sueldo pretendido', 0)

        # Si el sueldo fue estimado por IA, damos un pequeño beneficio en la puntuación
        if sueldo_cand <= sueldo_maximo:
            match_economico_score = 40
        else:
            exceso = (sueldo_cand - sueldo_maximo) / sueldo_maximo
            if exceso <= 0.15:
                match_economico_score = int(40 * (1 - (exceso / 0.15)))
            else:
                match_economico_score = 0

        score_total = match_tecnico_score + match_economico_score

        # Definimos el juicio final basado en el score total y la presencia de la tecnología
        if score_total >= 80 and tiene_tech:
            juicio = "Recomendar"
        elif score_total >= 55:
            juicio = "Evaluar"
        else:
            juicio = "Descartar"

        detalles = []

        # Justificación detallada para cada candidato
        if tiene_tech:
            detalles.append(f"Match Técnico sólido para {tecnologia} con {anios_cand} años de experiencia.")
        else:
            detalles.append(f"No menciona explícitamente la tecnología {tecnologia} en el CV.")

        if row.get('sueldo_estimado_por_IA') == True:
            detalles.append(
                f"Nota: El salario no estaba explícito; nuestra IA estimó una pretensión de ${sueldo_cand:,.2f} basada en su nivel."
            )
        else:
            if sueldo_cand <= sueldo_maximo:
                detalles.append(f"Su pretensión salarial de ${sueldo_cand:,.2f} se ajusta al presupuesto.")
            else:
                detalles.append(f"Su pretensión de ${sueldo_cand:,.2f} supera el presupuesto máximo.")
        # Agregamos detalles sobre la puntuación técnica y económica para transparencia

        scores.append(score_total)
        juicios.append(juicio)
        justificaciones.append(" ".join(detalles))

    # Agregamos las nuevas columnas al DataFrame evaluado
    df_evaluado['Score'] = scores
    df_evaluado['Juicio'] = juicios
    df_evaluado['Justificacion'] = justificaciones
    return df_evaluado

# Función para obtener el Top N de candidatos recomendados por el agente
def obtener_top_candidatos(df: pd.DataFrame, tecnologia: str, sueldo_maximo: float, experiencia_minima: int, top_n: int = 10) -> list:
    """Devuelve el Top N de candidatos ordenados por score del agente."""
    df_procesado = evaluar_talento_it(df, tecnologia, sueldo_maximo, experiencia_minima)
    top_df = df_procesado.sort_values(by='Score', ascending=False).head(top_n)
    return top_df.to_dict(orient='records')
