import numpy as np
import re
from collections import defaultdict
import json
import os

# ===================== 核心解析函数 =====================
def analyze_answer_list(answer_list_str, average_eucli_dis):
    ignore_count = 3
    target = average_eucli_dis
    DIFF_THRESHOLD = 1.0
    SAFE_MAX = 1e8

    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*ANSWER:\s*([A-D])\b"
    matches = re.findall(pattern, answer_list_str)
    if not matches:
        return {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}

    stat = defaultdict(lambda: {"total": 0.0, "count": 0})
    for score_str, ans in matches:
        score = float(score_str)
        stat[ans]["total"] += score
        stat[ans]["count"] += 1

    result = {}
    for ans, data in stat.items():
        if data["count"] < ignore_count:
            continue
        avg = data["total"] / data["count"]
        dis = abs(avg - target)
        result[ans] = {
            "dis": round(dis, 6),
            "count": data["count"]
        }

    if not result:
        return {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}

    sorted_by_count = sorted(result.items(), key=lambda x: x[1]["count"], reverse=True)
    top2 = [item[0] for item in sorted_by_count[:2]]

    top2_below_threshold = all(result[ans]["dis"] < DIFF_THRESHOLD for ans in top2)
    candidates = {ans: result[ans] for ans in top2} if top2_below_threshold else result

    ans_list = list(candidates.keys())
    dis_list = [candidates[ans]["dis"] for ans in ans_list]
    scores = [SAFE_MAX if d < 1e-6 else 1.0 / d for d in dis_list]

    scores_np = np.array(scores)
    exp_scores = np.exp(scores_np - np.max(scores_np))
    softmax_scores = (exp_scores / exp_scores.sum()).tolist()

    final = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}
    for i, ans in enumerate(ans_list):
        if ans in final:
            final[ans] = round(softmax_scores[i], 4)
    return final

# ===================== 从 DF 生成列表 =====================
def pick_average_dis_from_df(raw_df, average_eucli_dis):
    df = raw_df.copy()
    df["distance"] = abs(df["eucli_dis"] - average_eucli_dis)
    df = df.sort_values("distance").head(15)
    lines = ["=" * 100, f"{'RANK':<6} | {'CLOSE_SCORE':<15} | ANSWER", "=" * 100]
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        ans = row["ans"]
        dis = row["eucli_dis"]
        lines.append(f"{idx:<6} | {dis:<15.6f} | ANSWER: {ans}")
    lines.append("=" * 100)
    return "\n".join(lines)

# ===================== 计算平均值 =====================
def calculate_average_eucli_dis_from_df(raw_df):
    vals = raw_df["eucli_dis"].dropna()
    return vals.mean() if len(vals) > 0 else 0.0

# ===================== 处理单个 DF（直接传 ratio） =====================
def process_single_df(raw_df, mean_line_ratio):
    try:
        full_path = raw_df.attrs.get("db_path", "unknown")
        db_name = os.path.basename(full_path)

        # ✅ 直接使用传入的 ratio，不再读 config！
        avg_dis = calculate_average_eucli_dis_from_df(raw_df) * mean_line_ratio
        answer_list_str = pick_average_dis_from_df(raw_df, avg_dis)
        confs = analyze_answer_list(answer_list_str, avg_dis)

        return {
            "database": db_name,
            "A": confs["A"],
            "B": confs["B"],
            "C": confs["C"],
            "D": confs["D"]
        }
    except Exception as e:
        return {
            "database": "error",
            "A": 0.0,
            "B": 0.0,
            "C": 0.0,
            "D": 0.0
        }

# ===================== 批量处理（✅ 接收 ratio 参数！） =====================
def run_batch_analysis(raw_dfs, mean_line_ratio):
    return [process_single_df(df, mean_line_ratio) for df in raw_dfs]