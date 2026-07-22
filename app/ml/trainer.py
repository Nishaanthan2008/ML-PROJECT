import numpy as np
import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

# Attempt XGBoost import; fallback to sklearn's GradientBoostingClassifier if OpenMP system library is absent
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)

from app.ml.pipeline import FeaturePipeline, FEATURE_COLUMNS

class ModelTrainer:
    """Trains, benchmarks, and evaluates Random Forest, XGBoost, Logistic Regression, and SVM models."""

    def __init__(self, model_dir='saved_models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.pipeline = FeaturePipeline()
        self.best_model_name = None
        self.best_model = None

    def train_and_evaluate_all(self, df, label_col='is_bot'):
        """
        Fits pipeline and trains all 4 models.
        Returns detailed performance metrics dictionary for comparison dashboard.
        """
        X = df.drop(columns=[label_col, 'username'], errors='ignore')
        y = df[label_col].values

        # Preprocess features
        X_processed = self.pipeline.fit_transform(X)
        
        # Save pipeline state
        pipeline_path = os.path.join(self.model_dir, 'feature_pipeline.joblib')
        self.pipeline.save(pipeline_path)

        # Train-Test Split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=0.20, random_state=42, stratify=y
        )

        xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, eval_metric='logloss', random_state=42) if HAS_XGBOOST else GradientBoostingClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, random_state=42)

        models_to_train = {
            'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'XGBoost / GradientBoost': xgb_model,
            'Logistic Regression': LogisticRegression(C=1.0, max_iter=1000, random_state=42),
            'Support Vector Machine': SVC(C=1.0, kernel='rbf', probability=True, random_state=42)
        }

        results = {}
        best_f1 = -1.0

        for name, clf in models_to_train.items():
            # 5-Fold Stratified Cross-Validation
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            cv_scores = []
            
            clf.fit(X_train, y_train)
            
            y_pred = clf.predict(X_test)
            y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else clf.decision_function(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            auc = float(roc_auc_score(y_test, y_prob))
            cm = confusion_matrix(y_test, y_pred).tolist()
            
            fpr, tpr, _ = roc_curve(y_test, y_prob)

            results[name] = {
                'accuracy': round(acc, 4),
                'precision': round(prec, 4),
                'recall': round(rec, 4),
                'f1_score': round(f1, 4),
                'roc_auc': round(auc, 4),
                'confusion_matrix': cm,
                'roc_curve': {
                    'fpr': [round(x, 4) for x in fpr.tolist()[::max(1, len(fpr)//20)]],
                    'tpr': [round(y_val, 4) for y_val in tpr.tolist()[::max(1, len(tpr)//20)]]
                }
            }

            # Track best model
            if f1 > best_f1:
                best_f1 = f1
                self.best_model_name = name
                self.best_model = clf

        # Save best model to disk
        best_model_path = os.path.join(self.model_dir, 'best_profile_shield_model.joblib')
        joblib.dump({
            'model_name': self.best_model_name,
            'model': self.best_model,
            'feature_columns': FEATURE_COLUMNS,
            'metrics': results[self.best_model_name],
            'all_results': results
        }, best_model_path)

        return {
            'best_model_name': self.best_model_name,
            'best_metrics': results[self.best_model_name],
            'all_models': results
        }

if __name__ == '__main__':
    from app.ml.dataset_generator import generate_synthetic_profile_dataset
    df = generate_synthetic_profile_dataset()
    trainer = ModelTrainer()
    output = trainer.train_and_evaluate_all(df)
    print("Training finished! Best model:", output['best_model_name'])
