# Quyết định thiết kế

Ghi lại các luật và quy ước mà **game engine, solver, GUI và unit test** cùng dựa vào. Test chỉ được viết theo những dòng **Đã chốt**; dòng **Chưa chốt** cần cả nhóm (hoặc thầy) quyết trước.

Mỗi khi chốt một dòng: ghi ngày, người chốt và lý do. Nếu do thầy trả lời thì dẫn số câu trong [`TEACHER_QA.md`](TEACHER_QA.md).

**Bối cảnh (cập nhật 2026-10-21).** "Engine" là phần code biết luật: nước đi nào hợp lệ, khi nào rơi, khi nào thắng, switch làm gì. Nhóm từng có hai bản engine:

- Nhánh **`huyhoang`** (Huy Hoang): bản đầu tiên, màn chơi dạng text.
- Nhánh **`develop-refactor`** / **`develop-refactor-gui`** (Huy, NHuy165): bản viết lại từ bản của Huy Hoang (Huy Hoang đồng ý trên Discord ngày 16/10), màn chơi dạng JSON, có GUI và solver chạy trên đó.

Nhóm đã chọn bản thứ hai (D8). Cột "Engine hiện tại" trong bảng "Chưa chốt" mô tả cách bản này đang làm. Chi tiết các nhánh: [`BRANCHES.md`](BRANCHES.md).

## Đã chốt

| # | Quyết định | Nguồn | Ngày |
|---|---|---|---|
| D1 | Tọa độ `(row, col)`, bắt đầu từ 0; row tăng xuống dưới, col tăng sang phải. | Cả hai bản engine đều dùng | 2026-10-17 |
| D2 | Agent / solver được nhận **đầy đủ thông tin** màn chơi (switch nào điều khiển cầu nào, toggle hay permanent, vị trí teleport). | Thầy, câu 11 | 2026-10-17 |
| D3 | Thuật toán và engine viết bằng **Python**; GUI phải **3D**, **bắt buộc có** (chấm qua video). | Thầy, câu 6, 7, 15 | 2026-10-21 |
| D4 | Có **tối thiểu 10 màn chơi**, dùng chung cho mọi solver. | Thầy, câu 2, 9 | 2026-10-17 |
| D5 | Bấm Solve thì GUI **replay** lời giải, khối tự lăn tới đích. | Thầy, câu 4 | 2026-10-17 |
| D6 | Chỉ khối 1×1×2 **đứng** trên goal mới thắng; khối nằm hoặc khối nhỏ trên goal không thắng. | PDF trang 3 | 2026-10-17 |
| D7 | GUI làm tiếp từ GUI của Tuan; GUI trong nhánh `huyhoang` chỉ là bản tạm. Huy đã viết lại GUI của Tuan cho khớp engine mới trên `develop-refactor-gui`. | Cả nhóm; Huy (Discord 18/10) | 2026-10-21 |
| D8 | **Engine chính là bản refactor của Huy** (`develop-refactor-gui`); màn chơi dạng **JSON** (33 màn trong `maps/level_XX.json`). | Discord 16/10 (Huy Hoang đồng ý cho Huy refactor, đồng ý chuyển sang JSON) | 2026-10-21 |
| D9 | **Khối nhỏ 1×1×1 đứng trên ô fragile không làm vỡ ô** (không thua). Chỉ khối 1×1×2 đứng trên fragile mới vỡ. | Thầy, câu 16 (trả lời Q1) | 2026-10-21 |
| D10 | **Đổi khối điều khiển (Space) khi đang tách tính là 1 nước đi**, có cost, và tính vào solution length. | Nhóm chốt (trả lời Q4) | 2026-10-18 |
| D11 | **Hàm cost `RISK_AWARE`**: lăn / di chuyển khối nhỏ = 1, đáp lên ô fragile = 2, đổi khối = 1. **UCS = A\* + `RISK_AWARE` + heuristic `TRIVIAL`.** | PR #6 (Trong Tu), Huy merge | 2026-10-19 |
| D12 | **Heuristic `TELEPORT_AWARE`** cho A\*: cận dưới số bước, tính cả đường qua split switch. Đã kiểm chứng admissible + consistent trên cả 33 màn. | PR #6 | 2026-10-19 |
| D13 | Chỉ số bộ nhớ của mọi solver là **peak memory**. | Thầy, câu 17 | 2026-10-21 |
| D14 | GUI 3D phải có **background** và **animation** (thiếu sẽ bị chấm thấp hơn). | Thầy, câu 18 | 2026-10-21 |
| D15 | Thí nghiệm đo **chỉ số thuật toán** trên các nhóm màn: dễ, có fragile, có split, kết hợp. | Thầy, câu 19 | 2026-10-21 |

## Chưa chốt

| # | Vấn đề | Engine hiện tại đang làm | Ghi chú |
|---|---|---|---|
| U4 | Ghép khối có kích hoạt lại soft switch dưới khối đứng yên không? | Có | Câu hỏi Q2 |
| U5 | Cầu đóng dưới khối do chính nước đi đó gây ra: khối có rơi không? | Có (kiểm tra lại sàn sau khi cập nhật cầu) | Câu hỏi Q6. Trong bình luận PR #4, Tuan gọi việc **khối nhỏ** không rơi khi cầu hạ xuống là lỗi; chưa ai nói về khối 1×1×2 nguyên vẹn |
| U6 | Sau khi split, hai khối nhỏ đáp xuống cạnh nhau có ghép ngay không? | Không, chờ tới nước đi kế tiếp | Cần ghi rõ trong báo cáo |
| U10 | DFS hay IDS? | DFS + visited, không đẩy lại trạng thái đang có trong stack | Nếu giữ DFS thì báo cáo mô tả đúng cách này |
| U11 | Python version chung của nhóm | — | Ghi vào `README.md` và `CLAUDE.md` |
| U12 | Ngôn ngữ báo cáo (Việt hay Anh) | — | Thầy chỉ yêu cầu thống nhất (câu 3) |
| U13 | Switch "permanent" đặt cầu mở hay đóng? | Mỗi switch ghi rõ `PERMANENT_OPEN` / `PERMANENT_CLOSE` trong file màn | Câu hỏi Q3 |

Các mục U1, U2, U3, U7, U8, U9 cũ đã chuyển thành D8, D8, D9, D10, D11, D12.
