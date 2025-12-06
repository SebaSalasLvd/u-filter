from app.extensions import db

class Post(db.Model):
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