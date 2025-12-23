"""
CSV Utilities for Safe Data Cleaning in Sandbox
-------------------------------------------------
Provides helpers to read, infer schema, and clean CSV data within the sandbox.
All functions are pure and avoid network/external calls.

Memory optimizations:
- Use chunked reading for large files
- Check file size before loading
- Limit sample size for schema inference
"""
from __future__ import annotations

import csv
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Generator

import pandas as pd


logger = logging.getLogger(__name__)

# File size threshold for warning (50MB for CSV)
LARGE_CSV_THRESHOLD = 50 * 1024 * 1024
MAX_SAMPLE_ROWS = 1000  # Increased slightly for better schema detection


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    null_count: int
    unique_count: int
    sample_values: List[Any]


@dataclass
class CSVInfo:
    path: str
    rows: int
    columns: int
    column_info: List[ColumnInfo]
    encoding: str


def _check_csv_size(path: str) -> bool:
    """Check CSV file size and warn if large. Returns True if safe to proceed."""
    try:
        size = os.path.getsize(path)
        if size > LARGE_CSV_THRESHOLD:
            logger.warning(
                "Large CSV file detected: %s (%.2f MB). Consider chunked processing.",
                path, size / (1024 * 1024)
            )
        return size <= LARGE_CSV_THRESHOLD * 5  # Allow up to 5x with warning
    except OSError as e:
        logger.warning("Could not check CSV size for %s: %s", path, e)
        return True


def _read_csv_chunks(path: str, encoding: str, chunksize: int = 10000) -> Generator[pd.DataFrame, None, None]:
    """Read CSV in chunks to reduce memory usage."""
    for chunk in pd.read_csv(path, encoding=encoding, chunksize=chunksize):
        yield chunk


def sniff_csv(path: str, sample_rows: int = MAX_SAMPLE_ROWS) -> CSVInfo:
    """
    Read a sample of a CSV and infer schema.

    Memory optimized:
    - Limits sample size
    - Warns on large files
    - Uses efficient pandas dtypes
    """
    # Check file size before processing
    _check_csv_size(path)

    # Auto-detect encoding and delimiter
    sample_size = min(sample_rows * 200, 100000)  # Cap at 100KB for sniffing
    with open(path, "rb") as f:
        raw = f.read(sample_size)
    try:
        encoding = "utf-8"
        raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"

    with open(path, "r", encoding=encoding, newline="") as f:
        sample = f.read(sample_size)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            # Fallback to default if sniffing fails
            dialect = csv.get_dialect("excel")

    # Read with pandas for robust dtype inference
    # Use efficient dtypes to reduce memory
    df = pd.read_csv(
        path,
        nrows=sample_rows,
        dialect=dialect,
        encoding=encoding,
        dtype_backend="pyarrow"  # Use efficient pyarrow backend if available
    )

    column_info = []
    for col in df.columns:
        series = df[col]
        dtype = str(series.dtype)
        null_count = series.isnull().sum()
        unique_count = series.nunique()
        sample_vals = series.dropna().head(3).tolist()
        column_info.append(ColumnInfo(name=col, dtype=dtype, null_count=int(null_count), unique_count=int(unique_count), sample_values=sample_vals))

    return CSVInfo(
        path=path,
        rows=len(df),
        columns=len(df.columns),
        column_info=column_info,
        encoding=encoding
    )


def suggest_cleaning_steps(info: CSVInfo) -> List[Dict[str, Any]]:
    """Generate a list of suggested cleaning steps based on schema."""
    steps = []
    for col in info.column_info:
        # High null ratio
        if col.null_count > 0 and info.rows > 0:
            null_ratio = col.null_count / info.rows
            if null_ratio > 0.5:
                steps.append({"type": "drop_column", "column": col.name, "reason": f"{null_ratio:.0%} nulls"})
            elif null_ratio > 0.05:
                steps.append({"type": "fill_nulls", "column": col.name, "method": "forward_fill"})
        # Numeric columns with outliers
        if col.dtype.startswith("int") or col.dtype.startswith("float"):
            steps.append({"type": "validate_numeric", "column": col.name})
        # String columns: normalize case and whitespace
        if col.dtype == "object":
            steps.append({"type": "normalize_strings", "column": col.name})
    return steps


def clean_csv(info: CSVInfo, steps: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """Apply cleaning steps and write a cleaned CSV."""
    df = pd.read_csv(info.path, encoding=info.encoding)
    original_rows = len(df)
    for step in steps:
        typ = step.get("type")
        col = step.get("column")
        if typ == "drop_column" and col in df.columns:
            df = df.drop(columns=[col])
        elif typ == "fill_nulls" and col in df.columns:
            method = step.get("method", "forward_fill")
            if method == "forward_fill":
                df[col] = df[col].ffill()
            elif method == "mean":
                if df[col].dtype in ("int64", "float64"):
                    df[col] = df[col].fillna(df[col].mean())
            elif method == "mode":
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df[col] = df[col].fillna(mode_val.iloc[0])
        elif typ == "validate_numeric" and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif typ == "normalize_strings" and col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    # Write cleaned CSV
    df.to_csv(output_path, index=False, encoding="utf-8")
    return {
        "original_rows": original_rows,
        "cleaned_rows": len(df),
        "output_path": output_path,
        "steps_applied": steps
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python csv_utils.py <path_to_csv>")
        sys.exit(1)
    path = sys.argv[1]
    info = sniff_csv(path)
    print(json.dumps(info.__dict__, default=str, indent=2))
    steps = suggest_cleaning_steps(info)
    print("Suggested steps:", json.dumps(steps, indent=2))
