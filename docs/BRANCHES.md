# Các nhánh và quy trình làm việc

## Tình trạng các nhánh (cập nhật 2026-10-17)

| Nhánh | Người làm | Nội dung | Ghi chú |
|---|---|---|---|
| `main` | Nguyen Thanh Tuan | Commit đầu tiên: GUI Ursina tối giản (bàn 3×3 cố định), 9 màn text. Chưa có luật rơi / thắng, chưa có solver. | Chưa gộp nhánh nào |
| `develop` | — | Giống hệt `main`. | Dự kiến là nhánh gộp |
| `huyhoang` | Huy Hoang | Engine đầy đủ (`src/core/`: fragile, cầu, 3 loại switch, split / ghép), 4 solver BFS / DFS / UCS / A\* có đo số liệu (`src/solvers/`), GUI Ursina gắn solver, spec map `maps/MAP_FORMAT.txt`, 3 màn đặc biệt. | Đầy đủ nhất |
| `gui/gui1` | Nguyen Thanh Tuan | GUI đẹp hơn: hiệu ứng ô trồi lên, khối rơi, fragile vỡ, cầu, split, xoay / zoom camera, nút BFS / DFS / UCS / A\* / Manual. | Cần engine + solver của `huyhoang` mới chạy |
| `develop-refactor` | NHuy165 | Engine viết lại gọn hơn (`src/game/`): đủ fragile, cầu, 3 loại switch, split / ghép; loader **JSON**. Đã xóa `maps/` và GUI cũ. | Chưa có solver, chưa có màn JSON |
| `develop-solvers` | NHuy165 | Khung BFS / DFS / A\* tổng quát, chưa gắn engine. | Lỗi import (`Enum`), có thể bỏ |
| `docs` | Tran Trong Tu | Thư mục `docs/` và `CLAUDE.md`. | Chỉ tài liệu |

Chi tiết lỗi từng nhánh: [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).

## Quy trình đề xuất

- `main`: chỉ chứa bản **chạy được**, giống bản nộp và bản quay video.
- `develop`: nơi gộp công việc của mọi người.
- Nhánh con tạo từ `develop`, đặt tên theo loại việc: `feat/...` (tính năng), `fix/...` (sửa lỗi), `test/...` (unit test), `docs/...` (tài liệu).
- Gộp vào `develop` qua Pull Request, có ít nhất một người khác xem.
- Tới mốc ổn định (ví dụ trước khi quay video) thì gộp `develop` vào `main`.
- Không sửa nhánh của người khác khi chưa hỏi.

## Thứ tự gộp đề xuất

1. Chốt engine chính (quyết định U1 trong [`DECISIONS.md`](DECISIONS.md)).
2. Gộp engine + solver vào `develop`.
3. Gộp GUI (`gui/gui1`) vào `develop`, sửa import.
4. Gộp `docs` và unit test.
5. Benchmark, báo cáo, video, rồi gộp `develop` vào `main` để nộp.
