import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
from config import D_MODEL, N_HEADS, N_LAYERS, DROPOUT_RATE

class TransformerBlock(nn.Module):
    def __init__(self, dim, heads):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)
        self.drop1 = nn.Dropout(DROPOUT_RATE)

        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim//2),
            nn.SiLU(),
            nn.Dropout(DROPOUT_RATE),
            nn.Linear(dim//2, dim)
        )
        self.drop2 = nn.Dropout(DROPOUT_RATE)

    def forward(self, x):
        attn_out = self.attn(self.norm1(x), self.norm1(x), self.norm1(x))[0]
        x = x + self.drop1(attn_out)
        mlp_out = self.mlp(self.norm2(x))
        x = x + self.drop2(mlp_out)
        return x

class AnswerModel(nn.Module):
    def __init__(self, feature_dim):
        super().__init__()
        self.emb = nn.Linear(feature_dim, D_MODEL)
        self.pos_emb = nn.Parameter(torch.randn(1, 4, D_MODEL) * 0.02)
        self.drop_emb = nn.Dropout(DROPOUT_RATE)

        self.layers = nn.ModuleList([
            TransformerBlock(D_MODEL, N_HEADS) for _ in range(N_LAYERS)
        ])

        self.norm = nn.LayerNorm(D_MODEL)
        self.head = nn.Linear(D_MODEL, 1)

    def forward(self, x, mask=None):
        x = self.emb(x)
        x = x + self.pos_emb
        x = self.drop_emb(x)

        for layer in self.layers:
            x = layer(x)

        x = self.norm(x)
        logits = self.head(x).squeeze(-1)

        if mask is not None:
            logits = logits.masked_fill(mask == 0, -1e4)
        return logits