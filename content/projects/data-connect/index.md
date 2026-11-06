---
title: "Data Engineering: NHS & UoS Data Connect"
date: 2026-11-06
draft: false
slug: "data-connect"
---

This project builds a data extract from synthetic hospital admissions data. For my new job working as a data engineer at Data Connect (at the University of Sheffield and NHS South Yorkshire), it shows an anonymised example of the work I'll be undertaking in that role.

<!--more-->

The data is the artificial Admitted Patient Care (APC) sample published by NHS England. It follows the structure of real Hospital Episode Statistics (HES) data but contains **no real patients**, so it is safe for publishing on the internet. It is not suitable for drawing conclusions, because the fields are generated independently of each other.

I used Python and pandas to load the files, SQLite to hold the data, and DB Browser for SQLite to write and check the queries.
## The request

The cohort was defined by four criteria:

- The person was admitted to hospital
- They were aged over 18 at the start of the admission
- It was an emergency admission, which is admission method code 21
- They were admitted between 1 April 2020 and 31 March 2021

Before building anything I wrote down what I would normally confirm with the researchers, which included questions such as whether "over 18" includes 18 year olds, whether the date range includes its end dates, and whether every episode should be kept when a patient attends more than once.

## Structure: bronze, silver and gold

I split the work into three layers so that each step does one job.

- **Bronze** is the raw data loaded as text, with nothing changed.
- **Silver** is a view that cleans the data but drops no rows.
- **Gold** is a table with the cohort filters applied.

## Loading the data

The sample came as 21 CSV files of 10,000 rows each, 210,000 rows in total. A short Python script combines them into one SQL database. It loads only the four columns the request needs (patient ID, age at start of episode, admission method and admission date) plus a `source_file` column, so any row can be traced back to its file.

```python
import sqlite3
from pathlib import Path
import pandas as pd

data_folder = Path("data")
database_file = Path("apc.db")
output_columns = ["PSEUDO_HESID", "STARTAGE", "ADMIMETH", "ADMIDATE"]

sqlcon = sqlite3.connect(database_file)

# Dropping the table first means a re-run does not duplicate rows
sqlcon.execute("DROP TABLE IF EXISTS apc_bronze")

for csv_file in sorted(data_folder.glob("*.csv")):
    table = pd.read_csv(
        csv_file,
        usecols=output_columns,
        dtype=str,
        keep_default_na=False,
    )
    table["source_file"] = csv_file.name
    table.to_sql("apc_bronze", sqlcon, if_exists="append", index=False)
    print(csv_file.name, len(table), "rows loaded")

sqlcon.commit()
sqlcon.close()
```

A few choices are worth explaining:

- `dtype=str` and `keep_default_na=False` keep every value as text, so blanks stay blank and nothing is converted by accident. Type conversion happens later in SQL, where it is visible and repeatable.
- `glob` picks up every CSV in the folder, so adding a file needs no code change.
- Dropping the table at the start makes the script safe to re-run. With a dataset too large to reload in full, I would delete the rows for one `source_file` and reload only that file.
- Loading only four columns keeps the extract to what was requested.

## Cleaning decisions

**Blank and coded ages.** 71 rows had no age, and some ages were 7000 or above. The HES technical specification shows that 7001 to 7007 are codes for babies under one, not real ages. The request is for adults, and a blank age cannot be shown to be 18 or over, so both were excluded.

**Placeholder dates.** Some admission dates had a year of 1800 or 1801. These stand in for missing or invalid dates, so I set them to NULL in the silver layer. They cannot fall inside the date window, so they drop out of the cohort.

**Repeated IDs.** Patients can have many episodes, so the same ID appears more than once. I kept every episode and counted patients with `COUNT(DISTINCT PSEUDO_HESID)`.

The silver view does the cleaning without removing anything:

```sql
CREATE VIEW apc_silver AS
SELECT
  NULLIF(TRIM(PSEUDO_HESID), '') AS PSEUDO_HESID,
  CAST(NULLIF(TRIM(STARTAGE), '') AS INTEGER) AS STARTAGE,
  NULLIF(TRIM(ADMIMETH), '') AS ADMIMETH,
  CASE
    WHEN TRIM(ADMIDATE) = '' OR ADMIDATE LIKE '180%' THEN NULL
    ELSE TRIM(ADMIDATE)
  END AS ADMIDATE,
  source_file
FROM apc_bronze;
```

`NULLIF` turns blank text into NULL before the cast. Without it, a blank age would be cast to 0 and look like a real value.

The gold table then applies the cohort filters:

```sql
DROP TABLE IF EXISTS apc_gold;
CREATE TABLE apc_gold AS
SELECT PSEUDO_HESID, STARTAGE, ADMIMETH, ADMIDATE
FROM apc_silver
WHERE STARTAGE BETWEEN 18 AND 6999
  AND ADMIMETH = '21'
  AND ADMIDATE BETWEEN '2020-04-01' AND '2021-03-31'
ORDER BY PSEUDO_HESID, ADMIDATE;
```

The upper age bound of 6999 excludes the under-one codes. `BETWEEN` includes both ends, which matches the assumptions above.

## Checks

**A funnel.** Applying each filter in turn shows how the data narrows and gives me counts to check the final table against.

| Stage | Episodes | Patients |
| --- | --- | --- |
| All data | 210,000 | 99,790 |
| Aged 18 or over | 175,636 | 83,273 |
| Emergency admission (code 21) | 50,858 | 34,545 |
| Admitted 1 Apr 2020 to 31 Mar 2021 | 3,027 | 1,903 |

**Checks on the gold table.** No extra columns, no missing values, ages and dates within range, and counts matching the funnel. The most episodes for one patient in the final cohort is 38.

**Repeated rows.** On the four loaded columns, 96 combinations of ID, age, admission method and date appeared more than once, which looked like duplicates. Because I had loaded only four columns, I went back to the original files and checked for rows identical across all 193 columns. There were none, so they are not true duplicates and must differ elsewhere. I have not pinned down the cause. Possible reasons include separate episodes in the same hospital stay, or chance repeats among the synthetic test IDs. Not all of these rows had admission method 21, so not all of them affect the final output.

**Raw row counts per ID.** A separate Python script counted rows per ID straight from the raw files, to check that high counts came from the source data and not from my load. It found 83 synthetic IDs starting with "TEST", each appearing exactly 100 times. That looks like a feature of how the artificial data was made, so I treated it as part of the source and not as a loading error.

## Result

The final extract has 3,027 episodes across 1,903 patients, about 1.6 episodes per patient.

## What I would do differently

- Confirm the three assumptions with whoever requested the data, in writing.
- Add automated tests for the cleaning logic and a row count check after every load.
- Keep the scripts and queries in version control with review, and log each run.
- Because the date range was optional in the request, keep the earlier funnel stages available so either version can be supplied.
- With real patient data, run the whole process inside a secure environment, with no local copies and access limited to approved staff.
