import sqlite3
from pathlib import Path

import pandas as pd

PATIENT_DATA_FILE = #UPDATE FOR YOUR PATH
DB_PATH = #UPDATE FOR YOUR PATH


def get_south_yorkshire_practice_codes(conn: sqlite3.Connection) -> set:
    """Pull the list of South Yorkshire GP_CODEs from the practices table
    you already built, so we filter consistently with your appointments data."""
    codes = pd.read_sql("SELECT DISTINCT GP_CODE FROM practices", conn)["GP_CODE"]
    return set(codes)


def load_and_filter_patient_file(filepath: str, sy_codes: set) -> pd.DataFrame:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(
            f"{filepath} not found. Check PATIENT_DATA_FILE is set correctly."
        )

    print(f"Loading: {path.name}")
    df = pd.read_csv(path, low_memory=False)

    expected_cols = {"ORG_TYPE", "ORG_CODE", "SEX", "AGE_GROUP_5",
                      "NUMBER_OF_PATIENTS", "EXTRACT_DATE", "POSTCODE"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} is missing expected columns: {missing}")

    # Keep only GP-level rows, and only the pre-summed ALL/ALL total row
    # (avoids double-counting by manually summing age bands ourselves)
    gp_totals = df[
        (df["ORG_TYPE"] == "GP")
        & (df["SEX"] == "ALL")
        & (df["AGE_GROUP_5"] == "ALL")
    ].copy()

    # Filter to South Yorkshire practices using the codes from your
    # existing practices table
    gp_totals_sy = gp_totals[gp_totals["ORG_CODE"].isin(sy_codes)].copy()

    print(f"  {len(df):,} rows -> {len(gp_totals):,} GP total rows -> "
          f"{len(gp_totals_sy):,} South Yorkshire rows")

    result = gp_totals_sy[["ORG_CODE", "POSTCODE", "NUMBER_OF_PATIENTS", "EXTRACT_DATE"]].rename(
        columns={
            "ORG_CODE": "GP_CODE",
            "POSTCODE": "postcode",
            "NUMBER_OF_PATIENTS": "total_patients",
            "EXTRACT_DATE": "snapshot_date",
        }
    )
    result["snapshot_date"] = pd.to_datetime(result["snapshot_date"], format="%d/%m/%Y")

    return result


def main():
    conn = sqlite3.connect(DB_PATH)

    print("=== Getting South Yorkshire practice codes from existing database ===")
    sy_codes = get_south_yorkshire_practice_codes(conn)
    print(f"Found {len(sy_codes)} South Yorkshire practice codes\n")

    print("=== Loading and filtering patient list size data ===")
    patient_list_size = load_and_filter_patient_file(PATIENT_DATA_FILE, sy_codes)

    print("\n=== Writing to SQLite database ===")
    patient_list_size.to_sql("patient_list_size", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_practice ON patient_list_size(GP_CODE);")
    conn.commit()

    n_rows = conn.execute("SELECT COUNT(*) FROM patient_list_size").fetchone()[0]
    n_practices = conn.execute("SELECT COUNT(DISTINCT GP_CODE) FROM patient_list_size").fetchone()[0]
    snapshot = conn.execute("SELECT DISTINCT snapshot_date FROM patient_list_size").fetchall()

    print(f"\nDone. patient_list_size table added to: {DB_PATH}")
    print(f"  rows: {n_rows:,}")
    print(f"  distinct practices: {n_practices}")
    print(f"  snapshot date used: {[s[0] for s in snapshot]}")
    print("  (NOTE: this is a static snapshot applied across all appointment months - "
          "remember to document this assumption in your write-up)")

    conn.close()


if __name__ == "__main__":
    main()
