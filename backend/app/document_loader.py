from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from app.config import MAX_UPLOAD_MB


@dataclass(frozen=True)
class Document:
    filename: str
    text: str
    metadata: dict


def validate_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if path.stat().st_size > max_bytes:
        raise ValueError(f"{path.name} is larger than the {MAX_UPLOAD_MB} MB limit.")


def load_document(path: Path) -> Document:
    validate_file(path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        text = extract_pdf_text(path)
    else:
        raise ValueError(f"Unsupported file type for {path.name}. Upload TXT or PDF files.")

    text = text.strip()
    if not text:
        raise ValueError(f"No extractable text found in {path.name}.")

    return Document(
        filename=path.name,
        text=text,
        metadata={"file_type": suffix.lstrip("."), "path": str(path), "characters": len(text)},
    )


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages).strip()


def load_documents(paths: Iterable[Path]) -> list[Document]:
    documents = [load_document(Path(path)) for path in paths]
    if not documents:
        raise ValueError("No documents were provided.")
    return documents
