from typing import List, Dict, Optional
import json
import os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.llms import CTransformers
import traceback
from content_generator import ContentGenerator

class RAGHandler:
    def __init__(self, 
                 model_path: str = "models/llama-2-7b-chat.gguf",
                 embeddings_model: str = "intfloat/multilingual-e5-large",
                 data_dir: str = "rag/data",
                 vector_store_path: str = "rag/vector_store"):
        """Initialize RAG handler with models and data"""
        try:
            print("\nInicializando RAG Handler...")
            
            # Initialize LLM
            print("Cargando modelo LLM...")
            self.llm = CTransformers(
                model=model_path,
                model_type="llama",
                config={
                    'max_new_tokens': 1024,    # Reducido para evitar exceder el contexto
                    'temperature': 0.7,
                    'context_length': 1024,    # Reducido para evitar exceder el contexto
                    'gpu_layers': 0,           # Use CPU
                    'threads': 8,              # Use more CPU threads
                    'batch_size': 1,           # Keep batch size small
                    'top_k': 40,
                    'top_p': 0.95,
                    'stop': ['</s>']           # Stop token for Llama 2
                }
            )
            
            # Initialize embeddings
            print("Cargando modelo de embeddings...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embeddings_model
            )
            
            # Load or create vector store
            self.vector_store_path = vector_store_path
            if os.path.exists(vector_store_path):
                print("Cargando vector store existente...")
                self.vector_store = FAISS.load_local(
                    vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                print("Creando nuevo vector store...")
                self.vector_store = self._create_vector_store(data_dir)
            
            # Create generation chain
            print("Creando cadena de generación...")
            self.generation_chain = self._create_generation_chain()
            
            print("RAG Handler inicializado exitosamente!")
            
        except Exception as e:
            print(f"Error inicializando RAG Handler: {str(e)}")
            traceback.print_exc()
            raise
    
    def _load_knowledge_base(self, path: Optional[str]) -> List[str]:
        """Load knowledge base from file or use default data"""
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split content into paragraphs
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                return paragraphs
        return [
            "Las presentaciones efectivas tienen una estructura clara: introducción, desarrollo y conclusión.",
            "Es importante usar elementos visuales como gráficos e imágenes para mantener el interés.",
            "Cada diapositiva debe tener un mensaje claro y conciso.",
            "El diseño debe ser consistente en toda la presentación.",
            "Es recomendable usar la regla del 6x6: no más de 6 puntos por slide, no más de 6 palabras por punto."
        ]
    
    def _create_vector_store(self, data_dir: str) -> FAISS:
        """Create new vector store"""
        print("Creando nuevo vector store...")
        texts = self._load_knowledge_base(os.path.join(data_dir, "knowledge_base.txt"))
        vector_store = FAISS.from_texts(texts, self.embeddings)
        
        # Save vector store
        os.makedirs(self.vector_store_path, exist_ok=True)
        vector_store.save_local(self.vector_store_path)
        
        return vector_store
    
    def _create_generation_chain(self) -> LLMChain:
        """Create chain for generating presentation content"""
        prompt = PromptTemplate(
            input_variables=["context", "topic"],
            template="""Genera 4 secciones para una presentación sobre {topic}. Usa este formato:

Sección 1 - [Título corto]
Contenido detallado: [3 puntos cortos separados por puntos]

Sección 2 - [Título corto]
Contenido detallado: [3 puntos cortos separados por puntos]

[etc...]

Contexto útil: {context}
"""
        )
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def retrieve_information(self, query: str, generate: bool = False) -> str:
        """Retrieve information from the vector store"""
        try:
            print(f"\nRAG - Procesando consulta: {query}")
            
            # Get relevant documents - reducido a 2 documentos para menor contexto
            docs = self.vector_store.similarity_search(query, k=2)
            context = "\n".join(doc.page_content for doc in docs)
            
            # Limitar el contexto a 500 caracteres
            if len(context) > 500:
                context = context[:500] + "..."
            
            print(f"\nRAG - Contexto recuperado:")
            print(context)
            
            if generate:
                print("\nRAG - Generando contenido con LLM...")
                try:
                    # Generate content using LLM
                    raw_content = self.generation_chain.run(
                        context=context if context else "No hay información específica disponible.",
                        topic=query
                    )
                    print("\nRAG - Contenido generado:")
                    print(raw_content)
                    
                    # Process the raw content into sections
                    generator = ContentGenerator(raw_content)
                    generator.process_content()
                    sections_json = generator.to_json()
                    print("\nRAG - Secciones generadas:")
                    print(sections_json)
                    
                    # Convert sections to HTML
                    html_output = self.generate_html_from_sections(json.loads(sections_json))
                    print("\nRAG - HTML generado:")
                    print(html_output)
                    return html_output
                except Exception as llm_error:
                    print(f"\nRAG - Error con LLM: {str(llm_error)}")
                    traceback.print_exc()
                    return self._get_fallback_content()
            return context
            
        except Exception as e:
            print(f"\nRAG - Error general: {str(e)}")
            traceback.print_exc()
            if generate:
                return self._get_fallback_content()
            return "Error recuperando información"

    def generate_html_from_sections(self, sections):
        """Convert sections to HTML format"""
        html_content = '<html><head><title>Presentación</title></head><body>'
        for section in sections:
            html_content += f'<h2>{section["title"]}</h2>'
            html_content += '<ul>'
            for content in section["content"]:
                html_content += f'<li>{content}</li>'
            html_content += '</ul>'
        html_content += '</body></html>'
        return html_content

    def _get_fallback_content(self) -> str:
        """Get fallback content when generation fails"""
        return """
        Sección 1 - Introducción al Tema
        Contenido detallado: Este es un tema importante en la actualidad. Tiene múltiples aplicaciones prácticas. Su impacto es significativo.

        Sección 2 - Características Principales
        Contenido detallado: Ofrece funcionalidades avanzadas. Se integra con otros sistemas. Proporciona beneficios tangibles.

        Sección 3 - Beneficios y Ventajas
        Contenido detallado: Mejora la eficiencia operativa. Reduce costos significativamente. Aumenta la productividad.

        Sección 4 - Implementación
        Contenido detallado: Requiere planificación cuidadosa. Se integra con infraestructura existente. Tiene curva de aprendizaje manejable.
        """
