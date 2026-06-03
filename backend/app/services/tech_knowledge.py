"""
Base de conocimiento semántica de tecnologías usando ChromaDB.
Permite razonar sobre relaciones entre tecnologías (React ≈ Next.js, etc.)
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple
import chromadb
from chromadb.utils import embedding_functions

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

PROJECT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CHROMA_DIR = PROJECT_DIR / "data" / "chroma_db"


class TechKnowledgeBase:
    """Gestiona la base de conocimiento de tecnologías con embeddings semánticos."""
    
    def __init__(self, persist_dir: str | None = None):
        """
        Inicializa ChromaDB con persistencia local.
        Usa SentenceTransformer (all-MiniLM-L6-v2) explícitamente para consistencia.
        
        Args:
            persist_dir: Directorio para guardar la BD vectorial
        """
        persist_dir = str(persist_dir or DEFAULT_CHROMA_DIR)

        # Crear directorio si no existe
        os.makedirs(persist_dir, exist_ok=True)
        
        # Usar la nueva API de ChromaDB (v0.4+) con SentenceTransformer
        # IMPORTANTE: Especificar el mismo modelo que usamos en precompute_embeddings.py
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            local_files_only=True,
        )
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.persist_dir = persist_dir

        try:
            self.client.delete_collection(name="tech_ecosystem")
        except Exception:
            pass
        
        # Obtener o crear colección de tecnologías CON el embedding function
        self.collection = self.client.get_or_create_collection(
            name="tech_ecosystem",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_fn  # ← CRÍTICO: especificar función
        )
        
        # Cargar datos si la colección está vacía
        if self.collection.count() == 0:
            self._populate_knowledge_base()
    
    def _populate_knowledge_base(self):
        """Carga el grafo de tecnologías en ChromaDB (una sola vez)."""
        
        tech_data = {
            # Frontend - JavaScript/TypeScript
            "React": "JavaScript library for building user interfaces with JSX components hooks state management",
            "Next.js": "React framework with server-side rendering static generation API routes based on React",
            "Vue.js": "Progressive JavaScript framework reactive data binding component-based",
            "Angular": "Full-featured TypeScript framework dependency injection RxJS observable",
            "Svelte": "Compiler framework reactive components less boilerplate than React Vue",
            "Remix": "Full stack React framework server-side rendering data loaders",
            "Nuxt": "Vue framework similar to Next.js for Vue ecosystem server rendering",
            
            # Backend - Node.js ecosystem
            "Node.js": "JavaScript runtime for server-side development non-blocking IO",
            "Express.js": "Minimal Node.js web framework routing middleware",
            "NestJS": "TypeScript framework for Node.js inspired by Angular dependency injection",
            "Koa": "Lightweight Node.js framework with async middleware",
            "Hapi": "Enterprise framework for Node.js",
            
            # Backend - Python
            "FastAPI": "Modern Python web framework async support automatic API docs",
            "Django": "Full-stack Python framework ORM admin panel batteries included",
            "Flask": "Lightweight Python web framework microframework",
            "Fastify": "High performance Node.js web framework",
            "Pyramid": "Flexible Python web framework",
            
            # Backend - Other languages
            "Go": "Statically typed compiled language concurrent programming",
            "Rust": "Systems programming memory safety no garbage collector",
            "Java": "Object-oriented language JVM enterprise applications",
            "C#": "Object-oriented language .NET framework enterprise",
            
            # Lenguajes de programación
            "JavaScript": "Interpreted language for web development prototype-based",
            "TypeScript": "Superset of JavaScript with static typing compilation",
            "Python": "Interpreted language general-purpose data science machine learning",
            
            # Bases de datos - SQL
            "PostgreSQL": "Relational database ACID JSON support PostGIS",
            "MySQL": "Open source relational database popular LAMP stack",
            "MariaDB": "MySQL fork relational database",
            "SQLite": "Embedded relational database single file",
            
            # Bases de datos - NoSQL
            "MongoDB": "NoSQL document database JSON-like BSON flexible schema",
            "Firebase": "Cloud database real-time NoSQL by Google",
            "DynamoDB": "NoSQL key-value database by Amazon",
            "CouchDB": "NoSQL document database distributed",
            
            # Cache y almacenamiento
            "Redis": "In-memory data structure store key-value caching",
            "Memcached": "Memory caching system distributed",
            "Elasticsearch": "Search and analytics engine full-text search",
            
            # DevOps y Contenedores
            "Docker": "Containerization platform images containers isolation",
            "Kubernetes": "Container orchestration platform scaling deployment",
            "Docker Compose": "Multi-container Docker applications",
            
            # Cloud platforms
            "AWS": "Amazon cloud services EC2 S3 Lambda RDS",
            "Google Cloud": "GCP Google cloud services Compute Engine Cloud SQL",
            "Azure": "Microsoft cloud services virtual machines databases",
            "Heroku": "Platform as a service cloud application deployment",
            
            # Testing
            "Jest": "JavaScript testing framework unit tests mocks",
            "Mocha": "JavaScript test framework flexible",
            "Pytest": "Python testing framework fixtures parametrization",
            "Jasmine": "JavaScript testing framework BDD",
            
            # Build tools
            "Webpack": "Module bundler JavaScript assets",
            "Vite": "Frontend build tool fast development server ES modules",
            "Babel": "JavaScript transpiler ES6+ to ES5",
            "Rollup": "Module bundler for JavaScript libraries",
            
            # APIs y comunicación
            "REST": "Representational state transfer HTTP endpoints stateless",
            "GraphQL": "Query language for APIs flexible data fetching",
            "gRPC": "High performance RPC framework protocol buffers",
            "WebSocket": "Bidirectional communication full-duplex",
            
            # Authentication
            "JWT": "JSON web tokens stateless authentication",
            "OAuth": "Authorization protocol third-party access",
            "OAuth2": "Modern authorization framework delegated access",
            "SAML": "XML-based authentication federation",
        }
        
        documents = []
        metadatas = []
        ids = []
        
        for tech, description in tech_data.items():
            documents.append(description)
            metadatas.append({"technology": tech})
            ids.append(tech.lower().replace(" ", "_"))
        
        # Agregar a ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"OK Base de conocimiento cargada: {len(tech_data)} tecnologias")
    
    def find_similar_tech(
        self, 
        query_tech: str, 
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Busca tecnologías similares a una consulta.
        
        Args:
            query_tech: Tecnología a buscar
            top_k: Número de resultados
            threshold: Umbral mínimo de similitud (0-1)
        
        Returns:
            Lista de dicts: [{'technology': 'React', 'similarity': 0.95}, ...]
        """
        results = self.collection.query(
            query_texts=[query_tech],
            n_results=top_k
        )
        
        similar_techs = []
        if results['metadatas'] and len(results['metadatas'][0]) > 0:
            for i, metadata in enumerate(results['metadatas'][0]):
                # Convertir distancia cosine a similitud (0-1)
                distance = results['distances'][0][i]
                similarity = max(0, 1 - distance)
                
                if similarity >= threshold:
                    similar_techs.append({
                        'technology': metadata['technology'],
                        'similarity': round(similarity, 3)
                    })
        
        return similar_techs
    
    def calculate_semantic_match(
        self,
        cv_text: str,
        required_tech: str,
        threshold: float = 0.6
    ) -> Tuple[float, str]:
        """
        Calcula el match semántico entre un CV y una tecnología requerida.
        
        Args:
            cv_text: Texto del CV/Resume
            required_tech: Tecnología buscada por la empresa
            threshold: Umbral de similitud considerada válida
        
        Returns:
            (similitud: float, justificacion: str)
        """
        # Extraer tecnologías mencionadas en el CV
        techs_en_cv = self._extract_technologies(cv_text)
        
        if not techs_en_cv:
            return 0.0, f"No se detectaron tecnologías en el CV"
        
        # Para cada tech en el CV, buscar similitud con la requerida
        max_similitud = 0
        tech_match = None
        razon_tecnica = ""
        
        for tech_cv in techs_en_cv:
            # Buscar si la tech del CV es similar a la requerida
            similares = self.find_similar_tech(
                query_tech=required_tech,
                top_k=10,
                threshold=0
            )
            
            # Comparar directamente
            for sim_result in similares:
                if tech_cv.lower() == sim_result['technology'].lower():
                    similitud = sim_result['similarity']
                    if similitud > max_similitud:
                        max_similitud = similitud
                        tech_match = tech_cv
                        
                        if similitud >= 0.95:
                            razon_tecnica = f"match perfecto: {tech_cv} ~= {required_tech}"
                        elif similitud >= 0.75:
                            razon_tecnica = f"match alto: {tech_cv} (~{similitud*100:.0f}% similar a {required_tech})"
                        else:
                            razon_tecnica = f"match parcial: {tech_cv} ({similitud*100:.0f}% relacionado)"
                    break
            
            # Si no está en la BD, buscar similitud léxica
            if max_similitud == 0:
                similares = self.find_similar_tech(
                    query_tech=tech_cv,
                    top_k=5,
                    threshold=0.7
                )
                
                for sim_result in similares:
                    if required_tech.lower() in [s['technology'].lower() for s in similares]:
                        max_similitud = 0.8
                        tech_match = tech_cv
                        razon_tecnica = f"{tech_cv} es parte del ecosistema de {required_tech}"
                        break
        
        # Si no hay match pero tecnologías relacionadas
        if max_similitud == 0 and techs_en_cv:
            razon_tecnica = f"CV incluye: {', '.join(techs_en_cv[:3])}. Buscaba: {required_tech}"
        
        return max_similitud, razon_tecnica or f"No hay match directo con {required_tech}"
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas en un texto."""
        
        # Patrones regex para detectar tecnologías comunes
        tech_patterns = [
            # Frontend
            r'\b(react|vue|angular|svelte|ember|flutter|ionic)\b',
            r'\b(next\.js|nuxt|remix|gatsby|astro)\b',
            r'\b(tailwind|bootstrap|material design|chakra)\b',
            
            # Backend
            r'\b(node\.js|express|fastapi|django|flask|nest\.js|hapi|koa)\b',
            r'\b(spring|rails|laravel|asp\.net)\b',
            
            # Lenguajes
            r'\b(javascript|typescript|python|java|golang|rust|c\#|php|ruby)\b',
            
            # Bases de datos
            r'\b(postgres|postgresql|mongodb|mysql|mariadb|redis|cassandra|dynamodb|firebase|elasticsearch)\b',
            r'\b(sqlite|couchdb|neo4j)\b',
            
            # DevOps
            r'\b(docker|kubernetes|k8s|jenkins|gitlab ci|github actions|terraform)\b',
            
            # Cloud
            r'\b(aws|azure|gcp|google cloud|heroku|netlify|vercel)\b',
            
            # Testing
            r'\b(jest|mocha|pytest|jasmine|cypress|selenium|karma)\b',
            
            # Otros
            r'\b(graphql|rest|websocket|jwt|oauth|grpc)\b',
        ]
        
        encontradas = []
        text_lower = text.lower()
        
        for pattern in tech_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                tech = match.group(0)
                # Limpiar puntos (Next.js -> Nextjs)
                tech_clean = tech.replace(".", "")
                encontradas.append(tech_clean)
        
        # Remover duplicados manteniendo orden
        return list(dict.fromkeys(encontradas))


# Instancia global
_kb_instance = None

def get_tech_kb() -> TechKnowledgeBase:
    """Obtiene la instancia singleton de la base de conocimiento."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = TechKnowledgeBase()
    return _kb_instance
    
    def _populate_knowledge_base(self):
        """Carga el grafo de tecnologías en ChromaDB (una sola vez)."""
        
        tech_data = {
            # Frontend - JavaScript/TypeScript
            "React": "JavaScript library for building user interfaces with JSX components hooks state management",
            "Next.js": "React framework with server-side rendering static generation API routes based on React",
            "Vue.js": "Progressive JavaScript framework reactive data binding component-based",
            "Angular": "Full-featured TypeScript framework dependency injection RxJS observable",
            "Svelte": "Compiler framework reactive components less boilerplate than React Vue",
            "Remix": "Full stack React framework server-side rendering data loaders",
            "Nuxt": "Vue framework similar to Next.js for Vue ecosystem server rendering",
            
            # Backend - Node.js ecosystem
            "Node.js": "JavaScript runtime for server-side development non-blocking IO",
            "Express.js": "Minimal Node.js web framework routing middleware",
            "NestJS": "TypeScript framework for Node.js inspired by Angular dependency injection",
            "Koa": "Lightweight Node.js framework with async middleware",
            "Hapi": "Enterprise framework for Node.js",
            
            # Backend - Python
            "FastAPI": "Modern Python web framework async support automatic API docs",
            "Django": "Full-stack Python framework ORM admin panel batteries included",
            "Flask": "Lightweight Python web framework microframework",
            "Fastify": "High performance Node.js web framework",
            "Pyramid": "Flexible Python web framework",
            
            # Backend - Other languages
            "Go": "Statically typed compiled language concurrent programming",
            "Rust": "Systems programming memory safety no garbage collector",
            "Java": "Object-oriented language JVM enterprise applications",
            "C#": "Object-oriented language .NET framework enterprise",
            
            # Lenguajes de programación
            "JavaScript": "Interpreted language for web development prototype-based",
            "TypeScript": "Superset of JavaScript with static typing compilation",
            "Python": "Interpreted language general-purpose data science machine learning",
            
            # Bases de datos - SQL
            "PostgreSQL": "Relational database ACID JSON support PostGIS",
            "MySQL": "Open source relational database popular LAMP stack",
            "MariaDB": "MySQL fork relational database",
            "SQLite": "Embedded relational database single file",
            
            # Bases de datos - NoSQL
            "MongoDB": "NoSQL document database JSON-like BSON flexible schema",
            "Firebase": "Cloud database real-time NoSQL by Google",
            "DynamoDB": "NoSQL key-value database by Amazon",
            "CouchDB": "NoSQL document database distributed",
            
            # Cache y almacenamiento
            "Redis": "In-memory data structure store key-value caching",
            "Memcached": "Memory caching system distributed",
            "Elasticsearch": "Search and analytics engine full-text search",
            
            # DevOps y Contenedores
            "Docker": "Containerization platform images containers isolation",
            "Kubernetes": "Container orchestration platform scaling deployment",
            "Docker Compose": "Multi-container Docker applications",
            
            # Cloud platforms
            "AWS": "Amazon cloud services EC2 S3 Lambda RDS",
            "Google Cloud": "GCP Google cloud services Compute Engine Cloud SQL",
            "Azure": "Microsoft cloud services virtual machines databases",
            "Heroku": "Platform as a service cloud application deployment",
            
            # Testing
            "Jest": "JavaScript testing framework unit tests mocks",
            "Mocha": "JavaScript test framework flexible",
            "Pytest": "Python testing framework fixtures parametrization",
            "Jasmine": "JavaScript testing framework BDD",
            
            # Build tools
            "Webpack": "Module bundler JavaScript assets",
            "Vite": "Frontend build tool fast development server ES modules",
            "Babel": "JavaScript transpiler ES6+ to ES5",
            "Rollup": "Module bundler for JavaScript libraries",
            
            # APIs y comunicación
            "REST": "Representational state transfer HTTP endpoints stateless",
            "GraphQL": "Query language for APIs flexible data fetching",
            "gRPC": "High performance RPC framework protocol buffers",
            "WebSocket": "Bidirectional communication full-duplex",
            
            # Authentication
            "JWT": "JSON web tokens stateless authentication",
            "OAuth": "Authorization protocol third-party access",
            "OAuth2": "Modern authorization framework delegated access",
            "SAML": "XML-based authentication federation",
        }
        
        documents = []
        metadatas = []
        ids = []
        
        for tech, description in tech_data.items():
            documents.append(description)
            metadatas.append({"technology": tech})
            ids.append(tech.lower().replace(" ", "_"))
        
        # Agregar a ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"OK Base de conocimiento cargada: {len(tech_data)} tecnologias")
    
    def find_similar_tech(
        self, 
        query_tech: str, 
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Busca tecnologías similares a una consulta.
        
        Args:
            query_tech: Tecnología a buscar
            top_k: Número de resultados
            threshold: Umbral mínimo de similitud (0-1)
        
        Returns:
            Lista de dicts: [{'technology': 'React', 'similarity': 0.95}, ...]
        """
        results = self.collection.query(
            query_texts=[query_tech],
            n_results=top_k
        )
        
        similar_techs = []
        if results['metadatas'] and len(results['metadatas'][0]) > 0:
            for i, metadata in enumerate(results['metadatas'][0]):
                # Convertir distancia cosine a similitud (0-1)
                distance = results['distances'][0][i]
                similarity = max(0, 1 - distance)
                
                if similarity >= threshold:
                    similar_techs.append({
                        'technology': metadata['technology'],
                        'similarity': round(similarity, 3)
                    })
        
        return similar_techs
    
    def calculate_semantic_match(
        self,
        cv_text: str,
        required_tech: str,
        threshold: float = 0.6
    ) -> Tuple[float, str]:
        """
        Calcula el match semántico entre un CV y una tecnología requerida.
        
        Args:
            cv_text: Texto del CV/Resume
            required_tech: Tecnología buscada por la empresa
            threshold: Umbral de similitud considerada válida
        
        Returns:
            (similitud: float, justificacion: str)
        """
        # Extraer tecnologías mencionadas en el CV
        techs_en_cv = self._extract_technologies(cv_text)
        
        if not techs_en_cv:
            return 0.0, f"No se detectaron tecnologías en el CV"
        
        # Para cada tech en el CV, buscar similitud con la requerida
        max_similitud = 0
        tech_match = None
        razon_tecnica = ""
        
        for tech_cv in techs_en_cv:
            # Buscar si la tech del CV es similar a la requerida
            similares = self.find_similar_tech(
                query_tech=required_tech,
                top_k=10,
                threshold=0
            )
            
            # Comparar directamente
            for sim_result in similares:
                if tech_cv.lower() == sim_result['technology'].lower():
                    similitud = sim_result['similarity']
                    if similitud > max_similitud:
                        max_similitud = similitud
                        tech_match = tech_cv
                        
                        if similitud >= 0.95:
                            razon_tecnica = f"match perfecto: {tech_cv} ~= {required_tech}"
                        elif similitud >= 0.75:
                            razon_tecnica = f"match alto: {tech_cv} (~{similitud*100:.0f}% similar a {required_tech})"
                        else:
                            razon_tecnica = f"match parcial: {tech_cv} ({similitud*100:.0f}% relacionado)"
                    break
            
            # Si no está en la BD, buscar similitud léxica
            if max_similitud == 0:
                similares = self.find_similar_tech(
                    query_tech=tech_cv,
                    top_k=5,
                    threshold=0.7
                )
                
                for sim_result in similares:
                    if required_tech.lower() in [s['technology'].lower() for s in similares]:
                        max_similitud = 0.8
                        tech_match = tech_cv
                        razon_tecnica = f"{tech_cv} es parte del ecosistema de {required_tech}"
                        break
        
        # Si no hay match pero tecnologías relacionadas
        if max_similitud == 0 and techs_en_cv:
            razon_tecnica = f"CV incluye: {', '.join(techs_en_cv[:3])}. Buscaba: {required_tech}"
        
        return max_similitud, razon_tecnica or f"No hay match directo con {required_tech}"
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas en un texto."""
        
        # Patrones regex para detectar tecnologías comunes
        tech_patterns = [
            # Frontend
            r'\b(react|vue|angular|svelte|ember|flutter|ionic)\b',
            r'\b(next\.js|nuxt|remix|gatsby|astro)\b',
            r'\b(tailwind|bootstrap|material design|chakra)\b',
            
            # Backend
            r'\b(node\.js|express|fastapi|django|flask|nest\.js|hapi|koa)\b',
            r'\b(spring|rails|laravel|asp\.net)\b',
            
            # Lenguajes
            r'\b(javascript|typescript|python|java|golang|rust|c\#|php|ruby)\b',
            
            # Bases de datos
            r'\b(postgres|postgresql|mongodb|mysql|mariadb|redis|cassandra|dynamodb|firebase|elasticsearch)\b',
            r'\b(sqlite|couchdb|neo4j)\b',
            
            # DevOps
            r'\b(docker|kubernetes|k8s|jenkins|gitlab ci|github actions|terraform)\b',
            
            # Cloud
            r'\b(aws|azure|gcp|google cloud|heroku|netlify|vercel)\b',
            
            # Testing
            r'\b(jest|mocha|pytest|jasmine|cypress|selenium|karma)\b',
            
            # Otros
            r'\b(graphql|rest|websocket|jwt|oauth|grpc)\b',
        ]
        
        encontradas = []
        text_lower = text.lower()
        
        for pattern in tech_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                tech = match.group(0)
                # Limpiar puntos (Next.js -> Nextjs)
                tech_clean = tech.replace(".", "")
                encontradas.append(tech_clean)
        
        # Remover duplicados manteniendo orden
        return list(dict.fromkeys(encontradas))


# Instancia global
_kb_instance = None

def get_tech_kb() -> TechKnowledgeBase:
    """Obtiene la instancia singleton de la base de conocimiento."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = TechKnowledgeBase()
    return _kb_instance
