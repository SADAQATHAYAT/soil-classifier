# Geo Soil Classifier

## Description
Geo Soil Classifier is a desktop GUI application for soil classification based on the **Unified Soil Classification System (USCS)**. The app computes D-values (D10, D30, D60), soil coefficients (Cu, Cc), generates grain-size distribution curves and plasticity charts, and classifies soils using both **rule-based methods** and **machine learning models**. It also supports dataset management, visualization, and exporting of results.

---

## Features
- Compute **D-values** and soil coefficients from particle size and percent finer data  
- Generate **grain-size distribution curves** (semi-log plot)  
- Create **plasticity charts** using Liquid Limit (LL) and Plastic Limit (PL)  
- Classify soils using **USCS rule-based methods** (SP, SW, SC, SM, CL, CH, ML, MH)  
- Build and train a **Random Forest machine learning model** for soil type prediction  
- Load and save **CSV datasets** for machine learning training  
- Interactive **GUI** for easy input and visualization  
- Export results and charts for reporting  

---

## Tools and Technologies
- **Python 3.9+**: Core programming language  
- **Tkinter**: GUI framework for desktop applications  
- **NumPy**: Numerical computations and array operations  
- **Pandas**: CSV dataset handling and data manipulation  
- **Matplotlib**: Plotting grain-size curves and plasticity charts  
- **SciPy**: Interpolation (`PchipInterpolator`) and solving D-values (`brentq`)  
- **Scikit-learn**: Machine learning (Random Forest Classifier) and dataset splitting  
- **Joblib**: Save and load trained machine learning models  

---

## Machine Learning Model
- **Training:** Load a CSV dataset containing particle sizes, fines, LL, PL, and known soil types  
- **Model:** Random Forest Classifier trained on the dataset  
- **Prediction:** Predict soil type of new samples using the input data  
- **Persistence:** Save and load trained models as `.pkl` files  

---

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-folder>

**Create and activate a virtual environment:***
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

Install dependencies:

pip install -r requirements.txt

Run the application:

python soil_app.py
Usage

Enter Input Data

Particle sizes (mm)

Percent finer (%)

Liquid Limit (LL)

Plastic Limit (PL)

Fines content (%)

Compute

Calculates D-values, Cu, Cc, and visualizes grain-size curves

Rule-Based Classification

Classifies soil according to USCS rules

Machine Learning Prediction

Load CSV dataset → train Random Forest → predict soil types for new samples

Save Outputs

Export computed values, soil classification results, and charts

File Structure
soil_app/
├── soil_app.py        # Main application code
├── README.md          # Project documentation
├── requirements.txt   # Python dependencies
├── .gitignore         # Git ignore rules
└── LICENSE            # MIT License

License

This project is licensed under the MIT License – see the LICENSE file for details.

Author

Sadaqat – Software Engineer / Data Scientist
Contact: sadaqathayat881@gmail.com


Acknowledgments

Based on standard soil classification methods (USCS)

Uses Python scientific stack for computation and visualization

Machine learning integration inspired by Random Forest applications in geotechnical engineering
