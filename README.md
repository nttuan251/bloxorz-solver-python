# Bloxorz Solver (Python)

Mã nguồn cho đồ án **Cơ sở trí tuệ nhân tạo**: game Bloxorz (cơ học của khối 1×1×2,
công tắc mở/đóng cầu, tách/khớp 2 khối lập phương) cùng bộ giải AI
**DFS, BFS, UCS (Uniform Cost Search) và A\*** so sánh trên 33 map
(thống kê số bước, chi phí đường đi, số node mở rộng, thời gian, bộ nhớ đỉnh).

Khối game và mọi thuật toán tìm kiếm đều viết bằng Python. Phần đồ hoạ web
(three.js) chỉ vẽ: mỗi lần di chuyển/kiếm giải được gửi về server Python chạy
trong `src/`, rồi trả về trình duyệt. three.js r160 nằm sẵn trong
`web/static/vendor/` nên **chạy offline hoàn toàn**.

## Yêu cầu

- Python **3.10 trở lên** (kiểm tra: `python --version`).
- Không cần cài thư viện nào: dự án chỉ dùng **standard library**.
  (`pip install -r requirements.txt` sẽ chạy thành công và không cài gì thêm.)
- Trình duyệt thường (Chrome/Edge/Firefox) để chơi web GUI.

## Cách chạy mã nguồn

Toàn bộ lệnh dưới đây chạy **từ thư mục gốc của repo** (nơi chứa thư mục `src/`, `web/`).

### 1. Web GUI (khuyến nghị)

```
python -m web.server
```

Server chạy tại `http://127.0.0.1:8000` và tự mở trong trình duyệt. Bấm `Ctrl+C` trong
terminal để dừng.

Tuỳ chọn:

```
python -m web.server --port 9000          # đổi cổng
python -m web.server --host 0.0.0.0       # cho máy khác trong LAN truy cập
python -m web.server --no-browser         # không tự mở tab trình duyệt
```

### 2. Điều khiển trong game

| Phím | Chức năng |
| --- | --- |
| Mũi tên hoặc W A S D | Lăn khối |
| Space | Đổi điều khiển giữa 2 khối (sau khi tách) |
| R | chơi lại màn hiện tại |
| N | chọn màn |
| H | bảng hướng dẫn trò chơi |
| C | đặt lại camera |
| T | đổi giao diện (Aurora / Dusk) |
| Kéo chuột / lăn chuột | xoay camera / zoom |

Xong màn sẽ bắn pháo hoa và tự sang màn tiếp theo.

### 3. Panel giải thuật (bên phải màn chơi)

- Chọn **BFS**, **DFS**, **UCS** hoặc **A\***, chọn thêm *cost*
  (UNIFORM / RISK_AWARE / SWITCH_FRIENDLY / SPLIT_AWARE) và *heuristic*
  (TELEPORT_AWARE / GRID_DISTANCE / RELAXED_BLOCK) khi dùng A\*.
- Bấm nút để giải: game tự phát lại từng bước, hiển thị **số bước, chi phí
  đường đi, số node mở rộng, thời gian, bộ nhớ đỉnh**.
- "Show explored tiles" tô màu ô theo số lần state đã mở rộng đụng tới
  (heatmap). "Compare all" chạy cả 4 giải thuật so cạnh nhau.

### 4. Chạy test

```
python -m unittest discover tests
```

Bộ test bao gồm: test engine (game logic) trong `tests/`, test API web trong
`tests/web_tests/` và một script kiểm chứng heuristic (xem mục 5).

### 5. Chạy benchmark / kiểm chứng heuristic (tuỳ chọn, chạy lâu)

Benchmark tất cả giải thuật trên các nhóm map:

```
python -m tests.algorithm_tests.main
```

Mặc định hàm chạy cuối file là `test_cost_comparison_on_all_groups()`; bỏ chú
thích (uncomment) các hàm khác ở cuối `tests/algorithm_tests/main.py` để chọn
nhóm thí nghiệm khác (baseline, so sánh heuristic, so sánh cost). Nhóm map lớn
(Level 29–33) có thể chạy rất lâu với DFS/BFS.

Kiểm chứng heuristic (admissible, consistent, tối ưu) trên mọi level:

```
python -m tests.heuristic_tests.verify_heuristics
python -m tests.heuristic_tests.verify_heuristics --maps "maps/level_0*.json" --csv results.csv
```

## Cấu trúc dự án

```
bloxorz-solver-python/
├── src/
│   ├── game/
│   │   ├── core/        # Block, State, Tile, Switch, Action, Coordinate, Level
│   │   └── logic/       # engine, state_mover, switch_manager, level_loader, ...
│   └── solver_algorithms/
│       ├── solvers/     # BFS, DFS, A*, solver_factory
│       ├── cost/        # các hàm chi phí (UCS, RISK_AWARE, ...)
│       ├── heuristic/   # các heuristic (TELEPORT_AWARE, GRID_DISTANCE, ...)
│       ├── frontiers/   # Queue, Stack, PQueue (priority queue)
│       └── core/        # enum SolverType, CostCalculatorType, HeuristicCalculatorType
├── web/
│   ├── server.py        # HTTP server (standard library) + mở trình duyệt
│   ├── api.py           # bọc engine và bộ giải thành REST API JSON cho trang web
│   └── static/          # front-end three.js (vẽ game, HUD, heatmap)
├── maps/                # 33 level (level_01.json ... level_33.json)
├── tests/               # unit tests + benchmark + verify heuristic
└── requirements.txt     # không khai báo thư viện nào (chỉ dùng standard library)
```

Giao tiếp giữa trình duyệt và Python:

```
trình duyệt (web/static)                Python (web/server.py -> web/api.py -> src/)
three.js, HUD, animation        <->     GET  /api/levels, /api/levels/<id>, /api/options
                                        POST /api/step   {level, state, action}
                                        POST /api/solve  {level, solver, cost, heuristic}
```

## Thêm / sửa map

Level là file JSON trong `maps/` đặt tên `level_XX.json` (XX là số) để tự động
hiện trong GUI và trong benchmark. Ví dụ `maps/level_10.json`:

```json
{
	"map": [
		"---------------",
		"-------------h-",
		"------ooo--ooo-",
		"------ohooooob-",
		"----ooooo--oo--",
		"----oTob---oo--",
		"--ooooo---oooo-",
		"-ooSo-----oooo-",
		"-oooo--ooooo---",
		"------ooo------",
		"------ooo------",
		"---------------"
	],
	"bridges": [
		{"position": [3, 13], "initial_state": false},
		{"position": [5, 7], "initial_state": false}
	],
	"switches": [
		{"position": [1, 13], "coords_and_actions": [[[5, 7], "TOGGLE"]]},
		{"position": [3, 7], "coords_and_actions": [[[3, 13], "TOGGLE"]]}
	]
}
```

Ký hiệu trong `"map"` (các hàng từ trên xuống là **row 0, 1, 2...**, các cột từ
trái sang là **col 0, 1, 2...**):

| Ký hiệu | Loại ô | Hành vi trên khối |
| --- | --- | --- |
| `o` hoặc `.` | NORMAL | Ô thường, khối đứng/lăn bình thường |
| `-` | (không có ô) | Khoảng trống: khối rơi nếu lăn vào |
| `S` | START | Vị trí xuất phát khối (đứng tại đây khi bắt đầu) |
| `T` | GOAL | Ô đích: khối **đứng** đúng tại đây là thắng |
| `f` | FRAGILE | Khối chỉ có thể lăn qua; **đứng** trên ô là gãy |
| `b` | BRIDGE | Cầu; mở hoặc đóng theo công tắc (khai báo trong `bridges`) |
| `s` | SOFT_SWITCH | Công tắc thường: khối lăn/nằm trên nó là kích hoạt |
| `h` | HEAVY_SWITCH | Công tắc nặng: khối **đứng** trên nó mới kích hoạt |
| `p` | SPLIT_SWITCH | Công tắc tách/khớp: khối **đứng** trên nó sẽ tách thành 2 cube |

Lưu ý khi viết map:

- Mỗi ô `s`/`h`/`p` phải khớp một phần tử trong `"switches"` với `"position"`
  `[row, col]` đúng như ký hiệu trên map.
- Mỗi ô `b` phải khớp một phần tử trong `"bridges"`, `initial_state` cho biết cầu
  mở (`true`) hay đóng (`false`) lúc bắt đầu.
- `"coords_and_actions"` là danh sách `[ [row, col], "ACTION" ]` chỉ định công
  tắc làm gì với ô cầu nào: `TOGGLE` (đổi trạng thái), `PERMANENT_OPEN`,
  `PERMANENT_CLOSE` (mở/đóng vĩnh viễn), hoặc với công tắc `p` chúng là **hai vị
  trí** `[row, col]` của 2 cube sau khi tách (không phải ô cầu).
- Các hàng trong `"map"` có thể dài khác nhau; ô nào không được ghi trong chuỗi
  được coi là không tồn tại (không đi được).
