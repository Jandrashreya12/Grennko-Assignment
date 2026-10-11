"""Reproducible point-event evaluation for the bundled synthetic dataset."""
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score
from backend.app import score_data

# The bundled generator inserts two known elevated temperature/vibration episodes.
# Their row identifiers are documented here as synthetic injection labels, not field truth.
KNOWN_SYNTHETIC_EVENTS = {67, 68, 69, 173, 174}
scored = score_data()
y_true = scored.timestamp_id.astype(int).isin(KNOWN_SYNTHETIC_EVENTS)
y_pred = scored.is_anomaly.astype(bool)
print("Synthetic injected-event proxy labels; evaluate as a demonstration only.")
print("Confusion matrix [[TN, FP], [FN, TP]]:")
print(confusion_matrix(y_true, y_pred, labels=[False, True]).tolist())
print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.3f}")
print(f"Recall:    {recall_score(y_true, y_pred, zero_division=0):.3f}")
print(f"F1:        {f1_score(y_true, y_pred, zero_division=0):.3f}")
print(classification_report(y_true, y_pred, labels=[False, True], target_names=["normal proxy", "injected event"], zero_division=0))
