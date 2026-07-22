from datetime import datetime
import json
from app import db

class MLModelRegistry(db.Model):
    """Tracks machine learning models, cross-validation evaluation scores, and active production model selection."""
    __tablename__ = 'ml_models'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False) # e.g. XGBoost, Random Forest, Logistic Regression, SVM
    version = db.Column(db.String(50), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    
    # Evaluation Metrics
    accuracy = db.Column(db.Float, default=0.0)
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    roc_auc = db.Column(db.Float, default=0.0)
    
    # Stored evaluation artifacts
    confusion_matrix_json = db.Column(db.Text, nullable=True) # 2x2 matrix
    all_models_comparison_json = db.Column(db.Text, nullable=True) # Benchmarks for RF, XGB, LR, SVM
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def confusion_matrix(self):
        return json.loads(self.confusion_matrix_json) if self.confusion_matrix_json else []

    @confusion_matrix.setter
    def confusion_matrix(self, value):
        self.confusion_matrix_json = json.dumps(value)

    @property
    def all_models_comparison(self):
        return json.loads(self.all_models_comparison_json) if self.all_models_comparison_json else {}

    @all_models_comparison.setter
    def all_models_comparison(self, value):
        self.all_models_comparison_json = json.dumps(value)

    def __repr__(self):
        return f"<MLModelRegistry {self.model_name} v{self.version} (Active={self.is_active}, F1={self.f1_score:.4f})>"
