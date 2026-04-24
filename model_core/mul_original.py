# db_analyzer.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.mixture import GaussianMixture

ANSWER_LIST = ["A", "B", "C", "D"]

# --------------------------
# 统计函数（不变）
# --------------------------
def calc_group_stats(df, ans_label):
    sub = df[df["ans"] == ans_label].copy()
    vals = sub["eucli_dis"].dropna()
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
    vals = df["eucli_dis"].dropna()
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
# 分析单个 DF（从 df.attrs 拿 path）
# --------------------------
def analyze_single_df(raw_df):
    db_path = raw_df.attrs["db_path"]  # ✅ 从 df 内部拿，不用外部传
    unique_answers = sorted(raw_df["ans"].unique())
    db_results = []

    for ans in unique_answers:
        stat = calc_group_stats(raw_df, ans)
        if stat:
            db_results.append(stat)

    global_row = calc_global_stats(raw_df)
    db_results.append(global_row)

    # GMM
    y = raw_df["eucli_dis"].values.reshape(-1, 1)
    n_components = len(unique_answers)
    gmm = GaussianMixture(n_components=n_components, random_state=0)
    gmm.fit(y)
    raw_df["gmm_comp"] = gmm.predict(y)

    cross = pd.crosstab(raw_df["gmm_comp"], raw_df["ans"])
    ans_to_comp = {}
    for comp in cross.index:
        best_ans = cross.loc[comp].idxmax()
        ans_to_comp[best_ans] = comp

    for row in db_results:
        if row["Answer"] == "GLOBAL":
            continue
        ans_label = row["Answer"].split()[-1]
        if ans_label in ans_to_comp:
            comp = ans_to_comp[ans_label]
            row["GMM_pi"] = gmm.weights_[comp]
            row["GMM_mu"] = gmm.means_[comp][0]
            row["GMM_sigma"] = np.sqrt(gmm.covariances_[comp][0][0])

    # 固定顺序 A B C D
    ans_rows = [r for r in db_results if r["Answer"] != "GLOBAL"]
    fixed = []
    for ans in ANSWER_LIST:
        found = next((r for r in ans_rows if r["Answer"].endswith(ans)), None)
        if found:
            fixed.append(found)
        else:
            dummy = {k:0 for k in ans_rows[0].keys()} if ans_rows else {
                "Answer": f"ANSWER {ans}", "Count":0, "Mean":0, "Median":0,
                "Std":0, "Variance":0, "Min":0, "Max":0, "Range":0,
                "Skewness":0, "Kurtosis":0, "GMM_pi":np.nan,
                "GMM_mu":np.nan, "GMM_sigma":np.nan
            }
            dummy["Answer"] = f"ANSWER {ans}"
            fixed.append(dummy)

    # 归一化
    exclude = ["Answer", "GMM_pi", "GMM_mu", "GMM_sigma"]
    for row in fixed:
        for k in row:
            if k in exclude or k not in global_row:
                continue
            g = global_row[k]
            v = row[k]
            if isinstance(g, (int,float)) and g != 0:
                row[k] = round(v/g, 4)
            else:
                row[k] = 0

    return fixed, global_row, db_path

# --------------------------
# ✅ 最终完美版：只需要传 raw_dfs
# --------------------------
def analyze_all_dfs(raw_dfs):
    all_results = []
    for df in raw_dfs:
        fixed_rows, global_row, db_path = analyze_single_df(df)
        final_rows = fixed_rows + [global_row]
        for row in final_rows:
            row["Database"] = db_path
            row["Right_Answer_Pos"] = 0
        all_results.extend(final_rows)
    return pd.DataFrame(all_results)