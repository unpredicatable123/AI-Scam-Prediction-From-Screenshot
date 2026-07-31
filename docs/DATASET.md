# Training dataset

Snapshot as of 2026-07-31, model bundle `model_v3`. Regenerated from
`ml/run_full_batch.sh` (source CSVs + sampling quotas) and
`ml/src/splits/split_dataset.py` (the train/val/calibration/test split).

## Source datasets (13 total)

All samples are rendered into synthetic chat/email screenshots by
`ml/generate.py` — the underlying text is real in every case below, but the
*image* is always a synthetic render, not an actual captured screenshot.

| # | Source | Samples | Type | Notes |
|---|---|---:|---|---|
| 1 | phishing_email.csv | 1,200 | Email | |
| 2 | Enron.csv | 900 | Email | |
| 3 | fake_job_postings.csv | 800 | Job posting | |
| 4 | Mendeley SMS Phishing (Dataset_5971.csv) | 800 | Real SMS | Added 2026-07-31. 5,971 real independently-labeled SMS, CC BY 4.0. `ml/data/external/` |
| 5 | fraud_email_.csv | 750 | Email | |
| 6 | phishing_legit_dataset_KD_10000.csv | 700 | Email | |
| 7 | Fake Postings.csv | 600 | Job posting | |
| 8 | SpamAssasin.csv | 550 | Email | |
| 9 | spam.csv | 550 | SMS | |
| 10 | Nigerian_Fraud.csv | 400 | Email | |
| 11 | Ling.csv | 400 | Email | |
| 12 | Smishtank (smishtank_dataset.csv) | 400 | Real SMS | Added 2026-07-31. 1,062 real community-reported smishing messages. Citation-only license — kept local, not redistributed. `ml/data/external/` |
| 13 | Nazario.csv | 350 | Email | |
| 14 | demo_qr_messages.csv | 4 | QR demo text | |
| | **Total** | **8,404** | | 4,504 fraudulent / 3,900 genuine |

(14 rows because `demo_qr_messages.csv` is counted separately from the 13
named real-world sources — it's a small hand-written QR-payload demo set,
not a third-party dataset.)

## Train / validation / calibration / test split

Ratio: **70% / 10% / 10% / 10%**. Split is group-aware (every render
variant of the same source message stays in one split — verified zero
`group_key`s span multiple splits) and stratified by label.

| Split | Genuine | Fraudulent | Total | Share |
|---|---:|---:|---:|---:|
| Train | 2,730 | 3,151 | 5,881 | 70.0% |
| Validation | 390 | 451 | 841 | 10.0% |
| Calibration | 390 | 451 | 841 | 10.0% |
| Test | 390 | 451 | 841 | 10.0% |
| **Total** | **3,900** | **4,504** | **8,404** | 100% |

- **Train** — fits the Stage-1/Stage-2 classifiers.
- **Validation** — model selection (XGBoost vs Random Forest comparison).
- **Calibration** — isotonic calibration of confidence scores only, kept
  separate from validation so calibration doesn't leak into model selection.
- **Test** — held out entirely until final evaluation. `model_v3`'s reported
  84.2% accuracy / 93.3% ROC-AUC are measured on this split (n=841).

## Result history

| Model | Samples | Accuracy | ROC-AUC | Notes |
|---|---:|---:|---:|---|
| model_v1 | 7,204 | 82.1% | 90.5% | Original 11-source baseline, 47 features |
| model_v2 | 7,204 | 82.8% | 90.8% | Same data, expanded to 67 features |
| model_v3 | 8,404 | 84.2% | 93.3% | + Mendeley + Smishtank real SMS data |
