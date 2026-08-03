"""Chạy benchmark cá nhân trên corpus chung đã được nhóm chốt."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

# Cho phép chạy trực tiếp bằng `python3 src/.../bench.py` từ thư mục gốc repo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import build_knowledge_base

personal = importlib.import_module("src.Day07_2A202601155_Tran-Nguyen-The-Nhat")
RecursiveChunker = personal.RecursiveChunker
LocalEmbedder = personal.LocalEmbedder
_mock_embed = personal._mock_embed


BENCHMARK_QUERIES = [
    # Thay bằng đúng 5 query + gold answer cố định của nhóm trước khi benchmark chính thức.
]


def choose_embedder():
    if os.getenv("EMBEDDING_PROVIDER", "mock").lower() == "local":
        return LocalEmbedder()
    return _mock_embed


def run(corpus_dir: Path) -> int:
    if len(BENCHMARK_QUERIES) != 5:
        print("Cần chốt đúng 5 benchmark query trong BENCHMARK_QUERIES trước khi chạy.")
        return 2
    chunker = RecursiveChunker(chunk_size=400)
    store = build_knowledge_base(corpus_dir, embedding_fn=choose_embedder(), chunker=chunker)
    print(f"Strategy: RecursiveChunker(chunk_size=400); chunks: {store.get_collection_size()}")
    for index, item in enumerate(BENCHMARK_QUERIES, start=1):
        question, metadata_filter = item
        results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        print(f"\n{index}. {question} | filter={metadata_filter}")
        for rank, result in enumerate(results, start=1):
            preview = result["content"].replace("\n", " ")[:180]
            print(f"  {rank}. {result['score']:.4f} {result['metadata'].get('doc_id')}: {preview}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_dir", type=Path, help="Ví dụ: data/k3_university")
    raise SystemExit(run(parser.parse_args().corpus_dir))
