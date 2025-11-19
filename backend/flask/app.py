from flask import Flask, request, jsonify
from transformers import pipeline
import torch
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging
# from scrapper.scrapper import run_scrapper

import requests
import re
import csv
from bs4 import BeautifulSoup
import psycopg2  # NUEVO (POSTGRES): Importamos psycopg2 en lugar de sqlite3
import requests as _requests


# ---Configuración de la Base de Datos ---
# Modifica estos valores con los que creaste en el Paso 1
PG_CONFIG = {
    "dbname": "proyecto",
    "user": "postgres",
    "password": "password",
    "host": "localhost",  # IP
    "port": "5432"        # Puerto por defecto de Postgres
}
API_URL = "https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend"


def get_existing_links():
    """
    Se conecta a la base de datos PostgreSQL y obtiene un set de todos los
    links de la tabla 'mensajes' para evitar duplicados.
    """
    existing_links = set()
    conn = None  # Inicia la conexión como None
    try:
        # Conectarse a la BD de Postgres
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        
        # Asegurarse de que la tabla exista 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id BIGSERIAL PRIMARY KEY,
            post_dom_id TEXT NULL,
            post_external_id TEXT NULL,
            post_url TEXT NULL,
            title TEXT NULL,
            input_text TEXT NULL,
            author TEXT NULL,
            post_date TIMESTAMPTZ NULL,

            -- clasificacion
            model_name TEXT NULL,
            label TEXT NULL,
            score DOUBLE PRECISION NULL,
            candidate_labels JSONB NULL,

            -- datos libres y raw
            metadata JSONB DEFAULT '{}'::jsonb,
            raw JSONB NULL,

            user_id UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        conn.commit() # Guardar la creación de la tabla
        
        # Obtener todos los links
        cursor.execute("SELECT post_url FROM classifications")
        links = cursor.fetchall()
        
        # Añadirlos al set (fila[0] es el primer campo)
        for fila in links:
            if fila[0]:
                existing_links.add(fila[0])
                
        print(f"Se cargaron {len(existing_links)} links existentes desde la BD Postgres.")

    except (Exception, psycopg2.Error) as e:
        print(f"Error al leer links de la BD Postgres: {e}")
    finally:
        if conn:
            conn.close()
            
    return existing_links



# url objetivo
login_url = "https://www.u-cursos.cl/upasaporte/adi"

# datos usuario y contraseña
login_data = {
    "servicio": "ucursos",
    "debug": "0",
    "extras[_LB]": "ucursos03-int",
    "extras[lang]": "es",
    "extras[_sess]": "dc57oo5eb9fd48pshd67cen9r1",
    "extras[recordar]": "1",
    "username": "usuario",
    "password": "contraseña",
    "recordar": "1"
}

def run_scrapper(domain):
    # NUEVO: Cargar los links que ya tenemos ANTES de empezar
    saved_links = get_existing_links()

    session = requests.Session()
    response = session.post(login_url, data=login_data)
    rows = []

    if response.status_code == 200:
        print("Login exitoso!")

        forum_url_base = domain
        numero_pagina = 0
        seguir = True
        while seguir:
            forum_url = f"{forum_url_base}?id_tema=&offset={numero_pagina}"
            print(f"Obteniendo offset = {numero_pagina} …")
            forum_page = session.get(forum_url)

            soup = BeautifulSoup(forum_page.text, 'html.parser')

            mensajes = [
                div for div in soup.find_all('div', class_='new')
            ]
            if mensajes and numero_pagina < 735:
                print(f"scrapeando pagina {numero_pagina}")
            else:
                print("No se encontraron más mensajes o se alcanzó el límite.")
                break

            for mensaje in mensajes:
                titulo_tag = mensaje.find('a', id='mensaje-titulo')
                titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"
                contenidos = [
                    div for div in mensaje.find_all('div', class_='msg')
                    if 'hijo' not in div.get('class', [])
                ]

                for contenido in contenidos:
                    autor_tag = contenido.find('a', class_='usuario')
                    autor = autor_tag.text.strip() if autor_tag else "Desconocido"
                    fecha_tag = contenido.find('span', class_='tiempo_rel')
                    fecha_texto_completo = fecha_tag.text.strip() if fecha_tag else "0000-00-00"
                    fecha_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', fecha_texto_completo)
                    fecha_sql = fecha_match.group() if fecha_match else "0000-00-00"
                    texto_tag = contenido.find('span', class_='ta')
                    texto = texto_tag.get_text(separator="\n", strip=True) if texto_tag else "Sin mensaje"
                    link_tag = contenido.find('a', class_='permalink')
                    link = link_tag['href'] if link_tag and link_tag.has_attr('href') else "Desconocido"

                    if link in saved_links:
                        print(f"\nPost encontrado ya existe en la BD (Link: {link}).")
                        print("Deteniendo el scraping para evitar duplicados.")
                        seguir = False
                        break

                    if texto == "Sin mensaje":
                        continue

                    # Llamar al endpoint del backend para clasificar el texto
                    try:
                        resp = _requests.post(API_URL, json={"text": texto}, timeout=10)
                        if resp.status_code != 200:
                            print(f"Error al clasificar (status {resp.status_code}): {resp.text}")
                            continue
                        classification = resp.json()
                        categoria = classification.get('label')
                        score = classification.get('score')
                    except Exception as e:
                        print(f"Error llamando al API de clasificación: {e}")
                        continue
                    rows.append([autor, titulo, fecha_sql, texto, link, categoria, score, domain])
                
                if not seguir:
                    break
            
            numero_pagina += 1
    else:
        print("Error al intentar iniciar sesión.")


    if rows:
        print(f"Se recopilaron {len(rows)} filas NUEVAS. Insertando en la base de datos Postgres...")
        
        conn = None
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            cursor = conn.cursor()
            
            sql_insert = """
            INSERT INTO mensajes (author, title, post_date, input_text, post_url, label, score, post_url_domain) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_url) DO NOTHING
            """
            
            cursor.executemany(sql_insert, rows)

            conn.commit() # Guardar los cambios en la BD
            print(f"¡Datos guardados exitosamente en la base de datos Postgres!")

        except (Exception, psycopg2.Error) as e:
            print(f"Ocurrió un error con la base de datos Postgres: {e}")
            
        finally:
            if conn:
                conn.close()
                print("Conexión a la base de datos Postgres cerrada.")

    else:
        print("No se recopilaron filas nuevas. La base de datos está actualizada.")

    print("Proceso completado.")

# 1. Inicializar la aplicación Flask
app = Flask(__name__)

key_words = ["venta","vendo","compro","arriendo","clases","oferta laboral","practica","práctica"]


# Configurar SQLAlchemy si hay variables de entorno
db = SQLAlchemy()
logger = logging.getLogger(__name__)
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
    # No hay variables de entorno para Postgres: usar una DB SQLite local para desarrollo
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'dev.db')
    sqlite_uri = f"sqlite:///{os.path.abspath(sqlite_path)}"
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    logger.warning('No se encontraron variables DB_USER/DB_NAME: usando SQLite de desarrollo en %s', sqlite_path)
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
    # 'metadata' is a reserved attribute name on Declarative base; use attribute
    # name `metadata_json` and map it to column name 'metadata'
    metadata_json = db.Column('metadata', db.JSON, nullable=True)
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
                'metadata': c.metadata_json,
                'raw': c.raw,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            })

        return jsonify(out)

    except Exception as e:
        app.logger.error(f"Falló la query.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=7020)

    