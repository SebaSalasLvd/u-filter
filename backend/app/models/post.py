"""
Post Model

This module defines the `Post` model, which represents the `posts` table in the database.
Each post corresponds to a classified message or content scraped from a forum.

Attributes:
    id (BigInteger): Primary key for the `posts` table.
    title (Text): The title of the post.
    content (Text): The content of the post. Cannot be null.
    author (Text): The author of the post.
    post_date (Text): The date the post was created, as a string.
    post_url (Text): The URL of the post.
    classification_label (Text): The classification label assigned to the post.
    classification_score (Float): The confidence score of the classification.
    model_used (Text): The name of the model used for classification.
    link_id (BigInteger): Foreign key referencing the `links` table.
    created_at (DateTime): The timestamp when the post was created. Defaults to the current time.
"""

from app.extensions import db

class Post(db.Model):
    """
    Represents a post in the `posts` table.

    Attributes:
        id (BigInteger): Unique identifier for the post.
        title (Text): The title of the post.
        content (Text): The content of the post.
        author (Text): The author of the post.
        post_date (Text): The date the post was created.
        post_url (Text): The URL of the post.
        classification_label (Text): The classification label assigned to the post.
        classification_score (Float): The confidence score of the classification.
        model_used (Text): The name of the model used for classification.
        link_id (BigInteger): Foreign key referencing the `links` table.
        created_at (DateTime): Timestamp of when the post was created.
    """
    __tablename__ = 'posts'
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text)
    post_date = db.Column(db.Text)
    post_url = db.Column(db.Text)
    classification_label = db.Column(db.Text)
    classification_score = db.Column(db.Float)
    model_used = db.Column(db.Text)
    link_id = db.Column(db.BigInteger, db.ForeignKey('links.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())