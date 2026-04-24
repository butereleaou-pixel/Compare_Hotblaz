#Comapare with the varience of the mean_line_ratio, how different

import json
import re
import sqlite3
import glob
import os
import sys
import time
import matplotlib.pyplot as plt
from collections import defaultdict

# ===================== Core Config =====================
date_str = "3_30"
DB_FILES = sorted(glob.glob(f"../database/2026_{date_str}/compare_50_15.db"))
OUTPUT_MD = f"test_result_{date_str}_ALL_STAT.md"
IMAGE_FILE = f"ratio_ALL_curve_{date_str}.png"

START_RATIO = 0.850
END_RATIO = 1.100
STEP = 0.001

IGNORE_COUNT = 3
DIFF_THRESHOLD = 1.0

# ===================== Plot: 4 curves =====================
plt.ion()
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_title("Mean Line Ratio vs A/B/C/D Count", fontsize=14)
ax.set_xlabel("Mean Line Ratio", fontsize=12)
ax.set_ylabel("Total Count", fontsize=12)
ax.grid(True, alpha=0.3)

colors = ["#ff4b5c", "#2ca02c", "#1f77b4", "#ff7f0e"]
labels = ["A", "B", "C", "D"]
lines = []
data_log = {"ratio": [], "A": [], "B": [], "C": [], "D": []}

for i, ans in enumerate(labels):
    line, = ax.plot([], [], color=colors[i], linewidth=2, marker='o', markersize=1.5, label=f"Answer {ans}")
    lines.append(line)

ax.legend()

# ===================== Hover Annotation =====================
annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                    arrowprops=dict(arrowstyle="->"))
annot.set_visible(False)

def on_hover(event):
    if event.inaxes != ax:
        annot.set_visible(False)
        fig.canvas.draw_idle()
        return

    x = event.xdata
    y = event.ydata
    if x is None or y is None:
        return

    for i, ans in enumerate(labels):
        xs = data_log["ratio"]
        ys = data_log[ans]
        for j, (rx, ry) in enumerate(zip(xs, ys)):
            if abs(rx - x) < 0.0015 and abs(ry - y) < 0.3:
                annot.xy = (rx, ry)
                annot.set_text(f"Ratio: {rx:.3f}\nAnswer {ans}: {ry}")
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
    annot.set_visible(False)
    fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", on_hover)

# ===================== Analysis Function =====================
def analyze_answer_list(answer_list_str, average_eucli_dis):
    target = average_eucli_dis
    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*ANSWER:\s*([A-D])\b"
    matches = re.findall(pattern, answer_list_str)
    if not matches:
        return None, None, None

    stat = defaultdict(lambda: {"total": 0.0, "count": 0})
    for score_str, ans in matches:
        score = float(score_str)
        stat[ans]["total"] += score
        stat[ans]["count"] += 1

    result = {}
    for ans, data in stat.items():
        count = data["count"]
        if count < IGNORE_COUNT:
            continue
        avg = round(data["total"] / count, 6)
        result[ans] = {
            "count": count,
            "avg_score": avg,
            "diff": abs(avg - target)
        }

    if len(result) == 0:
        return result, None, None

    sorted_by_count = sorted(result.items(), key=lambda x: x[1]["count"], reverse=True)
    top2_names = [item[0] for item in sorted_by_count[:2]]

    top2_below_threshold = True
    for ans in top2_names:
        if result[ans]["diff"] >= DIFF_THRESHOLD:
            top2_below_threshold = False
            break

    if top2_below_threshold:
        candidates = {ans: result[ans] for ans in top2_names}
    else:
        candidates = result

    min_diff = float("inf")
    best_ans = None
    for ans, info in candidates.items():
        if info["diff"] < min_diff:
            min_diff = info["diff"]
            best_ans = ans

    return result, best_ans, min_diff

# ===================== Utility Function =====================
def pick_average_dis(conn, average_eucli_dis):
    cursor = conn.cursor()
    query = """
        SELECT answer, eucli_dis
        FROM (
            SELECT answer, eucli_dis, ABS(eucli_dis - ?) AS distance
            FROM sample
            UNION ALL
            SELECT answer, eucli_dis, ABS(eucli_dis - ?) AS distance
            FROM pre_sample
        )
        ORDER BY distance ASC
        LIMIT 15
    """
    cursor.execute(query, (average_eucli_dis, average_eucli_dis))
    rows = cursor.fetchall()
    lines = ["=" * 100, f"{'RANK':<6} | {'CLOSE_SCORE':<15} | ANSWER", "=" * 100]
    for idx, (answer, eucli_dis) in enumerate(rows, 1):
        if answer:
            lines.append(f"{idx:<6} | {eucli_dis:<15.6f} | {answer.strip()}")
    lines.append("=" * 100)
    return "\n".join(lines)

def calculate_average_eucli_dis(conn, table_names):
    cursor = conn.cursor()
    total_sum = 0.0
    total_count = 0
    for table_name in table_names:
        cursor.execute(f"SELECT SUM(eucli_dis), COUNT(*) FROM {table_name} WHERE eucli_dis IS NOT NULL")
        res = cursor.fetchone()
        if res[0] is not None:
            total_sum += res[0]
            total_count += res[1]
    return total_sum / total_count if total_count > 0 else 0.0

def process_db_get_best_ans(db_path, mean_line_ratio):
    try:
        conn = sqlite3.connect(db_path)
        avg_dis = calculate_average_eucli_dis(conn, ["sample", "pre_sample"]) * mean_line_ratio
        answer_list = pick_average_dis(conn, avg_dis)
        stats, best_ans, min_diff = analyze_answer_list(answer_list, avg_dis)
        conn.close()
        return best_ans
    except:
        return None

# ===================== Count All A B C D =====================
def count_all(ratio):
    cnt = {"A":0, "B":0, "C":0, "D":0}
    for db in DB_FILES:
        ans = process_db_get_best_ans(db, ratio)
        if ans in cnt:
            cnt[ans] += 1
    return cnt["A"], cnt["B"], cnt["C"], cnt["D"]

# ===================== Update Graph in Real-time =====================
def update_graph(ratio, a,b,c,d):
    data_log["ratio"].append(ratio)
    data_log["A"].append(a)
    data_log["B"].append(b)
    data_log["C"].append(c)
    data_log["D"].append(d)

    lines[0].set_data(data_log["ratio"], data_log["A"])
    lines[1].set_data(data_log["ratio"], data_log["B"])
    lines[2].set_data(data_log["ratio"], data_log["C"])
    lines[3].set_data(data_log["ratio"], data_log["D"])

    ax.relim()
    ax.autoscale_view()
    plt.draw()
    plt.pause(0.01)

# ===================== Save MD File (Include A B C D) =====================
def save_full_stat():
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# 📊 Ratio {START_RATIO}-{END_RATIO} A/B/C/D Full Statistics\n\n")
        f.write("| ratio | A | B | C | D |\n")
        f.write("|-------|---|---|---|---|\n")
        for i in range(len(data_log["ratio"])):
            r = data_log["ratio"][i]
            a = data_log["A"][i]
            b = data_log["B"][i]
            c = data_log["C"][i]
            d = data_log["D"][i]
            f.write(f"| {r:.3f} | {a} | {b} | {c} | {d} |\n")

# ===================== Main Program =====================
if __name__ == "__main__":
    print(f"🚀 Scanning ratio range: {START_RATIO:.3f} ~ {END_RATIO:.3f}")
    print(f"📂 Number of databases: {len(DB_FILES)}")

    ratio = START_RATIO
    while ratio <= END_RATIO + 1e-9:
        r = round(ratio, 3)
        print(f"\n📌 Current ratio: {r:.3f}")

        a,b,c,d = count_all(r)
        update_graph(r,a,b,c,d)
        save_full_stat()

        print(f"   ✅ A={a}  B={b}  C={c}  D={d}")
        ratio += STEP

    plt.ioff()
    plt.savefig(IMAGE_FILE, dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\n🎉 All tasks completed!")
    print(f"💾 Table saved to: {OUTPUT_MD}")
    print(f"🖼️  Image saved to: {IMAGE_FILE}")