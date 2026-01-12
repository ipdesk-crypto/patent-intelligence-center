import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURATION ---
BRAND_ORANGE = "#FF8C00"
DATA_FILE = "Data Structure - Patents in UAE (Archistrategos) - Type 5.csv"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide")

# Styling for Executive Dark Mode
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {BRAND_ORANGE}; }}
    h1, h2, h3, h4 {{ color: {BRAND_ORANGE} !important; font-weight: 800; }}
    .stMetric {{ background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #333; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("ARCHISTRATEGOS LOGIN")
        with st.form("login"):
            pwd = st.text_input("Enter System Passcode", type="password")
            if st.form_submit_button("AUTHENTICATE"):
                if pwd == "Archistrategos2024":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Access Denied.")
    st.stop()

# --- 3. DATA ENGINE ---
@st.cache_data
def load_and_clean_data():
    if not os.path.exists(DATA_FILE): return None
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # Date & Year Extraction
    df['Application Date'] = pd.to_datetime(df['Application Date'], errors='coerce')
    df['Year'] = df['Application Date'].dt.year
    
    # IPC Cleaning (Taking the high-level group)
    df['IPC_Group'] = df['Classification'].str.split().str[0].str.replace(',', '').str.strip()
    return df

df = load_and_clean_data()

# --- 4. NAVIGATION & GLOBAL FILTERS ---
with st.sidebar:
    nav = st.radio("SELECT MODE", ["Database Search", "Strategic Analysis"])
    st.markdown("---")
    st.subheader("Analysis Focus")
    
    # The IPC Selector you requested
    all_ipcs = sorted(df['IPC_Group'].unique().astype(str)) if df is not None else []
    clean_ipcs = [x for x in all_ipcs if x not in ['There', 'no', 'nan']]
    selected_ipcs = st.multiselect("Choose IPC Classes", clean_ipcs)
    
    # Jurisdiction Selector
    all_countries = sorted(df['Country Name (Priority)'].dropna().unique())
    selected_countries = st.multiselect("Choose Source Countries", all_countries)

# Apply Global Filters to the dataset
filtered_df = df.copy()
if selected_ipcs:
    filtered_df = filtered_df[filtered_df['IPC_Group'].isin(selected_ipcs)]
if selected_countries:
    filtered_df = filtered_df[filtered_df['Country Name (Priority)'].isin(selected_countries)]

# --- 5. SYSTEM MODULES ---
if nav == "Database Search":
    st.title("🔍 Patent Query Engine")
    st.markdown(f"**Current active results:** {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

else:
    st.title("📈 Strategic Intelligence Suite")
    
    # Analysis Tabs
    tab1, tab2, tab3 = st.tabs(["Technology Growth", "Geographic Velocity", "Market Complexity"])
    
    with tab1:
        st.subheader("IPC Growth Trajectory")
        growth_data = filtered_df.groupby(['Year', 'IPC_Group']).size().reset_index(name='Volume')
        fig1 = px.line(growth_data, x='Year', y='Volume', color='IPC_Group', markers=True, 
                        line_shape="spline", template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.subheader("Jurisdictional Filing Velocity")
        # This uses 'Country Name (Priority)' and 'Year' to show who is filing more recently
        geo_velocity = filtered_df.groupby(['Year', 'Country Name (Priority)']).size().reset_index(name='Filings')
        fig2 = px.area(geo_velocity, x='Year', y='Filings', color='Country Name (Priority)', 
                        template="plotly_dark", title="Filing Trends by Origin Country")
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("Technology Complexity Heatmap (Treemap)")
        # This uses IPC Group and Application Type to show density
        fig3 = px.treemap(filtered_df, path=['IPC_Group', 'Application Type (ID)'], 
                           color_discrete_sequence=px.colors.sequential.Oranges_r,
                           template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)

    # --- FOOTER METRICS ---
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Filter Set", len(filtered_df))
    c2.metric("Dominant Country", filtered_df['Country Name (Priority)'].mode()[0] if not filtered_df.empty else "N/A")
    c3.metric("Leading Sector", filtered_df['IPC_Group'].mode()[0] if not filtered_df.empty else "N/A")
