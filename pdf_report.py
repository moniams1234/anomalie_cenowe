"""PDF report generation using reportlab."""

import io
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Color palette
NAVY = colors.HexColor("#1E3A5F")
BLUE = colors.HexColor("#2563EB")
RED = colors.HexColor("#DC2626")
GREEN = colors.HexColor("#16A34A")
LIGHT_GRAY = colors.HexColor("#F8F9FA")
MID_GRAY = colors.HexColor("#E5E7EB")
DARK_GRAY = colors.HexColor("#374151")


def _make_chart_anomalies_by_month(df: pd.DataFrame) -> io.BytesIO:
    anomalies = df[df["Anomalia"] == True].copy()
    if anomalies.empty or "Data przyjęcia" not in anomalies.columns:
        return None
    anomalies["Miesiąc"] = anomalies["Data przyjęcia"].dt.to_period("M").astype(str)
    counts = anomalies.groupby("Miesiąc").size().reset_index(name="Liczba")
    counts = counts.sort_values("Miesiąc")

    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.bar(counts["Miesiąc"], counts["Liczba"], color="#2563EB", alpha=0.85, width=0.6)
    ax.set_title("Anomalie wg miesiąca przyjęcia", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Miesiąc", fontsize=9)
    ax.set_ylabel("Liczba anomalii", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_chart_top_indices(df: pd.DataFrame) -> io.BytesIO:
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return None
    top = anomalies.groupby("Index materiałowy").size().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    y_pos = range(len(top))
    ax.barh(list(y_pos), top.values, color="#2563EB", alpha=0.85)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(top.index.tolist(), fontsize=8)
    ax.set_title("Top 10 indeksów — liczba anomalii", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Liczba anomalii", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(top.values):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_chart_deviation_histogram(df: pd.DataFrame) -> io.BytesIO:
    devs = df[df["Anomalia"] == True]["Odchylenie % do mediany"].dropna()
    if devs.empty:
        return None

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.hist(devs, bins=20, color="#DC2626", alpha=0.7, edgecolor="white")
    ax.set_title("Rozkład odchyleń % (anomalie)", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("Odchylenie %", fontsize=9)
    ax.set_ylabel("Liczba rekordów", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _make_chart_pareto(df: pd.DataFrame) -> io.BytesIO:
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return None
    counts = anomalies.groupby("Index materiałowy").size().sort_values(ascending=False).head(15)
    cumulative = counts.cumsum() / counts.sum() * 100

    fig, ax1 = plt.subplots(figsize=(7, 3.5))
    ax2 = ax1.twinx()
    ax1.bar(range(len(counts)), counts.values, color="#2563EB", alpha=0.7, width=0.6)
    ax2.plot(range(len(counts)), cumulative.values, color="#DC2626", marker="o", markersize=4, linewidth=1.5)
    ax2.axhline(80, color="#F59E0B", linestyle="--", alpha=0.7, linewidth=1)
    ax1.set_xticks(range(len(counts)))
    ax1.set_xticklabels(counts.index.tolist(), rotation=45, ha="right", fontsize=7)
    ax1.set_ylabel("Liczba anomalii", fontsize=9)
    ax2.set_ylabel("Skumulowany udział %", fontsize=9)
    ax1.set_title("Wykres Pareto — udział indeksów w anomaliach", fontsize=11, fontweight="bold", pad=10)
    ax1.spines["top"].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf(
    df: pd.DataFrame,
    threshold_pct: float,
    file_name: str = "analiza",
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("Title2", parent=styles["Title"],
                                 fontSize=20, textColor=NAVY, spaceAfter=4)
    style_h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                               fontSize=13, textColor=NAVY, spaceAfter=4, spaceBefore=12)
    style_h3 = ParagraphStyle("H3", parent=styles["Heading3"],
                               fontSize=11, textColor=DARK_GRAY, spaceAfter=4, spaceBefore=8)
    style_body = ParagraphStyle("Body2", parent=styles["Normal"],
                                fontSize=9, textColor=DARK_GRAY, spaceAfter=3)
    style_caption = ParagraphStyle("Caption", parent=styles["Normal"],
                                   fontSize=8, textColor=colors.gray, spaceAfter=2)

    anomalies = df[df["Anomalia"] == True]
    n_total = len(df)
    n_anom = len(anomalies)
    n_idx = anomalies["Index materiałowy"].nunique() if not anomalies.empty else 0
    avg_dev = anomalies["Odchylenie % do mediany"].mean() if not anomalies.empty else 0.0

    story = []

    # Title
    story.append(Paragraph("Raport Anomalii Cenowych", style_title))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))
    story.append(Paragraph(f"Plik: <b>{file_name}</b>", style_body))
    story.append(Paragraph(f"Data wygenerowania: <b>{datetime.now().strftime('%Y-%m-%d %H:%M')}</b>", style_body))
    story.append(Paragraph(f"Próg odchylenia: <b>{threshold_pct}%</b>", style_body))
    story.append(Spacer(1, 0.5 * cm))

    # KPI table
    story.append(Paragraph("Podsumowanie", style_h2))
    kpi_data = [
        ["Parametr", "Wartość"],
        ["Liczba rekordów", str(n_total)],
        ["Liczba anomalii", str(n_anom)],
        ["Indeksy z anomaliami", str(n_idx)],
        ["Udział anomalii", f"{n_anom/n_total*100:.1f}%" if n_total > 0 else "0%"],
        ["Średnie odchylenie (anomalie)", f"{avg_dev:.2f}%" if not np.isnan(avg_dev) else "—"],
        ["Zastosowany próg", f"{threshold_pct}%"],
    ]
    t = Table(kpi_data, colWidths=[9 * cm, 7 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWHEIGHT", (0, 0), (-1, -1), 16),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # Charts
    story.append(Paragraph("Wykresy analityczne", style_h2))

    chart1 = _make_chart_anomalies_by_month(df)
    if chart1:
        story.append(Paragraph("Anomalie wg miesiąca przyjęcia", style_h3))
        story.append(Image(chart1, width=16 * cm, height=7 * cm))
        story.append(Spacer(1, 0.3 * cm))

    chart2 = _make_chart_top_indices(df)
    if chart2:
        story.append(Paragraph("Top 10 indeksów — liczba anomalii", style_h3))
        story.append(Image(chart2, width=16 * cm, height=7.5 * cm))
        story.append(Spacer(1, 0.3 * cm))

    chart3 = _make_chart_deviation_histogram(df)
    if chart3:
        story.append(Paragraph("Rozkład odchyleń procentowych", style_h3))
        story.append(Image(chart3, width=16 * cm, height=7 * cm))
        story.append(Spacer(1, 0.3 * cm))

    chart4 = _make_chart_pareto(df)
    if chart4:
        story.append(PageBreak())
        story.append(Paragraph("Wykres Pareto", style_h3))
        story.append(Image(chart4, width=16 * cm, height=7.5 * cm))
        story.append(Spacer(1, 0.3 * cm))

    # Anomalies by index table
    if not anomalies.empty:
        story.append(PageBreak())
        story.append(Paragraph("Anomalie wg indeksów", style_h2))
        idx_summary = (
            anomalies.groupby("Index materiałowy")
            .agg(
                Liczba=("Anomalia", "sum"),
                Suma_odch=("Odchylenie % do mediany", "sum"),
                Avg_odch=("Odchylenie % do mediany", "mean"),
            )
            .reset_index()
            .sort_values("Liczba", ascending=False)
        )
        tdata = [["Index materiałowy", "Anomalie", "Suma odch. %", "Śr. odch. %"]]
        for _, r in idx_summary.iterrows():
            tdata.append([
                str(r["Index materiałowy"]),
                str(int(r["Liczba"])),
                f"{r['Suma_odch']:.2f}",
                f"{r['Avg_odch']:.2f}",
            ])
        t2 = Table(tdata, colWidths=[8 * cm, 3 * cm, 3 * cm, 3 * cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWHEIGHT", (0, 0), (-1, -1), 14),
        ]))
        story.append(t2)

        # Anomalies by month
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Anomalie wg miesiąca", style_h2))
        if "Data przyjęcia" in anomalies.columns:
            anom_copy = anomalies.copy()
            anom_copy["Miesiąc"] = anom_copy["Data przyjęcia"].dt.to_period("M").astype(str)
            monthly = anom_copy.groupby("Miesiąc").size().reset_index(name="Liczba anomalii")
            mdata = [["Miesiąc", "Liczba anomalii"]] + monthly.values.tolist()
            tm = Table(mdata, colWidths=[8 * cm, 8 * cm])
            tm.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWHEIGHT", (0, 0), (-1, -1), 14),
            ]))
            story.append(tm)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
