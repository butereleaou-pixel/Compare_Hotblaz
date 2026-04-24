from data_loader import get_all_db_files, load_single_db
from mul_original import analyze_all_dfs
from pipeline_input import run_data_pipeline_once
from prediction_module import run_prediction
from mean_line_ratio import run_batch_analysis
import numpy as np
import time
import sys
import json
import os
import re
from itertools import cycle
import threading

# ===================== 【全局迭代设置】=====================
START = 0.01
END = 0.99
STEP = 0.01

# ===================== 加载正确答案 JSON =====================
CHECKPOINT_PATH = "../test_record/gpqa_checkpoint.json"

def load_correct_answers(path):
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    db_to_correct = {}
    for r in records:
        idx = r["index"]
        cor = r["correct_option"].strip().upper()
        db_name = f"compare_50_{idx}.db"
        db_to_correct[db_name] = cor
    return db_to_correct

correct_map = load_correct_answers(CHECKPOINT_PATH)

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
def fuse_and_judge(model_res, rule_res, correct_map, model_w, rule_w):
    fused = []
    rule_dict = {os.path.basename(item["database"]): item for item in rule_res}
    total = 0
    correct = 0

    for m_item in model_res:
        db_full = m_item["database"]
        db_name = os.path.basename(db_full)
        r_item = rule_dict.get(db_name)

        if r_item:
            A = m_item["A"] * model_w + r_item["A"] * rule_w
            B = m_item["B"] * model_w + r_item["B"] * rule_w
            C = m_item["C"] * model_w + r_item["C"] * rule_w
            D = m_item["D"] * model_w + r_item["D"] * rule_w
        else:
            A, B, C, D = m_item["A"], m_item["B"], m_item["C"], m_item["D"]

        scores = {"A": A, "B": B, "C": C, "D": D}
        final_answer = max(scores, key=scores.get)
        correct_ans = correct_map.get(db_name, None)
        is_correct = (final_answer == correct_ans) if correct_ans else False

        if correct_ans:
            total += 1
            if is_correct:
                correct += 1

        fused.append({
            "database": db_full,
            "A": round(A, 4),
            "B": round(B, 4),
            "C": round(C, 4),
            "D": round(D, 4),
            "final_answer": final_answer,
            "correct_option": correct_ans,
            "is_correct": is_correct
        })

    accuracy = (correct / total) * 100 if total > 0 else 0.0
    return fused, total, correct, accuracy

# ===================== 【一次性预加载所有数据 —— 完全和你正常代码一样】=====================
PATTERN = "../database/2026_4_2_2/compare_50*.db"
paths = get_all_db_files(PATTERN)
raw_dfs = [load_single_db(p) for p in paths]

df_input = analyze_all_dfs(raw_dfs)
processed_df = run_data_pipeline_once(df_input, None)

# 模型 & 规则只运行一次
model_results = run_with_animation(run_prediction, "模型推理中...", processed_df, temperature=1.0, topk=2)
rule_results = run_with_animation(run_batch_analysis, "规则分析中...", raw_dfs)

print(f"\n✅ 基础数据加载完成！")

# ===================== 权重迭代遍历（核心改动）=====================
print("\n" + "="*80)
print("📌 开始迭代权重：模型权重 [0.01 → 0.99]")
print("="*80)

final_stats = []

for w in [round(x, 2) for x in list(np.arange(START, END + STEP, STEP))]:
    MODEL_W = w
    RULE_W = round(1 - w, 2)

    print(f"\n--- 迭代：模型={MODEL_W:.2f} | 规则={RULE_W:.2f} ---")

    # 只迭代融合，不重复跑模型
    fused, total_cnt, correct_cnt, acc = run_with_animation(
        fuse_and_judge,
        "置信度融合中...",
        model_results,
        rule_results,
        correct_map,
        MODEL_W,
        RULE_W
    )

    final_stats.append({
        "model_w": MODEL_W,
        "rule_w": RULE_W,
        "total": total_cnt,
        "correct": correct_cnt,
        "accuracy(%)": acc
    })

    print(f"   → 正确：{correct_cnt} / {total_cnt} | 准确率：{acc:.2f}%")

# ===================== 最终输出 =====================
print("\n" + "="*80)
print("📊 权重迭代最终统计")
print("="*80)
for stat in final_stats:
    print(f"模型 {stat['model_w']:.2f} | 规则 {stat['rule_w']:.2f} | 准确率: {stat['accuracy(%)']:.2f}%")

