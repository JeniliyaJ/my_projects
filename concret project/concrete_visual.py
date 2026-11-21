import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Page Configuration
st.set_page_config(
    page_title="Concrete Compressive Strength Prediction Suite",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional UI look
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: 700;
    }
    .sub-text {
        font-size: 1.1rem;
        color: #4B5563;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Load Model & Data Safely
@st.cache_resource
def load_saved_bundle():
    try:
        data = joblib.load('concrete_model.pkl')
        return data
    except Exception as e:
        return None

bundle = load_saved_bundle()

# Sidebar Navigation / Options
st.sidebar.image("https://img.icons8.com/color/96/constructor.png", width=80)
st.sidebar.title("Navigation Menu")
app_mode = st.sidebar.radio("Choose a section:", ["🔮 Live Prediction", "📂 Batch CSV Prediction", "📊 Dataset Insights & EDA", "ℹ️ About Project"])

if bundle is None:
    st.error("⚠️ `concrete_model.pkl` file kidaikala! Unga project folder-la model file irukka nu check pannunga.")
else:
    model = bundle['model']
    scaler = bundle['scaler']
    features = bundle['features']

    # ==================== TAB 1: LIVE PREDICTION ====================
    if app_mode == "🔮 Live Prediction":
        st.markdown('<p class="main-header">🏗️ Concrete Compressive Strength AI</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-text">Predict the 28-day compressive strength of high-performance concrete mixtures using Machine Learning.</p>', unsafe_allow_html=True)
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Cement & Binders")
            cement = st.number_input("Cement (kg/m³)", min_value=100.0, max_value=600.0, value=280.0)
            slag = st.number_input("Blast Furnace Slag (kg/m³)", min_value=0.0, max_value=360.0, value=0.0)
            ash = st.number_input("Fly Ash (kg/m³)", min_value=0.0, max_value=200.0, value=0.0)

        with col2:
            st.subheader("Water & Additives")
            water = st.number_input("Water (kg/m³)", min_value=100.0, max_value=250.0, value=180.0)
            superplastic = st.number_input("Superplasticizer (kg/m³)", min_value=0.0, max_value=35.0, value=6.0)
            age = st.slider("Age (Days)", min_value=1, max_value=365, value=28)

        with col3:
            st.subheader("Aggregates")
            coarseagg = st.number_input("Coarse Aggregate (kg/m³)", min_value=800.0, max_value=1200.0, value=970.0)
            fineagg = st.number_input("Fine Aggregate (kg/m³)", min_value=500.0, max_value=1000.0, value=770.0)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Center Predict Button
        if st.button("🚀 Calculate Compressive Strength", use_container_width=True):
            # 1. Automatically calculate the engineered features to match the 12 columns
            binder = cement + slag + ash
            cem_wat_ratio = cement / water if water > 0 else 0
            wat_bin_ratio = water / binder if binder > 0 else 0
            log_age = np.log(age) if age > 0 else 0

            # 2. Create the exact 12-column DataFrame
            input_data = [[
                cement, slag, ash, water, superplastic, coarseagg, fineagg, age,
                binder, cem_wat_ratio, wat_bin_ratio, log_age
            ]]
            
            input_df = pd.DataFrame(input_data, columns=features)
            
            # 3. Scale and Predict
            if scaler is not None:
                input_scaled = scaler.transform(input_df)
                prediction = model.predict(input_scaled)[0]
            else:
                prediction = model.predict(input_df)[0]

            # Results Section
            st.markdown("---")
            res_col1, res_col2 = st.columns([2, 1])
            with res_col1:
                st.success(f"### 🎉 Predicted Compressive Strength: **{prediction:.2f} MPa**")
                st.info("💡 **Engineering Insight:** Higher cement-to-water ratios and optimum curing age significantly enhance structural load capacity.")
            with res_col2:
                st.metric(label="Estimated Grade Quality", value=f"{'High Strength' if prediction > 40 else 'Standard Strength'}", delta=f"{prediction - 30:.1f} MPa vs Baseline")

    # ==================== TAB 2: BATCH CSV PREDICTION ====================
    elif app_mode == "📂 Batch CSV Prediction":
        st.markdown('<p class="main-header">📂 Batch Prediction via CSV Upload</p>', unsafe_allow_html=True)
        st.markdown("Upload a CSV file containing basic concrete mix features to generate bulk predictions instantly.")
        
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is not None:
            df_batch = pd.read_csv(uploaded_file)
            st.write("### Preview of Uploaded Data:", df_batch.head())
            
            if st.button("Run Bulk Predictions"):
                try:
                    # Automatically compute engineering features if they are not in the uploaded CSV
                    if 'binder' not in df_batch.columns:
                        df_batch['binder'] = df_batch['cement'] + df_batch['slag'] + df_batch['ash']
                    if 'cem_wat_ratio' not in df_batch.columns:
                        df_batch['cem_wat_ratio'] = df_batch['cement'] / df_batch['water']
                    if 'wat_bin_ratio' not in df_batch.columns:
                        df_batch['wat_bin_ratio'] = df_batch['water'] / df_batch['binder']
                    if 'log_age' not in df_batch.columns:
                        df_batch['log_age'] = np.log(df_batch['age'])

                    X_batch = df_batch[features]
                    if scaler is not None:
                        X_batch_scaled = scaler.transform(X_batch)
                        preds = model.predict(X_batch_scaled)
                    else:
                        preds = model.predict(X_batch)
                        
                    df_batch['Predicted_Strength_MPa'] = preds
                    st.success("Predictions generated successfully!")
                    st.dataframe(df_batch)
                    
                    csv_download = df_batch.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Predictions as CSV",
                        data=csv_download,
                        file_name='concrete_strength_predictions.csv',
                        mime='text/csv',
                    )
                except Exception as ex:
                    st.error(f"Error processing file: {ex}")

    # ==================== TAB 3: DATASET INSIGHTS & EDA ====================
    elif app_mode == "📊 Dataset Insights & EDA":
        st.markdown('<p class="main-header">📊 Exploratory Data Analysis & Feature Correlations</p>', unsafe_allow_html=True)
        st.write("Explore how different components interact and affect concrete compressive strength.")
        
        if 'raw_data' in bundle and bundle['raw_data'] is not None:
            df_eda = bundle['raw_data']
            st.subheader("Statistical Summary of Training Data")
            st.dataframe(df_eda.describe())
            
            st.subheader("Correlation Heatmap")
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(df_eda.corr(), annot=True, cmap="Blues", fmt=".2f", ax=ax)
            st.pyplot(fig)
        else:
            st.info("ℹ️ Raw dataset summary was not embedded in the model bundle.")

    # ==================== TAB 4: ABOUT PROJECT ====================
    elif app_mode == "ℹ️ About Project":
        st.markdown('<p class="main-header">ℹ️ About the Internship Project</p>', unsafe_allow_html=True)
        st.markdown("""
        * **Domain:** Civil Engineering Materials & Predictive Machine Learning.
        * **Objective:** To build an accurate regression model predicting the compressive strength of concrete based on mix proportions and curing age.
        * **Tech Stack:** Python, Scikit-Learn, Pandas, NumPy, Streamlit, Joblib.
        * **Developer:** Built as part of a professional machine learning internship portfolio.
        """)
        st.success("✨ This application is fully ready for deployment!")