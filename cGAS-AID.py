import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import streamlit as st

st.set_page_config(
    page_title="cGAS-AID",
    page_icon="🧬",
    layout="wide"
)

# Now you can start the rest of your app
st.title("cGAS-AID: Bioactivity Predictor for cGAS enzyme")
# ... rest of your code ...


def fetch_chembl_data(target_id="CHEMBL4105728"):
    url = f'https://www.ebi.ac.uk/chembl/api/data/activity.json?target_chembl_id={target_id}&limit=1000'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["activities"]
        df = pd.DataFrame(data)
        return df[['canonical_smiles', 'pchembl_value']].dropna()
    else:
        print("Error fetching data")
        return pd.DataFrame()

data = fetch_chembl_data()

def smiles_to_descriptors(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return [
            Descriptors.MolWt(mol), Descriptors.TPSA(mol), 
            Descriptors.NumHAcceptors(mol), Descriptors.NumHDonors(mol)
        ]
    return [None, None, None, None]

data['Descriptors'] = data['canonical_smiles'].apply(smiles_to_descriptors)
data = data.dropna()
X = np.array(data['Descriptors'].tolist())
y = data['pchembl_value'].astype(float)

# Plot bioactivity distribution
sns.histplot(y, bins=30)
plt.title("Bioactivity Distribution")
plt.xlabel("pChEMBL Value")
st.pyplot()  # Use Streamlit's st.pyplot() for rendering matplotlib plots

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Train Support Vector Machine model
svm_model = SVR()
svm_model.fit(X_train, y_train)

# Evaluate models
y_pred_rf = rf_model.predict(X_test)
y_pred_svm = svm_model.predict(X_test)

mse_rf = mean_squared_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)
mse_svm = mean_squared_error(y_test, y_pred_svm)
r2_svm = r2_score(y_test, y_pred_svm)

print(f'Random Forest - MSE: {mse_rf}, R2: {r2_rf}')
print(f'SVM - MSE: {mse_svm}, R2: {r2_svm}')

# Save models
joblib.dump(rf_model, "rf_model.pkl")
joblib.dump(svm_model, "svm_model.pkl")

# Model loading function with error handling
def load_model(model_name):
    try:
        model = joblib.load(model_name)
        return model
    except FileNotFoundError:
        st.error(f"Model file {model_name} not found. Please ensure it's available in the environment.")
        return None

def predictor_app():
    st.title("Bioactivity Predictor for cGAS")
    model_choice = st.selectbox("Select Model", ["Random Forest", "SVM"])
    smiles = st.text_input("Enter SMILES:")
    
    if smiles:
        desc = smiles_to_descriptors(smiles)
        if None in desc:
            st.error("Invalid SMILES")
        else:
            model = load_model("rf_model.pkl") if model_choice == "Random Forest" else load_model("svm_model.pkl")
            if model:
                pred = model.predict([desc])[0]
                st.success(f"Predicted Bioactivity (pChEMBL): {pred}")

if __name__ == '__main__':
    predictor_app()
