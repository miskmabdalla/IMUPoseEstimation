# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import importlib.util
import sys
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Adam
from datetime import datetime
from IPython.display import display  # Jupyter-safe
from io import StringIO
import csv
import json
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch.utils.data import TensorDataset, DataLoader

# %%
torch_spec = importlib.util.find_spec("torch")
print(torch_spec)

# %% [markdown]
# Params

# %%
# Parameters
aligned_data_root = Path("dataset/final_dataset")
# aligned_data_root = Path("dataset/reduced_dataset/dataset_no_left_limbs")
window_size = 70


# %% [markdown]
# Load and Accumulate Data Across Trials

# %%
# Storage for all trials
X_trials = []
y_trials = []

# Load aligned IMU and angle data from all trials
for trial_dir in sorted(aligned_data_root.glob("trial_*")):
    X_path = trial_dir / "X.csv"
    y_path = trial_dir / "Y.csv"
    if not X_path.exists() or not y_path.exists():
        print(f"Missing data in {trial_dir}, skipping.")
        continue

    X_df = pd.read_csv(X_path)
    y_df = pd.read_csv(y_path)

    # Drop unnecessary columns
    X_df = X_df.drop(columns=['Millis'], errors='ignore')
    y_df = y_df.drop(columns=['time'], errors='ignore')

    assert len(X_df) == len(y_df), f"Length mismatch in {trial_dir}"

    X_trials.append(X_df.values)
    y_trials.append(y_df.values)


# %% [markdown]
#  Concatenate

# %%
# Concatenate all trials
X_all = np.concatenate(X_trials, axis=0)
y_all = np.concatenate(y_trials, axis=0)

# %% [markdown]
# Apply Sliding Window

# %%
def create_windows(X, y, window_size):
    X_windowed = []
    y_windowed = []
    for i in range(len(X) - window_size + 1):
        X_windowed.append(X[i:i+window_size])
        y_windowed.append(y[i+window_size-1])  # predict last frame
    return np.array(X_windowed), np.array(y_windowed)

X_all, y_all = create_windows(X_all, y_all, window_size)


# %% [markdown]
# Train/Validation/Test Split

# %%
# First split: 60% train, 40% temp
X_train, X_temp, y_train, y_temp = train_test_split(
    X_all, y_all, test_size=0.4, random_state=42
)

# Second split: 20% val, 20% test
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42
)


# %% [markdown]
# Fitting and Transforming Scalers

# %%
# --- Now fit scalers only on training data ---

# Flatten X_train for fitting (because windowed input has shape [samples, window_size, features])
X_train_flat = X_train.reshape(-1, X_train.shape[-1])

scaler_X = StandardScaler().fit(X_train_flat)

# Transform all sets
X_train_scaled = scaler_X.transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
X_val_scaled   = scaler_X.transform(X_val.reshape(-1, X_val.shape[-1])).reshape(X_val.shape)
X_test_scaled  = scaler_X.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)



# %% [markdown]
# Wrap in PyTorch Datasets and Check Shapes

# %%
# Wrap in PyTorch datasets
train_dataset = TensorDataset(
    torch.tensor(X_train_scaled, dtype=torch.float32),
    torch.tensor(y_train, dtype=torch.float32)
)
val_dataset = TensorDataset(
    torch.tensor(X_val_scaled, dtype=torch.float32),
    torch.tensor(y_val, dtype=torch.float32)
)

# Define loss
criterion = nn.MSELoss()

# Wrap test data into a Dataset and DataLoader
test_dataset = TensorDataset(
    torch.tensor(X_test_scaled, dtype=torch.float32),
    torch.tensor(y_test, dtype=torch.float32)
)


# Sanity check
x0, y0 = train_dataset[0]
print("Sample input shape:", x0.shape)
print("Sample target shape:", y0.shape)


# %%
X_df

# %%
y_df

# %% [markdown]
# # Model
# 
# Model Definition

# %%
import torch.nn as nn

class IMULSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, fc_hidden_size=64):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)

        self.fc1 = nn.Linear(hidden_size, 128)
        self.relu1 = nn.ReLU()
        # self.fc2 = nn.Linear(128, 64)
        # self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(128, output_size)

        self.output_activation = nn.Sigmoid()  # <-- Add this

    def forward(self, x):
        batch_size = x.size(0)
        out, _ = self.lstm(x)
        x = out[:, -1, :]  # last time step
        x = self.relu1(self.fc1(x))
        # x = self.relu2(self.fc2(x))
        x = self.fc3(x)
        x = self.output_activation(x)  # <-- Apply Sigmoid
        return x * 180.0  # <-- Scale output to [0, 180]


# %% [markdown]
# Logging Setup

# %%
# Setup log directory
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_dir = os.path.join('logs', f'run_{timestamp}')
os.makedirs(log_dir, exist_ok=True)

LOG_PATH = os.path.join(log_dir, 'training_log.txt')
csv_path = os.path.join(log_dir, 'metrics.csv')
SAVE_STDOUT = True  # If True, also print to terminal


# %% [markdown]
# CSV Logging Setup

# %%
# Metrics CSV setup
csv_fields = ['epoch', 'train_mse', 'train_mae', 'train_rmse', 'train_r2',
              'val_mse', 'val_mae', 'val_rmse', 'val_r2']

csv_file = open(csv_path, mode='w', newline='')
csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
csv_writer.writeheader()


# %%
print("Target sample shape:", train_dataset[0][1].shape)


# %% [markdown]
# Logger Class

# %%
class DualLogger:
    def __init__(self, filepath, print_to_stdout=True):
        self.log_file = open(filepath, 'w')
        self.print_to_stdout = print_to_stdout

    def log(self, text):
        self.log_file.write(text + '\n')
        self.log_file.flush()
        if self.print_to_stdout:
            print(text)

    def close(self):
        self.log_file.close()

logger = DualLogger(LOG_PATH, print_to_stdout=SAVE_STDOUT)


# %% [markdown]
# Hyperparameters and Summary

# %%
# Hyperparameters
hidden_size = 256
num_layers = 2
batch_size = 70
epochs = 50
learning_rate = 1e-3

# Show config info
print("=" * 70)
print(f"Training started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
print(f"Hyperparameters:")
print(f"  Hidden Size   = {hidden_size}")
print(f"  Num Layers    = {num_layers}")
print(f"  Batch Size    = {batch_size}")
print(f"  Epochs        = {epochs}")
print(f"  Learning Rate = {learning_rate}")
print(f"  Window Size   = {window_size}")
print("=" * 70)

# Save config to file
hyperparams = {
    "hidden_size": hidden_size,
    "num_layers": num_layers,
    "batch_size": batch_size,
    "epochs": epochs,
    "learning_rate": learning_rate,
    "window_size": window_size,
}
with open(os.path.join(log_dir, 'hyperparameters.json'), 'w') as f:
    json.dump(hyperparams, f, indent=2)


# %% [markdown]
# Model, Optimizer, Dataloaders

# %%
# Dataloaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size)

# Model setup
input_size = train_dataset[0][0].shape[1]
output_size = train_dataset[0][1].shape[0]
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = IMULSTMModel(input_size, hidden_size, num_layers, output_size).to(device)
optimizer = Adam(model.parameters(), lr=learning_rate)
mse_loss_fn = nn.MSELoss()
mae_loss_fn = nn.L1Loss()
# ── Log model architecture ───────────────────────────────
arch_path = os.path.join(log_dir, 'model_architecture.txt')
with open(arch_path, 'w') as f:
    f.write(str(model))
print(f"Saved model architecture to: {arch_path}")


# %% [markdown]
# Training Loop

# %%
# --- Clean Training Loop ---
import numpy as np
import torch
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger.log(f"\nStarting training for {epochs} epochs...\n")

# Early stopping parameters
early_stopping_patience = 10
best_val_loss = np.inf
epochs_without_improvement = 0

for epoch in range(epochs):
    # --- TRAINING PASS ---
    model.train()
    batch_train_preds = []
    batch_train_trues = []

    for batch_idx, (X_batch, y_batch) in enumerate(train_loader):
        Xb = X_batch.to(device)
        yb = y_batch.to(device)

        preds = model(Xb)

        loss = mse_loss_fn(preds, yb)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        batch_train_preds.append(preds.detach().cpu())
        batch_train_trues.append(yb.detach().cpu())

        if (batch_idx + 1) % 100 == 0 or (batch_idx + 1) == len(train_loader):
            avg_batch_loss = loss.item()
            logger.log(f"  Batch {batch_idx+1:>4}/{len(train_loader)} – Scaled MSE Loss: {avg_batch_loss:.4f}")

    # --- EPOCH TRAIN METRICS ---
    epoch_train_targets = torch.cat(batch_train_trues).numpy()
    epoch_train_preds   = torch.cat(batch_train_preds).numpy()



    mse_train = mean_squared_error(epoch_train_targets.ravel(), epoch_train_preds.ravel())
    rmse_train = np.sqrt(mse_train)
    mae_train = mean_absolute_error(epoch_train_targets.ravel(), epoch_train_preds.ravel())
    r2_train = r2_score(epoch_train_targets.ravel(), epoch_train_preds.ravel())

    # --- VALIDATION PASS ---
    model.eval()
    batch_val_preds = []
    batch_val_trues = []

    with torch.no_grad():
        for X_val_batch, y_val_batch in val_loader:
            Xv = X_val_batch.to(device)
            yv = y_val_batch.to(device)

            preds = model(Xv)

            batch_val_preds.append(preds.cpu())
            batch_val_trues.append(yv.cpu())

    epoch_val_targets = torch.cat(batch_val_trues).numpy()
    epoch_val_preds   = torch.cat(batch_val_preds).numpy()



    mse_val = mean_squared_error(epoch_val_targets.ravel(), epoch_val_preds.ravel())
    rmse_val = np.sqrt(mse_val)
    mae_val = mean_absolute_error(epoch_val_targets.ravel(), epoch_val_preds.ravel())
    r2_val = r2_score(epoch_val_targets.ravel(), epoch_val_preds.ravel())

    # --- LOG METRICS ---
    logger.log(f"Epoch {epoch+1}/{epochs}")
    logger.log(f"  ↳ Train (deg) → MSE: {mse_train:.2f}, MAE: {mae_train:.2f}, RMSE: {rmse_train:.2f}°, R²: {r2_train:.4f}")
    logger.log(f"  ↳ Val   (deg) → MSE: {mse_val:.2f}, MAE: {mae_val:.2f}, RMSE: {rmse_val:.2f}°, R²: {r2_val:.4f}")
    logger.log("-" * 70)

    csv_writer.writerow({
        'epoch': epoch + 1,
        'train_mse': mse_train,
        'train_mae': mae_train,
        'train_rmse': rmse_train,
        'train_r2': r2_train,
        'val_mse': mse_val,
        'val_mae': mae_val,
        'val_rmse': rmse_val,
        'val_r2': r2_val,
    })
    csv_file.flush()

    # --- EARLY STOPPING CHECK ---
    if mse_val < best_val_loss:
        best_val_loss = mse_val
        epochs_without_improvement = 0
        best_model_state = model.state_dict()
    else:
        epochs_without_improvement += 1
        logger.log(f"  ↳ No improvement for {epochs_without_improvement} consecutive epochs.")

    if epochs_without_improvement >= early_stopping_patience:
        logger.log(f"Early stopping triggered after {epoch+1} epochs (patience {early_stopping_patience}).")
        break

# --- AFTER TRAINING ---
csv_file.close()
logger.close()

# Save the best model state
model.load_state_dict(best_model_state)


# %% [markdown]
# Target Distribution Inspection

# %%
# Inspect target (y) distribution in training and validation sets
train_y = train_dataset[:][1]
val_y = val_dataset[:][1]

print("Train y mean/std:", train_y.mean().item(), train_y.std().item())
print("Val   y mean/std:", val_y.mean().item(), val_y.std().item())
print("Train y min/max:", train_y.min().item(), train_y.max().item())
print("Val   y min/max:", val_y.min().item(), val_y.max().item())


# %% [markdown]
# Save Model Weights

# %%
# Save the trained model weights
weights_path = os.path.join(log_dir, "model_weights.pth")
torch.save(model.state_dict(), weights_path)

# %% [markdown]
# Setup for Test Evaluation

# %%
test_loader = DataLoader(test_dataset, batch_size=batch_size)

# %% [markdown]
# Run Test Evaluation

# %%
# --- Imports ---
import torch
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# --- Evaluation Setup ---
model.eval()

all_preds = []
all_targets = []

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        Xb = X_batch.to(device)
        yb = y_batch.to(device)

        preds = model(Xb)

        all_preds.append(preds.cpu())
        all_targets.append(yb.cpu())

# --- Concatenate Predictions and Targets ---
y_true = torch.cat(all_targets, dim=0).numpy()
y_pred = torch.cat(all_preds, dim=0).numpy()



# --- Print First 5 Samples (Degrees) ---
print("\nFirst 5 Samples: Predicted vs Actual (Degrees)\n")
for i in range(min(5, len(y_true))):
    print(f"Sample {i+1}:")
    print(f"  Actual   : {np.round(y_true[i], 2)}")
    print(f"  Predicted: {np.round(y_pred[i], 2)}")
    print("-" * 70)

# --- Compute Metrics ---


# Degree-space metrics
mse_deg = mean_squared_error(y_true.ravel(), y_pred.ravel())
rmse_deg = np.sqrt(mse_deg)
mae_deg = mean_absolute_error(y_true.ravel(), y_pred.ravel())
r2_deg = r2_score(y_true.ravel(), y_pred.ravel())

# --- Print Metrics ---
print(f"\nDegree-space Metrics:")
print(f"  MSE  : {mse_deg:.2f}°")
print(f"  MAE  : {mae_deg:.2f}°")
print(f"  RMSE : {rmse_deg:.2f}°")
print(f"  R²   : {r2_deg:.4f}")

# --- Save Metrics ---
metrics = {
    "deg_mse": mse_deg,
    "deg_rmse": rmse_deg,
    "deg_mae": mae_deg,
    "deg_r2": r2_deg
}
df_metrics = pd.DataFrame([metrics])
csv_path = os.path.join(log_dir, "test_metrics.csv")
df_metrics.to_csv(csv_path, index=False)
print(f"\nSaved test metrics to: {csv_path}")

# --- Plot Actual vs Predicted (Degrees) ---
n_samples = min(100, len(y_true))
num_dims_to_plot = min(3, y_true.shape[1])

plt.figure(figsize=(14, 7))
for dim in range(num_dims_to_plot):
    plt.plot(y_true[:n_samples, dim], label=f'Actual Angle {dim}', linewidth=2)
    plt.plot(y_pred[:n_samples, dim], label=f'Predicted Angle {dim}', linestyle='--', linewidth=2)

plt.title('Selected Angles: Actual vs Predicted on Test Set (Degrees)')
plt.xlabel('Sample Index')
plt.ylabel('Angle (Degrees)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

max_points = 2000  # adjust as needed
y_true_flat = y_true.ravel()
y_pred_flat = y_pred.ravel()

if len(y_true_flat) > max_points:
    indices = np.random.choice(len(y_true_flat), size=max_points, replace=False)
    y_true_sampled = y_true_flat[indices]
    y_pred_sampled = y_pred_flat[indices]
else:
    y_true_sampled = y_true_flat
    y_pred_sampled = y_pred_flat

plt.figure(figsize=(7, 7))
plt.scatter(y_true_sampled, y_pred_sampled, alpha=0.5)
plt.plot(
    [y_true_sampled.min(), y_true_sampled.max()],
    [y_true_sampled.min(), y_true_sampled.max()],
    'r--'
)

plt.title('Predicted vs Actual Scatter Plot (Degrees)')
plt.xlabel('Actual Angle (deg)')
plt.ylabel('Predicted Angle (deg)')
plt.grid(True)
plt.axis('equal')
plt.tight_layout()


os.makedirs(log_dir, exist_ok=True)
plot_path = os.path.join(log_dir, "scatter_plot.png")
plt.savefig(plot_path, dpi=300)

plt.show()


# %% [markdown]
# Convert Test Outputs to NumPy (Optional for Analysis/Plotting)

# %%
# Convert predictions and targets to NumPy for visualization or metrics
all_preds = torch.cat(all_preds).numpy()
all_targets = torch.cat(all_targets).numpy()

# %%
print(all_preds.shape, all_targets.shape)



# %%
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import torch

# --- Step 0: Ensure tensors in all_preds and all_targets ---
all_preds = [torch.as_tensor(p) if isinstance(p, np.ndarray) else p for p in all_preds]
all_preds = [p.view(1, -1) if p.ndim == 1 else p for p in all_preds]

all_targets = [torch.as_tensor(t) if isinstance(t, np.ndarray) else t for t in all_targets]
all_targets = [t.view(1, -1) if t.ndim == 1 else t for t in all_targets]

# --- Step 1: Concatenate tensors ---
y_pred_tensor = torch.cat(all_preds, dim=0)
y_true_tensor = torch.cat(all_targets, dim=0)

# --- Step 2: Inverse transform to original scale ---
y_pred = y_pred_tensor.numpy()
y_true = y_true_tensor.numpy()

# --- Step 3: Compute per-joint errors ---
n_joints = y_true.shape[1]
mse_list = []
rmse_list = []
mae_list = []
r2_list = []

for i in range(n_joints):
    mse = mean_squared_error(y_true[:, i], y_pred[:, i])
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
    r2 = r2_score(y_true[:, i], y_pred[:, i])

    mse_list.append(mse)
    rmse_list.append(rmse)
    mae_list.append(mae)
    r2_list.append(r2)

# --- Step 4: Organize into DataFrame ---
joint_names = [
    "right ankle", "left ankle", "right knee", "left knee", "right hip", "left hip",
    "right shoulder", "left shoulder", "right elbow", "left elbow",
    "right foot", "left foot", "right shank", "left shank",
    "right thigh", "left thigh", "pelvis", "trunk", "shoulders", "head",
    "right arm", "left arm", "right forearm", "left forearm"
]

joint_errors = pd.DataFrame({
    "Joint": joint_names,
    "MSE": mse_list,
    "RMSE": rmse_list,
    "MAE": mae_list,
    "R2": r2_list
}).sort_values(by="RMSE")

# --- Step 5: Display best/worst joints ---
print("Best joints (lowest RMSE):")
print(joint_errors.head(5))
print("\nWorst joints (highest RMSE):")
print(joint_errors.tail(5))

# --- Step 6: Plot RMSE ---
plt.figure(figsize=(12, 5))
plt.bar(joint_errors["Joint"], joint_errors["RMSE"])
plt.xticks(rotation=90)
plt.ylabel("RMSE (degrees)")
plt.title("Per-Angle RMSE")
plt.grid(True)
plt.tight_layout()

os.makedirs(log_dir, exist_ok=True)

# Step 7: Save plot
plot_path = os.path.join(log_dir, "per_joint_rmse.png")
plt.savefig(plot_path, dpi=300)
plt.show()
print(f"Plot saved to: {plot_path}")

# Step 8: Save metrics to CSV
metrics_path = os.path.join(log_dir, "per_joint_errors.csv")
joint_errors.to_csv(metrics_path, index=False)
print(f"Metrics saved to: {metrics_path}")


# %% [markdown]
# PLOTS

# %%
import pandas as pd
import matplotlib.pyplot as plt

# --- Load Metrics CSV ---
metrics_path = log_dir  # Adjust path if needed
metrics_csv = os.path.join(metrics_path, 'metrics.csv')
df = pd.read_csv(metrics_csv)

# --- Plot Configuration ---
plt.style.use("seaborn-v0_8-whitegrid")  # for Matplotlib 3.6+

fig, axs = plt.subplots(4, 1, figsize=(8, 12))

metrics = [
    ("train_rmse", "val_rmse", "RMSE"),
    ("train_r2", "val_r2", "R²"),
    ("train_mse", "val_mse", "MSE"),
    ("train_mae", "val_mae", "MAE")
]

for idx, (train_col, val_col, label) in enumerate(metrics):
    axs[idx].plot(df["epoch"], df[train_col], label=f"Train {label}", marker='o')
    axs[idx].plot(df["epoch"], df[val_col], label=f"Validation {label}", marker='x')
    axs[idx].set_title(f"Training vs Validation {label}", fontsize=11)
    axs[idx].set_xlabel("Epoch")
    if (label == "RMSE" or label == "MAE"):
       axs[idx].set_ylabel(label+" (degrees)")
    else: 
        axs[idx].set_ylabel(label)
    axs[idx].legend()
    axs[idx].grid(True)

plt.tight_layout()

# --- Save Plots ---
fig.savefig(os.path.join(log_dir,"training_validation_metrics.png"), dpi=300)

print("Saved: training_validation_metrics.png")


# %%
# --- Get best and worst joints by RMSE ---
joint_errors_sorted = joint_errors.sort_values(by="RMSE", ascending=True)
best_joint = joint_errors_sorted.iloc[0]
worst_joint = joint_errors_sorted.iloc[-1]

# --- Define time slice range for zooming ---
start_idx = 1000
end_idx = start_idx + 100  # narrow time window for clarity

# --- Function to plot a single joint ---
def plot_joint(name, idx, label):
    actual = y_true[start_idx:end_idx, idx]
    predicted = y_pred[start_idx:end_idx, idx]

    plt.figure(figsize=(14, 5))
    plt.plot(actual, label="Actual", linewidth=2)
    plt.plot(predicted, label="Predicted", linestyle='--', linewidth=2)
    plt.title(f"{label} Predicted Angle: {name} – Actual vs Predicted (Degrees)\nSamples {start_idx} to {end_idx}")
    plt.xlabel("Sample Index")
    plt.ylabel("Angle (degrees)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    filename = f"{label.lower()}_angle_{name.replace(' ', '_').lower()}_zoomed.png"
    path = os.path.join(log_dir, filename)
    plt.savefig(path, dpi=300)
    plt.show()

    print(f"{label} joint plot saved: {path}")

# --- Plot worst joint ---
plot_joint(worst_joint["Joint"], joint_names.index(worst_joint["Joint"]), "Worst")

# --- Plot best joint ---
plot_joint(best_joint["Joint"], joint_names.index(best_joint["Joint"]), "Best")



