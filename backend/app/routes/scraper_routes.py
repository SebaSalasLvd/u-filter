from flask import Blueprint, request, jsonify
from app.services.scraper_service import ScraperService
from app.models.post import Post
from app.models.link import Link
import logging

logger = logging.getLogger(__name__)

scraper_bp = Blueprint('scraper', __name__, url_prefix='/api/scraper')

@scraper_bp.route('/run', methods=['POST'])
def run_scraper():
    """
    Run the scraper for a specific domain.

    Request Body:
        - domain (str): The domain to scrape.

    Responses:
        - 200: Scraping results as JSON.
        - 400: Missing or invalid domain.
        - 500: Internal server error.
    """
    data = request.get_json()
    domain = data.get('domain')
    if not domain:
        return jsonify({"error": "Domain es requerido"}), 400
    
    try:
        result = ScraperService.run_scraper(domain)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing scraper for domain {domain}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@scraper_bp.route('/run-all', methods=['POST'])
def run_scraper_all():
    try:
        result = ScraperService.run_all_scrapers()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error crítico en run-all: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@scraper_bp.route('/list', methods=['GET'])
def list_posts_by_domain():
    """
    Lista posts con soporte para paginación y filtrado por categorías.
    
    Query Parameters:
        - page (int): Número de página (default: 1)
        - per_page (int): Items por página (default: 5)
        - domain (str): Filtrar por dominio
        - categories (str): Categorías separadas por coma (ej: "Duda,Aviso")
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    categories_str = request.args.get('categories', '')
    
    query = Post.query.join(Link).filter(
        Post.classification_label != 'Otro'
    ).order_by(Post.created_at.desc())
    
    if categories_str:
        categories = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
        if categories:
            query = query.filter(Post.classification_label.in_(categories))
            
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    output = []
    for post in pagination.items:
        output.append({
            "id": post.id,
            "title": post.title,
            "user": post.author,
            "date": post.post_date,
            "url": post.post_url,
            "label": post.classification_label,
            "score": post.classification_score,
            "text": post.content,
            "created_at": post.created_at.isoformat(),
            "model": post.model_used,
        })
    
    return jsonify({
        "posts": output,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        }
    })

@scraper_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Obtiene todas las categorías únicas disponibles en los posts.
    """
    try:
        categories = Post.query.with_entities(
            Post.classification_label
        ).distinct().all()
        
        # Filtrar valores nulos o vacíos
        category_list = [cat[0] for cat in categories if cat[0] and cat[0]!="Otro"]
        
        return jsonify({
            "categories": sorted(category_list)
        })
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500