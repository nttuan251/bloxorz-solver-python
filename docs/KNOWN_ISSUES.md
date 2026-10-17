# Lỗi đã biết

Danh sách lỗi và rủi ro tìm thấy khi **đọc code** (chưa chạy test) ngày **2026-10-17**, theo commit mới nhất của từng nhánh trên GitHub. Mỗi lỗi nên được chuyển thành một unit test (đánh dấu `xfail` cho tới khi sửa xong); khi sửa, ghi commit sửa vào cột Trạng thái.

Mức độ: **Cao** = làm sai kết quả hoặc không chạy được; **TB** = sai trong một số trường hợp; **Thấp** = chất lượng code / tiện lợi. Các lỗi mức **Cao** có thêm phần **Nói đơn giản** cho người không trực tiếp viết code.

Đây là danh sách để **cả nhóm cùng sửa**, không phải để chê code của ai. Code đang làm dở thì có lỗi là bình thường.

## `origin/huyhoang` (commit `c06f49f`)

| # | Mức | File | Mô tả | Trạng thái |
|---|---|---|---|---|
| H1 | Cao | `src/solvers/ucs.py`, `astar.py` | Kiểm tra goal khi **sinh** node, không phải khi **lấy ra** khỏi hàng đợi. Với cost 1 đều thì vẫn đúng, nhưng khi đổi sang cost không đều thì UCS/A\* có thể trả lời giải **không tối ưu**. **Nói đơn giản:** solver dừng lại ngay khi *nhìn thấy* đích, thay vì chắc chắn đó là đường rẻ nhất; khi mỗi bước có giá khác nhau, nó có thể chọn đường đắt hơn. | Mở |
| H2 | Cao | `src/core/game.py` (`successors`) | Mọi action cost **1.0** cứng, nên UCS giống hệt BFS. Đề yêu cầu cost không đều có giải thích. **Nói đơn giản:** mọi nước đi đang "có giá" như nhau, nên UCS không khác gì BFS và phần UCS (10 điểm) mất ý nghĩa. | Mở |
| H3 | TB | `src/solvers/base.py` | `cost = len(actions)`, không phải tổng cost thật. Sẽ sai khi cost không đều. | Mở |
| H4 | TB | `src/solvers/heuristics.py` | Manhattan / 2 có thể **overestimate** (không admissible) khi màn có split switch: một nước đi có thể teleport rất xa. Chưa kiểm chứng trên màn cụ thể. | Mở |
| H5 | TB | `src/solvers/base.py` | Đo thời gian khi `tracemalloc` đang bật làm thời gian bị chậm hơn thực tế; trong GUI, peak memory gồm cả bộ nhớ của GUI. Cần script benchmark chạy riêng, không có GUI. | Mở |
| H6 | Thấp | `src/core/loader.py` | Ký tự lạ trong map được coi là sàn, không báo lỗi. | Mở |
| H7 | Thấp | `src/gui/game_state.py`, `block.py` | `game_state.py` không còn được dùng; `_pivot_for` có đoạn code thừa "fix tuple shape". | Mở |

## `origin/develop-refactor` (commit `aa01c54`)

| # | Mức | File | Mô tả | Trạng thái |
|---|---|---|---|---|
| R1 | Cao | `src/game/core/state.py` | `State` **không có `__eq__` / `__hash__`** và chứa `dict` (trạng thái cầu). Hai state giống nhau vẫn bị coi là khác nhau, nên `visited` của BFS/DFS sẽ không chặn được lặp. Cần làm state bất biến, hashable (ví dụ `dataclass(frozen=True)` + `tuple`). **Nói đơn giản:** solver không nhận ra "mình đã đứng ở đây rồi", nên có thể đi vòng vòng mãi hoặc tốn rất nhiều bộ nhớ. | Mở |
| R2 | TB | `src/game/logic/engine.py` | `successors()` chỉ trả về danh sách `State`, không có action và cost; solver cần cả hai để dựng lại đường đi và tính cost. | Mở |
| R3 | TB | `src/game/core/level.py` | Ô bridge không có trong danh sách `bridges` của JSON bị coi là **đang mở** (`.get()` trả `None`). | Mở |
| R4 | Thấp | `src/game/logic/map_loader.py` | Ký tự không nhận ra (kể cả lỗi gõ) bị bỏ qua và coi là ô trống, không báo lỗi; JSON chỉ được kiểm tra sơ bằng `assert`. | Mở |
| R5 | Thấp | cả nhánh | Đã xóa `maps/` và GUI cũ, `src/game/main.py` rỗng, chưa có màn chơi JSON nào. | Mở |

Lỗi `Enum` sai thứ tự base class (`class Action(Enum, str)`) trong các bản trước của nhánh này **đã được sửa** ở `71ee2fe`.

## `origin/gui/gui1` (commit `44eea05`)

| # | Mức | File | Mô tả | Trạng thái |
|---|---|---|---|---|
| G1 | Cao | `main.py` | Import `src.core` và `src.solvers` nhưng nhánh này **không có** hai thư mục đó; chỉ chạy được khi gộp với `huyhoang`. Sau khi gộp, `src/solvers/base.py` import `from core.game ...` có thể lỗi vì `main.py` dùng `src.`. Chưa kiểm chứng. **Nói đơn giản:** GUI này đang mượn engine và solver của nhánh khác; tách riêng thì không chạy, ghép vào có thể cần sửa vài dòng import. | Mở |
| G2 | TB | `src/gui/config.py` | Dùng `./assets/Playstation_*.png` nhưng không có thư mục `assets/` trong repo (`.gitignore` đang chặn `*.png`). | Mở |
| G3 | TB | `main.py` | Solver chạy trên luồng chính nên cửa sổ đứng trong lúc giải; không hiển thị peak memory. | Mở |
| G4 | TB | `main.py` | Không có nút **New Game / Restart** (chỉ phím `R`), cố định màn `level07`, không chọn được màn khác. | Mở |

## `origin/develop-solvers` (commit `9347df4`)

| # | Mức | File | Mô tả | Trạng thái |
|---|---|---|---|---|
| S1 | Cao | `solvers/core/Action.py` | `class Action(Enum, str)` gây `TypeError` khi import (đã chạy thử với Python 3.13). **Nói đơn giản:** chương trình báo lỗi ngay lúc khởi động. Sửa bằng cách đổi thành `(str, Enum)`. | Mở |
| S2 | TB | `solvers/frontier/Queue.py`, `Stack.py` | `contains()` duyệt cả hàng đợi (`state in self.data`) dù đã có `lookup_data` là `set`, làm BFS/DFS chậm bậc hai. | Mở |
| S3 | TB | cả nhánh | Không có UCS, không đo số liệu, không gắn với engine nào. Có thể bỏ nhánh này nếu nhóm dùng solver của `huyhoang`. | Mở |

## Chung

| # | Mức | Mô tả | Trạng thái |
|---|---|---|---|
| C1 | Cao | Chưa có gì được gộp vào `main`; có **hai** engine luật chơi song song. **Nói đơn giản:** mỗi người đang làm trên bản riêng; cần chọn một bản chung để test, GUI và solver cùng dùng. | Mở |
| C2 | TB | `README.md` rỗng ở mọi nhánh; `requirements.txt` chỉ có `ursina`, không ghim version. | Mở |
| C3 | TB | Chưa có unit test, chưa có script benchmark. | Mở |
