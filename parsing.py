"""Parsing and loading of XLSX warehouse data files."""

import io
import pandas as pd
import numpy as np
from typing import Optional


REQUIRED_COLS = {
    "Index materiałowy": ["index materiałowy", "index mat", "indeks materiałowy"],
    "Partia": ["partia", "batch", "lot"],
    "Magazyn": ["magazyn", "warehouse", "mag"],
    "Przyjęcie [PZ]": ["przyjęcie [pz]", "przyjęcie pz", "pz", "przyjęcie"],
    "Nazwa materiału": ["nazwa materiału", "nazwa mat", "nazwa", "material name"],
    "Stan mag.": ["stan mag.", "stan mag", "stan magazynowy", "stan"],
    "Wartość mag.": ["wartość mag.", "wartość mag", "wartość magazynowa", "wartość"],
    "Data przyjęcia": ["data przyjęcia", "data", "date"],
}

OPTIONAL_COLS = {
    "Kod kreskowy": ["kod kreskowy"],
    "Kod dostawcy": ["kod dostawcy"],
    "Typ surowca": ["typ surowca"],
    "jm.1": ["jm.1", "jm"],
}


def _normalize(name: str) -> str:
    return str(name).strip().lower()


def detect_header_row(df_raw: pd.DataFrame) -> int:
    """Find the row index that contains required column names."""
    required_normalized = [_normalize(v[0]) for v in REQUIRED_COLS.values()]
    for i, row in df_raw.iterrows():
        row_values = [_normalize(str(v)) for v in row.values if pd.notna(v)]
        matches = sum(1 for req in required_normalized if any(req in rv or rv in req for rv in row_values))
        if matches >= 4:
            return int(i)
    return 3  # default fallback


def detect_sheet(xl: pd.ExcelFile) -> str:
    """Return the best sheet name to use."""
    preferred = ["myprint", "data", "dane", "sheet1", "arkusz1"]
    for sheet in xl.sheet_names:
        if sheet.lower() in preferred:
            return sheet
    return xl.sheet_names[0]


def map_columns(df: pd.DataFrame) -> dict:
    """Map DataFrame columns to canonical names. Returns dict canonical->actual."""
    mapping = {}
    df_cols_norm = {_normalize(c): c for c in df.columns}

    for canonical, aliases in REQUIRED_COLS.items():
        for alias in aliases:
            if alias in df_cols_norm:
                mapping[canonical] = df_cols_norm[alias]
                break
        # direct match
        if canonical not in mapping:
            for col in df.columns:
                if _normalize(col) == _normalize(canonical):
                    mapping[canonical] = col
                    break

    for canonical, aliases in OPTIONAL_COLS.items():
        for alias in aliases:
            if alias in df_cols_norm:
                mapping[canonical] = df_cols_norm[alias]
                break

    return mapping


def parse_file(file_obj) -> tuple[pd.DataFrame, dict]:
    """
    Parse an uploaded XLSX file.
    Returns (DataFrame with canonical column names, info_dict).
    Raises ValueError with user-friendly message on failure.
    """
    try:
        if hasattr(file_obj, "read"):
            data = file_obj.read()
            file_obj.seek(0)
        else:
            data = file_obj

        xl = pd.ExcelFile(io.BytesIO(data) if isinstance(data, bytes) else data)
        sheet_name = detect_sheet(xl)

        # Read raw to detect header row
        df_raw = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, header=None)
        header_row = detect_header_row(df_raw)

        df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]

        col_map = map_columns(df)
        missing = [c for c in REQUIRED_COLS if c not in col_map]
        if missing:
            raise ValueError(f"Brakujące kolumny: {', '.join(missing)}")

        # Rename to canonical names
        reverse_map = {v: k for k, v in col_map.items()}
        df = df.rename(columns=reverse_map)

        # Keep only known columns plus any extra
        keep_cols = list(REQUIRED_COLS.keys()) + [c for c in OPTIONAL_COLS if c in df.columns]
        extra_cols = [c for c in df.columns if c not in keep_cols]
        df = df[keep_cols + extra_cols]

        # Clean numeric columns
        for col in ["Stan mag.", "Wartość mag."]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clean date
        df["Data przyjęcia"] = pd.to_datetime(df["Data przyjęcia"], errors="coerce")

        # Drop rows where both Stan mag. and Wartość mag. are null
        df = df.dropna(subset=["Stan mag.", "Wartość mag."], how="all")

        # Replace zero Stan mag. to avoid division by zero
        df = df[df["Stan mag."].notna() & (df["Stan mag."] != 0)]

        df = df.reset_index(drop=True)

        info = {
            "sheet_name": sheet_name,
            "header_row": header_row + 1,
            "n_records": len(df),
            "columns_found": list(col_map.keys()),
        }

        return df, info

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Błąd odczytu pliku: {e}")
