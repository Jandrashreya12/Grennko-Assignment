# Evaluation results

Command: `python -m evaluation.evaluate`

This is a point-event demonstration using five synthetic injected-event proxy labels (sample IDs 67–69 and 173–174), not verified operational fault labels.

| Metric | Result |
|---|---:|
| True negatives | 230 |
| False positives | 5 |
| False negatives | 0 |
| True positives | 5 |
| Precision | 0.500 |
| Recall | 1.000 |
| F1 | 0.667 |
| Accuracy | 0.979 |

All five proxy events were detected, with five additional readings flagged. The small synthetic sample makes these metrics unsuitable for predicting field performance. See the README for assumptions and limitations.
