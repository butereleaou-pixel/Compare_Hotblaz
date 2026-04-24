import pandas as pd
import numpy as np
import torch
import torch.nn as nn

# ====================== 必须和训练模型完全一样 ======================
D_MODEL = 128
N_HEADS = 2
N_LAYERS = 1

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

class AnswerModel(nn.Module):
    def __init__(self, feature_dim):
        super().__init__()
        self.emb = nn.Linear(feature_dim, D_MODEL)
        self.pos_emb = nn.Parameter(torch.randn(1, 4, D_MODEL) * 0.02)
        self.layers = nn.ModuleList([TransformerBlock(D_MODEL, N_HEADS) for _ in range(N_LAYERS)])
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

# ====================== 数据预处理（和训练完全一致！） ======================
def load_and_preprocess_group(group, feat_cols):
    feats = group[feat_cols].values.astype(np.float32)
    mask = (feats.sum(axis=1) != 0).astype(np.float32)

    # GMM 缺失值处理
    for i in range(4):
        pi, mu, sigma = feats[i, -3:]
        if np.isnan(pi) or np.isnan(mu) or np.isnan(sigma):
            pi, mu, sigma = 0.1, 100.0, 5.0
        mu = np.clip(mu, 1e-3, 1e6)
        sigma = np.clip(sigma, 1e-3, 1e6)
        feats[i, -3:] = [pi, np.log(mu), np.log(sigma)]

    feats = np.nan_to_num(feats, 0.0, 1e3, -1e3)

    # ✅ 组内标准化（关键！和训练完全一样）
    g_mean = feats.mean(axis=0, keepdims=True)
    g_std = feats.std(axis=0, keepdims=True) + 1e-6
    feats = (feats - g_mean) / g_std
    feats = np.clip(feats, -5, 5)

    return feats, mask

# ====================== 预测主函数 ======================
def predict_all(file_path="pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx", model_path="model/best_final_model.pth"):
    # 特征列
    ratio_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]
    gmm_cols = ["GMM_pi","GMM_mu","GMM_sigma"]
    feat_cols = ratio_cols + gmm_cols

    # 读取数据
    df = pd.read_excel(file_path)
    df = df[df["Answer"] != "GLOBAL"].copy()

    # 加载模型
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AnswerModel(len(feat_cols)).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # 结果保存
    results = []

    # 逐组预测
    with torch.no_grad():
        for db_name, group in df.groupby("Database"):
            group = group.sort_values("Answer").copy()
            if len(group) != 4:
                continue

            # 真实标签
            true_label = int(group["Right_Answer_Pos"].iloc[0]) - 1
            answers = group["Answer"].values.tolist()

            # 预处理
            feats, mask = load_and_preprocess_group(group, feat_cols)

            # 转 tensor
            x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(device)
            m = torch.tensor(mask, dtype=torch.float32).unsqueeze(0).to(device)

            # 预测
            logits = model(x, m)
            scores = logits.cpu().numpy()[0]
            pred_label = np.argmax(scores)

            # 记录
            results.append({
                "Database": db_name,
                "A_score": float(scores[0]),
                "B_score": float(scores[1]),
                "C_score": float(scores[2]),
                "D_score": float(scores[3]),
                "Predicted": ["A","B","C","D"][pred_label],
                "True": ["A","B","C","D"][true_label],
                "Correct": "✅" if pred_label == true_label else "❌"
            })

    # 输出结果
    res_df = pd.DataFrame(results)
    res_df.to_excel("PREDICTION_RESULT.xlsx", index=False)
    print("✅ 预测完成！结果已保存到：PREDICTION_RESULT.xlsx")
    print("\n==== 预测结果预览 ====")
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    predict_all()