"""
Script para recargar ChromaDB con embedding function correcto.
ChromaDB necesita saber explícitamente usar SentenceTransformer.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

print("=" * 70)
print("🔄 RECARGAR ChromaDB con Embedding Function Correcto")
print("=" * 70)

# Configuración
persist_dir = "./data/chroma_db"
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

print("\n1️⃣  Inicializando ChromaDB con SentenceTransformer...")
client = chromadb.PersistentClient(path=persist_dir)

# Obtener colección de candidatos CON embedding function
print("2️⃣  Verificando colección de candidatos...")
try:
    old_collection = client.get_collection(name="candidates")
    print(f"   ⚠️  Colección existente: {old_collection.count()} items")
    print(f"   ℹ️  Eliminando colección antigua para recargarla correctamente...")
    client.delete_collection(name="candidates")
except:
    print("   ℹ️  No existe colección previa (ok)")

# Recrear colección CON embedding function
print("\n3️⃣  Recreando colección con embedding function...")
candidates_collection = client.get_or_create_collection(
    name="candidates",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_fn  # ← CRÍTICO
)

print(f"   ✓ Colección creada: {candidates_collection.count()} items")

# Cargar dataset y crear embeddings
print("\n4️⃣  Cargando dataset...")
df = pd.read_csv("backend/data/job_applicant_dataset_final.csv", encoding="utf-8")
print(f"   ✓ Dataset cargado: {len(df)} candidatos")

# Preparar datos para ChromaDB
print("\n5️⃣  Preparando datos para ingestión...")
ids = [f"cand_{i}" for i in range(len(df))]
documents = df["Resume"].fillna("").astype(str).tolist()

# ChromaDB embebeerá automáticamente los documentos usando el embedding_fn
print("6️⃣  Ingestando documentos (ChromaDB calculará embeddings)...")
print("   ⏳ Esto puede tardar 1-2 minutos...\n")

try:
    candidates_collection.add(
        ids=ids,
        documents=documents,
        metadatas=[{"index": i} for i in range(len(df))]
    )
    print(f"   ✓ Ingestión completada!")
    print(f"   ✓ Total items en colección: {candidates_collection.count()}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ ChromaDB Recargado Correctamente")
print("=" * 70)
print("""
🎯 Estado:
   • Colección tech_ecosystem: Tecnologías (tech_knowledge.py carga automáticamente)
   • Colección candidates: 10,000 CVs con embeddings SentenceTransformer
   • Embedding function: all-MiniLM-L6-v2 (consistente en ambas colecciones)

🚀 Próximo paso: Ejecutar búsqueda rápida
   python validate_fast.py
""")
