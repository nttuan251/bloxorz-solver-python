# Đề xuất cải tiến

Ý kiến để cả nhóm thảo luận, **chưa phải quyết định**. Khi nhóm đồng ý một đề xuất, ghi vào [`DECISIONS.md`](DECISIONS.md) và đổi trạng thái ở đây.

| # | Đề xuất | Lý do | Ưu tiên | Trạng thái |
|---|---|---|---|---|
| P1 | Chọn **một** engine luật chơi rồi gộp vào `develop`. Hướng nhanh nhất: lấy `huyhoang` (đủ luật + solver + đo số liệu) làm nền, ghép GUI của `gui/gui1`; cân nhắc mang các phần viết gọn của `develop-refactor` (JSON loader, cấu trúc class) vào sau. | Hai engine song song làm test, GUI, solver không biết bám vào đâu. | Rất cao | Chờ nhóm |
| P2 | Thiết kế **hàm cost không đều** cho UCS / A\*, ví dụ: bước thường = 1, đáp lên ô fragile = 2, đổi khối (Space) = 1. Giữ mọi cost ≥ 1 để heuristic Manhattan / 2 vẫn là cận dưới. | Đề yêu cầu (UCS với cost 1 chỉ là BFS). | Cao | Chờ nhóm |
| P3 | Đưa goal test của UCS / A\* về lúc **lấy node ra** khỏi hàng đợi; tính `cost` bằng tổng cost thật. | Giữ tối ưu khi cost không đều (lỗi H1, H3). | Cao | Chờ nhóm |
| P4 | Xử lý teleport trong heuristic: với màn có split switch, lấy `min(khoảng cách trực tiếp, khoảng cách tới split switch + khoảng cách từ điểm teleport tới goal)`, hoặc dùng `h = 0` cho màn đó nếu chưa chứng minh được. | Tránh overestimate (lỗi H4); báo cáo cần lập luận admissible. | Cao | Chờ nhóm |
| P5 | Viết **unit test** bằng `pytest` cho engine trước: 12 cặp (tư thế, hướng), rơi, thắng, fragile, cầu, switch, split / ghép, loader; sau đó test solver (BFS và A\* cùng độ dài lời giải; replay lời giải phải tới goal). | Đề khuyên test bảng chuyển trạng thái sớm; phát hiện lỗi khi gộp nhánh. | Cao | Đang làm |
| P6 | Viết **script benchmark** chạy không cần GUI: chạy 4 solver trên ≥ 10 màn, xuất CSV, vẽ biểu đồ bằng `matplotlib`. | Số liệu cho phần Experiments (20 điểm); tránh sai số do GUI. | Cao | Chờ nhóm |
| P7 | Thêm màn chơi cho đủ ≥ 10 và phủ các nhóm: cơ bản, fragile, switch/bridge, split, kết hợp. Ghi nguồn nếu lấy từ game gốc. | Thầy yêu cầu tối thiểu 10 (câu 2). | Cao | Chờ nhóm |
| P8 | Ghim version trong `requirements.txt` (ví dụ `ursina==8.3.0`, `panda3d==1.10.16`) và ghi Python version vào `README.md`. | Mọi người cài giống nhau. | TB | Chờ nhóm |
| P9 | Viết `README.md` gốc: cài đặt (gồm cách chạy qua WSL nếu Windows chặn Panda3D), chạy game, chạy test, chạy benchmark. | Đề bắt buộc có README hướng dẫn chạy. | TB | Chờ nhóm |
| P10 | Trên GUI: thêm nút **New Game / Restart**, chọn màn, chạy solver ở luồng phụ, hiển thị cả peak memory. | Đề và video yêu cầu các nút này (lỗi G3, G4). | TB | Chờ nhóm |
| P11 | Đưa ảnh asset vào repo (bỏ chặn `*.png` cho thư mục `assets/`, giữ chặn ảnh benchmark). | Lỗi G2. | TB | Chờ nhóm |
| P12 | Bỏ nhánh `develop-solvers` sau khi solver của `huyhoang` được gộp. | Trùng chức năng, có lỗi import (S1). | Thấp | Chờ nhóm |
