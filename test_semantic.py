"""
Script de prueba para verificar la integración semántica.
Prueba el sistema con casos reales de matching.
"""

import sys
import os

# Agregar el backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from app.services.tech_knowledge import get_tech_kb

def test_semantic_matching():
    """Prueba casos de matching semántico."""
    
    print("=" * 70)
    print("🤖 TEST: Comprensión Semántica de Tecnologías")
    print("=" * 70)
    
    tech_kb = get_tech_kb()
    
    test_cases = [
        {
            "nombre": "React Developer busca React",
            "cv": "Proficient in React, JavaScript, TypeScript, Next.js, Hooks, Redux state management",
            "tech": "React",
            "esperado": "Alto (>0.8)"
        },
        {
            "nombre": "Next.js en CV, busca React",
            "cv": "Expert in Next.js, server-side rendering, static generation, API routes",
            "tech": "React",
            "esperado": "Alto (>0.8) - Next.js es framework de React"
        },
        {
            "nombre": "Angular en CV, busca React",
            "cv": "5 years with Angular, TypeScript, RxJS, dependency injection",
            "tech": "React",
            "esperado": "Medio (0.5-0.7) - Frameworks similares pero diferentes"
        },
        {
            "nombre": "JavaScript en CV, busca TypeScript",
            "cv": "Strong JavaScript fundamentals, ES6+, node.js backend development",
            "tech": "TypeScript",
            "esperado": "Alto (>0.7) - TypeScript es superset de JavaScript"
        },
        {
            "nombre": "MongoDB en CV, busca PostgreSQL",
            "cv": "MongoDB expert, NoSQL databases, document-based storage",
            "tech": "PostgreSQL",
            "esperado": "Bajo (0.2-0.4) - Diferentes paradigmas"
        },
        {
            "nombre": "Express en CV, busca Node.js",
            "cv": "Express.js backend, middleware, routing, REST APIs",
            "tech": "Node.js",
            "esperado": "Alto (>0.8) - Express corre en Node.js"
        },
    ]
    
    print("\n📋 Casos de Prueba:\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['nombre']}")
        print(f"   CV: {test['cv'][:60]}...")
        print(f"   Busca: {test['tech']}")
        
        similitud, razon = tech_kb.calculate_semantic_match(
            cv_text=test['cv'],
            required_tech=test['tech'],
            threshold=0.2  # Threshold bajo para ver todos los casos
        )
        
        print(f"   ✓ Similitud: {similitud:.2f} ({similitud*100:.0f}%)")
        print(f"   ℹ️  {razon}")
        print(f"   📌 Esperado: {test['esperado']}")
    
    print("\n" + "=" * 70)
    print("✅ Test completado\n")


def test_with_real_dataset():
    """Prueba con el dataset real."""
    
    print("=" * 70)
    print("📊 TEST: Dataset Real")
    print("=" * 70)
    
    try:
        df = pd.read_csv('backend/data/job_applicant_dataset_final.csv', encoding='utf-8')
        
        tech_kb = get_tech_kb()
        
        # Tomar 3 candidatos aleatorios
        sample_df = df.sample(min(3, len(df)))
        
        print(f"\nDataset: {len(df)} candidatos cargados\n")
        
        for idx, (_, row) in enumerate(sample_df.iterrows(), 1):
            nombre = row.get('Job Applicant Name', 'Desconocido')
            resume = row.get('Resume', '')[:100]
            roles = row.get('Job Roles', '')
            
            print(f"\n{idx}. Candidato: {nombre}")
            print(f"   Rol: {roles}")
            print(f"   Resume: {resume}...")
            
            # Probar con React como búsqueda
            similitud, razon = tech_kb.calculate_semantic_match(
                cv_text=row.get('Resume', ''),
                required_tech="React",
                threshold=0.4
            )
            
            print(f"   React Match: {similitud*100:.0f}% - {razon}")
        
        print("\n" + "=" * 70)
        print("✅ Test dataset completado\n")
        
    except Exception as e:
        print(f"❌ Error al leer dataset: {e}")


if __name__ == "__main__":
    test_semantic_matching()
    test_with_real_dataset()
    
    print("\n🎉 Todos los tests completados!")
    print("\n💡 Próximos pasos:")
    print("   1. Iniciar el servidor: uvicorn backend.app.main:app --reload")
    print("   2. Probar en: http://localhost:8000")
    print("   3. API de búsqueda: /api/agente/buscar?tecnologia=React&presupuesto=150000&experiencia=2")
