# Quyết định thiết kế

Ghi lại các luật và quy ước mà **game engine, solver, GUI và unit test** cùng dựa vào. Test chỉ được viết theo những dòng **Đã chốt**; dòng **Chưa chốt** cần cả nhóm (hoặc thầy) quyết trước.

Mỗi khi chốt một dòng: ghi ngày, người chốt và lý do. Nếu do thầy trả lời thì dẫn số câu trong [`TEACHER_QA.md`](TEACHER_QA.md).

**Bối cảnh: nhóm đang có hai bản engine luật chơi.** "Engine" là phần code biết luật: nước đi nào hợp lệ, khi nào rơi, khi nào thắng, switch làm gì.

- Nhánh **`huyhoang`** (Huy Hoang): bản đầy đủ nhất, đã có cả 4 solver và GUI chạy trên nó. Màn chơi dạng file text.
- Nhánh **`develop-refactor`** (NHuy165): bản viết lại cho gọn, cũng đủ các loại ô đặc biệt nhưng chưa có solver. Màn chơi dạng JSON.

Hai bản xử lý một số tình huống khác nhau, nên bảng "Chưa chốt" bên dưới có hai cột để so sánh. Chi tiết các nhánh: [`BRANCHES.md`](BRANCHES.md).

## Đã chốt

| # | Quyết định | Nguồn | Ngày |
|---|---|---|---|
| D1 | Tọa độ `(row, col)`, bắt đầu từ 0; row tăng xuống dưới, col tăng sang phải. | Cả hai bản engine đều dùng | 2026-10-17 |
| D2 | Agent / solver được nhận **đầy đủ thông tin** màn chơi (switch nào điều khiển cầu nào, toggle hay permanent, vị trí teleport). | Thầy, câu 11 | 2026-10-17 |
| D3 | Thuật toán và engine viết bằng **Python**; GUI phải **3D**. | Thầy, câu 6, 7 | 2026-10-17 |
| D4 | Có **tối thiểu 10 màn chơi**, dùng chung cho mọi solver. | Thầy, câu 2, 9 | 2026-10-17 |
| D5 | Bấm Solve thì GUI **replay** lời giải, khối tự lăn tới đích. | Thầy, câu 4 | 2026-10-17 |
| D6 | Chỉ khối 1×1×2 **đứng** trên goal mới thắng; khối nằm hoặc khối nhỏ trên goal không thắng. | PDF trang 3 | 2026-10-17 |
| D7 | **GUI chính là của Tuan** (nhánh `gui/gui1`). GUI trong nhánh `huyhoang` chỉ là bản tạm để thử engine, bỏ đi khi gộp. | Cả nhóm thống nhất; thực hiện trong PR #5 | 2026-10-18 |

## Chưa chốt

| # | Vấn đề | `huyhoang` đang làm | `develop-refactor` đang làm | Ghi chú |
|---|---|---|---|---|
| U1 | **Dùng engine nào** làm engine chính? | Đầy đủ luật + 4 solver có đo số liệu; GUI của Tuan đang chạy trên bản này (PR #5) | Code gọn, đủ luật, có BFS / DFS / A\* (cost, heuristic còn tạm), chưa đo số liệu | Quyết định quan trọng nhất; xem [`BRANCHES.md`](BRANCHES.md) |
| U2 | Định dạng file màn chơi: text hay JSON? | Text (grid + `[BRIDGES]`/`[SWITCHES]`), spec trong `maps/MAP_FORMAT.txt`; 12 màn | JSON (`map`, `bridges`, `switches`); **33 màn** | Đề cho phép cả hai |
| U3 | Khối nhỏ trên ô fragile có làm vỡ không? | Có (vỡ) | Không (an toàn) | Câu hỏi Q1 cho thầy |
| U4 | Ghép khối có kích hoạt lại soft switch dưới khối đứng yên không? | Có | Có | Câu hỏi Q2 |
| U5 | Cầu đóng dưới khối do chính nước đi đó gây ra: khối có rơi không? | Không (kiểm tra sàn với cầu **cũ**) | Có (kiểm tra lại sau khi cập nhật cầu) | Câu hỏi Q6 |
| U6 | Sau khi split, hai khối nhỏ đáp xuống cạnh nhau có ghép ngay không? | Không, chờ tới nước đi kế tiếp | Không (ghi chú trong code) | Hai bản giống nhau; cần ghi rõ trong báo cáo |
| U7 | Đổi khối điều khiển (Space) có tính là 1 bước và cost 1 không? | Có (action `SWITCH`, cost 1) | Là action `SWITCH_CONTROL`, chưa có cost | Câu hỏi Q4 |
| U8 | **Hàm cost cho UCS / A\*** | Mọi action cost 1 (UCS = BFS) | Chưa có | Đề muốn cost **không đều** và có giải thích; câu hỏi Q5 |
| U9 | Heuristic cho A\* và cách xử lý teleport của split switch | Manhattan / 2, +0.5 khi nằm | Chưa có | Có thể overestimate khi có teleport; xem [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) |
| U10 | DFS hay IDS? | DFS + visited | Chưa có | Nếu đổi sang IDS phải ghi rõ trong báo cáo |
| U11 | Python version chung của nhóm | — | — | Ghi vào `README.md` và `CLAUDE.md` |
| U12 | Ngôn ngữ báo cáo (Việt hay Anh) | — | — | Thầy chỉ yêu cầu thống nhất (câu 3) |
