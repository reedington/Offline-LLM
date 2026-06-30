from __future__ import annotations

from app.config import ABSTENTION_MESSAGE

SYSTEM_PROMPT = f"""You are an offline SME business assistant.
Answer only from the provided context.
Do not make up facts.
If the answer is not supported by the context, say exactly:
{ABSTENTION_MESSAGE}
Do not show hidden reasoning or chain-of-thought.
Use this format:

Answer:
...

Evidence:
- Source document:
- Relevant quote:
- Confidence / support level:
"""


def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Context {index}]",
                    f"Source document: {chunk['source_document']}",
                    f"Chunk id: {chunk['chunk_id']}",
                    f"Text: {chunk['text']}",
                ]
            )
        )
    context = "\n\n".join(context_blocks) if context_blocks else "No context provided."
    return f"""{SYSTEM_PROMPT}

Context:
{context}

Question:
{question}

Answer using only the context above.
"""
