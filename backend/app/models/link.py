"""
Link Model

This module defines the `Link` model, which represents the `links` table in the database.
Each link corresponds to a forum or external resource and may have associated posts.

Attributes:
    id (BigInteger): Primary key for the `links` table.
    url (Text): The URL of the link. Must be unique and cannot be null.
    name (Text): The name or description of the link. Cannot be null.
    created_at (DateTime): The timestamp when the link was created. Defaults to the current time.
    posts (relationship): A one-to-many relationship with the `Post` model. Represents all posts associated with this link.
"""

from app.extensions import db

class Link(db.Model):
    """
    Represents a link in the `links` table.

    Attributes:
        id (BigInteger): Unique identifier for the link.
        url (Text): The URL of the link.
        name (Text): A descriptive name for the link.
        created_at (DateTime): Timestamp of when the link was created.
        posts (relationship): Relationship to the `Post` model.
    """
    __tablename__ = 'links'
    id = db.Column(db.BigInteger, primary_key=True)
    url = db.Column(db.Text, unique=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    posts = db.relationship('Post', backref='link', lazy=True)