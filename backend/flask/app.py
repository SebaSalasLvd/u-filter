from flask import Flask, request, jsonify
from transformers import pipeline
import torch

# 1. Inicializar la aplicación Flask
app = Flask(__name__)

# 2. Cargar el modelo de clasificación de texto
# Usamos un pipeline para simplificar. "zero-shot-classification" es ideal
# porque te permite definir tus propias categorías al momento, sin re-entrenar.
# Model: facebook/bart-large-mnli -> Un modelo popular y robusto para esta tarea.
try:
    classifier = pipeline(
        "zero-shot-classification",
        #model="facebook/bart-large-mnli",
        model="Recognai/bert-base-spanish-wwm-cased-xnli",
        device=0 if torch.cuda.is_available() else -1 # Usa GPU si está disponible
    )
    print("Modelo cargado exitosamente en el dispositivo:", classifier.device)
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    classifier = None

# 3. Definir el endpoint de la API para clasificación
@app.route('/classify', methods=['POST'])
def classify_text():
    # Verificar que el modelo se haya cargado
    if not classifier:
        return jsonify({"error": "El modelo no está disponible"}), 500

    # Obtener los datos del cuerpo de la petición (request)
    data = request.get_json()

    # Validar que los datos de entrada son correctos
    if not data or 'text' not in data :
        return jsonify({"error": "Faltan los campos 'text' o 'categories' en el JSON"}), 400

    text_to_classify = data['text']
    candidate_labels = ["Arriendo","Oferta laboral/practica","Oferta Clases Particulares","Busqueda Clases Particulares","Venta Entrada","Venta Tecnologia","Venta Comida","Compra Tecnologia","Compra Comida","Compra Entrada"]
    hypothesis_template_es = "Este ejemplo es {}"
    # Realizar la clasificación
    try:
        # El parámetro multi_label=True permite que el texto pertenezca a varias categorías.
        # Cámbialo a False si solo quieres la categoría más probable.
        result = classifier(text_to_classify, candidate_labels,hypothesis_template=hypothesis_template_es, multi_label=False)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error durante la clasificación: {e}"}), 500

# 4. Ejecutar la aplicación
if __name__ == '__main__':
    # El puerto 5000 es el predeterminado de Flask
    app.run(debug=True, port=5000)

    