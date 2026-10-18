# Các nhánh và quy trình làm việc

## Tình trạng các nhánh (cập nhật 2026-10-18)

| Nhánh | Người làm | Nội dung | Ghi chú |
|---|---|---|---|
| `main` | Nguyen Thanh Tuan | Commit đầu tiên: GUI Ursina tối giản (bàn 3×3 cố định), 9 màn text. Chưa có luật rơi / thắng, chưa có solver. | Chưa gộp nhánh nào |
| `develop` | — | Giống hệt `main`. | Nhánh gộp; PR #3, #4, #5 đều nhắm vào đây |
| `huyhoang` | Huy Hoang | Engine đầy đủ (`src/core/`: fragile, cầu, 3 loại switch, split / ghép), 4 solver BFS / DFS / UCS / A\* có đo số liệu (`src/solvers/`), GUI tạm, spec map `maps/MAP_FORMAT.txt`, 3 màn đặc biệt. | PR #3. GUI tạm bỏ đi (D7) |
| `gui/gui1` | Nguyen Thanh Tuan | **GUI chính** (D7): hiệu ứng ô trồi lên, khối rơi, fragile vỡ, cầu, split, xoay / zoom camera, HUD, bảng hướng dẫn, chọn màn, nút Restart và BFS / DFS / UCS / A\*. | PR #4. Cần engine + solver của `huyhoang` mới chạy |
| `integrate/engine-gui` | Tran Trong Tu | Gộp `huyhoang` + `gui/gui1`, giữ GUI của Tuan, sửa lỗi import (G1) và tên file màn (G5). Đã chạy thử. | **PR #5**. Nếu gộp thì có thể đóng PR #3, #4 |
| `develop-refactor` | NHuy165 | Engine viết lại gọn hơn (`src/game/`), đủ luật; loader **JSON** với **33 màn**; BFS / DFS / A\* (cost, heuristic còn tạm). Đã xóa GUI cũ. | Chưa đo số liệu, chưa có GUI |
| `develop-refactor-gui` | NHuy165 | Trùng commit với `develop-refactor`. | Có lẽ để làm GUI trên engine mới |
| `develop-solvers` | NHuy165 | Khung BFS / DFS / A\* tổng quát, chưa gắn engine. | Lỗi import (`Enum`), có thể bỏ |
| `docs` | Tran Trong Tu | Thư mục `docs/` và `CLAUDE.md`. | Chỉ tài liệu |

## Pull Request đang mở

| PR | Nhánh → đích | Người tạo | Ghi chú |
|---|---|---|---|
| #3 | `huyhoang` → `develop` | Huy Hoang | Engine + solver + GUI tạm |
| #4 | `gui/gui1` → `develop` | Nguyen Thanh Tuan | GUI chính; xung đột với #3 trong `src/gui/` |
| #5 | `integrate/engine-gui` → `develop` | Tran Trong Tu | Gộp #3 + #4, đã giải quyết xung đột và sửa lỗi; thay thế cho #3 và #4 |

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
