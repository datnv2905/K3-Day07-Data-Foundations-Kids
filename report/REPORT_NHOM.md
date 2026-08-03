# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** B6-1
**Thành viên:** Phong (2A202601077), Lê Hồng Đức (2A202601313), Nguyễn Kim Trung Đức (2A202601325), Toàn (2A202601493), Nguyễn Văn Đạt (2A202601969), Trần Nguyễn Thế Nhật (2A202601155)
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào các quy định và dịch vụ dành cho sinh viên VinUniversity: thư viện, học bổng/hỗ trợ tài chính, đăng ký học phần, đời sống nội trú, học phí và liêm chính học thuật.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Guidelines for Student Financial Aid Support Request | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/guidelines-for-student-financial-support-request/) | 2026-08-03 / GDL-FAO-001-V2.0 | 6,345 | audience, department, category, language |
| 2 | Library Access and Services Policy | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/library-policies-for-users/) | 2026-08-03 / POL-LLR-001-V4.0 | 7,463 | audience, department, category, language |
| 3 | Residential Life Guideline | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/residential-life-guideline/) | 2026-08-03 / GDL-SAM-008-V5.0 | 15,491 | audience, department, category, language |
| 4 | Guidelines for Maintaining Entry Scholarship and Financial Aid Support | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/criteria-to-maintain-the-entry-scholarship-and-financial-aid-support/) | 2026-08-03 / GDL-SAM-004-V2.1 | 4,250 | audience, department, category, language |
| 5 | Student Academic Integrity | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/student-academic-integrity/) | 2026-08-03 / VUNI.14-V3.0 | 34,149 | audience, department, category, language |
| 6 | Financial Regulations and Tariff for Student | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/financial-regulations-and-tariff-for-student-2/) | 2026-08-03 / VUNI_TS03_Student-2025-10-08 | 36,295 | audience, department, category, language |
| 7 | Academic Regulations for Full-Time Undergraduate Programs | [VinUniversity Policy](https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/) | 2026-08-03 / VU_HT03-V8.1 | 68,365 | audience, department, category, language |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `vinuni-library-access-services` | Định danh ổn định để truy vết và xóa toàn bộ chunk của tài liệu. |
| `source_url` | string | URL trang policy VinUniversity | Kiểm chứng nguồn gốc và truy cập bản công bố. |
| `retrieved_at` | date string | `2026-08-03` | Biết thời điểm thu thập để đánh giá độ mới. |
| `document_version` | string | `POL-LLR-001-V4.0` | Phân biệt phiên bản chính sách. |
| `audience` | string | `student` | Giới hạn kết quả theo đối tượng sử dụng. |
| `department` | string | `VinUniversity Library` | Lọc theo đơn vị chịu trách nhiệm. |
| `category` | string | `library-services` | Thu hẹp miền tìm kiếm theo loại dịch vụ/quy định. |
| `language` | string | `en` | Chọn corpus phù hợp với ngôn ngữ và model embedding. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Library Access and Services | FixedSize (`500`, overlap `0`) | 15 | 497.5 | Có thể cắt ngang hàng của bảng. |
| Library Access and Services | Sentence (`3 câu`) | 33 | 221.9 | Khá tốt với quy tắc viết thành câu. |
| Library Access and Services | Recursive (`500`) | 16 | 464.3 | Giữ đoạn tốt hơn fixed-size nhưng bảng vẫn khó. |
| Residential Life | FixedSize (`500`, overlap `0`) | 31 | 499.7 | Có thể tách nhãn ngày khỏi giờ trong bảng. |
| Residential Life | Sentence (`3 câu`) | 40 | 385.0 | Giữ được chính sách khách nếu câu hoàn chỉnh. |
| Residential Life | Recursive (`500`) | 42 | 366.9 | Giữ ranh giới đoạn khá tốt. |
| Undergraduate Academic Regulations | FixedSize (`500`, overlap `0`) | 137 | 499.0 | Dễ cắt ngang điều khoản dài. |
| Undergraduate Academic Regulations | Sentence (`3 câu`) | 158 | 430.1 | Giữ câu add/drop hoàn chỉnh. |
| Undergraduate Academic Regulations | Recursive (`500`) | 184 | 369.5 | Giữ đoạn/tiêu đề tốt, số chunk cao hơn. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

Các cấu hình dưới đây được phân công theo thành viên và benchmark được chạy tập trung trên cùng máy để kiểm soát model, corpus và câu hỏi. Mỗi thành viên cần xác nhận cấu hình trước khi nộp.

| Thành viên | Cấu hình được phân công | Lý do thử nghiệm |
|---|---|---|
| Phong | FixedSize `500/50` | Đường cơ sở có overlap để hạn chế mất thông tin ở biên chunk. |
| Lê Hồng Đức | FixedSize `300/50` | Kiểm tra chunk ngắn hơn có tăng độ chính xác hay làm mất ngữ cảnh. |
| Nguyễn Kim Trung Đức | Sentence `3 câu/chunk` | Gom vài câu liên tiếp để cân bằng ngữ cảnh và độ tập trung. |
| Toàn | Recursive `500` | Ưu tiên ranh giới đoạn, dòng và câu thay vì cắt ký tự trực tiếp. |
| Nguyễn Văn Đạt | Sentence `1 câu/chunk` | Cô lập từng quy tắc ngắn, đặc biệt là hàng mượn tài liệu đã chuẩn hóa thành câu. |
| Trần Nguyễn Thế Nhật | Heading/section `500` | Thử yêu cầu riêng K3: giữ tiêu đề điều/mục với nội dung bên dưới. |

Mã custom heading/section và toàn bộ phép đo nằm trong `scripts/run_team_benchmark.py`.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm phủ bằng chứng (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phong | FixedSize `500/50` | 8 | Tốt nhất tổng thể; giữ đủ cặp mốc ở câu 3-5. | Chưa lấy đúng con số ở câu thư viện và học bổng. |
| Lê Hồng Đức | FixedSize `300/50` | 7 | Tốt ở quy trình khiếu nại và chính sách khách. | Cắt rời hai mốc add/drop. |
| Nguyễn Kim Trung Đức | Sentence `3 câu` | 7 | Tốt ở add/drop và chính sách khách. | Thiếu một mốc trong quy trình khiếu nại. |
| Toàn | Recursive `500` | 7 | Tốt ở add/drop, giữ ranh giới tự nhiên. | Chưa đưa đủ mốc khiếu nại vào top-3. |
| Nguyễn Văn Đạt | Sentence `1 câu` | 6 | Cấu hình duy nhất lấy đúng gold thư viện vào top-3. | Chunk quá nhỏ làm mất cặp mốc ở câu 3-5. |
| Trần Nguyễn Thế Nhật | Heading/section `500` | 4 | Có ngữ cảnh điều/mục và đáp ứng thử nghiệm K3. | Tiêu đề lặp làm loãng embedding; thất bại ở câu chính sách khách. |

> Điểm trên là heuristic phủ bằng chứng của script: 2 điểm khi top-3 chứa đủ cụm gold, 1 điểm khi chỉ có tài liệu đúng/một phần bằng chứng, 0 điểm khi không có tài liệu đúng. Đây không thay thế điểm rubric chính thức vì demo hiện chưa dùng LLM thật để xác minh câu trả lời agent.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> FixedSize `500/50` có độ phủ bằng chứng tổng thể cao nhất (`8/10`) vì các câu hỏi 3-5 cần nhiều mốc nằm gần nhau. Sentence `1 câu` tốt nhất riêng câu thư viện nhưng thất bại khi đáp án trải trên hai câu, cho thấy không có một kích thước chunk tối ưu cho mọi dạng chính sách.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên bậc cử nhân được mượn tối đa bao nhiêu tài liệu thư viện, thời hạn bao lâu và được gia hạn mấy lần? | 3 tài liệu, 2 tuần, gia hạn 1 lần. | `vinuni-library-access-services`, mục 2.2 Circulation Privileges. Lọc `audience=student`, `category=library-services`. |
| 2 | Mức CGPA tối thiểu để duy trì học bổng Full hoặc 100% là bao nhiêu? | CGPA tích lũy từ 3.2 trở lên trong năm học được đánh giá. | `vinuni-scholarship-maintenance`, bảng Merit-based Scholarships, Full & 100%. |
| 3 | Sinh viên phải khiếu nại quyết định hỗ trợ tài chính trong bao lâu và khi nào nhận quyết định cuối? | Nộp khiếu nại trong 5 ngày làm việc; quyết định cuối trong 10 ngày làm việc. | `vinuni-financial-aid-request`, mục 5.1 và 5.3. |
| 4 | Hạn thêm và bỏ học phần trong học kỳ chính là ngày làm việc thứ bao nhiêu? | Thêm trước hết ngày làm việc thứ 10; bỏ trước hết ngày làm việc thứ 15. | `vinuni-undergraduate-academic-regulations`, Article 12. |
| 5 | Sinh viên nội trú được tiếp tối đa bao nhiêu khách và phải đăng ký trước bao lâu? | Tối đa 3 khách; đăng ký trước 3 ngày làm việc cho khách trong ngày và 5 ngày làm việc cho khách qua đêm. | `vinuni-residential-life`, mục 4 Guest Visit Policy. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Quyền mượn thư viện | Sentence `1 câu` | Có, hạng 3 (`0.676`) | Gold nằm trọn trong một câu; hai hạng đầu cùng chủ đề nhưng sai nhóm người dùng. |
| 2 | CGPA học bổng Full/100% | Chưa có cấu hình đạt đủ | Không | Top-3 lấy đúng tài liệu nhưng ưu tiên dải GPA 2.50-3.19 thay vì ngưỡng 3.2. |
| 3 | Khiếu nại hỗ trợ tài chính | FixedSize `500/50` | Có | Top-3 chứa cả mốc 5 và 10 ngày làm việc. |
| 4 | Hạn add/drop | FixedSize `500/50`, Sentence `3 câu`, Recursive `500` | Có | Các cấu hình có ngữ cảnh nhiều câu giữ đủ hai mốc 10 và 15. |
| 5 | Khách khu nội trú | FixedSize `500/50`, FixedSize `300/50`, Sentence `3 câu`, Recursive `500` | Có | Sentence `1 câu` quá nhỏ nên không gom đủ số khách và hai hạn đăng ký. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Câu 1 được chạy với `{"audience": "student", "category": "library-services"}`. Với Sentence `1 câu`, top-3 filtered và unfiltered giống nhau vì ba kết quả đầu vốn đã thuộc tài liệu thư viện; filter không tăng thứ hạng trong lần đo này nhưng loại hoàn toàn các category khác và hữu ích khi corpus mở rộng. Chỉ lọc `audience=student` không có tác dụng phân biệt vì cả bảy tài liệu hiện cùng audience.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Bảng HTML bị làm phẳng khiến nhãn và giá trị dễ bị cắt rời; chuẩn hóa mỗi hàng thành câu đầy đủ giúp truy xuất có nghĩa hơn.
> - Chunk một câu đưa đáp án thư viện vào top-3 nhưng làm giảm khả năng trả lời câu cần ghép nhiều mốc.
> - Model đa ngữ nhận diện đúng chủ đề nhưng đôi khi phân biệt kém nhóm `undergraduate`, `graduate`, `faculty`; top-1 cùng chủ đề chưa chắc là gold.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus và model, FixedSize `500/50` đạt độ phủ tổng thể tốt hơn nhờ giữ nhiều mốc trong một chunk, còn Sentence `1 câu` chính xác hơn với quy tắc đơn lẻ. Heading/section không tự động tốt hơn: tiêu đề được lặp lại có thể lấn át từ khóa phân biệt trong nội dung.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa toàn bộ bảng thành các câu tự chứa chủ thể và giá trị, sau đó dùng chunk theo section với overlap theo câu thay vì lặp tiêu đề máy móc. Ngoài vector similarity, nhóm sẽ thử hybrid retrieval hoặc reranker để phân biệt các hàng có cấu trúc gần giống nhau như undergraduate/graduate/faculty.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |
