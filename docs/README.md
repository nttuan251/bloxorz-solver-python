# Hướng dẫn đọc tài liệu nội bộ

Thư mục `docs/` dành cho các thành viên (và Claude Code), **không phải** hướng dẫn chạy chương trình. Hướng dẫn cài đặt / chạy sẽ nằm ở `README.md` ở thư mục gốc.

Không commit file PDF đề bài vào repo (nhánh `huyhoang` đã chặn `*.pdf` trong `.gitignore`); mỗi người giữ bản riêng và dùng `ASSIGNMENT.md` để tra cứu.

## Thứ tự đọc

Người mới vào nhóm đọc theo thứ tự dưới đây. Bốn bước đầu là để **hiểu đề và các luật**: thầy đã trả lời gì → còn chờ thầy điều gì → nhóm đã chốt gì. Hai bước sau là để **hiểu tình trạng nhóm**, hai bước cuối dùng khi **bắt tay làm việc**.

| Bước | File | Thời gian đọc | Đọc xong sẽ biết |
|---|---|---|---|
| 1 | [`ASSIGNMENT.md`](ASSIGNMENT.md) | 40–60 phút | Đề yêu cầu gì, luật chơi, cách biến game thành bài toán tìm kiếm, 4 thuật toán, cách chấm điểm |
| 2 | [`TEACHER_QA.md`](TEACHER_QA.md) | 5 phút | Thầy đã giải đáp gì (những điểm này ưu tiên hơn PDF) |
| 3 | [`QUESTIONS_FOR_TEACHER.md`](QUESTIONS_FOR_TEACHER.md) | 5 phút | Những câu nhóm còn thắc mắc (Q1–Q6), được nhắc lại trong `DECISIONS.md` |
| 4 | [`DECISIONS.md`](DECISIONS.md) | 10 phút | Luật nào nhóm đã chốt, luật nào còn chờ quyết (và chờ câu hỏi nào của thầy) |
| 5 | [`BRANCHES.md`](BRANCHES.md) | 5 phút | Ai đang làm nhánh nào, nhánh nào có gì, quy trình gộp |
| 6 | [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) | 10 phút | Lỗi đã biết của từng nhánh và mức độ nghiêm trọng |
| 7 | [`PROPOSALS.md`](PROPOSALS.md) | 5 phút | Các việc nhóm nên làm tiếp, theo thứ tự ưu tiên |
| 8 | [`AI_USAGE.md`](AI_USAGE.md) | 2 phút | Cách ghi lại việc dùng AI và nguồn ngoài (bắt buộc cho báo cáo) |

Nếu chỉ có 15 phút: đọc mục 1–2 và 17 (checklist) của `ASSIGNMENT.md`, rồi `TEACHER_QA.md`, `QUESTIONS_FOR_TEACHER.md` và `DECISIONS.md`.

## Chú thích các mã viết tắt

Các file trỏ qua lại với nhau bằng mã ngắn. Chữ cái đầu cho biết mã nằm ở file nào.

| Mã | Ý nghĩa | Nằm ở file |
|---|---|---|
| `D1`, `D2`… | Quyết định **đã chốt** | `DECISIONS.md` |
| `U1`, `U2`… | Vấn đề **chưa chốt** | `DECISIONS.md` |
| `Q1`, `Q2`… | Câu hỏi định gửi thầy | `QUESTIONS_FOR_TEACHER.md` |
| `H1`… | Lỗi ở nhánh `huyhoang` | `KNOWN_ISSUES.md` |
| `R1`… | Lỗi ở nhánh `develop-refactor` | `KNOWN_ISSUES.md` |
| `G1`… | Lỗi ở nhánh `gui/gui1` | `KNOWN_ISSUES.md` |
| `S1`… | Lỗi ở nhánh `develop-solvers` | `KNOWN_ISSUES.md` |
| `C1`… | Vấn đề chung của cả repo | `KNOWN_ISSUES.md` |
| `P1`, `P2`… | Đề xuất cải tiến | `PROPOSALS.md` |

Số thứ tự câu hỏi đáp của thầy (câu 1–13) là số trong Google Sheet, xem `TEACHER_QA.md`.

## Nội dung từng file

### 1. `ASSIGNMENT.md` — Giải thích đề bài

Bản giải thích chi tiết file PDF đề, viết bằng tiếng Việt, đã bổ sung các giải đáp của thầy (đánh dấu **[THẦY GIẢI ĐÁP]**). Gồm:

- Tổng quan và bảng điểm (100 điểm: game 20, bốn solver 40, báo cáo 30, video 10).
- Luật chơi: ba tư thế của khối, **bảng chuyển trạng thái 12 ô**, điều kiện rơi và thắng.
- Ô đặc biệt: fragile, bridge, soft / heavy / split switch, toggle / permanent, tách và ghép khối.
- Cách mô hình hóa bài toán tìm kiếm: state, action, transition, goal test, cost, chống lặp.
- BFS, DFS / IDS, UCS, A\*: cách hoạt động, pseudocode, điểm mạnh / yếu, các "bẫy" khi thiết kế heuristic.
- Bốn số liệu phải đo, yêu cầu báo cáo, video, cách nộp bài.
- Gợi ý kiến trúc, bảng unit test tối thiểu, kế hoạch 3 tuần, **checklist trước khi nộp** (mục 17).

Đọc kỹ nhất file này. Các file còn lại đều dựa vào nó.

### 2. `TEACHER_QA.md` — Hỏi đáp với thầy

Bảng 13 câu hỏi đáp chép từ Google Sheet của lớp (kèm link), mỗi câu có cột "ảnh hưởng đến nhóm". Điểm chính: tối thiểu 10 test case, GUI 3D, chỉ thuật toán bắt buộc Python, được dùng code / AI có sẵn nhưng phải cite.

### 3. `QUESTIONS_FOR_TEACHER.md` — Câu hỏi chờ thầy

6 câu (Q1–Q6) nhóm chưa rõ, mỗi câu có bối cảnh và **đáp án nhóm đề xuất**. Câu hỏi thật được đăng lên Google Sheet; file này là bản nháp và nơi theo dõi trạng thái. Đọc trước `DECISIONS.md` vì nhiều dòng "Chưa chốt" ở đó đang chờ chính những câu này.

### 4. `DECISIONS.md` — Quyết định thiết kế

Hai bảng:

- **Đã chốt** (D1–D6): những điều chắc chắn, từ PDF hoặc từ thầy. Code và unit test được phép dựa vào.
- **Chưa chốt** (U1–U12): những điều nhóm còn phải quyết, kèm cách hai bản engine (`huyhoang` và `develop-refactor`) đang làm. Quan trọng nhất là **U1: dùng engine nào**.

### 5. `BRANCHES.md` — Các nhánh và quy trình

Bảng tình trạng 7 nhánh (ai làm, có gì, ghi chú), quy trình đặt tên nhánh và gộp qua Pull Request, thứ tự gộp đề xuất cho tới khi nộp bài.

### 6. `KNOWN_ISSUES.md` — Lỗi đã biết

Lỗi tìm được khi đọc code, chia theo từng nhánh, mỗi lỗi có mã (ví dụ H1, R1), mức độ (Cao / TB / Thấp), file và mô tả. Mỗi lỗi nên trở thành một unit test. Khi sửa xong thì ghi commit vào cột Trạng thái.

### 7. `PROPOSALS.md` — Đề xuất cải tiến

12 đề xuất (P1–P12) có lý do và mức ưu tiên: chọn một engine, hàm cost không đều, sửa UCS / A\*, heuristic khi có teleport, unit test, script benchmark, thêm màn chơi, README, GUI... Đây là **ý kiến**, chưa phải quyết định; khi nhóm đồng ý thì chuyển sang `DECISIONS.md`.

### 8. `AI_USAGE.md` — Ghi chép dùng AI

Hai bảng để điền dần: bảng ghi mỗi lần dùng AI (ngày, người, công cụ, prompt, phần AI làm, cách kiểm tra) và bảng nguồn ngoài (code, màn chơi, ảnh lấy từ đâu). Dùng để viết phần **Appendix** và **References** của báo cáo.

## Các file liên quan ngoài `docs/`

- `CLAUDE.md` (thư mục gốc): hướng dẫn ngắn cho Claude Code, được nạp tự động mỗi phiên làm việc. Chỉ ghi quy tắc và chỉ đường tới các file trong `docs/`.

## Khi nào cập nhật file nào

| Khi... | Cập nhật |
|---|---|
| Thầy trả lời câu hỏi mới | `TEACHER_QA.md`, rồi `DECISIONS.md`, rồi đổi trạng thái trong `QUESTIONS_FOR_TEACHER.md`; nếu thay đổi yêu cầu thì sửa cả `ASSIGNMENT.md` |
| Nhóm chốt một luật / quy ước | Chuyển dòng từ "Chưa chốt" sang "Đã chốt" trong `DECISIONS.md` |
| Tìm thấy hoặc sửa xong lỗi | `KNOWN_ISSUES.md` |
| Có ý tưởng cải tiến | `PROPOSALS.md` |
| Có nhánh mới hoặc gộp nhánh | `BRANCHES.md` |
| Dùng AI hoặc lấy code / màn chơi / ảnh từ ngoài | `AI_USAGE.md` |
