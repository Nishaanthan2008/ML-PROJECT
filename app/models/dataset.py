from datetime import datetime
from app import db

class Dataset(db.Model):
    """Stores metadata of uploaded and system training datasets."""
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    num_rows = db.Column(db.Integer, default=0)
    num_features = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Dataset {self.filename} ({self.num_rows} rows)>"
