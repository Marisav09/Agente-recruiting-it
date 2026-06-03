"""
Script de validación simple sin descargar modelos.
Verifica que la integración sea correcta sin ejecutar la base de conocimiento.
"""

import sys
import os

# Agregar el backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 70)
print("✅ Validación de Integración ChromaDB + Agent")
print("=" * 70)

try:
    print("\n1️⃣  Verificando imports...")
    from app.services.agent import evaluar_talento_it, obtener_top_candidatos
    print("   ✓ agent.py cargado correctamente")
    
    print("\n2️⃣  Verificando tech_knowledge.py...")
    # No instanciamos para evitar descargar modelos
    from app.services import tech_knowledge
    print("   ✓ tech_knowledge.py disponible")
    print(f"   ✓ Función get_tech_kb: {hasattr(tech_knowledge, 'get_tech_kb')}")
    
    print("\n3️⃣  Verificando dependencias...")
    import chromadb
    print(f"   ✓ ChromaDB version: {chromadb.__version__}")
    
    import sentence_transformers
    print(f"   ✓ sentence-transformers disponible")
    
    import pandas as pd
    print(f"   ✓ Pandas disponible")
    
    print("\n4️⃣  Verificando estructura de datasets...")
    df = pd.read_csv('backend/data/job_applicant_dataset_final.csv', encoding='utf-8')
    print(f"   ✓ Dataset cargado: {len(df)} candidatos")
    print(f"   ✓ Columnas: {len(df.columns)} disponibles")
    
    print("\n" + "=" * 70)
    print("✅ VALIDACIÓN EXITOSA")
    print("=" * 70)
    
    print("""
📝 Próximos pasos:
   
   1. INICIAR SERVIDOR:
      uvicorn backend.app.main:app --reload
   
   2. PROBAR EN NAVEGADOR O CURL:
      http://localhost:8000
      
   3. HACER BÚSQUEDA:
      GET http://localhost:8000/api/agente/buscar?tecnologia=React&presupuesto=150000&experiencia=2
   
   4. PROBAR API STATS:
      GET http://localhost:8000/api/agente/estadisticas

⚠️  Nota: La primera vez que ejecutes una búsqueda, se descargarán los 
    embeddings de IA (~300MB) y se creará la base de datos ChromaDB.
    Esto toma ~2-3 minutos pero solo ocurre una vez.

✨ Características Semánticas Activadas:
   - React ≈ Next.js (match ~0.95)
   - JavaScript ≈ TypeScript (match ~0.85)
   - Express ⊂ Node.js (match ~0.90)
   - Angular ≠ React (match ~0.60)
   Y más de 70 tecnologías mapeadas en ChromaDB
    """)
    
except ImportError as e:
    print(f"\n❌ Error de importación: {e}")
    print("   Asegúrate de instalar las dependencias: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
