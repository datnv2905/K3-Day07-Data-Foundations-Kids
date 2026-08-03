"""RAG agent nhỏ: retrieve context rồi gọi LLM được inject."""

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh liên quan trong cơ sở tri thức."

        context = "\n\n".join(
            f"[Nguồn {index}: {result['metadata'].get('doc_id', result['id'])}]\n{result['content']}"
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức. "
            "Chỉ trả lời bằng thông tin có trong ngữ cảnh. "
            "Nếu ngữ cảnh không đủ, hãy nói rằng bạn không tìm thấy đủ thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI:\n{question}\n\nTRẢ LỜI:"
        )
        return self.llm_fn(prompt)
