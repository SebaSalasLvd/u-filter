from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.link import Link

links_bp = Blueprint('links', __name__, url_prefix='/api/links')

@links_bp.route('', methods=['POST'])
def add_link():
    """
    Add a new link to the database.

    Request Body:
        - url (str): The URL of the link.
        - name (str): The name or description of the link.

    Responses:
        - 201: Link created successfully.
        - 400: Error creating the link.
    """
    data = request.get_json()
    try:
        new_link = Link(url=data['url'], name=data['name'])
        db.session.add(new_link)
        db.session.commit()
        return jsonify({
            "id": new_link.id,
            "url": new_link.url,
            "name": new_link.name,
            "created_at": new_link.created_at.isoformat()
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error creando link"}), 400

@links_bp.route('', methods=['GET'])
def list_links():
    """
    List all links in the database.

    Responses:
        - 200: A list of all links, ordered by creation date.
    """
    links = Link.query.order_by(Link.created_at.desc()).all()
    return jsonify([{
        "id": l.id, "name": l.name, "url": l.url, 
        "created_at": l.created_at.isoformat()
    } for l in links])

@links_bp.route('/search', methods=['GET'])
def search_link():
    """
    Search for a link by URL or name.

    Query Parameters:
        - url (str, optional): The URL of the link to search for.
        - name (str, optional): The name of the link to search for.

    Responses:
        - 200: Link found, with its details.
        - 404: Link not found.
    """
    url_query = request.args.get('url')
    name_query = request.args.get('name')
    
    link = None
    if url_query:
        link = Link.query.filter_by(url=url_query).first()
    elif name_query:
        link = Link.query.filter_by(name=name_query).first()

    if link:
        return jsonify({
            "exists": True, 
            "forum": {
                "id": link.id, 
                "url": link.url, 
                "name": link.name
            }
        })
    
    return jsonify({"exists": False}), 404