from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

from pypdf import PdfReader

from src.config import MAX_UPLOAD_MB


@dataclass(frozen=True)
class Document:
    filename: str
    text: str
    metadata: dict


def _check_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if path.stat().st_size > max_bytes:
        raise ValueError(f"{path.name} is larger than the {MAX_UPLOAD_MB} MB limit.")


def _load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages).strip()


def load_document(path: Path) -> Document:
    _check_file(path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = _load_txt(path)
    elif suffix == ".pdf":
        text = _load_pdf(path)
    else:
        raise ValueError(f"Unsupported document type for {path.name}. Use PDF or TXT.")

    text = text.strip()
    if not text:
        raise ValueError(f"No extractable text found in {path.name}.")

    return Document(
        filename=path.name,
        text=text,
        metadata={"path": str(path), "file_type": suffix.lstrip(".")},
    )


def load_documents_from_paths(paths: Iterable[Path]) -> list[Document]:
    documents = [load_document(Path(path)) for path in paths]
    if not documents:
        raise ValueError("No documents were provided.")
    return documents


def save_uploaded_files(uploaded_files: Iterable[BinaryIO], target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for uploaded_file in uploaded_files:
        filename = Path(getattr(uploaded_file, "name", "upload")).name
        path = target_dir / filename
        data = uploaded_file.read()
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise ValueError(f"{filename} is larger than the {MAX_UPLOAD_MB} MB limit.")
        path.write_bytes(data)
        paths.append(path)
    return paths
