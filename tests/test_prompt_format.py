from src.config import ABSTENTION_MESSAGE
from src.prompts import SYSTEM_INSTRUCTIONS, build_rag_prompt


def test_prompt_contains_required_format_and_abstention():
    assert "Answer:" in SYSTEM_INSTRUCTIONS
    assert "Evidence:" in SYSTEM_INSTRUCTIONS
    assert ABSTENTION_MESSAGE in SYSTEM_INSTRUCTIONS
    assert "chain-of-thought" in SYSTEM_INSTRUCTIONS


def test_build_rag_prompt_includes_sources():
    prompt = build_rag_prompt(
        "What are payment terms?",
        [
            {
                "source_document": "supplier.txt",
                "chunk_id": "supplier.txt::chunk-0000",
                "text": "Payment terms are net 30 days.",
            }
        ],
    )

    assert "supplier.txt" in prompt
    assert "Payment terms are net 30 days." in prompt
    assert "What are payment terms?" in prompt
