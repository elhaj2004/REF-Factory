import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ref_factory.config import CHROMA_DIR, REFERENCE_LIBRARY_DIR, ensure_runtime_dirs
from ref_factory.document_parser import SUPPORTED_TEXT_EXTENSIONS, extract_text_from_file, summarize_text
from ref_factory.llm.client import get_embeddings

ensure_runtime_dirs()

_STORE: Optional[Chroma] = None
_STORE_KEY: Optional[str] = None


@dataclass(frozen=True)
class LibraryConfig:
    documents_dir: Path
    persist_dir: Path
    collection_name: str
    signature: str

    @property
    def index_state_path(self) -> Path:
        return self.persist_dir / "index_state.json"

    @property
    def cache_key(self) -> str:
        return f"{self.collection_name}:{self.signature}"


class NoOpEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.0]


def count_reference_files() -> int:
    if not REFERENCE_LIBRARY_DIR.exists():
        return 0
    return sum(
        1
        for path in REFERENCE_LIBRARY_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS
    )


def index_reference_library(verbose: bool = True) -> int:
    config = _build_config()
    documents = _load_reference_documents(config.documents_dir)

    global _STORE, _STORE_KEY
    _STORE = None
    _STORE_KEY = None

    if config.persist_dir.exists():
        shutil.rmtree(config.persist_dir)
    config.persist_dir.mkdir(parents=True, exist_ok=True)

    if not documents:
        store = _build_empty_store(config)
        _persist_store(store)
        _write_index_state(config, document_count=0, chunk_count=0)
        _STORE = store
        _STORE_KEY = config.cache_key
        if verbose:
            print(f"[REF-RAG] Aucun document a indexer dans {config.documents_dir}")
        return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(documents)

    store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(config.persist_dir),
        collection_name=config.collection_name,
    )
    _persist_store(store)
    _write_index_state(config, document_count=len(documents), chunk_count=len(chunks))

    _STORE = store
    _STORE_KEY = config.cache_key

    if verbose:
        print(
            f"[REF-RAG] source={config.documents_dir} | fichiers={len(documents)} | chunks={len(chunks)}"
        )
    return len(chunks)


def search_reference_examples(query: str, k: int = 4) -> list[dict[str, Any]]:
    try:
        docs = _get_store().similarity_search(query or "fiche reference cyber", k=k)
    except Exception:
        docs = []

    results: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for doc in docs:
        source = doc.metadata.get("source", "")
        if source in seen_sources:
            continue
        seen_sources.add(source)
        results.append(
            {
                "source": source,
                "filename": doc.metadata.get("filename", Path(source).name if source else "document"),
                "extension": doc.metadata.get("extension", ""),
                "excerpt": summarize_text(doc.page_content, max_chars=260),
            }
        )
    return results


def _get_store() -> Chroma:
    global _STORE, _STORE_KEY
    config = _build_config()
    if _STORE is not None and _STORE_KEY == config.cache_key:
        return _STORE

    if _should_reindex(config):
        index_reference_library(verbose=False)
        if _STORE is not None and _STORE_KEY == config.cache_key:
            return _STORE

    config.persist_dir.mkdir(parents=True, exist_ok=True)
    index_state = _load_json(config.index_state_path)
    embeddings = NoOpEmbeddings() if index_state.get("document_count", 0) == 0 else get_embeddings()
    _STORE = Chroma(
        persist_directory=str(config.persist_dir),
        embedding_function=embeddings,
        collection_name=config.collection_name,
    )
    _STORE_KEY = config.cache_key
    return _STORE


def _build_config() -> LibraryConfig:
    documents_dir = REFERENCE_LIBRARY_DIR
    source_hash = hashlib.sha1(str(documents_dir.resolve()).encode("utf-8")).hexdigest()[:12]
    return LibraryConfig(
        documents_dir=documents_dir,
        persist_dir=CHROMA_DIR / f"reference_library_{source_hash}",
        collection_name=f"ref_factory_{source_hash}",
        signature=_compute_directory_signature(documents_dir),
    )


def _load_reference_documents(documents_dir: Path) -> list[Document]:
    if not documents_dir.exists():
        return []

    documents: list[Document] = []
    for file_path in sorted(documents_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
            continue
        text = extract_text_from_file(file_path)
        if not text.strip():
            continue
        relative_path = file_path.relative_to(documents_dir).as_posix()
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(file_path),
                    "relative_path": relative_path,
                    "filename": file_path.name,
                    "extension": file_path.suffix.lower(),
                },
            )
        )
    return documents


def _build_empty_store(config: LibraryConfig) -> Chroma:
    return Chroma(
        persist_directory=str(config.persist_dir),
        embedding_function=NoOpEmbeddings(),
        collection_name=config.collection_name,
    )


def _persist_store(store: Chroma) -> None:
    persist = getattr(store, "persist", None)
    if callable(persist):
        persist()


def _compute_directory_signature(directory: Path) -> str:
    digest = hashlib.sha256()
    if not directory.exists():
        digest.update(b"missing")
        return digest.hexdigest()

    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
            continue
        stats = file_path.stat()
        digest.update(file_path.relative_to(directory).as_posix().encode("utf-8"))
        digest.update(str(stats.st_size).encode("utf-8"))
        digest.update(str(stats.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


def _should_reindex(config: LibraryConfig) -> bool:
    if not config.persist_dir.exists():
        return True
    index_state = _load_json(config.index_state_path)
    return index_state.get("signature") != config.signature


def _write_index_state(config: LibraryConfig, document_count: int, chunk_count: int) -> None:
    payload = {
        "collection_name": config.collection_name,
        "signature": config.signature,
        "document_count": document_count,
        "chunk_count": chunk_count,
    }
    config.index_state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _load_json(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
