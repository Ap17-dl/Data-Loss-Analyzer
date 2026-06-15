from __future__ import annotations

from io import BytesIO
from datetime import timezone

import pandas as pd
import streamlit as st

from analysis import analyze_missing_data
from rag import default_knowledge_base, generate_sales_impact_summary
from storage import mongo_config_status, recent_user_history, save_uploaded_csv_pair


@st.cache_data(show_spinner=False)
def parse_uploaded_dataset(file_bytes: bytes, filename: str) -> pd.DataFrame:
    lower_name = filename.lower()
    if lower_name.endswith(".json"):
        buffer = BytesIO(file_bytes)
        try:
            return pd.read_json(buffer, lines=True)
        except ValueError:
            buffer.seek(0)
            return pd.read_json(buffer)
    return pd.read_csv(BytesIO(file_bytes))


@st.cache_data(ttl=30, show_spinner=False)
def cached_recent_user_history(user_email: str, limit: int = 5) -> list[dict]:
    return recent_user_history(user_email, limit=limit)


@st.cache_data(show_spinner=False)
def run_analysis_cached(df: pd.DataFrame, critical_columns: tuple[str, ...], business_context: str) -> tuple[dict, dict]:
    analysis = analyze_missing_data(df, critical_columns=list(critical_columns))
    summary = generate_sales_impact_summary(
        analysis,
        business_context=business_context,
        knowledge_base=default_knowledge_base(),
    )
    return analysis, summary


st.set_page_config(
    page_title="Data Loss Analyzer",
    page_icon="📉",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stHeader"]     { display: none !important; }
    [data-testid="stToolbar"]    { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    #MainMenu                    { visibility: hidden !important; }
    footer                       { visibility: hidden !important; }

    /* Black Stock Market / Grid background theme */
    .stApp {
        background-color: #060913;
        background-image: 
            radial-gradient(at 50% 0%, rgba(0, 229, 255, 0.12) 0px, transparent 50%),
            linear-gradient(rgba(0, 229, 255, 0.02) 1px, transparent 1px), 
            linear-gradient(90deg, rgba(0, 229, 255, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 30px 30px, 30px 30px;
        color: #e2e8f0 !important;
    }
    .block-container { padding-top: 2rem; }

    /* General text overrides for dark mode readability */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    p, label, li, span, caption {
        color: #cbd5e1 !important;
    }

    /* Glassmorphism Hero Box */
    .hero {
        padding: 3rem 2.5rem;
        background: rgba(13, 20, 35, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 229, 255, 0.25);
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .hero:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 229, 255, 0.2);
        border-color: rgba(0, 229, 255, 0.5);
    }
    .hero h1 { 
        color: #00e5ff !important; 
        margin: 0; 
        font-weight: 800; 
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.3); 
    }
    .hero p { 
        color: #94a3b8 !important; 
        margin: 0.8rem 0 0; 
        font-weight: 600; 
    }

    /* Glassmorphism File Uploader */
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(0, 229, 255, 0.3) !important;
        border-radius: 16px !important;
        background: rgba(13, 20, 35, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        padding: 2.5rem 2rem 2rem !important;
        margin: 1.5rem 0 !important;
        text-align: center !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: background 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stFileUploader"]:hover {
        background: rgba(13, 20, 35, 0.55) !important;
        border-color: rgba(0, 229, 255, 0.6) !important;
    }

    div[data-testid="stFileUploader"] label p {
        color: #00e5ff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.4rem 0 !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.2) !important;
    }

    div[data-testid="stFileUploader"] label::after {
        content: "Get started by uploading a CSV file to analyze missing data and sales impact";
        display: block;
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 1.8rem;
    }

    [data-testid="stFileUploadDropzone"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 auto !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }

    [data-testid="stFileUploadDropzone"] section > svg { display: block !important; color: #00e5ff !important; }
    [data-testid="stFileUploadDropzone"] section > span,
    [data-testid="stFileUploadDropzone"] section > p   { display: block !important; color: #94a3b8 !important; }

    [data-testid="stFileUploadDropzone"] section > button,
    [data-testid="stFileUploadDropzone"] section > button span,
    [data-testid="stFileUploadDropzone"] section > button p {
        background: linear-gradient(135deg, rgba(0, 229, 255, 0.8) 0%, rgba(0, 153, 255, 0.8) 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid rgba(0, 229, 255, 0.4) !important;
        padding: 0.8rem 2rem !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3) !important;
        margin: 0.8rem auto 0 !important;
        display: block !important;
        width: fit-content !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
        backdrop-filter: blur(4px);
    }
    [data-testid="stFileUploadDropzone"] section > button:hover,
    [data-testid="stFileUploadDropzone"] section > button:hover span {
        background: linear-gradient(135deg, rgba(0, 229, 255, 1) 0%, rgba(0, 153, 255, 1) 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4) !important;
    }

    [data-testid="stClearedFormSubmitButton"] { display: none !important; }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: #060913 !important;
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.02) 1px, transparent 1px), 
            linear-gradient(90deg, rgba(0, 229, 255, 0.02) 1px, transparent 1px) !important;
        background-size: 30px 30px !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(0, 229, 255, 0.15) !important;
    }

    /* Glassmorphism Forms */
    div[data-testid="stForm"] {
        background: rgba(13, 20, 35, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
    }

    /* Glassmorphism Expanders */
    [data-testid="stExpander"] {
        background: rgba(13, 20, 35, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    }

    /* Glassmorphism Alert / Info Boxes */
    div[data-testid="stAlert"] {
        background: rgba(13, 20, 35, 0.5) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
    }

    /* Glassmorphism Metric Cards */
    .metric-card {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: rgba(255, 149, 0, 0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 149, 0, 0.25);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-2px); }

    .metric-card-alt1 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: rgba(0, 230, 118, 0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 230, 118, 0.25);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card-alt1:hover { transform: translateY(-2px); }

    .metric-card-alt2 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: rgba(255, 23, 68, 0.06);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 23, 68, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card-alt2:hover { transform: translateY(-2px); }

    .metric-card-alt3 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: rgba(224, 64, 251, 0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(224, 64, 251, 0.25);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .metric-card-alt3:hover { transform: translateY(-2px); }

    .small-label { font-size: 0.85rem; font-weight: 700; margin-bottom: 0.3rem; }
    .metric-card .small-label { color: #ffb74d !important; }
    .metric-card-alt1 .small-label { color: #69f0ae !important; }
    .metric-card-alt2 .small-label { color: #ff5252 !important; }
    .metric-card-alt3 .small-label { color: #ea80fc !important; }

    .big-number { font-size: 1.8rem; font-weight: 800; }
    .metric-card .big-number { color: #ffa726 !important; }
    .metric-card-alt1 .big-number { color: #00e676 !important; }
    .metric-card-alt2 .big-number { color: #ff1744 !important; }
    .metric-card-alt3 .big-number { color: #e040fb !important; }

    /* Buttons */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, rgba(0, 229, 255, 0.8) 0%, rgba(0, 153, 255, 0.8) 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(4px);
    }
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, rgba(0, 229, 255, 1) 0%, rgba(0, 153, 255, 1) 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4) !important;
    }

    /* Style input elements to match */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="textarea"] > div, 
    div[data-baseweb="input"] > div {
        background-color: rgba(9, 14, 25, 0.75) !important;
        border: 1px solid rgba(0, 229, 255, 0.25) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(5px);
        color: #ffffff !important;
    }
    div[role="listbox"] {
        background-color: #0d1625 !important;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "uploaded_file_key" not in st.session_state:
    st.session_state.uploaded_file_key = 0
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "auth_user" not in st.session_state:
    st.session_state.auth_user = {"email": "guest@example.com"}
if "auth_token" not in st.session_state:
    st.session_state.auth_token = "guest-token"
if "upload_log_message" not in st.session_state:
    st.session_state.upload_log_message = ""
if "upload_log_error" not in st.session_state:
    st.session_state.upload_log_error = False
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "critical_columns" not in st.session_state:
    st.session_state.critical_columns = []
if "business_context" not in st.session_state:
    st.session_state.business_context = ""


def get_previously_uploaded_files() -> list[str]:
    import os
    upload_dir = "/Users/ankushpratham/Ankush_Coding/AI_Model/data_loss_analyzer/uploaded_datasets"
    if not os.path.exists(upload_dir):
        return []
    try:
        return sorted([
            f for f in os.listdir(upload_dir)
            if f.endswith((".csv", ".json")) and os.path.isfile(os.path.join(upload_dir, f))
        ])
    except Exception:
        return []


def save_uploaded_file_locally(filename: str, file_bytes: bytes) -> None:
    import os
    upload_dir = "/Users/ankushpratham/Ankush_Coding/AI_Model/data_loss_analyzer/uploaded_datasets"
    try:
        os.makedirs(upload_dir, exist_ok=True)
        with open(os.path.join(upload_dir, filename), "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        st.warning(f"Could not save file locally: {e}")


def reset_to_home() -> None:
    st.session_state.file_uploaded = False
    st.session_state.uploaded_df = None
    st.session_state.uploaded_filename = None
    st.session_state.analysis = None
    st.session_state.summary = None
    st.session_state.critical_columns = []
    st.session_state.business_context = ""
    st.session_state.uploaded_file_key += 1




mongo_ok, mongo_msg = mongo_config_status()

with st.sidebar:
    if not mongo_ok:
        st.warning(mongo_msg)
    elif st.session_state.upload_log_message:
        if st.session_state.upload_log_error:
            st.error(st.session_state.upload_log_message)
        else:
            st.caption(st.session_state.upload_log_message)

if not st.session_state.file_uploaded:
    st.markdown(
        """
        <div class="hero">
          <h1>Data Loss Analyzer</h1>
          <p>Detect missing data patterns and understand their business impact</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded = st.file_uploader(
            "Upload Your CSV or JSON File",
            type=["csv", "json"],
            key=f"uploader_{st.session_state.uploaded_file_key}",
        )

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        save_uploaded_file_locally(uploaded.name, file_bytes)
        st.session_state.uploaded_df = parse_uploaded_dataset(file_bytes, uploaded.name)
        st.session_state.uploaded_filename = uploaded.name
        if mongo_ok:
            saved, message = save_uploaded_csv_pair(
                user_email=st.session_state.auth_user["email"],
                csv_file_name=uploaded.name,
            )
            st.session_state.upload_log_message = message
            st.session_state.upload_log_error = not saved
            cached_recent_user_history.clear()
        st.session_state.file_uploaded = True
        st.rerun()

    st.divider()
    st.markdown(
        """
        **📝 Tips for best results:**
        - Include sales columns like revenue, order_value, customer_id, region, and date
        - Ensure your CSV has proper headers
        - Larger datasets provide better insights
        """
    )

    local_files = get_previously_uploaded_files()
    if local_files:
        st.markdown(
            """
            <div style='text-align: center; margin-top: 1.5rem; margin-bottom: 1rem;'>
                <h3 style='color: #00838f;'>Select a Previously Analyzed Dataset</h3>
                <p style='color: #00695c;'>Pick an already uploaded file below to bypass re-uploading:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            selected_file = st.selectbox(
                "Choose an existing dataset",
                options=local_files,
                label_visibility="collapsed",
                key="prev_dataset_select"
            )
            if st.button("Load and Analyze Selected Dataset", use_container_width=True):
                import os
                file_path = os.path.join("/Users/ankushpratham/Ankush_Coding/AI_Model/data_loss_analyzer/uploaded_datasets", selected_file)
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    st.session_state.uploaded_df = parse_uploaded_dataset(file_bytes, selected_file)
                    st.session_state.uploaded_filename = selected_file
                    st.session_state.file_uploaded = True
                    if mongo_ok:
                        saved, message = save_uploaded_csv_pair(
                            user_email=st.session_state.auth_user["email"],
                            csv_file_name=selected_file,
                        )
                        st.session_state.upload_log_message = message
                        st.session_state.upload_log_error = not saved
                        cached_recent_user_history.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading file: {e}")

    if mongo_ok:
        history = cached_recent_user_history(st.session_state.auth_user["email"], limit=5)
        if history:
            st.subheader("Recent Uploaded CSV Files")
            for item in history:
                created = item.get("created_at")
                timestamp = ""
                if created:
                    timestamp = created.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                st.write(
                    f"- **{item.get('value', item.get('csv_file_name', 'Unknown file'))}** "
                    + (f" | {timestamp}" if timestamp else "")
                )

    st.stop()

col1, col2 = st.columns([0.15, 0.85])
with col1:
    if st.button("Back to Upload", use_container_width=True):
        reset_to_home()
        st.rerun()

st.markdown(
    f"""
    <div class="hero">
      <h1 style="color: #00838f;">Analysis Results</h1>
      <p style="color: #00695c;">Analyzing: <strong>{st.session_state.uploaded_filename}</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)

df = st.session_state.uploaded_df

with st.sidebar:
    st.markdown("---")
    st.subheader("✏️ Business Notes")
    with st.form("analysis_controls", clear_on_submit=False):
        business_context = st.text_area(
            "Add notes the summary should consider",
            value=st.session_state.business_context,
            placeholder="Example: Revenue is recognized at order level and region-level fields drive territory reporting.",
            height=150,
            label_visibility="collapsed",
        )

        critical_default = [
            c
            for c in ["order_id", "customer_id", "region", "order_date", "order_value"]
            if c in df.columns
        ]
        if not st.session_state.critical_columns:
            st.session_state.critical_columns = critical_default

        critical_columns = st.multiselect(
            "Critical columns for sales impact",
            options=list(df.columns),
            default=st.session_state.critical_columns,
        )
        run_analysis = st.form_submit_button("Run Analysis", use_container_width=True)

if run_analysis or st.session_state.analysis is None or st.session_state.summary is None:
    st.session_state.business_context = business_context
    st.session_state.critical_columns = critical_columns
    analysis, summary = run_analysis_cached(df, tuple(critical_columns), business_context)
    st.session_state.analysis = analysis
    st.session_state.summary = summary

analysis = st.session_state.analysis
summary = st.session_state.summary

with st.sidebar:
    st.markdown("---")
    local_files = get_previously_uploaded_files()
    if local_files:
        st.subheader("📁 Switch Dataset")
        try:
            current_idx = local_files.index(st.session_state.uploaded_filename)
        except ValueError:
            current_idx = 0
        selected_file = st.selectbox(
            "Quick switch to another dataset",
            options=local_files,
            index=current_idx,
            key="sidebar_dataset_switch"
        )
        if selected_file != st.session_state.uploaded_filename:
            import os
            file_path = os.path.join("/Users/ankushpratham/Ankush_Coding/AI_Model/data_loss_analyzer/uploaded_datasets", selected_file)
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                st.session_state.uploaded_df = parse_uploaded_dataset(file_bytes, selected_file)
                st.session_state.uploaded_filename = selected_file
                st.session_state.file_uploaded = True
                # Reset analysis state to trigger re-run
                st.session_state.analysis = None
                st.session_state.summary = None
                st.session_state.critical_columns = []
                st.session_state.business_context = ""
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")

    if mongo_ok:
        history = cached_recent_user_history(st.session_state.auth_user["email"], limit=5)
        if history:
            st.caption("Recent uploaded CSV files")
            for item in history:
                created = item.get("created_at")
                timestamp = ""
                if created:
                    timestamp = created.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                st.write(
                    f"- {item.get('value', item.get('csv_file_name', 'Unknown file'))}"
                    + (f" | {timestamp}" if timestamp else "")
                )

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f'<div class="metric-card"><div class="small-label">Rows</div><div class="big-number">{analysis["rows"]:,}</div></div>',
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f'<div class="metric-card-alt1"><div class="small-label">Columns</div><div class="big-number">{analysis["columns"]:,}</div></div>',
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f'<div class="metric-card-alt2"><div class="small-label">Missing cells</div><div class="big-number">{analysis["missing_cells"]:,}</div></div>',
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f'<div class="metric-card-alt3"><div class="small-label">At-risk rows</div><div class="big-number">{analysis["at_risk_rows"]:,}</div></div>',
        unsafe_allow_html=True,
    )

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Missingness by column")
    missing_df = analysis["missing_by_column"]
    st.dataframe(missing_df, use_container_width=True, hide_index=True)
    if not missing_df.empty:
        chart_df = missing_df.set_index("column")[["missing_pct"]]
        st.bar_chart(chart_df)

with right:
    st.subheader("Sales Impact Summary")
    st.success(summary["summary"])
    st.write("**Most relevant evidence**")
    for item in summary["evidence"]:
        st.write(f"- {item}")

st.subheader("Detailed Findings")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**High-risk fields**")
    st.dataframe(analysis["high_risk_fields"], use_container_width=True, hide_index=True)
with col2:
    st.markdown("**Recommended next steps**")
    for step in analysis["recommendations"]:
        st.write(f"- {step}")

with st.expander("Show preview data"):
    st.dataframe(df.head(20), use_container_width=True)
