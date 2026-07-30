# AI-Powered Scam Detection from Messaging Screenshots
## Technical Implementation Blueprint v1.0

**Status:** Planning phase — no implementation authorised by this document.
**Audience:** Development team, ML engineers, reviewers/examiners.
**Source of truth:** `AI_Scam_Detection_Project_Document (1).docx` (abstract, related work, objectives, stack, dataset plan).

---

## 0. Assumptions Register

The abstract is detailed but leaves several decisions unspecified. Rather than invent facts silently, every assumption is recorded here with an ID. Anything downstream that depends on an assumption references its ID. **These must be confirmed before Milestone 1 closes.**

| ID | Area | Assumption | Impact if wrong |
|----|------|-----------|-----------------|
| A1 | Label semantics | **CONFIRMED 2026-07-26.** The dataset has **two** labels (`label` = genuine/fraudulent, `scamCategory` = one of 7). The model is **hierarchical**: Stage 1 binary, Stage 2 seven-class conditional on "fraudulent". A genuine screenshot has no meaningful scam category. | — |
| A2 | Scale | Academic/research deployment: ≤ 5,000 registered users, ≤ 200 analyses/day at peak, single region. Architecture is designed so it *can* scale, but v1 is not provisioned for it. | Over-engineering cost, or under-provisioning at demo time. |
| A3 | Languages | **CONFIRMED 2026-07-26: English only for v1.** No Hindi/Devanagari or Hinglish lexicon work in the initial build; simplifies OCR language packs (`eng` only), `langdetect` usage, and NLP lexicons. Multilingual support is Phase 2. | — |
| A4 | Deployment | Frontend on a Node-capable host; Python service as a **container** (Cloud Run / Railway / Fly.io). Not serverless-function-based, because Tesseract/OpenCV/model weights exceed serverless limits and cold-start budgets. | Deployment milestone rework. |
| A5 | Data source | **CONFIRMED 2026-07-26.** Not a from-scratch collected corpus. The user will supply existing scam, QR, phishing, and email-scam datasets in **raw text/CSV format** (labeled messages/emails — not images, not real screenshots). Every sample must pass through the synthetic screenshot-rendering pipeline (§19 O-list) before OCR/CV/layout training can use it; this is now the *primary* data pipeline, not a volume supplement. "QR dataset" here almost certainly means QR-related scam text/payload URLs, not QR pixel data — synthetic QR images will need to be generated to embed those real payloads. | **Elevated leakage risk (§18.3 R10):** with zero real screenshots so far, the "real-only test subset" safeguard can't be satisfied unless real screenshots are sourced separately later. `groupKey` + group-aware splitting is even more critical here, not optional. |
| A6 | Consent & ethics | **CONFIRMED 2026-07-26: no formal institutional ethics/IRB requirement for this project.** The redaction/PII discipline in §7.2 (`pii.redacted`, `pii.reviewedBy`) is still recommended good practice if any real third-party screenshots are used, but is no longer a blocking process step. | — |
| A7 | "Logo detection" scope | Interpreted as **brand impersonation detection over a closed set** (~30–60 known brands: banks, couriers, wallets, marketplaces), not open-world logo recognition. | Model scope and CV milestone size. |
| A8 | Real-time-ness | Analysis is **near-real-time (target p95 < 8 s)**, not interactive-instant. The UX is an async job with progress, not a blocking request. | Frontend and API contract design. |
| A9 | Language of implementation | Frontend stays **JavaScript + JSDoc types** unless the team elects TypeScript in M0. Shared contracts are defined as JSON Schema regardless. | §6 shared-types layout. |
| A10 | Model serving | Models are served **in-process** inside the FastAPI container (scikit-learn/XGBoost artifacts loaded at startup). No separate TF-Serving/Triton tier at v1. | §4 component count. |

---

## 1. Project Understanding

### 1.1 The project in plain terms

A person receives a suspicious message — a job offer, an OTP request, a payment link, a QR code, a lottery win. Most of the time, what they actually have in hand is a **screenshot**: forwarded from a friend, captured from a chat they can no longer scroll back to, or taken because copying text out of the app is awkward. Every existing scam-checking tool asks them to paste text or a URL. If all you have is a picture, those tools are useless.

This system takes the picture as the primary input. It cleans up the image, reads the text out of it, understands what that text is *asking the user to do*, separately looks at the non-text parts of the image (QR codes, brand logos, the visual layout of the chat), combines both signals, and returns a verdict: is this a scam, what kind of scam, how confident is the system, why does it think so, and what should the user do next.

### 1.2 The real-world problem

Three distinct failures compound:

1. **Input-format mismatch.** Fraud arrives as an image; detection tools consume text. The user is forced into manual transcription, which they won't do, so they act on instinct instead.
2. **Vertical fragmentation.** SMS-spam classifiers ignore WhatsApp. Job-scam detectors ignore OTP fraud. QR "quishing" detectors ignore the conversation that delivered the QR. A victim doesn't experience these as separate problems — they experience one message.
3. **Opaque verdicts.** A tool that says "85% spam" does not change behaviour. A tool that says *"this message asks you to pay a ₹2,000 'registration fee' for a job, uses urgency language, and links to a domain registered 6 days ago — do not pay, verify the company on its official site"* does. Trust is the actual product; the classifier is only the engine.

The population most exposed — first-time smartphone users, elderly users, job seekers — is exactly the population least able to reason about a bare probability.

### 1.3 Where the novelty actually sits

The novelty is **not** OCR (mature), **not** Random Forest/XGBoost (standard), and **not** SHAP (standard). Claiming otherwise weakens the work. The defensible novelty is the **combination and the input modality**:

| Axis | Prior work | This project |
|------|-----------|--------------|
| Input | Text corpora, URLs, or *browser-rendered webpage* screenshots | **Chat-UI screenshots** — a visually distinct domain (bubbles, avatars, timestamps, tick marks) that no reviewed work models |
| Platforms | One platform per paper | Five in one pipeline, with platform as both a routing signal and a feature |
| Output granularity | Binary (spam / phishing yes-no) | Binary **+ seven-class taxonomy** |
| Modality fusion | Text-only, or vision-only, or fusion for *webpages* | Text ⊕ vision fusion **for messaging screenshots** — the gap the related-work table establishes |
| Explanation | Present only in the single-domain job-scam work | Multi-category, with category-conditional recommendations |
| Data | Reused single-purpose public datasets | **New annotated multi-platform screenshot corpus** |

### 1.4 Research contributions (rank-ordered for defensibility)

1. **The dataset.** A multi-platform, multi-category, dual-labelled (genuine/fraudulent × 7 categories) annotated messaging-screenshot corpus with OCR ground truth. This is the contribution most likely to be cited and the hardest for a reviewer to dispute. It is also the contribution most at risk (§18) and must be resourced first.
2. **The fusion formulation for chat UIs.** A documented, reproducible feature schema that fuses OCR/NLP features with QR/logo/layout features specifically for chat interfaces, with an **ablation study** quantifying what the visual branch adds over text alone. Without the ablation, the fusion claim is unsupported — this ablation is a required deliverable, not a nice-to-have.
3. **Category-conditional explainability.** Extending SHAP-backed explanation from a single vertical into a seven-category setting, including the mapping from feature attributions to human-readable reasons and to *category-specific* recommended actions.
4. **A chat-structure-aware preprocessing stage** (§10.6). Segmenting the screenshot into incoming vs. outgoing message bubbles before OCR — so the model can distinguish "*they* asked me for an OTP" from "*I* sent an OTP" — is a low-cost idea absent from all reviewed work and materially affects accuracy on OTP/banking categories.

> **Framing note for the report:** Position the work as *systems + dataset* research, not as a novel-algorithm paper. The reviewed 2024–2026 literature is beaten on coverage and integration, not on modelling sophistication. Reviewers punish overclaimed algorithmic novelty; they reward a well-built dataset and an honest ablation.

---

## 2. Functional Requirements

Modules are given stable IDs (`FE-*` frontend, `BE-*` backend, `AI-*` AI service, `AD-*` admin, `DS-*` dataset) used throughout §16–17.

### 2.1 User-facing features

| ID | Module | Requirements |
|----|--------|-------------|
| FE-01 | **Onboarding & Auth** | Email/password sign-up, Google sign-in, email verification, password reset, sign-out, session persistence. Guest/anonymous mode for one-off checks (rate-limited, no history). |
| FE-02 | **Screenshot Upload** | Drag-and-drop dropzone, file picker, clipboard paste (Ctrl+V of a screenshot — high-value for this use case), mobile camera/gallery. Client-side validation: type (PNG/JPEG/WebP/HEIC), size (≤ 10 MB), min dimensions (≥ 300×300). Client-side downscale to ≤ 2000 px long edge before upload. Multi-file queue (≤ 5). |
| FE-03 | **Pre-submit Redaction** | Optional user-driven blur/box tool to mask phone numbers, names, and avatars before upload. Also offers *auto-suggested* redaction boxes from detected PII (A6). |
| FE-04 | **Analysis Progress** | Live per-stage progress (uploading → preprocessing → OCR → analysing → explaining) with cancel. Never a blank spinner (A8). |
| FE-05 | **Result Dashboard** | Verdict banner (Safe / Suspicious / Dangerous), scam category with icon, calibrated confidence, risk score 0–100, top contributing reasons in plain language, extracted text panel with low-confidence tokens visually flagged, detected entities (URLs, UPI IDs, phone numbers, amounts), QR decode result, brand-impersonation notice. |
| FE-06 | **Explanation Detail** | Expandable "why" view: ranked feature contributions rendered as a readable bar chart, evidence highlighted on the original image via bounding-box overlay, and a short methodology note. |
| FE-07 | **Recommended Actions** | Category-specific, actionable checklist (e.g. QR scam → "do not scan; verify the payee name in your UPI app before approving"), plus one-tap copy of a reporting template and links to official reporting channels (e.g. national cybercrime portal). |
| FE-08 | **History** | Paginated list of the user's past analyses with thumbnail, verdict, category, date. Filter by category/verdict/date. Open any past result. |
| FE-09 | **Feedback Loop** | "Was this correct?" — agree / disagree + correct category + free-text. Feeds active learning (AI-20). |
| FE-10 | **Data Controls** | View stored data, delete an individual analysis (image + record), delete account, export history as JSON, and an explicit **consent toggle for research use** of the uploaded screenshot (A6). |
| FE-11 | **Education Layer** | Static library of scam-type explainers and a "how this system works / what it can't do" limitations page. Required for responsible deployment. |
| FE-12 | **Accessibility & i18n** | Full keyboard operation, screen-reader labelling, colour-blind-safe verdict encoding (never colour alone), locale-ready copy strings. |

### 2.2 AI features

| ID | Module | Purpose |
|----|--------|---------|
| AI-01 | Image validation & integrity | Reject non-screenshots, corrupt files, and (heuristically) non-chat imagery. |
| AI-02 | Preprocessing | Denoise, deskew, contrast/CLAHE, adaptive binarisation, upscale. |
| AI-03 | Platform identification | Classify source app (WhatsApp/Telegram/SMS/Instagram/Email/Unknown). |
| AI-04 | Chat structure parsing | Segment message bubbles; assign direction (incoming/outgoing); order by position. |
| AI-05 | OCR | Multi-engine text extraction with per-token confidence and bounding boxes. |
| AI-06 | Text cleaning & normalisation | Unicode/emoji handling, OCR error correction, de-obfuscation. |
| AI-07 | Linguistic NLP features | Urgency, authority, reward, threat, secrecy, grammar-quality signals. |
| AI-08 | NER & entity extraction | URLs, domains, UPI IDs, phone numbers, monetary amounts, organisations, account numbers. |
| AI-09 | URL & entity risk scoring | Lexical URL features, shortener/homoglyph/TLD checks, blocklist lookup. |
| AI-10 | Semantic embeddings | Sentence-BERT vector of the message text. |
| AI-11 | QR detection & decode | Locate, decode, and risk-score embedded QR payloads. |
| AI-12 | Brand impersonation | Match logos/wordmarks against a closed brand set (A7); cross-check against claimed sender. |
| AI-13 | Layout & visual artifacts | Forwarded tags, unknown-number banners, business-account badges, screenshot-of-screenshot detection, compression artifacts. |
| AI-14 | Feature fusion | Assemble the unified feature vector; handle missing branches. |
| AI-15 | Stage-1 classifier | Genuine vs. fraudulent (A1). |
| AI-16 | Stage-2 classifier | Seven-class scam category, conditional on Stage 1. |
| AI-17 | Probability calibration | Make the displayed confidence a *real* probability. |
| AI-18 | SHAP explainer | Per-prediction feature attributions. |
| AI-19 | Explanation generation | Attribution → grounded, human-readable reason strings. |
| AI-20 | Recommendation engine | Category + risk + entities → prioritised safety actions. |
| AI-21 | Feedback & active learning | Surface low-confidence/disagreed samples for annotation. |
| AI-22 | Drift & performance monitoring | Track input and prediction distribution shift over time. |

### 2.3 Backend features

| ID | Module | Purpose |
|----|--------|---------|
| BE-01 | Session management | Firebase ID token → HTTP-only session cookie; refresh; revocation. |
| BE-02 | Upload orchestration | Issue scoped upload targets; validate; register storage objects. |
| BE-03 | Analysis orchestration | Create job, call AI service, persist result, expose status. |
| BE-04 | AI service client | Authenticated service-to-service calls with timeout, retry-with-backoff, and circuit breaker. |
| BE-05 | Persistence layer | All Firestore reads/writes, centralised. No direct client writes to result collections. |
| BE-06 | Rate limiting & quotas | Per-user and per-IP limits; anonymous quota; abuse throttling. |
| BE-07 | Validation layer | Schema validation of every inbound payload at the trust boundary. |
| BE-08 | Audit logging | Structured, correlated logs; security-relevant event trail. |
| BE-09 | Admin authorisation | Custom-claim-based role checks. |
| BE-10 | Dataset ingestion | Route consented screenshots into the annotation queue. |
| BE-11 | Retention & deletion | Scheduled purge per retention policy; cascade delete on account deletion. |
| BE-12 | Health & readiness | Aggregate upstream health for status reporting. |

### 2.4 Admin functionality

Admin is **required**, not optional — the dataset is a primary contribution (§1.4) and cannot be produced without annotation and QA tooling.

| ID | Module | Purpose |
|----|--------|---------|
| AD-01 | Annotation workbench | Image + OCR side-by-side; assign platform, category, label; correct OCR text; draw redaction boxes. |
| AD-02 | Annotation QA | Double-annotation on a sample, inter-annotator agreement (Cohen's/Fleiss' κ), disagreement adjudication queue. |
| AD-03 | Dataset explorer | Filter/count by platform × category × label; export versioned splits with a manifest. |
| AD-04 | Model registry view | Registered model versions, training metadata, evaluation metrics, active version, promote/rollback. |
| AD-05 | Misclassification review | Queue of user-disagreed and low-confidence predictions, with one-click promotion into the dataset. |
| AD-06 | Metrics dashboard | Accuracy/precision/recall/F1 per category, confusion matrix, latency percentiles, OCR confidence distribution, volume. |
| AD-07 | Blocklist management | CRUD for known-malicious domains, UPI IDs, phone numbers; source and expiry tracking. |
| AD-08 | User & abuse management | Suspend accounts, inspect quota usage, respond to data-deletion requests. |

---

## 3. Non-Functional Requirements

Every requirement below is stated with a **measurable target** and a **verification method**. Unverifiable NFRs are not requirements.

### 3.1 Performance

| Metric | Target | Verified by |
|--------|--------|------------|
| End-to-end analysis latency (p50 / p95) | ≤ 3.5 s / ≤ 8 s for a 1080×2400 screenshot (A8) | Load test, 50 concurrent, instrumented per-stage timings |
| Preprocessing | ≤ 250 ms | Per-stage timer emitted in every response |
| OCR | ≤ 2.0 s | Same |
| NLP branch (incl. embedding) | ≤ 800 ms | Same |
| CV branch | ≤ 600 ms | Same |
| Inference + SHAP | ≤ 400 ms | Same |
| Frontend Largest Contentful Paint | ≤ 2.0 s on 4G / mid-tier Android | Lighthouse CI in the build pipeline |
| Frontend JS bundle (initial route) | ≤ 180 KB gzipped | Bundle-size budget enforced in CI |
| AI service cold start | ≤ 20 s, mitigated by min-instances ≥ 1 in demo windows | Deployment smoke test |

**Design consequences:** the text and visual branches run **concurrently**, not sequentially; models and the embedding encoder load **once at process start**, never per request; the embedding model is a small one (`all-MiniLM-L6-v2` class, 384-dim) because a large encoder blows the entire latency budget on its own.

### 3.2 Scalability

- **Stateless AI service.** No request state in process memory → horizontal scaling is a replica-count change.
- **Async-capable contract from day one.** Even though v1 may answer synchronously, the API is shaped as create-job → poll/stream status (§8), so introducing a queue later requires **no client change**. This is the single most important scalability decision in the document.
- **Storage-by-reference.** Images are never passed as base64 through the SvelteKit layer to the AI service in the production path; a storage reference is passed and the AI service reads it directly.
- **Firestore modelling for growth.** Denormalised list-view fields so the history screen never fan-out-reads; composite indexes defined up front (§7).
- Target headroom: 10× the A2 baseline absorbable by configuration only.

### 3.3 Maintainability

- Strict layering: **route → service → repository**. Route handlers contain no business logic and no direct database calls.
- One schema definition per contract, shared by frontend and backend (§6.4); no hand-duplicated shapes.
- Every AI module is a **pure function of its declared inputs** with a fixed output schema, independently testable without the HTTP layer.
- Feature engineering lives in **one module used by both training and inference** — the single most common source of production ML bugs is a training/serving skew introduced by two copies of feature code. This is a hard rule.
- Minimum coverage gates: 80 % on feature-engineering and service layers; 100 % of API contracts covered by schema tests.
- ADRs (architecture decision records) in `docs/adr/` for every irreversible choice.

### 3.4 Reliability

- Graceful degradation ladder: if the CV branch fails → return a text-only prediction flagged `degraded`; if OCR yields text below a confidence floor → return `insufficient_evidence` rather than a guess; if the AI service is unreachable → queue the job and inform the user, never silently drop.
- Idempotent job creation keyed by content hash + user, so a double-submit cannot create duplicate charges on quota or duplicate records.
- Retry policy: 2 retries, exponential backoff with jitter, only on idempotent operations and only for 5xx/timeouts.
- Targets: 99.5 % monthly availability for the web app; ≤ 0.5 % analysis failure rate; RPO 24 h (daily Firestore export), RTO 4 h.

### 3.5 Accessibility

- WCAG 2.1 **AA** as the contractual bar.
- Verdict must never be conveyed by colour alone — always colour **+ icon + text label** (§2.1 FE-12).
- Uploaded-image alternative text is generated from the OCR result, so the extracted text is available to screen-reader users.
- All interactive elements keyboard reachable with a visible focus ring; modal focus trapping; `prefers-reduced-motion` respected.
- Verified by `axe-core` in CI plus one manual screen-reader pass per release.

### 3.6 Security

Full treatment in §18.7. Headline requirements:

- No secret (Firebase Admin credentials, AI service key, model artifacts) is ever reachable from the browser bundle.
- Session state in **HTTP-only, Secure, SameSite=Lax** cookies — never `localStorage`.
- Firestore security rules default-deny; result and dataset collections are **server-write-only**.
- Uploaded files are treated as hostile input: magic-byte type verification (not extension trust), size caps, dimension caps, EXIF stripping, decompression-bomb guards.
- The AI service is **not publicly routable**; it accepts only authenticated calls from the SvelteKit backend.
- CSP with no `unsafe-inline`; strict CORS allowlist; HSTS.

### 3.7 Responsiveness (UI)

- Mobile-first — the primary user is on a phone, because that is where the screenshot was taken. Design at 360 px first, then scale up.
- Breakpoints: 360 / 768 / 1024 / 1440. Touch targets ≥ 44×44 px.
- Result dashboard must be fully usable on a 360 px viewport without horizontal scroll; wide content (feature tables, confusion matrices) scrolls inside its own container.
- Offline-tolerant: upload failures are retryable without losing the selected file.

### 3.8 Extensibility

Named extension points, each requiring **no change** to unrelated modules:

1. **New platform** → add a platform profile (UI colour signature, bubble geometry, header pattern) + retrain the platform classifier.
2. **New scam category** → add taxonomy entry + recommendation template + retrain Stage 2. The taxonomy is data, not an enum hard-coded across the codebase.
3. **New OCR engine** → implement the OCR provider interface; engine choice becomes configuration.
4. **New feature family** → register in the feature schema with a version bump; the fusion layer reads the schema.
5. **New model backend** (e.g. transformer fusion, per §1.4 future work) → implement the classifier interface behind the same predict contract.
6. **New language** → add tokenisation/stopword/keyword resources; no pipeline restructuring.

---

## 4. Complete System Architecture

### 4.1 High-level view

```
                            ┌──────────────────────────────┐
                            │   Browser (mobile-first PWA) │
                            │   SvelteKit client + Tailwind│
                            │   + shadcn-svelte            │
                            └───────────┬──────────────────┘
                                        │ HTTPS, session cookie
                                        ▼
                     ┌───────────────────────────────────────┐
                     │  SvelteKit server (BFF / trust boundary)│
                     │  • +server.js API routes               │
                     │  • hooks.server.js: authN/Z, CSP, rate │
                     │  • services/  (business logic)         │
                     │  • repositories/ (Firestore access)    │
                     │  • Firebase Admin SDK                  │
                     └───┬───────────────┬───────────────┬────┘
                         │               │               │
      Admin SDK (server) │               │ signed URL /  │ service-to-service
                         │               │ storage ref   │ (OIDC / HMAC key)
                         ▼               ▼               ▼
        ┌────────────────────┐  ┌────────────────┐  ┌──────────────────────────┐
        │ Firebase Auth      │  │ Firebase       │  │  Python AI Microservice  │
        │ • identity         │  │ Storage        │  │  FastAPI + Uvicorn       │
        │ • custom claims    │  │ • screenshots  │  │  ┌────────────────────┐  │
        │   (role: admin)    │  │ • thumbnails   │  │  │ Preprocess (OpenCV)│  │
        └────────────────────┘  │ • dataset/     │  │  ├────────┬───────────┤  │
                                └───────┬────────┘  │  │ Text   │ Visual    │  │
        ┌────────────────────┐          │ read      │  │ branch │ branch    │  │
        │ Firebase Firestore │          └──────────►│  │ OCR    │ QR/pyzbar │  │
        │ • users            │                      │  │ NLP    │ Logo CNN  │  │
        │ • analyses         │◄─── server writes ───┤  │ spaCy  │ Layout    │  │
        │ • datasetSamples   │      only            │  │ S-BERT │           │  │
        │ • feedback         │                      │  └────┬───┴────┬──────┘  │
        │ • modelVersions    │                      │       └───┬────┘         │
        │ • blocklists       │                      │      Feature fusion      │
        │ • auditLogs        │                      │           ▼              │
        └────────────────────┘                      │  RF / XGBoost (2-stage)  │
                                                    │  + calibration           │
                                                    │           ▼              │
                                                    │  SHAP → explanation NLG  │
                                                    │  → recommendation engine │
                                                    └──────────┬───────────────┘
                                                               │ loads at startup
                                                               ▼
                                                    ┌──────────────────────────┐
                                                    │ Model artifact store     │
                                                    │ (versioned bundle:       │
                                                    │  models + feature schema │
                                                    │  + calibrators + meta)   │
                                                    └──────────────────────────┘
```

### 4.2 Why each component exists

**SvelteKit client.** Chosen in the abstract. It is genuinely well-suited here: the app is a handful of screens with heavy image interaction and a small JS budget target (§3.1), and Svelte 5 runes give fine-grained reactivity for live progress without a state-management library. Tailwind + shadcn-svelte gives an accessible component baseline (dropzone, cards, badges, alerts, tables) without building a design system from scratch.

**SvelteKit server (the BFF).** This is the **trust boundary**, and it is the reason the browser never talks to the AI service directly. It exists to:
- hold the Firebase Admin credential and the AI service key, which must never reach the client;
- convert a short-lived Firebase ID token into a server-side session;
- enforce rate limits and quotas *before* expensive GPU/CPU work is triggered;
- be the only writer to `analyses`, `datasetSamples`, and `modelVersions`, so client-side tampering cannot forge a verdict;
- shape the AI service's raw output into a UI-friendly response, decoupling the frontend from model internals.

**Python AI microservice.** Separated because the entire ML toolchain — Tesseract, OpenCV, spaCy, scikit-learn, XGBoost, SHAP — is Python-native, and because ML workload has a completely different resource profile (CPU-bound, memory-heavy, slow cold start, infrequent deploys) from the web tier (I/O-bound, light, frequent deploys). Coupling them would mean every UI copy change redeploys a 2 GB container and reloads the models. Separation also allows the ML service to be scaled, versioned, and rolled back independently, and lets ML engineers work without touching the web codebase.

**Firebase Auth.** Removes the need to build and secure credential storage, password reset, and OAuth. Custom claims carry the `admin` role, so authorisation is verifiable server-side from the token without an extra database read on every request.

**Firebase Storage.** Screenshots are large binary blobs with a lifecycle (upload → analyse → optionally retain for dataset → delete). Storage handles that with lifecycle rules and signed URLs. Critically, it lets the AI service **read the image directly** rather than having it proxied through the web tier as base64 — which would inflate payloads ~33 % and put image bytes through a tier that has no reason to see them.

**Firestore.** Document model fits the data (an analysis is one nested document; there are no complex joins). Real-time listeners give the progress UI (FE-04) for free without building websockets. Its weakness — no aggregation queries — is handled by maintaining counters and by exporting to BigQuery for analytics if the admin dashboard outgrows it (§19).

**Model artifact store.** A versioned bundle (models + calibrators + **feature schema** + training metadata) is the unit of deployment for ML. Versioning the feature schema alongside the model is what prevents a silent training/serving skew when features change.

### 4.3 Communication contracts between services

| Path | Protocol | Auth | Notes |
|------|----------|------|-------|
| Browser → SvelteKit | HTTPS / JSON + multipart | Session cookie (HTTP-only) | CSRF token on state-changing requests |
| Browser → Firebase Auth | HTTPS (Firebase SDK) | — | Returns ID token, immediately exchanged for a session cookie |
| Browser → Firebase Storage | HTTPS resumable upload | Short-lived signed URL issued by the BFF | Direct upload avoids proxying large files through the web tier |
| SvelteKit → Firestore / Storage / Auth | Firebase Admin SDK | Service account | Server-only credential |
| SvelteKit → AI service | HTTPS / JSON | OIDC identity token (preferred) or HMAC-signed shared secret | 30 s timeout, 2 retries, circuit breaker |
| AI service → Storage | HTTPS | Service account, read-only, scoped to the screenshots prefix | Least privilege |
| AI service → SvelteKit | *none* (no callback at v1) | — | Deliberately one-directional; if async is introduced, the callback is a signed webhook |

**Design rule:** the AI service is stateless and has **no database access**. It receives a storage reference plus context and returns a result. All persistence is the BFF's job. This keeps the ML team out of the data model and makes the AI service trivially replayable for offline evaluation.

---

## 5. AI Pipeline

### 5.1 Stage flow

```
  [1] Image Upload / Ingestion
        ↓
  [2] Image Validation & Integrity Check ──► reject → structured error
        ↓
  [3] Preprocessing (OpenCV)
        ↓
  [4] Platform Identification
        ↓
  [5] Chat Structure Parsing (bubble segmentation + direction)
        ↓
        ├──────────────── TEXT BRANCH ─────────────────┐   ┌─── VISUAL BRANCH ───┐
        │  [6]  OCR (+ per-token confidence, boxes)    │   │ [11] QR detect/decode│
        │  [7]  Text Cleaning & Normalisation          │   │ [12] Logo / brand    │
        │  [8]  Linguistic NLP Feature Extraction      │   │ [13] Layout & visual │
        │  [9]  NER & Entity Extraction                │   │      artifacts       │
        │  [10] URL / Entity Risk Scoring              │   │                      │
        │  [10b]Semantic Embedding (Sentence-BERT)     │   │                      │
        └──────────────────────┬───────────────────────┘   └──────────┬───────────┘
                               └───────────────┬──────────────────────┘
                                               ▼
                                    [14] Feature Fusion
                                               ▼
                                    [15] Stage-1: genuine vs fraudulent
                                               ▼
                                    [16] Stage-2: 7-class category (if fraudulent)
                                               ▼
                                    [17] Probability Calibration
                                               ▼
                                    [18] SHAP Explanation
                                               ▼
                                    [19] Explanation Generation (NLG)
                                               ▼
                                    [20] Recommendation Engine
                                               ▼
                                    [21] Response Assembly + Telemetry
```

### 5.2 Stage-by-stage specification

**[1] Ingestion.** Input: storage reference + request context (user locale, declared platform if the user picked one, request ID). The service fetches bytes, verifies the object size and content type server-side, and computes a SHA-256 content hash used for idempotency and duplicate detection. Output: decoded image array + metadata.

**[2] Validation & integrity.** Verifies magic bytes match the declared MIME type; enforces max decoded pixel count (decompression-bomb guard); rejects images below a minimum resolution because OCR on them is unreliable; strips EXIF (privacy — screenshots can carry device metadata). A lightweight heuristic gate flags images that are almost certainly not chat screenshots (e.g. a photograph with no text regions and no rectilinear structure) so the system returns "this doesn't look like a chat screenshot" instead of a confident nonsense verdict. **Failure here is a hard stop with a specific error code**, never a silent pass-through.

**[3] Preprocessing.** Purpose: maximise OCR accuracy without destroying the visual information the CV branch needs. Critical design point: **preprocessing forks.** The text branch gets an aggressively processed grayscale/binarised image; the visual branch gets the *original colour* image, because binarisation destroys logo colour, bubble colour (which encodes message direction), and QR contrast. Producing one over-processed image for both branches is a common and costly mistake. Operations: grayscale conversion, bilateral/non-local-means denoising, deskew via Hough-line or minimum-area-rect estimation, CLAHE contrast enhancement, adaptive (Sauvola/Otsu) thresholding, and 2× upscaling when the source is below a DPI threshold. Every operation is individually toggleable and its effect on OCR confidence is measured during tuning — preprocessing that *reduces* accuracy on a given platform is disabled for that platform.

**[4] Platform identification.** A cheap classifier (colour-histogram + header-region template match, with a small CNN as fallback) predicts WhatsApp / Telegram / SMS / Instagram / Email / Unknown. It serves three purposes: it is a **feature** (scam base rates differ by platform), it **routes preprocessing** (per-platform tuned parameters), and it **parameterises bubble segmentation** (each app has distinct bubble geometry and colours). If the user declared a platform in the UI, that declaration is used as a prior but not blindly trusted.

**[5] Chat structure parsing.** Segments the screenshot into message bubbles using contour detection and per-platform colour/geometry profiles, then labels each bubble **incoming** (from the potential scammer) or **outgoing** (from the user) using horizontal alignment and background colour. Output is an ordered list of turns with bounding boxes. This unlocks direction-aware features — *"the incoming message requests an OTP"* is a scam signal; *"the outgoing message contains an OTP"* is a victimisation signal — and both are far stronger than the bag-of-words fact that "OTP appears somewhere". Degrades gracefully: on failure, treat the whole image as one incoming turn and set a `structure_parsed=false` flag that downstream features respect.

**[6] OCR.** Runs the configured engine over each bubble region (better than whole-image OCR: smaller regions, cleaner backgrounds, natural reading order). Produces per-token text, confidence, and bounding box. A **dual-engine strategy** (§10) reruns low-confidence regions with a second engine. Output: structured text per turn + aggregate OCR confidence, which is itself a feature and a gate.

**[7] Text cleaning & normalisation.** Unicode normalisation (NFKC), emoji extraction into a separate feature (emoji density and specific emoji like 🎁💰🔥 are signals — discarding them loses information), whitespace collapse, OCR-confusion correction (`0/O`, `1/l/I`, `rn/m`, `5/S`) applied lexicon-guided rather than blindly, and **de-obfuscation** of deliberate evasion (`w-h-a-t-s-a-p-p`, `paytm[.]com`, zero-width characters, homoglyph substitution). De-obfuscation must be recorded as a feature: the *presence* of obfuscation is one of the strongest scam signals available.

**[8] Linguistic NLP features.** Interpretable, hand-designed feature families (§11.5): urgency, authority/impersonation, reward/greed, threat/fear, secrecy, action-demand, financial-request, grammar quality, capitalisation and punctuation anomalies, message length, and per-category lexicon hit counts. These are the features that will carry the *explanations*, so they are designed for human legibility first and predictive power second.

**[9] NER & entity extraction.** Hybrid: spaCy NER for ORG/PERSON/MONEY/DATE, plus high-precision regex/validator extractors for URLs, domains, UPI VPAs, IFSC codes, Indian and international phone numbers, card-like number patterns, OTP-shaped tokens, and currency amounts. Extracted entities are both features and **user-visible evidence** (FE-05).

**[10] URL & entity risk scoring.** Purely **lexical and offline at v1** — no live network lookups in the request path (latency, privacy, and the fact that a scam URL should never be fetched from the analysis server). Features: URL length, subdomain depth, hyphen/digit counts, IP-literal host, shortener match, punycode/homoglyph presence, suspicious TLD, brand-name-in-subdomain (`sbi.secure-login.xyz`), and blocklist membership from Firestore-cached lists. Optional Phase-2 enrichment (domain age, safe-browsing) runs **asynchronously and out of band**, never blocking the verdict.

**[10b] Semantic embedding.** Sentence-BERT vector of the concatenated incoming-message text. Captures paraphrase and novel phrasings that lexicons miss. Dimensionality is reduced (SVD to ~48–64 dims) before fusion for three reasons: tree models handle a few hundred features far better than a few thousand, SHAP cost grows with feature count, and 384 individually meaningless dimensions would swamp the interpretable features in the attribution ranking (§14.3).

**[11] QR detection & decode.** Locate QR/barcode regions (pyzbar + OpenCV `QRCodeDetector`, with preprocessing retries for low-contrast captures), decode the payload, and risk-score it: is it a UPI payment intent, and if so what is the payee VPA and is an amount pre-filled? Is it a URL, and does it inherit the URL risk features from [10]? Is it a raw text/`tel:`/`SMSTO:` payload? A pre-filled-amount UPI QR embedded in a chat message is close to a decisive signal for the QR-scam category.

**[12] Brand impersonation.** Over a closed brand set (A7): detect logo/wordmark presence via template + embedding similarity matching, then check **consistency** — a message claiming to be from a bank whose logo is absent, or whose logo is present but whose links point to a non-bank domain, is the actual signal. Isolated logo presence is nearly worthless as a feature; *mismatch between claimed identity and evidence* is the feature.

**[13] Layout & visual artifacts.** Platform-specific UI cues that are strong priors: "Forwarded"/"Forwarded many times" tags, "This message is from an unknown number", business-account badges, unsaved-contact phone-number-as-title headers, blue-tick/verification marks, screenshot-of-a-screenshot detection (nested chrome), and JPEG compression-artifact level (heavily recompressed images correlate with mass-forwarded content).

**[14] Feature fusion.** Concatenates the branch outputs into a single fixed-length, **schema-versioned** vector. Responsibilities: enforce feature order (a silent reordering is catastrophic and invisible), apply the declared missing-value policy per feature (a missing QR feature means "no QR", a missing OCR feature means "unknown" — these are *different* and must not both become 0), scale where required, and emit the feature-schema version stamped onto the prediction record. Also produces the feature-group map (which indices belong to which family) that the SHAP layer needs for grouped attribution.

**[15] Stage-1 classifier.** Binary genuine vs. fraudulent (A1). Trained on the full corpus. Optimised for **recall on fraudulent** with a tunable threshold, because a missed scam costs far more than a false alarm — see §13.9.

**[16] Stage-2 classifier.** Seven-class category, invoked only when Stage 1 predicts fraudulent above threshold. Trained only on fraudulent samples. This hierarchy is preferred to a flat 8-class model because the genuine class is heterogeneous and would otherwise contaminate category boundaries, because the two stages want different features and different thresholds, and because the binary decision — the one the user actually acts on — stays clean and separately tunable.

**[17] Calibration.** Raw tree-ensemble scores are **not probabilities** and are typically overconfident. Since the UI shows a confidence number and users will anchor on it, an uncalibrated score is an honesty problem, not just a metrics problem. Isotonic regression (or Platt scaling if data is scarce) is fitted on a held-out calibration split, and calibration quality is reported via Expected Calibration Error and a reliability diagram in the evaluation.

**[18] SHAP explanation.** `TreeExplainer` (exact and fast for RF/XGBoost) computes per-feature attributions for the specific prediction. Attributions are aggregated into **feature groups** so the user sees "urgency language" rather than 11 separate lexicon counters. Both the raw attributions and the grouped summary are persisted — raw for research and auditing, grouped for display.

**[19] Explanation generation.** Maps the top-K grouped attributions to human-readable sentences using a **template library keyed by (feature group, direction, category)**, and — critically — **grounds each sentence in extracted evidence**: not "urgency language detected" but "the message pressures you to act within 2 hours ('offer expires today')". Deliberately template-based, not LLM-generated, for three reasons: it cannot hallucinate evidence that isn't in the SHAP output, it is deterministic and therefore reproducible for the paper, and it adds no latency or external dependency.

**[20] Recommendation engine.** A rule table keyed by (category, risk band, detected entities) producing a prioritised, imperative action list, plus reporting-channel links and a "what not to do" list. Category-specific by design — the correct advice for an OTP scam ("never share the code; your bank will never ask") is different from a QR scam ("check the payee name before approving; receiving money never requires scanning").

**[21] Response assembly + telemetry.** Assembles the response against the versioned contract, attaches per-stage timings, model version, feature-schema version, OCR confidence, and degradation flags, and emits structured telemetry. Every prediction is reproducible from (image hash, model version, feature schema version) — a hard requirement for the research write-up.

### 5.3 Cross-cutting pipeline rules

1. **Every stage declares an explicit output schema**; no stage returns an untyped dictionary.
2. **Every stage can fail independently** and must declare a degraded-mode output plus a flag. The pipeline never dies because logo matching threw.
3. **Every stage is individually timed**; the timings ship in the response.
4. **The text and visual branches run concurrently** (thread pool — both are I/O-and-native-bound, so the GIL is not the constraint).
5. **No stage performs network I/O to third parties in the request path** (privacy + latency + never fetch an attacker-controlled URL).
6. **Feature code is shared verbatim between training and inference** (§3.3).

---

## 6. Folder Structure

### 6.1 Repository layout

A **monorepo** is recommended: the three deliverables share contracts and the dataset schema, and the project is small enough that split repos cost more in synchronisation than they save.

```
ai-powered-scam-detection/
├── docs/
│   ├── BLUEPRINT.md                 ← this document
│   ├── adr/                         ← architecture decision records
│   ├── api/openapi.yaml             ← generated + hand-maintained API spec
│   ├── dataset/
│   │   ├── ANNOTATION_GUIDE.md      ← the single most important dataset artifact
│   │   ├── TAXONOMY.md              ← 7 categories, definitions, edge cases
│   │   └── DATASHEET.md             ← "Datasheets for Datasets" disclosure
│   ├── ethics/CONSENT_AND_PRIVACY.md
│   └── evaluation/                  ← results, ablations, confusion matrices
├── packages/
│   └── contracts/                   ← THE shared contract package
│       ├── schemas/                 ← JSON Schema: analysis, prediction, error, feature-schema
│       ├── taxonomy/                ← scam categories, risk bands, recommendation templates (data, not code)
│       └── generated/               ← JSDoc typedefs (JS) + Pydantic models (Py), both GENERATED
├── apps/
│   ├── web/                         ← SvelteKit app (see 6.2)
│   └── ai-service/                  ← Python FastAPI service (see 6.3)
├── ml/                              ← research/training workspace (see 6.3)
├── infra/
│   ├── firebase/                    ← firestore.rules, storage.rules, firestore.indexes.json
│   ├── docker/                      ← Dockerfiles, compose for local dev
│   └── ci/                          ← pipeline definitions
└── scripts/                         ← codegen, dataset export, smoke tests
```

### 6.2 Frontend + BFF — `apps/web/`

```
apps/web/
├── src/
│   ├── app.html
│   ├── app.css                              ← Tailwind entry + design tokens
│   ├── hooks.server.js                      ← auth, CSP, security headers, request ID, rate limit
│   ├── hooks.client.js                      ← client error reporting
│   ├── lib/
│   │   ├── components/
│   │   │   ├── ui/                          ← shadcn-svelte primitives (button, card, badge, alert, table, dialog, progress, tabs)
│   │   │   ├── upload/                      ← Dropzone, FilePreview, RedactionCanvas, UploadQueue
│   │   │   ├── analysis/                    ← ProgressTracker, VerdictBanner, RiskGauge, CategoryBadge
│   │   │   ├── explanation/                 ← FeatureContributionChart, ReasonList, EvidenceOverlay
│   │   │   ├── entities/                    ← UrlChip, UpiChip, PhoneChip, QrPayloadCard
│   │   │   ├── history/                     ← HistoryTable, HistoryFilters, AnalysisCard
│   │   │   ├── admin/                       ← AnnotationWorkbench, DatasetExplorer, MetricsPanel, ModelRegistryTable
│   │   │   └── layout/                      ← Header, Nav, Footer, Toaster
│   │   ├── stores/                          ← Svelte 5 rune-based state: session, uploadQueue, analysis, toast
│   │   ├── hooks/                           ← reusable client logic: useUpload, useAnalysisStatus, usePaste, useMediaQuery
│   │   ├── server/                          ← SERVER-ONLY. Never importable by client code.
│   │   │   ├── firebase/                    ← admin app, auth, firestore, storage initialisation
│   │   │   ├── repositories/                ← analysisRepo, userRepo, datasetRepo, feedbackRepo, blocklistRepo, modelRepo
│   │   │   ├── services/                    ← analysisService, uploadService, authService, adminService, quotaService
│   │   │   ├── clients/aiServiceClient.js   ← retry, timeout, circuit breaker, auth
│   │   │   ├── middleware/                  ← requireAuth, requireAdmin, rateLimit, validateBody, csrf
│   │   │   └── mappers/                     ← AI service response → API response shape
│   │   ├── client/firebase.js               ← client SDK: auth only, public config
│   │   ├── schemas/                         ← re-export of packages/contracts validators
│   │   ├── constants/                       ← categories, risk bands, error codes, limits
│   │   ├── utils/                           ← formatting, image resize, file validation, a11y helpers
│   │   └── config/env.js                    ← validated env access, fails fast on missing vars
│   └── routes/
│       ├── +layout.svelte / +layout.server.js
│       ├── +page.svelte                      ← landing
│       ├── (auth)/login, /register, /reset
│       ├── (app)/
│       │   ├── analyze/+page.svelte           ← upload flow
│       │   ├── analysis/[id]/+page.svelte     ← result dashboard
│       │   ├── history/+page.svelte
│       │   ├── learn/+page.svelte             ← education layer
│       │   └── settings/+page.svelte          ← data controls, consent
│       ├── (admin)/admin/
│       │   ├── annotate/[id], dataset, models, metrics, blocklists, users
│       └── api/
│           ├── auth/session/+server.js
│           ├── uploads/+server.js
│           ├── analyses/+server.js
│           ├── analyses/[id]/+server.js
│           ├── analyses/[id]/feedback/+server.js
│           ├── me/+server.js
│           └── admin/**/+server.js
├── static/
└── tests/  (unit | integration | e2e)
```

**Hard rule:** anything under `lib/server/` is server-only. SvelteKit enforces this at build time — a client import of a `$lib/server/*` module fails the build. This is the primary mechanism preventing credential leakage into the browser bundle.

### 6.3 Python AI service — `apps/ai-service/` and `ml/`

The split between the two is deliberate: `apps/ai-service` is **production inference only** (small, fast, containerised); `ml/` is the **research workspace** (notebooks, training, experiments) which must never be a runtime dependency of the service.

```
apps/ai-service/
├── app/
│   ├── main.py                     ← FastAPI app factory, lifespan (model loading)
│   ├── api/v1/                     ← routers: predict, health, model_info, explain, ocr_debug
│   ├── core/                       ← config, logging, security, exceptions, timing
│   ├── schemas/                    ← Pydantic request/response models (generated from contracts)
│   ├── pipeline/
│   │   ├── orchestrator.py         ← stage sequencing, concurrency, degradation policy
│   │   └── stages/                 ← one module per pipeline stage [1]–[21]
│   │       ├── ingestion.py, validation.py, preprocessing.py
│   │       ├── platform_id.py, chat_parser.py
│   │       ├── ocr/                ← engine interface + tesseract/easyocr/paddle adapters
│   │       ├── text/               ← cleaning, linguistic, ner, url_risk, embeddings
│   │       ├── vision/             ← qr, logo, layout
│   │       ├── fusion.py
│   │       ├── inference.py, calibration.py
│   │       └── explain/            ← shap_explainer, nlg, recommendations
│   ├── features/                   ← ⚠ SHARED WITH TRAINING. Feature definitions, schema, registry.
│   ├── models/                     ← loader, registry, version resolution (NOT weights)
│   ├── resources/                  ← lexicons, brand templates, platform profiles, regex packs
│   └── services/                   ← storage_client, blocklist_cache
├── artifacts/                      ← downloaded/mounted model bundles (gitignored)
├── tests/                          ← unit per stage, golden-image regression, contract tests
├── Dockerfile
└── pyproject.toml

ml/
├── data/                           ← raw | interim | processed | splits  (gitignored; DVC-tracked)
├── notebooks/                      ← EDA, error analysis (exploration only, never imported)
├── src/
│   ├── data/                       ← ingest, split (stratified + group-aware), augment
│   ├── features/                   ← thin wrapper importing apps/ai-service/app/features
│   ├── training/                   ← train_stage1, train_stage2, tune, calibrate
│   ├── evaluation/                 ← metrics, confusion, ablation, calibration curves, error analysis
│   └── export/                     ← bundle builder (models + schema + calibrators + metadata + card)
├── configs/                        ← experiment configs (YAML, one per run, versioned)
├── experiments/                    ← MLflow/W&B run metadata
└── reports/                        ← generated figures and tables for the paper
```

### 6.4 Shared contracts — `packages/contracts/`

The single most valuable structural decision in this layout. **JSON Schema is the source of truth.** From it, generate:
- JSDoc typedefs for the SvelteKit app (A9) — giving editor autocomplete without a TypeScript migration;
- Pydantic models for the Python service;
- runtime validators used at both trust boundaries.

Also versioned here as **data, not code**: the seven-category taxonomy with definitions, the risk bands, the recommendation template library, and the feature-schema manifest. Because these are data files, adding a scam category (§3.8) touches one file plus a retrain — not fifteen source files across two languages.

**CI gate:** if a schema changes and the generated artifacts are not regenerated, the build fails.

---

## 7. Database Design (Firestore)

### 7.1 Modelling principles

1. **Server-write-only for anything the user must not forge.** Verdicts, dataset labels, and model records are written exclusively by the Admin SDK. Security rules deny all client writes to those collections.
2. **Denormalise for the read path.** The history screen reads one document per row; it never fans out. Display fields are copied onto the list document at write time.
3. **Separate hot from cold.** A full analysis document with SHAP values, all OCR tokens, and the complete feature vector can reach hundreds of kilobytes. That payload lives in a subcollection so listing history doesn't transfer it.
4. **Separate PII from research data.** A `datasetSamples` document must be usable for training and publication without carrying the uploader's identity. Linkage is one-way and stored separately.
5. **Every document carries `schemaVersion`.** Migration without it is guesswork.

### 7.2 Collections

---

#### `users/{uid}`

**Purpose:** profile, preferences, consent state, and usage counters for an authenticated user.

| Field | Type | Notes |
|-------|------|-------|
| `uid` | string | Matches Firebase Auth UID and the document ID |
| `email` | string | |
| `displayName` | string \| null | |
| `photoUrl` | string \| null | |
| `role` | string | `user` \| `annotator` \| `admin`. Mirrors the Auth custom claim; the **claim** is authoritative for authorisation, this field is for display only |
| `locale` | string | e.g. `en-IN` |
| `createdAt` / `lastActiveAt` | timestamp | |
| `consent.researchUse` | boolean | Explicit opt-in for dataset inclusion (A6). Defaults **false** |
| `consent.researchUseUpdatedAt` | timestamp | Consent must be timestamped to be defensible |
| `consent.termsVersion` | string | Which terms version was accepted |
| `usage.analysesTotal` | number | Lifetime counter |
| `usage.analysesToday` / `usage.dayKey` | number / string | Quota window (`YYYY-MM-DD`); reset by comparing `dayKey` |
| `status` | string | `active` \| `suspended` |
| `schemaVersion` | number | |

**Relationships:** 1→N `analyses` (via `analyses.userId`); 1→N `feedback`.
**Indexes:** single-field on `role`, `status` (admin listing). Composite `status ASC, lastActiveAt DESC`.
**Security:** client may read only its own document; client may write only `displayName`, `locale`, and `consent.*`. `role`, `usage.*`, and `status` are server-only — a client-writable `role` field is a privilege-escalation vulnerability.

---

#### `analyses/{analysisId}`

**Purpose:** one screenshot analysis — the central entity. Holds the summary needed for lists and the verdict view.

| Field | Type | Notes |
|-------|------|-------|
| `analysisId` | string | Document ID |
| `userId` | string \| null | Null for anonymous analyses |
| `anonymousSessionId` | string \| null | For guest quota tracking |
| `status` | string | `pending` \| `uploading` \| `processing` \| `completed` \| `failed` \| `cancelled` |
| `stage` | string \| null | Current pipeline stage, drives FE-04 progress |
| `image.storagePath` | string | Storage object path |
| `image.thumbnailPath` | string \| null | |
| `image.contentHash` | string | SHA-256; idempotency + duplicate detection |
| `image.width` / `height` / `sizeBytes` / `mimeType` | number / string | |
| `platform.declared` | string \| null | What the user selected |
| `platform.detected` | string | What AI-03 predicted |
| `platform.confidence` | number | |
| `result.label` | string | `genuine` \| `fraudulent` \| `insufficient_evidence` |
| `result.category` | string \| null | One of the 7; null when genuine |
| `result.categoryConfidence` | number \| null | Calibrated |
| `result.labelConfidence` | number | Calibrated |
| `result.riskScore` | number | 0–100 |
| `result.riskBand` | string | `safe` \| `low` \| `medium` \| `high` \| `critical` |
| `result.topReasons` | array\<object\> | ≤ 5 `{ code, text, contribution, evidence }` — denormalised for the list/summary view |
| `result.degraded` | array\<string\> | Branches that failed, e.g. `["logo","qr"]` |
| `ocr.textPreview` | string | First ~300 chars, for search/preview |
| `ocr.confidence` | number | Aggregate |
| `ocr.language` | string | Detected |
| `entities.urlCount` / `hasQr` / `hasUpi` / `hasPhone` / `hasAmount` | number / boolean | Denormalised flags for filtering |
| `model.version` | string | e.g. `v1.3.0` |
| `model.featureSchemaVersion` | string | Reproducibility (§5.2 [21]) |
| `timings.totalMs` and per-stage | object | Performance monitoring |
| `error.code` / `error.message` | string \| null | Populated when `status = failed` |
| `feedback.given` / `feedback.agreed` | boolean \| null | Denormalised from `feedback` |
| `retention.deleteAfter` | timestamp | Drives scheduled purge |
| `createdAt` / `completedAt` | timestamp | |
| `schemaVersion` | number | |

**Subcollection `analyses/{id}/details/{detailId}`** — the cold, heavy payload, fetched only when the detail view is opened:
`ocrTokens[]` (text, confidence, bbox, turnIndex), `chatTurns[]` (direction, text, bbox), `featureVector` (named map), `shapValues` (raw + grouped), `qrPayloads[]`, `brandMatches[]`, `layoutSignals`, `rawServiceResponse`.

**Relationships:** N→1 `users`; 1→1 `datasetSamples` (optional, only with consent); 1→N `feedback`.
**Indexes (composite, required):**
- `userId ASC, createdAt DESC` — history list
- `userId ASC, result.category ASC, createdAt DESC` — filtered history
- `userId ASC, result.riskBand ASC, createdAt DESC`
- `status ASC, createdAt ASC` — stuck-job sweeper
- `retention.deleteAfter ASC` — purge job
- `result.label ASC, result.categoryConfidence ASC, createdAt DESC` — low-confidence review queue (AD-05)

**Security:** client reads only where `userId == request.auth.uid`; **no client writes at all**. The `details` subcollection inherits the same read rule. Admins read all.

---

#### `datasetSamples/{sampleId}`

**Purpose:** the research corpus — the project's primary contribution (§1.4). Deliberately **decoupled from `analyses`** so it can be exported, versioned, and published without user identity.

| Field | Type | Notes |
|-------|------|-------|
| `sampleId` | string | |
| `source` | string | `user_upload` \| `collected` \| `synthetic` \| `public_dataset` |
| `sourceAnalysisId` | string \| null | Present only when consented; the **only** link back |
| `platform` | string | whatsapp \| telegram \| sms \| instagram \| email |
| `scamCategory` | string \| null | job \| otp \| banking \| qr \| investment \| lottery \| delivery; null when genuine |
| `label` | string | `genuine` \| `fraudulent` |
| `ocrText` | string | Machine-extracted |
| `ocrTextCorrected` | string \| null | Human-corrected ground truth — enables OCR-accuracy evaluation as a separate result |
| `imageUrl` | string | Storage path under a dataset-only prefix |
| `redactedImageUrl` | string \| null | Published version with PII masked |
| `annotatedBy` | string | Annotator ID |
| `annotationStatus` | string | `pending` \| `annotated` \| `double_annotated` \| `disputed` \| `adjudicated` \| `rejected` |
| `annotations[]` | array\<object\> | Each: `{annotatorId, label, category, platform, confidence, notes, at}` — keeping all annotations enables κ computation (AD-02) |
| `agreement.kappa` / `agreement.resolved` | number / boolean | |
| `groupKey` | string | **Critical.** Template ID, conversation ID, or campaign ID. Splits are grouped by this to prevent leakage (§18.3) |
| `split` | string \| null | `train` \| `val` \| `calibration` \| `test` — assigned once, immutable |
| `datasetVersion` | string | e.g. `v1.0` |
| `pii.redacted` | boolean | Must be `true` before publication |
| `pii.reviewedBy` | string \| null | |
| `qualityFlags[]` | array\<string\> | `blurry`, `partial`, `low_ocr_confidence`, `duplicate_suspect` |
| `contentHash` | string | Deduplication |
| `createdAt` / `updatedAt` | timestamp | |
| `schemaVersion` | number | |

**Indexes:** `annotationStatus ASC, createdAt ASC` (work queue); `split ASC, label ASC, scamCategory ASC` (export); `platform ASC, scamCategory ASC, label ASC` (balance monitoring); `contentHash ASC` (dedup); `datasetVersion ASC, split ASC`.
**Security:** annotators read + write only `annotations[]` and `qualityFlags`; only admins set `split`, `datasetVersion`, and `pii.reviewedBy`. No general-user access at all.

---

#### `feedback/{feedbackId}`

**Purpose:** user corrections feeding active learning (AI-21) and honest error analysis.

Fields: `feedbackId`, `analysisId`, `userId`, `agreed` (boolean), `correctedLabel`, `correctedCategory`, `comment` (free text, length-capped and sanitised), `predictedLabel`/`predictedCategory`/`predictedConfidence` (**snapshotted** — the model will change, and the feedback must remain interpretable against the model that produced it), `modelVersion`, `status` (`new` | `triaged` | `promoted_to_dataset` | `dismissed`), `createdAt`, `schemaVersion`.

**Indexes:** `status ASC, createdAt ASC`; `agreed ASC, predictedCategory ASC, createdAt DESC`; `analysisId ASC`.
**Security:** client may create feedback only for an analysis it owns, once per analysis (enforced server-side); client cannot read others' feedback; admins read all.

---

#### `modelVersions/{version}`

**Purpose:** model registry and audit trail (AD-04); makes every historical prediction explainable after the fact.

Fields: `version`, `stage1Algorithm` / `stage2Algorithm`, `featureSchemaVersion`, `datasetVersion`, `trainedAt`, `trainedBy`, `hyperparameters` (map), `metrics` (`{overall:{accuracy,macroF1,...}, perCategory:{...}, calibration:{ece,brier}}`), `artifactPath`, `artifactHash`, `status` (`training` | `staged` | `active` | `deprecated` | `rolled_back`), `activatedAt`, `notes`, `modelCardPath`, `schemaVersion`.

**Constraint:** exactly one document may have `status = active` — enforced in a transaction during promotion.
**Indexes:** `status ASC, trainedAt DESC`.
**Security:** read for admins; write server-only via the promotion service.

---

#### `blocklists/{entryId}`

**Purpose:** known-malicious indicators (AD-07) used by AI-09/AI-11 as a high-precision feature.

Fields: `entryId`, `type` (`domain` | `url` | `upi` | `phone` | `keyword`), `value` (normalised, lowercase), `valueHash` (indexed lookup key), `severity` (`low`|`medium`|`high`), `source`, `addedBy`, `addedAt`, `expiresAt`, `active`, `hitCount`, `schemaVersion`.

**Indexes:** `type ASC, valueHash ASC` (lookup); `active ASC, expiresAt ASC` (expiry sweep).
**Security:** admin-write only; the AI service reads via a **cached snapshot** refreshed on an interval — never a per-request query, which would add a round-trip to the latency budget (§3.1).

---

#### `auditLogs/{logId}`

**Purpose:** security and compliance trail.

Fields: `logId`, `actorId`, `actorRole`, `action` (e.g. `analysis.create`, `admin.model.promote`, `user.data.delete`, `auth.login.failed`), `targetType`, `targetId`, `ipHash` (**hashed, not raw** — the log itself must not become a PII store), `userAgent`, `outcome`, `metadata`, `requestId`, `createdAt`.

**Indexes:** `actorId ASC, createdAt DESC`; `action ASC, createdAt DESC`.
**Security:** no client access whatsoever; append-only from the server; retention 12 months.

---

#### `quotas/{quotaKey}`

**Purpose:** rate limiting and abuse control (BE-06). `quotaKey` is `user:{uid}:{YYYY-MM-DD}` or `ip:{ipHash}:{YYYY-MM-DD-HH}`.
Fields: `count`, `limit`, `windowStart`, `blocked`, `expiresAt`. Incremented via `FieldValue.increment` in a transaction. TTL policy set on `expiresAt` so entries self-clean.
**Security:** server-only.

---

#### `systemConfig/{configKey}`

**Purpose:** runtime-tunable settings without redeploy — decision thresholds, feature flags, maintenance mode, quota defaults, active model pin. Read by the server on a short cache; admin-writable; every change audit-logged.

### 7.3 Storage design (Firebase Storage)

```
/uploads/{uid}/{analysisId}/original.{ext}      ← as uploaded (EXIF-stripped server-side)
/uploads/{uid}/{analysisId}/processed.png       ← preprocessed, optional, short TTL
/uploads/{uid}/{analysisId}/thumb.webp          ← 320 px, for history lists
/anon/{sessionId}/{analysisId}/original.{ext}   ← guest uploads, 24 h lifecycle
/dataset/{datasetVersion}/{sampleId}/image.png  ← research corpus (admin-only)
/dataset/{datasetVersion}/{sampleId}/redacted.png
/artifacts/models/{version}/bundle.tar.gz       ← model bundles (no public access)
/exports/{userId}/{exportId}.json               ← user data exports, signed URL, 7-day TTL
```

**Rules:**
- Client uploads only to its own `/uploads/{uid}/...` prefix, enforced by a Storage rule matching `request.auth.uid`, with size (≤ 10 MB) and content-type (`image/*`) constraints declared **in the rule**, not only in application code.
- The AI service's service account has **read-only** access scoped to `/uploads/` and `/anon/`.
- No path is publicly readable. All client reads go through short-lived signed URLs issued by the BFF.
- Lifecycle rules: `/anon/` → delete after 24 h; `/uploads/` → delete per the user's retention setting (default 90 days); `/exports/` → 7 days; `/dataset/` → no expiry.

---

## 8. API Design

### 8.1 Conventions

- Base path `/api`, versioned via the `Accept-Version` header (v1 default).
- All requests/responses JSON, except the direct-to-Storage upload.
- **Authentication:** HTTP-only session cookie (`__session`). State-changing requests additionally require a CSRF token (double-submit).
- **Validation:** every inbound payload is validated against the shared JSON Schema at the route boundary. Reject on first failure with field-level detail.
- **Errors:** one shape, always:
  ```
  { "error": { "code": "UPPER_SNAKE_CODE", "message": "human readable",
               "details": { "field": "reason" }, "requestId": "req_..." } }
  ```
- **Error codes:** `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_FAILED`, `RATE_LIMITED`, `QUOTA_EXCEEDED`, `FILE_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `IMAGE_INVALID`, `NOT_A_SCREENSHOT`, `OCR_INSUFFICIENT_TEXT`, `AI_SERVICE_UNAVAILABLE`, `AI_SERVICE_TIMEOUT`, `ANALYSIS_FAILED`, `CONFLICT`, `INTERNAL_ERROR`.
- **Idempotency:** `Idempotency-Key` header honoured on all POSTs.
- Every response carries `X-Request-Id`; every error is logged with it.

### 8.2 Public / authenticated endpoints (SvelteKit BFF)

---

**`POST /api/auth/session`** — exchange a Firebase ID token for a session cookie.
Request: `{ idToken: string }`. Validation: token present, verified via Admin SDK, `email_verified` checked for password accounts.
Response `200`: `{ user: { uid, email, displayName, role, consent } }` + `Set-Cookie: __session=...; HttpOnly; Secure; SameSite=Lax; Max-Age=1209600`.
Errors: `401 UNAUTHENTICATED` (invalid/expired token), `403 FORBIDDEN` (suspended account).
Auth: none (this is the login step). Rate limit: 10/min per IP.

**`DELETE /api/auth/session`** — sign out; revokes refresh tokens and clears the cookie. `204`.

**`GET /api/me`** — current user profile + quota. Response: `{ user, quota: { used, limit, resetsAt } }`. `401` if unauthenticated.

**`PATCH /api/me`** — update `displayName`, `locale`, `consent.researchUse`, `retentionDays`. Consent changes are audit-logged. `200` with the updated user.

---

**`POST /api/uploads`** — request an upload target. Does **not** carry the file.
Request: `{ fileName, mimeType, sizeBytes, width, height, contentHash }`.
Validation: mimeType ∈ {png,jpeg,webp,heic}; sizeBytes ≤ 10 MB; dimensions ≥ 300×300 and ≤ 8000×8000; quota not exceeded.
Response `201`: `{ uploadId, storagePath, uploadUrl, expiresAt, headers }` — a signed resumable-upload URL scoped to that exact path.
Errors: `413 FILE_TOO_LARGE`, `415 UNSUPPORTED_MEDIA_TYPE`, `429 QUOTA_EXCEEDED`.
Rationale: the file goes browser → Storage directly. The BFF never handles image bytes on the hot path (§4.2).

---

**`POST /api/analyses`** — create an analysis job.
Request: `{ uploadId, storagePath, declaredPlatform?, consentResearchUse?, redactionApplied? }`.
Validation: the storage object exists, is owned by the caller, matches the registered `contentHash`, and passes server-side magic-byte checking; quota check; idempotency by `(userId, contentHash)` within 60 s.
Response `202 Accepted`: `{ analysisId, status: "processing", stage: "preprocessing", pollUrl, estimatedMs }`.
Errors: `404 NOT_FOUND` (missing object), `409 CONFLICT` (duplicate in-flight → returns the existing `analysisId`), `422 IMAGE_INVALID`, `429`, `503 AI_SERVICE_UNAVAILABLE`.
Auth: session or valid anonymous session. Rate limit: 20/hr authenticated, 3/hr anonymous.
**Note (A8):** `202` + poll is the contract even if v1 completes synchronously internally. This is what makes the later move to a queue a zero-client-change migration (§3.2).

**`GET /api/analyses/{id}`** — fetch status or result.
Response `200`, `status = processing`: `{ analysisId, status, stage, progress, startedAt }`.
Response `200`, `status = completed`: the full result — `result` (label, category, confidences, riskScore, riskBand, topReasons[]), `ocr` (textPreview, confidence, language), `entities` (urls[], upiIds[], phones[], amounts[], qrPayloads[]), `platform`, `image` (signed thumbnail URL), `model` (version, featureSchemaVersion), `degraded[]`, `timings`.
Query param `?include=details` additionally returns the `details` subcollection payload (SHAP values, OCR tokens, chat turns, feature vector) — omitted by default because it is large.
Errors: `403 FORBIDDEN` (not the owner), `404`.
Supports `If-None-Match` / ETag; completed analyses are immutable and cacheable.

**`GET /api/analyses`** — paginated history.
Query: `limit` (≤ 50, default 20), `cursor`, `category`, `riskBand`, `label`, `from`, `to`.
Response: `{ items: [...summary...], nextCursor, total? }`. Cursor-based, not offset — Firestore has no efficient offset.

**`DELETE /api/analyses/{id}`** — delete the record, the details subcollection, and all Storage objects. If a consented dataset sample was derived, deletion also removes it unless it has already been published in a frozen dataset version — in which case the response states this explicitly rather than silently retaining it (A6). `204`.

**`POST /api/analyses/{id}/cancel`** — best-effort cancellation of an in-flight job. `200`.

**`POST /api/analyses/{id}/feedback`** — submit a correction.
Request: `{ agreed: boolean, correctedLabel?, correctedCategory?, comment? (≤ 1000 chars) }`.
Validation: caller owns the analysis; analysis is `completed`; no existing feedback (else `409`); if `agreed=false` then a corrected label is required; comment sanitised.
Response `201`: `{ feedbackId, thanksMessage }`.

**`GET /api/taxonomy`** — the seven categories with display names, descriptions, icons, and risk-band definitions. Public, heavily cached. Serves §3.8 extension point 2: the frontend never hard-codes the taxonomy.

**`POST /api/exports`** / **`GET /api/exports/{id}`** — request and retrieve a JSON export of the user's data (FE-10). Async; returns a signed URL on completion.

**`DELETE /api/me`** — account deletion. Cascades: Auth user, `users` doc, all `analyses` + details, all Storage objects, all `feedback`. Consented dataset samples are anonymised (`sourceAnalysisId` nulled) rather than deleted if already in a frozen version — again, stated explicitly in the response. Requires re-authentication within 5 minutes. `202`.

### 8.3 Admin endpoints (`requireAdmin`, all audit-logged)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/admin/metrics` | Volume, latency percentiles, per-category performance, OCR confidence distribution, degradation rate |
| `GET` | `/api/admin/samples` | Annotation queue; filter by `annotationStatus`, platform, category |
| `GET` | `/api/admin/samples/{id}` | Sample + image signed URL + OCR output for the workbench |
| `POST` | `/api/admin/samples/{id}/annotate` | Submit an annotation `{label, category, platform, correctedOcrText?, qualityFlags[], notes}` |
| `POST` | `/api/admin/samples/{id}/adjudicate` | Resolve a disputed sample (senior annotator only) |
| `POST` | `/api/admin/samples/import` | Bulk import collected/synthetic screenshots with a manifest |
| `POST` | `/api/admin/dataset/split` | Assign group-aware stratified splits; **immutable once set** |
| `POST` | `/api/admin/dataset/export` | Produce a versioned export + manifest + datasheet |
| `GET` | `/api/admin/dataset/stats` | Platform × category × label balance matrix |
| `GET` | `/api/admin/models` | Registry listing |
| `POST` | `/api/admin/models/{version}/promote` | Transactional activation (exactly one active) |
| `POST` | `/api/admin/models/{version}/rollback` | Revert to the previous active version |
| `GET` | `/api/admin/feedback` | Triage queue |
| `POST` | `/api/admin/feedback/{id}/promote` | Promote a disputed prediction into `datasetSamples` |
| `GET/POST/DELETE` | `/api/admin/blocklists` | Indicator CRUD |
| `GET/PATCH` | `/api/admin/users/{uid}` | Inspect / suspend |
| `GET/PATCH` | `/api/admin/config` | Runtime configuration (`systemConfig`) |

### 8.4 Internal AI service API (FastAPI — not publicly routable)

**`POST /v1/predict`**
Request: `{ requestId, imageRef: { bucket, path } | imageBase64, declaredPlatform?, locale?, options: { includeShap: bool, includeOcrTokens: bool, ocrEngine?: string, modelVersion?: string } }`.
Response `200`: `{ requestId, modelVersion, featureSchemaVersion, platform{detected,confidence}, ocr{text, confidence, language, tokens?[], turns[]}, entities{...}, visual{qrPayloads[], brandMatches[], layoutSignals{}}, prediction{ label, labelProbability, category, categoryProbability, riskScore, riskBand }, explanation{ groupedContributions[], topFeatures[], reasons[], evidence[] }, recommendations[], degraded[], timings{} }`.
Errors: `400 IMAGE_INVALID`, `422 NOT_A_SCREENSHOT`, `422 OCR_INSUFFICIENT_TEXT`, `503 MODEL_NOT_LOADED`, `500`.
Auth: OIDC identity token audience-scoped to the service (preferred) or an HMAC-signed request with a rotating shared secret. **Never** open.

**`POST /v1/predict/batch`** — offline evaluation and bulk dataset scoring. Admin/service use only; not exposed via the BFF.
**`POST /v1/explain`** — recompute SHAP for a stored feature vector without re-running the pipeline. Used by the research workflow.
**`POST /v1/ocr`** — OCR only. Debug and annotation pre-fill.
**`GET /v1/model/info`** — active version, feature schema version, dataset version, loaded engines, warm status.
**`GET /v1/health`** (liveness, no model check) / **`GET /v1/ready`** (readiness, asserts models loaded).
**`GET /metrics`** — Prometheus exposition.

### 8.5 Sequence — happy path

```
Browser                 BFF                  Storage         AI Service        Firestore
   │  POST /api/uploads  │                      │                 │                │
   │────────────────────►│ validate + quota     │                 │                │
   │                     │─── signed URL ──────►│                 │                │
   │◄── uploadUrl ───────│                      │                 │                │
   │  PUT bytes ─────────────────────────────► │                 │                │
   │  POST /api/analyses │                      │                 │                │
   │────────────────────►│ verify object, hash, magic bytes       │                │
   │                     │─────────────────── create doc ────────────────────────►│
   │◄── 202 {id} ────────│                      │                 │                │
   │                     │  POST /v1/predict ──────────────────► │                │
   │  GET /api/analyses/{id} (poll / snapshot listener)          │  read image ───►│
   │────────────────────►│                      │◄────────────────│                │
   │◄── processing ──────│                      │                 │ pipeline runs  │
   │                     │◄──── prediction JSON ─────────────────│                │
   │                     │──────────── write result + details ───────────────────►│
   │  GET /api/analyses/{id}                    │                 │                │
   │────────────────────►│◄─────────────────────────────────────── read ──────────│
   │◄── completed result │                      │                 │                │
```

---

## 9. AI Modules

Each module is independently testable, has a fixed contract, and declares a degraded-mode output.

---

### AI-01 · Image Validation & Integrity
**Purpose:** reject inputs the pipeline cannot honestly process. **Input:** raw bytes + declared MIME. **Output:** `{valid, decodedImage, meta{w,h,format,hasAlpha}, rejectionCode?}`.
**Dependencies:** none (first stage). **Libraries:** Pillow, python-magic, OpenCV, `imagehash`.
**Strategy:** magic-byte verification; decoded-pixel cap (guards decompression bombs); min/max dimension checks; EXIF strip; perceptual hash for duplicate detection; a cheap "is this a chat screenshot?" gate combining text-region density (MSER/EAST), rectilinear-structure ratio, and colour-palette flatness. The gate is tuned for **high recall on real screenshots** — wrongly rejecting a valid screenshot is a much worse user experience than accepting an odd one.

### AI-02 · Preprocessing
**Purpose:** maximise OCR accuracy while preserving colour information for the visual branch. **Input:** decoded image + platform hint. **Output:** `{textImage, visualImage, ops[], deskewAngle}`.
**Libraries:** OpenCV, scikit-image, Pillow.
**Strategy:** the **forked** pipeline of §5.2[3]. Per-platform parameter profiles stored in `resources/platform_profiles/`. Each op is measured against OCR confidence during tuning and disabled where it hurts. Deskew is skipped when the estimated angle is < 0.5° (screenshots are usually already axis-aligned; needless rotation introduces resampling blur).

### AI-03 · Platform Identification
**Purpose:** identify the source app. **Input:** `visualImage`. **Output:** `{platform, confidence, scores{}}`.
**Dependencies:** AI-02. **Libraries:** OpenCV, scikit-learn (or a small PyTorch CNN).
**Strategy:** start with a **rules + colour-signature baseline** (WhatsApp's green/cream bubble palette, Telegram's blue, iMessage grey/blue, Instagram gradient header, email client chrome) plus header-region template matching. Escalate to a small CNN only if the baseline drops below ~90 % — a CNN here adds container size, cold-start time, and an extra model to version, for a task that is largely solvable with colour statistics. Declared platform is used as a prior, never as truth.

### AI-04 · Chat Structure Parsing
**Purpose:** recover message turns and their direction. **Input:** `visualImage` + platform profile. **Output:** `{turns[{index, direction, bbox, bgColor}], parsed: bool}`.
**Dependencies:** AI-02, AI-03. **Libraries:** OpenCV (contours, morphology, connected components), NumPy.
**Strategy:** colour-mask the known bubble colours for the identified platform, morphologically close, extract contours, filter by area/aspect ratio, sort top-to-bottom, and assign direction by horizontal centroid relative to the image midline cross-checked against bubble colour. Degrades to a single-turn whole-image treatment with `parsed=false`. **This is a differentiating module (§1.4 #4) and should be evaluated separately** — report bubble-segmentation precision/recall in the paper.

### AI-05 · OCR
**Purpose:** extract text with confidence and position. **Input:** `textImage` + turn bboxes. **Output:** `{fullText, turns[{index,text,confidence}], tokens[{text,conf,bbox}], engine, language, aggregateConfidence}`.
**Dependencies:** AI-02, AI-04. **Libraries:** pytesseract + Tesseract 5, EasyOCR, PaddleOCR (behind one provider interface).
**Strategy:** §10 in full. Region-wise OCR over bubbles; dual-engine escalation on low confidence; per-token confidence retained because it feeds both a feature and the UI's low-confidence highlighting.

### AI-06 · Text Cleaning & Normalisation
**Purpose:** produce analysable text without discarding signal. **Input:** raw OCR text. **Output:** `{cleanText, emojis[], obfuscationSignals{}, corrections[]}`.
**Libraries:** `regex`, `unicodedata`, `emoji`, `ftfy`, `symspellpy`, `confusable_homoglyphs`.
**Strategy:** §5.2[7]. The key discipline: **normalisation is lossy, so every removal becomes a feature**. Emoji removed → emoji-density feature. Zero-width characters stripped → obfuscation flag. Homoglyphs folded → homoglyph-count feature. Nothing is discarded without leaving a trace.

### AI-07 · Linguistic Feature Extraction
**Purpose:** interpretable text features that carry the explanations. **Input:** `cleanText`, `turns`. **Output:** named feature map (~60–90 features).
**Dependencies:** AI-06. **Libraries:** spaCy, NLTK, scikit-learn (TF-IDF), curated lexicons.
**Strategy:** §11.5. Direction-aware where meaningful (`incoming_requests_otp` vs `outgoing_contains_otp`). Lexicons live in `resources/lexicons/` as versioned data files with provenance notes, not as literals in source.

### AI-08 · NER & Entity Extraction
**Purpose:** pull out actionable entities. **Input:** `cleanText`, `tokens`. **Output:** `{urls[], domains[], upiIds[], phones[], amounts[], emails[], orgs[], accountNumbers[], otpTokens[]}` each with position and confidence.
**Libraries:** spaCy (`en_core_web_sm` at v1 for latency), `urlextract`, `phonenumbers`, custom validators.
**Strategy:** regex/validator-first for structured entities (deterministic, auditable, high precision); statistical NER only for ORG/PERSON. UPI VPAs validated against handle patterns; phone numbers validated and region-normalised via `phonenumbers`. **Entities are user-visible evidence**, so precision matters more than recall — a wrong "we found a UPI ID" destroys trust.

### AI-09 · URL & Entity Risk Scoring
**Purpose:** score extracted indicators. **Input:** entities + cached blocklists. **Output:** per-URL risk features + aggregate.
**Dependencies:** AI-08, blocklist cache. **Libraries:** `tldextract`, `confusable_homoglyphs`, `idna`.
**Strategy:** §11.7. Offline and lexical only in the request path. Blocklist lookups hit an in-memory snapshot refreshed on a timer.

### AI-10 · Semantic Embeddings
**Purpose:** capture meaning beyond lexicons. **Input:** incoming-turn text. **Output:** reduced dense vector (48–64 dims) + `semantic_scam_similarity` scalars per category.
**Libraries:** `sentence-transformers` (`all-MiniLM-L6-v2`), scikit-learn (TruncatedSVD).
**Strategy:** encode once at startup-loaded model; fit SVD on training data and ship the transformer in the model bundle. Additionally compute **cosine similarity to each category's training centroid** — seven scalars that are both predictive *and* human-explainable ("this message closely resembles known lottery scams"), unlike the raw dimensions. These seven are the features surfaced in explanations; the SVD dims contribute to accuracy silently.

### AI-11 · QR Detection & Decode
**Purpose:** find and interpret embedded codes. **Input:** `visualImage`. **Output:** `{qrCount, payloads[{type, raw, parsed{vpa,amount,name}, bbox, risk}]}`.
**Libraries:** pyzbar (+ ZBar), OpenCV `QRCodeDetector`, `wechat_qrcode` as a fallback for damaged codes.
**Strategy:** §12.2. Multi-detector with preprocessing retries. Decoded URLs are fed back through AI-09 — **never fetched**.

### AI-12 · Brand Impersonation Detection
**Purpose:** detect claimed-vs-evidenced identity mismatch. **Input:** `visualImage`, extracted orgs, domains. **Output:** `{brandMatches[{brand, score, bbox}], impersonationSignals{claimedBrand, logoPresent, domainMatchesBrand, mismatch: bool}}`.
**Libraries:** OpenCV (ORB/template matching), a small CNN embedding (MobileNetV3/CLIP-style) over a curated brand-template set.
**Strategy:** §12.3. Closed set (A7). The output feature that matters is **`mismatch`**, not `logoPresent`.

### AI-13 · Layout & Visual Artifact Analysis
**Purpose:** platform UI cues that carry strong priors. **Input:** `visualImage`, platform. **Output:** boolean/scalar layout feature map.
**Libraries:** OpenCV, targeted OCR over header/banner regions.
**Strategy:** §12.4. Region-of-interest OCR on the header and above-bubble strip is far more reliable than trying to detect these visually.

### AI-14 · Feature Fusion
**Purpose:** produce the single, ordered, schema-versioned feature vector. **Input:** all branch outputs. **Output:** `{vector, names[], groups{}, schemaVersion, missingMask}`.
**Dependencies:** AI-07…AI-13. **Libraries:** NumPy, pandas.
**Strategy:** §5.2[14]. Contract-tested: a unit test asserts that the emitted feature order matches the schema exactly, and CI fails on drift. **This test is non-negotiable** — a silent reordering produces a model that is wrong in a way no metric will reveal.

### AI-15 / AI-16 · Stage-1 and Stage-2 Classifiers
**Purpose:** binary verdict, then category. **Input:** fused vector. **Output:** probabilities.
**Libraries:** scikit-learn (`RandomForestClassifier`), `xgboost`.
**Strategy:** §13. Both algorithms trained and compared per the abstract's objective; the better-performing one is promoted per stage, and the comparison itself is a reportable result.

### AI-17 · Probability Calibration
**Purpose:** make displayed confidence truthful. **Input:** raw scores + calibration split. **Output:** calibrated probabilities.
**Libraries:** scikit-learn (`CalibratedClassifierCV`, isotonic).
**Strategy:** §5.2[17]; report ECE, Brier score, and a reliability diagram.

### AI-18 · SHAP Explainer
**Purpose:** per-prediction attribution. **Input:** fused vector + model. **Output:** `{raw[], grouped[], baseValue}`.
**Libraries:** `shap` (`TreeExplainer`).
**Strategy:** §14. Explainer object is built once at startup, not per request (construction is the expensive part).

### AI-19 · Explanation Generation
**Purpose:** attribution → grounded sentences. **Input:** grouped SHAP + entities + category. **Output:** ordered `reasons[{code, text, contribution, evidence, polarity}]`.
**Libraries:** none beyond the template engine — deliberately dependency-free.
**Strategy:** §14.5. Template library lives in `packages/contracts/taxonomy/` so explanations are reviewable by non-engineers and translatable.

### AI-20 · Recommendation Engine
**Purpose:** actionable next steps. **Input:** category, risk band, entities, reasons. **Output:** ordered `recommendations[{priority, action, rationale, link?}]`.
**Strategy:** deterministic rule table, category-conditional, with a "do not" list. Reviewed by someone with domain/consumer-protection knowledge before release — bad safety advice is a real-world harm, not a bug.

### AI-21 · Feedback & Active Learning
**Purpose:** close the loop. **Input:** `feedback` records + low-confidence predictions. **Output:** prioritised annotation queue.
**Strategy:** uncertainty sampling (predictions near the decision threshold) + all user disagreements + all `insufficient_evidence` outcomes. Runs as a scheduled job, not in the request path.

### AI-22 · Drift & Performance Monitoring
**Purpose:** detect degradation over time. **Input:** rolling prediction and feature logs. **Output:** drift metrics + alerts.
**Libraries:** `evidently` or hand-rolled PSI/KL computation.
**Strategy:** track the feature distribution, predicted-class distribution, OCR confidence distribution, and degradation-flag rate against the training baseline. Alert on threshold breach. Scam language evolves fast — this is a genuine operational need, not decoration.

---

## 10. OCR Strategy

### 10.1 Why OCR is the highest-leverage component

Every downstream text feature depends on OCR output. A 10 % word-error rate does not cost 10 % accuracy — it costs disproportionately more, because the tokens OCR fails on (URLs, UPI IDs, numbers, unusual brand names) are precisely the highest-signal tokens. **OCR quality should be measured and reported as a first-class result, not assumed.**

### 10.2 Preprocessing for OCR

Applied to the `textImage` fork only: grayscale → bilateral denoise (edge-preserving, unlike Gaussian) → CLAHE → deskew if |angle| > 0.5° → adaptive threshold (Sauvola for uneven backgrounds, Otsu for flat ones) → 2× Lanczos upscale when text height is below ~20 px → optional morphological open to remove speckle.

Two screenshot-specific issues that generic OCR advice misses:
- **Dark mode.** A large fraction of chat screenshots are light text on dark bubbles. Tesseract expects dark-on-light. Detect mean bubble luminance and **invert per bubble** — not per image, because a screenshot commonly contains both light incoming and dark outgoing bubbles.
- **Low-contrast bubble backgrounds.** Chat bubbles are tinted, not white. Per-bubble normalisation before thresholding materially outperforms whole-image thresholding.

### 10.3 Engine selection

| Engine | Strengths | Weaknesses | Role |
|--------|-----------|-----------|------|
| **Tesseract 5 (LSTM)** | Fast on CPU, small footprint, mature, per-word confidence, easy multilingual traineddata | Weak on low contrast, stylised fonts, and dense emoji | **Primary** for clean, high-contrast screenshots |
| **EasyOCR** | Much better on noisy/low-contrast/curved text; strong Indic support | Heavier (PyTorch), slower on CPU, coarser confidence | **Secondary** — escalation for low-confidence regions |
| **PaddleOCR** | Best-in-class detection, excellent multilingual, strong on small text | Largest dependency footprint, deployment complexity | **Evaluated, optional** — adopt only if it wins the benchmark by a margin that justifies the container size |

**Decision procedure (do not pick by reputation — measure):** build a 300-image benchmark stratified across the five platforms and light/dark mode, with human-transcribed ground truth. Score each engine on Character Error Rate, Word Error Rate, entity-level recall (did it get the URL/UPI/number right — this matters more than overall WER), and p95 latency. Pick on evidence and publish the table; it is a reportable result.

### 10.4 Confidence scoring

Three levels, all retained:
- **Token confidence** — direct from the engine; drives UI highlighting of uncertain text.
- **Turn confidence** — length-weighted mean over the turn's tokens.
- **Aggregate confidence** — length-weighted mean over the image; a **feature** and a **gate**.

Gates: aggregate < 0.45 → return `OCR_INSUFFICIENT_TEXT` and ask the user for a clearer screenshot rather than guessing. Aggregate in [0.45, 0.65) → proceed but mark the result `degraded` and reduce displayed confidence. Individual regions < 0.60 → escalate to the secondary engine and keep whichever result has higher confidence. (Thresholds are initial values in `systemConfig`, to be tuned on the benchmark — not constants.)

### 10.5 Multilingual handling (A3)

- Run a fast script/language detection (`langdetect` / `fasttext-langdetect`) on a first-pass extraction, then re-run OCR with the correct language pack when the detected script is non-Latin.
- Load Tesseract with combined packs (`eng+hin`) for mixed-script screenshots, which are the norm in Indian chat.
- **Romanised Indic ("Hinglish") is the hard case** — it is Latin script, so language detection reports English, and English NLP resources handle it poorly. Handle it as: keep OCR in English, then apply a Hinglish keyword lexicon and rely on the Sentence-BERT embedding (multilingual variant if the benchmark justifies the size) for semantics. **Document this as a known limitation** rather than overclaiming coverage.
- Persist detected language as a feature; scam-type base rates differ by language.

### 10.6 Error correction

Ordered, most-conservative-first:
1. **Lexicon-guided confusion repair** — apply `0↔O`, `1↔l↔I`, `5↔S`, `rn↔m` substitutions only when the corrected form exists in a domain lexicon and the original does not. Never blind substitution — it destroys UPI IDs and OTP codes.
2. **Context-aware entity repair** — inside a detected URL, prefer character classes valid for domains; inside a detected amount, prefer digits.
3. **SymSpell** over a domain dictionary for ordinary words only, with a strict edit-distance cap and never applied to tokens that validate as an entity.
4. **Never "correct" numbers.** OTPs, amounts, phone numbers, and account numbers are surfaced verbatim with their confidence; a silently "corrected" number is worse than an admittedly uncertain one.
5. Every correction is logged in `corrections[]` so the annotation workbench can show annotators what was altered.

### 10.7 Expected outputs

Full text; per-turn text with direction; per-token text/confidence/bbox; aggregate confidence; detected language and script; engine used and whether escalation occurred; correction log; per-stage timing. Bounding boxes are required for the evidence-overlay feature (FE-06) — an OCR integration that discards positions cannot support the explanation UI, so this must be designed in from the start.

---

## 11. NLP Strategy

### 11.1 Cleaning
Per AI-06. Operations: Unicode NFKC normalisation, mojibake repair (`ftfy`), zero-width and control-character stripping (**flagged**), emoji extraction (**retained as features**), whitespace collapse, URL/entity masking with placeholder tokens *before* linguistic analysis so a long URL doesn't distort length and punctuation statistics, and de-obfuscation with signal retention.

### 11.2 Tokenisation
spaCy tokenisation for linguistic features (handles contractions, punctuation, and URLs sensibly). Separate tokenisation strategies where appropriate: character n-grams for URL analysis, word n-grams (1–2) for TF-IDF, and the model's own subword tokeniser for embeddings. Emoji and currency symbols kept as tokens.

### 11.3 Lemmatisation
spaCy lemmatisation with POS tagging, applied before lexicon matching so `urgent/urgently/urgency` collapse to one lexicon hit. Stopwords retained for the linguistic-feature pass (function words carry the imperative/urgency signal — "you must send now" is mostly stopwords) and removed only for the TF-IDF pass.

### 11.4 Keyword extraction
Two complementary approaches:
- **Curated category lexicons** (versioned data files) — seven per-category keyword sets plus cross-cutting sets (urgency, authority, reward, threat, secrecy, financial-action). Interpretable, controllable, and the primary source of explanation text.
- **Corpus-derived terms** — TF-IDF (1–2 grams, sublinear tf, min_df tuned) fitted on the training set, plus a per-category chi-square/log-odds ranking to *discover* discriminative terms. Discovered terms are reviewed by a human before promotion into the curated lexicon, which keeps the lexicon both data-driven and legible.

### 11.5 Feature families (the interpretable core)

| Family | Example features |
|--------|-----------------|
| Urgency | count/presence of urgency terms, deadline mentions, time-pressure phrases, exclamation density |
| Authority & impersonation | claims of being a bank/govt/courier/HR, official-sounding titles, reference/ticket numbers, claimed-brand token |
| Reward & greed | prize/lottery/bonus/guaranteed-return terms, unrealistic return percentages, "selected"/"congratulations" patterns |
| Threat & fear | account-suspension, legal-action, blocking, penalty terms |
| Secrecy | "don't tell", "confidential", "don't share with bank", "keep this between us" |
| Financial request | payment-verb presence, amount present + magnitude bucket, registration/processing-fee phrasing, "pay to receive" pattern |
| Credential request | **incoming** request for OTP/PIN/CVV/password/Aadhaar/PAN, "share the code you received" |
| Contact-channel shift | "message me on WhatsApp/Telegram", external number present, "click to join group" |
| Link behaviour | URL count, shortener presence, link-with-imperative-CTA pattern |
| Grammar & style | spelling-error rate, ALL-CAPS ratio, punctuation anomaly, emoji density, message length, avg word length, sentence count |
| Direction-aware (AI-04) | `incoming_requests_credential`, `incoming_requests_payment`, `outgoing_contains_otp`, `incoming_turn_count`, `is_first_contact` |
| Platform context | detected platform (one-hot), declared-vs-detected mismatch |
| Semantic | 7 × per-category centroid similarity + 48–64 SVD dims (AI-10) |

Target: ~140–200 features total, of which ~80–120 are individually human-interpretable. **The interpretable features must outnumber and out-rank the opaque ones in explanations** — this is a design constraint on §14, not an accident.

### 11.6 Named Entity Recognition
Hybrid per AI-08. spaCy statistical NER for ORG/PERSON/MONEY/DATE/GPE; deterministic validators for URL, domain, email, phone (`phonenumbers`, region-aware), UPI VPA, IFSC, card-like sequences, OTP-shaped tokens (4–8 digits near an OTP keyword), and currency amounts with unit normalisation. **Do not train a custom NER model at v1** — the entity types that matter are all regex-tractable, and a custom NER needs annotated spans that the project cannot afford to produce alongside everything else. Record this as a deliberate scope decision.

### 11.7 Suspicious URL detection
Purely lexical/offline in the request path (§5.3 rule 5). Features per URL: length, path depth, subdomain count, hyphen and digit counts, `@` presence, IP-literal host, non-standard port, punycode/IDN presence, homoglyph score against a brand list, shortener-domain match, suspicious/cheap TLD match, brand-name-in-subdomain-but-not-registrable-domain (the single strongest lexical phishing signal), HTTPS presence, blocklist match, and entropy of the domain label. Aggregated to image level as max/mean risk and a count of high-risk URLs.

**Explicitly out of scope at v1:** fetching the URL, WHOIS/domain-age lookup, or Safe Browsing API calls — each adds latency, external dependency, privacy leakage (the user's screenshot content leaves the system), and in the fetch case an active security risk. Listed as Phase-2 asynchronous enrichment in §19.

### 11.8 Financial request detection
A composite, rule-plus-feature detector because it is central to five of the seven categories. Signals: payment verb (pay/send/transfer/deposit/recharge) in an **incoming** turn; amount entity present; UPI ID / account number / QR present; fee framing ("registration fee", "processing charge", "security deposit", "GST"); the **"pay-to-receive" inversion** (money demanded in order to receive a larger sum — near-decisive for lottery/job/delivery scams); and urgency co-occurrence. Emitted both as individual features and as one composite `financial_request_score` that appears prominently in explanations.

### 11.9 Embeddings
Per AI-10. Sentence-BERT over the incoming-turn text only (outgoing text is the victim's own words and dilutes the signal). Model choice is a latency/accuracy trade-off measured on the benchmark; `all-MiniLM-L6-v2` (384-dim, ~80 MB) is the default and a multilingual variant is evaluated against A3 requirements. The encoder is loaded once at startup. Both the SVD transformer and the per-category centroids are frozen into the model bundle so training and serving cannot diverge.

### 11.10 Feature generation contract
One module, imported by both `ml/` and `apps/ai-service` (§3.3). It emits a named feature map; the fusion layer orders it against the schema. Every feature declares: name, family, dtype, valid range, missing-value policy, whether it is explanation-eligible, and a human-readable description used by the explanation templates. **This registry is the backbone of the whole ML system** — build it in Milestone 3, before any model training.

---

## 12. Computer Vision Strategy

The visual branch's job is to supply signals that text cannot. Its value must be **proven by ablation** (§13.10), not assumed — if the visual branch adds under ~2 points of macro-F1, that is itself an honest and publishable finding, and the fusion claim must be tempered accordingly.

### 12.1 Scope
Four detectors: QR/barcode, brand impersonation, layout/UI artifacts, and image-quality/provenance signals. All operate on the **colour** `visualImage` (§5.2[3]).

### 12.2 QR detection
- **Detection cascade:** pyzbar (fast, handles multiple symbologies) → OpenCV `QRCodeDetector` → WeChat QR model for damaged/low-res codes. Stop at first success.
- **Retry ladder** for failures: upscale 2×, sharpen, re-threshold, try a rotated variant. Chat-screenshot QRs are often small and recompressed, so a single-pass detector has a poor hit rate.
- **Payload parsing:** classify as `upi://` intent, `http(s)` URL, `tel:`, `SMSTO:`, `WIFI:`, vCard, or plain text. For UPI intents, parse `pa` (payee VPA), `pn` (payee name), `am` (amount), `tn` (note).
- **Risk features:** QR present; QR is a payment intent; **amount is pre-filled**; payee VPA is on the blocklist; payee name mismatches any brand claimed in the text; QR payload is a URL (then inherit all AI-09 features); QR occupies an anomalous position/size in the layout.
- **The decisive insight for this category:** a QR received in a chat that requests *payment* while the message claims the user is *receiving* money is a near-certain scam, because UPI collect/payment QRs debit the scanner. That cross-modal contradiction — QR says "you pay", text says "you receive" — is a fusion feature that neither branch could produce alone, and it is exactly the kind of signal that justifies the multimodal claim in §1.4.

### 12.3 Logo / brand impersonation (A7)
- **Brand template set:** 30–60 entries covering major banks, payment wallets, couriers, e-commerce, government portals, and social platforms. Each entry: logo images at multiple scales, wordmark variants, canonical domains, canonical UPI handles, and category.
- **Matching:** two-tier. Tier 1 — ORB/SIFT keypoint matching plus multi-scale template matching (fast, no model to ship). Tier 2 — embedding similarity from a small pretrained vision backbone against template embeddings, used when Tier 1 is inconclusive.
- **Also match wordmarks via OCR** — the brand *name* in the text is often present without any logo, and it is cheaper and more reliable to detect. In practice this may be the dominant signal; measure both.
- **Output features (mismatch-centric):** `claimed_brand` (from text), `logo_detected_brand`, `logo_confidence`, `brand_domain_match` (does any extracted URL belong to the claimed brand's canonical domains?), `brand_upi_match`, and `impersonation_mismatch` — true when a brand is claimed but the links/VPAs point elsewhere. **`impersonation_mismatch` is the feature that carries the weight; raw logo presence is nearly non-discriminative** because legitimate messages contain logos too.
- **Known limitation to state honestly:** a closed brand set cannot detect impersonation of brands outside it. Report coverage explicitly.

### 12.4 Layout analysis
Region-of-interest driven, using per-platform geometry profiles, with targeted OCR over small regions rather than pure visual detection:
- **Header strip:** contact name vs. bare phone number (unsaved contact — strong signal), business-account badge, verification tick, "online/last seen" text.
- **Above-bubble strip:** "Forwarded" / "Forwarded many times" tag, "This message is from an unknown number", "Tap to add to contacts", encryption notices.
- **Bubble geometry:** turn count, incoming/outgoing ratio (a one-sided conversation with zero outgoing turns is a strong first-contact/broadcast signal), average bubble height, presence of an attachment/document bubble, presence of a link-preview card.
- **Structural anomalies:** nested screenshot chrome (screenshot of a screenshot), cropping that removes the header (often deliberate concealment), aspect ratio outside phone-screenshot norms.

### 12.5 Visual scam indicators & provenance
JPEG quantisation-table analysis and blockiness to estimate recompression generations (heavily recompressed = mass-forwarded); colour-palette deviation from the platform's canonical palette (indicates a doctored or fake-app screenshot); font-rendering inconsistency within a bubble (a strong tamper signal); and residual detection of blur/redaction regions. These are secondary features — cheap to compute, occasionally decisive.

### 12.6 CV feature output
~30–45 features covering QR (8–10), brand/impersonation (8–10), layout (12–15), and provenance/quality (5–8). All named, schema-registered, and explanation-eligible where meaningful.

### 12.7 What is deliberately excluded at v1
Full object detection (YOLO/DETR) on chat UI elements, deep visual-similarity phishing models, screenshot-to-layout-graph parsing, and any GPU-dependent vision model. Rationale: each would add container weight, cold-start latency, and an annotation burden (bounding-box labels) that the project's dataset budget cannot absorb alongside the classification labels. All are listed as Phase-2 in §19.

---

## 13. Machine Learning Strategy

### 13.1 Dataset

**Target composition (v1.0):**

| Split | Purpose | Target size |
|-------|---------|------------|
| Train | Model fitting | ~4,200 (70 %) |
| Validation | Hyperparameter selection, threshold tuning | ~600 (10 %) |
| Calibration | Isotonic/Platt fitting **only** | ~600 (10 %) |
| Test | Reported once, at the end | ~600 (10 %) |
| **Total** | | **~6,000** |

**Distribution targets:** roughly 50/50 genuine/fraudulent for Stage 1; within the fraudulent half, a minimum of **250 samples per scam category** (7 × 250 ≈ 1,750 floor, targeting ~430 each at 3,000 fraudulent); each platform represented with a floor of ~15 % so no platform is a long tail. Perfect balance is neither achievable nor desirable — but the **floors** are what make per-category metrics meaningful, and a category below its floor should be reported as under-powered rather than quietly averaged into a macro score.

**Sourcing (A5):** public scam-text corpora rendered into platform-accurate chat screenshots (synthetic, high volume, low cost); community/crowdsourced donations under consent (real, high value, slow); scam-awareness accounts and public reporting channels (real, licence-permitting); genuine conversations from consenting volunteers and from mundane synthetic content (the genuine class is *harder to source than the scam class* and is routinely underestimated — plan for it explicitly).

**Minimum viable dataset for a first end-to-end result:** ~1,400 samples (200/category) is enough to prove the pipeline and produce preliminary numbers. Do not wait for 6,000 before training the first model — an early model surfaces feature bugs that no amount of data collection will.

**Datasheet requirement:** publish a "Datasheets for Datasets"-style disclosure (`docs/dataset/DATASHEET.md`) covering motivation, composition, collection process, synthetic/real ratio, preprocessing, uses, distribution, maintenance, and ethical review. Without it the dataset contribution is significantly weaker as a research artifact.

### 13.2 Annotation protocol
- A written **annotation guide** (`docs/dataset/ANNOTATION_GUIDE.md`) with a definition, three positive examples, and two hard negatives per category, plus explicit tie-break rules for multi-category messages (**rule: assign the category of the *action being requested*, not the pretext** — a fake job offer that ultimately demands a UPI payment is `job`, because the pretext determines the user's mental model and hence the correct advice).
- Every sample annotated by one annotator; a **20 % overlap sample double-annotated** for Cohen's/Fleiss' κ. Target κ ≥ 0.75; below 0.6 means the taxonomy is ambiguous and the guide must be revised before continuing — a low κ discovered late invalidates everything downstream.
- Disagreements go to an adjudication queue (AD-02).
- OCR text is human-corrected for a stratified subsample (~500) to serve as **OCR ground truth**, enabling §10.3's benchmark and a separate reportable result.

### 13.3 Splitting — the most important methodological decision
Splits are **group-aware and stratified**, using `datasetSamples.groupKey` (§7.2). All samples sharing a template, a source conversation, or a campaign go into the **same** split. A naive random split leaks near-duplicates between train and test and produces inflated accuracy that collapses in the real demo — this is the single most likely way this project's headline number becomes indefensible.

Additionally, hold out a **real-only test subset**: a portion of test that contains no synthetic samples. Report metrics on (a) the full test set and (b) the real-only subset. If they diverge sharply, the model has learned rendering artifacts, and that must be stated (§18.3).

Splits are assigned once, written to the sample document, and treated as immutable. Reassigning splits between experiments is silent leakage.

### 13.4 Feature engineering
Governed entirely by §11.10's shared registry. Pipeline: extract named features → apply per-feature missing-value policy → one-hot encode categoricals (platform, detected language) → scale only where the model needs it (tree ensembles don't, but the registry supports it for baseline comparison) → assemble in schema order. Fitted transformers (SVD, TF-IDF vocabulary, category centroids, scalers) are fitted on **train only** and serialised into the model bundle.

### 13.5 Baseline models
Establish, in order, because each answers a question that the final result must be defended against:
1. **Majority class** — the floor.
2. **Keyword rules only** — "does ML earn its place?"
3. **TF-IDF + Logistic Regression on OCR text** — "does anything beyond bag-of-words help?"
4. **Interpretable features only (no embeddings, no CV)** — the text-lexical baseline.
5. **Text branch complete (features + embeddings)** — the ablation reference point for the fusion claim.

Baselines are not busywork; without #5 there is no evidence that the visual branch contributes, and the central claim of §1.4 #2 is unsupported.

### 13.6 Final models
Per the abstract: **Random Forest and XGBoost**, trained for both stages and compared.
- **Stage 1 (binary):** class weighting or `scale_pos_weight` to reflect the asymmetric cost of a false negative (§13.9).
- **Stage 2 (7-class):** multi-class softmax objective; class weights to counter residual imbalance; consider one-vs-rest if a specific category is chronically confused.
- Both are natural fits for the feature set: mixed types, non-linear interactions, no scaling requirement, robust to irrelevant features, and — decisively — **exactly supported by SHAP's fast `TreeExplainer`**, which the explainability requirement depends on.

### 13.7 Hyperparameter tuning
`RandomizedSearchCV` for a broad sweep, then Optuna (TPE) for refinement, with **StratifiedGroupKFold (k=5)** — group-aware CV, matching §13.3's discipline. Tuned on validation only; the test set is untouched until the end. Search spaces: RF — `n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`, `class_weight`; XGBoost — `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`, `gamma`, `reg_lambda`, `scale_pos_weight`. Every run logged to MLflow with config, git SHA, dataset version, and feature-schema version.

### 13.8 Evaluation metrics

**Stage 1:** accuracy, precision, recall, F1 (fraudulent as positive), ROC-AUC, PR-AUC (**more informative than ROC-AUC under imbalance**), confusion matrix, and the full precision/recall trade-off curve for threshold selection.
**Stage 2:** per-category precision/recall/F1/support, macro-F1 (**the headline number** — it weights rare categories equally, which is what a seven-class contribution claim requires), weighted-F1, 7×7 confusion matrix, and top-2 accuracy (useful because some categories genuinely overlap).
**Calibration:** ECE, Brier score, reliability diagram.
**End-to-end:** accuracy as a function of OCR confidence bucket (this reveals how much of the error is really an OCR problem), per-platform breakdown, real-vs-synthetic breakdown, degradation-rate.
**Operational:** p50/p95/p99 latency per stage; throughput.

Report with confidence intervals (bootstrap over the test set). A single point estimate on a ~600-sample test set is not a result — the interval on per-category F1 at n≈85 per category is wide, and stating it honestly is stronger than stating a bare number that a reviewer will immediately question.

### 13.9 Threshold selection
The Stage-1 decision threshold is a **product decision, not a default of 0.5**. The cost asymmetry is real: a missed scam can cost the user money; a false alarm costs them mild annoyance. Set the threshold on the validation PR curve to target **recall ≥ 0.92 on fraudulent** while keeping precision acceptable, and expose the chosen value in `systemConfig` so it is tunable without a redeploy. Map the calibrated probability to the five risk bands (safe / low / medium / high / critical) with band edges also stored as configuration, and use an `insufficient_evidence` outcome for the ambiguous middle rather than forcing a verdict.

### 13.10 Ablation study (required deliverable)
Train and evaluate: (1) text-lexical features only; (2) + embeddings; (3) + CV features (full fusion); (4) full fusion − chat-structure features; (5) full fusion − QR features; (6) full fusion − brand features; (7) full fusion with a naive random split (to quantify how much leakage would have inflated the result). This table is the empirical backbone of the fusion and novelty claims and should be planned into Milestone 6, not improvised at write-up time.

### 13.11 Model export
The deployable unit is a **bundle**, not a pickle: Stage-1 model, Stage-2 model, both calibrators, the SVD transformer, TF-IDF vocabulary, category centroids, encoders/scalers, the **feature schema** (names, order, dtypes, missing policies), thresholds and band edges, and `metadata.json` (version, git SHA, dataset version, training date, metrics, library versions). Serialised with joblib (plus XGBoost's native format for the boosters, which is version-portable where pickle is not), hashed, and uploaded to `/artifacts/models/{version}/`.

**Loading contract:** the service verifies the bundle hash and asserts that the bundle's feature-schema version matches the code's, and **refuses to start on mismatch**. Failing loudly at startup is the correct behaviour; serving predictions from a mismatched schema is the worst possible failure mode because it is silent.

### 13.12 Inference
Models load once in the FastAPI lifespan handler. Single-sample prediction: fuse → Stage 1 → calibrate → threshold → Stage 2 if fraudulent → calibrate → risk score → SHAP → explanation → recommendation. Budget ≤ 400 ms (§3.1). Batch mode reuses the identical code path with vectorised feature assembly, guaranteeing that offline evaluation measures the same thing production serves.

---

## 14. Explainable AI Strategy

### 14.1 What is being explained, and to whom
Two audiences with different needs, served from the same computation:
- **The end user** needs to know *why they should not click the link*. They need 3–5 grounded sentences, not attributions.
- **The researcher/examiner** needs to verify the model isn't exploiting a spurious artifact. They need the full attribution vector, global importance, and the ability to recompute.

The design serves the researcher's need completely and the user's need selectively. Confusing the two — showing users raw SHAP values — is the standard failure of XAI in applied systems.

### 14.2 SHAP integration
`shap.TreeExplainer` on both stages. Chosen because it is **exact** for tree ensembles (not sampled like KernelSHAP), fast enough for the request path, and directly compatible with RF and XGBoost. The explainer is constructed once at startup and reused; per-request cost is then a few milliseconds.

Two explainers are maintained — one per stage — and they explain different questions: Stage 1 explains *"why is this fraudulent?"*, Stage 2 explains *"why this category?"*. The UI leads with the Stage-1 explanation, because that is the decision the user acts on, and offers the Stage-2 explanation secondarily.

Global explanations (mean |SHAP| across the test set, beeswarm plots, dependence plots) are generated offline during evaluation and shipped in `docs/evaluation/` and the admin dashboard — **not** computed per request.

### 14.3 Handling the interpretability/accuracy tension
The embedding dimensions are predictive but individually meaningless. Left unmanaged, they will occupy the top of the attribution ranking and produce explanations like "dimension 23 contributed 0.08" — worthless. Three mitigations, applied together:

1. **Grouped attribution.** SHAP values are summed within feature groups defined in the registry (`urgency`, `financial_request`, `url_risk`, `qr_risk`, `brand_impersonation`, `credential_request`, `layout`, `semantic_similarity`, …). Users see groups; researchers can expand.
2. **Explanation eligibility flag.** Each feature declares whether it may appear in user-facing text. All SVD dimensions collapse into a single `semantic_similarity` group rendered as "the wording closely matches known *lottery* scam messages" — backed by the per-category centroid similarity (AI-10), which is genuinely interpretable.
3. **Dimensionality discipline.** Keeping embeddings at 48–64 dims rather than 384 both limits their aggregate share of attribution and keeps SHAP cheap.

### 14.4 Confidence score vs. risk score — deliberately different things
Conflating these is a common and consequential error; they are kept separate:

- **Confidence** = the calibrated probability from the model (§13, AI-17). It answers *"how sure is the model?"* It is **penalised** by pipeline degradation: low OCR confidence, failed branches, or `structure_parsed=false` reduce displayed confidence via a documented multiplicative penalty, because a model cannot be trusted more than its inputs.
- **Risk score (0–100)** = how dangerous the situation is *for the user*. It combines the fraud probability with **severity**: presence of a credential request, presence of a payment demand with a concrete amount, a blocklisted indicator, a pre-filled-amount payment QR. A message that is only 70 % likely to be fraudulent but is asking for an OTP is **high risk** — because the downside is catastrophic and the correct advice ("don't share it") is safe regardless. The risk score, not the probability, drives the verdict banner and the recommendations.

Both are shown, with distinct labels and a tooltip explaining the difference. The formula for the risk score is documented and stored in configuration, not hidden in code.

### 14.5 From attribution to human-readable explanation
Deterministic four-step mapping (AI-19):
1. Take the top-K grouped contributions (K = 5) toward the predicted class, keeping both positive and, where informative, negative contributors ("nothing in the message asked for money" is useful reassurance on a genuine verdict).
2. Look up a template keyed by `(featureGroup, polarity, category)` from the versioned template library.
3. **Ground the template in extracted evidence** — inject the actual matched phrase, URL, amount, or entity from the pipeline output. `"Uses time pressure — the message says 'offer expires in 2 hours'"` rather than `"urgency_score = 0.81"`. Every reason carries the bounding box of its evidence so the UI can highlight it on the original image (FE-06).
4. Order by contribution magnitude and render.

Rules: templates are plain-language and jargon-free; a reason is only emitted if its evidence exists (no unbacked claims); **no LLM is used**, so the explanation cannot hallucinate, is deterministic and reproducible for the paper, and adds no latency or vendor dependency.

### 14.6 Recommendations
Rule table keyed by `(category, riskBand, entityFlags)`, producing prioritised imperative actions plus an explicit "do not" list plus reporting links. Examples of the category-conditionality that makes this worth building: OTP → "never share the code; no bank or company will ask for it"; QR → "scanning a QR **sends** money, it never receives it — check the payee name before approving"; Job → "legitimate employers never charge a registration or training fee"; Investment → "guaranteed returns do not exist; check SEBI/regulator registration"; Delivery → "verify via the courier's official app or website, never via a link in a message". Reviewed by a domain-competent human before release (AI-20).

### 14.7 Honesty requirements
- When OCR confidence is low or a branch failed, the UI **says so** and lowers confidence accordingly rather than presenting a clean verdict.
- `insufficient_evidence` is a first-class outcome, not a failure state.
- A permanent limitations statement (FE-11): the system can be wrong in both directions, is not a substitute for the user's own judgement, and its coverage of brands, languages, and platforms is bounded.
- The verdict is never phrased as certainty ("This is a scam") but as an assessment with confidence ("This looks like a job scam — high confidence").

---

## 15. Development Roadmap

Twelve milestones. Complexity is relative effort (S/M/L/XL), not calendar time — sequence and dependencies are the useful content; durations depend on team size and are shown as indicative for a 2–3 person team.

---

### M0 · Foundations & Contracts — *Complexity: M · ~1 week*
**Objectives:** repository, tooling, and the shared contract layer that everything else depends on.
**Deliverables:** monorepo restructure (`apps/web`, `apps/ai-service`, `ml/`, `packages/contracts`); `packages/contracts` with initial JSON Schemas, the taxonomy as data, and codegen to JSDoc + Pydantic; linting/formatting/pre-commit; CI skeleton; Docker Compose for local dev; ADR process; environment configuration with fail-fast validation; the A9 decision (JS+JSDoc vs TypeScript) recorded as an ADR.
**Dependencies:** none.
**Risks:** contract churn later — mitigate by treating schemas as versioned and additive, never edited in place after M4.

### M1 · Firebase & Authentication — *Complexity: M · ~1 week*
**Objectives:** identity, storage, and the security-rules baseline.
**Deliverables:** Firebase project (dev + prod); Auth with email/password + Google + verification + reset; **session-cookie flow** (ID token → HTTP-only cookie via Admin SDK) in `hooks.server.js`; `requireAuth`/`requireAdmin` middleware with custom claims; `firestore.rules` and `storage.rules` default-deny with tests; `firestore.indexes.json`; the `users` collection; audit-log writer.
**Dependencies:** M0.
**Risks:** the SvelteKit + Firebase Auth SSR session pattern is the most commonly mis-implemented piece of this stack (teams store tokens in `localStorage` and break SSR and security simultaneously). Budget time for it and write the ADR.

### M2 · Data Collection & Annotation Infrastructure — *Complexity: L · ~2–3 weeks, then continuous*
**Objectives:** start producing the dataset. **Begins in parallel with M1 and never stops until M9.**
**Deliverables:** taxonomy document with definitions and edge cases; annotation guide; ethics/consent documentation and approval submission (A6); `datasetSamples` schema; annotation workbench (AD-01) — even a rough one; synthetic screenshot generator (renders text corpora into platform-accurate chat UIs across the five platforms, light/dark, multiple device widths, with `groupKey` stamped per template); collection of the first 500 real samples; double-annotation and first κ measurement.
**Dependencies:** M0, M1 (for auth on the workbench).
**Risks:** **this is the critical path and the most underestimated milestone in the entire project.** Data collection is slow, ethics approval is slower, and annotation is tedious. Starting it late is the single most likely cause of project failure. Mitigate by starting it in week 1, leaning on synthetic generation for volume, and setting a weekly annotation quota.

### M3 · AI Service Skeleton & Feature Registry — *Complexity: M · ~1 week*
**Objectives:** the Python service shell and — critically — the feature registry, before any feature exists.
**Deliverables:** FastAPI app with lifespan model loading, health/ready, structured logging, request IDs, error handling, timing middleware; the pipeline orchestrator with stage interface, concurrency, and the degradation policy; **the feature registry** (§11.10) with schema versioning and the contract test that asserts feature ordering; a stub `/v1/predict` returning a schema-valid mock so the frontend can integrate immediately; container image; storage client.
**Dependencies:** M0.
**Risks:** low. High leverage — the stub unblocks M7 frontend work weeks early.

### M4 · Text Branch — *Complexity: L · ~2–3 weeks*
**Objectives:** preprocessing through NLP feature generation.
**Deliverables:** AI-01 validation; AI-02 preprocessing with the colour/text fork and per-platform profiles; AI-03 platform identification; AI-04 chat structure parsing; the OCR benchmark set (300 images, human-transcribed) and the **engine comparison table** (§10.3); AI-05 OCR with dual-engine escalation; AI-06 cleaning; AI-07 linguistic features; AI-08 NER; AI-09 URL risk; AI-10 embeddings; lexicon resource files.
**Dependencies:** M3; M2 for the benchmark images.
**Risks:** OCR quality on real-world screenshots is the top technical risk (§18.1). Dark mode and low contrast will underperform initial expectations — the per-bubble inversion of §10.2 is the mitigation, and it must be built, not deferred.

### M5 · Visual Branch — *Complexity: M–L · ~2 weeks*
**Objectives:** the CV features.
**Deliverables:** AI-11 QR with the detection cascade and UPI payload parsing; brand template set curation (30–60 brands) and AI-12 two-tier matching with the mismatch feature; AI-13 layout analysis with per-platform ROI profiles; AI-14 visual quality/provenance features; visual-branch unit tests with golden images.
**Dependencies:** M3, M4 (AI-03/AI-04 outputs; entity extraction for the mismatch feature).
**Risks:** brand matching underperforms on stylised/partial logos — mitigate by leaning on OCR wordmark detection, which §12.3 predicts may dominate anyway. Curating the brand set is unglamorous manual work; schedule it explicitly.

### M6 · Fusion, Training & Evaluation — *Complexity: L · ~2–3 weeks*
**Objectives:** the models and the honest numbers.
**Deliverables:** AI-14 fusion with the ordering contract test; group-aware stratified splitting (§13.3); training pipelines for Stage 1 and Stage 2 across RF and XGBoost; hyperparameter tuning with StratifiedGroupKFold; the full baseline ladder (§13.5); the **ablation study** (§13.10); calibration (AI-17) with reliability diagrams; threshold and risk-band selection; the evaluation report with confidence intervals and per-platform/real-vs-synthetic breakdowns; MLflow experiment tracking; the model bundle exporter and `modelVersions` registry.
**Dependencies:** M4, M5, and **M2 at ≥ 1,400 samples**.
**Risks:** insufficient data for some categories; leakage from synthetic templates (§18.3); disappointing macro-F1. Mitigate by running a first training pass on partial data as soon as ~1,400 samples exist, so problems surface with weeks of runway rather than days.

### M7 · Explainability Layer — *Complexity: M · ~1–1.5 weeks*
**Objectives:** turn predictions into trustworthy explanations.
**Deliverables:** AI-18 SHAP with grouped attribution; the explanation template library in `packages/contracts`; AI-19 evidence-grounded NLG; the risk-score formula (§14.4) with the degradation penalty; AI-20 recommendation rule table with domain review; global explanation artifacts for `docs/evaluation/`; explanation quality review (a human reads 100 generated explanations and rates coherence — a cheap, reportable evaluation).
**Dependencies:** M6.
**Risks:** explanations that are technically correct but useless to a layperson. Mitigate with the human review, ideally including non-technical readers.

### M8 · Web Integration — *Complexity: L · ~2–3 weeks*
**Objectives:** the product.
**Deliverables:** all §8.2 API routes with validation, rate limiting, and error handling; the AI service client with retry/timeout/circuit breaker; repositories and services; shadcn-svelte component set; upload flow with paste support, client-side resize, and the redaction tool (FE-03); progress UI via Firestore listeners; the result dashboard with verdict, risk gauge, reasons, entities, and the evidence overlay; explanation detail view; history with filters and pagination; feedback UI; data controls and consent; the education/limitations pages.
**Dependencies:** M1, M3 (stub is enough to start), M7 for the real response shape.
**Risks:** scope creep in the UI. Mitigate by building the result dashboard first — it is the product; everything else is navigation.

### M9 · Admin & Dataset Tooling — *Complexity: M · ~1.5 weeks*
**Objectives:** productionise the annotation and model workflow.
**Deliverables:** full annotation workbench with OCR pre-fill and correction; κ computation and adjudication queue; dataset explorer with the balance matrix; versioned export with manifest and datasheet; model registry UI with transactional promote/rollback; metrics dashboard; misclassification review queue; blocklist management; user/abuse management.
**Dependencies:** M2 (rough version), M6, M8.
**Risks:** low. Often deferred and then regretted — the dataset contribution depends on it.

### M10 · Hardening — *Complexity: M · ~1.5 weeks*
**Objectives:** make it safe and fast enough to demo and deploy.
**Deliverables:** security review against §18.7 with rules tests; rate limiting and quota verification under load; load testing to the §3.1 targets with per-stage profiling and optimisation; accessibility audit (axe + manual screen reader) to WCAG AA; error-handling and degraded-path testing (kill the AI service mid-request and verify the UX); monitoring, alerting, and dashboards; retention/purge jobs; backup and restore rehearsal; deployment pipeline for both services; runbook.
**Dependencies:** M8, M9.
**Risks:** performance targets missed — the likely culprits are OCR and cold starts; mitigations are per-bubble region OCR, engine selection, min-instances, and (if needed) moving to the async queue the API contract already anticipates.

### M11 · Evaluation, Iteration & Write-up — *Complexity: M · ~2 weeks*
**Objectives:** the research output.
**Deliverables:** final held-out test evaluation (run **once**); error analysis by category, platform, and OCR-confidence bucket; targeted data collection for weak categories and a retrain; the dataset release package (redacted images, labels, splits, datasheet, licence); model card; all figures and tables; a small **user study** (10–20 participants rating explanation clarity and trust — this directly supports the §1.4 #3 contribution and is the cheapest available strengthening of the paper); the final report.
**Dependencies:** all.
**Risks:** results below expectation. Mitigate by treating an honest negative result on the visual branch as a finding, and by having the ablation table (M6) ready early enough to act on.

### M12 · Deployment & Handover — *Complexity: S · ~0.5 week*
**Deliverables:** production deployment of both services; custom domain and TLS; monitoring live; demo script and seeded demo data; README and setup documentation; handover session.
**Dependencies:** M10, M11.

**Indicative total:** ~16–20 weeks for a 2–3 person team, with M2 running continuously in the background from week 1.

---

## 16. Project Dependency Graph

### 16.1 Module dependencies

```
                          ┌──────────────────────┐
                          │ M0 Foundations       │
                          │ (contracts, taxonomy)│
                          └───┬──────────┬───────┘
                              │          │
                ┌─────────────▼──┐   ┌───▼───────────────┐
                │ M1 Firebase    │   │ M3 AI Skeleton    │
                │    + Auth      │   │  + FEATURE        │
                └───┬────────┬───┘   │    REGISTRY       │
                    │        │       └───┬───────────┬───┘
                    │        │           │           │
        ┌───────────▼──────┐ │   ┌───────▼─────┐ ┌───▼──────────┐
        │ M2 DATA + ANNOT. │ │   │ M4 Text     │ │ M5 Visual    │
        │  ★ CRITICAL PATH │ │   │    Branch   │ │    Branch    │
        │  (continuous)    │ │   └──────┬──────┘ └──────┬───────┘
        └──────────┬───────┘ │          │               │
                   │         │          └───────┬───────┘
                   │         │                  │
                   └─────────┼──────────────────▼────────┐
                             │        │ M6 Fusion +      │
                             │        │    Training      │
                             │        └────────┬─────────┘
                             │                 │
                             │        ┌────────▼─────────┐
                             │        │ M7 Explainability│
                             │        └────────┬─────────┘
                             │                 │
                     ┌───────▼─────────────────▼─────────┐
                     │ M8 Web Integration                │
                     │ (can START on M3 stub, weeks early)│
                     └───────────────┬───────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ M9 Admin & Dataset  │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ M10 Hardening       │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ M11 Evaluation      │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ M12 Deployment      │
                          └─────────────────────┘
```

### 16.2 Fine-grained AI module dependencies

```
AI-01 validation
  └─► AI-02 preprocessing ──┬─► AI-03 platform id ─► AI-04 chat parsing
                            │                             │
                            │        ┌────────────────────┴──────────┐
                            │        ▼                               ▼
                            │   AI-05 OCR                    AI-11 QR ─┐
                            │        ▼                       AI-12 brand├─► (needs AI-08 for mismatch)
                            │   AI-06 cleaning               AI-13 layout┘
                            │        ├─► AI-07 linguistic         │
                            │        ├─► AI-08 NER ─► AI-09 URL risk
                            │        └─► AI-10 embeddings         │
                            │                 │                   │
                            └─────────────────┴─────────┬─────────┘
                                                        ▼
                                                 AI-14 fusion
                                                        ▼
                                          AI-15 stage1 ─► AI-16 stage2
                                                        ▼
                                                 AI-17 calibration
                                                        ▼
                                                 AI-18 SHAP
                                                        ▼
                                          AI-19 NLG ─► AI-20 recommendations

AI-21 active learning  ← feedback + AI-16   (offline, non-blocking)
AI-22 drift monitoring ← prediction logs    (offline, non-blocking)
```

### 16.3 Critical path

**M0 → M2 (data + annotation) → M6 (training) → M7 (XAI) → M11 (evaluation)**

Everything else can slip without moving the end date; **M2 cannot**. The model cannot be trained without data, evaluation cannot happen without a model, and the write-up cannot happen without evaluation. Data collection has an irreducible lead time (ethics approval, human annotation throughput) that no amount of engineering effort compresses.

Practical implications:
- Start M2 in week 1, before the AI service exists.
- Track annotated-samples-per-week as **the** project health metric. If it falls behind the burn-down to 1,400 by M6's start, escalate immediately — add annotators or increase the synthetic ratio (accepting the §18.3 cost).
- Submit ethics/consent paperwork in week 1; it is pure lead time.
- Do the first training run at 1,400 samples, not at 6,000.

### 16.4 Modules that can be developed independently

Genuinely parallelisable, with no cross-dependency:

| Track | Modules | Can start after |
|-------|---------|----------------|
| **Data** | Taxonomy, annotation guide, ethics docs, synthetic generator, collection | M0 (partly before) |
| **Web/UI** | All components and routes against the M3 stub; upload flow; result dashboard; education pages | M3 stub |
| **Text branch** | AI-05…AI-10 | M3 |
| **Visual branch** | AI-11…AI-13 (except the brand-mismatch feature) | M3 |
| **Infra** | Docker, CI/CD, monitoring, security rules, load-test harness | M0 |
| **Resources** | Lexicons, brand templates, platform profiles, recommendation copy | M0 — no code dependency at all |
| **OCR benchmark** | Benchmark set + engine comparison | M2 images only |

The resource files (lexicons, brand set, recommendation copy) are worth highlighting: they are substantial, entirely non-blocking, require no programming, and can absorb a team member or collaborator who is idle at any point in the schedule.

---

## 17. Development Order

### 17.1 Recommended sequence

```
Week 1      M0 Foundations ─┬─ M2 Data track STARTS (never stops) ── ethics submitted
Week 2      M1 Firebase/Auth ┘
Week 3      M3 AI skeleton + FEATURE REGISTRY  ──►  M8 Web track starts against the stub
Weeks 4–6   M4 Text branch      ║  M8 Web (parallel)  ║  M2 continues
Weeks 6–8   M5 Visual branch    ║  M8 Web (parallel)  ║  M2 continues
Week 7      ★ First training pass on partial data (~1,400 samples) — smoke, not results
Weeks 8–10  M6 Fusion + training + ablation
Weeks 10–11 M7 Explainability
Weeks 11–13 M8 Web integration completed against real responses
Weeks 13–14 M9 Admin & dataset tooling
Weeks 14–15 M10 Hardening
Weeks 15–17 M11 Evaluation, targeted collection, retrain, write-up, user study
Week 18     M12 Deployment & handover
```

### 17.2 Why this order

**Contracts before anything.** Two languages and three deliverables share the same data shapes. Defining them first means the frontend and the AI service can be built simultaneously against the same definition rather than being reconciled painfully at integration time. This is the highest-return day of work in the project.

**Data starts first and never stops.** §16.3. The only irreducible lead time in the plan.

**The feature registry precedes any feature.** Building features first and formalising them later guarantees a training/serving skew, because two divergent implementations will exist before anyone notices. Registry-first costs a day and eliminates an entire class of bug that is famously hard to diagnose.

**The stub `/v1/predict` precedes the real one.** A schema-valid mock unblocks weeks of frontend work in parallel with ML development. Without it, the web track waits idle until week 10 and then has three weeks of work compressed into one.

**Text branch before visual branch.** Text carries most of the signal, is the prerequisite for the brand-mismatch feature, and produces a working text-only model early. If the schedule compresses, a text-only system is a complete product; a vision-only system is not.

**Train early on partial data.** The first training run is a *debugging* exercise, not a results exercise. It surfaces feature bugs, leakage, and pipeline mismatches while there is still time to fix them. Teams that wait for the "complete" dataset discover these problems in the final fortnight.

**Explainability after the model, before the UI's final form.** The response shape depends on what SHAP produces; building the explanation UI against a guess means rebuilding it.

**Admin after the core product.** Tempting to build first (it is easier), but it delivers no user value and its requirements are clarified by having a real dataset and real predictions to manage.

**Hardening before final evaluation.** Load and security testing sometimes force architectural change; discovering that after the results are written up means redoing the results.

### 17.3 Ordering rules to hold under pressure

1. Never let the data track pause for an engineering push.
2. Never let two copies of feature code exist, even briefly.
3. Never touch the test split before M11.
4. Never merge a schema change without regenerating both language bindings (CI enforces).
5. If schedule pressure forces a cut, cut **scope inside M5 (visual)** and **M9 (admin polish)** — never M2, M6, or M11.

---

## 18. Potential Challenges

Ordered by expected impact. Each has a concrete mitigation and, where useful, a fallback.

### 18.1 Technical risks

**R1 · OCR accuracy on real screenshots (High likelihood / High impact).** Every text feature depends on it, and real screenshots are worse than test images: dark mode, low-contrast bubbles, heavy recompression from repeated forwarding, mixed scripts, emoji, small text on high-DPI captures. *Mitigation:* per-bubble inversion and normalisation (§10.2); the measured engine benchmark rather than a guessed choice; dual-engine escalation; per-token confidence surfaced honestly; the `OCR_INSUFFICIENT_TEXT` gate instead of guessing. *Fallback:* allow the user to correct extracted text before analysis — cheap to build, dramatically improves the worst case, and produces free annotation data.

**R2 · Chat structure parsing is brittle across platform versions (Medium/Medium).** Bubble colours and geometry change with app updates and themes. *Mitigation:* per-platform profiles as **data files**, not code, so updates are a config change; explicit graceful degradation with `structure_parsed=false`; direction-aware features designed to be optional rather than required.

**R3 · Latency budget overrun (Medium/Medium).** OCR plus embeddings plus SHAP on CPU can exceed 8 s on large images. *Mitigation:* concurrent branches; region-wise OCR; small embedding model; downscale before processing; startup-loaded models and explainer. *Fallback:* the API contract is already async (§8.2), so moving to a queue with progress streaming requires no client change — this is why that decision was made in §3.2.

**R4 · Cold starts (Medium/Medium).** A 1.5–2 GB container with model loading takes 15–25 s to become ready — catastrophic during a live demo. *Mitigation:* min-instances ≥ 1 in demo windows; slim the image (CPU-only torch wheels, no build toolchain in the final layer); lazy-load the secondary OCR engine; a readiness probe that only passes when models are loaded; a warm-up ping before demos.

**R5 · Firebase + SvelteKit SSR auth complexity (Medium/Low).** Widely mis-implemented. *Mitigation:* the session-cookie pattern specified in §4.3 and M1, written up as an ADR, with integration tests covering expiry and revocation.

### 18.2 AI/model risks

**R6 · Poor per-category performance on rare categories (High/High).** With ~250–430 samples per category, some — likely delivery and lottery, which overlap heavily with generic phishing — will underperform. *Mitigation:* per-category floors enforced during collection; macro-F1 as the headline metric so the problem is visible rather than hidden; targeted collection in M11 driven by the confusion matrix; top-2 accuracy reported as a secondary metric. *Fallback:* merge chronically confused categories in the reported taxonomy, documenting the merge honestly, rather than reporting a 7-class result where two classes are noise.

**R7 · Explanations that are correct but useless (Medium/High).** Trust is the actual product (§1.2); an unhelpful explanation defeats the project's purpose. *Mitigation:* evidence grounding (§14.5); grouped attribution; the human explanation-quality review in M7; the user study in M11 with non-technical participants.

**R8 · Overconfident, uncalibrated probabilities (High if unaddressed/Medium).** Tree ensembles are systematically overconfident, and the UI shows a number users will anchor on. *Mitigation:* a dedicated calibration split, isotonic calibration, ECE/Brier reporting, and the degradation penalty on displayed confidence (§14.4).

**R9 · Adversarial evasion (Medium/Medium).** Scammers adapt: obfuscated spellings, text rendered as images inside the screenshot, homoglyphs, splitting the scam across turns. *Mitigation:* obfuscation *presence* as a feature (§5.2[7]) — evasion attempts become signal; embeddings for paraphrase robustness; the drift monitor (AI-22); the feedback loop for fast dataset updates. *Honest limitation:* a determined adversary with access to the model can evade it; state this in the limitations section rather than claiming robustness.

### 18.3 Dataset risks

**R10 · Synthetic-data leakage and artifact learning (High/Critical).** This is the most dangerous risk in the project. If synthetic screenshots come from a handful of templates, the model can learn "template 3 ⇒ lottery scam" and report 97 % accuracy that collapses on real screenshots. *Mitigation:* `groupKey` stamped on every synthetic sample and group-aware splitting (§13.3); wide randomisation in the generator (fonts, widths, themes, timestamps, avatars, contact names, message counts, compression); the **real-only test subset** reported separately; and ablation variant #7 (naive random split) included specifically to quantify how much leakage *would* have inflated the number. *Detection:* if real-only test performance is far below full-test performance, artifact learning has occurred — treat that as a finding and rebalance toward real data.

**R11 · Insufficient real data (High/High).** Real scam screenshots are hard to obtain at volume, and the **genuine** class is often harder still. *Mitigation:* start week 1; multiple sourcing channels; synthetic for volume with real reserved for test; a documented minimum real-sample fraction per category; partner with a consumer-protection or campus group for donations.

**R12 · Annotation quality and taxonomy ambiguity (Medium/High).** Multi-purpose scams genuinely span categories. Low κ discovered late invalidates everything downstream. *Mitigation:* the written guide with hard negatives; the "category of the requested action, not the pretext" tie-break rule; 20 % double annotation with κ measured **early** (M2, not M11); an adjudication queue; guide revision if κ < 0.6.

**R13 · Privacy and legal exposure (Medium/Critical).** Screenshots contain third-party personal data — names, phone numbers, photos, private conversation content — from people who never consented. Publishing such a dataset without redaction and approval is a serious legal and ethical failure under India's DPDP Act 2023 and GDPR. *Mitigation:* explicit opt-in consent (§7.2 `users.consent`); pre-upload user redaction (FE-03) plus automated PII detection; mandatory `pii.redacted` and `pii.reviewedBy` before any sample enters a published version; institutional ethics review submitted in week 1; the datasheet documenting collection and consent; a published takedown process. **Treat this as a blocking requirement for the dataset contribution, not a compliance formality.**

### 18.4 Deployment risks

**R14 · Container size and build times (Medium/Low).** Tesseract, OpenCV, PyTorch, spaCy models, and XGBoost together produce a large image. *Mitigation:* multi-stage builds; CPU-only torch wheels; `opencv-python-headless`; download models at build time into a cached layer; aggressive layer ordering; drop PaddleOCR unless the benchmark justifies it.

**R15 · Cost overrun (Low/Medium).** Always-warm instances plus Firestore reads plus Storage egress. *Mitigation:* quotas and rate limits from day one (BE-06); thumbnails for lists rather than full images; storage lifecycle rules; billing alerts; min-instances only during demo windows.

**R16 · Two-service deployment coupling (Medium/Low).** A response-shape change deployed to one service and not the other breaks production. *Mitigation:* versioned contracts with additive-only changes; the CI codegen gate; independent deploy pipelines with contract tests running against the deployed pair.

### 18.5 Performance bottlenecks

Ranked by expected cost: OCR (highest — mitigated by region-wise processing and engine choice); image download and decode (mitigated by client-side downscale before upload); embedding inference (mitigated by a small model and startup loading); SHAP (mitigated by `TreeExplainer` and reduced feature count); Firestore writes of large detail documents (mitigated by the subcollection split, §7.2); frontend image handling on low-end phones (mitigated by client-side resize using canvas with an explicit memory cap).

### 18.6 Scalability issues

Firestore's lack of aggregation queries will constrain the admin dashboard as volume grows — mitigate with maintained counters now, BigQuery export later. Single-region deployment adds latency for distant users — acceptable at A2 scale, noted for later. Synchronous prediction ties up a worker for seconds, capping throughput per instance — the async contract is the pre-built escape hatch. Model bundle size grows with each added feature family — versioned artifacts and a documented size budget.

### 18.7 Security concerns

| Threat | Mitigation |
|--------|-----------|
| Malicious image upload (decompression bomb, polyglot file, embedded payload) | Magic-byte verification, decoded-pixel cap, dimension limits, re-encode through a decoder rather than passing bytes through, EXIF strip, size cap enforced in Storage rules |
| SSRF via decoded QR / extracted URL | **Never fetch any extracted URL.** Lexical analysis only (§11.7). If Phase-2 enrichment is added, it runs out-of-band through a vetted third-party API, never a direct fetch |
| Unauthorised access to another user's screenshots | Ownership check on every read; Firestore rules as defence-in-depth; signed URLs scoped and short-lived; no public Storage paths |
| Privilege escalation via a client-writable role | `role` is server-only in Firestore and authoritative only as an Auth custom claim; the security rules test suite asserts this explicitly |
| Direct calls to the AI service bypassing quotas and auth | Service not publicly routable; OIDC/HMAC service-to-service auth; ingress restricted to the web tier |
| Credential leakage into the client bundle | All secrets under `$lib/server/` (build-time enforced); env validation at startup; no Admin SDK import outside `server/`; a CI check greps the client bundle for known secret patterns |
| XSS via OCR text or user comments rendered in the UI | OCR text and free-text comments are **untrusted input** — escape on render, never inject as HTML; strict CSP with no `unsafe-inline`; sanitise and length-cap feedback comments |
| Prompt/content injection through screenshot text | No LLM is in the decision path (§14.5), which eliminates this class entirely — an underrated benefit of the template-based explanation design |
| CSRF | SameSite=Lax cookies + double-submit CSRF token on state-changing routes |
| Enumeration of analysis IDs | Non-sequential IDs plus an ownership check; never rely on ID unguessability alone |
| Abuse / cost-exhaustion via mass uploads | Per-user and per-IP quotas, anonymous limits, content-hash deduplication, exponential backoff on repeated failures |
| Sensitive data in logs | Never log OCR text, entities, or image bytes; hash IPs; structured logging with an explicit allowlist of loggable fields |
| Dependency vulnerabilities | Automated dependency scanning in CI; pinned versions; regular review |

---

## 19. Suggested Improvements

Split into **essential** (should be treated as in-scope; omitting them materially weakens the result) and **optional** (genuine value, but safe to defer). None changes the core idea.

### 19.1 Essential

**E1 · Hierarchical two-stage classification instead of a flat 8-class model.** (§5.2, A1.) The binary decision the user acts on stays separately tunable, the heterogeneous genuine class stops contaminating category boundaries, and thresholds can be set independently per stage. *Cost:* low — it is a training-script structure choice. *Value:* high accuracy and interpretability gain.

**E2 · Probability calibration.** (§13, §14.4.) The UI displays a confidence number; an uncalibrated tree-ensemble score is not a probability, so displaying one is misleading users about how much to trust the verdict. *Cost:* one extra data split and ~30 lines of training code. *Value:* correctness and honesty; ECE and reliability diagrams are also directly reportable.

**E3 · Group-aware splitting with a real-only test subset.** (§13.3, R10.) Without this, the headline accuracy is very likely inflated and will not survive scrutiny. *Cost:* one field on the sample document plus the right CV splitter. *Value:* the difference between a defensible result and an indefensible one.

**E4 · Chat structure parsing with direction awareness.** (§5.2[5], §1.4 #4.) Distinguishing "they asked for the OTP" from "I sent the OTP" is a large accuracy gain on the OTP and banking categories and is a genuine, cheap novelty. *Cost:* medium (M5-sized). *Value:* accuracy plus a defensible novelty claim plus a separately reportable segmentation result.

**E5 · The ablation study.** (§13.10.) Without it, the multimodal-fusion claim — the project's central contribution — is asserted rather than demonstrated. *Cost:* a handful of extra training runs against configurations that already exist. *Value:* it *is* the evidence.

**E6 · Shared feature registry used by both training and inference.** (§3.3, §11.10.) Prevents training/serving skew, the most common and hardest-to-diagnose production ML failure. *Cost:* one day, if done first. *Value:* eliminates a class of silent, catastrophic bugs.

**E7 · Risk score separated from confidence.** (§14.4.) A 70 %-confidence OTP request is high risk; a 70 %-confidence generic promotional message is not. Conflating them produces bad safety advice, which is a real-world harm. *Cost:* a documented formula in configuration. *Value:* materially better user outcomes.

**E8 · Async-shaped API contract from day one.** (§3.2, §8.2.) Costs nothing now; makes the future scaling migration invisible to clients. *Cost:* near zero. *Value:* avoids a breaking API change later.

**E9 · Ethics, consent, and PII redaction pipeline.** (R13.) Blocking for the dataset contribution and for any real-user deployment. *Cost:* medium, mostly process and lead time. *Value:* legal defensibility and publishability.

**E10 · Evidence-grounded, template-based explanations rather than LLM-generated text.** (§14.5.) Deterministic, reproducible, hallucination-free, zero added latency, and immune to prompt injection from screenshot content. *Cost:* the template library. *Value:* trustworthiness and reproducibility.

**E11 · User-editable OCR text before analysis.** (R1 fallback.) Turns the worst failure mode — a confident verdict built on garbled text — into a recoverable one, and harvests free annotation data. *Cost:* small UI addition. *Value:* large improvement in the worst case.

**E12 · A datasheet and model card.** (§13.1.) Standard practice for dataset and model releases; their absence is a reviewer's first question. *Cost:* documentation only. *Value:* significant research credibility.

### 19.2 Optional

**O1 · Asynchronous URL enrichment** — domain age, Safe Browsing, certificate transparency — run out-of-band after the verdict, updating the record if the signal is decisive. Keeps the request path fast and private while adding a strong signal. *Deferred because* it introduces external dependencies and privacy considerations.

**O2 · Transformer-based multimodal fusion** (e.g. a CLIP-style joint encoder, or LayoutLM over the OCR-plus-layout representation) as an alternative to feature concatenation — explicitly named in the abstract's future work. A strong follow-up paper; a poor v1 choice because it needs far more data and destroys the SHAP-based explainability the project is built on.

**O3 · Progressive Web App with offline capability and a share-target handler** — registering as an Android share target so users can share a screenshot directly from WhatsApp into the app. This is arguably the single highest-value UX improvement available and could be promoted to essential if user adoption is a project goal.

**O4 · Multi-screenshot conversation analysis** — accepting several screenshots of one conversation and analysing them jointly. Scams unfold over turns; single-screenshot analysis sees a slice. Natural v2.

**O5 · Browser extension / desktop clipboard watcher** for the same pipeline on desktop chat clients.

**O6 · Active-learning-driven annotation prioritisation** — AI-21 exists in the design; making it drive the annotation queue ordering would measurably improve label efficiency once volume is high enough to matter.

**O7 · Federated or on-device inference** for privacy-sensitive users — a distilled model running client-side so the screenshot never leaves the device. Research-worthy and directly addresses R13, but a large undertaking.

**O8 · Per-platform specialised models** if the evaluation shows large per-platform variance, rather than one general model.

**O9 · Real-time threat-intelligence feed integration** for the blocklists (currently manual, AD-07), with automatic expiry and source attribution.

**O10 · Public API for third-party integration** — a rate-limited, key-authenticated endpoint enabling other consumer-protection tools to use the classifier. Increases impact and citation surface.

**O11 · Comparative human baseline** — measure how accurately untrained humans classify the same test screenshots. If the system beats the human baseline, that is a far more compelling headline than a raw F1 score, and it costs one afternoon with 20 volunteers.

**O12 · Longitudinal drift study** — re-evaluate on screenshots collected 3–6 months after training to quantify how fast scam language evolves. Cheap, and genuinely novel in this problem space.

---

## Appendix A · Third-Party Dependencies

### Frontend (`apps/web`)
`@sveltejs/kit`, `svelte` (5.x, runes), `vite`, `tailwindcss` (4.x), `bits-ui`/`shadcn-svelte`, `lucide-svelte`, `firebase` (client SDK), `firebase-admin` (server), `zod` or `ajv` (schema validation), `clsx`/`tailwind-merge`, `layerchart` or a lightweight charting library for the contribution chart, `dompurify` (defence-in-depth on rendered untrusted text). Dev: `vitest`, `@testing-library/svelte`, `playwright`, `eslint`, `prettier`, `axe-core`, `@firebase/rules-unit-testing`.

### AI service (`apps/ai-service`)
`fastapi`, `uvicorn[standard]`, `pydantic` (v2), `python-multipart`, `opencv-python-headless`, `pillow`, `numpy`, `scikit-image`, `pytesseract` (+ Tesseract 5 system binary and language data), `easyocr`, optionally `paddleocr`, `spacy` + `en_core_web_sm`, `nltk`, `sentence-transformers`, `torch` (**CPU-only wheels**), `scikit-learn`, `xgboost`, `shap`, `pyzbar` (+ `libzbar0`), `phonenumbers`, `tldextract`, `urlextract`, `confusable-homoglyphs`, `symspellpy`, `ftfy`, `emoji`, `regex`, `langdetect`, `google-cloud-storage`, `joblib`, `structlog`, `prometheus-client`, `httpx`, `tenacity`. Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`, `locust`.

### ML workspace (`ml/`)
`pandas`, `matplotlib`, `seaborn`, `optuna`, `mlflow`, `jupyterlab`, `imbalanced-learn`, `dvc` (dataset versioning), `evidently` (drift), `label-studio` (optional external annotation), `faker` + `playwright` or `pillow`-based rendering for the synthetic screenshot generator.

### Infrastructure
Firebase (Auth, Firestore, Storage, Hosting), Cloud Run or equivalent container host, Docker, GitHub Actions, Sentry or equivalent error tracking.

**System packages required in the AI container:** `tesseract-ocr`, `tesseract-ocr-hin` (and other language packs per A3), `libzbar0`, `libgl1`, `libglib2.0-0`.

---

## Appendix B · Open Questions for Stakeholders

**Resolved 2026-07-26:**

1. ~~**A1** — hierarchical two-label design vs. flat 8-class.~~ → **Confirmed: hierarchical.**
2. ~~**A3** — v1 language scope.~~ → **Confirmed: English only.**
3. ~~**A6/R13** — institutional ethics approval required?~~ → **Confirmed: not required.**
4. ~~**A5/R11** — real-screenshot sources / dataset format.~~ → **Confirmed: raw text/CSV datasets (scam, QR, phishing, email-scam), no real screenshots yet.** The synthetic screenshot-rendering pipeline (§19 O-list) is now the primary data pipeline, not a supplement. Real-screenshot sourcing for the leakage-safe test subset (§18.3 R10) remains genuinely open.

**Still open:**

5. **A7** — Which brands should the closed impersonation set cover? Regional banks, wallets, couriers?
6. **A9** — TypeScript or JavaScript + JSDoc for the web app? *(De facto answered by the current build: JavaScript + JSDoc, no TypeScript migration has been made.)*
7. Is a **public dataset release** intended, or internal use only? This determines how strict the redaction requirements are.
8. Is **anonymous/guest usage** required, or is authentication mandatory for all analyses?
9. What is the team size and availability? The roadmap's parallel tracks assume 2–3 people.
10. Is there a **hard deadline** (submission date)? If so, apply §17.3 rule 5 (cut visual scope and admin polish, never data, training, or evaluation) from the start rather than in the final weeks.
11. **New — infrastructure:** Firebase project (does one exist, or does it need creating?), hosting choice for the SvelteKit app (Vercel/Netlify/Cloudflare/Node), and hosting choice for the Python AI microservice (Cloud Run/Railway/Fly.io). These block connecting any real backend.

---

*End of blueprint. No implementation is authorised by this document; §15 M0 is the first executable milestone.*
