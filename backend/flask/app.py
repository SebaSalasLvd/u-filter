from flask import Flask, request, jsonify
from transformers import pipeline
import torch
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging
import re
import time

# --- IMPORTS SELENIUM ---
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
USUARIO_UCURSOS = "nicolas.inostroza.n"
CLAVE_UCURSOS   = "Salsadeperro12"

# Configuración de la Base de Datos
PG_CONFIG = {
    "dbname": "proyecto",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

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



@app.route('/proyecto/u-filter/backend/scrapper', methods=['POST'])
def call_scrapper():
    try:
        data = request.get_json()
        domain = data.get('domain', 'unknown')
        
        # Ejecución directa (Síncrona)
        # El navegador web esperará aquí hasta que termine Selenium
        run_scrapper(domain)
        
        return jsonify({"status": "ok", "message": "Scraping finalizado"}), 200
    except Exception as e:
        print(f"Error endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/proyecto/u-filter/backend/list', methods=['GET'])
def list_by_domain():
    try:
        data = request.get_json() 
        domain = data.get('domain')
        if not domain: return jsonify([])

        query = Classification.query.filter(Classification.post_url_domain == domain).order_by(Classification.created_at.desc())
        rows = query.all()
        out = [{
            'id': c.id,
            'post_url': c.post_url,
            'title': c.title,
            'label': c.label,
            'score': c.score,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        } for c in rows]
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # threaded=False fuerza ejecución simple si lo prefieres, 
    # aunque 'run' por defecto en flask de desarrollo es single-threaded.
    app.run(debug=True, port=7020)