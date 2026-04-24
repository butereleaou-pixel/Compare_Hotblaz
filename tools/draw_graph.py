import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob

# --------------------------
# Basic Settings
# --------------------------
# Auto find all DBs, BUT exclude compare_50.db and compare_50_panel.db
DB_FILES = sorted(glob.glob("../database/2026_4_2/compare_50_12.db"))
DB_FILES = [
    db for db in DB_FILES
    if db not in ["compare_50.db", "compare_50_panel.db"]
]

TABLES = ["sample", "pre_sample"]

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]
MARKERS = ["o", "s", "^", "D", "p", "*", "h", "x", "P", "v"]

# --------------------------
# Extract Answer
# --------------------------
def extract_answer(text):
    if pd.isna(text):
        return None
    match = re.search(r"ANSWER:\s*([A-Za-z])", str(text), re.IGNORECASE)
    return match.group(1).upper() if match else None

# --------------------------
# Plot ALL DBs AT THE SAME TIME
# --------------------------
for idx, DB_PATH in enumerate(DB_FILES):
    print("Plotting:", DB_PATH)

    # Read DB
    conn = sqlite3.connect(DB_PATH)
    df_list = []
    for table in TABLES:
        query = f"SELECT id, eucli_dis, answer FROM {table}"
        temp_df = pd.read_sql(query, conn)
        df_list.append(temp_df)
    df = pd.concat(df_list, ignore_index=True)
    conn.close()

    # Process data
    df["ans_label"] = df["answer"].apply(extract_answer)
    df = df.dropna(subset=["id", "eucli_dis", "ans_label"])
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["eucli_dis"] = pd.to_numeric(df["eucli_dis"], errors="coerce")

    # Mean line logic
    ratio_panel = 0.995142
    cal_mean_val = df["eucli_dis"].mean()
    mean_val = ratio_panel * cal_mean_val

    # Create NEW FIGURE for each DB
    plt.figure(figsize=(12, 6), num=f"Figure {idx+1}: {DB_PATH}")

    # Plot points
    unique_ans = sorted(df["ans_label"].unique())
    for i, ans in enumerate(unique_ans):
        sub = df[df["ans_label"] == ans]
        c = COLORS[i % len(COLORS)]
        m = MARKERS[i % len(MARKERS)]
        plt.scatter(sub["id"], sub["eucli_dis"], color=c, marker=m, s=70, alpha=0.9, label=f"ANSWER: {ans}")

    # Blue mean line
    plt.axhline(
        y=mean_val,
        color='blue',
        linestyle='--',
        linewidth=2,
        label=f'Mean Euclidean Distance = {mean_val:.3f}'
    )

    # Title ON TOP = database name
    plt.xlabel("ID", fontsize=12)
    plt.ylabel("Euclidean Distance", fontsize=12)
    plt.title(f"Euclidean Distance - {DB_PATH}", fontsize=14)
    plt.grid(alpha=0.3, linestyle="--")
    plt.legend(title="Legend", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

# --------------------------
# Show ALL figures TOGETHER
# --------------------------
plt.show()