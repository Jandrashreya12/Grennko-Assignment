# Renewable Asset Anomaly Copilot

A small, runnable decision-support demo for screening solar inverter and wind turbine telemetry. It combines per-asset Isolation Forest scores with transparent energy-domain rules, exposes the results through FastAPI, and serves a lightweight operator dashboard.

## Run locally

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Open http://127.0.0.1:8000. The data is bundled at `data/asset_telemetry.csv`; no API keys, external services, or network access are needed after installing dependencies.

## What it does

- `GET /api/health`: service health.
- `GET /api/summary`: readings and anomaly counts per asset.
- `GET /api/assets`: available asset IDs.
- `POST /api/run`: score and explain anomalies, optionally scoped to one asset. Example body: `{"asset_id":"SOLAR_INV_01","limit":50}`.
- `GET /api/readings?anomalies_only=true`: readings with anomaly annotations.

Isolation Forest is trained separately per asset so the distinct solar and wind operating regimes are not mixed. The feature set includes hour, resource readings, temperature, vibration, and power. Rule flags call attention to temperature at or above 45 °C, vibration at or above 3.0 mm/s, solar output below 0.15 MW with irradiance at or above 200 W/m², or wind output below 0.05 MW when wind speed is at least 3 m/s. The UI translates these signals into plain language and suggested checks. Anomaly score is relative and is not a probability.

## Evaluation

Run `python -m evaluation.evaluate` to reproduce the point-event metrics. The CSV is synthetic and has no supplied ground-truth labels. For a clearly bounded demonstration only, row IDs 67–69 and 173–174 are treated as injected-event proxy labels because those rows contain the synthetic high-temperature/high-vibration episodes. This is not a production validation set, and results should not be interpreted as real-world accuracy. The script prints confusion matrix, precision, recall, F1, and per-class summary.

## Data and limitations

The bundled CSV contains 240 hourly-indexed samples (120 per asset), but it has no wall-clock timestamps, maintenance records, status codes, curtailment labels, weather context, or verified fault labels. Rules and thresholds are illustrative and must be calibrated by asset class and site. Small-sample Isolation Forest can be unstable and may flag normal rare operating states; repeated readings are evaluated independently. The system does not establish root cause, issue work orders, or replace site safety procedures. Confirm each finding against SCADA state, alarms, work history, and approved operating limits.

A production system needs validated labels, longer seasonal histories, asset-specific operating envelopes, time-aware validation, drift monitoring, alert deduplication, access controls, observability, and operator feedback. Any predictive maintenance claim requires review by qualified reliability engineers.

## Deployment (Railway)

The included `Procfile` starts the FastAPI application on Railway's assigned `$PORT`; the root route serves the frontend and the CSV is included in the repository. To deploy, create a Railway project, connect this repository, and deploy the service with the Python buildpack. No secrets or environment variables are needed. After deploy, check `/api/health` and the dashboard URL.

**Deployment evidence:** not yet available. Add the public Railway URL and a deployment screenshot or successful health-check note after deployment. This workspace currently has no Git repository metadata, and deployment requires a Railway project/account and authorization to publish the service.

## Submission contents

- `backend/app.py`: API, anomaly pipeline, and operator explanations.
- `frontend/index.html`: interactive dashboard.
- `data/asset_telemetry.csv`: bundled runnable dataset.
- `evaluation/evaluate.py` and `evaluation/results.md`: reproducible proxy-label evaluation and the computed results.
- `DEMO_NOTES.md`: short operator walkthrough.
- `PROJECT_GUIDE.md`: detailed architecture, API, evaluation, limitations, and run instructions.
- `submission_instructions.md`, `candidate_task.md`, `evaluation_rubric.md`: assignment documents.




