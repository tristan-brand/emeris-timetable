from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    import tabula  # tabula-py
except ImportError as e:
    raise SystemExit(
        "tabula-py is not installed. Run: poetry install (or pip install tabula-py)."
    ) from e


def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempt to convert object columns to numbers where possible.
    Handles commas and currency-ish noise lightly.
    """
    out = df.copy()

    def clean_cell(x):
        if not isinstance(x, str):
            return x
        s = x.strip()
        # remove common thousands separators
        s = s.replace(",", "")
        # remove currency symbols (light touch)
        s = re.sub(r"[R$£€]", "", s)
        return s.strip()

    for col in out.columns:
        # Clean strings first
        out[col] = out[col].map(clean_cell)

        # Try numeric conversion (non-numeric stays as-is)
        converted = pd.to_numeric(out[col], errors="ignore")
        out[col] = converted

    return out


def extract_tables(
    pdf_path: Path,
    pages: str = "all",
    guess: bool = True,
    lattice: bool | None = None,
) -> list[pd.DataFrame]:
    """
    Extract tables from a PDF using tabula-py.

    Requires Java installed.

    Args:
        pages: "all" or "1" or "1-3" etc.
        guess: Let Tabula guess table areas.
        lattice: If True, Tabula tries ruling lines; if False, stream mode;
                 if None, let Tabula choose defaults.

    Returns:
        List of DataFrames (one per table).
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    read_kwargs = dict(
        pages=pages,
        multiple_tables=True,
        guess=guess,
    )
    if lattice is not None:
        read_kwargs["lattice"] = lattice

    dfs = tabula.read_pdf(str(pdf_path), **read_kwargs)
    # tabula can return None entries sometimes
    dfs = [df for df in dfs if df is not None and not df.empty]
    return dfs


def normalize_tables(dfs: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """
    Normalize and merge extracted tables into one dataframe.
    - strips whitespace from headers/cells
    - removes fully empty rows
    - attempts numeric conversion
    """
    cleaned: list[pd.DataFrame] = []

    for df in dfs:
        df2 = df.copy()

        # Normalize column names
        df2.columns = [str(c).strip() for c in df2.columns]

        # Strip string cells
        df2 = df2.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Drop completely empty rows
        df2 = df2.dropna(how="all")

        df2 = _coerce_numeric(df2)
        cleaned.append(df2)

    if not cleaned:
        return pd.DataFrame()

    # Outer concat to keep all columns even if tables differ slightly
    merged = pd.concat(cleaned, ignore_index=True, sort=False)
    return merged


def filter_rows_contains(df: pd.DataFrame, column: str, needle: str) -> pd.DataFrame:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found. Columns: {list(df.columns)}")
    mask = df[column].astype(str).str.contains(needle, case=False, na=False)
    return df.loc[mask].copy()


def sum_column(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found. Columns: {list(df.columns)}")

    series = pd.to_numeric(df[column], errors="coerce")
    return float(series.fillna(0).sum())


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf-sheet",
        description="Extract spreadsheet-like tables from a PDF and run simple actions.",
    )
    p.add_argument("pdf", type=Path, help="Path to the PDF file")
    p.add_argument("--pages", default="all", help='Tabula pages, e.g. "all" or "1-3"')
    p.add_argument(
        "--mode",
        choices=["auto", "lattice", "stream"],
        default="auto",
        help="Table extraction mode (Tabula).",
    )
    p.add_argument(
        "--no-guess",
        action="store_true",
        help="Disable Tabula's table area guessing (sometimes helps).",
    )

    p.add_argument(
        "--out",
        type=Path,
        default=Path("output.csv"),
        help="Where to save merged CSV output (default: output.csv).",
    )

    p.add_argument(
        "--filter-col",
        type=str,
        default=None,
        help="Column name to filter on (substring match).",
    )
    p.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Substring to filter rows by (case-insensitive).",
    )

    p.add_argument(
        "--sum-col",
        type=str,
        default=None,
        help="Column name to sum (numeric). Prints the result.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    lattice = None
    if args.mode == "lattice":
        lattice = True
    elif args.mode == "stream":
        lattice = False

    try:
        dfs = extract_tables(
            pdf_path=args.pdf,
            pages=args.pages,
            guess=not args.no_guess,
            lattice=lattice,
        )
        if not dfs:
            print("No tables found. If the PDF is scanned, you’ll need OCR instead.", file=sys.stderr)
            raise SystemExit(2)

        merged = normalize_tables(dfs)
        if merged.empty:
            print("Tables extracted but merged result is empty.", file=sys.stderr)
            raise SystemExit(2)

        # Optional filtering
        if args.filter_col and args.filter:
            merged = filter_rows_contains(merged, args.filter_col, args.filter)

        # Optional sum
        if args.sum_col:
            total = sum_column(merged, args.sum_col)
            print(f"Sum({args.sum_col}) = {total}")

        merged.to_csv(args.out, index=False)
        print(f"Saved CSV: {args.out.resolve()}")
        print(f"Rows: {len(merged)} | Columns: {len(merged.columns)}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
