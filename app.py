import streamlit as st
import pandas as pd
import os
import sys
import json
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.core_agent import run_agent
from audit.logger import get_all_records, export_to_excel, init_db
from config.settings import settings

# Initialize DB
init_db()

# Page Config
st.set_page_config(
    page_title="FinanceFlow AI | Enterprise Recovery",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM CSS STYLING (Glassmorphism & Gradients) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(18, 28, 45) 0%, rgb(10, 15, 25) 81.3%);
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border: 1px solid rgba(0, 150, 255, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transform: translateY(-5px);
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 5px 15px rgba(0, 114, 255, 0.4);
        transform: scale(1.02);
    }

    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        background: -webkit-linear-gradient(#00C6FF, #0072FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Sidebar Styling */
    .css-164773 {
        background-color: #0E141B;
    }
    
    /* Animation for Fade-In */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.8s ease-out forwards;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper Functions
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Assets
lottie_welcome = load_lottieurl("https://lottie.host/6ad3459c-6fcc-4f11-96d5-86641219b6e8/8P6Lz3U69x.json")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00C6FF; font-size: 24px;'>FinanceFlow AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 12px; opacity: 0.6;'>Enterprise Collections v2.0</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    selected = option_menu(
        menu_title=None,
        options=["Launchpad", "Command Center", "Insights", "Settings"],
        icons=["house", "cpu", "bar-chart-line", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00C6FF", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "rgba(0,198,255,0.1)"},
            "nav-link-selected": {"background-color": "rgba(0,198,255,0.2)", "border-left": "4px solid #00C6FF"},
        }
    )
    
    st.markdown("---")
    uploaded_file = st.file_uploader("📂 Master Data Source", type=["csv", "xlsx"])
    dry_run = st.toggle("🛡️ Safety Mode (Dry Run)", value=True)
    
    if st.button("🚀 EXPORT RECOVERY REPORT"):
        export_path = "output/enterprise_audit.xlsx"
        os.makedirs("output", exist_ok=True)
        export_to_excel(export_path)
        with open(export_path, "rb") as f:
            st.download_button("📥 Click to Download", f, file_name=f"FinanceFlow_Report_{datetime.now().strftime('%Y%m%d')}.xlsx")

# --- DATA FETCHING ---
records = get_all_records()
df_audit = pd.DataFrame([r.model_dump() for r in records]) if records else pd.DataFrame()

# --- PAGE ROUTING ---

if selected == "Launchpad":
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.title("Welcome to FinanceFlow AI")
        st.markdown("""
            ### The Next Generation of Debt Recovery.
            Harness the power of Large Language Models to transform your collections process. 
            FinanceFlow AI autonomously manages client relationships, escalates overdue accounts, 
            and recovers revenue—all with human-level nuance and machine-level scale.
            
            - **✨ 0% Failure Engine**: Advanced JSON repair and multi-model fallbacks.
            - **🧠 Context-Aware AI**: Formal, structured communication tailored to debtor history.
            - **📈 Scalable Architecture**: Supabase-ready, enterprise-grade audit trail.
        """)
        if st.button("GO TO COMMAND CENTER"):
            st.info("Navigate to Command Center using the sidebar to begin.")
    
    with c2:
        if lottie_welcome:
            st_lottie(lottie_welcome, height=300, key="welcome")
    
    st.markdown("---")
    st.subheader("System Health & Status")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown("<div class='glass-card'><h4>Active API</h4><h2 style='color: #00C6FF;'>Groq / Llama 3.3</h2></div>", unsafe_allow_html=True)
    with k2:
        st.markdown("<div class='glass-card'><h4>Storage Engine</h4><h2 style='color: #00C6FF;'>SQLAlchemy / PostgreSQL</h2></div>", unsafe_allow_html=True)
    with k3:
        st.markdown("<div class='glass-card'><h4>Processing Latency</h4><h2 style='color: #00C6FF;'>~450ms / Token</h2></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Command Center":
    st.title("🎯 Recovery Command Center")
    st.markdown("Monitor and execute AI-driven follow-up sequences.")
    
    # Execution Progress
    exec_col1, exec_col2 = st.columns([1, 4])
    with exec_col1:
        if st.button("RUN AGENT"):
            if not uploaded_file:
                filepath = os.path.join(settings.DATA_DIR, "sample_invoices.csv")
                st.toast("⚡ Running with Sample Dataset")
            else:
                filepath = os.path.join(settings.DATA_DIR, "uploaded_invoices.csv")
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            settings.DRY_RUN_MODE = dry_run
            with st.spinner("🧠 Agent is thinking..."):
                summary = run_agent(filepath)
            st.success("Sequence Complete.")
            st.rerun()

    # Queue Tabs
    q_tab1, q_tab2 = st.tabs(["📋 Active Queue", "📧 Email Lab"])
    
    with q_tab1:
        if not df_audit.empty:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(df_audit.head(20), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Ready for input. Upload data to begin.")

    with q_tab2:
        if not df_audit.empty:
            email_df = df_audit[df_audit['subject'].notna()]
            if not email_df.empty:
                inv_id = st.selectbox("Select Invoice to Preview", email_df['invoice_no'].unique())
                row = email_df[email_df['invoice_no'] == inv_id].iloc[0]
                st.markdown(f"""
                    <div class='glass-card'>
                        <h3>{row['subject']}</h3>
                        <p style='opacity: 0.7;'>To: {row['client_email']} | Stage: {row['stage']}</p>
                        <hr>
                        <div style='white-space: pre-wrap; font-size: 1.1rem;'>{row['body']}</div>
                    </div>
                """, unsafe_allow_html=True)

elif selected == "Insights":
    st.title("📈 Performance Insights")
    st.markdown("Analyze recovery velocity and agent performance.")
    
    if not df_audit.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Collection Stages Distribution")
            fig = px.pie(df_audit, names='stage', hole=.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Days Overdue Analysis")
            fig2 = px.histogram(df_audit, x="days_overdue", nbins=10, color_discrete_sequence=['#00C6FF'])
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Time Series
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Processing Velocity (Last 30 Days)")
        df_audit['date'] = pd.to_datetime(df_audit['timestamp']).dt.date
        date_counts = df_audit.groupby('date').size().reset_index(name='count')
        fig3 = px.line(date_counts, x='date', y='count', line_shape='spline', markers=True)
        fig3.update_traces(line_color='#00C6FF')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No data available for analysis.")

elif selected == "Settings":
    st.title("⚙️ System Configuration")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Model Configuration")
    st.text_input("Primary Model", value="llama-3.3-70b-versatile", disabled=True)
    st.text_input("Fallback Model", value="mixtral-8x7b-32768", disabled=True)
    
    st.subheader("API Credentials")
    st.text_input("Groq API Key", value=settings.GROQ_API_KEY[:10] + "*"*20, type="password")
    
    st.subheader("Business Rules")
    st.checkbox("Skip Weekends", value=settings.SKIP_WEEKENDS)
    st.slider("Max Generation Retries", 1, 5, value=settings.MAX_EMAIL_RETRIES)
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; opacity: 0.5;'>FinanceFlow AI - Enterprise Credit Control System © 2026</p>", unsafe_allow_html=True)
