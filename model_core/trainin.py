import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import time
import signal
from sklearn.model_selection import train_test_split
from config import *
from model import AnswerModel

# Environment
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
os.environ['TORCH_USE_CUDA_DSA'] = '1'

# Ctrl+C handler
stop_flag = False
def handle_ctrl_c(signum, frame):
    global stop_flag
    print("\n\n🛑 CTRL+C detected! Safely stopping training...")
    stop_flag = True
signal.signal(signal.SIGINT, handle_ctrl_c)

processed_data = "pipeline_data/PROCESSED_FINAL_28292923042.xlsx"

# =============================================================================
# 🔥 LOAD ALREADY PROCESSED DATA FROM EXCEL (NO RE-PROCESSING!)
# =============================================================================
def load_processed_data():
    df = pd.read_excel(processed_data)

    feat_cols = [
        "Count","Mean","Median","Std","Variance","Min","Max",
        "Range","Skewness","Kurtosis","GMM_pi","GMM_mu","GMM_sigma"
    ]

    units = []
    for db_name, group in df.groupby("Database"):
        group = group.sort_values("Answer").copy()
        if len(group) != 4:
            continue

        feats = group[feat_cols].values.astype(np.float32)
        label = int(group["True_Label(0=A,1=B,2=C,3=D)"].iloc[0])
        mask = np.ones(4, dtype=np.float32)

        units.append((feats, label, mask))

    return units, feat_cols

# =============================================================================
# ORIGINAL DATA PROCESS (RUN ONLY ONCE TO CREATE PROCESSED FILE)
# =============================================================================
def run_data_pipeline_once(raw_path="pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx"):
    df = pd.read_excel(raw_path)
    df = df[df["Answer"] != "GLOBAL"].copy()

    ratio_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]
    gmm_cols = ["GMM_pi","GMM_mu","GMM_sigma"]
    feat_cols = ratio_cols + gmm_cols

    units = []
    all_rows = []

    for db_name, group in df.groupby("Database"):
        # ✅ 【终极正确】直接取值！0=A,1=B,2=C,3=D
        raw_pos = int(group["Right_Answer_Pos"].iloc[0])
        true_label = raw_pos  # ❌ 再也不减1！

        # 按 A B C D 排序，固定顺序
        group = group.sort_values("Answer").reset_index(drop=True)
        if len(group) != 4:
            continue

        feats = group[feat_cols].values.astype(np.float32)
        mask = (feats.sum(axis=1) != 0).astype(np.float32)

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

        units.append((feats, true_label, mask))

        for i, ans in enumerate(group["Answer"].values):
            row = [db_name, ans, true_label] + feats[i].tolist()
            all_rows.append(row)

    pd.DataFrame(
        all_rows,
        columns=["Database","Answer","True_Label(0=A,1=B,2=C,3=D)"] + feat_cols
    ).to_excel(processed_data, index=False)

    print("✅ ✅ ✅ 标签 100% 正确！0=A,1=B,2=C,3=D 完全对齐！")
    return units, feat_cols

# Batch generator
def get_batches(units, bs):
    np.random.shuffle(units)
    for i in range(0, len(units), bs):
        b = units[i:i+bs]
        x = np.stack([o[0] for o in b])
        y = np.array([o[1] for o in b])
        m = np.stack([o[2] for o in b])
        yield torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.long), torch.tensor(m, dtype=torch.float32)

# =============================================================================
# MAIN TRAINING
# =============================================================================
if __name__ == "__main__":
    # -------------------------------
    # 👇 RUN ONCE TO CREATE THE FILE
    #run_data_pipeline_once()
    # -------------------------------

    # 🔥 NOW WE LOAD SAVED DATA DIRECTLY
    units, feat_cols = load_processed_data()
    print(f"✅ Loaded ALREADY PROCESSED data from {processed_data}")

    train_units, val_units = train_test_split(units, test_size=VAL_RATIO, random_state=42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AnswerModel(len(feat_cols)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    criterion = nn.CrossEntropyLoss()

    best_val = np.inf
    t0 = time.time()

    print("\n🚀 TRAINING START — PRESS CTRL+C TO STOP & SAVE")
    epoch = 0

    while not stop_flag:
        epoch += 1
        model.train()
        tl, tc, tt = 0, 0, 0

        for x, y, m in get_batches(train_units, BATCH_SIZE):
            if stop_flag:
                break
            x, y, m = x.to(device), y.to(device), m.to(device)
            p = model(x, m)
            loss = criterion(p, y)
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD)
            optimizer.step()

            tl += loss.item() * x.size(0)
            tc += (p.argmax(1) == y).sum().item()
            tt += x.size(0)

        train_loss = tl / tt if tt else 0
        train_acc = tc / tt if tt else 0

        # Validation (NO TRAINING HERE)
        model.eval()
        vl, vc, vt = 0, 0, 0
        with torch.no_grad():
            for x, y, m in get_batches(val_units, BATCH_SIZE):
                if stop_flag:
                    break
                x, y, m = x.to(device), y.to(device), m.to(device)
                p = model(x, m)
                vl += criterion(p, y).item() * x.size(0)
                vc += (p.argmax(1) == y).sum().item()
                vt += x.size(0)

        val_loss = vl / vt if vt else 0
        val_acc = vc / vt if vt else 0

        # Save best model
        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "model/best_final_model.pth")
            print(f"EP {epoch:3d} | TL {train_loss:.4f} | TA {train_acc:.4f} | VL {val_loss:.4f} | VA {val_acc:.4f} ✅ BEST SAVED")
        else:
            print(f"EP {epoch:3d} | TL {train_loss:.4f} | TA {train_acc:.4f} | VL {val_loss:.4f} | VA {val_acc:.4f}")

        # Backup every 10 epochs
        if epoch % 10 == 0:
            torch.save(model.state_dict(), "latest_model.pth")

    # Final save on CTRL+C
    torch.save(model.state_dict(), "model_pth/final_model_after_ctrlc_28292923042.pth")
    print("\n✅ TRAINING STOPPED")
    print("✅ Models saved: best, latest, final_after_ctrlc_28292923042.pth")
