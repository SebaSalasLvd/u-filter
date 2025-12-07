import os
from flask import Flask
from flask_cors import CORS
from app.extensions import db
from app.routes.classify_routes import classify_bp 
from app.routes.link_routes import links_bp
from app.routes.scraper_routes import scraper_bp

def create_app():
    app = Flask(__name__)
    
    CORS(app)
    
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'proyecto')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(classify_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(scraper_bp)

    return app