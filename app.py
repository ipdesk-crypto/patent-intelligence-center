import streamlit as st
import pandas as pd
import hmac
import os
import io
import plotly.express as px
from datetime import datetime

# --- 1. PAGE CONFIG & ARCHISTRATEGOS BRANDING ---
st.set_page_config(page_title="Archistrategos Intelligence", layout="wide", page_icon="⚖️")

# Professional Executive Theme
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 2px solid #FF8C00; }
    
    /* Branded Orange Headers and Metric Badges */
    h1, h2, h3 { color: #FF8C00 !important; font-weight: 800; }
    .metric-badge {
        background: linear-gradient(135deg, #161b22 0%, #0E1117 100%);
        color: #FF8C00 !important;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #FF8C00;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #FF8C00 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: none !important;
        width: 100%;
    }

    /* Tabs Styling */
    .stTabs [aria-selected="true"] {
        background-color: #FF8C00 !important;
        color: black !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY GATEWAY ---
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
            pwd = st.text_input("Enter Passcode", type="password")
            if st.form_submit_button("AUTHENTICATE SYSTEM"):
                # Matches your requirement for configurable security
                if pwd == "Archistrategos2024": 
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials.")
    return False

if not check_password():
    st.stop()

# --- 3. DATA INGESTION ENGINE ---
@st.cache_data
def load_and_prep_data(file):
    df = pd.read_csv(file)
    # Ensure column names match your requested list exactly
    df.columns = [c.strip() for c in df.columns]
    
    # Prep Dates for Analysis
    date_cols = ['Application Date', 'Priority Date', 'Earliest Priority Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Extract Year for IPC Growth tracking
    if 'Application Date' in df.columns:
        df['Filing Year'] = df['Application Date'].dt.year
    
    return df

# --- 4. NAVIGATION & SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", use_container_width=True)
    st.markdown("---")
    nav = st.radio("COMMAND CENTER", ["Search Engine", "Analysis Engine"])
    
    uploaded_file = st.file_uploader("Upload Master Patent CSV", type="csv")
    
    if st.button("🔄 Reset System"):
        for key in st.session_state.keys():
            if key.startswith('search_'): st.session_state[key] = ""
        st.rerun()

# --- 5. MAIN LOGIC ---
if uploaded_file:
    master_df = load_and_prep_data(uploaded_file)
    
    # --- 5.1 SEARCH ENGINE MODULE ---
    if nav == "Search Engine":
        st.title("🔍 Patent Query Engine")
        
        # 10 Requested Search Filters
        st.markdown("### Active Filters")
        c1, c2, c3 = st.columns(3)
        with c1:
            q_app_num = st.text_input("Application Number", key="search_1")
            q_title = st.text_input("Title", key="search_2")
            q_abstract = st.text_input("Abstract", key="search_3")
            q_date = st.text_input("Application Date (YYYY-MM-DD)", key="search_4")
        with c2:
            q_class = st.text_input("Classification (IPC)", key="search_5")
            q_country = st.text_input("Country Name (Priority)", key="search_6")
            q_prio_num = st.text_input("Priority Number", key="search_7")
        with c3:
            q_prio_date = st.text_input("Priority Date (YYYY-MM-DD)", key="search_8")
            q_early_date = st.text_input("Earliest Priority Date", key="search_9")
            q_type = st.text_input("Application Type (ID)", key="search_10")

        # Filtering Logic
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

        st.session_state['filtered_data'] = f

        st.markdown(f'<div class="metric-badge">IDENTIFIED: {len(f)} RECORDS</div>', unsafe_allow_html=True)
        st.dataframe(f, use_container_width=True, hide_index=True)

    # --- 5.2 ANALYSIS ENGINE MODULE ---
    elif nav == "Analysis Engine":
        st.title("📈 Intelligence Analysis Engine")
        
        # Use filtered data if available, else use master
        df_ana = st.session_state.get('filtered_data', master_df)
        
        if df_ana.empty:
            st.warning("No data available for analysis. Adjust your search filters.")
        else:
            # --- IPC GROWTH OVER TIME ---
            st.subheader("Temporal IPC Growth")
            if 'Classification' in df_ana.columns and 'Filing Year' in df_ana.columns:
                # Cleaning IPC for better graphing (getting top level code)
                df_growth = df_ana.copy()
                df_growth['IPC_Group'] = df_growth['Classification'].str.split().str[0]
                
                growth_counts = df_growth.groupby(['Filing Year', 'IPC_Group']).size().reset_index(name='Volume')
                
                fig_growth = px.line(growth_counts, x='Filing Year', y='Volume', color='IPC_Group',
                                    title="IPC Classification Trends (Growth over Time)",
                                    markers=True, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_growth, use_container_width=True)

            # --- DYNAMIC COMPONENT COMPARISON ---
            st.markdown("---")
            st.subheader("Cross-Component Comparison")
            col_a, col_b = st.columns(2)
            
            with col_a:
                comp_field = st.selectbox("Analyze Distribution of:", 
                                         ['Classification', 'Country Name (Priority)', 'Application Type (ID)'])
                dist_data = df_ana[comp_field].value_counts().reset_index().head(10)
                fig_dist = px.bar(dist_data, x=comp_field, y='count', color=comp_field,
                                 template="plotly_dark", title=f"Top 10: {comp_field}")
                st.plotly_chart(fig_dist, use_container_width=True)
            
            with col_b:
                st.markdown("#### Summary Intelligence")
                st.write(df_ana.describe(include='all').astype(str))

else:
    st.info("👋 Welcome to the Archistrategos Patent Portal. Please upload your CSV file in the sidebar to begin.")
