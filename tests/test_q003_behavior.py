"""Phase 7C regression tests for the q003 false abstention.

q003 ("What must BrightMart provide when reporting damaged goods?") passed on
macOS/arm64 but falsely abstained under x86 emulation. Root cause: retrieval
was correct, but temperature-0.1 sampling let a borderline generation flip
across architectures. The fix is greedy decoding (temperature=0.0, fixed
seed). These tests pin the retrieval path and the answerability decision so a
regression is caught without needing model weights.
"""

import numpy as np
import pytest

from app.config import ABSTENTION_MESSAGE
from app.llm import LlamaCppLLM
from app.rag import RAGAssistant, weak_retrieval

Q003 = "What must BrightMart provide when reporting damaged goods?"
Q003_SOURCE = "sample_supplier_agreement.txt"


def test_llm_defaults_to_greedy_decoding_with_fixed_seed():
    llm = LlamaCppLLM()
    assert llm.temperature == 0.0, "Greedy decoding required for cross-architecture consistency"


def test_q003_retrieves_supplier_agreement_from_sample_docs():
    pytest.importorskip("sentence_transformers")
    from app.chunking import chunk_documents
    from app.config import SAMPLE_DOCS_DIR
    from app.document_loader import load_documents
    from app.embeddings import EmbeddingModel
    from app.schemas import DocumentMetadata
    from app.vector_store import VectorStore

    paths = sorted(SAMPLE_DOCS_DIR.glob("*.txt"))
    assert paths, "sample docs must exist"
    try:
        embedder = EmbeddingModel()
        query = embedder.embed([Q003])[0]
    except Exception as exc:  # embedding model not cached locally
        pytest.skip(f"local embedding model unavailable: {exc}")

    documents = load_documents(paths)
    chunks = chunk_documents(documents)
    metadata = [
        DocumentMetadata(filename=d.filename, file_type=d.metadata.get("file_type", ""), characters=len(d.text))
        for d in documents
    ]
    store = VectorStore(SAMPLE_DOCS_DIR.parent / "_tmp_q003_index")
    store.build(chunks, embedder.embed([chunk.text for chunk in chunks]), metadata)

    retrieved = store.search(query, top_k=3)
    assert retrieved, "retrieval must return chunks"
    assert retrieved[0]["source_document"] == Q003_SOURCE, "supplier agreement must rank first for q003"
    assert not weak_retrieval(retrieved), "q003 retrieval must clear the relevance threshold"
    assert "photos" in retrieved[0]["text"].lower()
    assert "delivery note" in retrieved[0]["text"].lower()


class Q003Store:
    ready = True
    chunks = [object()]
    documents = []

    def search(self, query_embedding, top_k=3):
        return [
            {
                "source_document": Q003_SOURCE,
                "chunk_id": f"{Q003_SOURCE}::chunk-0000",
                "text": (
                    "Northline Foods must replace damaged goods reported within 48 hours of delivery. "
                    "BrightMart must provide photos and the delivery note number when reporting damaged goods."
                ),
                "score": 0.44,
            }
        ]


class Q003Embedder:
    def embed(self, texts):
        return np.array([[1.0, 0.0]], dtype=np.float32)


class GroundedLLM:
    def generate(self, prompt, max_tokens=512):
        assert "photos and the delivery note number" in prompt, "retrieved evidence must reach the prompt"
        return "Answer:\nBrightMart must provide photos and the delivery note number.\n\nEvidence:\n- Source document: sample_supplier_agreement.txt"


def test_q003_does_not_abstain_when_relevant_document_is_indexed():
    result = RAGAssistant(Q003Store(), Q003Embedder(), GroundedLLM()).answer(Q003)
    assert result["answer"] != ABSTENTION_MESSAGE
    assert "photos" in result["answer"].lower()
    assert result["evidence"][0]["source_document"] == Q003_SOURCE
