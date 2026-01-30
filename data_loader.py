import os
import pandas as pd

BASE_DIR = "output_versions"

TABLE_MAP = {
    "industry": "industry.xlsx",
    "practice_area": "practice_area.xlsx",
    "detailed_practice_area": "detailed_practice_area.xlsx",
    "amlaw_bucket": "amlaw_bucket.xlsx",
    "firm_size": "firm_size.xlsx",
    "role": "role.xlsx",
    "years_of_experience": "years_of_experience.xlsx",
    "city": "city.xlsx",
    "country": "country.xlsx",
    "matter_type": "matter_type.xlsx",
}

def load_all_tables(version: str):
    version = version.capitalize()
    folder = os.path.join(BASE_DIR, version)

    if not os.path.exists(folder):
        raise FileNotFoundError(f"Missing folder: {folder}")

    data = {}
    for key, file in TABLE_MAP.items():
        path = os.path.join(folder, file)
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        df = pd.read_excel(path)
        df.columns = [c.strip() for c in df.columns]
        data[key] = df

    return data

def load_all_2d_tables(version: str):
    """
    Loads all 2D pivot tables (files containing '_x_')
    """
    version = version.capitalize()
    folder = os.path.join(BASE_DIR, version)

    if not os.path.exists(folder):
        raise FileNotFoundError(f"Missing folder: {folder}")

    data_2d = {}

    for file in os.listdir(folder):
        if "_x_" in file and file.endswith(".xlsx"):
            key = file.replace(".xlsx", "")
            path = os.path.join(folder, file)

            df = pd.read_excel(path)
            df.columns = [c.strip() for c in df.columns]

            data_2d[key] = df

    return data_2d

