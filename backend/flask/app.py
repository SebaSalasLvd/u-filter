from flask import Flask, request, jsonify
from transformers import pipeline
import torch
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging
import re
import time

# --- IMPORTS NUEVOS PARA SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import psycopg2

# --- CONFIGURACIÓN ---
USUARIO_UCURSOS = "nicolas.inostroza.n"  # Correo completo
CLAVE_UCURSOS   = "Salsadeperro12"

# Configuración de la Base de Datos
PG_CONFIG = {
    "dbname": "proyecto",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

def get_existing_links():
    """
    Obtiene los links ya guardados en Postgres para evitar duplicados.
    """
    existing_links = set()
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        
        # Asegurarse de que la tabla exista
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id BIGSERIAL PRIMARY KEY,
            post_dom_id TEXT NULL,
            post_external_id TEXT NULL,
            post_url TEXT NULL,
            post_url_domain TEXT NULL, -- Aseguramos que esta columna exista
            title TEXT NULL,
            input_text TEXT NULL,
            author TEXT NULL,
            post_date TIMESTAMPTZ NULL,
            model_name TEXT NULL,
            label TEXT NULL,
            score DOUBLE PRECISION NULL,
            candidate_labels JSONB NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            raw JSONB NULL,
            user_id UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """)
        conn.commit()
        
        cursor.execute("SELECT post_url FROM classifications")
        links = cursor.fetchall()
        
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

# --- LOGICA DEL SCRAPER CON SELENIUM ---
def run_scrapper(domain):
    saved_links = get_existing_links()
    rows = []

    print("--- INICIANDO SELENIUM ---")
    
    # Opciones de Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") # Descomenta esto si quieres que corra oculto en background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        # Instalar y lanzar driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # 0. LIMPIEZA DE COOKIES
        driver.delete_all_cookies()

        # 1. LOGIN EN U-CURSOS
        print("1. Accediendo al login...")
        driver.get("https://www.u-cursos.cl/ingenieria/2/foro_institucion/")
        
        wait = WebDriverWait(driver, 10)
        
        # Llenar Usuario
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_field.clear()
        user_field.send_keys(USUARIO_UCURSOS)
        
        # Llenar Clave
        pass_field = driver.find_element(By.NAME, "password")
        pass_field.clear()
        pass_field.send_keys(CLAVE_UCURSOS)
        
        print(f"2. Intentando entrar como: {USUARIO_UCURSOS}")
        pass_field.send_keys(Keys.RETURN) 
        
        # Esperar redirección (Dashboard)
        time.sleep(5)

        # Verificación visual rápida
        if "Visitante" in driver.page_source or "denegó el acceso" in driver.page_source:
            print("❌ ERROR: Login fallido en Selenium.")
            driver.quit()
            return
        
        print("✅ LOGIN EXITOSO. Comenzando scraping...")

        # 2. RECORRER EL FORO (Paginación)
        forum_url_base = domain
        numero_pagina = 700
        seguir = True

        while seguir:
            # Construir URL con offset
            # Nota: U-Cursos usa offsets de 10 en 10 o 20 en 20? 
            # Asumimos paginación por páginas estándar (0, 1, 2...) según tu código original
            # Si el offset es por número de posts, verifica si debe ser numero_pagina * 20
            forum_url = f"{forum_url_base}?id_tema=&offset={numero_pagina}"
            
            print(f"Navegando a offset = {numero_pagina} ...")
            driver.get(forum_url)
            time.sleep(2) # Espera prudente para cargar y no saturar

            # Obtener HTML actual y parsear con BS4
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Buscar mensajes
            mensajes = soup.find_all('div', class_='new')
            if not mensajes:
                mensajes = soup.find_all('div', class_='msg')

            # Condición de parada (Si no hay mensajes o límite de seguridad)
            if not mensajes or numero_pagina >= 735:
                print("No se encontraron más mensajes o se alcanzó el límite.")
                break

            # Procesar mensajes
            for mensaje in mensajes:
                # Título
                titulo_tag = mensaje.find('a', id='mensaje-titulo')
                titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"
                
                # Contenidos (posts hijos)
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

                    # Verificar duplicados
                    if link in saved_links:
                        print(f"Post existente ({link}). Deteniendo scraping.")
                        seguir = False
                        break

                    if texto == "Sin mensaje":
                        continue

                    # Clasificar
                    classification = classify_text(texto)
                    if not classification:
                        print("Error al clasificar el texto.")
                        continue
                    
                    categoria = classification['label']
                    print(f"Clasificado como: {categoria}")
                    score = classification['score']
                    
                    # Agregar a la lista para guardar
                    rows.append([autor, titulo, fecha_sql, texto, link, categoria, score, domain])
                
                if not seguir:
                    break
            
            numero_pagina += 1 # Siguiente página

    except Exception as e:
        print(f"Error crítico en Selenium: {e}")
    
    finally:
        print("Cerrando navegador...")
        if 'driver' in locals():
            driver.quit()

    # 3. GUARDAR EN BASE DE DATOS
    if rows:
        print(f"Se recopilaron {len(rows)} filas NUEVAS. Insertando en Postgres...")
        conn = None
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            cursor = conn.cursor()
            
            # Importante: Ajusté los nombres de columnas para coincidir con tu tabla
            sql_insert = """
            INSERT INTO classifications (author, title, post_date, input_text, post_url, label, score, post_url_domain) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING -- Ojo: post_url no es PK en tu CREATE TABLE, revisa tu constraint
            """
            # NOTA: Si post_url no tiene restricción UNIQUE en la BD, el ON CONFLICT fallará. 
            # Lo cambié a un INSERT simple para este ejemplo, o asegúrate de tener un UNIQUE INDEX en post_url.
            
            # Mejor usamos una query segura asumiendo que no tienes constraints complejos aun:
            sql_insert_simple = """
            INSERT INTO classifications (author, title, post_date, input_text, post_url, label, score, post_url_domain) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(sql_insert_simple, rows)
            conn.commit()
            print(f"¡Datos guardados exitosamente!")

        except (Exception, psycopg2.Error) as e:
            print(f"Error BD: {e}")
        finally:
            if conn:
                conn.close()
    else:
        print("No se recopilaron filas nuevas.")

# 1. Inicializar la aplicación Flask
app = Flask(__name__)

# Configurar SQLAlchemy
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
    # SQLite fallback
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'dev.db')
    sqlite_uri = f"sqlite:///{os.path.abspath(sqlite_path)}"
    app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    metadata_json = db.Column('metadata', db.JSON, nullable=True)
    raw = db.Column(db.JSON, nullable=True)
    user_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False)



MODEL_PATH = "/Users/inost/Documents/universidad/2025/proyecto_ia/entrenamiento/modelo_finetuned_ufilter"

try:
    classifier = pipeline(
        "text-classification",
        model=MODEL_PATH,
        tokenizer=MODEL_PATH,
        device=0 if torch.cuda.is_available() else -1
    )
    print("Modelo cargado exitosamente:", classifier.device)
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    classifier = None

# --- ENDPOINTS ---

@app.route('/proyecto/u-filter/backend/scrapper', methods=['POST'])
def call_scrapper():
    try:
        data = request.get_json()
        print(data)
        domain = data['domain']
        # Ejecuta la nueva lógica de Selenium
        run_scrapper(domain)
        return 'ok'
    except Exception as e:
        print(f"Error al llamar al scrapper: {e}")
        return 'not ok'

def classify_text(text_to_classify):
    if not classifier:
        return jsonify({"error": "El modelo no está cargado o no se encontró la ruta"}), 500
    
    # Obtener y validar datos
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Falta el campo 'text' en el JSON"}), 400

    text_to_classify = data['text']

    # Realizar la clasificación
    try:

        # return_all_scores=False devuelve solo la etiqueta ganadora por defecto en versiones nuevas.
        results = classifier(text_to_classify)

        # El pipeline de text-classification devuelve una lista: [{'label': 'Venta', 'score': 0.98},...]
        # Extraemos el primer resultado (el de mayor probabilidad)
        best_prediction = results[0]

        top_result = {
            "label": best_prediction['label'],
            "score": best_prediction['score']
        }

        return jsonify(top_result)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error durante la inferencia: {e}"}), 500

@app.route('/proyecto/u-filter/backend/list', methods=['GET'])
def list_by_domain():
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        return jsonify({"error": "Error DB URI"}), 500

    try:
        data = request.get_json()
        domain = data.get('domain')
        if not domain: return jsonify([])

        query = Classification.query.filter(Classification.post_url_domain == domain).order_by(Classification.created_at.desc())
        rows = query.all()
        out = []
        for c in rows:
            out.append({
                'id': c.id,
                'post_url': c.post_url,
                'title': c.title,
                'label': c.label,
                'score': c.score,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            })
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=7020)