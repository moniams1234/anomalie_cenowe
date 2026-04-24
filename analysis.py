"""Anomaly detection logic for price analysis."""

import pandas as pd
import numpy as np
from typing import Optional


def compute_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Add Cena column: Wartość mag. / Stan mag."""
    df = df.copy()
    df["Cena"] = df["Wartość mag."] / df["Stan mag."]
    return df


def compute_medians(df: pd.DataFrame) -> pd.DataFrame:
    """Add Mediana ceny indeksu column per Index materiałowy."""
    medians = df.groupby("Index materiałowy")["Cena"].transform("median")
    df["Mediana ceny indeksu"] = medians
    return df


def compute_deviations(
    df: pd.DataFrame,
    threshold_pct: float = 20.0,
    manual_prices: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Add Cena referencyjna, Źródło ceny referencyjnej, Odchylenie % do mediany, Anomalia.
    manual_prices: dict {index_mat -> price} for manual overrides.
    """
    df = df.copy()
    if manual_prices is None:
        manual_prices = {}

    ref_prices = []
    ref_sources = []

    for idx_mat, cena_median in zip(df["Index materiałowy"], df["Mediana ceny indeksu"]):
        if idx_mat in manual_prices and manual_prices[idx_mat] is not None:
            val = manual_prices[idx_mat]
            try:
                val = float(val)
                ref_prices.append(val)
                ref_sources.append("Ręczna")
            except (ValueError, TypeError):
                ref_prices.append(cena_median)
                ref_sources.append("Mediana")
        else:
            ref_prices.append(cena_median)
            ref_sources.append("Mediana")

    df["Cena referencyjna"] = ref_prices
    df["Źródło ceny referencyjnej"] = ref_sources

    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        dev = np.where(
            (df["Cena referencyjna"].notna()) & (df["Cena referencyjna"] != 0),
            np.abs(df["Cena"] - df["Cena referencyjna"]) / df["Cena referencyjna"] * 100,
            np.nan,
        )
    df["Odchylenie % do mediany"] = dev
    df["Anomalia"] = df["Odchylenie % do mediany"] >= threshold_pct

    return df


def run_analysis(
    df: pd.DataFrame,
    threshold_pct: float = 20.0,
    manual_prices: Optional[dict] = None,
) -> pd.DataFrame:
    """Full analysis pipeline."""
    df = compute_prices(df)
    df = compute_medians(df)
    df = compute_deviations(df, threshold_pct, manual_prices)
    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
    """Return summary statistics."""
    n_total = len(df)
    anomalies = df[df["Anomalia"] == True]
    n_anomalies = len(anomalies)
    n_idx_anomalies = anomalies["Index materiałowy"].nunique() if n_anomalies > 0 else 0
    avg_dev = anomalies["Odchylenie % do mediany"].mean() if n_anomalies > 0 else 0.0

    return {
        "n_total": n_total,
        "n_anomalies": n_anomalies,
        "n_idx_anomalies": n_idx_anomalies,
        "avg_deviation": round(avg_dev, 2) if not np.isnan(avg_dev) else 0.0,
        "anomaly_rate": round(n_anomalies / n_total * 100, 1) if n_total > 0 else 0.0,
    }


def get_anomaly_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-index summary for anomalous indices."""
    anomalies = df[df["Anomalia"] == True]
    if anomalies.empty:
        return pd.DataFrame(columns=["Index materiałowy", "Liczba anomalii", "Mediana ceny indeksu"])

    summary = (
        anomalies.groupby("Index materiałowy")
        .agg(
            Liczba_anomalii=("Anomalia", "sum"),
            Mediana=("Mediana ceny indeksu", "first"),
            Suma_odchylen=("Odchylenie % do mediany", "sum"),
        )
        .reset_index()
        .rename(columns={
            "Liczba_anomalii": "Liczba anomalii",
            "Mediana": "Mediana ceny indeksu",
            "Suma_odchylen": "Suma odchyleń %",
        })
        .sort_values("Liczba anomalii", ascending=False)
    )
    return summary
