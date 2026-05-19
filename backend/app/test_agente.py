# Este test simula la ejecución completa del pipeline en memoria, desde la 
# carga del dataset enriquecido por la IA, hasta la evaluación de candidatos 
# por el agente. Es una prueba integral para validar que todas las partes del 
# sistema funcionan juntas correctamente.

import pandas as pd
import numpy as np
from app.data.loader import cargar_dataset
from app.services.analisis import resumen_estadistico
from app.services.agent import obtener_top_candidatos
from app.services.prediccion import enriquecer_dataset # Importamos tu función de ML

def ejecutar_test():
    print("==================================================")
    print("EJECUTANDO PIPELINE COMPLETO EN MEMORIA")
    print("==================================================")
    
    # 1. PASO CLAVE: Forzamos a la IA a correr y a pisar el archivo con datos reales
    try:
        print("Pasando datos por el Arbol de Decision de Machine Learning...")
        df_enriquecido = enriquecer_dataset()
        print("Dataset completado por la IA y guardado con exito.")
        print("-" * 50)
    except Exception as e:
        print(f"Error al ejecutar el Machine Learning: {e}")
        return

    # 2. Mostramos métricas para confirmar que los datos no estén vacíos
    metrics = resumen_estadistico(df_enriquecido)
    print(f"Dataset cargado con exito: {metrics['filas']} registros detectados.")
    print(f"Columnas disponibles: {metrics['nombres_columnas']}")
    print("-" * 50)

    # 3. Filtros del Reclutador (Cambiamos a 'Senior' o 'Python' para probar)
    tecnologia_buscada = "Python"
    sueldo_max = 80000.0
    exp_min = 3
    
    print(f"Agente evaluando candidatos para: '{tecnologia_buscada}'")
    print(f"Presupuesto Max: ${sueldo_max} | Exp. Minima: {exp_min} anios\n")
    
    # 4. Evaluamos usando el DataFrame que la IA acaba de escupir en caliente
    top_3 = obtener_top_candidatos(df_enriquecido, tecnologia_buscada, sueldo_max, exp_min, top_n=3)
    
    print(f"TOP {len(top_3)} RECOMENDACIONES DEL AGENTE:")
    for i, candidato in enumerate(top_3, 1):
        sueldo_val = candidato.get('sueldo pretendido')
        sueldo_texto = f"${sueldo_val:,.2f}" if pd.notnull(sueldo_val) else "No especificado"
        
        # Validamos qué llaves reales trae para no imprimir None
        nombre_cand = candidato.get('Job Applicant Name') or candidato.get('Name') or "No encontrado"
        exp_cand = candidato.get('años de experiencia')
        if exp_cand is None:
            exp_cand = candidato.get('Años de Experiencia', 'None')

        print(f"\n[{i}] Nombre: {nombre_cand}")
        print(f"    Score: {candidato.get('Score')}/100 | Juicio: {candidato.get('Juicio')}")
        print(f"    Exp: {exp_cand} anios | Sueldo: {sueldo_texto}")
        print(f"    Justificacion: {candidato.get('Justificacion')}")
    print("==================================================")

if __name__ == "__main__":
    ejecutar_test()
