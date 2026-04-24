"""Anomalia Cenowa — Streamlit application for price anomaly detection."""

import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import uuid

# Page config MUST be first
st.set_page_config(
    page_title="Anomalia Cenowa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from parsing import parse_file
from analysis import run_analysis, get_anomaly_summary, get_anomaly_indices
from excel_export import generate_xlsx
from pdf_report import generate_pdf
from database import init_db, save_analysis, save_price, get_last_price, get_analysis_history, get_price_history
from utils import (
    generate_session_id, safe_float,
    make_chart_anomalies_by_month, make_chart_top_indices_count,
    make_chart_top_indices_sum_dev, make_chart_deviation_histogram, make_chart_pareto,
)

# ─── Init ───────────────────────────────────────────────────────────────────
init_db()

if "session_id" not in st.session_state:
    st.session_state.session_id = generate_session_id()
if "df_raw" not in st.session_state:
    st.session_state.df_raw = None
if "df_result" not in st.session_state:
    st.session_state.df_result = None
if "file_info" not in st.session_state:
    st.session_state.file_info = None
if "file_name" not in st.session_state:
    st.session_state.file_name = ""
if "manual_prices" not in st.session_state:
    st.session_state.manual_prices = {}
if "analysis_id" not in st.session_state:
    st.session_state.analysis_id = None
if "xlsx_bytes" not in st.session_state:
    st.session_state.xlsx_bytes = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Analiza"

# ─── CSS ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ==========================================================
   LIGHT GREY DASHBOARD REDESIGN — Anomalia Cenowa
   Styl zgodny z makietą: jasny panel, szary sidebar,
   białe karty, dużo światła, spokojne akcenty.
   ========================================================== */

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}

.stApp {
    background: #F8FAFC;
    color: #111827;
}

/* Main content */
.main .block-container {
    background: #F8FAFC;
    padding: 1.7rem 2rem 2.6rem 2rem !important;
    max-width: 1500px;
}

/* Sidebar - jasnoszary jak na wizualizacji */
[data-testid="stSidebar"] {
    background: #F3F4F6 !important;
    border-right: 1px solid #E5E7EB;
}

[data-testid="stSidebar"] * {
    color: #111827 !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #111827 !important;
}

[data-testid="stSidebar"] .stMarkdown hr {
    border-color: #E5E7EB !important;
}

/* Sidebar buttons jako płaskie pozycje menu */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #111827 !important;
    border: 0 !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    font-weight: 600 !important;
    justify-content: flex-start !important;
    padding: 0.65rem 0.85rem !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #E5E7EB !important;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #D1D5DB !important;
    color: #111827 !important;
}

/* Sidebar inputs */
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stCheckbox label,
[data-testid="stSidebar"] .stSelectbox label {
    color: #374151 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stTextInput,
[data-testid="stSidebar"] .stNumberInput {
    background: transparent !important;
}

/* Page header */
.page-header {
    padding: 0 0 18px 0;
    border-bottom: 0;
    margin-bottom: 18px;
}

.page-header h1 {
    font-size: 28px;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.025em;
}

.page-header p {
    font-size: 14px;
    color: #64748B;
    margin: 7px 0 0 0;
}

/* Cards base */
.kpi-card,
.info-box,
.status-box,
.chart-card,
.section-header {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

/* KPI cards */
.kpi-card {
    padding: 20px 18px;
    min-height: 116px;
    transition: all .16s ease;
}

.kpi-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 22px rgba(15,23,42,0.06);
    border-color: #D1D5DB;
}

.kpi-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-bottom: 12px;
    background: #F1F5F9;
}

.kpi-value {
    font-size: 29px;
    font-weight: 800;
    line-height: 1.1;
    color: #0F172A;
    letter-spacing: -0.025em;
}

.kpi-label {
    font-size: 12px;
    color: #64748B;
    margin-top: 7px;
    font-weight: 600;
}

/* Pastel icons / value accents */
.kpi-accent-blue .kpi-icon { background: #EEF2FF; color: #3B82F6; }
.kpi-accent-red .kpi-icon { background: #FEE2E2; color: #EF4444; }
.kpi-accent-orange .kpi-icon { background: #FFEDD5; color: #F97316; }
.kpi-accent-green .kpi-icon { background: #DCFCE7; color: #22C55E; }
.kpi-accent-purple .kpi-icon { background: #F3E8FF; color: #8B5CF6; }

.kpi-accent-blue .kpi-label { color: #2563EB; }
.kpi-accent-red .kpi-label { color: #EF4444; }
.kpi-accent-orange .kpi-label { color: #F97316; }
.kpi-accent-green .kpi-label { color: #16A34A; }
.kpi-accent-purple .kpi-label { color: #8B5CF6; }

/* Info / upload / status cards */
.info-box,
.status-box {
    padding: 20px 18px;
    height: 100%;
}

.info-box h4,
.status-box h4,
.chart-card h5 {
    font-size: 15px;
    font-weight: 800;
    color: #0F172A;
    margin: 0 0 16px 0;
    border-bottom: none;
    padding-bottom: 0;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid #F1F5F9;
    font-size: 12px;
}

.info-row:last-child {
    border-bottom: none;
}

.info-key {
    color: #64748B;
    font-weight: 600;
}

.info-val {
    color: #0F172A;
    font-weight: 700;
    text-align: right;
    max-width: 62%;
    word-break: break-word;
}

/* Upload visual */
.upload-box {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 30px 18px;
    text-align: center;
    border: 2px dashed #CBD5E1;
    box-shadow: none;
}

.upload-icon {
    font-size: 44px;
    color: #64748B;
    margin-bottom: 8px;
}

.upload-title {
    font-size: 15px;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 5px;
}

.upload-sub {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 12px;
}

/* Status */
.status-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #F1F5F9;
    font-size: 12px;
    color: #475569;
}

.status-step:last-child {
    border-bottom: none;
}

.status-ok {
    color: #22C55E;
    font-size: 16px;
}

.status-wait {
    color: #94A3B8;
    font-size: 16px;
}

.status-success {
    background: #ECFDF5;
    border: 1px solid #BBF7D0;
    border-radius: 12px;
    padding: 11px 14px;
    margin-top: 14px;
    font-size: 12px;
    color: #047857;
    font-weight: 800;
    text-align: center;
}

.status-pending {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 11px 14px;
    margin-top: 14px;
    font-size: 12px;
    color: #64748B;
    font-weight: 800;
    text-align: center;
}

/* Section header */
.section-header {
    padding: 18px 22px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.section-title {
    font-size: 22px;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.025em;
}

.section-sub {
    font-size: 13px;
    color: #64748B;
    margin: 4px 0 0 0;
}

/* Charts */
.chart-card {
    padding: 18px;
}

/* Table header */
.anomaly-table-header {
    font-size: 17px;
    font-weight: 800;
    color: #0F172A;
    margin: 24px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Correction rows */
.corr-row {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 15px 16px;
    margin-bottom: 9px;
    border: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

.corr-idx {
    font-weight: 800;
    color: #0F172A;
    font-size: 14px;
    min-width: 160px;
}

.corr-badge {
    background: #FEE2E2;
    color: #DC2626;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 999px;
}

.corr-median {
    font-size: 12px;
    color: #64748B;
}

/* Buttons */
.stButton button,
.stDownloadButton button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 0.55rem 1rem !important;
    border: 1px solid #D1D5DB !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.05) !important;
    transition: all .15s ease !important;
}

.stButton button:hover,
.stDownloadButton button:hover {
    transform: translateY(-1px);
    border-color: #94A3B8 !important;
}

/* Primary buttons - dark grey, jak mockup */
.stButton button[kind="primary"],
.stDownloadButton button[kind="primary"] {
    background: #4B5563 !important;
    border-color: #4B5563 !important;
    color: #FFFFFF !important;
}

.stButton button[kind="primary"]:hover,
.stDownloadButton button[kind="primary"]:hover {
    background: #374151 !important;
    border-color: #374151 !important;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 10px !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

/* Alerts */
.stAlert {
    border-radius: 14px !important;
}

/* Sidebar helper boxes */
[data-testid="stSidebar"] div[style*="background:rgba"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

[data-testid="stSidebar"] p {
    color: #475569 !important;
}

[data-testid="stSidebar"] p[style*="letter-spacing"] {
    color: #64748B !important;
}

/* Better visual rhythm */
div[data-testid="column"] {
    padding-bottom: 0.15rem;
}
</style>
""", unsafe_allow_html=True)



# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Anomalia Cenowa")
    st.markdown("<p style='font-size:12px;color:#475569;margin-top:-8px;'>Wykrywanie anomalii cenowych w danych magazynowych</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Navigation
    st.markdown("<p style='font-size:11px;font-weight:700;color:#64748B;letter-spacing:1px;margin-bottom:6px;'>NAWIGACJA</p>", unsafe_allow_html=True)
    pages = ["Analiza", "Korekta cen", "Podsumowanie", "Historia analiz", "Historia cen ręcznych", "Ustawienia"]
    page_icons = ["🔍", "✏️", "📈", "📋", "💰", "⚙️"]

    for icon, page in zip(page_icons, pages):
        is_active = st.session_state.active_tab == page
        btn = st.button(
            f"{icon} {page}",
            key=f"nav_{page}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        )
        if btn:
            st.session_state.active_tab = page
            st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:11px;font-weight:700;color:#64748B;letter-spacing:1px;margin-bottom:6px;'>USTAWIENIA ANALIZY</p>", unsafe_allow_html=True)
    threshold = st.slider(
        "Próg odchylenia (%)",
        min_value=1, max_value=200, value=20, step=1,
        help="Odchylenie powyżej tego progu jest oznaczane jako anomalia",
    )
    st.session_state.threshold = threshold

    st.markdown("---")
    st.markdown("""
<div style="background:rgba(255,255,255,0.06);border-radius:8px;padding:12px 14px;">
<p style="font-size:11px;font-weight:700;color:#64748B;margin:0 0 8px 0;letter-spacing:1px;">JAK ZACZĄĆ</p>
<p style="font-size:11px;color:#475569;margin:4px 0;">1️⃣ Wgraj plik XLSX</p>
<p style="font-size:11px;color:#475569;margin:4px 0;">2️⃣ Ustaw próg odchylenia</p>
<p style="font-size:11px;color:#475569;margin:4px 0;">3️⃣ Kliknij "Analizuj"</p>
<p style="font-size:11px;color:#475569;margin:4px 0;">4️⃣ Opcjonalnie koryguj ceny</p>
<p style="font-size:11px;color:#475569;margin:4px 0;">5️⃣ Pobierz XLSX / PDF</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    demo_mode = st.checkbox("🎭 Tryb demo", value=False, help="Użyj przykładowych danych bez wgrywania pliku")
    st.session_state.demo_mode = demo_mode

    st.markdown(f"<p style='font-size:10px;color:#94A3B8;text-align:center;margin-top:16px;'>Sesja: {st.session_state.session_id}</p>", unsafe_allow_html=True)


# ─── Helper functions ────────────────────────────────────────────────────────
def kpi_card(icon, value, label, accent="blue"):
    return f"""
<div class="kpi-card kpi-accent-{accent}">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-label">{label}</div>
</div>"""


def render_download_buttons():
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state.xlsx_bytes:
            st.download_button(
                "📥 Pobierz XLSX",
                data=st.session_state.xlsx_bytes,
                file_name=f"anomalie_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )
        else:
            st.button("📥 Pobierz XLSX", disabled=True, use_container_width=True)
    with col2:
        if st.session_state.pdf_bytes:
            st.download_button(
                "📄 Pobierz PDF",
                data=st.session_state.pdf_bytes,
                file_name=f"raport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("📄 Pobierz PDF", disabled=True, use_container_width=True)


def generate_outputs(df_result: pd.DataFrame):
    """Generate XLSX and PDF and store in session state."""
    with st.spinner("Generowanie plików..."):
        st.session_state.xlsx_bytes = generate_xlsx(
            df_result, st.session_state.threshold, st.session_state.file_name
        )
        st.session_state.pdf_bytes = generate_pdf(
            df_result, st.session_state.threshold, st.session_state.file_name
        )


def load_demo_data():
    """Generate synthetic demo data."""
    np.random.seed(42)
    n = 300
    indices = [f"IDX-{i:04d}" for i in range(1, 16)]
    data = {
        "Index materiałowy": np.random.choice(indices, n),
        "Partia": np.random.randint(1000000, 9999999, n),
        "Magazyn": np.random.choice(["Glasshouse", "Główny", "Zapasowy"], n),
        "Przyjęcie [PZ]": [f"PZ {np.random.randint(100,999)}/{np.random.randint(1,12):02d}/2025" for _ in range(n)],
        "Nazwa materiału": [f"Materiał testowy {np.random.randint(1,20)}" for _ in range(n)],
        "Stan mag.": np.random.randint(50, 2000, n).astype(float),
        "Wartość mag.": None,
        "Data przyjęcia": pd.date_range("2025-01-01", periods=n, freq="D").tolist()[:n],
    }
    base_prices = {idx: np.random.uniform(0.5, 50.0) for idx in indices}
    values = []
    for idx, stan in zip(data["Index materiałowy"], data["Stan mag."]):
        bp = base_prices[idx]
        factor = np.random.normal(1.0, 0.05)
        if np.random.random() < 0.08:  # 8% anomalies
            factor = np.random.choice([np.random.uniform(2.5, 5.0), np.random.uniform(0.1, 0.3)])
        values.append(stan * bp * factor)
    data["Wartość mag."] = values
    return pd.DataFrame(data)


# ─── Pages ───────────────────────────────────────────────────────────────────

def page_analiza():
    # Page header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("""
<div class="page-header">
  <h1>🔍 Analiza danych</h1>
  <p>Wgraj plik XLSX z danymi magazynowymi, aby wykryć anomalie cenowe</p>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        render_download_buttons()

    # ── KPI Row ──
    df_result = st.session_state.df_result
    summary = get_anomaly_summary(df_result) if df_result is not None else None

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("📦", summary["n_total"] if summary else "—", "Liczba rekordów", "blue"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("🚨", summary["n_anomalies"] if summary else "—", "Liczba anomalii", "red"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("🗂️", summary["n_idx_anomalies"] if summary else "—", "Indeksy z anomaliami", "orange"), unsafe_allow_html=True)
    with k4:
        val = f"{summary['avg_deviation']:.1f}%" if summary else "—"
        st.markdown(kpi_card("📐", val, "Średnie odchylenie", "purple"), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_card("⚙️", f"{st.session_state.threshold}%", "Próg odchylenia", "green"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    # ── Upload / Info / Status Row ──
    ucol, icol, scol = st.columns(3)

    with ucol:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("<h4>📤 Wgraj plik danych</h4>", unsafe_allow_html=True)
        if st.session_state.demo_mode:
            st.info("Tryb demo jest aktywny. Kliknij 'Analizuj demo', aby załadować przykładowe dane.")
            if st.button("🎭 Analizuj demo", type="primary", use_container_width=True):
                df_raw = load_demo_data()
                st.session_state.df_raw = df_raw
                st.session_state.file_name = "demo_data.xlsx"
                st.session_state.file_info = {
                    "sheet_name": "demo",
                    "header_row": 1,
                    "n_records": len(df_raw),
                    "columns_found": list(df_raw.columns),
                }
                df_result = run_analysis(df_raw, st.session_state.threshold, {})
                st.session_state.df_result = df_result
                summary_data = get_anomaly_summary(df_result)
                aid = save_analysis(
                    "demo_data.xlsx", st.session_state.threshold,
                    summary_data["n_total"], summary_data["n_anomalies"],
                    summary_data["n_idx_anomalies"], "Demo",
                )
                st.session_state.analysis_id = aid
                generate_outputs(df_result)
                st.rerun()
        else:
            uploaded = st.file_uploader(
                "Przeciągnij plik XLSX tutaj",
                type=["xlsx"],
                help="Plik raportu magazynowego (Material stat day stock)",
                label_visibility="collapsed",
            )
            if uploaded:
                if uploaded.name != st.session_state.file_name:
                    try:
                        df_raw, info = parse_file(uploaded)
                        st.session_state.df_raw = df_raw
                        st.session_state.file_name = uploaded.name
                        st.session_state.file_info = info
                        st.session_state.df_result = None
                        st.session_state.manual_prices = {}
                        st.session_state.xlsx_bytes = None
                        st.session_state.pdf_bytes = None
                        st.success(f"✅ Wczytano {info['n_records']} rekordów")
                    except ValueError as e:
                        st.error(f"❌ {e}")

            if st.session_state.df_raw is not None:
                if st.button("🚀 Analizuj dane", type="primary", use_container_width=True):
                    df_result = run_analysis(
                        st.session_state.df_raw,
                        st.session_state.threshold,
                        st.session_state.manual_prices,
                    )
                    st.session_state.df_result = df_result
                    s = get_anomaly_summary(df_result)
                    aid = save_analysis(
                        st.session_state.file_name, st.session_state.threshold,
                        s["n_total"], s["n_anomalies"], s["n_idx_anomalies"], "Auto",
                    )
                    st.session_state.analysis_id = aid
                    generate_outputs(df_result)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with icol:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("<h4>📋 Informacje o pliku</h4>", unsafe_allow_html=True)
        info = st.session_state.file_info
        if info:
            rows = [
                ("Nazwa pliku", st.session_state.file_name or "—"),
                ("Arkusz", info.get("sheet_name", "—")),
                ("Wiersz nagłówka", str(info.get("header_row", "—"))),
                ("Liczba rekordów", str(info.get("n_records", "—"))),
                ("Data analizy", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ]
        else:
            rows = [("Nazwa pliku", "—"), ("Arkusz", "—"), ("Wiersz nagłówka", "—"), ("Liczba rekordów", "—"), ("Data analizy", "—")]
        for k, v in rows:
            st.markdown(f'<div class="info-row"><span class="info-key">{k}</span><span class="info-val">{v}</span></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with scol:
        has_raw = st.session_state.df_raw is not None
        has_result = st.session_state.df_result is not None
        steps = [
            ("Wczytanie pliku", has_raw),
            ("Identyfikacja kolumn", has_raw),
            ("Obliczenie cen", has_result),
            ("Obliczenie median", has_result),
            ("Wykrywanie anomalii", has_result),
        ]
        st.markdown('<div class="status-box">', unsafe_allow_html=True)
        st.markdown("<h4>⚡ Status analizy</h4>", unsafe_allow_html=True)
        for step_name, done in steps:
            icon = '<span class="status-ok">✅</span>' if done else '<span class="status-wait">⭕</span>'
            st.markdown(f'<div class="status-step">{icon} {step_name}</div>', unsafe_allow_html=True)
        if has_result:
            s = get_anomaly_summary(st.session_state.df_result)
            st.markdown(f'<div class="status-success">✅ Analiza zakończona — znaleziono {s["n_anomalies"]} anomalii</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-pending">⏳ Oczekiwanie na plik i analizę</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Anomaly Table ──
    if df_result is not None:
        summary = get_anomaly_summary(df_result)
        st.markdown(f'<div class="anomaly-table-header">🚨 Wykryte anomalie ({summary["n_anomalies"]})</div>', unsafe_allow_html=True)

        # Filter controls
        f1, f2, f3 = st.columns([2, 2, 1])
        with f1:
            search = st.text_input("🔍 Szukaj (indeks, partia, magazyn...)", key="search_anom", placeholder="Wpisz aby filtrować...")
        with f2:
            show_only = st.selectbox("Pokaż:", ["Tylko anomalie", "Wszystkie rekordy", "Tylko normalne"], key="show_filter")
        with f3:
            st.markdown("<br>", unsafe_allow_html=True)
            per_page = st.selectbox("Wierszy:", [25, 50, 100, 200], key="per_page")

        display_df = df_result.copy()

        if show_only == "Tylko anomalie":
            display_df = display_df[display_df["Anomalia"] == True]
        elif show_only == "Tylko normalne":
            display_df = display_df[display_df["Anomalia"] == False]

        if search:
            mask = display_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]

        show_cols = [c for c in [
            "Index materiałowy", "Partia", "Nazwa materiału", "Magazyn",
            "Przyjęcie [PZ]", "Data przyjęcia", "Stan mag.", "Wartość mag.",
            "Cena", "Cena referencyjna", "Odchylenie % do mediany", "Anomalia",
        ] if c in display_df.columns]

        disp = display_df[show_cols].head(per_page).copy()

        # Format for display
        if "Cena" in disp.columns:
            disp["Cena"] = disp["Cena"].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
        if "Cena referencyjna" in disp.columns:
            disp["Cena referencyjna"] = disp["Cena referencyjna"].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
        if "Odchylenie % do mediany" in disp.columns:
            disp["Odchylenie % do mediany"] = disp["Odchylenie % do mediany"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")
        if "Data przyjęcia" in disp.columns:
            disp["Data przyjęcia"] = disp["Data przyjęcia"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "—")
        if "Anomalia" in disp.columns:
            disp["Anomalia"] = disp["Anomalia"].map({True: "🔴 TAK", False: "🟢 NIE"})
        if "Wartość mag." in disp.columns:
            disp["Wartość mag."] = disp["Wartość mag."].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")

        st.dataframe(disp, use_container_width=True, height=420)
        st.caption(f"Pokazano {min(per_page, len(display_df))} z {len(display_df)} rekordów")

        # ── Charts ──
        st.markdown("---")
        st.markdown("### 📊 Wykresy analityczne")
        ch1, ch2 = st.columns(2)
        with ch1:
            fig = make_chart_anomalies_by_month(df_result)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Brak danych do wykresu miesięcznego")
        with ch2:
            fig = make_chart_top_indices_count(df_result)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Brak anomalii do wykresu")

        ch3, ch4 = st.columns(2)
        with ch3:
            fig = make_chart_top_indices_sum_dev(df_result)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Brak anomalii do wykresu")
        with ch4:
            fig = make_chart_deviation_histogram(df_result)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Brak danych do histogramu")


def page_korekta():
    st.markdown("""
<div class="page-header">
  <h1>✏️ Korekta cen referencyjnych</h1>
  <p>Ręcznie ustaw ceny referencyjne dla wybranych indeksów z anomaliami</p>
</div>""", unsafe_allow_html=True)

    if st.session_state.df_result is None:
        st.warning("⚠️ Najpierw przeprowadź analizę w zakładce **Analiza**.")
        return

    df_result = st.session_state.df_result
    anom_idx = get_anomaly_indices(df_result)

    if anom_idx.empty:
        st.success("✅ Brak anomalii — nie ma indeksów do korekty.")
        return

    st.info(
        "💡 **Instrukcja:** Wpisz nową cenę referencyjną dla wybranych indeksów. "
        "Puste pola oznaczają zachowanie mediany. "
        "Po wpisaniu cen kliknij **Przelicz ponownie**.",
        icon=None
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Table header
    hc = st.columns([3, 1.5, 2, 2.5, 2, 1.5])
    labels = ["Index materiałowy", "Anomalie", "Mediana / Ref.", "Nowa cena ref.", "Ostatnio wprowadzona", "Akcja"]
    for col, label in zip(hc, labels):
        col.markdown(f"<p style='font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin:0;padding-bottom:6px;border-bottom:2px solid #E5E7EB;'>{label}</p>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    for _, row in anom_idx.iterrows():
        idx_mat = row["Index materiałowy"]
        n_anom = int(row["Liczba anomalii"])
        median_val = row["Mediana ceny indeksu"]
        last = get_last_price(idx_mat)

        c1, c2, c3, c4, c5, c6 = st.columns([3, 1.5, 2, 2.5, 2, 1.5])

        with c1:
            st.markdown(f"<p style='font-size:13px;font-weight:700;color:#0F172A;margin:8px 0;'>{idx_mat}</p>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<span class='corr-badge'>{n_anom}</span>", unsafe_allow_html=True)
        with c3:
            cur_ref = st.session_state.manual_prices.get(idx_mat)
            if cur_ref:
                st.markdown(f"<p style='font-size:12px;color:#2563EB;font-weight:600;margin:8px 0;'>{cur_ref:.4f} ✏️</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='font-size:12px;color:#6B7280;margin:8px 0;'>{median_val:.4f}</p>", unsafe_allow_html=True)
        with c4:
            new_price = st.number_input(
                f"Nowa cena dla {idx_mat}",
                min_value=0.0,
                value=float(st.session_state.manual_prices.get(idx_mat, 0.0)),
                step=0.001,
                format="%.4f",
                key=f"price_{idx_mat}",
                label_visibility="collapsed",
            )
            if new_price > 0:
                st.session_state.manual_prices[idx_mat] = new_price
            elif idx_mat in st.session_state.manual_prices and new_price == 0:
                pass  # keep previous if typed 0
        with c5:
            if last:
                st.markdown(f"<p style='font-size:11px;color:#6B7280;margin:6px 0;'>{last['price']:.4f}<br><span style='font-size:10px;color:#9CA3AF;'>{last['created_at']}</span></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size:11px;color:#D1D5DB;margin:8px 0;'>—</p>", unsafe_allow_html=True)
        with c6:
            if last:
                if st.button("↩️ Użyj", key=f"use_last_{idx_mat}", help="Użyj ostatnio wprowadzonej ceny"):
                    st.session_state.manual_prices[idx_mat] = last["price"]
                    st.rerun()
            else:
                st.button("↩️ Użyj", key=f"use_last_{idx_mat}", disabled=True)

        st.markdown("<hr style='margin:4px 0;border-color:#F3F4F6;'>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([2, 2, 3])
    with b1:
        if st.button("🔄 Przelicz ponownie", type="primary", use_container_width=True, key="recalc_btn"):
            # Save manual prices to DB
            for idx_mat, price in st.session_state.manual_prices.items():
                if price and price > 0:
                    save_price(idx_mat, price, st.session_state.session_id, st.session_state.analysis_id)

            df_result_new = run_analysis(
                st.session_state.df_raw,
                st.session_state.threshold,
                st.session_state.manual_prices,
            )
            st.session_state.df_result = df_result_new
            s = get_anomaly_summary(df_result_new)
            aid = save_analysis(
                st.session_state.file_name, st.session_state.threshold,
                s["n_total"], s["n_anomalies"], s["n_idx_anomalies"], "Ręczna",
            )
            st.session_state.analysis_id = aid
            generate_outputs(df_result_new)
            st.success(f"✅ Przeliczono ponownie. Wykryto {s['n_anomalies']} anomalii.")
            st.rerun()
    with b2:
        if st.button("✅ Zakończ i pobierz", use_container_width=True, key="finish_btn"):
            generate_outputs(st.session_state.df_result)
            st.success("✅ Pliki gotowe do pobrania — wróć do zakładki Analiza.")
            st.session_state.active_tab = "Analiza"
            st.rerun()


def page_podsumowanie():
    st.markdown("""
<div class="page-header">
  <h1>📈 Podsumowanie analizy</h1>
  <p>Przegląd wyników i wizualizacje</p>
</div>""", unsafe_allow_html=True)

    if st.session_state.df_result is None:
        st.warning("⚠️ Najpierw przeprowadź analizę w zakładce **Analiza**.")
        return

    df_result = st.session_state.df_result
    summary = get_anomaly_summary(df_result)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("📦", summary["n_total"], "Liczba rekordów", "blue"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("🚨", summary["n_anomalies"], "Liczba anomalii", "red"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("🗂️", summary["n_idx_anomalies"], "Indeksy z anomaliami", "orange"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("📊", f"{summary['anomaly_rate']}%", "Udział anomalii", "purple"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        fig = make_chart_anomalies_by_month(df_result)
        if fig:
            st.pyplot(fig)
    with c2:
        fig = make_chart_top_indices_count(df_result)
        if fig:
            st.pyplot(fig)

    c3, c4 = st.columns(2)
    with c3:
        fig = make_chart_top_indices_sum_dev(df_result)
        if fig:
            st.pyplot(fig)
    with c4:
        fig = make_chart_deviation_histogram(df_result)
        if fig:
            st.pyplot(fig)

    # Pareto
    fig = make_chart_pareto(df_result)
    if fig:
        st.pyplot(fig)

    # Per-index summary table
    st.markdown("### 📋 Podsumowanie per indeks")
    anom_idx = get_anomaly_indices(df_result)
    if not anom_idx.empty:
        st.dataframe(anom_idx, use_container_width=True)

    # Download buttons
    st.markdown("---")
    render_download_buttons()


def page_historia_analiz():
    st.markdown("""
<div class="page-header">
  <h1>📋 Historia analiz</h1>
  <p>Rejestr przeprowadzonych analiz w tej sesji</p>
</div>""", unsafe_allow_html=True)

    df = get_analysis_history()
    if df.empty:
        st.info("📭 Brak historii analiz. Przeprowadź pierwszą analizę.")
        return

    # Filter
    f1, f2 = st.columns(2)
    with f1:
        search = st.text_input("🔍 Filtruj po nazwie pliku", key="hist_search", placeholder="...")
    with f2:
        typ = st.selectbox("Typ analizy", ["Wszystkie"] + df["Typ"].unique().tolist(), key="hist_type")

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["Plik"].str.contains(search, case=False, na=False)]
    if typ != "Wszystkie":
        filtered = filtered[filtered["Typ"] == typ]

    st.dataframe(filtered, use_container_width=True, height=450)
    st.caption(f"Łącznie: {len(filtered)} rekordów")


def page_historia_cen():
    st.markdown("""
<div class="page-header">
  <h1>💰 Historia cen ręcznych</h1>
  <p>Rejestr ręcznie wprowadzonych cen referencyjnych</p>
</div>""", unsafe_allow_html=True)

    df = get_price_history()
    if df.empty:
        st.info("📭 Brak historii cen. Wprowadź ceny ręczne w zakładce Korekta cen.")
        return

    f1 = st.text_input("🔍 Filtruj po indeksie materiałowym", key="price_hist_search", placeholder="...")
    filtered = df.copy()
    if f1:
        filtered = filtered[filtered["Index materiałowy"].str.contains(f1, case=False, na=False)]

    st.dataframe(filtered, use_container_width=True, height=450)
    st.caption(f"Łącznie: {len(filtered)} rekordów")


def page_ustawienia():
    st.markdown("""
<div class="page-header">
  <h1>⚙️ Ustawienia</h1>
  <p>Konfiguracja aplikacji</p>
</div>""", unsafe_allow_html=True)

    st.markdown("### 🔧 Parametry analizy")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input(
            "Próg odchylenia (%)",
            min_value=1, max_value=500,
            value=st.session_state.threshold,
            key="settings_threshold",
            help="Rekordy z odchyleniem >= tego progu są oznaczane jako anomalie",
        )
    with c2:
        st.markdown(f"""
<div class="info-box">
  <h4>ℹ️ Aktualne ustawienia</h4>
  <div class="info-row"><span class="info-key">Próg odchylenia</span><span class="info-val">{st.session_state.threshold}%</span></div>
  <div class="info-row"><span class="info-key">ID sesji</span><span class="info-val">{st.session_state.session_id}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗑️ Zarządzanie danymi sesji")
    if st.button("🔄 Wyczyść dane sesji", type="secondary"):
        for key in ["df_raw", "df_result", "file_info", "file_name", "manual_prices",
                    "analysis_id", "xlsx_bytes", "pdf_bytes"]:
            if key in st.session_state:
                del st.session_state[key]
                st.session_state[key] = None if key != "manual_prices" else {}
                if key == "file_name":
                    st.session_state[key] = ""
        st.success("✅ Dane sesji wyczyszczone.")
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ O aplikacji")
    st.markdown("""
**Anomalia Cenowa** — narzędzie do wykrywania anomalii cenowych w danych magazynowych.

**Wersja:** 1.0.0  
**Technologie:** Python, Streamlit, pandas, openpyxl, reportlab, SQLite  

**Logika biznesowa:**
- `Cena = Wartość mag. / Stan mag.`
- `Odchylenie % = |Cena - Cena referencyjna| / Cena referencyjna × 100`
- Anomalia = Odchylenie ≥ Próg odchylenia
    """)


# ─── Router ──────────────────────────────────────────────────────────────────
tab = st.session_state.active_tab

if tab == "Analiza":
    page_analiza()
elif tab == "Korekta cen":
    page_korekta()
elif tab == "Podsumowanie":
    page_podsumowanie()
elif tab == "Historia analiz":
    page_historia_analiz()
elif tab == "Historia cen ręcznych":
    page_historia_cen()
elif tab == "Ustawienia":
    page_ustawienia()
