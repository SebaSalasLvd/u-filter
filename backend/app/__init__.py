import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_apscheduler import APScheduler 
from app.extensions import db
from app.routes.classify_routes import classify_bp 
from app.routes.link_routes import links_bp
from app.routes.scraper_routes import scraper_bp
from app.services.scraper_service import ScraperService 

# Configuración básica de logging para ver cuándo se ejecuta el job
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    CORS(app)
    
    # Configuración de Base de Datos
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'proyecto')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)

    # Registrar Blueprints
    app.register_blueprint(classify_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(scraper_bp)

    # --- CONFIGURACIÓN DEL SCHEDULER (TAREAS AUTOMÁTICAS) ---
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # Definir la tarea: Intervalo de 1 hora
    @scheduler.task('interval', id='scrape_all_job', hours=1)
    def scheduled_scraping_job():
        """
        Esta función se ejecutará automáticamente cada 1 hora.
        """
        # Es CRÍTICO usar app_context() para acceder a la BD desde un hilo secundario
        with app.app_context():
            logger.info("🕒 [Scheduler] Iniciando scraping masivo automático...")
            try:
                # Llamamos al método estático que definimos en ScraperService
                result = ScraperService.run_all_scrapers()
                logger.info(f"✅ [Scheduler] Finalizado. Total foros procesados: {result.get('total', 0)}")
            except Exception as e:
                logger.error(f"❌ [Scheduler] Error durante la ejecución automática: {e}")

    return app