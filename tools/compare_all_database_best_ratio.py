#Compare all the curves how different mean_line_ratio in each
#test behaviour


import re
import glob
import matplotlib.pyplot as plt
import os
from matplotlib.ticker import FormatStrFormatter

# ===================== 配置 =====================
# 👇 这里改成匹配所有日期：3_* 、4_* 全部能读到
FILE_PATTERN = f"result_path/test_result_*_A_stat.md"  
OUTPUT_FIGURE = "combined_ratio_A_curve.png"

COLORS = [
    "#1f77b4", "#ff4b5c", "#2ca02c", "#ff7f0e", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

# ===================== 读取 MD 数据 =====================
def read_md_data(file_path):
    ratios = []
    counts = []
    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*(\d+)\s*\|"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.search(pattern, line)
                if m:
                    ratios.append(float(m.group(1)))
                    counts.append(int(m.group(2)))
        return ratios, counts
    except:
        return [], []

# ===================== 交互式悬浮显示（蓝色底白字） =====================
def create_hover_annotation(fig, ax, lines, all_data):
    annot = ax.annotate(
        "", xy=(0,0), xytext=(10,10), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", fc="#3377ff", ec="#003399", lw=1),
        fontsize=10, color="white"
    )
    annot.set_visible(False)

    def on_mouse_move(event):
        vis = annot.get_visible()
        if event.inaxes != ax:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        found = False
        for i, line in enumerate(lines):
            xd, yd = line.get_data()
            for x, y in zip(xd, yd):
                if abs(event.xdata - x) < 0.0015 and abs(event.ydata - y) < 0.3:
                    annot.xy = (x, y)
                    fname = os.path.basename(all_data[i]["file"])
                    text = f"File: {fname}\nRatio: {x:.3f}\nA count: {y}"
                    annot.set_text(text)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    found = True
                    return
        if not found and vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)

# ===================== 主程序 =====================
if __name__ == "__main__":
    # 👇 自动匹配所有 test_result_*_A_stat.md 文件
    files = sorted(glob.glob(FILE_PATTERN))
    if not files:
        print("❌ No file found")
        exit()

    print(f"✅ 读取到 {len(files)} 个文件：")
    for f in files:
        print(f"   - {os.path.basename(f)}")

    fig, ax = plt.subplots(figsize=(14,7))
    ax.set_title("Mean Line Ratio vs Answer A Count (Multi-file combined)", fontsize=16)
    ax.set_xlabel("Mean Line Ratio", fontsize=12)
    ax.set_ylabel("Total A Count", fontsize=12)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))

    lines = []
    all_data = []

    for i, f in enumerate(files):
        r, c = read_md_data(f)
        if not r: continue
        color = COLORS[i % len(COLORS)]
        label = os.path.basename(f)
        line, = ax.plot(r, c, linewidth=2.5, color=color, label=label)
        lines.append(line)
        all_data.append({"file": f, "x": r, "y": c})

    # 自动适应 + 顶部留白，防止数值溢出
    ax.relim()
    ax.autoscale_view(True, True, True)
    ax.margins(y=0.1)

    ax.legend(loc="best", fontsize=10)
    create_hover_annotation(fig, ax, lines, all_data)
    plt.tight_layout()

    plt.savefig(OUTPUT_FIGURE, dpi=300, bbox_inches='tight')
    print(f"\n✅ Image saved: {OUTPUT_FIGURE}")
    
    plt.show()