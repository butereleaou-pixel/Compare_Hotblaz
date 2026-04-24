import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from model import AnswerModel
from config import *

# =============================================================================
# 🧠 PREDICTION SETTINGS (USE YOUR BEST MODEL)
# =============================================================================
MODEL_PATH = "model_pth/final_model_after_ctrlc.pth"
DATA_PATH = "pipeline_data/PROCESSED_FINAL_ALL.xlsx"

# Device (auto CPU/GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Feature list (MUST match training)
feat_cols = [
    "Count", "Mean", "Median", "Std", "Variance", "Min", "Max",
    "Range", "Skewness", "Kurtosis", "GMM_pi", "GMM_mu", "GMM_sigma"
]

# Label mapping
ans_map = {0: "ANSWER A", 1: "ANSWER B", 2: "ANSWER C", 3: "ANSWER D"}

# =============================================================================
# 🚀 LOAD TRAINED MODEL
# =============================================================================
print("🔹 Loading trained model...")
model = AnswerModel(len(feat_cols)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()  # Set to PREDICTION MODE (no dropout, no training)
print("✅ Model loaded successfully!\n")

# =============================================================================
# 📊 LOAD DATA TO PREDICT
# =============================================================================
df = pd.read_excel(DATA_PATH)
df_results = []

# Predict per Database (each group = 4 answers)
for db_name, group in df.groupby("Database"):
    group = group.sort_values("Answer").copy()
    if len(group) != 4:
        continue

    # Get features
    feats = group[feat_cols].values.astype(np.float32)
    true_label = int(group["True_Label(0=A,1=B,2=C,3=D)"].iloc[0])

    # Convert to model tensor
    x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(device)
    mask = torch.ones((1, 4), dtype=torch.float32).to(device)

    # PREDICT
    with torch.no_grad():
        output = model(x, mask)
        pred_label = torch.argmax(output, dim=1).item()

    # Store result
    df_results.append({
        "Database": db_name,
        "True_Answer": ans_map[true_label],
        "Predicted_Answer": ans_map[pred_label],
        "Correct?": "✅ YES" if pred_label == true_label else "❌ NO",
        "Raw_Prediction_Logits": output.cpu().numpy().tolist()
    })

# =============================================================================
# 📝 SHOW & SAVE RESULTS
# =============================================================================
df_out = pd.DataFrame(df_results)
print("=" * 80)
print("📊 PREDICTION RESULTS")
print("=" * 80)
print(df_out[["Database", "True_Answer", "Predicted_Answer", "Correct?"]].to_string(index=False))
print("=" * 80)

# Save full prediction
df_out.to_excel("pipeline_data/PREDICTION_RESULTS.xlsx", index=False)
print("\n✅ Prediction saved to: PREDICTION_RESULTS.xlsx")

# Final accuracy
acc = (df_out["Correct?"] == "✅ YES").mean()
print(f"\� Total Prediction Accuracy: {acc:.2%}")