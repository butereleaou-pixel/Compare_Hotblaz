import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.mixture import GaussianMixture
import re
import glob

# --------------------------
# CONFIG
# --------------------------
DELTA = 0.05
ALPHA = 50

db_files = sorted(glob.glob("compare_50*.db"))
db_files = [f for f in db_files if f not in ["compare_50.db", "compare_50_panel.db"]]

TABLES = ["sample", "pre_sample"]

# --------------------------
# FUNCTIONS
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
    sub = df[df["ans"] == ans_label]
    vals = pd.to_numeric(sub["eucli_dis"], errors="coerce").dropna()

    if len(vals) == 0:
        return None

    return {
        "Answer": ans_label,
        "Count": len(vals),
        "Mean": vals.mean(),
        "Std": vals.std(),
        "Variance": vals.var(),
        "Skewness": skew(vals),
        "Kurtosis": kurtosis(vals)
    }

# --------------------------
# NEW: Fisher Separation
# --------------------------
def fisher_ratio(mu1, mu2, var1, var2):
    return (mu1 - mu2) ** 2 / (var1 + var2 + 1e-8)

# --------------------------
# NEW: Optimal Threshold
# --------------------------
def find_best_threshold(df):
    df["is_A"] = (df["ans"] == "A")
    values = np.sort(df["eucli_dis"].unique())

    best = None
    best_score = -np.inf

    for t in values:
        window = df[(df["eucli_dis"] >= t - DELTA) & (df["eucli_dis"] <= t + DELTA)]
        A_rows = window[window["is_A"]]

        if len(A_rows) == 0:
            continue

        count_A = len(A_rows)
        mean_A = A_rows["eucli_dis"].mean()
        distance = abs(mean_A - t)

        score = count_A - ALPHA * distance

        if score > best_score:
            best_score = score
            best = (t, count_A, mean_A, distance, score)

    return best

# --------------------------
# PROCESS
# --------------------------
for db_path in db_files:
    print("\n" + "=" * 80)
    print(f"📂 DATABASE: {db_path}")

    df = load_db(db_path)
    df["ans"] = df["answer"].apply(extract_ans)
    df["eucli_dis"] = pd.to_numeric(df["eucli_dis"], errors="coerce")
    df = df.dropna(subset=["eucli_dis", "ans"])

    # --------------------------
    # 1. GROUP STATS
    # --------------------------
    stats = {}
    for ans in sorted(df["ans"].unique()):
        s = calc_group_stats(df, ans)
        if s:
            stats[ans] = s

    stats_df = pd.DataFrame(stats).T
    print("\n📊 GROUP DISTRIBUTION:")
    print(stats_df)

    # --------------------------
    # 2. GLOBAL DISTRIBUTION
    # --------------------------
    y = df["eucli_dis"].values
    print("\n🌍 GLOBAL DISTRIBUTION:")
    print(f"Mean={y.mean():.4f}, Std={y.std():.4f}, Skew={skew(y):.4f}, Kurt={kurtosis(y):.4f}")

    # --------------------------
    # 3. GAUSSIAN MIXTURE MODEL
    # --------------------------
    print("\n🧠 GMM (Mixture Model):")
    gmm = GaussianMixture(n_components=3, random_state=0)
    gmm.fit(y.reshape(-1, 1))

    for i in range(3):
        print(f"Component {i}: π={gmm.weights_[i]:.3f}, μ={gmm.means_[i][0]:.3f}, σ={np.sqrt(gmm.covariances_[i][0][0]):.3f}")

    # --------------------------
    # 4. FISHER SEPARATION
    # --------------------------
    print("\n📏 FISHER SEPARATION:")
    keys = list(stats.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            f = fisher_ratio(
                stats[a]["Mean"], stats[b]["Mean"],
                stats[a]["Variance"], stats[b]["Variance"]
            )
            print(f"{a} vs {b}: {f:.4f}")

    # --------------------------
    # 5. OPTIMAL THRESHOLD
    # --------------------------
    print("\n🎯 OPTIMAL THRESHOLD (for ANSWER A):")
    best = find_best_threshold(df)

    if best:
        t, count_A, mean_A, dist, score = best
        print(f"Threshold={t:.4f}, CountA={count_A}, MeanA={mean_A:.4f}, Dist={dist:.4f}, Score={score:.4f}")
    else:
        print("No valid threshold found")

    print("=" * 80)