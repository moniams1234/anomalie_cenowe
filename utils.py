"""Utility functions."""

import uuid
import pandas as pd
import numpy as np
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


def generate_session_id() -> str:
    return str(uuid.uuid4())[:8]


def format_number(val, decimals=2) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "—"
    return f"{val:,.{decimals}f}".replace(",", " ").replace(".", ",")


def safe_float(val) -> float | None:
    try:
        v = float(str(val).replace(",", ".").replace(" ", ""))
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except (ValueError, TypeError):
        return None


def make_chart_anomalies_by_month(df: pd.DataFrame):
    """Return matplotlib figure for anomalies by month."""
    anomalies = df[df["Anomalia"] == True].copy()
    if anomalies.empty or "Data przyjęcia" not in anomalies.columns:
        return None
    anomalies["Miesiąc"] = anomalies["Data przyjęcia"].dt.to_period("M").astype(str)
    counts = anomalies.groupby("Miesiąc").size().reset_index(name="Liczba")
    counts = counts.sort_values("Miesiąc")

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(counts["Miesiąc"], counts["Liczba"], color="#2563EB", alpha=0.85, width=0.6)
    ax.set_title("Anomalie wg miesiąca przyjęcia", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Miesiąc", fontsize=10)
    ax.set_ylabel("Liczba anomalii", fontsize=10)
    ax.tick_params(axis="x", rotation=45)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def make_chart_top_indices_count(df: pd.DataFrame):
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return None
    top = anomalies.groupby("Index materiałowy").size().sort_values(ascending=True).tail(10)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors_list = ["#2563EB"] * len(top)
    ax.barh(top.index.tolist(), top.values, color=colors_list, alpha=0.85)
    ax.set_title("Top 10 indeksów — liczba anomalii", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Liczba anomalii", fontsize=10)
    for i, v in enumerate(top.values):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def make_chart_top_indices_sum_dev(df: pd.DataFrame):
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return None
    top = (anomalies.groupby("Index materiałowy")["Odchylenie % do mediany"]
           .sum().sort_values(ascending=True).tail(10))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(top.index.tolist(), top.values, color="#DC2626", alpha=0.75)
    ax.set_title("Top 10 indeksów — suma odchyleń %", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Suma odchyleń %", fontsize=10)
    for i, v in enumerate(top.values):
        ax.text(v + 0.5, i, f"{v:.1f}", va="center", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def make_chart_deviation_histogram(df: pd.DataFrame):
    devs = df["Odchylenie % do mediany"].dropna()
    if devs.empty:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(devs, bins=30, color="#6366F1", alpha=0.75, edgecolor="white")
    ax.set_title("Rozkład odchyleń % (wszystkie rekordy)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Odchylenie %", fontsize=10)
    ax.set_ylabel("Liczba rekordów", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def make_chart_pareto(df: pd.DataFrame):
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return None
    counts = anomalies.groupby("Index materiałowy").size().sort_values(ascending=False).head(15)
    cumulative = counts.cumsum() / counts.sum() * 100
    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax2 = ax1.twinx()
    ax1.bar(range(len(counts)), counts.values, color="#2563EB", alpha=0.7, width=0.65, label="Liczba anomalii")
    ax2.plot(range(len(counts)), cumulative.values, color="#DC2626", marker="o", ms=5, lw=2, label="Skumul. %")
    ax2.axhline(80, color="#F59E0B", ls="--", alpha=0.7, lw=1.5, label="80%")
    ax1.set_xticks(range(len(counts)))
    ax1.set_xticklabels(counts.index.tolist(), rotation=45, ha="right", fontsize=7)
    ax1.set_ylabel("Liczba anomalii", fontsize=10)
    ax2.set_ylabel("Skumulowany udział %", fontsize=10)
    ax1.set_title("Wykres Pareto — udział indeksów w anomaliach", fontsize=12, fontweight="bold", pad=12)
    ax1.spines["top"].set_visible(False)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=8)
    fig.tight_layout()
    return fig


def df_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Simple DataFrame to xlsx bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()
