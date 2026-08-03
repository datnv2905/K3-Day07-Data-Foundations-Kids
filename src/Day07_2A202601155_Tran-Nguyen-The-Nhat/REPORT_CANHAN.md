# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Nguyễn Thế Nhật  
**Mã học viên:** 2A202601155  
**Nhóm:** Chưa cập nhật  
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

> Hai vector embedding có hướng gần nhau; mô hình thường đang biểu diễn hai đoạn văn có nội dung hoặc ngữ nghĩa gần nhau. Điểm càng gần 1 thì càng tương tự, gần 0 là ít liên hệ, còn âm là hướng đối nghịch.

**Ví dụ có độ tương tự cao:**

- Câu A: Sinh viên có thể mượn tài liệu tại thư viện.
- Câu B: Thư viện cho phép sinh viên mượn sách.
- Cả hai cùng nói về quyền mượn tài liệu của sinh viên.

**Ví dụ có độ tương tự thấp:**

- Câu A: Học phí phải được thanh toán đúng hạn.
- Câu B: Trời hôm nay có nhiều mây.
- Hai câu thuộc hai chủ đề không liên quan: tài chính học vụ và thời tiết.

**Vì sao cosine thường phù hợp hơn Euclidean distance cho text embedding?**

> Cosine so sánh hướng vector thay vì độ lớn, nên phù hợp khi cần so mức gần nhau về ngữ nghĩa. Khoảng cách Euclid bị ảnh hưởng rõ hơn bởi độ lớn vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

> `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23` chunks.

**Khi tăng overlap lên 100:**

> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunks. Overlap lớn giữ ngữ cảnh tại biên chunk tốt hơn nhưng tăng số vector, dung lượng và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`**

> Dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách sau dấu kết thúc câu. Sau đó loại khoảng trắng thừa, bỏ chuỗi rỗng và gom tối đa `max_sentences_per_chunk` câu. Văn bản rỗng trả về `[]`; tham số nhỏ hơn 1 được chuẩn hóa thành 1.

**`RecursiveChunker.chunk` / `_split`**

> Thuật toán thử separator theo thứ tự đoạn văn, dòng, câu, từ rồi ký tự. Các đoạn nhỏ được ghép đến trước giới hạn `chunk_size`; đoạn vẫn quá dài đi tiếp sang separator ưu tiên thấp hơn. Base case cắt fixed-size để luôn kết thúc.

### Lớp EmbeddingStore

**`add_documents` + `search`**

> Mỗi `Document` được chuẩn hóa thành record có ID nội bộ duy nhất, content, bản sao metadata và embedding. Store nhúng query một lần, tính dot product với mọi record, sắp xếp giảm dần rồi cắt `top_k`.

**`search_with_filter` + `delete_document`**

> `search_with_filter` lọc metadata trước rồi mới xếp hạng để không làm mất kết quả hợp lệ sau top-k. `delete_document` xóa mọi record có `metadata['doc_id']` phù hợp và trả về `True` khi có dữ liệu bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`**

> Agent gọi `store.search()`, đánh số context cùng `doc_id`, rồi đưa vào prompt yêu cầu chỉ trả lời dựa trên ngữ cảnh. Khi store rỗng, agent trả thông báo rõ ràng thay vì bịa câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

```text
platform darwin -- Python 3.11.9, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]
============================== 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua:** 42 / 42

Lệnh đã chạy:

```bash
LAB_SOLUTION_PACKAGE='src.Day07_2A202601155_Tran-Nguyen-The-Nhat' python3 -m pytest tests -v
```

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| --- | --- | --- | --- | ---: | --- |
| 1 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học ghi danh môn học qua hệ thống học vụ. | cao | -0.066465 | Không |
| 2 | Thư viện cho phép sinh viên mượn sách. | Sinh viên có thể mượn tài liệu tại thư viện. | cao | 0.076851 | Không |
| 3 | Học phí phải được thanh toán đúng hạn. | Trời hôm nay có nhiều mây. | thấp | 0.240984 | Không |
| 4 | Sinh viên cần kiểm tra môn tiên quyết. | Môn học có thể yêu cầu học phần tiên quyết. | cao | -0.034324 | Không |
| 5 | Ký túc xá dành cho sinh viên. | Cơ sở dữ liệu vector lưu embedding. | thấp | 0.037364 | Không |

**Kết quả bất ngờ nhất và ý nghĩa:**

> Cặp 3 là bất ngờ nhất: hai câu không liên quan nhưng điểm dương. Nguyên nhân là `_mock_embed` sinh vector quyết định từ hash của toàn chuỗi, không học ngữ nghĩa. Vì vậy các điểm trên chỉ kiểm tra pipeline; benchmark chất lượng tiếng Việt cần `LocalEmbedder`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược cá nhân: `RecursiveChunker(chunk_size=400)`. Kết quả dưới đây là chạy sơ bộ với corpus template hiện có và mock embedding.

| # | Câu hỏi | Top-1 chunk | Score | Liên quan? | Nhận xét |
| --- | --- | --- | ---: | --- | --- |
| 1 | Sinh viên đăng ký học phần ở đâu? | `k3-library-services`: template thư viện | 0.090805 | Không | Truy xuất sai tài liệu. |
| 2 | Cần làm gì trước khi đăng ký môn có tiên quyết? | `k3-library-services`: hướng dẫn bổ sung quy định | 0.269569 | Không | Mock embedding không nhận diện điều kiện tiên quyết. |
| 3 | Xử lý lỗi trùng lịch học thế nào? | `k3-course-registration`: nội dung đăng ký học phần | 0.221978 | Có | Chunk có thông tin điều chỉnh lớp trước thời hạn. |
| 4 | Thư viện cung cấp những dịch vụ gì? | `k3-library-services`: template thư viện | 0.063288 | Có, nhưng thiếu | Dữ liệu template làm context nhiễu. |
| 5 | Cần mang gì khi mượn tài liệu thư viện? | `k3-library-services`: hướng dẫn bổ sung quy định | 0.075019 | Không | Chunk top-1 không chứa yêu cầu thẻ định danh. |

**Số câu có top-1 liên quan trong lần chạy sơ bộ:** 2 / 5.

> Đây chưa phải benchmark chính thức: corpus hiện chỉ có 2 tài liệu template dùng URL `example.edu`; nhóm chưa chốt 5 query/gold answer chung; mock embedding không đánh giá được ngữ nghĩa. Trước khi nộp, cần thay bằng corpus 5–10 nguồn công khai thật, điền đúng 5 query cố định vào `bench.py`, chạy A/B với `metadata_filter={"audience": "student"}`, lưu top-3 và cập nhật bảng này.

**Điều học được từ nhóm/demo:**

> Chưa có dữ liệu thảo luận nhóm để kết luận trung thực; bổ sung mục này sau phiên so sánh strategy.

---

## Tự đánh giá (Phần cá nhân)

| Tiêu chí | Điểm tự đánh giá |
| --- | --- |
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | Chưa tự chấm / 10 |
| **Tổng có thể xác minh** | **50 / 60** |
