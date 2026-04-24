import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from scipy.stats import skew, kurtosis
from sklearn.mixture import GaussianMixture
from collections import defaultdict
from model import AnswerModel
from config import *
import glob
import re
import os

# ===================== 固定配置 =====================
DB_FOLDER = "../database/2026_3_29_2/compare_50*.db"
TABLES = ["sample", "pre_sample"]
ANSWER_LIST = ["A", "B", "C", "D"]
ans_map = {0: "A", 1: "B", 2: "C", 3: "D"}
idx_map = {"A": 0, "B": 1, "C": 2, "D": 3}

# ===================== 融合比例 =====================
WEIGHT_MODEL = 1
WEIGHT_RULE  = 0

# ===================== ✅ NEW: 温度 & TopK 参数 =====================
TEMPERATURE   = 1    # 越大越平滑（推荐1.5~3.0）
TOP_K         = 2      # 只保留最高K个概率
# ====================================================================

# ===================== 1. 数据库读取与特征计算 =====================
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
        "Count": len(vals), "Mean": vals.mean(), "Median": vals.median(),
        "Std": vals.std(), "Variance": vals.var(), "Min": vals.min(),
        "Max": vals.max(), "Range": vals.max() - vals.min(),
        "Skewness": skew(vals), "Kurtosis": kurtosis(vals)
    }

def calc_global_stats(df):
    vals = pd.to_numeric(df["eucli_dis"], errors="coerce").dropna()
    return {
        "Count": len(vals), "Mean": vals.mean(), "Median": vals.median(),
        "Std": vals.std(), "Variance": vals.var(), "Min": vals.min(),
        "Max": vals.max(), "Range": vals.max() - vals.min(),
        "Skewness": skew(vals), "Kurtosis": kurtosis(vals)
    }

def process_single_db_features(db_path):
    df = load_db(db_path)
    df["ans"] = df["answer"].apply(extract_ans)
    df["eucli_dis"] = pd.to_numeric(df["eucli_dis"], errors="coerce")
    df = df.dropna(subset=["eucli_dis", "ans"])

    ans_rows = []
    for ans in ANSWER_LIST:
        stat = calc_group_stats(df, ans)
        if stat:
            ans_rows.append(stat)
        else:
            dummy = {k:0 for k in ["Answer","Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]}
            dummy["Answer"] = f"ANSWER {ans}"
            ans_rows.append(dummy)

    y = df["eucli_dis"].values.reshape(-1, 1)
    n_comp = max(1, len([a for a in ANSWER_LIST if f"ANSWER {a}" in [r["Answer"] for r in ans_rows]]))
    gmm = GaussianMixture(n_components=n_comp, random_state=0)
    gmm.fit(y)
    df["gmm_comp"] = gmm.predict(y)
    cross = pd.crosstab(df["gmm_comp"], df["ans"])

    ans_to_comp = {}
    for comp in cross.index:
        best_ans = cross.loc[comp].idxmax()
        ans_to_comp[best_ans] = comp

    for row in ans_rows:
        ans_label = row["Answer"].split()[-1]
        if ans_label in ans_to_comp:
            c = ans_to_comp[ans_label]
            row["GMM_pi"] = gmm.weights_[c]
            row["GMM_mu"] = gmm.means_[c][0]
            row["GMM_sigma"] = np.sqrt(gmm.covariances_[c][0][0])
        else:
            row["GMM_pi"] = np.nan
            row["GMM_mu"] = np.nan
            row["GMM_sigma"] = np.nan

    global_row = calc_global_stats(df)
    exclude = ["Answer", "GMM_pi", "GMM_mu", "GMM_sigma"]
    for row in ans_rows:
        for k in row:
            if k in exclude or k not in global_row:
                continue
            gv = global_row[k]
            rv = row[k]
            if isinstance(gv, (int, float)) and gv != 0:
                row[k] = round(rv / gv, 4)
            else:
                row[k] = 0

    ans_rows = sorted(ans_rows, key=lambda x: x["Answer"])
    true_label = 0

    feat_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis","GMM_pi","GMM_mu","GMM_sigma"]
    feats = []
    for r in ans_rows:
        row_feats = []
        for c in feat_cols:
            v = r.get(c, 0)
            if pd.isna(v):
                v = 0
            row_feats.append(float(v))
        feats.append(row_feats)
    feats = np.array(feats, dtype=np.float32)

    for i in range(4):
        pi, mu, sigma = feats[i, -3:]
        if np.isnan(pi) or np.isnan(mu) or np.isnan(sigma):
            pi, mu, sigma = 0.1, 100.0, 5.0
        mu = np.clip(mu, 1e-3, 1e6)
        sigma = np.clip(sigma, 1e-3, 1e6)
        feats[i, -3:] = [pi, np.log(mu), np.log(sigma)]

    feats = np.nan_to_num(feats, 0.0, 1e3, -1e3)
    g_mean = feats.mean(0, keepdims=True)
    g_std = feats.std(0, keepdims=True) + 1e-6
    feats = (feats - g_mean) / g_std
    feats = np.clip(feats, -5, 5)

    return feats, true_label

# ===================== 2. 规则分析函数 =====================
def analyze_answer_list_scored(answer_list_str, average_eucli_dis):
    ignore_count = 3
    target = average_eucli_dis
    DIFF_THRESHOLD = 1.0

    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*ANSWER:\s*([A-D])\b"
    matches = re.findall(pattern, answer_list_str)
    if not matches:
        return np.zeros(4)

    stat = defaultdict(lambda: {"total": 0.0, "count": 0})
    for score_str, ans in matches:
        score = float(score_str)
        stat[ans]["total"] += score
        stat[ans]["count"] += 1

    result = {}
    for ans, data in stat.items():
        if data["count"] < ignore_count:
            continue
        avg = round(data["total"] / data["count"], 6)
        result[ans] = {
            "count": data["count"],
            "avg_score": avg,
            "diff": abs(avg - target)
        }

    if len(result) == 0:
        return np.zeros(4)

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

    scores = np.zeros(4)
    diff_list = [item["diff"] for item in candidates.values()]
    max_diff = max(diff_list) if diff_list else 1e-9

    for ans, info in candidates.items():
        score = 1.0 - (info["diff"] / max_diff)
        scores[idx_map[ans]] = round(score, 6)

    return scores

def calculate_average_eucli_dis(conn):
    total_sum = 0
    total_count = 0
    for t in TABLES:
        cursor = conn.cursor()
        cursor.execute(f"SELECT SUM(eucli_dis), COUNT(*) FROM {t} WHERE eucli_dis IS NOT NULL")
        r = cursor.fetchone()
        if r[0] and r[1]:
            total_sum += r[0]
            total_count += r[1]
    return total_sum / total_count if total_count > 0 else 1.0

def pick_average_dis(conn, target):
    cursor = conn.cursor()
    q = """
    SELECT answer, eucli_dis FROM (
        SELECT answer, eucli_dis, ABS(eucli_dis-?) AS d FROM sample
        UNION ALL SELECT answer, eucli_dis, ABS(eucli_dis-?) AS d FROM pre_sample
    ) ORDER BY d ASC LIMIT 15
    """
    cursor.execute(q, (target, target))
    rows = cursor.fetchall()
    lines = []
    for i, (ans, dis) in enumerate(rows):
        if ans:
            lines.append(f"| {dis:.6f} | {ans.strip()}")
    return "\n".join(lines)

def get_rule_confidence(db_path):
    conn = sqlite3.connect(db_path)
    avg = calculate_average_eucli_dis(conn)
    ans_list = pick_average_dis(conn, avg)
    scores = analyze_answer_list_scored(ans_list, avg)
    conn.close()
    return scores

# ===================== 3. 模型加载 =====================
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feat_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis","GMM_pi","GMM_mu","GMM_sigma"]
    model = AnswerModel(len(feat_cols)).to(device)
    if os.path.exists("best_final_model.pth"):
        model.load_state_dict(torch.load("model/best_final_model.pth", map_location=device))
    model.eval()
    return model, device

# ===================== 4. ✅ 融合预测（Temperature + TopK）=====================
def fuse_predict(model, device, feats, rule_scores):
    x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(device)
    mask = torch.ones(1, 4, dtype=torch.float32).to(device)

    with torch.no_grad():
        logits = model(x, mask)[0]

    # -----------------------
    # ✅ Step1: Temperature
    # -----------------------
    logits_scaled = logits / TEMPERATURE

    # -----------------------
    # ✅ Step2: Top-K Mask
    # -----------------------
    topk_vals, topk_indices = torch.topk(logits_scaled, k=TOP_K)
    mask = torch.zeros_like(logits_scaled)
    mask[topk_indices] = 1.0
    logits_masked = logits_scaled * mask

    # -----------------------
    # ✅ Step3: Softmax
    # -----------------------
    model_probs = F.softmax(logits_masked, dim=0).cpu().numpy()

    # -----------------------
    # ✅ Fusion
    # -----------------------
    fused = WEIGHT_MODEL * model_probs + WEIGHT_RULE * rule_scores
    final_idx = np.argmax(fused)
    return final_idx, fused[final_idx], fused

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 一体化融合预测（Temperature + TopK + 固定顺序A）")
    print("=" * 80)

    db_files = sorted(glob.glob(DB_FOLDER))
    db_files = [f for f in db_files if not f.endswith(("compare_50.db", "compare_50_panel.db"))]

    model, device = load_model()
    total = 0
    correct = 0

    for db in db_files:
        total += 1
        feats, true_idx = process_single_db_features(db)
        rule_scores = get_rule_confidence(db)
        pred_idx, conf, full_conf = fuse_predict(model, device, feats, rule_scores)

        true_ans = ans_map[true_idx]
        pred_ans = ans_map[pred_idx]
        ok = "✅ YES" if pred_idx == true_idx else "❌ NO"
        if ok == "✅ YES":
            correct +=1

        print(f"📂 DB: {os.path.basename(db)}")
        print(f"🎯 True: {true_ans} | Pred: {pred_ans} | Conf: {conf:.4f} | {ok}")
        print(f"📊 Fusion Conf: A={full_conf[0]:.3f} B={full_conf[1]:.3f} C={full_conf[2]:.3f} D={full_conf[3]:.3f}")
        print("-" * 80)

    print("\n" * 1)
    print("=" * 80)
    print(f"🎯 最终结果：Total={total} Correct={correct} Accuracy={correct/total:.2%}")
    print("=" * 80)