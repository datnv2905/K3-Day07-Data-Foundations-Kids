# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Nguyễn Thế Nhật  
**Mã học viên:** 2A202601155  
**Nhóm:** Kids
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
| 1 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học ghi danh môn học qua hệ thống học vụ. | cao | 0.496389 | Có |
| 2 | Thư viện cho phép sinh viên mượn sách. | Sinh viên có thể mượn tài liệu tại thư viện. | cao | 0.687075 | Có |
| 3 | Học phí phải được thanh toán đúng hạn. | Trời hôm nay có nhiều mây. | thấp | 0.241541 | Có |
| 4 | Sinh viên cần kiểm tra môn tiên quyết. | Môn học có thể yêu cầu học phần tiên quyết. | cao | 0.589369 | Có |
| 5 | Ký túc xá dành cho sinh viên. | Cơ sở dữ liệu vector lưu embedding. | thấp | 0.309803 | Có |

**Kết quả bất ngờ nhất và ý nghĩa:**

> Cặp 3 là bất ngờ nhất: hai câu không liên quan vẫn có điểm dương 0.241541. Embedding không phải phép kiểm tra đúng/sai tuyệt đối; điểm cosine chỉ là tín hiệu xếp hạng tương đối. Các cặp đồng nghĩa có điểm cao hơn rõ rệt, phù hợp với kỳ vọng khi dùng `text-embedding-3-small`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Corpus chung: 7 chính sách công khai của VinUni trong `data/k3_university/`; strategy cá nhân: `RecursiveChunker(chunk_size=1000)`; backend: OpenAI `text-embedding-3-small`; số chunk đã nạp: 200. Bộ 5 query, gold document và evidence string được khai báo trong `bench.py` để các lần chạy dùng cùng một chuẩn.

| # | Câu hỏi | Gold evidence cần có trong top-3 | Top-1 chunk | Score | Liên quan? | Nhận xét |
| --- | --- | --- | --- | ---: | --- | --- |
| 1 | Hạn nộp hỗ trợ tài chính cho Fall? | `July 10th` | `vinuni-financial-aid-request`: timeline Fall | 0.4494 | Có | Evidence có trong top-3. |
| 2 | Ai được vào thư viện, mượn tài liệu hoặc dùng tài nguyên điện tử? | `valid VinUni ID` | `vinuni-library-access-services`: non-regular user access | 0.3856 | Có, nhưng thiếu | Đúng tài liệu nhưng evidence ID không nằm trong top-3. |
| 3 | Đăng ký khách trong ngày/qua đêm trước bao lâu? | `03 working days` | `vinuni-residential-life`: guest responsibility | 0.4230 | Có | Evidence có trong top-3. |
| 4 | GPA 0.0–2.49 ảnh hưởng học bổng thế nào? | `Automatic Downgrade` | `vinuni-undergraduate-academic-regulations`: academic standing | 0.5608 | Có, nhưng không top-1 | Evidence xuất hiện ở hạng 3 từ policy học bổng. |
| 5 | Sinh viên bị cáo buộc gian lận được bảo đảm quy trình nào? | `due process` | `vinuni-student-academic-integrity`: instructor guidance | 0.3789 | Không đủ | Đúng policy nhưng top-3 không có evidence `due process`. |

**Số câu có evidence chính xác trong top-3:** 3 / 5.

> Failure case là query 5: cả top-3 cùng đúng policy Academic Integrity nhưng không chunk nào chứa câu “due process”. Điều này cho thấy retrieval theo ngữ nghĩa đã tìm đúng chủ đề, nhưng chunk 1.000 ký tự vẫn có thể làm phần trả lời cụ thể bị xếp sau top-3. Cải thiện khả dĩ là giảm `chunk_size` hoặc thử chunk theo heading, trong khi vẫn giữ nguyên corpus và query để so sánh công bằng.

**A/B metadata filter:**

> Các query 1, 3, 4, 5 gọi `metadata_filter={"audience": "student"}`; query thư viện không filter. Việc hoàn thiện metadata diversity và đánh giá A/B filter thuộc phần corpus/report nhóm, không thuộc phần code cá nhân.

**Điều học được từ nhóm/demo:**

> Cùng một corpus chỉ so sánh công bằng khi mọi người giữ nguyên data, 5 query và embedding backend, chỉ đổi strategy. Kết quả mock cho thấy score cao không đủ chứng minh câu trả lời đúng; cần kiểm evidence string ở cấp chunk, không chỉ nhìn `doc_id`.

---

## Tự đánh giá (Phần cá nhân)

| Tiêu chí | Điểm tự đánh giá |
| --- | --- |
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 6 / 10 (3 evidence đúng top-3; 2 trường hợp context thiếu) |
| **Tổng có thể xác minh** | **56 / 60** |
