from data_loader import get_all_db_files, load_single_db
from mul_original import analyze_all_dfs
from pipeline_input import run_data_pipeline_once
from prediction_module import run_prediction
from mean_line_ratio import run_batch_analysis
import time
import sys
import json
from itertools import cycle

# ==============================================
# 🔥 所有固定配置、路径、变量 全部集中在这里（只改这里）
# ==============================================
# 路径配置
DB_PATTERN          = "../database/2026_3_29_2/compare_50*.db"
ANSWER_JSON_PATH    = "../test_record/gpqa_checkpoint_alla.json"

# 融合权重
MODEL_WEIGHT        = 0.36    # 模型权重
RULE_WEIGHT         = 0.64    # 规则权重

# 模型参数
MODEL_TEMPERATURE   = 1.0
MODEL_TOPK          = 2

# ==============================================
# 动画函数
# ==============================================
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
    result = func(*args, **kwargs)
    event.set()
    t.join()
    return result

# ===================== 核心辅助函数（100%兼容你的路径格式）=====================
# 从database字段提取题目index和正确答案
def get_question_info(item, answer_map):
    db_str = item["database"]
    # 兼容带路径和纯文件名两种格式
    db_name = db_str.split("\\")[-1].split("/")[-1]
    try:
        # 从 compare_50_xxx.db 提取数字index
        idx = int(db_name.replace(".db", "").split("_")[-1])
        gt = answer_map.get(idx, None)
        return idx, gt
    except:
        return None, None

# 从置信度提取预测选项
def get_predict_choice(item):
    option_scores = {k: item[k] for k in ["A", "B", "C", "D"] if k in item}
    return max(option_scores, key=option_scores.get) if option_scores else None

# ===================== 主流程 =====================
paths = get_all_db_files(DB_PATTERN)
raw_dfs = [load_single_db(p) for p in paths]

# 加载正确答案（提前加载，避免循环内重复操作）
correct_answer_map = {}
try:
    with open(ANSWER_JSON_PATH, "r", encoding="utf-8") as f:
        checkpoint_data = json.load(f)
    correct_answer_map = {item["index"]: item["correct_option"] for item in checkpoint_data}
    print("✅ 正确答案库加载成功！")
except Exception as e:
    print(f"⚠️ 正确答案加载失败: {e}")

# 1. 模型预测
df_input = analyze_all_dfs(raw_dfs)
processed_df = run_data_pipeline_once(df_input, None)
model_results = run_with_animation(
    run_prediction,
    "模型推理中...",
    processed_df,
    temperature=MODEL_TEMPERATURE,
    topk=MODEL_TOPK
)

# 【模型结果：每一题强制显示对错】
print("\n🔍 模型预测结果（每题对错明细）：")
model_correct = 0
model_total = 0
for item in model_results:
    # 提取信息
    idx, gt = get_question_info(item, correct_answer_map)
    pred = get_predict_choice(item)
    is_correct = (gt is not None) and (pred == gt)
    
    # 统计
    if gt is not None:
        model_total += 1
        if is_correct:
            model_correct += 1
    
    # 【强制打印，绝对不会消失】
    status = "✅ Correct" if is_correct else "❌ Wrong" if gt is not None else "❓ No GT"
    gt_display = gt if gt else "N/A"
    print(f"{item} | 预测选项: {pred} | 正确答案: {gt_display} | {status}")

# 模型总正确率
if model_total > 0:
    print(f"\n🎯 模型预测总正确率: {model_correct}/{model_total} ({model_correct/model_total:.2%})")

# 2. 规则分析
rule_results = run_with_animation(
    run_batch_analysis,
    "规则分析中...",
    raw_dfs
)

# 【规则结果：每一题强制显示对错】
print("\n📊 规则分析结果（每题对错明细）：")
rule_correct = 0
rule_total = 0
for item in rule_results:
    # 提取信息
    idx, gt = get_question_info(item, correct_answer_map)
    pred = get_predict_choice(item)
    is_correct = (gt is not None) and (pred == gt)
    
    # 统计
    if gt is not None:
        rule_total += 1
        if is_correct:
            rule_correct += 1
    
    # 【强制打印，绝对不会消失】
    status = "✅ Correct" if is_correct else "❌ Wrong" if gt is not None else "❓ No GT"
    gt_display = gt if gt else "N/A"
    print(f"{item} | 预测选项: {pred} | 正确答案: {gt_display} | {status}")

# 规则总正确率
if rule_total > 0:
    print(f"\n🎯 规则分析总正确率: {rule_correct}/{rule_total} ({rule_correct/rule_total:.2%})")

# ===================== 融合 + 判决 =====================
def fuse_confidences(model_res, rule_res, model_w=0.75, rule_w=0.25):
    fused = []
    # 规则结果用纯文件名做key，匹配模型的文件名
    rule_dict = {item["database"].split("\\")[-1].split("/")[-1]: item for item in rule_res}

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

# 3. 融合结果
final_results = run_with_animation(
    fuse_confidences,
    "置信度融合中...",
    model_results,
    rule_results,
    MODEL_WEIGHT,
    RULE_WEIGHT
)

# 【融合结果：每一题强制显示对错】
print("\n✅ 最终融合结果（每题对错明细）：")
fusion_correct = 0
fusion_total = 0
for item in final_results:
    # 提取信息
    idx, gt = get_question_info(item, correct_answer_map)
    pred = item["final_answer"]
    is_correct = (gt is not None) and (pred == gt)
    
    # 统计
    if gt is not None:
        fusion_total += 1
        if is_correct:
            fusion_correct += 1
    
    # 【强制打印，绝对不会消失】
    status = "✅ Correct" if is_correct else "❌ Wrong" if gt is not None else "❓ No GT"
    gt_display = gt if gt else "N/A"
    print(f"{item} | 正确答案: {gt_display} | {status}")

# 融合总正确率
if fusion_total > 0:
    print(f"\n🏆 最终融合总正确率: {fusion_correct}/{fusion_total} ({fusion_correct/fusion_total:.2%})")




