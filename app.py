import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# --- 1. CONFIGURATION ---
BRAND_ORANGE = "#FF8C00"
DATA_FILE = "Data Structure - Patents in UAE (Archistrategos) - Type 5.csv"

st.set_page_config(page_title="Archistrategos Intelligence Portal", layout="wide")

# Custom UI Styling
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 2px solid {BRAND_ORANGE}; }}
    h1, h2, h3, h4 {{ color: {BRAND_ORANGE} !important; font-weight: 800; }}
    .stMetric {{ background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #333; }}
    .stDataFrame {{ border: 1px solid #333; border-radius: 5px; }}
    /* Custom Dossier Card Styling */
    .dossier-card {{
        border: 1px solid {BRAND_ORANGE};
        padding: 25px;
        border-radius: 12px;
        background-color: #161b22;
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("ARCHISTRATEGOS LOGIN")
        pwd = st.text_input("Passcode", type="password")
        if st.button("ENTER SYSTEM"):
            if pwd == "Archistrategos2024":
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE): return None
    df = pd.read_csv(DATA_FILE)
    df.columns = [c.strip() for c in df.columns]
    
    # FIX: Convert to datetime then extract ONLY the date to remove 00:00:00 timestamp
    df['Application Date'] = pd.to_datetime(df['Application Date'], errors='coerce').dt.date
    
    # Create helper columns for analysis
    df['Year'] = pd.to_datetime(df['Application Date']).dt.year
    df['IPC_Group'] = df['Classification'].astype(str).str.split().str[0].str.replace(',', '').str.strip()
    return df

master_df = load_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown(f"## ARCHISTRATEGOS")
    nav = st.radio("SELECT MODE", ["Search Engine", "Strategic Analysis"])
    st.markdown("---")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

if master_df is not None:
    # --- 5. SEARCH ENGINE & GOOGLE-STYLE DOSSIER ---
    if nav == "Search Engine":
        st.title("🔍 Patent Intelligence Engine")
        
        # Keyword and Filters
        global_q = st.text_input("Global Search", placeholder="Search by Applicant, Technology, or ID...")
        
        with st.expander("Advanced Filters"):
            c1, c2, c3 = st.columns(3)
            with c1: f_country = st.text_input("Source Country")
            with c2: f_ipc = st.text_input("IPC Code")
            with c3: f_year = st.text_input("Filing Year")

        # Filtering Logic
        df_search = master_df.copy()
        if global_q:
            mask = df_search.apply(lambda row: row.astype(str).str.contains(global_q, case=False).any(), axis=1)
            df_search = df_search[mask]
        if f_country: df_search = df_search[df_search['Country Name (Priority)'].str.contains(f_country, case=False, na=False)]
        if f_ipc: df_search = df_search[df_search['Classification'].str.contains(f_ipc, case=False, na=False)]
        if f_year: df_search = df_search[df_search['Year'].astype(str).contains(f_year, na=False)]

        if not df_search.empty:
            st.markdown("---")
            # Selectbox to generate the dossier for a specific record
            selected_id = st.selectbox("Select a Record to Open Intelligence Dossier", df_search['Application Number'].unique())
            patent = df_search[df_search['Application Number'] == selected_id].iloc[0]

            # Dossier Layout (Neat & Tidy like Google Patents)
            st.markdown(f"""
                <div class="dossier-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin:0; color:{BRAND_ORANGE}; letter-spacing: 2px;">INTELLECTUAL PROPERTY DOSSIER</h4>
                            <h2 style="margin:0; font-size: 32px;">{patent['Application Number']}</h2>
                            <p style="color:#888; font-size: 18px;">{patent['Classification']}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="background:{BRAND_ORANGE}; color:black; padding:8px 20px; border-radius:50px; font-weight:bold; font-size: 14px;">
                                {patent['Year']} FILING
                            </span>
                        </div>
                    </div>
                    <hr style="border-color:#333; margin: 20px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                        <div>
                            <p style="color:#888; margin:0; font-size: 12px;">APPLICATION DATE</p>
                            <p style="font-size:18px; margin:0;"><b>{patent['Application Date']}</b></p>
                        </div>
                        <div>
                            <p style="color:#888; margin:0; font-size: 12px;">PRIORITY COUNTRY</p>
                            <p style="font-size:18px; margin:0;"><b>{patent['Country Name (Priority)']}</b></p>
                        </div>
                        <div>
                            <p style="color:#888; margin:0; font-size: 12px;">IPC PRIMARY GROUP</p>
                            <p style="font-size:18px; margin:0;"><b>{patent['IPC_Group']}</b></p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Raw Data Table
            with st.expander("View Full Data Results Table", expanded=True):
                st.dataframe(df_search, use_container_width=True, hide_index=True)
        else:
            st.info("No matching patents found.")

 # --- 6. STRATEGIC ANALYSIS (Optimized Layout) ---
    else:
        st.title("📈 Strategic Analysis Dashboard")
        
        with st.sidebar:
            st.markdown("### Dashboard Controls")
            all_ipcs = sorted(master_df['IPC_Group'].unique().astype(str))
            sel_ipcs = st.multiselect("Filter Analysis by IPC Class", [x for x in all_ipcs if x not in ['nan', 'None']])
            
            all_years = sorted(master_df['Year'].dropna().unique().astype(int))
            sel_years = st.slider("Timeline Range", min(all_years), max(all_years), (min(all_years), max(all_years)))

        df_ana = master_df.copy()
        if sel_ipcs: 
            df_ana = df_ana[df_ana['IPC_Group'].isin(sel_ipcs)]
        df_ana = df_ana[(df_ana['Year'] >= sel_years[0]) & (df_ana['Year'] <= sel_years[1])]

        if not df_ana.empty:
            # KPI Metrics Row
            k1, k2, k3 = st.columns(3)
            k1.metric("Selected Portfolio", len(df_ana))
            k2.metric("Primary Jurisdiction", df_ana['Country Name (Priority)'].mode()[0] if not df_ana['Country Name (Priority)'].empty else "N/A")
            k3.metric("Peak Year", int(df_ana['Year'].mode()[0]) if not df_ana['Year'].empty else "N/A")

            # PLOT 1: Time Series
            st.subheader("Filing Volume Over Time")
            growth_df = df_ana.groupby('Year').size().reset_index(name='Count')
            fig1 = px.area(growth_df, x='Year', y='Count', template="plotly_dark")
            fig1.update_traces(line_color=BRAND_ORANGE, fillcolor="rgba(255, 140, 0, 0.2)")
            st.plotly_chart(fig1, use_container_width=True)

            # PLOT 2 & 3: Optimized Columns
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Top 10 Tech Classes")
                # FIX: Only show Top 10 to prevent X-axis clutter seen in your screenshot
                ipc_counts = df_ana['IPC_Group'].value_counts().head(10).reset_index()
                fig2 = px.bar(ipc_counts, x='IPC_Group', y='count', template="plotly_dark", text_auto=True)
                fig2.update_traces(marker_color=BRAND_ORANGE)
                fig2.update_layout(xaxis_tickangle=-45) # Angle labels for readability
                st.plotly_chart(fig2, use_container_width=True)
            
            with col_b:
                st.subheader("Leading Jurisdictions")
                geo_counts = df_ana['Country Name (Priority)'].value_counts().head(5).reset_index()
                fig3 = px.pie(geo_counts, names='Country Name (Priority)', values='count', hole=0.5, template="plotly_dark")
                fig3.update_traces(marker=dict(colors=px.colors.sequential.Oranges_r), textinfo='percent+label')
                st.plotly_chart(fig3, use_container_width=True)

            # PLOT 4: Tech Heatmap (Larger and Cleaner)
            st.subheader("Technology Emergence Heatmap")
            # Only show Top 15 IPCs in heatmap to prevent the "smear" effect
            top_ipcs = df_ana['IPC_Group'].value_counts().head(15).index
            heat_df = df_ana[df_ana['IPC_Group'].isin(top_ipcs)]
            heat_df = heat_df.groupby(['Year', 'IPC_Group']).size().reset_index(name='Count')
            
            fig4 = px.density_heatmap(heat_df, x="Year", y="IPC_Group", z="Count", 
                                     color_continuous_scale="Oranges", template="plotly_dark",
                                     height=600) # Increased height for better label spacing
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("Adjust filters to load analysis data.")

else:
    st.error(f"Data file '{DATA_FILE}' not found. Please ensure the file is in the same directory.")
