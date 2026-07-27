"""Utilities for extracting class and assessment tables from timetable PDFs.

This module is responsible for:
- running PDF table extraction (`tabula` primary, `camelot` fallback),
- identifying week/section blocks from extracted class tables,
- normalizing those blocks for downstream event parsing,
- and shaping assessment tables into a predictable dataframe format.
"""

import re
import shutil
from pathlib import Path

import pandas as pd
import tabula



def extract_tables(pdf_path: Path) -> list[pd.DataFrame]:
    """Extract all tables from a PDF using tabula.

    Returns an empty list if Java is unavailable or extraction fails.
    """
    # `tabula-py` requires a Java runtime.
    if shutil.which("java") is None:
        print("Error extracting tables from PDF: Java runtime not found on PATH.")
        return []

    try:
        tables = tabula.read_pdf(
            str(pdf_path),
            pages="all",
            multiple_tables=True,
            lattice=True,
            guess=False,
            force_subprocess=True,
        )
        print(f"Extracted {len(tables)} tables from PDF.")

        return tables
    except Exception as e:
        print(f"Error extracting tables from PDF (subprocess mode): {e}")
        return []


def extract_tables_fallback(pdf_path: Path) -> list[pd.DataFrame]:
    """Fallback table extractor that uses Camelot lattice parsing."""
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            tbls: list[pd.DataFrame] = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    tbls.append(df)

            return tbls

    except Exception as e:
        print(f"Error extracting tables from PDF using Camelot: {e}")
        return []


def is_section_header(row: pd.Series) -> bool:
    """Return True when a row contains a week/section heading label."""
    section_label_re = re.compile(
        r"^\s*(Academic\s+Week\b.*|CATCH\s*UP\b.*|ASSESS\s+WEEK\b.*)\s*$",
        re.I,
    )
    return any(section_label_re.match(str(cell)) for cell in row)


def is_timeslot_row(row: pd.Series) -> bool:
    """Return True when the first cell looks like a timetable time range."""
    time_re = re.compile(
        r"^\s*\d{1,2}H\d{2}\s*-\s*\d{1,2}H\d{2}\s*$" r"|^\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*$",
        re.I,
    )
    first = str(row.iloc[0]).strip() if len(row) > 0 else ""
    return bool(time_re.match(first))


def extract_weeks(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Split one extracted timetable table into normalized per-week dataframes."""
    header_indices = [i for i, row in df.iterrows() if is_section_header(row)]
    if not header_indices:
        return []

    weeks: list[pd.DataFrame] = []

    for i, start in enumerate(header_indices):
        end = header_indices[i + 1] if i + 1 < len(header_indices) else len(df)
        block = df.iloc[start:end].reset_index(drop=True)

        if block.empty:
            continue

        # Use section-header row as columns
        block.columns = block.iloc[0]
        block = block[1:].reset_index(drop=True)

        # Keep timetable rows only
        block = block[block.apply(is_timeslot_row, axis=1)].reset_index(drop=True)

        if not block.empty:
            # normalize en dash for downstream parsing
            block.iloc[:, 0] = block.iloc[:, 0].astype(str).str.replace("–", "-", regex=False)
            weeks.append(block)

    return weeks


def extract_classes(tables: list[pd.DataFrame]) -> list[pd.DataFrame]:
    """Flatten all extracted tables into a single list of week dataframes."""
    all_weeks: list[pd.DataFrame] = []
    for df in tables:
        weeks = extract_weeks(df)
        all_weeks.extend(weeks)
    return all_weeks


def extract_assessments(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """Convert extracted assessment tables into a standardized dataframe."""
    assessments = []

    for df in tables:
        for _, row in df.iterrows():
            module = str(row["Module Code"]).strip().replace("\n", "")
            assessment_name = str(row["Assessment Name"]).strip().replace("\n", "")
            due_date = str(row["Assessment Date"]).strip().replace("\n", "")
            due_time = str(row["Assessment Time"]).strip().replace("\n", "")

            if (
                not module
                or not assessment_name
                or not due_date
                or module.lower() in ["nan", "tbc", "none"]
                or assessment_name.lower() in ["nan", "tbc", "none"]
                or due_date.lower() in ["nan", "tbc", "none"]
            ):
                continue
            assessments.append(
                {
                    "MODULE": module,
                    "ASSESSMENT": assessment_name,
                    "DUE DATE": due_date,
                    "DUE TIME": due_time,
                }
            )

    assessments_df = pd.DataFrame(
        assessments,
        columns=["MODULE", "ASSESSMENT", "DUE DATE", "DUE TIME"],
    )

    return assessments_df


def get_modules_from_table(df: pd.DataFrame) -> list[str]:
    """Return distinct module codes from a normalized assessment dataframe."""
    return df["MODULE CODE"].dropna().unique().tolist()


def get_version(df: pd.DataFrame) -> str:
    """Extract the version date (e.g. '04 FEB') from a table containing 'LATEST VERSION'."""

    version_date = (
        df.astype(str)
        .stack()
        .loc[lambda s: s.str.contains("LATEST VERSION", case=False)]
        .str.extract(r"(\d{1,2}\s+[A-Z]{3})")
        .iloc[0, 0]
    )

    return version_date
