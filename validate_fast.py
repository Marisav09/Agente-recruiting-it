"""
Script de validación rápido: Búsqueda semántica optimizada (50 candidatos).
Tiempo esperado: 2-3 segundos
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from app.services.agent import obtener_top_candidatos

print("=" * 70)
print("⚡ VALIDACIÓN RÁPIDA: Búsqueda Semántica Optimizada")
print("=" * 70)

# Cargar dataset
print("\n📊 Cargando dataset...")
df = pd.read_csv("backend/data/job_applicant_dataset_final.csv", encoding="utf-8")
print(f"   ✓ {len(df)} candidatos cargados")

# Prueba 1: React Developer
print("\n🔍 Prueba 1: React Developer ($150k, 2 años exp)...")
start = time.time()
resultados = obtener_top_candidatos(df, "React", 150000, 2, top_n=5)
elapsed = time.time() - start

print(f"   ✓ Completada en {elapsed:.2f}s")
print(f"   ✓ Top 5 encontrados:\n")
for i, cand in enumerate(resultados, 1):
    print(f"   {i}. {cand['Job Applicant Name']} | Score: {cand['Score']}/100")
    print(f"      Salario: ${cand.get('sueldo pretendido', 0):,.0f} | Match: {cand['MatchTecnico']}%")

# Prueba 2: Python Developer
print("\n🔍 Prueba 2: Python Developer ($120k, 3 años exp)...")
start = time.time()
resultados = obtener_top_candidatos(df, "Python", 120000, 3, top_n=5)
elapsed = time.time() - start

print(f"   ✓ Completada en {elapsed:.2f}s")
print(f"   ✓ Top 5 encontrados:\n")
for i, cand in enumerate(resultados, 1):
    print(f"   {i}. {cand['Job Applicant Name']} | Score: {cand['Score']}/100")
    print(f"      Salario: ${cand.get('sueldo pretendido', 0):,.0f} | Match: {cand['MatchTecnico']}%")

print("\n" + "=" * 70)
print("✅ VALIDACIÓN COMPLETADA")
print("=" * 70)
print("""
🎯 Resumen:
   • Búsquedas utilizan ChromaDB (precomputados)
   • Filtro inicial: 50 candidatos más similares
   • Tiempo esperado: 2-3s por búsqueda
   • Escala: 10,000 candidatos sin recalcular embeddings

🚀 Próximo paso: Iniciar uvicorn
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
""")
