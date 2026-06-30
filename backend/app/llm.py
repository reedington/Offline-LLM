from __future__ import annotations

from pathlib import Path

from app.config import LLM_CTX, LLM_MAX_TOKENS, LLM_THREADS, MODEL_PATH


class ModelNotFoundError(FileNotFoundError):
    pass


class LlamaCppLLM:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        n_ctx: int = LLM_CTX,
        n_threads: int = LLM_THREADS,
        temperature: float = 0.1,
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
            verbose=False,
        )
        return self._llm

    def generate(self, prompt: str, max_tokens: int = LLM_MAX_TOKENS) -> str:
        llm = self._load()
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
            stop=["\n\nQuestion:", "\n\nContext:"],
        )
        return output["choices"][0]["text"].strip()
