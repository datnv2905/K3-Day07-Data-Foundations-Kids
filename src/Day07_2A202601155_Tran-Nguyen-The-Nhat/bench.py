"""Chạy benchmark cá nhân trên corpus chung đã được nhóm chốt."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Cho phép chạy trực tiếp bằng `python3 src/.../bench.py` từ thư mục gốc repo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=False)

from ingest import build_knowledge_base, chunk_document, load_documents

personal = importlib.import_module("src.Day07_2A202601155_Tran-Nguyen-The-Nhat")
RecursiveChunker = personal.RecursiveChunker
LocalEmbedder = personal.LocalEmbedder
_mock_embed = personal._mock_embed


BENCHMARK_QUERIES = [
    {
        "question": "Hạn nộp đơn xin hỗ trợ tài chính cho học kỳ Fall là ngày nào?",
        "filter": {"audience": "student"},
        "gold_doc_id": "vinuni-financial-aid-request",
        "evidence": "July 10th",
    },
    {
        "question": "Ai được vào thư viện, mượn tài liệu hoặc dùng tài nguyên điện tử?",
        "filter": None,
        "gold_doc_id": "vinuni-library-access-services",
        "evidence": "valid VinUni ID",
    },
    {
        "question": "Đăng ký khách đến ở trong ngày và khách ở qua đêm trước bao lâu?",
        "filter": {"audience": "student"},
        "gold_doc_id": "vinuni-residential-life",
        "evidence": "03 working days",
    },
    {
        "question": "Điều gì xảy ra với học bổng khi Academic Year GPA từ 0.0 đến 2.49?",
        "filter": {"audience": "student"},
        "gold_doc_id": "vinuni-scholarship-maintenance",
        "evidence": "Automatic Downgrade",
    },
    {
        "question": "Sinh viên bị cáo buộc gian lận học thuật được bảo đảm quy trình nào?",
        "filter": {"audience": "student"},
        "gold_doc_id": "vinuni-student-academic-integrity",
        "evidence": "due process",
    },
]


def choose_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
    if provider == "local":
        return LocalEmbedder()
    if provider == "openai":
        return personal.OpenAIEmbedder()
    return _mock_embed


def _build_openai_store(corpus_dir: Path, chunker, embedder):
    """Nạp cùng pipeline của ingest, nhưng gửi embedding theo lô để benchmark nhanh."""
    chunk_docs = [
        chunk
        for document in load_documents(corpus_dir)
        for chunk in chunk_document(document, chunker)
    ]
    cache: dict[str, list[float]] = {}
    batch_size = 50
    for start in range(0, len(chunk_docs), batch_size):
        contents = [document.content for document in chunk_docs[start : start + batch_size]]
        response = embedder.client.embeddings.create(model=embedder.model_name, input=contents)
        cache.update(
            {
                content: [float(value) for value in item.embedding]
                for content, item in zip(contents, response.data)
            }
        )

    def cached_embedding(text: str) -> list[float]:
        if text not in cache:
            response = embedder.client.embeddings.create(model=embedder.model_name, input=text)
            cache[text] = [float(value) for value in response.data[0].embedding]
        return cache[text]

    store = personal.EmbeddingStore(collection_name="personal_benchmark", embedding_fn=cached_embedding)
    store.add_documents(chunk_docs)
    return store


def run(corpus_dir: Path) -> int:
    chunker = RecursiveChunker(chunk_size=1000)
    embedder = choose_embedder()
    if os.getenv("EMBEDDING_PROVIDER", "mock").lower() == "openai":
        store = _build_openai_store(corpus_dir, chunker, embedder)
    else:
        store = build_knowledge_base(corpus_dir, embedding_fn=embedder, chunker=chunker)
    print(f"Strategy: RecursiveChunker(chunk_size=1000); chunks: {store.get_collection_size()}")
    for index, item in enumerate(BENCHMARK_QUERIES, start=1):
        question = item["question"]
        metadata_filter = item["filter"]
        results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        found_evidence = any(item["evidence"].lower() in result["content"].lower() for result in results)
        print(f"\n{index}. {question} | filter={metadata_filter}")
        print(f"   gold={item['gold_doc_id']} | evidence={item['evidence']} | top-3 evidence={found_evidence}")
        for rank, result in enumerate(results, start=1):
            preview = result["content"].replace("\n", " ")[:180]
            print(f"  {rank}. {result['score']:.4f} {result['metadata'].get('doc_id')}: {preview}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_dir", type=Path, help="Ví dụ: data/k3_university")
    raise SystemExit(run(parser.parse_args().corpus_dir))
