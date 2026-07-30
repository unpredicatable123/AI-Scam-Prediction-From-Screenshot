# External real-world datasets

Downloaded 2026-07-30, not committed to git (see `.gitignore` — licensing
terms weren't clear enough to redistribute publicly, so they stay local).
Neither is wired into `ml/generate.py` or `train.py` yet — that's a
follow-up step, not done here.

## mendeley_sms_phishing/Dataset_5971.csv

5,971 real SMS messages, labeled `ham` / `spam` / `Smishing` (case is
inconsistent in the source file — normalize before use). Columns: LABEL,
TEXT, URL, EMAIL, PHONE.

- Source: https://data.mendeley.com/datasets/f45bkkt8pr/1
- License: CC BY 4.0 — redistribution is fine with attribution, kept local
  here only because it hasn't been integrated yet.
- Cite: Sandhya Shankar, Devpriya Soni, "SMS Phishing Dataset for Machine
  Learning and Pattern Recognition," Mendeley Data.

## smishtank_dataset.csv

1,062 real smishing messages sourced from smishtank.com's community
submissions. Much richer than the Mendeley set: includes sender,
timestamp, extracted URL/subdomain/domain/TLD, redirected URL,
malicious/phishing/suspicious flags, impersonated brand, message category,
and domain registrar/creation/update dates. Directly useful for validating
`brand_guard.py` (real brand-impersonation examples) and the URL
intelligence checks (real registrar/domain-age data, which the current
pipeline doesn't use at all yet).

- Source: https://smishtank.com/dataset
- License: no explicit redistribution license found — only a citation
  requirement in their Terms of Use. Do not push this file to a public
  repo without checking with them first.
- Cite: Timko, D. and Rahman, M.L., "Commercial Anti-Smishing Tools and
  Their Comparative Effectiveness Against Modern Threats," Proceedings of
  the 16th ACM Conference on Security and Privacy in Wireless and Mobile
  Networks, 2023.
