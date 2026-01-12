import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# --- 1. CONFIGURATION ---
BRAND_ORANGE = "#FF8C00"
DATA_FILE = "Data Structure - Patents in UAE (Archistrategos) - Type 5.csv"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide")

# Custom CSS for the Archistrategos Brand Identity
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {BRAND_ORANGE}; }}
    h1, h2, h3, h4 {{ color: {BRAND_ORANGE} !important; font-weight: 800; }}
    .stMetric {{ background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #333; }}
    .stDataFrame {{ border: 1px solid {BRAND_ORANGE}; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
if "auth" not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("ARCHISTRATEGOS LOGIN")
        pwd = st.text_input("Passcode", type="password")
        if st.button("ENTER SYSTEM"):
            if pwd == "Archistrategos2024":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Access Denied.")
    st.stop()

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE): 
        return None
    try:
        df = pd.read_csv(DATA_FILE)
        df.columns = [c.strip() for c in df.columns]
        # Date processing
        df['Application Date'] = pd.to_datetime(df['Application Date'], errors='coerce')
        df['Year'] = df['Application Date'].dt.year
        # Extract IPC Group (First part of the classification)
        df['IPC_Group'] = df['Classification'].astype(str).str.split().str[0].str.replace(',', '').str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

master_df = load_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50.png?text=ARCHISTRATEGOS", use_container_width=True) # Replace with real logo
    nav = st.radio("SELECT MODE", ["Search Engine", "Strategic Analysis"])
    st.markdown("---")
    st.markdown("© 2026 Archistrategos Intelligence")

if master_df is not None:
    
    # --- 5. SEARCH ENGINE (Global Search + Specific Filters) ---
    if nav == "Search Engine":
        st.title("🔍 Patent Search & Analysis Engine")
        
        # A. GLOBAL KEYWORD SEARCH
        global_q = st.text_input("Global Search", placeholder="Type keywords (e.g., 'Solar', 'IBM', 'Processing')...")
        
        # B. STRUCTURED FILTERS
        with st.expander("Advanced Filter Controls", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                f_app = st.text_input("Application Number")
                f_ipc = st.text_input("IPC Code (e.g. G06K)")
            with c2:
                f_country = st.text_input("Source Country")
                f_type = st.text_input("App Type ID")
            with c3:
                f_year = st.text_input("Specific Year")
        
        # Logic: Narrowing down the data
        df_search = master_df.copy()

        if global_q:
            # Global filter: checks if any cell in the row contains the keyword
            mask = df_search.apply(lambda row: row.astype(str).str.contains(global_q, case=False).any(), axis=1)
            df_search = df_search[mask]
        
        if f_app: df_search = df_search[df_search['Application Number'].astype(str).str.contains(f_app, case=False, na=False)]
        if f_ipc: df_search = df_search[df_search['Classification'].astype(str).str.contains(f_ipc, case=False, na=False)]
        if f_country: df_search = df_search[df_search['Country Name (Priority)'].astype(str).str.contains(f_country, case=False, na=False)]
        if f_type: df_search = df_search[df_search['Application Type (ID)'].astype(str).str.contains(f_type, na=False)]
        if f_year: df_search = df_search[df_search['Year'].astype(str).str.contains(f_year, na=False)]

        # C. RESULTS & EXPORT
        m1, m2 = st.columns([1, 4])
        m1.metric("Results", len(df_search))
        
        # Export functionality
        towrite = BytesIO()
        df_search.to_csv(towrite, index=False)
        st.download_button(label="📥 Download Search Results", data=towrite.getvalue(), file_name="search_export.csv", mime="text/csv")

        st.dataframe(df_search, use_container_width=True, hide_index=True)

    # --- 6. STRATEGIC ANALYSIS (Visualization) ---
    else:
        st.title("📈 Strategic Intelligence Dashboard")
        
        # Analysis Sidebar Filters
        with st.sidebar:
            all_ipcs = sorted(master_df['IPC_Group'].unique().astype(str))
            sel_ipcs = st.multiselect("Filter by IPC Classes", [x for x in all_ipcs if x not in ['nan', 'None']])
            
            all_years = sorted(master_df['Year'].dropna().unique().astype(int))
            sel_years = st.slider("Timeline Range", min(all_years), max(all_years), (min(all_years), max(all_years)))

        df_ana = master_df.copy()
        if sel_ipcs: 
            df_ana = df_ana[df_ana['IPC_Group'].isin(sel_ipcs)]
        df_ana = df_ana[(df_ana['Year'] >= sel_years[0]) & (df_ana['Year'] <= sel_years[1])]

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Patents", len(df_ana))
        
        countries = df_ana['Country Name (Priority)'].mode()
        k2.metric("Primary Hub", countries[0] if not countries.empty else "N/A")
        
        ipcs = df_ana['IPC_Group'].mode()
        k3.metric("Lead Technology", ipcs[0] if not ipcs.empty else "N/A")
        
        avg_year = round(df_ana['Year'].mean(), 1) if not df_ana.empty else 0
        k4.metric("Avg Portfolio Age", int(avg_year))

        # Visualizations
        st.markdown("---")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Geopolitical Patent Distribution")
            geo_data = df_ana.groupby(['Year', 'Country Name (Priority)']).size().reset_index(name='Patents')
            fig_area = px.area(geo_data, x='Year', y='Patents', color='Country Name (Priority)', 
                               template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_area, use_container_width=True)

        with col_right:
            st.subheader("Technology Classification Hierarchy")
            fig_tree = px.treemap(df_ana, path=['IPC_Group', 'Application Type (ID)'], 
                                  color='Year', template="plotly_dark",
                                  color_continuous_scale='Oranges')
            st.plotly_chart(fig_tree, use_container_width=True)

        # Growth Chart
        st.subheader("Annual Filing Velocity")
        growth_data = df_ana.groupby('Year').size().reset_index(name='Volume')
        fig_line = px.line(growth_data, x='Year', y='Volume', markers=True, 
                           template="plotly_dark", line_shape="spline")
        fig_line.update_traces(line_color=BRAND_ORANGE)
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.error(f"Critical Error: System cannot find '{DATA_FILE}'. Please verify the file path.")
