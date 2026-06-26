# RetailIQ — Live Dashboard (Streamlit)

A deployed, interactive version of the RetailIQ analysis — same findings as the Power BI dashboard, but live at a shareable URL with no software install required to view it.

## Why a separate CSV layer (`data/`)

This app reads from small, pre-aggregated CSVs (`data_prep.py` generates them from the Postgres database) rather than the raw ~60MB of source tables. Streamlit Community Cloud has no access to a hosted database for this project, and shipping raw row-level data to a dashboard that only ever displays aggregates would be wasteful — the 11 files here total under 10KB combined and load instantly.

## Local testing (verified working)

```bash
pip install -r requirements.txt
streamlit run app.py
```
Tested locally: returns HTTP 200, passes Streamlit's `_stcore/health` check, zero errors in logs.

## Deploying to Streamlit Community Cloud (free)

1. Push this `streamlit_app/` folder (including `data/`) to a GitHub repository
2. Go to **share.streamlit.io** → sign in with GitHub
3. Click **New app** → select your repo, branch, and set the main file path to `streamlit_app/app.py`
4. Click **Deploy** — Streamlit Cloud installs `requirements.txt` automatically and gives you a live URL (e.g., `retailiq-pranay.streamlit.app`)
5. Embed this URL in your resume/portfolio, or iframe it into `pranay-devloper-portfolio.netlify.app`

## Regenerating the data (if the underlying analysis changes)

```bash
python3 data_prep.py
```
This reconnects to the Postgres `retailiq` database and re-exports all 11 CSVs in `data/`.

## Files
```
streamlit_app/
├── app.py              # Main dashboard (2 pages: Executive Overview, Customer Segmentation)
├── data_prep.py         # Generates the pre-aggregated CSVs from Postgres
├── data/                 # 11 small CSVs the app reads from
├── requirements.txt
└── README.md
```
