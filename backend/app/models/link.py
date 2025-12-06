from app.extensions import db

class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column(db.BigInteger, primary_key=True)
    url = db.Column(db.Text, unique=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    posts = db.relationship('Post', backref='link', lazy=True)