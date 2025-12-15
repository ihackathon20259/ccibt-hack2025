from __future__ import annotations
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)

def current_plan(customer_id: str) -> str:
    df = load_csv("billing_history.csv")
    df = df[df["customer_id"] == customer_id].copy()
    if df.empty:
        return "Basic"
    df["start_date"] = pd.to_datetime(df["start_date"])
    return df.sort_values("start_date").iloc[-1]["plan"]
