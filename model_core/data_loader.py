# data_loader.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import pandas as pd
import re
import glob

TABLES = ["sample", "pre_sample"]

def load_single_db(db_path):
    conn = sqlite3.connect(db_path)
    dfs = []
    for tbl in TABLES:
        df = pd.read_sql(f"SELECT id, eucli_dis, answer FROM {tbl}", conn)
        dfs.append(df)
    conn.close()

    df = pd.concat(dfs, ignore_index=True)
    df["ans"] = df["answer"].apply(extract_ans)
    df["eucli_dis"] = pd.to_numeric(df["eucli_dis"], errors="coerce")
    df = df.dropna(subset=["eucli_dis", "ans"])

    # ✅ 关键：把 path 存在 df 里
    df.attrs["db_path"] = db_path
    return df

def extract_ans(text):
    if pd.isna(text):
        return None
    match = re.search(r"ANSWER:\s*([A-Z])", str(text).upper())
    return match.group(1) if match else None

def get_all_db_files(pattern):
    files = sorted(glob.glob(pattern))
    return [f for f in files if not f.endswith(("compare_50.db", "compare_50_panel.db"))]