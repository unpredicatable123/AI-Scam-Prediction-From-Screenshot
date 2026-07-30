#!/bin/bash
# Full stratified generation batch across all provided real datasets.
# Quotas are hand-picked (not proportional to raw file size) so no single
# large file dominates the corpus, every source contributes real diversity,
# and overall label balance stays close to 50/50 for Stage-1 training.
cd "$(dirname "$0")"
# Output redirected to D: — C: had 0 bytes free mid-batch. D: has 86GB free
# and this project's own footprint on it is small, so no risk of repeating
# the disk-full crash that killed the previous two attempts on C:.
OUT=D:/ai-scam-detection-data/generated
FAILED=""
run() { echo ">>> $*"; "$@" || FAILED="$FAILED\n  $*"; }

echo "=== FRAUDULENT ==="
run python generate.py --input "data/raw/Fake Postings.csv" --source-type scam --output-dir $OUT \
  --text-cols "title,description,requirements,benefits" --label-col fraudulent --sample 600 --seed 101

run python generate.py --input "data/raw/fake_job_postings.csv" --source-type scam --output-dir $OUT \
  --text-cols "title,description,requirements,benefits" --label-col fraudulent --label-filter fraudulent --sample 300 --seed 102

run python generate.py --input "data/raw/Nigerian_Fraud.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter fraudulent --sample 400 --seed 103

run python generate.py --input "data/raw/Nazario.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter fraudulent --sample 350 --seed 104

run python generate.py --input "data/raw/phishing_email.csv" --source-type phishing --output-dir $OUT \
  --label-filter fraudulent --sample 500 --seed 105

run python generate.py --input "data/raw/fraud_email_.csv" --source-type email --output-dir $OUT \
  --label-filter fraudulent --sample 350 --seed 106

run python generate.py --input "data/raw/phishing_legit_dataset_KD_10000.csv" --source-type email --output-dir $OUT \
  --label-filter fraudulent --sample 300 --seed 107

run python generate.py --input "data/raw/SpamAssasin.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter fraudulent --sample 250 --seed 108

run python generate.py --input "data/raw/spam.csv" --source-type scam --output-dir $OUT \
  --label-filter fraudulent --sample 250 --seed 109

run python generate.py --input "data/raw/Enron.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter fraudulent --sample 200 --seed 110

run python generate.py --input "data/raw/Ling.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter fraudulent --sample 200 --seed 111

echo "=== GENUINE ==="
run python generate.py --input "data/raw/phishing_email.csv" --source-type phishing --output-dir $OUT \
  --label-filter genuine --sample 700 --seed 201

run python generate.py --input "data/raw/Enron.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter genuine --sample 700 --seed 202

run python generate.py --input "data/raw/fake_job_postings.csv" --source-type scam --output-dir $OUT \
  --text-cols "title,description,requirements,benefits" --label-col fraudulent --label-filter genuine --sample 500 --seed 203

run python generate.py --input "data/raw/fraud_email_.csv" --source-type email --output-dir $OUT \
  --label-filter genuine --sample 400 --seed 204

run python generate.py --input "data/raw/phishing_legit_dataset_KD_10000.csv" --source-type email --output-dir $OUT \
  --label-filter genuine --sample 400 --seed 205

run python generate.py --input "data/raw/SpamAssasin.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter genuine --sample 300 --seed 206

run python generate.py --input "data/raw/spam.csv" --source-type scam --output-dir $OUT \
  --label-filter genuine --sample 300 --seed 207

run python generate.py --input "data/raw/Ling.csv" --source-type email --output-dir $OUT \
  --text-cols "subject,body" --label-filter genuine --sample 200 --seed 208

echo "=== QR (demo scam text + real QR images — flagged gap, see report) ==="
run python generate.py --input "data/samples/demo_qr_messages.csv" --source-type qr --output-dir $OUT \
  --qr-image-dir "data/raw/benign" --seed 301

echo "=== DONE ==="
if [ -n "$FAILED" ]; then
  echo "FAILED COMMANDS:"
  echo -e "$FAILED"
  exit 1
else
  echo "All commands succeeded."
fi
