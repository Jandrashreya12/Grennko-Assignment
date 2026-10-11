# Demo notes

1. Start the API with `uvicorn backend.app:app --reload` and open `http://127.0.0.1:8000`.
2. The fleet cards show the number of telemetry samples and flagged rows for the two bundled assets.
3. Choose `SOLAR_INV_01` or `WTG_07` to focus the findings; select **Explain** on a finding to see its telemetry evidence and recommended operator checks.
4. Solar example: sample 67 has 53.5 °C temperature and 3.86 mm/s vibration, so it is flagged for thermal and vibration review. Wind example: sample 173 has similarly elevated temperature and vibration.
5. API consumers can POST `{"asset_id":"SOLAR_INV_01","limit":50}` to `/api/run` for structured explanations.

The dataset is synthetic. Findings are intended to demonstrate triage language, not diagnose equipment faults.
