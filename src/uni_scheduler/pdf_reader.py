from pathlib import Path
import tabula
import pandas as pd

pdf_path = Path("./bin/resrc/timetable.pdf") # change to input


def extract_timetable_section(df : pd.DataFrame) -> pd.DataFrame:
    # Ensure column 0 is treated as string
    col0 = df.iloc[:, 0].astype(str)

    # Find index where timetable begins
    start_idx = col0.str.contains("Academic Week", case=False, na=False).idxmax()

    # Slice from that row downward
    return df.iloc[start_idx:].reset_index(drop=True)


# Extract all tables from all pages
def extract_tables_from_pdf(pdf_path: Path) -> pd.DataFrame:
    tables = tabula.read_pdf(
        str(pdf_path),
        pages="all",
        multiple_tables=True,
        lattice=True,
        guess=False
    )

    cleaned_tables = [extract_timetable_section(df) for df in tables]
    combined = pd.concat(cleaned_tables, ignore_index=True)

    combined.columns = combined.iloc[0]  # Set the first row as header
    combined = combined[1:]  # Remove the header row from the data
    combined.reset_index(drop=True, inplace=True)  # Reset index after removing header row
    return combined



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