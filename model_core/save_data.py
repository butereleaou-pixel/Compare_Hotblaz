import pandas as pd
import numpy as np

# ===================== Config =====================
ratio_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]
gmm_cols = ["GMM_pi","GMM_mu","GMM_sigma"]
feature_names = ratio_cols + gmm_cols

# ===================== Data Processing (Identical to Training) =====================
def load_and_process_data(excel_path):
    df = pd.read_excel(excel_path)
    df = df[df["Answer"] != "GLOBAL"].copy()

    processed_rows = []
    db_info = []

    # Process each DB group
    for db_name, group in df.groupby("Database"):
        group = group.sort_values("Answer").copy()
        if len(group) != 4:
            continue

        # Raw features
        feats = group[feature_names].values.astype(np.float32)
        label = int(group["Right_Answer_Pos"].iloc[0]) - 1
        label = np.clip(label, 0, 3)

        # ================ 1. Cleaning + Filling + Safe log ================
        for i in range(4):
            pi, mu, sigma = feats[i, -3:]
            if np.isnan(pi) or np.isnan(mu) or np.isnan(sigma):
                pi, mu, sigma = 0.1, 100.0, 5.0
            # Safe clipping
            mu = np.clip(mu, 1e-3, 1e6)
            sigma = np.clip(sigma, 1e-3, 1e6)
            feats[i, -3:] = [pi, np.log(mu), np.log(sigma)]

        # ================ 2. Final NaN/Inf Replacement ================
        feats = np.nan_to_num(feats, nan=0.0, posinf=1e3, neginf=-1e3)

        # Save each group data
        for i in range(4):
            ans = group["Answer"].iloc[i]
            row = [db_name, ans, label] + feats[i].tolist()
            processed_rows.append(row)

    # ================ 3. Global Standardization (Identical to Training) ================
    all_feats = np.array([r[3:] for r in processed_rows], dtype=np.float32)
    mean = np.mean(all_feats, axis=0)
    std = np.std(all_feats, axis=0) + 1e-6

    # Apply standardization
    for r in processed_rows:
        feats = np.array(r[3:], dtype=np.float32)
        feats = (feats - mean) / std
        feats = np.clip(feats, -5, 5)  # Prevent extreme values
        r[3:] = feats.tolist()

    # ================ Build Final DataFrame ================
    columns = ["Database", "Answer", "True_Label(0=A,1=B,2=C,3=D)"] + feature_names
    out_df = pd.DataFrame(processed_rows, columns=columns)
    return out_df

# ===================== Main Program =====================
if __name__ == "__main__":
    INPUT_FILE = "pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx"
    OUTPUT_FILE = "pipeline_data/PROCESSED_CLEAN_DATA.xlsx"

    print("🔄 Processing data (cleaning → fill NaN → standardization)...")
    final_df = load_and_process_data(INPUT_FILE)

    print(f"💾 Saving to {OUTPUT_FILE} ...")
    final_df.to_excel(OUTPUT_FILE, index=False)

    print("✅ Save completed! You can open and check the processed data directly")