from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from rag.rag_handler import RAGHandler
from content_generation.content_generator import ContentGenerator
from template.template_manager import TemplateManager
from pdf_export.pdf_exporter import PDFExporter
from document_management.document_handler import DocumentHandler
import os
import logging
import pdfkit
import uuid
import json
from datetime import datetime
import traceback

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Initialize components
# Inicializar RAG
rag_handler = RAGHandler(
    model_path="models/llama-2-7b-chat.gguf",
    embeddings_model="intfloat/multilingual-e5-large",
    data_dir="rag/data",
    vector_store_path="rag/vector_store"
)

# Inicializar generador de contenido
content_generator = ContentGenerator(rag_handler)
template_manager = TemplateManager()
document_handler = DocumentHandler(base_dir='path/to/documents')
pdf_exporter = PDFExporter(document_handler)

# Directorio para almacenar presentaciones
PRESENTATIONS_DIR = os.path.join(os.path.dirname(__file__), 'presentations')
os.makedirs(PRESENTATIONS_DIR, exist_ok=True)
app.config['PRESENTATIONS_FOLDER'] = PRESENTATIONS_DIR

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data['message']
    history = data['history']
    
    # Use RAG to get context and generate response
    context = rag_handler.retrieve_information(message, generate=True)
    
    # Generate assistant response
    response = "Entiendo que quieres una presentación sobre " + message + ". "
    response += "Puedo ayudarte con eso. ¿Hay algo específico que te gustaría incluir?"
    
    return jsonify({'response': response})

@app.route('/generate', methods=['POST'])
def generate_presentation():
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        
        print(f"\nGenerando presentación sobre: {topic}")
        
        # Generar ID único para la presentación
        presentation_id = str(uuid.uuid4())
        
        # Generar contenido usando RAG
        slides = content_generator.generate_content(topic)
        
        print("\nSlides generados:")
        for slide in slides:
            print(f"\nTítulo: {slide.title}")
            print("Contenido:")
            for point in slide.content:
                print(f"- {point}")
        
        # Convertir slides a formato JSON
        slides_data = []
        for slide in slides:
            slide_dict = {
                'title': slide.title,
                'content': slide.content if isinstance(slide.content, list) else [slide.content],
                'notes': slide.notes
            }
            slides_data.append(slide_dict)
        
        # Crear datos de la presentación
        presentation_data = {
            'id': presentation_id,
            'topic': topic,
            'slides': slides_data
        }
        
        # Guardar los datos en un archivo
        presentation_file = os.path.join(app.config['PRESENTATIONS_FOLDER'], f'{presentation_id}.json')
        with open(presentation_file, 'w', encoding='utf-8') as f:
            json.dump(presentation_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nPresentación guardada en: {presentation_file}")
        
        return jsonify({
            'id': presentation_id,
            'message': 'Presentación generada exitosamente',
            'slides': slides_data
        })
        
    except Exception as e:
        print(f"Error generando presentación: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/view/<presentation_id>')
def view_presentation(presentation_id):
    try:
        # Cargar el archivo JSON de la presentación
        presentation_file = os.path.join(app.config['PRESENTATIONS_FOLDER'], f'{presentation_id}.json')
        if not os.path.exists(presentation_file):
            return "Presentación no encontrada", 404

        with open(presentation_file, 'r', encoding='utf-8') as f:
            presentation_data = json.load(f)
            
        # Extraer el título del primer slide o usar uno por defecto
        title = "Presentación"
        if isinstance(presentation_data, dict) and 'slides' in presentation_data:
            slides = presentation_data['slides']
        else:
            slides = presentation_data if isinstance(presentation_data, list) else []
            
        if slides and slides[0].get('title'):
            title = slides[0]['title']

        return render_template('presentation.html', 
                             presentation_id=presentation_id,
                             title=title)
    except Exception as e:
        print(f"Error viewing presentation: {str(e)}")
        return "Error interno del servidor", 500

@app.route('/presentation/<presentation_id>/data')
def get_presentation_data(presentation_id):
    try:
        # Cargar el archivo JSON de la presentación
        presentation_file = os.path.join(app.config['PRESENTATIONS_FOLDER'], f'{presentation_id}.json')
        if not os.path.exists(presentation_file):
            return jsonify({'error': 'Presentación no encontrada'}), 404

        with open(presentation_file, 'r', encoding='utf-8') as f:
            presentation_data = json.load(f)
            
        # Asegurarse de que los datos tienen el formato correcto
        if not isinstance(presentation_data, dict) or 'slides' not in presentation_data:
            presentation_data = {
                'slides': presentation_data if isinstance(presentation_data, list) else []
            }
            
        return jsonify(presentation_data)
    except Exception as e:
        print(f"Error loading presentation data: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/download/<presentation_id>')
def download_pdf(presentation_id):
    try:
        # Load presentation data
        with open(os.path.join(app.config['PRESENTATIONS_FOLDER'], f'{presentation_id}.json'), 'r', encoding='utf-8') as f:
            presentation_data = json.load(f)
        
        # Generate HTML content
        html_content = render_template('presentation.html',
                                     title=presentation_data['topic'],
                                     content=presentation_data['slides'],
                                     presentation_id=presentation_id)
        
        # Convert to PDF
        pdf_path = os.path.join(app.config['PRESENTATIONS_FOLDER'], f'{presentation_id}.pdf')
        pdfkit.from_string(html_content, pdf_path)
        
        return send_file(pdf_path, 
                        as_attachment=True, 
                        download_name='presentacion.pdf')
    except Exception as e:
        logging.error(f'Error downloading PDF: {str(e)}')
        return "Error al generar PDF", 500

if __name__ == '__main__':
    app.run(debug=True)
