# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Nguyên Phong
**MSSV:** 2A202601077
**Nhóm:** Kids
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai vector embedding trỏ gần như cùng một "hướng" trong không gian nhiều chiều, bất kể độ dài (magnitude) của chúng — nói cách khác, hai đoạn văn bản mang ý nghĩa/chủ đề gần giống nhau, dù cách diễn đạt (từ ngữ, độ dài câu) có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối các ngày trong tuần."
- Câu B: "Giờ hoạt động của thư viện là 7h–22h, tất cả các ngày."
- Tại sao tương đồng: Cùng nói về giờ mở cửa thư viện, chỉ khác cách diễn đạt và định dạng giờ — mô hình embedding nắm được ý nghĩa chung nên vector của hai câu gần như cùng hướng.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối."
- Câu B: "Học phí học kỳ này tăng 5% so với năm trước."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (dịch vụ thư viện vs. học phí), không chia sẻ ngữ nghĩa nên vector của chúng gần như vuông góc/ngẫu nhiên với nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chỉ so sánh *hướng* của vector (tức ý nghĩa), bỏ qua độ dài của vector — trong khi độ dài embedding thường bị ảnh hưởng bởi độ dài văn bản hoặc tần suất từ, không phản ánh ngữ nghĩa. Khoảng cách Euclid lại nhạy với độ lớn này, nên hai câu cùng ý nghĩa nhưng độ dài khác nhau có thể bị đánh giá "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Trình bày phép tính: `số_chunk = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> Đáp án: **23 chunks** — đã kiểm chứng bằng cách chạy trực tiếp `FixedSizeChunker(chunk_size=500, overlap=50).chunk(text)` trên chuỗi 10,000 ký tự: kết quả thực tế cũng ra đúng 23 chunk.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> `ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` (kiểm chứng lại bằng code cũng ra 25) — tăng từ 23 lên 25 chunk. Overlap lớn hơn làm bước trượt (`step = chunk_size − overlap`) nhỏ lại nên có nhiều chunk hơn, nhưng đổi lại giảm rủi ro một câu/ý quan trọng bị cắt đúng ngay ranh giới chunk — thông tin ở gần biên được lặp lại ở chunk kế tiếp, giúp truy xuất (retrieval) ít bỏ sót ngữ cảnh hơn, đánh đổi bằng việc lưu trữ dư thừa hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng `re.split` với pattern `(\. |! |\? |\.\n)` (có nhóm capture) để giữ lại dấu câu làm điểm phân tách mà không mất chính dấu câu đó, sau đó gom các "buffer" lại thành câu hoàn chỉnh mỗi khi gặp một trong 4 delimiter. Các câu được nhóm theo `max_sentences_per_chunk`. Edge case xử lý: văn bản rỗng trả về `[]`; câu cuối không có delimiter kết thúc (phần dư trong buffer) vẫn được thêm vào nếu còn nội dung sau khi `.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> `_split` đệ quy thử từng separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → `` → `""`): tách văn bản theo separator hiện tại, rồi gộp các mảnh nhỏ lại thành buffer cho tới sát `chunk_size`; nếu một mảnh đơn lẻ vẫn lớn hơn `chunk_size`, đệ quy tiếp với danh sách separator còn lại (bỏ separator vừa dùng). Base case: `len(current_text) <= chunk_size` → trả về `[current_text]`; hoặc hết separator (`remaining_separators` rỗng) → cắt cứng theo `chunk_size` (hard slice) để đảm bảo luôn dừng đệ quy.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> `add_documents` chuẩn hoá mỗi `Document` thành 1 record (`id`, `content`, `embedding`, `metadata` — trong đó `metadata["doc_id"]` mặc định lấy từ `doc.id` nếu chưa có) rồi append vào `self._store` (in-memory) hoặc gọi `collection.add(...)` nếu ChromaDB khả dụng. `search` nhúng câu truy vấn bằng `embedding_fn`, tính **tích vô hướng (dot product)** giữa vector truy vấn và từng embedding đã lưu (`_dot`), sắp xếp giảm dần theo score rồi cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Lọc theo metadata **trước**: chỉ giữ các record mà mọi cặp `key: value` trong `metadata_filter` khớp với `record["metadata"]`, sau đó mới chạy similarity search (`_search_records`) trên tập đã lọc — cách này tránh phải tính điểm tương tự cho các chunk chắc chắn bị loại. `delete_document` xoá bằng cách lọc lại `self._store`, giữ lại mọi record có `metadata["doc_id"] != doc_id`; trả về `True` nếu kích thước store giảm sau khi xoá, `False` nếu không có gì bị xoá (doc_id không tồn tại).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `__init__` lưu tham chiếu tới `store` và `llm_fn`. `answer` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan, nối nội dung (`content`) của chúng bằng `"\n\n"` thành một khối `context`, rồi ghép vào một prompt có cấu trúc rõ ràng (`Context: ... / Question: ... / Answer:` kèm chỉ dẫn chỉ trả lời dựa trên context) trước khi gọi `llm_fn(prompt)` và trả về chuỗi kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ py -3.11 -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Lưu ý về embedder dùng ở đây:** chạy bằng `_mock_embed` (Trình nhúng giả lập), **không phải** trình nhúng đa ngữ cục bộ (`LocalEmbedder`). README nêu rõ mock sinh vector xác định theo chuỗi nhưng **gần như ngẫu nhiên về mặt ngữ nghĩa** — chỉ dùng để chạy nhanh/unit test, không phản ánh ý nghĩa thật. Kết quả bên dưới vì vậy dùng để minh hoạ đúng đặc điểm đó của mock (xem phần "bất ngờ nhất"), không dùng để kết luận chiến lược retrieval nào tốt hơn.


| Cặp | Câu A                                                     | Câu B                                                                                                   | Dự đoán | Điểm thực tế | Đúng?                                                                       |
| ------ | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ------------ | ------------------ | ------------------------------------------------------------------------------- |
| 1    | "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối." | "Giờ hoạt động của thư viện là 7h–22h mỗi ngày." (paraphrase cùng ý)                        | cao        | 0.2183           | Sai — mock không nhận ra đây là paraphrase                              |
| 2    | "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối." | "Học phí học kỳ này tăng 5% so với năm trước." (khác chủ đề)                               | thấp      | -0.2405          | Đúng (tình cờ) — vẫn là điểm ngẫu nhiên, không do hiểu chủ đề |
| 3    | "Sinh viên đăng ký học phần qua cổng học vụ."     | "Đăng ký môn học được thực hiện trên hệ thống học vụ trực tuyến." (paraphrase cùng ý) | cao        | 0.0177           | Sai — gần 0 dù cùng ý nghĩa                                             |
| 4    | "Ký túc xá ưu tiên sinh viên năm nhất."            | "Học bổng dành cho sinh viên có hoàn cảnh khó khăn." (khác chủ đề)                          | thấp      | 0.0405           | Gần đúng — điểm thấp/gần 0                                            |
| 5    | "Thư viện mở cửa từ 7 giờ sáng đến 10 giờ tối." | (chính nó, lặp lại y hệt)                                                                           | cao        | 1.0000           | Đúng — hai chuỗi giống hệt luôn cho cosine similarity = 1              |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là Cặp 3: hai câu diễn đạt lại đúng một ý ("đăng ký học phần qua cổng học vụ" vs "đăng ký môn học trên hệ thống học vụ trực tuyến") nhưng điểm tương tự gần 0, không hề "cao" như dự đoán. Điều này cho thấy `MockEmbedder` chỉ băm (hash) chuỗi ký tự thành vector giả-ngẫu nhiên có seed phụ thuộc *chính xác từng ký tự* của chuỗi đầu vào — nó hoàn toàn không mã hoá ngữ nghĩa, nên hai câu paraphrase (khác chữ, cùng nghĩa) và hai câu khác chủ đề đều cho điểm ngẫu nhiên như nhau; chỉ có chuỗi *giống hệt tuyệt đối* (Cặp 5) mới chắc chắn ra 1.0. Đây đúng là điều README cảnh báo: mock hợp để kiểm thử (deterministic, không cần model) nhưng vô nghĩa để đánh giá chất lượng ngữ nghĩa — muốn dự đoán/so sánh có ý nghĩa thật sự cần `EMBEDDING_PROVIDER=local` (hoặc `openai`).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **⚠️ Chưa hoàn thành — phụ thuộc vào Giai đoạn 2 (Nhóm).** Mục này cần: (1) bộ 5 câu hỏi đánh giá + gold answer đã thống nhất trong nhóm (`REPORT_NHOM.md` — Phần 3), và (2) corpus thật của nhóm trong `data/`. Hiện tại `data/k3_university/` mới chỉ chứa **dữ liệu khởi động dạng template** (`source_url: https://example.edu/...` là placeholder, chưa phải nguồn thật — xem ghi chú đầu mỗi file `.md`), và `REPORT_NHOM.md` Phần 3 vẫn còn để trống. Bảng dưới sẽ được điền lại ngay khi nhóm chốt xong Bài tập 3.0 (thu thập tài liệu thật) và 3.2 (5 câu hỏi đánh giá).

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).


| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| --- | ------------------- | -------------------------------------------- | -------------- | ----------------------------------- | --------------------------------------- |
| 1 |                   |                                            |              |                                   |                                       |
| 2 |                   |                                            |              |                                   |                                       |
| 3 |                   |                                            |              |                                   |                                       |
| 4 |                   |                                            |              |                                   |                                       |
| 5 |                   |                                            |              |                                   |                                       |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Viết 2-3 câu (sau buổi demo nhóm):*

---

## Tự Đánh Giá (Phần Cá Nhân)


| Tiêu chí                                           | Điểm tự đánh giá                                                                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Khởi động (Warm-up)                               | 5 / 5                                                                                                    |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                                                                                                  |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30 (42/42 tests pass)                                                                               |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                                                                                                    |
| Kết quả truy xuất của tôi (Competition Results) | 0 / 10 —**chưa làm được**, chờ Giai đoạn 2 (nhóm) chốt corpus thật + 5 câu hỏi đánh giá |
| **Tổng phần cá nhân (hiện tại)**               | **50 / 60**, sẽ đạt tối đa sau khi hoàn thành Phần 5                                             |
