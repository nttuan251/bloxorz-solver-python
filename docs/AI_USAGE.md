# Ghi chép sử dụng AI (cho phần Appendix của báo cáo)

Đề yêu cầu Appendix ghi lại **cách nhóm dùng Generative AI (LLM)** và **các prompt đã dùng** (PDF trang 7). Thầy cho phép dùng AI và code có sẵn nhưng **phải cite** (hỏi đáp câu 5, 12). Thầy có thể phỏng vấn ngẫu nhiên, nên mỗi người phải giải thích được phần code mình nộp.

Mỗi thành viên tự thêm dòng cho phần việc của mình, ghi ngay khi dùng, đừng để tới cuối mới nhớ lại.

## Bảng ghi chép

| Ngày | Thành viên | Công cụ | Dùng cho việc gì | Prompt tiêu biểu (rút gọn) | Phần AI tạo ra | Nhóm đã kiểm tra / sửa thế nào |
|---|---|---|---|---|---|---|
| 2026-10-17 | Tran Trong Tu | Claude Code | Đọc đề, đọc code các nhánh, soạn tài liệu trong `docs/` | "Đọc đề và code của các nhánh, giải thích nhóm đã làm gì" | Tóm tắt đề, danh sách lỗi, đề xuất, file `docs/*`, `CLAUDE.md` | Tự đọc lại, đối chiếu với PDF và hỏi đáp của thầy |
| 2026-10-18 | Tran Trong Tu | Claude Code | Review PR #3, #4; chạy thử solver các nhánh; gộp hai PR thành PR #5 và sửa lỗi import, tên file màn | "Đọc code tất cả các nhánh xem có lỗi không", "sửa code theo pull request" | Bình luận review PR #3, #4; nhánh `integrate/engine-gui` (merge + 3 commit sửa lỗi); script kiểm tra chạy ngoài repo | Chạy 4 solver trên 12 màn, replay lời giải, chạy GUI offscreen trong WSL; cần Tuan và Huy Hoang xem lại PR #5 |
| | | | | | | |

## Nguồn ngoài (code, màn chơi, asset)

Ghi mọi thứ không do nhóm tự làm, để đưa vào References.

| Thành phần trong repo | Lấy từ đâu (link) | Giấy phép | Người thêm |
|---|---|---|---|
| `maps/level01.txt` … `level09.txt` | *(cần hỏi người commit đầu tiên)* | | |
| Code GUI ban đầu `src/gui/` | *(cần hỏi người commit đầu tiên)* | | |
| `assets/Playstation_*.png` | *(cần hỏi người thêm)* | | |
| | | | |
