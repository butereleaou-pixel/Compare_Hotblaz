import numpy as np
import matplotlib.pyplot as plt
import mplcyberpunk  # For hand-drawn style (pip install mplcyberpunk)

# --------------------------
# 1. Set hand-drawn style
# --------------------------
plt.style.use("cyberpunk")
plt.rcParams['font.family'] = 'Comic Sans MS'  # Handwriting font (Windows)
# For macOS/Linux: use 'Marker Felt' or 'Comic Neue'
# plt.rcParams['font.family'] = 'Marker Felt'

# --------------------------
# 2. Generate random data (100 samples)
# --------------------------
np.random.seed(42)  # Fixed seed for reproducibility
sample_id = np.arange(1, 101)  # X-axis: sample_id (1-100)
mean_close_score = 7.5  # Mean line value

# Generate 3 groups of close_score:
# Group A: around mean (±0.5) | Group B: slightly deviated (±1.5) | Group C: far deviated (±3)
group_a_idx = np.random.choice(sample_id, size=30, replace=False)  # 30 points
group_b_idx = np.random.choice([i for i in sample_id if i not in group_a_idx], size=40, replace=False)  # 40 points
group_c_idx = [i for i in sample_id if i not in group_a_idx and i not in group_b_idx]  # 30 points

# Generate values for each group
close_score = np.zeros_like(sample_id, dtype=float)
close_score[group_a_idx - 1] = mean_close_score + np.random.uniform(-0.5, 0.5, size=30)
close_score[group_b_idx - 1] = mean_close_score + np.random.uniform(-1.5, 1.5, size=40)
close_score[group_c_idx - 1] = mean_close_score + np.random.uniform(-3, 3, size=30)

# --------------------------
# 3. Define threshold lines (dashed lines)
# --------------------------
upper_threshold = mean_close_score + 1.0  # Upper dashed line
lower_threshold = mean_close_score - 1.0  # Lower dashed line

# --------------------------
# 4. Plot the graph
# --------------------------
fig, ax = plt.subplots(figsize=(12, 8))

# Plot 3 groups with different colors/shapes
ax.scatter(group_a_idx, close_score[group_a_idx - 1], 
           color='#2ecc71', marker='o', s=80, label='Group A (Around Mean)', zorder=5)
ax.scatter(group_b_idx, close_score[group_b_idx - 1], 
           color='#3498db', marker='s', s=80, label='Group B (Slightly Deviated)', zorder=5)
ax.scatter(group_c_idx, close_score[group_c_idx - 1], 
           color='#e74c3c', marker='^', s=80, label='Group C (Far Deviated)', zorder=5)

# Plot mean line (horizontal solid line)
ax.axhline(y=mean_close_score, color='#9b59b6', linewidth=2.5, label=f'Mean Close Score ({mean_close_score})', zorder=3)

# Plot dashed threshold lines
ax.axhline(y=upper_threshold, color='#f39c12', linestyle='--', linewidth=2, label=f'Upper Threshold ({upper_threshold})', zorder=2)
ax.axhline(y=lower_threshold, color='#f39c12', linestyle='--', linewidth=2, label=f'Lower Threshold ({lower_threshold})', zorder=2)

# Add arrows (up/down of mean line)
ax.annotate('', xy=(95, mean_close_score + 0.8), xytext=(95, mean_close_score),
            arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2, shrinkA=0, shrinkB=0))
ax.annotate('', xy=(95, mean_close_score - 0.8), xytext=(95, mean_close_score),
            arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2, shrinkA=0, shrinkB=0))

# Add "Schematic Diagram" label (small tips)
ax.text(0.02, 0.98, 'Schematic Diagram', transform=ax.transAxes, 
        fontsize=10, ha='left', va='top', 
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# --------------------------
# 5. Customize graph (hand-drawn style)
# --------------------------
mplcyberpunk.add_glow_effects()  # Enhance hand-drawn feel
ax.set_xlabel('Sample ID', fontsize=14, fontweight='bold')
ax.set_ylabel('Close Score', fontsize=14, fontweight='bold')
ax.set_title('Close Score Distribution by Sample ID (Hand-Drawn Style)', fontsize=16, fontweight='bold')
ax.legend(loc='upper right', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.5)  # Soft grid

# Set axis limits
ax.set_xlim(0, 101)
ax.set_ylim(mean_close_score - 4, mean_close_score + 4)

# --------------------------
# 6. Show/save the graph
# --------------------------
plt.tight_layout()
plt.savefig('handdrawn_close_score_graph.png', dpi=300, bbox_inches='tight')  # Save high-res
plt.show()