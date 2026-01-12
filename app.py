import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. CONFIGURATION & BRANDING ---
BRAND_ORANGE = "#FF8C00"
# Ensure this matches your file name on GitHub exactly
DATA_FILE = "Data Structure - Patents in UAE (Archistrategos) - Type 5.csv"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide", page_icon="⚖️")

# Custom CSS for Archistrategos Branding
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
            # HARDCODED PASSWORD
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
def load_and_prep_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping Dates 
        date_cols = ['Application Date', 'Priority Date', 'Earliest Priority Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if 'Application Date' in df.columns:
            df['Filing Year'] = df['Application Date'].dt.year
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- 4. NAVIGATION & SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", use_container_width=True)
    st.markdown("---")
    nav = st.radio("COMMAND NAVIGATION", ["Search Engine", "Analysis Engine"])
    
    if st.button("🔄 Clear Filters"):
        for key in st.session_state.keys():
            if key.startswith('search_'): st.session_state[key] = ""
        st.rerun()

# Load Data Automatically
master_df = load_and_prep_data(DATA_FILE)

if master_df is not None:
    # --- 5. SEARCH ENGINE ---
    if nav == "Search Engine":
        st.title("🔍 Patent Query Engine")
        st.markdown("### Search Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            q_app_num = st.text_input("Application Number", key="search_1") # 
            q_title = st.text_input("Title", key="search_2") # 
            q_abstract = st.text_input("Abstract", key="search_3") # 
            q_date = st.text_input("Application Date (YYYY-MM-DD)", key="search_4") # 
        with c2:
            q_class = st.text_input("Classification", key="search_5") # 
            q_country = st.text_input("Country Name (Priority)", key="search_6") # 
            q_prio_num = st.text_input("Priority Number", key="search_7") # 
        with c3:
            q_prio_date = st.text_input("Priority Date (YYYY-MM-DD)", key="search_8") # 
            q_early_date = st.text_input("Earliest Priority Date", key="search_9") # 
            q_type = st.text_input("Application Type (ID)", key="search_10") # 

        f = master_df.copy()
        # Filter Logic based on your CSV Headers 
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

    # --- 6. ANALYSIS ENGINE ---
    elif nav == "Analysis Engine":
        st.title("📈 Strategic Analysis Engine")
        df_ana = st.session_state.get('filtered_df', master_df)
        
        # High-Level Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", len(df_ana))
        m2.metric("Top IPC Group", df_ana['Classification'].mode()[0] if 'Classification' in df_ana.columns else "N/A")
        m3.metric("Primary Region", df_ana['Country Name (Priority)'].mode()[0] if 'Country Name (Priority)' in df_ana.columns else "N/A")

        # IPC Growth Analysis
        if 'Classification' in df_ana.columns and 'Filing Year' in df_ana.columns:
            st.subheader("Technology Growth Over Time (IPC)")
            df_ana['IPC_Main'] = df_ana['Classification'].str.split().str[0].str.replace(',', '')
            growth = df_ana.groupby(['Filing Year', 'IPC_Main']).size().reset_index(name='Volume')
            
            fig_growth = px.line(growth, x='Filing Year', y='Volume', color='IPC_Main',
                               markers=True, template="plotly_dark", 
                               color_discrete_sequence=px.colors.qualitative.Prism)
            fig_growth.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_growth, use_container_width=True)

        st.markdown("---")
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("#### Top Jurisdictions")
            geo = df_ana['Country Name (Priority)'].value_counts().head(10).reset_index()
            geo.columns = ['Country', 'Count']
            fig_bar = px.bar(geo, x='Country', y='Count', template="plotly_dark", color_discrete_sequence=[BRAND_ORANGE])
            fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c_right:
            st.markdown("#### Portfolio Type Distribution")
            types = df_ana['Application Type (ID)'].value_counts().reset_index()
            types.columns = ['Type', 'Count']
            # Replaced st.pie_chart with Plotly to avoid AttributeError
            fig_pie = px.pie(types, values='Count', names='Type', hole=0.4, template="plotly_dark",
                            color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.error(f"Critical System File Missing: Please ensure '{DATA_FILE}' is in the GitHub repository.")
