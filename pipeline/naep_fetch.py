import requests
import pandas as pd
import json
import re
import time
import os

BASE_URL = "https://www.nationsreportcard.gov/Dataservice/GetAdhocData.aspx"

# cohort (grade) mapping
COHORTS = {
    4: 1,
    8: 2,
    12: 3
}

# per-cohort year chunks: 1992/1994 have no RRPCM data and poison bundles;
# grade 12 was not assessed in 2003 so its 2005-2011 chunk omits it.
YEAR_CHUNKS = {
    1: ["1998,2000,2002", "2003,2005,2007,2009,2011", "2013,2015,2017,2019,2022,2024"],
    2: ["1998,2000,2002", "2003,2005,2007,2009,2011", "2013,2015,2017,2019,2022,2024"],
    3: ["1998,2000,2002", "2005,2007,2009,2011",      "2013,2015,2017,2019,2022,2024"],
}

# TOTAL = all students, SLUNCH3 = income proxy, SDRACE = race
VARIABLES = ["TOTAL", "GENDER", "SLUNCH3", "SDRACE"]

def fetch_naep(cohort, variable, years):
    params = {
        "type": "data",
        "subject": "reading",
        "cohort": cohort,
        "subscale": "RRPCM",
        "variable": variable,
        "jurisdiction": "NP",
        "stattype": "MN:MN",
        "Year": years
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        text = response.text
        # strip control characters (CR, LF, and others) from stack traces embedded in error JSON
        text = re.sub(r'[\x00-\x08\x0a-\x0c\x0e-\x1f\r]', '', text)
        # fix unescaped backslashes from windows paths
        text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
        data = json.loads(text)
        result = data.get("result", [])
        if isinstance(result, list) and all(isinstance(r, dict) for r in result):
            return result
        else:
            return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

def main():
    all_records = []

    for grade, cohort in COHORTS.items():
        for variable in VARIABLES:
            for year_chunk in YEAR_CHUNKS[cohort]:
                print(f"Fetching grade {grade}, variable {variable}, years {year_chunk}...")
                records = fetch_naep(cohort, variable, year_chunk)
                print(f"  Got {len(records)} records")
                if records:
                    all_records.extend(records)

    print(f"\nTotal records collected: {len(all_records)}")

    if all_records:
        df = pd.DataFrame(all_records)
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")

        os.makedirs("data/raw", exist_ok=True)

        # remove old file if it exists
        if os.path.exists("data/raw/naep_raw.csv"):
            os.remove("data/raw/naep_raw.csv")

        df.to_csv("data/raw/naep_raw.csv", index=False)
        print(f"Saved to data/raw/naep_raw.csv")
        print(df.head())

if __name__ == "__main__":
    main()
