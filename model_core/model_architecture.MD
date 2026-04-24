# Model Architecture Explanation (AnswerModel + TransformerBlock)
I'll give you a **clear, complete, visual, and detailed breakdown** of this transformer-based classification model architecture step by step.

---

## Full Model Architecture Overview
This is a **small transformer encoder model for 4-option multiple-choice answer ranking/classification**
- Input: 4 candidate answers per question → each with 13 numerical features
- Output: 4-class logits (select which option is correct: 0/A,1/B,2/C,3/D)

---

## 1. Core Model Components
The model has **two main classes**:
1. `TransformerBlock`: Single transformer encoder layer
2. `AnswerModel`: Full end-to-end model

### Hyperparameters (Fixed)
```python
D_MODEL = 128       # Hidden dimension size
N_HEADS = 2         # Multi-head attention heads
N_LAYERS = 1        # Transformer layers
Sequence Length = 4 (fixed: 4 options per question)
Feature dim = 13    # Input features per option
```

---

## 2. Full Architecture Diagram (Text Flowchart)
```
[Input: Batch × 4 (options) × 13 (features)]
                ↓
Linear Projection (13 → 128)
                ↓
+ Positional Embedding (1 × 4 × 128)
                ↓
1 × TransformerBlock (128 dim, 2 heads)
                ↓
Layer Normalization
                ↓
Linear Head (128 → 1) → Squeeze → [Batch × 4]
                ↓
Masked Logits (for 4-class classification)
```

---

## 3. Detailed Layer-by-Layer Architecture

### A. TransformerBlock
Pre-norm residual transformer block (standard modern design):
1. **LayerNorm** (dim=128)
2. **Multi-head Attention** (2 heads, dim=128, batch_first=True)
   - Self-attention: query = key = value
   - Residual connection: `x = x + attn_output`
3. **LayerNorm** (dim=128)
4. **MLP (Feed-Forward)**:
   - Linear(128 → 128)
   - SiLU activation
   - Linear(128 → 128)
   - Residual connection: `x = x + mlp_output`

### B. AnswerModel (Full Model)
1. **Input Embedding**
   - Linear layer: `nn.Linear(feature_dim=13, D_MODEL=128)`
   - Projects raw 13 features → 128-dim transformer space

2. **Positional Embedding**
   - Learnable: `nn.Parameter(torch.randn(1, 4, 128))`
   - Fixed sequence length = 4 (A/B/C/D options)
   - Added directly to embedded features

3. **Transformer Layers**
   - Stack of N_LAYERS = 1 `TransformerBlock`
   - Processes 4 × 128 sequence

4. **Final Normalization**
   - `nn.LayerNorm(128)`

5. **Classification Head**
   - `nn.Linear(128, 1)`
   - Squeeze last dimension → output shape: `(batch, 4)`
   - Mask applied to pad invalid positions (set to -1e4)

---

## 4. Input/Output Shape Summary
- **Input**: `(BATCH_SIZE, 4, 13)`
- **After Embedding**: `(BATCH_SIZE, 4, 128)`
- **After Transformer**: `(BATCH_SIZE, 4, 128)`
- **Final Output**: `(BATCH_SIZE, 4)` (logits for 4 options)

---

## 5. Full Model Summary Table
| Module | Type | Output Shape |
|--------|------|--------------|
| Input | Tensor | (B, 4, 13) |
| Embedding | Linear(13→128) | (B, 4, 128) |
| Pos Encoding | Learnable | (1, 4, 128) |
| Transformer Block | 1 layer | (B, 4, 128) |
| Layer Norm | LayerNorm(128) | (B, 4, 128) |
| Head | Linear(128→1) | (B, 4) |
| Output | Logits | (B, 4) |

---

## 6. Key Design Choices
- **Pre-norm transformer** (stable for small datasets)
- **Fixed 4-length sequence** (4 multiple-choice options)
- **Group-wise normalization** (features normalized per question)
- **Maskable logits** for invalid entries
- **Residual connections** in transformer block

---

### Summary
This is a **tiny, stable transformer encoder** for **4-option multiple-choice classification**:
- Input: 4 options × 13 numerical features
- Core: 1 transformer layer with 2 attention heads
- Output: 4-class selection logits
- Optimized for small datasets