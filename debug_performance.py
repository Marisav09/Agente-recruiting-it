"""
Script de diagnóstico: identifica cuello de botella en búsqueda.
Prueba cada componente por separado.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb
import pandas as pd

print("=" * 70)
print("🔍 DIAGNÓSTICO: Identificar Cuello de Botella")
print("=" * 70)

# 1. Prueba ChromaDB Query
print("\n1️⃣  Prueba: Consulta ChromaDB (búsqueda semántica)...")
try:
    client = chromadb.PersistentClient(path="data/chroma_db")
    collection = client.get_collection(name="candidates")
    
    start = time.time()
    results = collection.query(
        query_texts=["React 2 years experience $150000"],
        n_results=100
    )
    elapsed = time.time() - start
    
    print(f"   ✓ ChromaDB query completada en {elapsed:.3f}s")
    print(f"   ✓ Resultados encontrados: {len(results['ids'][0]) if results['ids'] else 0}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 2. Prueba carga de dataset
print("\n2️⃣  Prueba: Cargar dataset...")
try:
    start = time.time()
    df = pd.read_csv("backend/data/job_applicant_dataset_final.csv", encoding="utf-8")
    elapsed = time.time() - start
    print(f"   ✓ Dataset cargado en {elapsed:.3f}s ({len(df)} filas)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Prueba extracción de tecnologías
print("\n3️⃣  Prueba: Extracción de tecnologías (regex)...")
try:
    from app.services.tech_knowledge import get_tech_kb
    
    tech_kb = get_tech_kb()
    sample_cv = df.iloc[0]["Resume"]
    
    start = time.time()
    techs = tech_kb._extract_technologies(sample_cv)
    elapsed = time.time() - start
    
    print(f"   ✓ Extracción completada en {elapsed:.3f}s")
    print(f"   ✓ Tecnologías encontradas: {len(techs)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 4. Prueba similitud semántica en uno
print("\n4️⃣  Prueba: Similitud semántica (1 candidato)...")
try:
    sample_cv = df.iloc[0]["Resume"]
    
    start = time.time()
    similitud, razon = tech_kb.calculate_semantic_match(sample_cv, "React", threshold=0.6)
    elapsed = time.time() - start
    
    print(f"   ✓ Cálculo completado en {elapsed:.3f}s")
    print(f"   ✓ Similitud: {similitud:.2f}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 5. Prueba similitud en 10 candidatos
print("\n5️⃣  Prueba: Similitud semántica (10 candidatos)...")
try:
    start = time.time()
    for i in range(10):
        sample_cv = df.iloc[i]["Resume"]
        similitud, razon = tech_kb.calculate_semantic_match(sample_cv, "React", threshold=0.6)
    elapsed = time.time() - start
    
    print(f"   ✓ 10 cálculos completados en {elapsed:.3f}s ({elapsed/10:.3f}s c/u)")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 70)
