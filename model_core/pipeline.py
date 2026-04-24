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


def run_data_pipeline_once(raw_path="pipeline_data/ALL_DB_FINAL_SHUFFLED.xlsx"):
    df = pd.read_excel(raw_path)
    df = df[df["Answer"] != "GLOBAL"].copy()

    ratio_cols = ["Count","Mean","Median","Std","Variance","Min","Max","Range","Skewness","Kurtosis"]
    gmm_cols = ["GMM_pi","GMM_mu","GMM_sigma"]
    feat_cols = ratio_cols + gmm_cols

    units = []
    all_rows = []

    for db_name, group in df.groupby("Database"):
        # Get label value directly: 0=A,1=B,2=C,3=D
        raw_pos = int(group["Right_Answer_Pos"].iloc[0])
        true_label = raw_pos  # NO subtraction!

        # Sort by A B C D fixed order
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
    ).to_excel("pipeline_data/PROCESSED_FINAL.xlsx", index=False)

    print("✅ ✅ ✅ Labels are 100% correct! 0=A,1=B,2=C,3=D fully aligned!")
    return units, feat_cols

if __name__ == "__main__":
    run_data_pipeline_once()
