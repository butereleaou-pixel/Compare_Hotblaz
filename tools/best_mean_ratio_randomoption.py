#best mean ratio for single time test

import json
import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor

from data_loader import get_all_db_files, load_single_db
from mean_line_ratio_iteration import run_batch_analysis

date_str = "3_28"
PATTERN = f"../database/2026_{date_str}/compare_50_*.db"
JSON_FILE = "../test_record/gpqa_checkpoint_alla.json"
OUTPUT_MD = f"result_path/test_result_{date_str}_acc_stat.md"
IMAGE_FILE = f"result_pic_path/ratio_acc_curve_{date_str}.png"

START_RATIO = 0.850
END_RATIO = 1.100
STEP = 0.001

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(figsize=(12,6))
ax.set_title("Mean Line Ratio vs Total Correct Match", fontsize=14, pad=12)
ax.set_xlabel("Mean Line Ratio", fontsize=12)
ax.set_ylabel("Total Correct Match", fontsize=12)
ax.grid(True, alpha=0.3)
line, = ax.plot([], [], '#22aa22', linewidth=1.8, markersize=3)
ratios_list = []
correct_list = []

annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.4", fc="#22aa22", ec="#006622"),
                    fontsize=10, color="white")
annot.set_visible(False)

def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = line.contains(event)
        if cont:
            x = line.get_xdata()[ind["ind"][0]]
            y = line.get_ydata()[ind["ind"][0]]
            annot.xy = (x,y)
            annot.set_text(f"Ratio: {x:.3f}\nCorrect: {y}")
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", hover)
Cursor(ax, useblit=True, color='gray', linewidth=1, linestyle='--')

def load_correct_map(json_path):
    with open(json_path,"r",encoding="utf-8") as f:
        data = json.load(f)
    mp = {}
    for item in data:
        idx = item.get("index")
        ans = item.get("correct_option","").strip().upper()
        if idx and ans in ("A","B","C","D"):
            mp[int(idx)] = ans
    return mp

def get_db_index(p):
    m = re.search(r"compare_50_(\d+)\.db", p)
    return int(m.group(1)) if m else None

def get_predictions(raw_dfs, ratio):
    return run_batch_analysis(raw_dfs, ratio)

def count_total_correct(ratio, correct_map, raw_dfs):
    res = get_predictions(raw_dfs, ratio)
    right = 0
    for df in raw_dfs:
        path = df.attrs["db_path"]
        idx = get_db_index(path)
        if idx not in correct_map: continue
        true = correct_map[idx]
        name = os.path.basename(path)
        pred = None
        for item in res:
            if item["database"] == name:
                pred = max(("A","B","C","D"), key=lambda k: item[k])
                break
        if pred == true:
            right +=1
    return right

def update_graph(r,c):
    ratios_list.append(r)
    correct_list.append(c)
    line.set_data(ratios_list, correct_list)
    ax.relim()
    ax.autoscale_view(True, True, True)
    plt.draw()
    plt.pause(0.01)

def save_md(res):
    with open(OUTPUT_MD,"w",encoding="utf-8") as f:
        f.write("# Mean Line Ratio Accuracy Curve\n| mean_line_ratio | Correct Count |\n|----------------|----------|\n")
        for r,c in res:
            f.write(f"| {r:.3f} | {c} |\n")

if __name__ == "__main__":
    paths = get_all_db_files(PATTERN)
    raw_dfs = [load_single_db(p) for p in paths]
    correct_map = load_correct_map(JSON_FILE)

    ratio = START_RATIO
    results = []
    plt.ion()
    while ratio <= END_RATIO + 1e-9:
        r = round(ratio,3)
        cor = count_total_correct(r, correct_map, raw_dfs)
        results.append((r,cor))
        update_graph(r,cor)
        save_md(results)
        print(f"ratio={r:.3f} correct={cor}")
        ratio += STEP

    plt.ioff()
    ax.set_xlim(START_RATIO, END_RATIO)
    ax.margins(y=0.1)
    fig.tight_layout()
    plt.savefig(IMAGE_FILE, dpi=300, bbox_inches="tight")
    plt.show()