from __future__ import annotations

from pathlib import Path

from app.config import LLM_CTX, LLM_MAX_TOKENS, LLM_THREADS, MODEL_PATH
from app.prompts import SYSTEM_PROMPT


class ModelNotFoundError(FileNotFoundError):
    pass


class LlamaCppLLM:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        n_ctx: int = LLM_CTX,
        n_threads: int = LLM_THREADS,
        # Greedy decoding: temperature 0.1 sampling let borderline generations
        # flip across architectures (q003 falsely abstained under x86
        # emulation while passing on arm64/macOS). Grounding and abstention
        # come from the prompt and retrieval threshold, not from sampling.
        temperature: float = 0.0,
    ):
        self.model_path = Path(model_path)
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.temperature = temperature
        self._llm = None

    @property
    def loaded(self) -> bool:
        return self._llm is not None

    def _load(self):
        if self._llm is not None:
            return self._llm
        if not self.model_path.exists():
            raise ModelNotFoundError(
                f"GGUF model not found at {self.model_path}. "
                "Place a small quantized model at models/model.gguf or set MODEL_PATH."
            )
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("llama-cpp-python is required for local GGUF inference.") from exc

        self._llm = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            seed=42,
            verbose=False,
        )
        return self._llm

    def generate(self, prompt: str, max_tokens: int = LLM_MAX_TOKENS) -> str:
        # Instruct models are prompted through their chat template: raw text
        # completion is out-of-distribution for them and left q003-style
        # borderline questions flipping between answer and abstention across
        # runs/architectures. Prompts built by build_rag_prompt embed the
        # system prompt, so it is split back out into the system role here.
        llm = self._load()
        if prompt.startswith(SYSTEM_PROMPT):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt[len(SYSTEM_PROMPT):].strip()},
            ]
        else:
            messages = [{"role": "user", "content": prompt}]
        try:
            output = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            return output["choices"][0]["message"]["content"].strip()
        except Exception:
            # GGUF without a usable chat template: fall back to raw completion.
            output = llm(
                prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                stop=["\n\nQuestion:", "\n\nContext:"],
            )
            return output["choices"][0]["text"].strip()
