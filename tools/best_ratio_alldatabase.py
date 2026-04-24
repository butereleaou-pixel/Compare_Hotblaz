#find best mean ratio , for all test

import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# ===================== CONFIG =====================
FILE_PATTERN = "result_path/test_result_*_acc_stat.md"
START = 0.85
END = 1.10
STEP = 0.01

# ===================== Read Data =====================
def read_single_md(file):
    data = {}
    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*(\d+)\s*\|"
    try:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                m = re.search(pattern, line)
                if m:
                    ratio = round(float(m.group(1)), 3)
                    count = int(m.group(2))
                    data[ratio] = count
    except:
        pass
    return data

# ===================== Mouse Hover (Blue background white text) =====================
def create_hover(fig, ax, line, ratios, totals, diffs, scores):
    annot = ax.annotate(
        "", xy=(0,0), xytext=(12,12), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", fc="#3377ff", ec="#003399", lw=1),
        fontsize=10, color="white"
    )
    annot.set_visible(False)

    def on_move(event):
        vis = annot.get_visible()
        if event.inaxes != ax:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        for i, r in enumerate(ratios):
            if abs(event.xdata - r) < 0.008:
                s = scores[i]
                t = totals[i]
                d = diffs[i]
                annot.xy = (r, s)
                txt = (f"Ratio: {r:.3f}\n"
                       f"Total A: {t}\n"
                       f"Sum diff: {d}\n"
                       f"Score: {s}")
                annot.set_text(txt)
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
        if vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)

# ===================== Main Program =====================
if __name__ == "__main__":
    files = sorted(glob.glob(FILE_PATTERN))
    if not files:
        print("❌ No files")
        exit()

    all_data = {}
    file_max = {}
    for f in files:
        d = read_single_md(f)
        all_data[f] = d
        file_max[f] = max(d.values()) if d else 0

    # Exhaustive search 0.85 ~ 1.10, step 0.01
    ratios = np.arange(START, END + 1e-6, STEP)
    ratios = [round(r,3) for r in ratios]

    total_A_list = []
    sum_diff_list = []
    score_list = []

    for r in ratios:
        total = 0
        sum_d = 0
        for f in files:
            val = all_data[f].get(r, 0)
            total += val
            sum_d += (file_max[f] - val)
        score = total - sum_d

        total_A_list.append(total)
        sum_diff_list.append(sum_d)
        score_list.append(score)

    # Find optimal score
    best_idx = np.argmax(score_list)
    best_r = ratios[best_idx]
    best_score = score_list[best_idx]
    best_total = total_A_list[best_idx]
    best_sumd = sum_diff_list[best_idx]

    # ===================== New: Find minimum SUM DIFF =====================
    min_diff_idx = np.argmin(sum_diff_list)
    min_diff_r = ratios[min_diff_idx]
    min_diff_val = sum_diff_list[min_diff_idx]
    min_diff_total = total_A_list[min_diff_idx]
    min_diff_score = score_list[min_diff_idx]

    # ===================== Print Output =====================
    print("="*70)
    print("🎯 Best Result (Max Total A - Sum Diff)")
    print("="*70)
    print(f"✅ Best ratio: {best_r:.3f}")
    print(f"✅ Total A: {best_total}")
    print(f"✅ Sum (max - current): {best_sumd}")
    print(f"✅ Final Score: {best_score}")
    print("\n📉 Minimum Sum Diff Result")
    print("="*70)
    print(f"✅ Min Sum Diff Ratio: {min_diff_r:.3f}")
    print(f"✅ Min Sum Diff Value: {min_diff_val}")
    print(f"✅ Total A at Min Diff: {min_diff_total}")
    print(f"✅ Score at Min Diff: {min_diff_score}")
    print("="*70)

    # Plot
    fig, ax = plt.subplots(figsize=(13,6))
    ax.set_title("Best Ratio: Total A - Sum(Max-Current)", fontsize=15)
    ax.set_xlabel("Mean Line Ratio", fontsize=12)
    ax.set_ylabel("Score = TotalA - SumDiff", fontsize=12)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))

    line, = ax.plot(ratios, score_list, 'b-o', linewidth=2.5, markersize=4)
    
    # ===================== New: Mark Min Sum Diff on plot =====================
    ax.scatter(min_diff_r, min_diff_score, 
               color='red', s=80, zorder=5, label=f'Min Sum Diff\nRatio={min_diff_r:.3f}\nVal={min_diff_val}')
    ax.legend(loc='best')
    
    create_hover(fig, ax, line, ratios, total_A_list, sum_diff_list, score_list)

    # Auto scale + top margin
    ax.relim()
    ax.autoscale_view(True,True,True)
    ax.margins(y=0.15)
    plt.tight_layout()

    plt.savefig("best_ratio_score_curve.png", dpi=300, bbox_inches='tight')
    plt.show()