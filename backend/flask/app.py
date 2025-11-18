from flask import Flask, request, jsonify
from transformers import pipeline
import torch
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from scrapper.scrapper import run_scrapper

# 1. Inicializar la aplicación Flask
app = Flask(__name__)

key_words = ["venta","vendo","compro","arriendo","clases","oferta laboral","practica","práctica"]


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
    # Inicializar de todas formas
    db.init_app(app)


# Modelo ORM
class Classification(db.Model):
    __tablename__ = 'classifications'

    id = db.Column(db.BigInteger, primary_key=True)
    post_dom_id = db.Column(db.Text, nullable=True)
    post_external_id = db.Column(db.Text, nullable=True)
    post_url = db.Column(db.Text, nullable=True)
    post_url_domain = db.Column(db.Text, nullable=True)
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

# Endpoint legacy para clasificar
@app.route('/proyecto/u-filter/backend/simple', methods=['POST'])
def classify_text_legacy():
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
   
# Llamada al scrapper cuando un usuario entra al foro 
@app.route('/proyecto/u-filter/backend/scrapper/<string:domain>', methods=['POST'])
def call_scrapper(domain):
    run_scrapper(domain)

def classify_text(text_to_classify):
    # Verificar que el modelo se haya cargado
    if not classifier:
        return jsonify({"error": "El modelo no está disponible"}), 500
    
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
        result = classifier(text_to_classify, candidate_labels,hypothesis_template=hypothesis_template_es)
        top_result = {
            "label": result["labels"][0],
            "score": result["scores"][0]
        }
        return top_result

    except Exception as e:
        return None

@app.route('/proyecto/u-filter/backend/list/<string:domain>', methods=['GET'])
def list_by_domain(domain: str):
    # Si no se tiene uri
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        return jsonify({"error": "Ocurrio un error al obtener la base de datos"}), 500

    try:
        query = Classification.query.filter(Classification.post_url_domain == domain).order_by(Classification.created_at.desc())
        rows = query.all()
        out = []
        for c in rows:
            out.append({
                'id': c.id,
                'post_dom_id': c.post_dom_id,
                'post_url': c.post_url,
                'post_url_domain': c.post_url_domain,
                'title': c.title,
                'label': c.label,
                'score': c.score,
                'candidate_labels': c.candidate_labels,
                'metadata': c.metadata,
                'raw': c.raw,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            })

        return jsonify(out)

    except Exception as e:
        app.logger.error(f"Falló la query.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=7020)

    