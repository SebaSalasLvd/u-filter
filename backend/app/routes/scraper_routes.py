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

# app/routes/scraper_routes.py

@scraper_bp.route('/run-all', methods=['POST'])
def run_scraper_all():
    try:
        # Ahora llamamos al método estático del servicio
        result = ScraperService.run_all_scrapers()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error crítico en run-all: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@scraper_bp.route('/list', methods=['GET'])
def list_posts_by_domain():
    # Obtener parámetros de paginación (por defecto página 1, 20 items por página)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    domain = request.args.get('domain')
    
    query = Post.query.join(Link).order_by(Post.created_at.desc())
    
    if domain:
        query = query.filter(Link.url.contains(domain))
        
    # Usar paginate de SQLAlchemy
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
            "created_at": post.created_at.isoformat()
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
        
    return jsonify(output)