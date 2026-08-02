# BluePrintCost &mdash; AI Construction Cost Estimator (MVP)

BluePrintCost is an AI-powered web application that estimates construction costs from building blueprints using Machine Learning and Explainable AI (SHAP). Users can upload blueprints in **SVG, PNG, JPG/JPEG, or PDF** format, automatically extract architectural features, predict construction costs using a trained **HistGradientBoostingRegressor**, and visualize the key factors influencing the prediction through SHAP explanations.

This project is developed as a **Minimum Viable Product (MVP)**. Authentication, database integration, chatbot support, and PDF report generation are planned for future enhancements.

---

## Features

- Upload blueprint files (SVG, PNG, JPG/JPEG, PDF)
- Automatic blueprint feature extraction
- Construction cost prediction using HistGradientBoostingRegressor
- SHAP-based explainable AI for prediction insights
- Detailed construction cost breakdown
- Responsive React frontend with Flask backend
- Support for multiple blueprint formats through a unified extraction pipeline

---

## Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- Axios
- Recharts

### Backend
- Flask
- OpenCV
- pdf2image
- scikit-learn
- SHAP

### Machine Learning
- HistGradientBoostingRegressor

### Dataset
- CubiCasa5K
- CPWD & Tamil Nadu PWD Schedule of Rates

---

## Project Structure

```text
construction-cost-estimator/
├── backend/
│   ├── app.py                     Flask application
│   ├── model.pkl                  Trained machine learning model
│   ├── requirements.txt
│   ├── sample_data/
│   │   ├── sample_blueprint.svg
│   │   ├── sample_blueprint.png
│   │   └── sample_blueprint.pdf
│   └── services/
│       ├── extractor_router.py
│       ├── feature_extraction.py
│       ├── raster_extraction.py
│       ├── pdf_extraction.py
│       ├── predictor.py
│       └── explainer.py
└── frontend/
    ├── src/
    │   ├── pages/
    │   ├── components/
    │   └── api/
    └── Vite + React + Tailwind CSS
```

---

## Architecture

All supported blueprint formats (SVG, PNG, JPG/JPEG, and PDF) follow a unified processing pipeline. Each extractor generates the same **ExtractionResult** containing the required feature set, detected objects, and warnings. These standardized features are passed to the prediction and explanation modules, making the machine learning pipeline independent of the uploaded file format.

---

# Backend Setup

### Install Poppler (Required only for PDF uploads)

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# Download Poppler binaries and add the 'bin' folder to your PATH
# https://github.com/oschwartz10612/poppler-windows/releases
```

### Create Virtual Environment and Install Dependencies

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

python app.py
```

The backend runs at:

```
http://localhost:5000
```

---

## Verify Backend

```bash
curl http://localhost:5000/api/health
```

---

## Test Prediction API

```bash
curl -F "file=@sample_data/sample_blueprint.svg" http://localhost:5000/api/predict

curl -F "file=@sample_data/sample_blueprint.png" http://localhost:5000/api/predict

curl -F "file=@sample_data/sample_blueprint.pdf" http://localhost:5000/api/predict
```

---

# Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

The frontend runs at:

```
http://localhost:5173
```

The Vite development server automatically proxies API requests to the backend running on **http://localhost:5000**, so no additional environment configuration is required for local development.

---

## API Endpoint

### POST `/api/predict`

Upload a blueprint file using multipart/form-data.

**Supported Formats**

- SVG
- PNG
- JPG
- JPEG
- PDF

The API returns:

- Extracted blueprint features
- Predicted construction cost
- Cost breakdown
- SHAP values
- Feature importance
- Natural language explanation
- Detection warnings (if any)

---

## Future Enhancements

- User authentication
- Database integration
- Project history
- AI chatbot assistance
- PDF report generation
- YOLO-based blueprint object detection
- Cloud deployment

---

## License

This project is licensed under the MIT License.
