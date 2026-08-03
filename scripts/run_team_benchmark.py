from __future__ import annotations

import re

from ingest import build_knowledge_base
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder


DATA_DIR = "data/k3_university"

QUERIES = [
    {
        "query": "Sinh viên bậc cử nhân được mượn tối đa bao nhiêu tài liệu thư viện, thời hạn bao lâu và được gia hạn mấy lần?",
        "doc_id": "vinuni-library-access-services",
        "markers": ["Undergraduate students may borrow 3 items for 2 weeks and renew them 1 time"],
        "filter": {"audience": "student", "category": "library-services"},
    },
    {
        "query": "Mức CGPA tối thiểu để duy trì học bổng Full hoặc 100% là bao nhiêu?",
        "doc_id": "vinuni-scholarship-maintenance",
        "markers": ["cumulative GPA of 3.2 or higher"],
    },
    {
        "query": "Sinh viên phải khiếu nại quyết định hỗ trợ tài chính trong bao lâu và khi nào nhận quyết định cuối?",
        "doc_id": "vinuni-financial-aid-request",
        "markers": ["within five working days", "within ten working days"],
    },
    {
        "query": "Hạn thêm và bỏ học phần trong học kỳ chính là ngày làm việc thứ bao nhiêu?",
        "doc_id": "vinuni-undergraduate-academic-regulations",
        "markers": ["10th business day", "15th business day"],
    },
    {
        "query": "Sinh viên nội trú được tiếp tối đa bao nhiêu khách và phải đăng ký trước bao lâu?",
        "doc_id": "vinuni-residential-life",
        "markers": ["no more than three guests", "03 working days", "05 working days"],
    },
]


class HeadingSectionChunker:
    """Group paragraphs under short numbered headings while respecting a size limit."""

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        chunks: list[str] = []
        heading = ""
        current: list[str] = []

        for paragraph in paragraphs:
            first_line = paragraph.splitlines()[0].strip()
            is_heading = len(paragraph) <= 120 and bool(
                re.match(r"^(?:\d+(?:\.\d+)*\.?|Article\s+\d+\.?|Appendix\s+\w+)\s+", first_line)
            )
            if is_heading:
                heading = paragraph
                continue

            prefix = f"{heading}\n\n" if heading else ""
            candidate = "\n\n".join([*current, paragraph])
            if current and len(prefix) + len(candidate) > self.chunk_size:
                chunks.append(prefix + "\n\n".join(current))
                current = [paragraph]
            else:
                current.append(paragraph)

        if current:
            prefix = f"{heading}\n\n" if heading else ""
            chunks.append(prefix + "\n\n".join(current))
        return chunks


STRATEGIES = [
    ("Phong", "FixedSize 500/50", FixedSizeChunker(chunk_size=500, overlap=50)),
    ("Lê Hồng Đức", "FixedSize 300/50", FixedSizeChunker(chunk_size=300, overlap=50)),
    ("Nguyễn Kim Trung Đức", "Sentence 3 câu", SentenceChunker(max_sentences_per_chunk=3)),
    ("Toàn", "Recursive 500", RecursiveChunker(chunk_size=500)),
    ("Nguyễn Văn Đạt", "Sentence 1 câu", SentenceChunker(max_sentences_per_chunk=1)),
    ("Trần Nguyễn Thế Nhật", "Heading/section 500", HeadingSectionChunker(chunk_size=500)),
]


def evaluate(results: list[dict], expected_doc_id: str, markers: list[str]) -> tuple[int, str]:
    joined = "\n".join(result["content"] for result in results)
    found_markers = sum(marker.casefold() in joined.casefold() for marker in markers)
    has_expected_doc = any(result["metadata"].get("doc_id") == expected_doc_id for result in results)
    if found_markers == len(markers):
        return 2, "đủ bằng chứng"
    if has_expected_doc or found_markers:
        return 1, f"thiếu bằng chứng ({found_markers}/{len(markers)})"
    return 0, "không có tài liệu đúng"


def main() -> int:
    embedder = LocalEmbedder()
    print(f"MODEL\t{LOCAL_EMBEDDING_MODEL}")
    for strategy_index, (member, strategy_name, chunker) in enumerate(STRATEGIES, start=1):
        store = build_knowledge_base(
            DATA_DIR,
            embedding_fn=embedder,
            chunker=chunker,
            collection_name=f"team_benchmark_{strategy_index}",
        )
        total = 0
        print(f"\nMEMBER\t{member}\t{strategy_name}\tchunks={store.get_collection_size()}")
        for query_index, benchmark in enumerate(QUERIES, start=1):
            if benchmark.get("filter"):
                results = store.search_with_filter(
                    benchmark["query"], top_k=3, metadata_filter=benchmark["filter"]
                )
            else:
                results = store.search(benchmark["query"], top_k=3)
            points, note = evaluate(results, benchmark["doc_id"], benchmark["markers"])
            total += points
            top = ", ".join(
                f"{result['metadata'].get('doc_id')}#{result['metadata'].get('chunk_index')}:{result['score']:.3f}"
                for result in results
            )
            print(f"Q{query_index}\t{points}/2\t{note}\t{top}")
        print(f"TOTAL\t{total}/10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())