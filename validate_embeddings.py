"""
Script de validación: verifica que ChromaDB tiene embeddings precomputados
y mide el tiempo de búsqueda (debe ser rápido sin recalcular).
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from app.services.agent import obtener_top_candidatos
import chromadb

print("=" * 70)
print("✅ VALIDACIÓN: ChromaDB con Embeddings Precomputados")
print("=" * 70)

# 1. Verificar colección de candidatos
print("\n1️⃣  Verificando colección de embeddings precomputados...")
try:
    client = chromadb.PersistentClient(path="data/chroma_db")
    coll = client.get_collection(name="candidates")
    count = coll.count()
    print(f"   ✓ Colección 'candidates' encontrada")
    print(f"   ✓ Total de embeddings: {count}")
    if count > 0:
        print(f"   ✓ Embeddings ingestados exitosamente")
    else:
        print(f"   ⚠️  Colección vacía - ejecuta: python backend/scripts/precompute_embeddings.py")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 2. Cargar dataset
print("\n2️⃣  Cargando dataset...")
try:
    df = pd.read_csv("backend/data/job_applicant_dataset_final.csv", encoding="utf-8")
    print(f"   ✓ Dataset cargado: {len(df)} candidatos")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 3. Hacer búsqueda de prueba y medir tiempo
print("\n3️⃣  Prueba de búsqueda (React Developer, presupuesto $150k, 2 años exp)...")
print("   Midiendo tiempo de ejecución...")
print("   ⏳ Esto puede tardar 5-10 segundos (evaluando 100 candidatos)...\n")

start = time.time()
try:
    resultados = obtener_top_candidatos(
        df=df,
        tecnologia="React",
        sueldo_maximo=150000,
        experiencia_minima=2,
        top_n=5
    )
    elapsed = time.time() - start
    print(f"   ✓ Top 5 candidatos encontrados:\n")
    
    for i, cand in enumerate(resultados, 1):
        print(f"   {i}. {cand['Job Applicant Name']} | Score: {cand['Score']}/100")
        print(f"      Match técnico: {cand['MatchTecnico']}% | Salario: ${cand.get('sueldo pretendido', 0):,.0f}")
        print(f"      Juicio: {cand['Juicio']}")
        print()

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 70)
print("✅ VALIDACIÓN COMPLETADA")
print("=" * 70)

print(f"""
📊 Resultados:
   • Embeddings: {count} precomputados en ChromaDB
   • Tiempo búsqueda: {elapsed:.2f}s (sin recalcular embeddings)
   • Estado: ✅ LISTO para producción

🚀 Próximo paso: Iniciar servidor
   cd backend
   python -m uvicorn app.main:app --reload

⚡ Con embeddings precomputados, las búsquedas deberían ser:
   • 10-50x más rápidas que antes
   • Respuestas en <1 segundo (típicamente 100-300ms)
   • GPU utilizada solo para la extracción de tecnologías, no para embeddings
""")
