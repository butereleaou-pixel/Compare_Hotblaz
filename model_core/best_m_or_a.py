from data_loader import get_all_db_files, load_single_db
from mul_original import analyze_all_dfs
from pipeline_input import run_data_pipeline_once
from prediction_module import run_prediction
from mean_line_ratio import run_batch_analysis
import numpy as np   # ✅ 这里补上缺失的 np
import time
import sys
from itertools import cycle
import threading

# ===================== 【全局迭代设置】=====================
START = 0.01    # 起始模型权重
END = 0.99      # 结束模型权重
STEP = 0.01     # 步长

# ===================== 动画函数 =====================
def loading_animation(text="loading", event=None):
    symbols = cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
    while not (event and event.is_set()):
        sys.stdout.write(f'\r{text} {next(symbols)}  ')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f'\r✅ {text.replace("...", "")} 完成！\n')
    sys.stdout.flush()

# ===================== 带动画的执行函数 =====================
def run_with_animation(func, text, *args, **kwargs):
    event = threading.Event()
    t = threading.Thread(target=loading_animation, args=(text, event))
    t.daemon = True
    t.start()

    result = func(*args, **kwargs)

    event.set()
    t.join()
    return result

# ===================== 融合 + 判决 =====================
def fuse_confidences(model_res, rule_res, model_w, rule_w):
    fused = []
    rule_dict = {item["database"]: item for item in rule_res}

    for m_item in model_res:
        db_full = m_item["database"]
        db_name = db_full.split("\\")[-1].split("/")[-1]
        r_item = rule_dict.get(db_name)

        if not r_item:
            fused.append(m_item)
            continue

        A = m_item["A"] * model_w + r_item["A"] * rule_w
        B = m_item["B"] * model_w + r_item["B"] * rule_w
        C = m_item["C"] * model_w + r_item["C"] * rule_w
        D = m_item["D"] * model_w + r_item["D"] * rule_w

        scores = {"A": A, "B": B, "C": C, "D": D}
        final_answer = max(scores, key=scores.get)

        fused.append({
            "database": db_full,
            "A": round(A, 4),
            "B": round(B, 4),
            "C": round(C, 4),
            "D": round(D, 4),
            "final_answer": final_answer
        })
    return fused

# ===================== 【一次性预加载所有基础结果】=====================
PATTERN = "../database/2026_*/compare_50*.db"
paths = get_all_db_files(PATTERN)
raw_dfs = [load_single_db(p) for p in paths]

df_input = analyze_all_dfs(raw_dfs)
processed_df = run_data_pipeline_once(df_input, None)

# 只推理一次！
model_results = run_with_animation(run_prediction, "模型推理中...", processed_df, temperature=1.0, topk=2)
rule_results = run_with_animation(run_batch_analysis, "规则分析中...", raw_dfs)

total_dbs = len(model_results)
print(f"\n✅ 基础数据加载完成！总计 {total_dbs} 个数据库")

# ===================== 🔥 权重迭代遍历 + 统计 A 占比 =====================
print("\n" + "="*80)
print("📌 开始迭代权重：模型权重 [0.01 → 0.99]")
print("="*80)

# 保存所有结果
final_stats = []

for w in [round(x, 2) for x in list(np.arange(START, END+STEP, STEP))]:
    MODEL_W = w
    RULE_W = round(1 - w, 2)

    print(f"\n--- 迭代：模型={MODEL_W:.2f} | 规则={RULE_W:.2f} ---")

    # 融合
    fused = run_with_animation(fuse_confidences, "置信度融合中...", model_results, rule_results, MODEL_W, RULE_W)

    # 统计答案 A
    count_A = sum(1 for item in fused if item["final_answer"] == "A")
    ratio_A = round(count_A / total_dbs, 4) * 100

    final_stats.append({
        "model_w": MODEL_W,
        "rule_w": RULE_W,
        "total_db": total_dbs,
        "answer_A_count": count_A,
        "answer_A_ratio(%)": ratio_A
    })

    print(f"   → 最终答案为 A：{count_A} 个 / 占比 {ratio_A:.2f}%")

# ===================== 📊 最终输出完整统计 =====================
print("\n" + "="*80)
print("📊 【最终权重迭代统计】所有组合的 Answer A 占比")
print("="*80)
for stat in final_stats:
    print(f"模型 {stat['model_w']:.2f} | 规则 {stat['rule_w']:.2f} | A 占比: {stat['answer_A_ratio(%)']:.2f}%")