# PROFILE SHIELD AI

**Tagline:** *Next Generation Social Profile Trust Intelligence Platform*

PROFILE SHIELD AI is a commercial-grade, AI-powered social profile security intelligence platform. Rather than binary fake/real classification, the platform functions like an AI Security Analyst producing multi-dimensional Trust Intelligence Reports (0-100 Trust Score), Digital DNA fingerprints (`BHV-87231`), 7-axis Trust Radars, 5-stage Evolution Timelines, 24/7 Activity Heatmaps, SHAP explainability, side-by-side profile comparison, CSV batch scanning, printable PDF exports, and an automated multi-model ML retraining suite.

---

## Key Features

1. **AI Trust Score (0-100)**: Multi-dimensional trust score with animated confidence ring and health status.
2. **Digital DNA Fingerprint**: Generates a unique behavior ID (e.g. `BHV-87231`) summarizing the profile's digital signature.
3. **7-Axis Trust Radar**: Chart analyzing *Activity, Engagement, Popularity, Consistency, Completeness, Credibility, and Authenticity*.
4. **Behaviour Evolution Timeline**: Visualizes profile history across 5 stages (*Initial Registration $\rightarrow$ Early Audience Building $\rightarrow$ Activity Shift $\rightarrow$ Mid-Term Pattern $\rightarrow$ Current Assessment*).
5. **24/7 Activity Heatmap**: Interactive posting matrix by day of week and hour of day.
6. **Natural Language AI Narrative & SHAP**: AI Security Analyst narrative explainability with waterfall bar chart of anomaly drivers.
7. **Behavioural Clustering**: Categorizes accounts into *Natural, Influencer, Business, Bot-like, Spam, Inactive, or Growing*.
8. **Side-by-Side Profile Comparator**: Compare 2 profiles simultaneously with dual radar chart overlay and differential score metrics.
9. **Batch CSV Scanner & Audit Log**: Upload CSV files for bulk analysis; filter and search historical scans.
10. **Multi-Model Benchmark & Retraining Suite**: Admin suite evaluating **Random Forest, XGBoost, Logistic Regression, and Support Vector Machine (SVM)** with 5-fold Cross-Validation & confusion matrices. Auto-selects best model.
11. **Official PDF Export**: Professional report generation for compliance and sharing.

---

## Tech Stack

- **Backend**: Python 3.14, Flask (Blueprint Architecture), SQLAlchemy, SQLite, Gunicorn
- **Machine Learning**: Scikit-Learn, XGBoost, SHAP, Joblib, Pandas, NumPy
- **Frontend**: Bootstrap 5 (Dark/Light mode switch, Glassmorphism UI), Chart.js, Plotly
- **Reporting**: ReportLab PDF Exporter

---

## Quick Start & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Train Models
Run the seeder script to populate initial sample data and train the ML models:
```bash
python seed.py
```

### 3. Launch Application Server
```bash
python app.py
```

Open your browser and navigate to: **http://127.0.0.1:5000/**

---

## Default Access Credentials

- **Administrator**: `admin@profileshield.ai` / `Admin123!`
- **Analyst**: `analyst@profileshield.ai` / `Analyst123!`
