import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ref_factory.rag.store import count_reference_files, index_reference_library


def main() -> int:
    file_count = count_reference_files()
    chunk_count = index_reference_library(verbose=True)
    print(f"[REF-Factory] fichiers references={file_count} | chunks indexes={chunk_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
