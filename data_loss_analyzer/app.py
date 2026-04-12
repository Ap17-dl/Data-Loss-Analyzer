from __future__ import annotations

from datetime import timezone

import pandas as pd
import streamlit as st

from analysis import analyze_missing_data
from auth import auth_config_status, get_user_from_token, sign_in_user, sign_out_user, sign_up_user
from rag import default_knowledge_base, generate_sales_impact_summary
from storage import mongo_config_status, recent_user_history, save_uploaded_csv_pair

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

    .stApp {
        background: linear-gradient(180deg, #f0f9ff 0%, #f5f3ff 45%, #fff5f7 100%);
        color: #1a1a1a;
    }
    .block-container { padding-top: 2rem; }
    .hero {
        padding: 3rem 2.5rem;
        border: 3px solid #00d4ff;
        border-radius: 20px;
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
        box-shadow: 0 15px 50px rgba(0, 212, 255, 0.3);
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 { color: #ffffff; margin: 0; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .hero p { color: #f0f9ff; margin: 0.8rem 0 0; font-weight: 500; }

    div[data-testid="stFileUploader"] {
        border: 3px dashed #00d4ff !important;
        border-radius: 16px !important;
        background: rgba(0, 212, 255, 0.08) !important;
        padding: 2.5rem 2rem 2rem !important;
        margin: 1.5rem 0 !important;
        text-align: center !important;
    }

    div[data-testid="stFileUploader"] label p {
        color: #00695c !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.4rem 0 !important;
    }

    div[data-testid="stFileUploader"] label::after {
        content: "Get started by uploading a CSV file to analyze missing data and sales impact";
        display: block;
        color: #00897b;
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

    [data-testid="stFileUploadDropzone"] section > svg { display: block !important; color: #00b0d0 !important; }
    [data-testid="stFileUploadDropzone"] section > span,
    [data-testid="stFileUploadDropzone"] section > p   { display: block !important; color: #00897b !important; }

    [data-testid="stFileUploadDropzone"] section > button,
    [data-testid="stFileUploadDropzone"] section > button span,
    [data-testid="stFileUploadDropzone"] section > button p {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 2px solid #0099ff !important;
        padding: 0.8rem 2rem !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3) !important;
        margin: 0.8rem auto 0 !important;
        display: block !important;
        width: fit-content !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploadDropzone"] section > button:hover,
    [data-testid="stFileUploadDropzone"] section > button:hover span {
        background: linear-gradient(135deg, #00bbff 0%, #0088ff 100%) !important;
        box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stClearedFormSubmitButton"] { display: none !important; }

    .metric-card {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #ffb347 0%, #ff9500 100%);
        border: 2px solid #ff8c00;
        box-shadow: 0 8px 20px rgba(255, 149, 0, 0.2);
    }
    .metric-card-alt1 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #39ff14 0%, #00ff00 100%);
        border: 2px solid #00dd00;
        box-shadow: 0 8px 20px rgba(0, 255, 0, 0.2);
    }
    .metric-card-alt2 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #ff006e 0%, #ec0c38 100%);
        border: 2px solid #ff0055;
        box-shadow: 0 8px 20px rgba(255, 0, 110, 0.2);
    }
    .metric-card-alt3 {
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #9d4edd 0%, #7209b7 100%);
        border: 2px solid #7209b7;
        box-shadow: 0 8px 20px rgba(146, 39, 141, 0.2);
    }
    .small-label { color: #ffffff; font-size: 0.85rem; font-weight: 600; }
    .big-number  { font-size: 1.8rem; font-weight: 700; color: #ffffff; }

    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3) !important;
    }
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #00bbff 0%, #0088ff 100%) !important;
        box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4) !important;
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
    st.session_state.auth_user = None
if "auth_token" not in st.session_state:
    st.session_state.auth_token = ""
if "upload_log_message" not in st.session_state:
    st.session_state.upload_log_message = ""
if "upload_log_error" not in st.session_state:
    st.session_state.upload_log_error = False


def reset_to_home() -> None:
    st.session_state.file_uploaded = False
    st.session_state.uploaded_df = None
    st.session_state.uploaded_filename = None
    st.session_state.uploaded_file_key += 1


def reset_auth() -> None:
    st.session_state.auth_user = None
    st.session_state.auth_token = ""
    reset_to_home()


def auth_gate() -> None:
    auth_ok, auth_msg = auth_config_status()
    if not auth_ok:
        st.error(auth_msg)
        st.info("Authentication is required now. Configure Supabase and refresh.")
        st.stop()

    if st.session_state.auth_token and st.session_state.auth_user is None:
        st.session_state.auth_user = get_user_from_token(st.session_state.auth_token)

    if st.session_state.auth_user is not None:
        return

    st.markdown(
        """
        <div class="hero">
          <h1>Data Loss Analyzer</h1>
          <p>Create an account or sign in to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sign_in_tab, sign_up_tab = st.tabs(["Sign In", "Sign Up"])

    with sign_in_tab:
        with st.form("sign_in_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submit_in = st.form_submit_button("Sign In", use_container_width=True)
        if submit_in:
            ok, message, user = sign_in_user(email.strip(), password)
            if ok and user:
                st.session_state.auth_user = user
                st.session_state.auth_token = user["access_token"]
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with sign_up_tab:
        with st.form("sign_up_form", clear_on_submit=False):
            email = st.text_input("New email", placeholder="you@example.com")
            password = st.text_input("New password", type="password", help="Use at least 8 characters.")
            submit_up = st.form_submit_button("Create Account", use_container_width=True)
        if submit_up:
            if len(password) < 8:
                st.warning("Password should be at least 8 characters.")
            else:
                ok, message = sign_up_user(email.strip(), password)
                if ok:
                    st.success(message)
                else:
                    st.error(message)

    st.stop()


auth_gate()

mongo_ok, mongo_msg = mongo_config_status()

with st.sidebar:
    st.subheader("Account")
    st.caption(f"Signed in as: **{st.session_state.auth_user['email']}**")
    if st.button("Sign Out", use_container_width=True):
        sign_out_user()
        reset_auth()
        st.rerun()
    if not mongo_ok:
        st.warning(mongo_msg)

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
            "Upload Your CSV File",
            type=["csv"],
            key=f"uploader_{st.session_state.uploaded_file_key}",
        )

    if uploaded is not None:
        st.session_state.uploaded_df = pd.read_csv(uploaded)
        st.session_state.uploaded_filename = uploaded.name
        if mongo_ok:
            saved, message = save_uploaded_csv_pair(
                user_email=st.session_state.auth_user["email"],
                csv_file_name=uploaded.name,
            )
            st.session_state.upload_log_message = message
            st.session_state.upload_log_error = not saved
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

    if mongo_ok:
        if st.session_state.upload_log_message:
            st.session_state.upload_log_message = ""
            st.session_state.upload_log_error = False

        history = recent_user_history(st.session_state.auth_user["email"], limit=5)
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
    business_context = st.text_area(
        "Add notes the summary should consider",
        placeholder="Example: Revenue is recognized at order level and region-level fields drive territory reporting.",
        height=150,
        label_visibility="collapsed",
    )

critical_default = [
    c for c in ["order_id", "customer_id", "region", "order_date", "order_value"] if c in df.columns
]
critical_columns = st.multiselect(
    "Critical columns for sales impact",
    options=list(df.columns),
    default=critical_default,
)

analysis = analyze_missing_data(df, critical_columns=critical_columns)
summary = generate_sales_impact_summary(
    analysis,
    business_context=business_context,
    knowledge_base=default_knowledge_base(),
)

with st.sidebar:
    st.markdown("---")
    if mongo_ok:
        history = recent_user_history(st.session_state.auth_user["email"], limit=5)
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
