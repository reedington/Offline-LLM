# AGENTS.md

You are working on the Offline SME AI Assistant for ADTC 2026.

Current build phase:
v1 English offline RAG assistant only.

Product style:
This is not a Streamlit demo. Build a polished local web app with:
- React + Vite + Tailwind frontend
- FastAPI backend
- dark ADTC-style aesthetic
- warm cream typography
- gold/amber accents
- premium deep-tech feel
- clean Answer / Evidence cards

Hard rules:
- No Streamlit.
- No Gradio.
- No cloud APIs.
- Main answering model must be local GGUF through llama.cpp or llama-cpp-python.
- Do not implement NLLB until the English core is stable.
- Do not implement RAFT/QLoRA fine-tuning in v1.
- Do not implement LightRAG/graph retrieval in v1.
- Do not expose chain-of-thought.
- Always use Answer / Evidence format.
- If documents do not support the answer, say:
  "I do not know based on the provided documents."

Performance rules:
- Keep context length controlled, default 2048.
- Retrieve top-k = 3 chunks by default.
- Keep chunks around 256-512 tokens.
- Cache indexes on disk.
- Avoid loading unnecessary models.
- Avoid memory leaks.
- Keep the app profiler-friendly.

Testing:
Before finishing any coding task, run:

Backend:
cd backend
python -m compileall app
pytest ../tests -q

Frontend:
cd frontend
npm run build

Documentation:
Update README.md and REPORT.md whenever behavior changes.
