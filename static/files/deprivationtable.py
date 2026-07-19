import re
import sqlite3

import pandas as pd


ONSPD_PATH = #UPDATE TO YOUR PATHS FOR ALL 3
IMD_PATH = XX
DB_PATH = XX

CHUNK_SIZE = 200_000  # rows to read from ONSPD at a time


def normalise_postcode(pc: str) -> str:
    if pd.isna(pc):
        return pc
    pc = re.sub(r"\s+", "", str(pc)).upper()  # remove all whitespace
    return pc[:-3] + " " + pc[-3:]            # re-insert single space


def get_target_postcodes(conn: sqlite3.Connection) -> set:
    raw = pd.read_sql("SELECT DISTINCT postcode FROM patient_list_size", conn)["postcode"]
    return set(normalise_postcode(p) for p in raw)


def filter_onspd_to_postcodes(path: str, target_postcodes: set) -> pd.DataFrame:

    matches = []
    chunks_read = 0

    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, usecols=["pcds", "lsoa21cd"],
                              dtype=str, low_memory=False):
        chunk["pcds_norm"] = chunk["pcds"].apply(normalise_postcode)
        matched = chunk[chunk["pcds_norm"].isin(target_postcodes)]
        if len(matched) > 0:
            matches.append(matched)
        chunks_read += 1

    if not matches:
        raise ValueError("No postcodes matched in ONSPD file - check postcode formatting.")

    result = pd.concat(matches, ignore_index=True)
    result = result[["pcds_norm", "lsoa21cd"]].rename(columns={"pcds_norm": "postcode"})
    result = result.drop_duplicates(subset="postcode")

    print(f"  Scanned {chunks_read} chunk(s) of ONSPD")
    print(f"  Matched {len(result)} of {len(target_postcodes)} target postcodes")

    missing = target_postcodes - set(result["postcode"])
    if missing:
        print(f"  WARNING: {len(missing)} postcode(s) not found in ONSPD:")
        for m in sorted(missing):
            print(f"    - {m}")

    return result


def load_imd_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="IMD25")
    df = df.rename(columns={
        "LSOA code (2021)": "lsoa21cd",
        "LSOA name (2021)": "lsoa_name",
        "Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)": "imd_rank",
        "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOA": "imd_decile",
    })
    return df[["lsoa21cd", "lsoa_name", "imd_rank", "imd_decile"]]


def main():
    conn = sqlite3.connect(DB_PATH)

    print("=== Getting target postcodes from patient_list_size ===")
    target_postcodes = get_target_postcodes(conn)
    print(f"{len(target_postcodes)} unique postcodes to match\n")

    print("=== Filtering ONSPD to target postcodes (this may take a minute) ===")
    postcode_lsoa = filter_onspd_to_postcodes(ONSPD_PATH, target_postcodes)

    print("\n=== Loading IMD 2025 data ===")
    imd = load_imd_data(IMD_PATH)
    print(f"  {len(imd):,} LSOAs loaded")

    print("\n=== Joining postcode -> LSOA -> IMD ===")
    postcode_deprivation = postcode_lsoa.merge(imd, on="lsoa21cd", how="left")

    unmatched_lsoa = postcode_deprivation["imd_decile"].isna().sum()
    if unmatched_lsoa > 0:
        print(f"  WARNING: {unmatched_lsoa} postcode(s) matched an LSOA not found in IMD file")

    print("\n=== Joining to practices (via patient_list_size) ===")
    patient_list_size = pd.read_sql("SELECT GP_CODE, postcode, total_patients FROM patient_list_size", conn)
    patient_list_size["postcode"] = patient_list_size["postcode"].apply(normalise_postcode)

    practice_deprivation = patient_list_size.merge(postcode_deprivation, on="postcode", how="left")

    print("\n=== Writing to SQLite database ===")
    practice_deprivation.to_sql("practice_deprivation", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_deprivation_practice ON practice_deprivation(GP_CODE);")
    conn.commit()

    n_rows = conn.execute("SELECT COUNT(*) FROM practice_deprivation").fetchone()[0]
    n_missing = conn.execute(
        "SELECT COUNT(*) FROM practice_deprivation WHERE imd_decile IS NULL"
    ).fetchone()[0]

    print(f"\nDone. practice_deprivation table added to: {DB_PATH}")
    print(f"  rows: {n_rows}")
    print(f"  practices missing an IMD decile: {n_missing}")

    conn.close()


if __name__ == "__main__":
    main()