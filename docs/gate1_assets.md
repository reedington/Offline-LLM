# Gate 1 Assets: Screenshots and 2-Minute Demo Video

Gate 1 (deadline **2026-08-25**) requires, besides the repo and REPORT.md:

1. Screenshots / short clips of the model running
2. A 2-minute demo video

This document is the production checklist. Honesty rule: every frame shows
the real app doing real inference on this machine — no mockups, no sped-up
generation presented as real-time (if a cut compresses waiting time, say so
in a caption).

## Prepare the demo state

```bash
# 1. Backend (model at models/model.gguf)
cd backend && ../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

# 2. Frontend (or use the FastAPI-served build at :8000 after npm run build)
cd frontend && npm run dev

# 3. Load the sample documents (Upload panel -> "use samples", or upload
#    the files from data/sample_docs/).
```

Demo questions (all verified to behave correctly in the product benchmark):

| Intent | Question | Expected |
|---|---|---|
| Document Q&A | What is the payment period in the supplier agreement? | Grounded answer + evidence quotes |
| Document Q&A | Can customers return opened hygiene products? | "No, unless defective" + evidence |
| Abstention | Who is the CFO of the company? | Exact abstention message |
| Calculator | What is my profit if cost is 7500 and revenue is 10000? | Deterministic answer + Calculation/Formula/Inputs evidence |
| Calculator | An invoice dated 2026-07-01 has net 30 terms. When is payment due? | 2026-07-31 + working shown |

## Screenshot shot list

Save to `docs/assets/` as PNG (committed; keep each under ~1 MB):

1. `01-upload.png` — documents uploaded/indexed, chunk counts visible
2. `02-grounded-answer.png` — a document question with Answer + evidence
   cards showing source document and confidence
3. `03-abstention.png` — the exact abstention message on an unanswerable
   question
4. `04-calculator.png` — a finance question with Calculation / Formula /
   Inputs evidence (cross-disciplinary integration, load-bearing)
5. `05-metrics.png` — the live metrics/status panel (RSS, index state,
   latency)
6. `06-offline-proof.png` — the app answering with Wi-Fi visibly off
   (macOS: menu bar Wi-Fi icon off in frame)
7. `07-ubuntu-gate.png` — terminal showing the Docker 7 GB gate `RESULT:
   PASS` output

## 2-minute video script (timings at 30 fps of talking, not rushed)

- **0:00–0:15 — Problem.** SMEs in low-connectivity, budget-hardware
  settings need document answers and business arithmetic they can trust; no
  cloud, no GPU.
- **0:15–0:30 — Constraints.** Runs fully offline on a 7 GB-RAM CPU-only
  laptop; llama.cpp + GGUF (Qwen2.5-1.5B Q4_K_M); show Wi-Fi turning OFF now
  and stays off for the rest of the demo.
- **0:30–1:00 — Document intelligence.** Upload samples, ask the supplier
  agreement question, show the grounded answer and evidence quotes; ask the
  CFO question, show the honest abstention.
- **1:00–1:30 — Load-bearing finance tools.** Ask the profit and payment-due
  questions; call out that the language model never does arithmetic — the
  deterministic calculator answers with formula and inputs shown.
- **1:30–1:50 — Proof of discipline.** Cut to terminal: 7 GB-capped Ubuntu
  container gate passing (`RESULT: PASS`, peak RSS ~1.3 GB); mention the
  official profiler numbers (~101–107 tok/s, ~1.2 GB model RSS, no
  throttling, measured on the dev machine).
- **1:50–2:00 — Close.** Open-source repo, REPORT.md with measured-only
  numbers, ADTC Corporate/Enterprise track.

Recording tips: capture at 1080p or higher, browser at ~110% zoom, dark UI
already matches the ADTC style; keep the terminal font large for the gate
clip. Record generation in real time at least once — the tokens/sec is a
selling point (~100 tok/s on the dev machine), so let one answer stream
visibly.

## Publishing checklist

- [ ] Screenshots committed under `docs/assets/`
- [ ] Video uploaded (YouTube unlisted or repo release asset) and linked in
      README.md and REPORT.md
- [ ] README top section links the video and one hero screenshot
- [ ] Repo public, latest main pushed, CI-free (tests run locally: document
      the command)
- [ ] REPORT.md current: profiler numbers, model comparison, arm64 gate PASS,
      x86 status
