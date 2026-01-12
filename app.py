import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. CONFIGURATION & BRANDING ---
BRAND_ORANGE = "#FF8C00"
# Hardcoded data file reference as requested
DATA_FILE = "Data Structure - Patents in UAE (Archistrategos) - Type 5.csv"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide", page_icon="⚖️")

# Custom CSS for Archistrategos Branding & Layout
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {BRAND_ORANGE}; }}
    h1, h2, h3, h4 {{ color: {BRAND_ORANGE} !important; font-weight: 800; }}
    .metric-card {{
        background: #161b22;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {BRAND_ORANGE};
        text-align: center;
        margin-bottom: 20px;
    }}
    div.stButton > button {{
        background-color: {BRAND_ORANGE} !important;
        color: #000000 !important;
        font-weight: 700 !important;
        width: 100%;
        border-radius: 5px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_ORANGE} !important;
        color: black !important;
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

# --- 3. DATA ENGINE (Pre-ingestion) ---
@st.cache_data
def load_and_prep_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip() for c in df.columns]
        
        # Convert date columns to datetime objects for analysis 
        date_cols = ['Application Date', 'Priority Date', 'Earliest Priority Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if 'Application Date' in df.columns:
            df['Filing Year'] = df['Application Date'].dt.year
        return df
    except Exception as e:
        st.error(f"Error loading system data: {e}")
        return None

# --- 4. NAVIGATION & SHARED SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", use_container_width=True)
    st.markdown("---")
    nav = st.radio("COMMAND NAVIGATION", ["Search Engine", "Analysis Engine"])
    
    if st.button("🔄 Reset Portal View"):
        for key in st.session_state.keys():
            if key.startswith('search_'): st.session_state[key] = ""
        st.rerun()

# Load Data Automatically for all users
master_df = load_and_prep_data(DATA_FILE)

if master_df is not None:
    # --- 5. SEARCH ENGINE ---
    if nav == "Search Engine":
        st.title("🔍 Patent Query Engine")
        st.markdown("### Search Parameters")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            q_app_num = st.text_input("Application Number", key="search_1")
            q_title = st.text_input("Title", key="search_2")
            q_abstract = st.text_input("Abstract", key="search_3")
        with c2:
            q_class = st.text_input("Classification (IPC)", key="search_5")
            q_country = st.text_input("Country (Priority)", key="search_6")
            q_prio_num = st.text_input("Priority Number", key="search_7")
        with c3:
            q_date = st.text_input("Application Date (YYYY-MM-DD)", key="search_4")
            q_type = st.text_input("App Type (ID)", key="search_10")

        # Dynamic Filter Logic 
        f = master_df.copy()
        if q_app_num: f = f[f['Application Number'].astype(str).str.contains(q_app_num, case=False, na=False)]
        if q_title: f = f[f['Title'].astype(str).str.contains(q_title, case=False, na=False)]
        if q_abstract: f = f[f['Abstract'].astype(str).str.contains(q_abstract, case=False, na=False)]
        if q_date: f = f[f['Application Date'].astype(str).str.contains(q_date, na=False)]
        if q_class: f = f[f['Classification'].astype(str).str.contains(q_class, case=False, na=False)]
        if q_country: f = f[f['Country Name (Priority)'].astype(str).str.contains(q_country, case=False, na=False)]
        if q_type: f = f[f['Application Type (ID)'].astype(str).str.contains(q_type, na=False)]

        st.session_state['filtered_df'] = f
        st.markdown(f'<div class="metric-card"><h4>ACTIVE RESULTS IN SYSTEM: {len(f)}</h4></div>', unsafe_allow_html=True)
        st.dataframe(f, use_container_width=True, hide_index=True)

    # --- 6. ANALYSIS ENGINE ---
    elif nav == "Analysis Engine":
        st.title("📈 Strategic Analysis Engine")
        
        # Determine base data (results from Search Engine OR complete dataset)
        base_data = st.session_state.get('filtered_df', master_df)
        
        # --- ANALYSIS CONTROL SIDEBAR (Filter the Analysis) ---
        with st.sidebar:
            st.markdown("### Visual Toggles")
            show_kpis = st.checkbox("Executive Summary Metrics", value=True)
            show_growth = st.checkbox("Technology Growth Trends", value=True)
            show_geo = st.checkbox("Geographic Landscape", value=True)
            show_composition = st.checkbox("Portfolio Distribution", value=True)
            
            st.markdown("---")
            st.markdown("### Analysis Deep Dive")
            
            # Interactive filters that only affect the Analysis tab
            all_juris = sorted(base_data['Country Name (Priority)'].dropna().unique())
            sel_juris = st.multiselect("Filter Analysis by Country", all_juris)
            
            all_years = sorted(base_data['Filing Year'].dropna().unique().astype(int))
            sel_years = st.slider("Filter Analysis by Year Range", min(all_years), max(all_years), (min(all_years), max(all_years)))

        # Apply Deep-Dive Filters to Analysis
        df_ana = base_data.copy()
        if sel_juris:
            df_ana = df_ana[df_ana['Country Name (Priority)'].isin(sel_juris)]
        df_ana = df_ana[(df_ana['Filing Year'] >= sel_years[0]) & (df_ana['Filing Year'] <= sel_years[1])]

        # MODULE 1: EXECUTIVE METRICS
        if show_kpis:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Records", len(df_ana))
            m2.metric("Unique IPCs", df_ana['Classification'].nunique() if 'Classification' in df_ana.columns else 0)
            m3.metric("Primary Region", df_ana['Country Name (Priority)'].mode()[0] if not df_ana.empty else "N/A")
            m4.metric("Active Year Span", f"{int(df_ana['Filing Year'].min())}-{int(df_ana['Filing Year'].max())}" if not df_ana.empty else "N/A")
            st.markdown("---")

        # MODULE 2: TECHNOLOGY GROWTH (IPC)
        if show_growth and 'Classification' in df_ana.columns:
            st.subheader("Technology Sector Growth Over Time")
            # Cleaning IPC for accurate grouping 
            df_ana['IPC_Main'] = df_ana['Classification'].str.split().str[0].str.replace(',', '').str.strip()
            growth = df_ana.groupby(['Filing Year', 'IPC_Main']).size().reset_index(name='Volume')
            
            fig_growth = px.line(growth, x='Filing Year', y='Volume', color='IPC_Main',
                               markers=True, line_shape="spline", template="plotly_dark",
                               color_discrete_sequence=px.colors.qualitative.Prism)
            fig_growth.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                   xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#333333'))
            st.plotly_chart(fig_growth, use_container_width=True)

        st.markdown("---")
        col_left, col_right = st.columns(2)
        
        # MODULE 3: GEOGRAPHIC LANDSCAPE
        with col_left:
            if show_geo:
                st.markdown("#### Geographic Landscape (Top 10)")
                geo = df_ana['Country Name (Priority)'].value_counts().head(10).reset_index()
                geo.columns = ['Country', 'Count']
                fig_bar = px.bar(geo, x='Country', y='Count', template="plotly_dark",
                                color_discrete_sequence=[BRAND_ORANGE])
                fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)
            
        # MODULE 4: PORTFOLIO COMPOSITION (Donut Chart)
        with col_right:
            if show_composition:
                st.markdown("#### Portfolio Composition")
                types = df_ana['Application Type (ID)'].value_counts().reset_index()
                types.columns = ['Type', 'Volume']
                fig_pie = px.pie(types, values='Volume', names='Type', hole=0.5,
                                template="plotly_dark", 
                                color_discrete_sequence=px.colors.sequential.Oranges_r)
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.error(f"Critical Error: System data file '{DATA_FILE}' not found. Please upload to the repository.")
