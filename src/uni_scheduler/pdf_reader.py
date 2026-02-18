from pathlib import Path
import re
import shutil
import tabula
import pandas as pd

pdf_path = Path("./bin/resrc/timetable.pdf") # change to input

def extract_tables(pdf_path: Path) -> list[pd.DataFrame]:
    # Extract tables from PDF using tabula
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

def is_section_header(row: pd.Series) -> bool:
    SECTION_LABEL_RE = re.compile(r"^\s*(Academic\s+Week\b.*|CATCH\s*UP\b.*|ASSESS\s+WEEK\b.*)\s*$",re.I,)
    return any(SECTION_LABEL_RE.match(str(cell)) for cell in row)

def is_timeslot_row(row: pd.Series) -> bool:
    TIME_RE = re.compile(r"^\s*\d{1,2}H\d{2}\s*-\s*\d{1,2}H\d{2}\s*$|^\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*$",re.I,)
    first = str(row.iloc[0]).strip() if len(row) > 0 else ""
    return bool(TIME_RE.match(first))

def extract_weeks(df: list[pd.DataFrame]) -> list[pd.DataFrame]:
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

def extract_schedule(tables : list[pd.DataFrame]) -> list[pd.DataFrame]:
    all_weeks : list[pd.DataFrame] = []
    for df in tables:
        weeks = extract_weeks(df)
        all_weeks.extend(weeks)
    return all_weeks

def get_modules_from_table(df : pd.DataFrame) -> list[str]:
    return df["MODULE CODE"].dropna().unique().tolist()

def get_version(df : pd.DataFrame) -> str:

    version_date = (
        df.astype(str)
        .stack()
        .loc[lambda s: s.str.contains("LATEST VERSION", case=False)]
        .str.extract(r"(\d{1,2}\s+[A-Z]{3})")
        .iloc[0, 0]
    )

    return version_date
