"""
Helpers and Utilities for this demo app
"""
import os
import json
import requests
import base64
import uuid
from typing import Dict, Any
import streamlit as st

WORKFLOW_ID  = None # dùng nếu endpoint cần
HTTP_TIMEOUT = 180
# HTTP timeout (seconds) for blocking workflow run

def call_dify_workflow(inputs: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Gọi Dify Workflows (blocking) trả về kết quả ngay.
    Hai biến thể phổ biến của endpoint (tùy phiên bản Dify bạn dùng):
    1) POST {BASE_URL}/v1/workflows/run
       body: {"workflow_id": "...", "inputs": {...}, "response_mode": "blocking", "user": "..."}
    2) POST {BASE_URL}/v1/workflows/{workflow_id}/run
       body: {"inputs": {...}, "response_mode": "blocking", "user": "..."}

    Hàm này thử #2 trước (nếu có WORKFLOW_ID); nếu lỗi 404 sẽ fallback sang #1.
    """

    headers = ...
    url = ...
    payload = ...

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=(15, HTTP_TIMEOUT))
        return {"status_code": resp.status_code, "json": safe_json(resp)}
    except requests.Timeout:
        return {"status_code": 408, "json": {"error": "request_timeout", "message": f"Workflow exceeded timeout of {HTTP_TIMEOUT}s"}}
    except requests.RequestException as e:
        return {"status_code": 0, "json": {"error": "request_error", "message": str(e)}}

def safe_json(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception:
        return {"raw_text": resp.text}

def create_shareable_link(html_content: str) -> str:
    """
    Create a shareable link by encoding HTML content in base64
    This allows users to share portfolios without needing a server
    """
    encoded_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    return f"data:text/html;base64,{encoded_html}"

def render_open_new_tab_button(html_content: str, label: str = "Open Preview in New Tab") -> None:
    """Render a client-side button that opens the HTML in a new tab via Blob.
    This avoids browser restrictions that sometimes show about:blank for data: URLs.
    """
    try:
        b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    except Exception:
        b64 = ""
    btn_id = f"open-new-tab-{uuid.uuid4().hex[:8]}"
    st.components.v1.html(
        f"""
        <button id="{btn_id}" style="display:inline-block;padding:0.5rem 0.75rem;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer;margin-bottom:0.5rem;">{label}</button>
        <script>
        (function(){{
            const b64 = "{b64}";
            const toBlob = (b64str) => {{
                if (!b64str) return new Blob([""], {{type: 'text/html'}});
                const byteChars = atob(b64str);
                const byteNums = new Array(byteChars.length);
                for (let i = 0; i < byteChars.length; i++) byteNums[i] = byteChars.charCodeAt(i);
                return new Blob([new Uint8Array(byteNums)], {{type: 'text/html'}});
            }};
            const blob = toBlob(b64);
            const btn = document.getElementById('{btn_id}');
            if (btn) {{
                btn.addEventListener('click', function() {{
                    const url = URL.createObjectURL(blob);
                    const w = window.open(url, '_blank');
                    if (!w) {{
                        alert('Please allow pop-ups to open the preview.');
                    }}
                    setTimeout(() => URL.revokeObjectURL(url), 60000);
                }});
            }}
        }})();
        </script>
        """,
        height=60,
    )

def save_to_session_state(html_content: str, user_inputs: Dict[str, Any]) -> str:
    """Save generated HTML to session state with unique ID for sharing"""
    if 'portfolios' not in st.session_state:
        st.session_state.portfolios = {}
    
    portfolio_id = str(uuid.uuid4())[:8]
    st.session_state.portfolios[portfolio_id] = {
        'html': html_content,
        'inputs': user_inputs,
        'created_at': datetime.now().isoformat(),
        'title': f"{user_inputs.get('full_name', 'Portfolio')} - {user_inputs.get('job_title', 'Professional')}"
    }
    return portfolio_id

def get_html_preview_component(html_content: str, height: int = 600) -> None:
    """Enhanced HTML preview component with click prevention and error handling"""
    if not html_content.strip():
        st.warning("No HTML content to preview")
        return
    
    # Add responsive meta tag if not present
    if 'viewport' not in html_content:
        html_content = html_content.replace(
            '<head>',
            '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
    
    # More robust click prevention script
    click_prevention_script = """
    <script>
        // Prevent all navigation and interactions
        function preventDefaultBehavior(e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
        
        function setupPreventionHandlers() {
            // Prevent all form submissions
            document.querySelectorAll('form').forEach(function(form) {
                form.addEventListener('submit', preventDefaultBehavior);
            });
            
            // Handle all links
            document.querySelectorAll('a').forEach(function(link) {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const href = link.href;
                    if (href && href.startsWith('mailto:')) {
                        // Allow mailto links
                        window.open(href, '_blank');
                    } else if (href && (href.startsWith('tel:') || href.startsWith('phone:'))) {
                        // Allow phone links
                        window.open(href, '_blank');
                    } else if (href && (href.startsWith('http') || href.startsWith('https'))) {
                        // External links - open in new tab
                        window.open(href, '_blank');
                    } else {
                        // Show info for other links
                        console.log('Link navigation prevented in preview mode:', href || link.textContent);
                    }
                    return false;
                });
                
                // Also prevent default link behavior
                link.style.cursor = 'pointer';
            });
            
            // Prevent button interactions
            document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Button interaction prevented in preview mode');
                    return false;
                });
            });
            
            // Disable form inputs
            document.querySelectorAll('input:not([type="button"]):not([type="submit"]), textarea, select').forEach(function(input) {
                input.addEventListener('focus', function(e) {
                    e.target.blur();
                });
                input.addEventListener('click', preventDefaultBehavior);
                input.style.cursor = 'not-allowed';
                input.title = 'Form inputs disabled in preview mode';
            });
            
            // Prevent context menu
            document.addEventListener('contextmenu', preventDefaultBehavior);
            
            // Prevent drag and drop
            document.addEventListener('dragstart', preventDefaultBehavior);
            document.addEventListener('drop', preventDefaultBehavior);
        }
        
        // Setup handlers when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupPreventionHandlers);
        } else {
            setupPreventionHandlers();
        }
        
        // Also setup with a small delay to catch dynamically added elements
        setTimeout(setupPreventionHandlers, 100);
    </script>
    """
    
    # Inject the script before closing body tag or at the end
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{click_prevention_script}\n</body>')
    elif '</html>' in html_content:
        html_content = html_content.replace('</html>', f'{click_prevention_script}\n</html>')
    else:
        html_content += click_prevention_script
    
    try:
        # Use Streamlit's HTML component with additional security
        st.components.v1.html(
            html_content, 
            height=height, 
            scrolling=True,
        )
    except Exception as e:
        st.error(f"Error rendering HTML preview: {str(e)}")
        with st.expander("View raw HTML content"):
            st.code(html_content, language='html')

def extract_html(result: Dict[str, Any]) -> str:
    """
    Output
    - {"data": {"outputs": {"html": "<...>"}}}
    - hoặc {"data": {"output": "<...>"}} / {"data": "<...>"} / {"output_text": "<...>"}
    - hoặc text có chứa markdown code block ```html...```
    Hàm này quét các nơi hay gặp để lấy HTML.
    """
    if not result:
        return ""
    
    def extract_html_from_markdown(text: str) -> str:
        """
        Trích xuất HTML từ markdown code block.
        Tìm ```html...``` hoặc ````html...```` và lấy nội dung bên trong.
        """
        if not isinstance(text, str):
            return ""
        
        import re
        # Tìm code block html với ít nhất 3 backticks
        patterns = [
            r'```+html\s*\n(.*?)```+',  # ```html hoặc ````html
            r'```+\s*\n<!DOCTYPE html(.*?)```+',  # ```\n<!DOCTYPE html (trường hợp không có label html)
            r'```+\s*\n<html(.*?)```+',  # ```\n<html
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                html_content = matches[0].strip()
                # Nếu match đầu tiên không phải là HTML hoàn chỉnh, thử ghép lại
                if pattern != r'```+html\s*\n(.*?)```+':
                    if pattern == r'```+\s*\n<!DOCTYPE html(.*?)```+':
                        html_content = "<!DOCTYPE html" + html_content
                    elif pattern == r'```+\s*\n<html(.*?)```+':
                        html_content = "<html" + html_content
                
                # Kiểm tra xem có phải HTML hợp lệ không
                if html_content and ('<html' in html_content.lower() or '<!doctype html' in html_content.lower()):
                    return html_content
        
        return ""
    
    # các đường dẫn phổ biến
    candidates = [
        ("data", "outputs", "output"),  # Dify (new) common
        ("data", "outputs", "html"),
        ("data", "outputs", "output_text"),
        ("data", "output"),
        ("data", "answer"),
        ("data", "text"),
        ("data",),
        ("output_text",),
        ("outputs", "html"),
        ("html",),
        ("output",),  # thêm output trực tiếp
        ("raw_text",),  # from safe_json fallback
        ("result",),
    ]
    
    def deep_get(d, path):
        cur = d
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                return None
        return cur

    for path in candidates:
        val = deep_get(result, path)
        if isinstance(val, str) and len(val.strip()) > 0:
            # Thử trích xuất HTML từ markdown trước
            html_from_markdown = extract_html_from_markdown(val)
            if html_from_markdown:
                return html_from_markdown
            # Nếu không phải markdown, kiểm tra xem có phải HTML thô không
            if '<html' in val.lower() or '<!doctype html' in val.lower():
                return val

    # Nếu Dify trả danh sách events (stream đã gom), lấy phần text cuối
    if isinstance(result, dict) and "events" in result and isinstance(result["events"], list):
        texts = [e.get("data", {}).get("text", "") for e in result["events"] if isinstance(e, dict)]
        texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if texts:
            # Thử trích xuất từ text cuối cùng
            html_from_markdown = extract_html_from_markdown(texts[-1])
            if html_from_markdown:
                return html_from_markdown
            # Hoặc ghép tất cả text lại và thử trích xuất
            combined_text = "\n".join(texts)
            html_from_markdown = extract_html_from_markdown(combined_text)
            if html_from_markdown:
                return html_from_markdown
            return texts[-1]
    # Fallback: recursive scan for any string containing HTML or markdown code block
    visited = set()

    def scan(obj) -> str:
        oid = id(obj)
        if oid in visited:
            return ""
        visited.add(oid)
        try:
            if isinstance(obj, dict):
                for v in obj.values():
                    found = scan(v)
                    if found:
                        return found
            elif isinstance(obj, list):
                for v in obj:
                    found = scan(v)
                    if found:
                        return found
            elif isinstance(obj, str):
                s = obj.strip()
                if not s:
                    return ""
                html_from_md = extract_html_from_markdown(s)
                if html_from_md:
                    return html_from_md
                if '<html' in s.lower() or '<!doctype html' in s.lower():
                    return s
                # If it looks like JSON string, try parse once
                if (s.startswith('{') and s.endswith('}')) or (s.startswith('[') and s.endswith(']')):
                    try:
                        parsed = json.loads(s)
                        return scan(parsed)
                    except Exception:
                        return ""
        except Exception:
            return ""
        return ""

    fallback = scan(result)
    if isinstance(fallback, str) and fallback:
        return fallback

    return ""
