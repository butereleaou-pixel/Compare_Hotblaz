import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import os
import time

os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
os.environ['TORCH_USE_CUDA_DSA'] = '1'

# ============================
#  小模型（适合小数据集）
# ============================
D_MODEL = 128
N_HEADS = 2
N_LAYERS = 1
LR = 5e-4
EPOCHS = 1000
WARMUP_EPOCHS = 10
BATCH_SIZE = 2
VAL_RATIO = 0.2
PATIENCE = 10
CLIP_GRAD = 1.0

# ====================== Simple Transformer ======================
class TransformerBlock(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim),
            nn.SiLU(),
            nn.Linear(dim, dim)
        )

    def forward(self, x):
        x = x + self.attn(self.norm1(x), self.norm1(x), self.norm1(x))[0]
        x = x + self.mlp(self.norm2(x))
        return x

# ====================== 小模型 ======================
class AnswerModel(nn.Module):
    def __init__(self, feature_dim):
        super().__init__()
        self.emb = nn.Linear(feature_dim, D_MODEL)
        self.pos_emb = nn.Parameter(torch.randn(1, 4, D_MODEL) * 0.02)
        self.layers = nn.ModuleList([
            TransformerBlock(D_MODEL, N_HEADS) for _ in range(N_LAYERS)
        ])
        self.norm = nn.LayerNorm(D_MODEL)
        self.head = nn.Linear(D_MODEL, 1)

    def forward(self, x, mask=None):
        x = self.emb(x)
        x = x + self.pos_emb
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x)
        logits = self.head(x).squeeze(-1)
        if mask is not None:
            logits = logits.masked_fill(mask == 0, -1e4)
        return logits

# ====================== 数据处理（组内标准化） ======================
def load_and_process_data(path):
    df = pd.read_excel(path)
    df = df[df["Answer"] != "GLOBAL"].copy()
    ratio_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]
    gmm_cols = ["GMM_pi","GMM_mu","GMM_sigma"]
    feat_cols = ratio_cols + gmm_cols

    units = []
    all_rows = []

    for db_name, group in df.groupby("Database"):
        group = group.sort_values("Answer").copy()
        if len(group) != 4: continue

        feats = group[feat_cols].values.astype(np.float32)
        label = int(group["Right_Answer_Pos"].iloc[0]) - 1
        label = np.clip(label, 0, 3)
        mask = (feats.sum(axis=1) != 0).astype(np.float32)

        for i in range(4):
            pi, mu, sigma = feats[i, -3:]
            if np.isnan(pi) or np.isnan(mu) or np.isnan(sigma):
                pi, mu, sigma = 0.1, 100.0, 5.0
            mu = np.clip(mu, 1e-3, 1e6)
            sigma = np.clip(sigma, 1e-3, 1e6)
            feats[i, -3:] = [pi, np.log(mu), np.log(sigma)]

        feats = np.nan_to_num(feats, 0.0, 1e3, -1e3)

        # 组内标准化（保留相对分布）
        g_mean = feats.mean(0, keepdims=True)
        g_std = feats.std(0, keepdims=True) + 1e-6
        feats = (feats - g_mean) / g_std
        feats = np.clip(feats, -5, 5)

        units.append((feats, label, mask))

        for i, ans in enumerate(group["Answer"].values):
            row = [db_name, ans, label] + feats[i].tolist()
            all_rows.append(row)

    pd.DataFrame(all_rows, columns=["Database","Answer","True_Label(0=A,1=B,2=C,3=D)"]+feat_cols).to_excel("pipeline_data/PROCESSED_FINAL.xlsx", index=False)
    return units, feat_cols

def get_batches(units, bs):
    np.random.shuffle(units)
    for i in range(0, len(units), bs):
        b = units[i:i+bs]
        x = np.stack([o[0] for o in b])
        y = np.array([o[1] for o in b])
        m = np.stack([o[2] for o in b])
        yield torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.long), torch.tensor(m, dtype=torch.float32)

# ====================== TRAIN ======================
if __name__ == "__main__":
    units, feat_cols = load_and_process_data("pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx")
    from sklearn.model_selection import train_test_split
    train_units, val_units = train_test_split(units, test_size=VAL_RATIO, random_state=42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AnswerModel(len(feat_cols)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    best_val = np.inf
    wait = 0
    t0 = time.time()

    print("\n🚀 最终小模型训练开始\n")

    for epoch in range(EPOCHS):
        model.train()
        tl, tc, tt = 0,0,0
        for x,y,m in get_batches(train_units, BATCH_SIZE):
            x,y,m = x.to(device), y.to(device), m.to(device)
            p = model(x,m)
            loss = criterion(p, y)
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), CLIP_GRAD)
            optimizer.step()
            tl += loss.item() * x.size(0)
            tc += (p.argmax(1)==y).sum().item()
            tt += x.size(0)
        train_loss = tl/tt if tt else 0
        train_acc = tc/tt if tt else 0

        model.eval()
        vl, vc, vt = 0,0,0
        with torch.no_grad():
            for x,y,m in get_batches(val_units, BATCH_SIZE):
                x,y,m = x.to(device), y.to(device), m.to(device)
                p = model(x,m)
                vl += criterion(p,y).item() * x.size(0)
                vc += (p.argmax(1)==y).sum().item()
                vt += x.size(0)
        val_loss = vl/vt if vt else 0
        val_acc = vc/vt if vt else 0

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "model/best_final_model.pth")
            wait = 0
        else:
            wait +=1
            if wait >= PATIENCE:
                print(f"\n🛑 早停 Epoch {epoch+1}")
                break

        used = time.time()-t0
        print(f"EP {epoch+1:3d} | TL {train_loss:.4f} | TA {train_acc:.4f} | VL {val_loss:.4f} | VA {val_acc:.4f}")

    print("\n✅ 训练完成！")