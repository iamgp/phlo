# generate_bioreactor_sample.py
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime, timedelta
from pathlib import Path

out_dir = Path("data/lake/raw/bioreactor")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "bioreactor_batch001.parquet"

# --- Synthetic metadata ---
batch_id = "BATCH001"
site = "OXB-HQ"
equipment_id = "BIOREACTOR_A1"

# --- Timeline: 12 h of 1-min samples ---
n = 12 * 60
ts = [datetime(2025, 10, 7, 8, 0) + timedelta(minutes=i) for i in range(n)]

# --- Tags we’ll simulate ---
tags = ["pH", "DO", "Temp", "Agitation", "Glucose"]

def noisy_signal(base, noise=0.02, drift=0.0, size=n):
    arr = base * (1 + noise * np.random.randn(size))
    return arr + np.linspace(0, drift * size, size)

# One series per tag (length n each)
series_by_tag = {
    "pH":        noisy_signal(7.2,  noise=0.01, drift=0.0),
    "DO":        noisy_signal(60.0, noise=0.05, drift=-0.001),
    "Temp":      noisy_signal(37.0, noise=0.005, drift=0.0),
    "Agitation": noisy_signal(200.0,noise=0.10, drift=0.0),
    "Glucose":   noisy_signal(4.5,  noise=0.20, drift=-0.002),
}

# Build long-form table: 5 blocks of length n
data = pd.DataFrame({
    "batch_id":     np.repeat(batch_id, len(tags) * n),
    "site":         np.repeat(site, len(tags) * n),
    "equipment_id": np.repeat(equipment_id, len(tags) * n),
    "ts":           np.tile(ts, len(tags)),
    "tag":          np.repeat(tags, n),
    "value":        np.concatenate([series_by_tag[t] for t in tags]),
})

# Ensure dtypes
data["batch_id"] = data["batch_id"].astype("string")
data["site"] = data["site"].astype("string")
data["equipment_id"] = data["equipment_id"].astype("string")
data["tag"] = data["tag"].astype("string")

# Write Parquet
table = pa.Table.from_pandas(data)
pq.write_table(table, out_path)

print(f"✅ Sample written to {out_path.resolve()} ({len(data)} rows)")
print(data.head())
