# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Đạt
**Mã học viên:** 2A202601969
**Nhóm:** B6-1
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai vector embedding hướng gần giống nhau, nghĩa là hai văn bản được mô hình biểu diễn với nội dung hoặc ngữ nghĩa gần nhau. Điểm càng gần 1 thì mức tương đồng càng cao.

**Ví dụ có độ tương tự CAO:**

- Câu A: Sinh viên có thể mượn tài liệu tại thư viện.
- Câu B: Thư viện cho phép sinh viên mượn sách.
- Tại sao tương đồng: Cả hai câu đều nói về quyền mượn tài liệu của sinh viên tại thư viện.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Học phí phải được thanh toán đúng hạn.
- Câu B: Trời hôm nay có nhiều mây.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan là tài chính học vụ và thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine tập trung vào hướng của vector thay vì độ lớn, nên phù hợp để so sánh ngữ nghĩa ngay cả khi các embedding có độ lớn khác nhau. Khoảng cách Euclid có thể bị ảnh hưởng nhiều bởi độ lớn vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Phép tính: $\left\lceil\frac{10000-50}{500-50}\right\rceil = \left\lceil\frac{9950}{450}\right\rceil = 23$.
> Đáp án: 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap bằng 100, số chunk là $\left\lceil\frac{10000-100}{500-100}\right\rceil = \left\lceil\frac{9900}{400}\right\rceil = 25$. Overlap lớn hơn giúp giữ ngữ cảnh nằm sát biên chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách sau dấu kết thúc câu khi có khoảng trắng hoặc xuống dòng. Các câu được loại khoảng trắng thừa rồi gom theo `max_sentences_per_chunk`; văn bản rỗng trả về danh sách rỗng và tham số nhỏ hơn 1 được chuẩn hóa thành 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử separator theo thứ tự đoạn văn, dòng, câu, từ và ký tự; các phần nhỏ được ghép đến gần `chunk_size`. Base case là đoạn đã không vượt kích thước; nếu hết separator, thuật toán cắt trực tiếp theo số ký tự để luôn kết thúc và xử lý được văn bản không có dấu phân cách.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi `Document` được chuẩn hóa thành record gồm ID nội bộ duy nhất, content, bản sao metadata và embedding. Store nhúng query, tính dot product với từng embedding, sắp xếp score giảm dần và trả tối đa `top_k`; bộ nhớ trong là nguồn dữ liệu chính, ChromaDB chỉ là backend mirror tùy chọn.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` lọc record trước bằng cách yêu cầu mọi cặp key/value metadata phải khớp, sau đó mới tính similarity để tránh kết quả ngoài phạm vi. `delete_document` tìm và xóa toàn bộ record có `metadata['doc_id']` tương ứng, đồng thời xóa các ID đó khỏi ChromaDB nếu backend này đang hoạt động.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Agent gọi `store.search()` để lấy top-k chunk, đánh số từng nguồn rồi ghép vào phần `NGỮ CẢNH` của prompt cùng câu hỏi. Prompt yêu cầu LLM chỉ dùng dữ liệu được truy xuất và nói rõ khi context không đủ nhằm giảm câu trả lời không có căn cứ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]
============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

> Kết quả trên được kiểm chứng bằng `py -3.14 -m pytest tests/ -v`. Máy hiện chưa có Python 3.11 là phiên bản chuẩn của lab, vì vậy nên chạy lại cùng lệnh trong môi trường Python 3.11 trước khi nộp chính thức.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                 | Câu B                                                   | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------ | -------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Sinh viên đăng ký học phần trên cổng học vụ. | Người học ghi danh môn học qua hệ thống học vụ. | cao        | 0.593602        | Đúng  |
| 2    | Thư viện cho phép sinh viên mượn sách.          | Sinh viên có thể mượn tài liệu tại thư viện.   | cao        | 0.916984         | Đúng  |
| 3    | Học phí phải được thanh toán đúng hạn.       | Trời hôm nay có nhiều mây.                          | thấp      | 0.008151         | Đúng  |
| 4    | Sinh viên cần kiểm tra môn tiên quyết.           | Môn học có thể yêu cầu học phần tiên quyết.    | cao        | 0.553424         | Đúng  |
| 5    | Ký túc xá dành cho sinh viên.                     | Cơ sở dữ liệu vector lưu embedding.                 | thấp      | 0.020328         | Đúng  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Cặp 2 có điểm cao nhất (`0.916984`), phù hợp vì hai câu gần như diễn đạt cùng một ý. Cặp 3 và 5 gần 0, cho thấy model đa ngữ tách khá rõ các chủ đề không liên quan. Kết quả được đo bằng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, không dùng mock embedding.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query)                                                                 | Top-1 Chunk truy xuất được (tóm tắt)                  | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt)                                                    |
| - | --------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------ | --------------------------------- | ---------------------------------------------------------------------------------------- |
| 1 | Sinh viên bậc cử nhân được mượn tối đa bao nhiêu tài liệu thư viện, thời hạn bao lâu và được gia hạn mấy lần? | Chính sách mượn sách cho giảng viên; gold undergraduate ở top-3 hạng 3 | 0.685 | Một phần; gold ở top-3 | Context đủ để trả lời: 3 tài liệu, 2 tuần, gia hạn 1 lần. |
| 2 | Mức CGPA tối thiểu để duy trì học bổng Full hoặc 100% là bao nhiêu? | Dải GPA 2.50-3.19 để duy trì có điều kiện | 0.688 | Không trực tiếp | Context thiếu ngưỡng gold 3.2 nên agent phải báo chưa đủ thông tin. |
| 3 | Sinh viên phải khiếu nại quyết định hỗ trợ tài chính trong bao lâu và khi nào nhận quyết định cuối? | Thông báo kết quả hỗ trợ tài chính, không có hạn appeal | 0.697 | Không | Context thiếu cả mốc 5 và 10 ngày làm việc. |
| 4 | Hạn thêm và bỏ học phần trong học kỳ chính là ngày làm việc thứ bao nhiêu? | Điều add course: ngày làm việc thứ 10 | 0.666 | Một phần | Có hạn thêm nhưng thiếu hạn bỏ ngày thứ 15 trong top-3. |
| 5 | Sinh viên nội trú được tiếp tối đa bao nhiêu khách và phải đăng ký trước bao lâu? | Quy định đăng ký chỗ ở mới trong một học kỳ | 0.623 | Không | Context không chứa số khách và hạn đăng ký, không đủ để trả lời. |

**Bao nhiêu câu hỏi trả về chunk chứa đầy đủ gold answer trong top-3?** 1 / 5

> Kết quả được chạy trên 7 tài liệu công khai VinUniversity bằng `SentenceChunker(max_sentences_per_chunk=1)` và local multilingual embedder. Heuristic của script là `6/10` vì cho 1 điểm khi top-3 có tài liệu đúng hoặc một phần bằng chứng; nếu chấm nghiêm theo đủ gold evidence thì câu 1 đạt, câu 4 chỉ có một nửa bằng chứng, còn câu 2, 3, 5 thất bại. `demo_llm` chỉ xem trước prompt nên chưa thể khẳng định điểm “agent answer” như khi dùng LLM thật.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Qua benchmark tập trung, tôi học được rằng chunk nhỏ không luôn tốt hơn. Sentence một câu lấy đúng quy tắc thư viện, nhưng FixedSize `500/50` giữ đủ các cặp mốc thời gian và đạt độ phủ tổng thể cao hơn (`8/10`).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                               | Điểm tự đánh giá |
| -------------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                                   | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)               | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)         | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions)     | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results)     | 6 / 10 (heuristic phủ bằng chứng) |
| **Tổng phần cá nhân hiện có thể xác minh** | **56 / 60**      |
