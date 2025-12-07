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
    """
    Run the scraper for all registered links in the database.

    Responses:
        - 200: Results of the scraping process, including successes and failures.
        - 500: Internal server error.
    """
    try:
        links = Link.query.all()
        
        if not links:
            return jsonify({"message": "No hay links registrados en la base de datos."}), 200

        results = []
        errors = []

        logger.info(f"Iniciando scraping masivo para {len(links)} foros.")

        for link in links:
            try:
                logger.info(f"Procesando: {link.url}")
                scrape_result = ScraperService.run_scraper(link.url)
                
                results.append({
                    "url": link.url,
                    "status": "success",
                    "details": scrape_result
                })
            except Exception as e:
                logger.error(f"Error scrapeando {link.url}: {e}", exc_info=True)
                errors.append({
                    "url": link.url,
                    "status": "error",
                    "error": str(e)
                })

        return jsonify({
            "message": "Proceso masivo finalizado",
            "total_links": len(links),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Error crítico en run-all: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

@scraper_bp.route('/list', methods=['GET'])
def list_posts_by_domain():
    """
    List posts filtered by domain.

    Query Parameters:
        - domain (str, optional): The domain to filter posts by.

    Responses:
        - 200: A list of posts, limited to 100, ordered by creation date.
    """
    domain = request.args.get('domain')
    
    query = Post.query.join(Link).order_by(Post.created_at.desc())
    
    if domain:
        query = query.filter(Link.url.contains(domain))
        
    posts = query.limit(100).all()
    
    output = []
    for post in posts:
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
        
    return jsonify(output)