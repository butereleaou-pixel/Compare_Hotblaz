import json
import re
import sqlite3
import glob
import os
import sys
import time
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.widgets import Cursor

# ===================== 核心配置 =====================
date_str = "3_29"
DB_FILES = sorted(glob.glob(f"../database/2026_{date_str}/compare_50_*.db"))
OUTPUT_MD = f"test_result_{date_str}_A_stat.md"
IMAGE_FILE = f"ratio_A_curve_{date_str}.png"

START_RATIO = 0.850
END_RATIO = 1.100
STEP = 0.001

IGNORE_COUNT = 3
DIFF_THRESHOLD = 1.0

# ===================== 绘图初始化 =====================
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_title("Mean Line Ratio vs Answer A Count", fontsize=14, pad=12)
ax.set_xlabel("Mean Line Ratio", fontsize=12)
ax.set_ylabel("Total A Count", fontsize=12)
ax.grid(True, alpha=0.3)
line, = ax.plot([], [], 'b-o', linewidth=1.8, markersize=3)
ratios_list = []
a_counts_list = []

# ===================== 鼠标悬浮：蓝色底色 + 白字 =====================
annot = ax.annotate(
    "",
    xy=(0, 0),
    xytext=(10, 10),
    textcoords="offset points",
    bbox=dict(boxstyle="round,pad=0.4", fc="#3377ff", ec="#003399", lw=1),  # 蓝色底
    fontsize=10,
    color="white"   # 字体白色
)
annot.set_visible(False)

def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = line.contains(event)
        if cont:
            x = line.get_xdata()[ind["ind"][0]]
            y = line.get_ydata()[ind["ind"][0]]
            annot.xy = (x, y)
            annot.set_text(f"Ratio: {x:.3f}\nA Count: {y}")
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", hover)
cursor = Cursor(ax, useblit=True, color='gray', linewidth=1, linestyle='--')

# ===================== 解析函数 =====================
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

# ===================== 工具函数 =====================
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

def count_total_A(ratio):
    count = 0
    for db in DB_FILES:
        ans = process_db_get_best_ans(db, ratio)
        if ans == "A":
            count += 1
    return count

# ===================== 实时更新图表 =====================
def update_graph(ratio, count):
    ratios_list.append(ratio)
    a_counts_list.append(count)
    line.set_data(ratios_list, a_counts_list)
    ax.relim()
    ax.autoscale_view()
    plt.draw()
    plt.pause(0.01)

# ===================== 保存 MD =====================
def save_simple_stat(results):
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("# 📊 不同比率下答案 A 总数统计\n\n")
        f.write("| mean_line_ratio | A 的总数 |\n")
        f.write("|----------------|----------|\n")
        for r, t in results:
            f.write(f"| {r:.3f} | {t} |\n")

# ===================== 主程序 =====================
if __name__ == "__main__":
    print(f"🚀 遍历比率：{START_RATIO:.3f} ~ {END_RATIO:.3f}，步长 {STEP:.3f}")
    print(f"📂 数据库数量：{len(DB_FILES)}")

    ratio = START_RATIO
    results = []

    plt.ion()

    while ratio <= END_RATIO + 1e-9:
        r = round(ratio, 3)
        print(f"\n📌 当前比率: {r:.3f}")

        total_A = count_total_A(r)
        results.append((r, total_A))
        update_graph(r, total_A)
        save_simple_stat(results)

        print(f"   ✅ A 的总数: {total_A}")
        ratio += STEP

    plt.ioff()
    ax.set_title(f"Mean Line Ratio ({START_RATIO:.3f} ~ {END_RATIO:.3f}) vs Answer A Count", fontsize=12)
    fig.tight_layout()
    plt.savefig(IMAGE_FILE, dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\n🎉 全部完成！")
    print(f"💾 表格已保存到：{OUTPUT_MD}")
    print(f"🖼️  图表已保存到：{IMAGE_FILE}")