# workshop-agent
A collection of exercises and demo ai workflows for hackathon

Small Streamlit demo that calls a Dify Workflow to generate a Vacation plan in `Markdown` and render it in the browser.

This repo contains:

- `app.py` - Streamlit UI and helper functions that call the Dify Workflows API and extract HTML from the response.
- `pyproject.toml` - Python dependency manifest.

## Features

- Calls Dify Workflows (blocking mode) and shows raw response.
- Extracts raw HTML even when the Workflow returns explanatory text + a Markdown code block (```html ... ```).
- Renders the HTML inline in Streamlit and offers a download button

## Requirements

- Python 3.11+
- See `pyproject.toml` for pinned dependencies (Streamlit, requests).

### Set up Virtual Env (Mac)

```bash
python -m venv .venv
source .venv/bin/activate
pip install uv
uv sync
```

### Set up Virtual Env (Windows)
```shell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install uv
uv sync
```
### Check virtual env packages

```
pip list
```

## Configuration

The app needs the Dify API key and optional configuration. You can provide them via Streamlit secrets or environment variables.

- `DIFY_API_KEY` (required) — API key for your Dify instance.
- `BASE_URL` (optional) — Dify base URL (default: `https://api.dify.ai`).
- `WORKFLOW_ID` (optional) — workflow id when you prefer the `/v1/workflows/{id}/run` endpoint.

Recommended: create a file `.streamlit/secrets.toml` with:

```toml
[default]
DIFY_API_KEY = "your_api_key_here"
```

## Run

Start the Streamlit app from the project root:

```bash
streamlit run app.py
```

Open the browser at the address Streamlit prints (usually `http://localhost:8501`). Fill the form and click "Call Dify for Plan".

## Troubleshooting

- If you see `Thiếu DIFY_API_KEY` in the UI, ensure `DIFY_API_KEY` is present in `.streamlit/secrets.toml` or the environment.
- If Streamlit shows the raw response but no HTML, check that your Workflow's final node outputs either `html` or an `output` that contains the full HTML. The extractor now checks `data.outputs.output` first.
- Large HTML payloads may take time; the HTTP timeout in `app.py` defaults to 180 seconds for blocking response mode (configurable via `HTTP_TIMEOUT`).

## Notes & Next steps

- If you want the app to support more response shapes, add additional candidate paths in `extract_html`.
- Consider sanitizing or sandboxing untrusted HTML before rendering in production.

![alt text](image.png)
![alt text](image-1.png)
