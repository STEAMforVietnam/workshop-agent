import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from src.utils import call_dify_workflow, extract_html, render_open_new_tab_button, get_html_preview_component

load_dotenv()

DIFY_API_KEY = st.secrets.get("DIFY_API_KEY") if not os.getenv("DIFY_API_KEY") else os.getenv("DIFY_API_KEY") 
BASE_URL     = "https://api.dify.ai"
# 1x1 transparent PNG (base64)
# _BLANK_FAVICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/aoGxX8AAAAASUVORK5CYII="
# try:
#     _blank_favicon = base64.b64decode(_BLANK_FAVICON_B64)
# except Exception:
#     _blank_favicon = None

st.set_page_config(
    page_title="Portfolio Generator via Dify",
    # page_icon=_blank_favicon,  # neutral favicon (no icon)
    layout="wide",
)


# ===== UI =====
# Custom CSS for professional look and to hide Streamlit chrome (menu/header/footer)
st.markdown("""
<style>
    /* Hide Streamlit default chrome */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}

    /* Tidy buttons */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #ddd;
        transition: all 0.2s ease-in-out;
        background: #fff;
    }
    .stButton > button:hover {
        border-color: #999;
        color: #111;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }

    /* Subtle containers */
    .success-message {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f1f8f4;
        color: #0f5132;
        border: 1px solid #cfe3d6;
    }
    .portfolio-card {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e6e6e6;
        margin: 0.5rem 0;
        background: #fff;
    }

    /* Status badges (used if needed) */
    .status-badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem; font-weight: 500; }
    .status-success { background-color: #e8f5e9; color: #2e7d32; }
    .status-error   { background-color: #ffebee; color: #c62828; }
    .status-warning { background-color: #fff8e1; color: #ef6c00; }

    /* Reduce top/bottom padding slightly */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("AI Portfolio Generator")
st.markdown("Fill your details, generate via Dify, preview and download.")

# Minimal sidebar: only show a reminder if missing API key
with st.sidebar:
    if not os.getenv("DIFY_API_KEY"):
        st.warning("Please configure `DIFY_API_KEY` in `.env`.")

# Load portfolio data if selected from history
default_values = {
    "place_to_visit": "Trần Khánh Thành",
    "time_to_visit": "Software Engineer", 
}

# No history loading in simplified UI

with st.form("portfolio_form", height="stretch"):
    # col1, col2 = st.columns(2)

    place_to_visit = st.text_input("Nơi muốn đến", value=default_values["place_to_visit"])
    time_to_visit = st.text_input("Khoảng thời gian muốn đến", value=default_values["time_to_visit"])
        
    user_id = "3a469858-bd0a-4800-97e7-c572d7bbb759"
    submitted = st.form_submit_button("Call Dify for Plan", use_container_width=True)

# ===== Submit =====
if submitted:
    if not os.getenv("DIFY_API_KEY"):
        st.error("Thiếu DIFY_API_KEY. Vui lòng cấu hình trong `.env`.")
        st.stop()

    # Chuẩn hoá inputs theo ví dụ bạn đưa:
    inputs = {
        "full_name": place_to_visit.strip(),
        "job_title": time_to_visit.strip(),
        
        # Nếu workflow của bạn có sử dụng các sys.* thì có thể truyền thêm:
        # "sys.files": [],  # ở dưới có ví dụ chuyển file -> base64/URL nếu cần
        # "sys.app_id": "...",
        # "sys.workflow_id": WORKFLOW_ID or "..."
    }

    # Đính kèm file nếu workflow cần (minh hoạ: đọc bytes -> base64)
    # Nhiều workflow của Dify đọc file từ "sys.files" theo dạng URL; nếu bạn cần upload lên storage khác rồi truyền URL.
    # Ở đây chỉ demo cách đưa metadata về file; điều chỉnh theo node đọc file của bạn.
    # Simple mode: no file attachments

    with st.spinner(f"Đang gọi Dify workflow (blocking)"):
        result = call_dify_workflow(inputs, user_id=user_id)

    status = result.get("status_code", 0)
    response = result.get("json", {})
    
    # Simplified result: only Preview and Download
    if output := response.get("output"):
        st.markdown("### Preview")
        # Robust new-tab open using a Blob (works even when data: URLs are blocked)
        render_open_new_tab_button(output, label="Open Preview in New Tab")
        get_html_preview_component(output, height=600)

        st.download_button(
            "Download Plan",
            data=output.encode("utf-8"),
            file_name=f"Kế_hoạch_du_lịch_{place_to_visit.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True
        )
    else:
        st.error("Không tìm thấy HTML content trong phản hồi từ API")
        with st.expander("Xem phản hồi thô để debug"):
            st.json(output)

# (Tips removed to keep UI minimal)
