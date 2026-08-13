import numpy as np
import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

# Attempt XGBoost import; fallback to GradientBoostingClassifier if unavailable
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


SUPPORTED_MODELS = {
    'random_forest': {
        'name': 'Random Forest',
        'factory': lambda: RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    },
    'gradient_boosting': {
        'name': 'Gradient Boosting',
        'factory': lambda: GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    },
    'logistic_regression': {
        'name': 'Logistic Regression',
        'factory': lambda: LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    },
    'xgboost': {
        'name': 'XGBoost' if HAS_XGBOOST else 'Gradient Boosting (XGBoost Fallback)',
        'factory': lambda: (
            xgb.XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.08,
                eval_metric='logloss', random_state=42, verbosity=0
            ) if HAS_XGBOOST else GradientBoostingClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.08, random_state=42
            )
        )
    }
}


class ModelTrainer:
    """
    Trains, benchmarks, and evaluates:
      - Random Forest
      - Gradient Boosting
      - Logistic Regression
      - XGBoost (or GradientBoosting fallback)
    """

    def __init__(self, model_dir: str = 'saved_models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.pipeline = FeaturePipeline()
        self.best_model_name: str | None = None
        self.best_model = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_label_col(df: pd.DataFrame) -> str:
        """Return the label column name, supporting 'label' and 'is_bot'."""
        for candidate in ('label', 'is_bot'):
            if candidate in df.columns:
                return candidate
        raise ValueError(
            "Dataset must contain a 'label' column (0 = genuine, 1 = bot). "
            f"Found columns: {list(df.columns)}"
        )

    def _prepare_data(self, df: pd.DataFrame):
        label_col = self._resolve_label_col(df)

        df = df.copy()
        df[label_col] = pd.to_numeric(df[label_col], errors='coerce').fillna(0).astype(int)

        drop_cols = [label_col, 'username', 'display_name', 'platform']
        X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')
        y = df[label_col].values

        X_processed = self.pipeline.fit_transform(X)

        pipeline_path = os.path.join(self.model_dir, 'feature_pipeline.joblib')
        self.pipeline.save(pipeline_path)

        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=0.20, random_state=42, stratify=y
        )
        return X_train, X_test, y_train, y_test

    def _evaluate_classifier(self, clf, X_train, X_test, y_train, y_test):
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        y_prob = (
            clf.predict_proba(X_test)[:, 1]
            if hasattr(clf, 'predict_proba')
            else clf.decision_function(X_test)
        )

        acc  = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec  = float(recall_score(y_test, y_pred, zero_division=0))
        f1   = float(f1_score(y_test, y_pred, zero_division=0))
        auc  = float(roc_auc_score(y_test, y_prob))
        cm   = confusion_matrix(y_test, y_pred).tolist()

        fpr, tpr, _ = roc_curve(y_test, y_prob)
        step = max(1, len(fpr) // 20)

        metrics = {
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1_score': round(f1, 4),
            'roc_auc': round(auc, 4),
            'confusion_matrix': cm,
            'roc_curve': {
                'fpr': [round(v, 4) for v in fpr.tolist()[::step]],
                'tpr': [round(v, 4) for v in tpr.tolist()[::step]],
            },
        }
        return metrics

    def save_as_production_model(self, model_object, model_name: str, metrics: dict, all_results: dict = None):
        """Persist model as the active production model."""
        best_model_path = os.path.join(self.model_dir, 'best_profile_shield_model.joblib')
        joblib.dump(
            {
                'model_name': model_name,
                'model': model_object,
                'feature_columns': FEATURE_COLUMNS,
                'metrics': metrics,
                'all_results': all_results or {},
            },
            best_model_path,
        )
        print(f"[DEBUG] Production model updated: {model_name} at {best_model_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train_single_model(self, df: pd.DataFrame, model_key: str) -> dict:
        """
        Trains a single selected algorithm.
        """
        if model_key not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model key '{model_key}'. Must be one of {list(SUPPORTED_MODELS.keys())}")

        model_info = SUPPORTED_MODELS[model_key]
        model_name = model_info['name']

        print(f"[DEBUG] Selected model from request: {model_key}")
        print(f"[DEBUG] Training model: {model_name}")

        X_train, X_test, y_train, y_test = self._prepare_data(df)
        clf = model_info['factory']()
        metrics = self._evaluate_classifier(clf, X_train, X_test, y_train, y_test)

        single_model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
        joblib.dump(
            {
                'model_name': model_name,
                'algorithm_key': model_key,
                'model': clf,
                'feature_columns': FEATURE_COLUMNS,
                'metrics': metrics,
            },
            single_model_path,
        )
        print(f"[DEBUG] Model saved: {single_model_path}")

        return {
            'model_name': model_name,
            'algorithm_key': model_key,
            'metrics': metrics,
            'model': clf,
            'filepath': single_model_path,
        }

    def train_and_evaluate_all(self, df: pd.DataFrame) -> dict:
        """
        Fits pipeline, trains all models, evaluates, and persists individual models & best model.
        """
        X_train, X_test, y_train, y_test = self._prepare_data(df)
        results: dict = {}
        best_f1 = -1.0

        for key, info in SUPPORTED_MODELS.items():
            name = info['name']
            try:
                clf = info['factory']()
                metrics = self._evaluate_classifier(clf, X_train, X_test, y_train, y_test)
                results[name] = metrics

                single_path = os.path.join(self.model_dir, f"{key}.joblib")
                joblib.dump(
                    {
                        'model_name': name,
                        'algorithm_key': key,
                        'model': clf,
                        'feature_columns': FEATURE_COLUMNS,
                        'metrics': metrics,
                    },
                    single_path,
                )

                if metrics['f1_score'] > best_f1:
                    best_f1 = metrics['f1_score']
                    self.best_model_name = name
                    self.best_model = clf

            except Exception as exc:
                results[name] = {
                    'accuracy': 0.0, 'precision': 0.0,
                    'recall': 0.0, 'f1_score': 0.0,
                    'roc_auc': 0.0, 'confusion_matrix': [],
                    'error': str(exc),
                }

        if self.best_model is None:
            raise RuntimeError("All models failed to train. Check your dataset.")

        self.save_as_production_model(
            self.best_model,
            self.best_model_name,
            results[self.best_model_name],
            all_results=results
        )

        return {
            'best_model_name': self.best_model_name,
            'best_metrics': results[self.best_model_name],
            'all_models': results,
        }

