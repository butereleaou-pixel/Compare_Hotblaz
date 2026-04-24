import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.mixture import GaussianMixture
import re
import glob
import random

# --------------------------
# Auto find DBs
# --------------------------

db_files = sorted(
    glob.glob("../database/2026_3_29/compare_50*.db") +
    glob.glob("../database/2026_3_28/compare_50*.db") +
    glob.glob("../database/2026_3_29_2/compare_50*.db") +
    glob.glob("../database/2026_3_30/compare_50*.db") +
    glob.glob("../database/2026_4_2/compare_50*.db")
)
'''
db_files = sorted(
    glob.glob("../database/2026_3_29_2/compare_50*.db")
)
'''
db_files = [f for f in db_files if not f.endswith(("compare_50.db", "compare_50_panel.db"))]

if not db_files:
    print("❌ No compare_50*.db found!")
    exit()

TABLES = ["sample", "pre_sample"]
ANSWER_LIST = ["A", "B", "C", "D"]

# --------------------------
# Functions
# --------------------------
def load_db(db_path):
    conn = sqlite3.connect(db_path)
    dfs = []
    for tbl in TABLES:
        df = pd.read_sql(f"SELECT id, eucli_dis, answer FROM {tbl}", conn)
        dfs.append(df)
    conn.close()
    return pd.concat(dfs, ignore_index=True)

def extract_ans(text):
    if pd.isna(text):
        return None
    match = re.search(r"ANSWER:\s*([A-Z])", str(text).upper())
    return match.group(1) if match else None

def calc_group_stats(df, ans_label):
    sub = df[df["ans"] == ans_label].copy()
    vals = pd.to_numeric(sub["eucli_dis"], errors="coerce").dropna()
    if len(vals) == 0:
        return None

    return {
        "Answer": f"ANSWER {ans_label}",
        "Count": len(vals),
        "Mean": vals.mean(),
        "Median": vals.median(),
        "Std": vals.std(),
        "Variance": vals.var(),
        "Min": vals.min(),
        "Max": vals.max(),
        "Range": vals.max() - vals.min(),
        "Skewness": skew(vals),
        "Kurtosis": kurtosis(vals)
    }

def calc_global_stats(df):
    vals = pd.to_numeric(df["eucli_dis"], errors="coerce").dropna()
    return {
        "Answer": "GLOBAL",
        "Count": len(vals),
        "Mean": vals.mean(),
        "Median": vals.median(),
        "Std": vals.std(),
        "Variance": vals.var(),
        "Min": vals.min(),
        "Max": vals.max(),
        "Range": vals.max() - vals.min(),
        "Skewness": skew(vals),
        "Kurtosis": kurtosis(vals),
        "GMM_pi": np.nan,
        "GMM_mu": np.nan,
        "GMM_sigma": np.nan
    }

# --------------------------
# MAIN PROCESS
# --------------------------
print("\n" + "=" * 80)
print("START PROCESSING ALL DATABASES WITH GLOBAL NORMALIZATION")
print("=" * 80)

all_results = []

for db_path in db_files:
    print(f"\n📂 DATABASE: {db_path}")

    df = load_db(db_path)
    df["ans"] = df["answer"].apply(extract_ans)
    df["eucli_dis"] = pd.to_numeric(df["eucli_dis"], errors="coerce")
    df = df.dropna(subset=["eucli_dis", "ans"])

    unique_answers = sorted(df["ans"].unique())
    db_results = []

    # --------------------------
    # 1. GROUP STATS
    # --------------------------
    for ans in unique_answers:
        stat = calc_group_stats(df, ans)
        if stat:
            db_results.append(stat)

    # --------------------------
    # 2. GLOBAL STATS
    # --------------------------
    global_row = calc_global_stats(df)
    db_results.append(global_row)

    # --------------------------
    # 3. GMM FIT
    # --------------------------
    y = df["eucli_dis"].values.reshape(-1, 1)
    n_components = len(unique_answers)

    gmm = GaussianMixture(n_components=n_components, random_state=0)
    gmm.fit(y)

    df["gmm_comp"] = gmm.predict(y)

    # --------------------------
    # 4. COMPONENT → ANSWER
    # --------------------------
    cross = pd.crosstab(df["gmm_comp"], df["ans"])

    ans_to_comp = {}
    for comp in cross.index:
        best_ans = cross.loc[comp].idxmax()
        if best_ans not in ans_to_comp:
            ans_to_comp[best_ans] = comp
        else:
            prev = ans_to_comp[best_ans]
            if cross.loc[comp, best_ans] > cross.loc[prev, best_ans]:
                ans_to_comp[best_ans] = comp

    # --------------------------
    # 5. MERGE GMM INTO ANSWERS
    # --------------------------
    for row in db_results:
        if row["Answer"] == "GLOBAL":
            continue

        ans_label = row["Answer"].split()[-1]

        if ans_label in ans_to_comp:
            comp = ans_to_comp[ans_label]

            row["GMM_pi"] = gmm.weights_[comp]
            row["GMM_mu"] = gmm.means_[comp][0]
            row["GMM_sigma"] = np.sqrt(gmm.covariances_[comp][0][0])
        else:
            row["GMM_pi"] = np.nan
            row["GMM_mu"] = np.nan
            row["GMM_sigma"] = np.nan

    # --------------------------
    # 6. FILL + SHUFFLE
    # --------------------------
    ans_rows = [r for r in db_results if r["Answer"] != "GLOBAL"]

    # 补齐 A/B/C/D
    for ans in ANSWER_LIST:
        if not any(r["Answer"].endswith(ans) for r in ans_rows):
            dummy = {k: 0 for k in ans_rows[0].keys()}
            dummy["Answer"] = f"ANSWER {ans}"
            dummy["GMM_pi"] = np.nan
            dummy["GMM_mu"] = np.nan
            dummy["GMM_sigma"] = np.nan
            ans_rows.append(dummy)

    random.shuffle(ans_rows)

    # 记录正确答案位置
    right_answer_position = None
    for i, row in enumerate(ans_rows):
        if row["Answer"].endswith("A"):
            right_answer_position = i
        row["Answer"] = f"ANSWER {ANSWER_LIST[i]}"

    # --------------------------
    # 7. NORMALIZE BY GLOBAL
    # --------------------------
    exclude_cols = ["Answer", "GMM_pi", "GMM_mu", "GMM_sigma"]

    for row in ans_rows:
        for key in row.keys():
            if key in exclude_cols:
                continue

            if key not in global_row:
                continue

            g_val = global_row[key]
            r_val = row[key]

            if isinstance(g_val, (int, float)) and g_val != 0:
                row[key] = round(r_val / g_val, 4)
            else:
                row[key] = 0

    # --------------------------
    # 8. FINAL TABLE
    # --------------------------
    final_rows = ans_rows + [global_row]

    final_df = pd.DataFrame(final_rows)
    final_df["Right_Answer_Pos"] = right_answer_position

    print(final_df.round(4).to_string(index=False))

    # 保存
    for row in final_rows:
        row["Database"] = db_path
        row["Right_Answer_Pos"] = right_answer_position
        all_results.append(row)

    print("\n" + "=" * 80)

# --------------------------
# SAVE EXCEL
# --------------------------
if all_results:
    final_df = pd.DataFrame(all_results)
    final_df.to_excel("pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx", index=False)
    print("\n✅ Excel saved: ALL_DB_FINAL_SHUFFLED.xlsx")