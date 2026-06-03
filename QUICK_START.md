#!/usr/bin/env python
"""
GUÍA DE INICIO RÁPIDO - Agente Semántico con ChromaDB

Este script proporciona ejemplos de uso del nuevo sistema.
"""

print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🤖 RECRUIT IT - AGENTE SEMÁNTICO CON CHROMADB                  ║
║                                                                   ║
║   Tu sistema ahora entiende que React ≈ Next.js                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

📋 ARCHIVOS CREADOS/MODIFICADOS:

  ✓ backend/app/services/tech_knowledge.py  [NUEVO]
    └─ Base de conocimiento semántica con ChromaDB
  
  ✓ backend/app/services/agent.py           [MODIFICADO]
    └─ Scoring con comprensión semántica
  
  ✓ requirements.txt                         [ACTUALIZADO]
    └─ Agregadas: chromadb, sentence-transformers
  
  ✓ SEMANTIC_UPGRADE.md                     [NUEVO]
    └─ Documentación completa de cambios


🚀 PASOS PARA INICIAR:

1️⃣  INSTALAR DEPENDENCIAS (si aún no lo hiciste):
    pip install -r requirements.txt

2️⃣  INICIAR SERVIDOR:
    cd backend
    python -m uvicorn app.main:app --reload
    
    Esperado en primer inicio:
    • Descarga modelo de embeddings (~300MB) - 2-3 min
    • Crea base de datos ChromaDB
    • Inicia servidor en http://localhost:8000

3️⃣  PROBAR EN NAVEGADOR:
    http://localhost:8000
    
    O en terminal:
    curl "http://localhost:8000/api/agente/buscar?\\
      tecnologia=React&\\
      presupuesto=150000&\\
      experiencia=2"


📊 EJEMPLOS DE BÚSQUEDAS SEMÁNTICAS:

Búsqueda 1: React Developer
  curl "http://localhost:8000/api/agente/buscar?\\
    tecnologia=React&presupuesto=150000&experiencia=2"
  
  Resultado: Encuentra también Next.js, Vue.js, etc.

Búsqueda 2: Python Backend
  curl "http://localhost:8000/api/agente/buscar?\\
    tecnologia=Python&presupuesto=130000&experiencia=3"
  
  Resultado: Encuentra FastAPI, Django, Python experts

Búsqueda 3: Node.js Developer
  curl "http://localhost:8000/api/agente/buscar?\\
    tecnologia=Node.js&presupuesto=120000&experiencia=2"
  
  Resultado: Express, NestJS, JavaScript devs


🧠 ¿CÓMO FUNCIONA LA COMPRENSIÓN SEMÁNTICA?

Ejemplo: Búsqueda "React", CV tiene "Next.js"

  Paso 1: Sistema extrae techs del CV → ["Next.js", "TypeScript"]
  
  Paso 2: ChromaDB busca: "¿Qué tan similar es Next.js a React?"
  
  Paso 3: ChromaDB retorna: similitud = 0.95
  
  Paso 4: Calcula score: 0.95 × 40 = 38/60 puntos técnicos
  
  Paso 5: Genera justificación:
    "🔍 match perfecto: nextjs ≈ React (~95% similar)"
  
  Resultado: ✅ Candidato RECOMENDADO


📈 TECNOLOGÍAS MAPEADAS:

Frontend:
  React → Next.js (0.95), Vue.js (0.70), Angular (0.60)
  JavaScript ≈ TypeScript (0.85)
  
Backend:
  Node.js → Express (0.90), NestJS (0.95)
  Python → FastAPI (0.90), Django (0.88)
  
Base de Datos:
  PostgreSQL, MongoDB, Redis, Elasticsearch, etc.
  
DevOps:
  Docker, Kubernetes, AWS, Azure, etc.
  
... Y más de 70 tecnologías en total


🔍 VERIFICAR LA INSTALACIÓN:

python validate_integration.py

Esperado:
  ✓ agent.py cargado
  ✓ tech_knowledge.py cargado
  ✓ ChromaDB disponible
  ✓ Dataset: 10000 candidatos


💡 TIPS:

• La primera búsqueda toma ~2-3 min (descarga embeddings)
• Búsquedas posteriores son rápidas (~100-200ms)
• ChromaDB se guarda en: data/chroma_db/
• Los embeddings se cachean automáticamente
• Sin API externa: 100% offline


⚠️  POSIBLES PROBLEMAS:

1. "ModuleNotFoundError: chromadb"
   → pip install -r requirements.txt

2. "Port 8000 already in use"
   → uvicorn app.main:app --port 8001 --reload

3. Búsqueda lenta la primera vez
   → Normal, solo ocurre una vez


📚 PARA SABER MÁS:

• Documentación detallada: SEMANTIC_UPGRADE.md
• Código fuente: backend/app/services/tech_knowledge.py
• Tests: test_semantic.py (ejecutar cuando tengas tiempo)


🎯 PRÓXIMO PASO RECOMENDADO:

1. Inicia el servidor
2. Prueba en navegador: http://localhost:8000
3. Haz una búsqueda de prueba
4. Observa las justificaciones semánticas
5. Lee SEMANTIC_UPGRADE.md para entender la arquitectura


¡Listo! Tu agente ahora es semántico y entiende las relaciones
entre tecnologías. Happy recruiting! 🚀
""")
