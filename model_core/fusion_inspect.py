from data_loader import get_all_db_files, load_single_db
from mul_original import analyze_all_dfs
from pipeline_input import run_data_pipeline_once
from prediction_module import run_prediction
from mean_line_ratio import run_batch_analysis
import time
import sys
from itertools import cycle

# ===================== 【可调权重】=====================
MODEL_WEIGHT = 0.36    # 模型权重
RULE_WEIGHT = 0.64    # 规则权重

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
    import threading
    event = threading.Event()
    t = threading.Thread(target=loading_animation, args=(text, event))
    t.daemon = True
    t.start()

    # 后台执行任务
    result = func(*args, **kwargs)

    # 结束动画
    event.set()
    t.join()
    return result

# ===================== 主流程 =====================
PATTERN = "../database/2026_3_28/compare_50*.db"
paths = get_all_db_files(PATTERN)
raw_dfs = [load_single_db(p) for p in paths]

# 1. 模型预测（播放动画）
df_input = analyze_all_dfs(raw_dfs)
processed_df = run_data_pipeline_once(df_input, None)

model_results = run_with_animation(
    run_prediction,
    "模型推理中...",
    processed_df,
    temperature=1.0,
    topk=2
)

# 输出模型结果
print("\n🔍 模型预测结果：")
for item in model_results:
    print(item)

# 2. 规则分析（播放动画）
rule_results = run_with_animation(
    run_batch_analysis,
    "规则分析中...",
    raw_dfs
)

# 输出规则结果
print("\n📊 规则分析结果：")
for item in rule_results:
    print(item)

# ===================== 融合 + 判决 =====================
def fuse_confidences(model_res, rule_res, model_w=0.75, rule_w=0.25):
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

# 3. 融合结果（播放动画）
final_results = run_with_animation(
    fuse_confidences,
    "置信度融合中...",
    model_results,
    rule_results,
    MODEL_WEIGHT,
    RULE_WEIGHT
)

# 输出最终结果
print("\n✅ 最终融合结果：")
for item in final_results:
    print(item)




