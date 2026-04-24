import json
import requests
import re
import sqlite3
import glob
import os
import sys
import time
from itertools import cycle
from collections import defaultdict

# ===================== 批量遍历所有 DB 配置 =====================
date_str = "3_29_2"
DB_FILES = sorted(glob.glob(f"../database/2026_{date_str}/compare_50_*.db"))
OUTPUT_MD = f"test_result_{date_str}_2.md"

conn = None
cursor = None

# ===================== 核心解析函数 =====================
import re
from collections import defaultdict

def analyze_answer_list(answer_list_str, average_eucli_dis):
    # 固定配置
    ignore_count = 3
    target = average_eucli_dis
    DIFF_THRESHOLD = 1.0  # 差值阈值 <1.0 才启用TOP2规则

    # 1. 正则提取分数和答案
    pattern = r"\|\s*(\d+\.\d+)\s*\|\s*ANSWER:\s*([A-D])\b"
    matches = re.findall(pattern, answer_list_str)
    if not matches:
        return None, None, None

    # 2. 统计总分 & 次数
    stat = defaultdict(lambda: {"total": 0.0, "count": 0})
    for score_str, ans in matches:
        score = float(score_str)
        stat[ans]["total"] += score
        stat[ans]["count"] += 1

    # 3. 计算平均分 & 过滤掉 < ignore_count 的答案
    result = {}
    for ans, data in stat.items():
        count = data["count"]
        if count < ignore_count:
            continue  # 直接忽略次数不足的
        avg = round(data["total"] / count, 6)
        result[ans] = {
            "count": count,
            "avg_score": avg,
            "diff": abs(avg - target)  # 提前算好差值
        }

    if len(result) == 0:
        return result, None, None

    # ====================== 核心规则逻辑 ======================
    # 步骤A：按出现次数 降序 排序
    sorted_by_count = sorted(result.items(), key=lambda x: x[1]["count"], reverse=True)
    top2_names = [item[0] for item in sorted_by_count[:2]]  # 取次数前2的答案

    # 步骤B：判断 TOP2 的差值是否都 < 1.0
    top2_below_threshold = True
    for ans in top2_names:
        if result[ans]["diff"] >= DIFF_THRESHOLD:
            top2_below_threshold = False
            break

    # 步骤C：决定候选池
    if top2_below_threshold:
        # 情况1：TOP2 差值都 <1.0 → 只比较 TOP2
        candidates = {ans: result[ans] for ans in top2_names}
    else:
        # 情况2：否则 → 比较所有 >=ignore_count 的
        candidates = result

    # 步骤D：从候选池中找最接近的
    min_diff = float("inf")
    best_ans = None
    for ans, info in candidates.items():
        if info["diff"] < min_diff:
            min_diff = info["diff"]
            best_ans = ans

    return result, best_ans, min_diff

def loading_animation(text="loading", duration=2):
    symbols = cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
    end_time = time.time() + duration
    while time.time() < end_time:
        sys.stdout.write(f'\r{text} {next(symbols)}')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(text) + 2) + '\r')
    sys.stdout.flush()

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
    lines = []
    lines.append("=" * 100)
    lines.append(f"{'RANK':<6} | {'CLOSE_SCORE':<15} | ANSWER")
    lines.append("=" * 100)
    for idx, (answer, eucli_dis) in enumerate(rows, 1):
        if answer:
            lines.append(
                f"{idx:<6} | {eucli_dis:<15.6f} | {answer.strip()}"
            )
    lines.append("=" * 100)
    return "\n".join(lines)

def calculate_average_eucli_dis(conn, table_names):
    """Calculate the average eucli_dis across multiple tables."""
    cursor = conn.cursor()
    total_sum = 0
    total_count = 0
    
    for table_name in table_names:
        cursor.execute(f"SELECT SUM(eucli_dis), COUNT(*) FROM {table_name} WHERE eucli_dis IS NOT NULL")
        result = cursor.fetchone()
        if result[0] is not None and result[1] is not None:
            total_sum += result[0]
            total_count += result[1]
    
    return total_sum / total_count if total_count > 0 else 0.0
# ===================== 处理单个数据库 =====================
def process_single_db(db_path):
    global conn, cursor
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"\n==================================================")
        print(f"📂 正在处理：{db_path}")
        print(f"==================================================")

        with open('../config_adjust.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        mean_line_ratio = config['test']['mean_line_ratio']
        
        
        ignore_count = config['generate']['ignore_count']

        average_eucli_dis = calculate_average_eucli_dis(conn, ['sample', 'pre_sample']) * mean_line_ratio
        answer_list = pick_average_dis(conn, average_eucli_dis)

        print(f"== answer_list:\n{answer_list}")

        # ===================== 新版解析（无API） =====================
        stats, best_ans, min_diff = analyze_answer_list(answer_list, average_eucli_dis)
        print(f"== mean_close_score:{average_eucli_dis}")
        print("=== 统计结果 ===")
        for ans, info in stats.items():
            print(f"{ans}: 出现 {info['count']} 次, 平均分 {info['avg_score']}")
        print(f"\n最接近 {average_eucli_dis} 的答案：{best_ans}，差值：{min_diff:.6f}")

        # ===================== 返回正确字段 =====================
        return {
            "db": db_path,
            "average_eucli_dis": round(average_eucli_dis, 6),
            "answer_list": answer_list,
            "stats": stats,
            "best_ans": best_ans,
            "min_diff": round(min_diff, 6)
        }

    except Exception as e:
        print(f"❌ 处理 {db_path} 出错：{e}")
        return None
    finally:
        if conn:
            conn.close()

# ===================== 保存 MD（已完全适配新结构） =====================
def save_results_to_md(results, output_md):
    # ===================== 先统计所有库中最终答案为 A 的数量 =====================
    total_A = 0
    total_processed = 0
    for res in results:
        if res:
            total_processed += 1
            if res.get("best_ans") == "A":
                total_A += 1

    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# 📊 所有数据库测试结果\n\n")

        # ===================== 【你要的】顶置输出答案 A 的数量 =====================
        f.write(f"## 📈 总统计\n")
        f.write(f"- ✅ 总计处理库数：**{total_processed}**\n")
        f.write(f"- 🟢 最终答案为 A 的库数：**{total_A}**\n\n")
        f.write("---\n\n")

        # ===================== 以下不变 =====================
        f.write(f"## 📂 详细结果\n\n")

        for res in results:
            if not res:
                continue

            db = res["db"]
            avg_dis = res["average_eucli_dis"]
            alist = res["answer_list"]
            stats = res["stats"]
            best_ans = res["best_ans"]
            min_diff = res["min_diff"]

            f.write(f"## 📂 数据库：{os.path.basename(db)}\n")
            f.write(f"- **路径**：{db}\n")
            f.write(f"- **基准平均距离**：{avg_dis}\n\n")

            f.write("### 📊 答案统计\n")
            for ans, info in stats.items():
                f.write(f"- **{ans}**：{info['count']} 次 | 平均分：`{info['avg_score']}`\n")

            f.write(f"\n### 🎯 最终选择\n")
            f.write(f"- ✅ 最接近答案：**{best_ans}**\n")
            f.write(f"- 📉 差值：`{min_diff}`\n")
            f.write("\n---\n\n")

    print(f"\n💾 结果已保存到：{output_md}")
    print(f"📊 统计完成：答案为 A 的数据库总数 = {total_A}")

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("🚀 开始批量处理所有 compare_50_*.db 数据库")
    print(f"📂 找到 {len(DB_FILES)} 个文件")
    #print(f"ℹ️  输入 c = 继续下一个 | e = 退出\n")

    all_results = []

    for idx, db in enumerate(DB_FILES):
        '''
        while True:
            
            user_input = input(f"\n⌨️  准备处理第 {idx+1}/{len(DB_FILES)} 个库 | 输入命令 (c=继续 / e=退出)：").strip().lower()
            if user_input == "c":
                break
            elif user_input == "e":
                print("\n🛑 用户选择退出，结束处理")
                save_results_to_md(all_results, OUTPUT_MD)
                sys.exit(0)
            else:
                print("❌ 无效命令，请重新输入 (c / e)")
            '''
        res = process_single_db(db)
        all_results.append(res)
        save_results_to_md(all_results, OUTPUT_MD)

    print("\n🎉 所有数据库处理完成！")
    save_results_to_md(all_results, OUTPUT_MD)