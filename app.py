import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime

# --- 1. CONFIGURATION & BRANDING ---
# Set the brand color to the Archistrategos Orange
BRAND_ORANGE = "#FF8C00"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide", page_icon="⚖️")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {BRAND_ORANGE}; }}
    h1, h2, h3 {{ color: {BRAND_ORANGE} !important; font-weight: 800; }}
    .metric-badge {{
        background: #161b22;
        color: {BRAND_ORANGE} !important;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid {BRAND_ORANGE};
        text-align: center;
        margin-bottom: 20px;
    }}
    div.stButton > button {{
        background-color: {BRAND_ORANGE} !important;
        color: #000000 !important;
        font-weight: 700 !important;
        width: 100%;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_ORANGE} !important;
        color: black !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY GATEWAY (Password Included) ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo.jpeg"):
            st.image("logo.jpeg", use_container_width=True)
        st.markdown("<h2 style='text-align: center;'>SECURITY GATEWAY</h2>", unsafe_allow_html=True)
        
        with st.form("login_gateway"):
            # PASSWORD ADDED HERE
            pwd = st.text_input("Enter Passcode", type="password")
            if st.form_submit_button("AUTHENTICATE SYSTEM"):
                if pwd == "Archistrategos2024": 
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Access Denied.")
    return False

if not check_password():
    st.stop()

# --- 3. DATA ENGINE ---
@st.cache_data
def load_and_prep_data(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    
    # Date processing for Growth Analysis
    date_cols = ['Application Date', 'Priority Date', 'Earliest Priority Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'Application Date' in df.columns:
        df['Filing Year'] = df['Application Date'].dt.year
        
    return df

# --- 4. NAVIGATION ---
with st.sidebar:
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", use_container_width=True)
    st.markdown("---")
    nav = st.radio("COMMAND NAVIGATION", ["Search Engine", "Analysis Engine"])
    
    # Allows user to upload their specific CSV
    uploaded_file = st.file_uploader("Upload Patent Dataset", type="csv")
    
    if st.button("🔄 Clear Filters"):
        for key in st.session_state.keys():
            if key.startswith('search_'): st.session_state[key] = ""
        st.rerun()

# --- 5. SYSTEM LOGIC ---
if uploaded_file:
    master_df = load_and_prep_data(uploaded_file)
    
    if nav == "Search Engine":
        st.title("🔍 Patent Query Engine")
        
        # 10 FILTERS REQUESTED BY USER
        st.markdown("### Search Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            q_app_num = st.text_input("Application Number", key="search_1")
            q_title = st.text_input("Title", key="search_2")
            q_abstract = st.text_input("Abstract", key="search_3")
            q_date = st.text_input("Application Date (YYYY-MM-DD)", key="search_4")
        with c2:
            q_class = st.text_input("Classification", key="search_5")
            q_country = st.text_input("Country Name (Priority)", key="search_6")
            q_prio_num = st.text_input("Priority Number", key="search_7")
        with c3:
            q_prio_date = st.text_input("Priority Date (YYYY-MM-DD)", key="search_8")
            q_early_date = st.text_input("Earliest Priority Date", key="search_9")
            q_type = st.text_input("Application Type (ID)", key="search_10")

        # Filtering Execution
        f = master_df.copy()
        if q_app_num: f = f[f['Application Number'].astype(str).str.contains(q_app_num, case=False, na=False)]
        if q_title: f = f[f['Title'].astype(str).str.contains(q_title, case=False, na=False)]
        if q_abstract: f = f[f['Abstract'].astype(str).str.contains(q_abstract, case=False, na=False)]
        if q_date: f = f[f['Application Date'].astype(str).str.contains(q_date, na=False)]
        if q_class: f = f[f['Classification'].astype(str).str.contains(q_class, case=False, na=False)]
        if q_country: f = f[f['Country Name (Priority)'].astype(str).str.contains(q_country, case=False, na=False)]
        if q_prio_num: f = f[f['Priority Number'].astype(str).str.contains(q_prio_num, na=False)]
        if q_prio_date: f = f[f['Priority Date'].astype(str).str.contains(q_prio_date, na=False)]
        if q_early_date: f = f[f['Earliest Priority Date'].astype(str).str.contains(q_early_date, na=False)]
        if q_type: f = f[f['Application Type (ID)'].astype(str).str.contains(q_type, na=False)]

        st.session_state['filtered_df'] = f

        st.markdown(f'<div class="metric-badge">RESULTS IDENTIFIED: {len(f)}</div>', unsafe_allow_html=True)
        st.dataframe(f, use_container_width=True, hide_index=True)

    elif nav == "Analysis Engine":
        st.title("📈 Strategic Analysis Engine")
        df_ana = st.session_state.get('filtered_df', master_df)
        
        # --- IPC GROWTH CHART ---
        st.subheader("International Patent Classification (IPC) Growth")
        if 'Classification' in df_ana.columns and 'Filing Year' in df_ana.columns:
            # Grouping IPC to main categories
            df_ana['IPC_Main'] = df_ana['Classification'].str.split().str[0]
            growth = df_ana.groupby(['Filing Year', 'IPC_Main']).size().reset_index(name='Count')
            
            fig = px.line(growth, x='Filing Year', y='Count', color='IPC_Main', 
                         markers=True, template="plotly_dark", 
                         title="IPC Technology Growth Over Time")
            st.plotly_chart(fig, use_container_width=True)

        # --- ADDITIONAL COMPARISONS ---
        st.markdown("---")
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### Top Countries")
            geo = df_ana['Country Name (Priority)'].value_counts().head(10)
            st.bar_chart(geo)
        with col_right:
            st.markdown("#### Application Types")
            types = df_ana['Application Type (ID)'].value_counts()
            st.pie_chart(types)

else:
    st.info("System Initialized. Please upload 'Data Structure - Patents in UAE (Archistrategos) - Type 5.csv' to begin.")
