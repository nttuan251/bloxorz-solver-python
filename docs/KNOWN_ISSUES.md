# Lỗi đã biết

Danh sách lỗi và rủi ro theo từng nhánh, cập nhật ngày **2026-10-18** theo commit mới nhất trên GitHub. Mỗi lỗi nên được chuyển thành một unit test (đánh dấu `xfail` cho tới khi sửa xong); khi sửa, ghi commit sửa vào cột Trạng thái.

Mức độ: **Cao** = làm sai kết quả hoặc không chạy được; **TB** = sai trong một số trường hợp; **Thấp** = chất lượng code / tiện lợi. Các lỗi mức **Cao** có thêm phần **Nói đơn giản** cho người không trực tiếp viết code.

Cột **Kiểm chứng** cho biết lỗi được tìm bằng cách nào: **Chạy** = đã chạy code và thấy lỗi; **Đọc** = chỉ đọc code, chưa chạy.

Đây là danh sách để **cả nhóm cùng sửa**, không phải để chê code của ai. Code đang làm dở thì có lỗi là bình thường.

## Kết quả chạy thử (2026-10-18)

- `huyhoang`: BFS / DFS / UCS / A\* giải đúng **12/12 màn**, replay mọi lời giải đều tới đích; BFS, UCS, A\* cùng độ dài.
- `develop-refactor`: BFS / DFS / A\* giải đúng **33/33 màn JSON**, replay đều tới đích; BFS và A\* cùng độ dài.
- PR #5 (`integrate/engine-gui`, gộp `huyhoang` + `gui/gui1`): engine + solver qua đường import của GUI giải đúng 12/12 màn; GUI chạy offscreen trong WSL mở được cả 12 màn, A\* tự lăn tới đích ở `level12_split`.

## `origin/huyhoang` (commit `c06f49f`)

| # | Mức | File | Mô tả | Kiểm chứng | Trạng thái |
|---|---|---|---|---|---|
| H1 | Cao | `src/solvers/ucs.py`, `astar.py` | Kiểm tra goal khi **sinh** node, không phải khi **lấy ra** khỏi hàng đợi. Với cost 1 đều thì vẫn đúng, nhưng khi đổi sang cost không đều thì UCS/A\* có thể trả lời giải **không tối ưu**. **Nói đơn giản:** solver dừng lại ngay khi *nhìn thấy* đích, thay vì chắc chắn đó là đường rẻ nhất; khi mỗi bước có giá khác nhau, nó có thể chọn đường đắt hơn. | Đọc | Mở |
| H2 | Cao | `src/core/game.py` (`successors`) | Mọi action cost **1.0** cứng, nên UCS giống hệt BFS. Đề yêu cầu cost không đều có giải thích. **Nói đơn giản:** mọi nước đi đang "có giá" như nhau, nên UCS không khác gì BFS và phần UCS (10 điểm) mất ý nghĩa. | Chạy (UCS và BFS cùng số node, cùng độ dài trên cả 12 màn) | Mở |
| H3 | TB | `src/solvers/base.py` | `cost = len(actions)`, không phải tổng cost thật. Sẽ sai khi cost không đều. | Đọc | Mở |
| H4 | Cao | `src/solvers/heuristics.py` | Manhattan / 2 **không admissible** khi màn có split switch: một nước đi có thể teleport rất xa. Ở `level12_split` có **7 trạng thái** có h lớn hơn chi phí thật; tệ nhất là khối nằm dọc ở (1,2)–(2,2) ngay trên split switch: h = 6.5, chi phí thật = 4. **Nói đơn giản:** A\* "đoán" đường còn dài hơn thực tế, nên không còn được đảm bảo tìm đường ngắn nhất; báo cáo phải nói đúng điều này hoặc sửa heuristic. | Chạy (tính khoảng cách thật cho mọi trạng thái) | Mở |
| H5 | TB | `src/solvers/base.py` | Đo thời gian khi `tracemalloc` đang bật làm thời gian bị chậm hơn thực tế; trong GUI, peak memory gồm cả bộ nhớ của GUI. Cần script benchmark chạy riêng, không có GUI. | Đọc | Mở |
| H6 | Thấp | `src/core/loader.py` | Ký tự lạ trong map được coi là sàn, không báo lỗi. | Đọc | Mở |
| H7 | Thấp | `src/gui/game_state.py`, `block.py` | `game_state.py` không còn được dùng; `_pivot_for` có đoạn code thừa. | Đọc | Không còn trong PR #5 (GUI của nhánh này bị thay bằng GUI của Tuan) |

## `origin/develop-refactor` (commit `163a5ca`)

| # | Mức | File | Mô tả | Kiểm chứng | Trạng thái |
|---|---|---|---|---|---|
| R1 | Cao | `src/game/core/state.py` | `State` không có `__eq__` / `__hash__` nên `visited` không chặn được lặp. | Đọc | **Đã sửa** (`163a5ca` có `__eq__` / `__hash__` dựa trên key bất biến) |
| R2 | TB | `src/game/logic/engine.py` | `successors()` chỉ trả về `State`, không có action và cost. | Đọc | **Sửa một phần**: giờ trả `(action, state)`; cost do từng solver tự tính |
| R3 | TB | `src/game/core/level.py` | Ô bridge không có trong danh sách `bridges` của JSON bị coi là **đang mở** (`.get()` trả `None`). | Đọc | Mở |
| R4 | Thấp | `src/game/logic/level_loader.py` | Ký tự không nhận ra (kể cả lỗi gõ) bị bỏ qua và coi là ô trống, không báo lỗi; JSON chỉ được kiểm tra sơ bằng `assert`. | Đọc | Mở |
| R5 | Thấp | `src/game/main.py` | `main.py` rỗng, nhánh chưa có GUI (nhánh `develop-refactor-gui` vừa tạo, chưa có commit riêng). | Đọc | Mở (đã có 33 màn JSON) |
| R6 | TB | `src/solvers/core/*.py` | Solver **chưa đo** thời gian, peak memory, số node mở rộng; đề bắt buộc có. | Đọc | Mở |
| R7 | TB | `src/solvers/core/AStar.py` | Chưa có UCS riêng; cost và heuristic của A\* ghi `# TEMPORARY` (cost 1, h = 0), nên A\* hiện giống BFS. | Chạy (A\* và BFS cùng số trạng thái trên cả 33 màn) | Mở |
| R8 | Thấp | `state.py`, `Solver.py`, `AStar.py` | `State.__eq__` báo `TypeError` khi so sánh với thứ không phải `State` (ví dụ `state == None`); `solve()` trả `([], 0)` cho cả "không có lời giải" và "đứng sẵn ở đích"; `AStar(engine, level)` nhận tham số khác `BFS(engine)`. | Đọc | Mở |

## `origin/gui/gui1` (commit `9f68730`)

| # | Mức | File | Mô tả | Kiểm chứng | Trạng thái |
|---|---|---|---|---|---|
| G1 | Cao | `src/solvers/*.py` (sau khi gộp) | `main.py` import `src.solvers`, nhưng solver import `from core.game ...` nên báo `ModuleNotFoundError: No module named 'core'`. **Nói đơn giản:** GUI không mở được vì không tìm thấy engine. | Chạy | **Đã sửa trong PR #5** (`6373fdf`, đổi sang import tương đối) |
| G2 | TB | `src/gui/config.py` | Thiếu thư mục ảnh `assets/`. | Đọc | **Đã sửa** (`9f68730` thêm `src/gui/assets/`; PR #5 thêm ngoại lệ `.gitignore` cho ảnh này) |
| G3 | TB | `main.py` | Solver chạy trên luồng chính, không hiển thị peak memory. | Đọc | **Đã sửa** (`9f68730`) |
| G4 | TB | `main.py` | Không có nút Restart, cố định một màn. | Đọc | **Đã sửa** (`9f68730`: nút Restart, chọn màn) |
| G5 | Cao | `src/gui/controller.py` | Mở `maps/level_01.txt` … `level_33.txt` nhưng **không nhánh nào có file tên như vậy** (màn là `level01.txt` … `level12_split.txt`), nên game lỗi ngay khi mở. **Nói đơn giản:** GUI tìm sai tên file màn chơi. | Đọc (liệt kê file) | **Đã sửa trong PR #5** (`eac5f51`, tự liệt kê `maps/level*.txt`) |
| G6 | TB | `src/gui/controller.py` (`is_tile_solid`) | GUI tự kiểm tra lại sàn sau khi khối nhỏ di chuyển, tức là viết lại luật ngoài engine. Engine `huyhoang` kiểm tra sàn theo trạng thái cầu **cũ**, nên nếu switch vừa đóng cầu dưới khối nhỏ đứng yên, engine coi là hợp lệ mà GUI lại cho rơi. | Đọc | Mở |

## `origin/develop-solvers` (commit `9347df4`)

| # | Mức | File | Mô tả | Kiểm chứng | Trạng thái |
|---|---|---|---|---|---|
| S1 | Cao | `solvers/core/Action.py` | `class Action(Enum, str)` gây `TypeError` khi import. **Nói đơn giản:** chương trình báo lỗi ngay lúc khởi động. Sửa bằng cách đổi thành `(str, Enum)`. | Chạy (Python 3.13) | Mở |
| S2 | TB | `solvers/frontier/Queue.py`, `Stack.py` | `contains()` duyệt cả hàng đợi dù đã có `lookup_data` là `set`, làm BFS/DFS chậm bậc hai. | Đọc | Mở (bản mới trong `develop-refactor` đã làm đúng) |
| S3 | TB | cả nhánh | Không có UCS, không đo số liệu, không gắn với engine nào. Có thể bỏ nhánh này. | Đọc | Mở |

## Chung

| # | Mức | Mô tả | Kiểm chứng | Trạng thái |
|---|---|---|---|---|
| C1 | Cao | Chưa có gì được gộp vào `main` / `develop`; có **hai** engine luật chơi song song. **Nói đơn giản:** mỗi người đang làm trên bản riêng; cần chọn một bản chung để test, GUI và solver cùng dùng. | — | **Đang xử lý**: PR #5 gộp engine `huyhoang` + GUI của Tuan; vẫn còn engine của `develop-refactor` (quyết định U1) |
| C2 | TB | `README.md` rỗng ở mọi nhánh; `requirements.txt` chỉ có `ursina`, không ghim version. | — | Mở |
| C3 | TB | Chưa có unit test, chưa có script benchmark. | — | Mở |
