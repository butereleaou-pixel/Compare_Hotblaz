import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix VRAM fragmentation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()

import pandas as pd
import numpy as np
import torch.nn as nn
from model import AnswerModel
from config import *

# =============================================================================
# 🧠 PREDICTION SETTINGS
# =============================================================================
# ✅ FIX 1: Use ABSOLUTE path to guarantee model is found
MODEL_FILE = "model_pth/final_model_after_ctrlc_282929230424223_916.pth"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODEL_FILE)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

feat_cols = [
    "Count", "Mean", "Median", "Std", "Variance", "Min", "Max",
    "Range", "Skewness", "Kurtosis", "GMM_pi", "GMM_mu", "GMM_sigma"
]

idx2label = ["A", "B", "C", "D"]

# =============================================================================
# 🚀 LOAD MODEL
# =============================================================================
print("🔹 Loading trained model...")
model = AnswerModel(len(feat_cols)).to(device)

# ✅ FIX 2: Add weights_only=True to eliminate warning & fix loading
model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))

model.eval()
print("✅ Model loaded successfully!\n")

# =============================================================================
# 🎯 Prediction Function
# =============================================================================
def run_prediction(
    processed_df,
    temperature: float = 1.0,
    topk: int = 2
):
    results = []

    for db_name, group in processed_df.groupby("Database"):
        group = group.sort_values("Answer").copy()
        if len(group) != 4:
            continue

        feats = group[feat_cols].values.astype(np.float32)
        x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(device)
        mask = torch.ones((1, 4), dtype=torch.float32).to(device)

        with torch.no_grad():
            logits = model(x, mask)

        logits = logits / temperature
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        results.append({
            "database": db_name,
            "A": round(float(probs[0]), 4),
            "B": round(float(probs[1]), 4),
            "C": round(float(probs[2]), 4),
            "D": round(float(probs[3]), 4)
        })

    return results

# =============================================================================
if __name__ == "__main__":
    print("ℹ️  Call: run_prediction(processed_df, temperature=1.0, topk=2)")