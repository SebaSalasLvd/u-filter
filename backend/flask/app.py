from flask import Flask, request, jsonify
from transformers import pipeline
import torch
import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# 1. Inicializar la aplicación Flask
app = Flask(__name__)

# Configurar SQLAlchemy si hay variables de entorno
db = SQLAlchemy()
db_user = os.getenv('DB_USER')
db_name = os.getenv('DB_NAME')
if db_user and db_name:
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
else:
    # Inicializar de todas formas; operaciones fallarán si no hay URI
    db.init_app(app)

key_words = ["venta","vendo","compro","arriendo","clases","oferta laboral","practica","práctica"]


# Modelo ORM para clasificaciones
class Classification(db.Model):
    __tablename__ = 'classifications'

    id = db.Column(db.BigInteger, primary_key=True)
    post_dom_id = db.Column(db.Text, nullable=True)
    post_external_id = db.Column(db.Text, nullable=True)
    post_url = db.Column(db.Text, nullable=True)
    title = db.Column(db.Text, nullable=True)
    input_text = db.Column(db.Text, nullable=True)
    author = db.Column(db.Text, nullable=True)
    post_date = db.Column(db.DateTime(timezone=True), nullable=True)
    model_name = db.Column(db.Text, nullable=True)
    label = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    candidate_labels = db.Column(db.JSON, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    raw = db.Column(db.JSON, nullable=True)
    user_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

# 2. Cargar el modelo de clasificación de texto
# Usamos un pipeline para simplificar. "zero-shot-classification" es ideal
# porque te permite definir tus propias categorías al momento, sin re-entrenar.
# Model: facebook/bart-large-mnli -> Un modelo popular y robusto para esta tarea.
try:
    classifier = pipeline(
        "zero-shot-classification",
        model="Recognai/bert-base-spanish-wwm-cased-xnli",
        device=0 if torch.cuda.is_available() else -1 # Usa GPU si está disponible
    )
    print("Modelo cargado exitosamente en el dispositivo:", classifier.device)
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    classifier = None

# 3. Definir el endpoint de la API para clasificación
@app.route('/proyecto/u-filter/backend', methods=['POST'])
def classify_text():
    # Verificar que el modelo se haya cargado
    if not classifier:
        return jsonify({"error": "El modelo no está disponible"}), 500

    # Obtener los datos del cuerpo de la petición (request)
    data = request.get_json()

    # Validar que los datos de entrada son correctos
    if not data or 'text' not in data :
        return jsonify({"error": "Falta el campo 'text' en el JSON"}), 400

    text_to_classify = data['text']
    candidate_labels = ["Otro","Arriendo","Oferta laboral/practica","Clases Particulares","Venta","Compra"]
    for word in key_words:
        if word.lower() in text_to_classify.lower():
            candidate_labels.remove("Otro")
            match word.lower():
                case "venta" | "vendo":
                    candidate_labels.remove("Arriendo")
                    candidate_labels.remove("Clases Particulares")
                case "compro":
                    candidate_labels.remove("Arriendo")
                    candidate_labels.remove("Clases Particulares")
            break
    hypothesis_template_es = "Este texto representa una publicacion que esta intentando ofrecer o promocionar una(s) {}"
    # Realizar la clasificación
    try:
        result = classifier(text_to_classify, candidate_labels, hypothesis_template=hypothesis_template_es)
        top_result = {
            "label": result["labels"][0],
            "score": result["scores"][0]
        }

        # Si el cliente envía un objeto `post`, intentamos guardar la clasificación en la BD usando SQLAlchemy
        post = data.get('post') if isinstance(data, dict) else None
        if post:
            try:
                # Construir lista de candidate labels con scores
                candidate_list = []
                for lbl, sc in zip(result.get('labels', []), result.get('scores', [])):
                    candidate_list.append({'label': lbl, 'score': float(sc)})

                # Parsear fecha (si viene en formato 'YYYY-MM-DD HH:MM:SS' o ISO)
                post_date = None
                raw_date = post.get('date') if isinstance(post, dict) else None
                if raw_date:
                    try:
                        post_date = datetime.fromisoformat(raw_date)
                    except Exception:
                        try:
                            post_date = datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')
                        except Exception:
                            post_date = None

                # Verificar que la app tiene configurada la URI de la DB
                if not app.config.get('SQLALCHEMY_DATABASE_URI'):
                    app.logger.warning('SQLALCHEMY_DATABASE_URI no configurada; omitiendo guardado.')
                else:
                    classification = Classification(
                        post_dom_id=str(post.get('id')) if post.get('id') is not None else None,
                        post_external_id=None,
                        post_url=post.get('link'),
                        title=post.get('title'),
                        input_text=post.get('text'),
                        author=post.get('user'),
                        post_date=post_date,
                        model_name='Recognai/bert-base-spanish-wwm-cased-xnli',
                        label=top_result['label'],
                        score=float(top_result['score']) if top_result.get('score') is not None else None,
                        candidate_labels=candidate_list,
                        metadata={'source': 'content-script'},
                        raw=post
                    )
                    db.session.add(classification)
                    db.session.commit()
            except Exception as e:
                app.logger.error(f"Error guardando clasificación en DB (SQLAlchemy): {e}")

        return jsonify(top_result)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error durante la clasificación: {e}"}), 500

# 4. Ejecutar la aplicación
if __name__ == '__main__':
    # El puerto 5000 es el predeterminado de Flask
    app.run(debug=True, port=7020)

    