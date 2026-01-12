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
    .dossier-card {{ border: 1px solid {BRAND_ORANGE}; padding: 25px; border-radius: 12px; background-color: #161b22; margin-bottom: 20px; }}
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
    
    # Remove Timestamp: Keep only date
    df['Application Date'] = pd.to_datetime(df['Application Date'], errors='coerce').dt.date
    df['Year'] = pd.to_datetime(df['Application Date']).dt.year
    df['IPC_Group'] = df['Classification'].astype(str).str.split().str[0].str.replace(',', '').str.strip()
    return df

master_df = load_data()

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("ARCHISTRATEGOS")
    nav = st.radio("SELECT MODE", ["Search Engine", "Strategic Analysis"])

if master_df is not None:
    # --- 5. SEARCH ENGINE & DOSSIER ---
    if nav == "Search Engine":
        st.title("🔍 Patent Intelligence Engine")
        global_q = st.text_input("Global Search", placeholder="Search keywords...")
        
        df_search = master_df.copy()
        if global_q:
            mask = df_search.apply(lambda row: row.astype(str).str.contains(global_q, case=False).any(), axis=1)
            df_search = df_search[mask]

        if not df_search.empty:
            selected_id = st.selectbox("Select a Patent", df_search['Application Number'].unique())
            p = df_search[df_search['Application Number'] == selected_id].iloc[0]

            st.markdown(f"""
                <div class="dossier-card">
                    <h2 style="margin:0;">{p['Application Number']}</h2>
                    <p style="color:{BRAND_ORANGE};">{p['Classification']}</p>
                    <hr style="border-color:#333;">
                    <div style="display: flex; gap: 50px;">
                        <div><small>DATE</small><br><b>{p['Application Date']}</b></div>
                        <div><small>COUNTRY</small><br><b>{p['Country Name (Priority)']}</b></div>
                        <div><small>IPC</small><br><b>{p['IPC_Group']}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(df_search, use_container_width=True, hide_index=True)

    # --- 6. STRATEGIC ANALYSIS (THE FIXED SECTION) ---
    else:
        st.title("📈 Strategic Analysis")
        
        with st.sidebar:
            all_ipcs = sorted(master_df['IPC_Group'].unique().astype(str))
            sel_ipcs = st.multiselect("Filter Analysis", [x for x in all_ipcs if x not in ['nan', 'None']])
            all_years = sorted(master_df['Year'].dropna().unique().astype(int))
            sel_years = st.slider("Years", min(all_years), max(all_years), (min(all_years), max(all_years)))

        df_ana = master_df.copy()
        if sel_ipcs: df_ana = df_ana[df_ana['IPC_Group'].isin(sel_ipcs)]
        df_ana = df_ana[(df_ana['Year'] >= sel_years[0]) & (df_ana['Year'] <= sel_years[1])]

        if not df_ana.empty:
            # SAFETY FIX FOR KEYERROR
            m_country = df_ana['Country Name (Priority)'].mode()
            m_year = df_ana['Year'].mode()
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Selected Patents", len(df_ana))
            k2.metric("Top Jurisdiction", m_country[0] if not m_country.empty else "N/A")
            k3.metric("Peak Year", int(m_year[0]) if not m_year.empty else "N/A")

            # CHART 1: CLEAN BAR CHART (Top 10 only)
            st.subheader("Top Technology Distribution")
            top_10_ipc = df_ana['IPC_Group'].value_counts().nlargest(10).reset_index()
            fig_bar = px.bar(top_10_ipc, x='IPC_Group', y='count', template="plotly_dark", color_discrete_sequence=[BRAND_ORANGE])
            fig_bar.update_layout(xaxis_title="IPC Class", yaxis_title="Count", height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

            col_left, col_right = st.columns(2)
            
            with col_left:
                # CHART 2: CLEAN DONUT
                st.subheader("Regional Hubs")
                top_countries = df_ana['Country Name (Priority)'].value_counts().nlargest(5).reset_index()
                fig_pie = px.pie(top_countries, names='Country Name (Priority)', values='count', hole=0.5, template="plotly_dark")
                fig_pie.update_traces(marker=dict(colors=px.colors.sequential.Oranges_r))
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_right:
                # CHART 3: CLEAN HEATMAP
                st.subheader("Growth Heatmap")
                # Filter to top 15 groups so the Y-axis isn't "ugly"
                top_15 = df_ana['IPC_Group'].value_counts().nlargest(15).index
                heat_df = df_ana[df_ana['IPC_Group'].isin(top_15)].groupby(['Year', 'IPC_Group']).size().reset_index(name='Count')
                fig_heat = px.density_heatmap(heat_df, x="Year", y="IPC_Group", z="Count", color_continuous_scale="Oranges", template="plotly_dark")
                st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("No data found for current filters.")
