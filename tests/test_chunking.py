from src.chunking import chunk_text


def test_chunk_text_keeps_overlap_and_source():
    text = " ".join(f"word{i}" for i in range(20))
    chunks = chunk_text(text, "doc.txt", chunk_size=8, overlap=2)

    assert len(chunks) == 3
    assert chunks[0].source_document == "doc.txt"
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert chunks[0].chunk_id == "doc.txt::chunk-0000"


def test_chunk_text_rejects_invalid_overlap():
    try:
        chunk_text("hello world", "doc.txt", chunk_size=5, overlap=5)
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
