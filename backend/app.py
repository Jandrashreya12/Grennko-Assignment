from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest

BASE = Path(__file__).resolve().parents[1]
DATA_PATH = BASE / "data" / "asset_telemetry.csv"
FEATURES = ["hour", "irradiance_wm2", "wind_speed_ms", "temperature_c", "vibration_mm_s", "power_mw"]
app = FastAPI(title="Renewable Asset Anomaly Copilot", version="1.0.0")

class RunRequest(BaseModel):
    asset_id: str | None = None
    limit: int = Field(default=100, ge=1, le=240)


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise RuntimeError(f"Bundled telemetry file not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    required = {"timestamp_id", "asset_id", *FEATURES}
    missing = required.difference(df.columns)
    if missing:
        raise RuntimeError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    df = df.dropna(subset=list(required)).copy()
    df["timestamp_id"] = pd.to_numeric(df["timestamp_id"], errors="coerce")
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["timestamp_id", *FEATURES])


def explain(row: pd.Series, model_flag: bool) -> tuple[list[str], list[str], str]:
    asset = str(row.asset_id)
    reasons: list[str] = []
    actions: list[str] = []
    if row.temperature_c >= 45:
        reasons.append(f"temperature is elevated at {row.temperature_c:.1f} °C")
        actions.extend(["Check cooling airflow, filters, and ambient conditions.", "Review temperature trend and sensor calibration."])
    if row.vibration_mm_s >= 3.0:
        reasons.append(f"vibration is elevated at {row.vibration_mm_s:.2f} mm/s")
        actions.extend(["Inspect mounting, bearings, and nearby rotating equipment.", "Compare with the asset-specific vibration alarm limits."])
    if asset.startswith("SOLAR") and row.irradiance_wm2 >= 200 and row.power_mw < 0.15:
        reasons.append("power is unusually low while solar irradiance is available")
        actions.extend(["Check inverter state, string output, and grid curtailment records.", "Verify irradiance and power meter readings."])
    if asset.startswith("WTG") and row.wind_speed_ms >= 3 and row.power_mw < 0.05:
        reasons.append("wind is present but recorded turbine output is near zero")
        actions.extend(["Check turbine availability, cut-in state, and active curtailment.", "Review SCADA status and power sensor quality."])
    if not reasons and model_flag:
        reasons.append("the telemetry combination is rare relative to this asset's baseline")
        actions.append("Review adjacent readings and operating state before dispatching maintenance.")
    if not reasons:
        reasons.append("the reading is unusual relative to this asset's baseline")
        actions.append("Compare with neighboring readings, alarms, and the asset's operating limits.")
    severity = "high" if row.temperature_c >= 50 or row.vibration_mm_s >= 3.5 else "medium"
    return reasons, list(dict.fromkeys(actions)), severity


def score_data(asset_id: str | None = None) -> pd.DataFrame:
    df = load_data()
    if asset_id:
        df = df[df.asset_id == asset_id].copy()
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Unknown asset_id: {asset_id}")
    parts = []
    for asset, group in df.groupby("asset_id", sort=False):
        g = group.copy()
        x = g[FEATURES].astype(float)
        model = IsolationForest(n_estimators=200, contamination=0.04, random_state=42)
        model.fit(x)
        g["anomaly_score"] = -model.score_samples(x)
        g["model_flag"] = model.predict(x) == -1
        g["rule_flags"] = g.apply(lambda r: int(r.temperature_c >= 45) + int(r.vibration_mm_s >= 3.0) + int(str(r.asset_id).startswith("SOLAR") and r.irradiance_wm2 >= 200 and r.power_mw < 0.15) + int(str(r.asset_id).startswith("WTG") and r.wind_speed_ms >= 3 and r.power_mw < 0.05), axis=1)
        g["is_anomaly"] = g.model_flag | (g.rule_flags > 0)
        parts.append(g)
    return pd.concat(parts).sort_values("timestamp_id")


def serialize_row(row: pd.Series) -> dict[str, Any]:
    reasons, actions, severity = explain(row, bool(row.model_flag))
    return {
        "timestamp_id": int(row.timestamp_id), "asset_id": str(row.asset_id), "hour": int(row.hour),
        "irradiance_wm2": round(float(row.irradiance_wm2), 1), "wind_speed_ms": round(float(row.wind_speed_ms), 2),
        "temperature_c": round(float(row.temperature_c), 1), "vibration_mm_s": round(float(row.vibration_mm_s), 2),
        "power_mw": round(float(row.power_mw), 3), "anomaly_score": round(float(row.anomaly_score), 4),
        "is_anomaly": bool(row.is_anomaly), "severity": severity if row.is_anomaly else "normal",
        "reasons": reasons if row.is_anomaly else [], "recommended_checks": actions if row.is_anomaly else [],
        "detection": "rule + Isolation Forest" if row.is_anomaly else "baseline"
    }

@app.get("/")
def home():
    return FileResponse(BASE / "frontend" / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "dataset": DATA_PATH.name}

@app.get("/api/summary")
def summary():
    scored = score_data()
    counts = scored.groupby("asset_id").agg(readings=("timestamp_id", "count"), anomalies=("is_anomaly", "sum")).reset_index()
    return {"total_readings": int(len(scored)), "anomaly_count": int(scored.is_anomaly.sum()), "assets": counts.to_dict(orient="records"), "method": "Per-asset Isolation Forest (contamination=0.04, seed=42) plus transparent energy-domain rules."}

@app.post("/api/run")
def run_case(request: RunRequest):
    scored = score_data(request.asset_id)
    anomalies = scored[scored.is_anomaly].sort_values(["rule_flags", "anomaly_score"], ascending=False)
    rows = [serialize_row(row) for _, row in anomalies.head(request.limit).iterrows()]
    return {"asset_id": request.asset_id or "all", "anomaly_count": int(len(anomalies)), "results": rows, "method": "Isolation Forest is fit per asset to respect different solar and wind operating regimes; explicit rules flag high temperature, vibration, and low output under resource availability.", "limitations": ["The bundled data is small synthetic telemetry with no timestamps, fault labels, or asset-specific alarm limits.", "Isolation Forest scores are relative to this sample and are not calibrated probabilities.", "Findings are triage suggestions; confirm against SCADA state, work orders, and site procedures."]}

@app.get("/api/readings")
def readings(asset_id: str | None = None, anomalies_only: bool = False, limit: int = Query(240, ge=1, le=240)):
    scored = score_data(asset_id)
    if anomalies_only:
        scored = scored[scored.is_anomaly]
    return {"count": min(len(scored), limit), "results": [serialize_row(row) for _, row in scored.head(limit).iterrows()]}

@app.get("/api/assets")
def assets():
    return sorted(load_data().asset_id.astype(str).unique().tolist())

app.mount("/static", StaticFiles(directory=BASE / "frontend"), name="static")
