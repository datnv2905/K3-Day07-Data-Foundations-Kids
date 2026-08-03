# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Toan  
**Nhóm:** [Cập nhật tên nhóm]  
**Ngày:** 2026-08-03

> Nộp 1 bản / sinh viên. Phần nhóm như lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá và demo sẽ nộp chung trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất cá nhân (10).

---

## 1. Khởi động (Warm-up) - Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) - Bài tập 1.1

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector. Với văn bản, điều này thường cho thấy hai đoạn có chủ đề hoặc ý nghĩa gần nhau, dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Sinh viên đăng ký học phần trên cổng học vụ.
- Câu B: Người học chọn lớp học phần trong hệ thống đăng ký môn học.
- Tại sao tương đồng: Hai câu đều nói về việc sinh viên chọn/đăng ký học phần trên hệ thống học vụ.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Sinh viên đăng ký học phần trên cổng học vụ.
- Câu B: Thư viện yêu cầu người dùng mang thẻ định danh khi mượn tài liệu.
- Tại sao khác: Hai câu thuộc hai chủ đề khác nhau, một câu nói về đăng ký học phần, câu còn lại nói về dịch vụ thư viện.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine similarity tập trung vào hướng của vector, nên phù hợp để so sánh ý nghĩa văn bản hơn là độ lớn tuyệt đối của vector. Với embedding văn bản, hai câu có cùng ý nghĩa có thể có độ dài hoặc cường độ vector khác nhau, nhưng hướng vector vẫn gần nhau.

### Bài toán tính toán Chunking - Bài tập 1.2

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

Công thức:

```text
số chunk = ceil((độ dài tài liệu - overlap) / (chunk_size - overlap))
         = ceil((10000 - 50) / (500 - 50))
         = ceil(9950 / 450)
         = ceil(22.11)
         = 23 chunks
```

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

```text
số chunk = ceil((10000 - 100) / (500 - 100))
         = ceil(9900 / 400)
         = ceil(24.75)
         = 25 chunks
```

Khi overlap tăng từ 50 lên 100, số chunk tăng từ 23 lên 25 vì bước nhảy giữa hai chunk nhỏ hơn. Overlap nhiều hơn giúp giữ ngữ cảnh giữa các chunk, giảm rủi ro cắt mất ý quan trọng ở ranh giới chunk, nhưng đổi lại làm tăng số lượng chunk cần lưu và tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) - Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` - hướng tiếp cận:**

Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách văn bản tại ranh giới câu sau dấu `.`, `!`, hoặc `?`, sau đó loại bỏ khoảng trắng thừa. Các câu được gom lại theo `max_sentences_per_chunk`, giúp mỗi chunk giữ được câu hoàn chỉnh thay vì cắt ngang giữa câu. Trường hợp văn bản rỗng trả về danh sách rỗng, còn văn bản không tách được thành câu thì trả về phần nội dung đã strip.

**`RecursiveChunker.chunk` / `_split` - hướng tiếp cận:**

Tôi triển khai chia đệ quy theo thứ tự separator ưu tiên: đoạn văn, dòng, câu, từ, rồi cuối cùng là cắt theo ký tự nếu không còn separator phù hợp. Base case là khi đoạn hiện tại rỗng hoặc đã ngắn hơn `chunk_size`, khi đó trả về ngay. Nếu một đoạn vẫn quá dài sau khi tách bằng separator hiện tại, hàm tiếp tục gọi `_split` với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search` - hướng tiếp cận:**

Mỗi `Document` được chuẩn hóa thành một record gồm `id`, `content`, `metadata` và `embedding`. Khi thêm tài liệu, store gọi `embedding_fn` để tạo vector rồi lưu vào danh sách trong bộ nhớ. Khi tìm kiếm, query cũng được embed và hệ thống tính điểm bằng dot product giữa query embedding và từng document embedding, sau đó sắp xếp giảm dần theo `score`.

**`search_with_filter` + `delete_document` - hướng tiếp cận:**

Với `search_with_filter`, tôi lọc metadata trước rồi mới chạy similarity search trên tập record đã lọc. Cách này giúp giảm nhiễu khi chỉ muốn tìm trong một nhóm tài liệu cụ thể, ví dụ `audience="student"` hoặc `department="library"`. Với `delete_document`, tôi xóa tất cả record có `metadata["doc_id"]` trùng với `doc_id` cần xóa và trả về `True` nếu có ít nhất một chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer` - hướng tiếp cận:**

Agent nhận câu hỏi, gọi `store.search()` để lấy top-k chunk liên quan nhất, rồi ghép các chunk này thành phần `Context` trong prompt. Prompt yêu cầu LLM chỉ trả lời dựa trên ngữ cảnh đã truy xuất và nói rõ nếu không đủ thông tin. Cuối cùng agent gọi `llm_fn(prompt)` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) - Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

Lệnh đã chạy:

```bash
C:\Users\Fptshop123\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/ -v
```

Kết quả:

```text
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::* PASSED
tests/test_solution.py::TestSentenceChunker::* PASSED
tests/test_solution.py::TestRecursiveChunker::* PASSED
tests/test_solution.py::TestEmbeddingStore::* PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::* PASSED
tests/test_solution.py::TestComputeSimilarity::* PASSED
tests/test_solution.py::TestCompareChunkingStrategies::* PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::* PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::* PASSED

42 passed in 0.09s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) - Cá nhân (5 điểm)

Ghi chú: Kết quả thực tế bên dưới dùng `_mock_embed`, đây là embedding giả lập để kiểm thử nên điểm số không phản ánh chất lượng ngữ nghĩa thật như local multilingual embedder.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học chọn lớp học phần trong hệ thống đăng ký. | Cao | -0.1505 | Không |
| 2 | Thư viện cho sinh viên mượn tài liệu. | Người dùng cần mang thẻ định danh khi mượn sách. | Cao | -0.0136 | Không rõ |
| 3 | Học bổng hỗ trợ sinh viên có kết quả tốt. | Ký túc xá cung cấp chỗ ở cho sinh viên. | Thấp | -0.0355 | Có |
| 4 | Lỗi trùng lịch cần điều chỉnh trước hạn. | Sinh viên đổi lớp khi bị trùng thời khóa biểu. | Cao | 0.0233 | Có một phần |
| 5 | Máy học sử dụng dữ liệu để huấn luyện mô hình. | Thư viện yêu cầu thẻ định danh hợp lệ. | Thấp | 0.0038 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 1 và cặp 2 khá bất ngờ vì về mặt ngữ nghĩa chúng tương đồng, nhưng `_mock_embed` lại cho điểm thấp hoặc âm. Điều này cho thấy mock embedding chỉ phù hợp để kiểm tra code chạy đúng, không phù hợp để đánh giá ý nghĩa văn bản thật. Khi so sánh retrieval trong nhóm, nên dùng `EMBEDDING_PROVIDER=local` như README khuyến nghị.

---

## 5. Kết quả truy xuất của tôi (Competition Results) - Cá nhân (10 điểm)

Ghi chú: Phần dưới là bản nháp chạy trên dữ liệu mẫu `data/k3_university`. Khi nhóm đã thống nhất corpus 5-10 tài liệu thật và đúng 5 câu hỏi benchmark, cần thay bảng này bằng kết quả cuối cùng của nhóm.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên đăng ký học phần ở đâu? | Chunk thuộc `k3-course-registration`, nói về metadata và đăng ký học phần. | 0.1166 | Có một phần | Agent trả lời dựa trên các chunk truy xuất về đăng ký học phần. |
| 2 | Khi bị trùng lịch học phần sinh viên cần làm gì? | Chunk top-1 bị lệch sang `k3-library-services` do dùng mock embedding. | -0.0157 | Không | Agent vẫn nhận context nhưng context chưa đúng trọng tâm. |
| 3 | Thư viện cung cấp những dịch vụ gì? | Chunk top-1 bị lệch sang `k3-course-registration`. | 0.2172 | Không | Agent trả lời dựa trên context truy xuất nhưng retrieval chưa tốt. |
| 4 | Người dùng cần mang gì khi mượn tài liệu thư viện? | Chunk top-1 bị lệch sang `k3-course-registration`. | 0.1278 | Không | Agent thiếu context thư viện chính xác ở top-1. |
| 5 | Tài liệu nào dành cho audience student? | Chunk top-1 là `k3-library-services`, nhưng metadata của tài liệu này là `audience=all`; cần dùng filter. | 0.0499 | Không | Câu này nên chạy lại bằng `search_with_filter(metadata_filter={"audience": "student"})`. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Cần cập nhật sau khi chạy benchmark trên corpus thật của nhóm.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác qua demo:**

Tôi học được rằng chất lượng retrieval không chỉ phụ thuộc vào code chạy đúng, mà còn phụ thuộc rất nhiều vào chất lượng tài liệu, cách chia chunk và metadata. Với dữ liệu có cấu trúc như quy định đại học, metadata như `audience`, `department`, `category` có thể giúp lọc kết quả tốt hơn và tránh lấy nhầm tài liệu dành cho đối tượng khác.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation - tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Cần cập nhật theo benchmark nhóm / 10 |
| **Tổng phần cá nhân** | **Cần cập nhật sau phần nhóm / 60** |
