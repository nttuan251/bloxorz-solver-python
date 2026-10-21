# Câu hỏi chờ thầy trả lời

Bản nháp trong repo. **Câu hỏi thật được đăng lên Google Sheet của lớp** (link trong [`TEACHER_QA.md`](TEACHER_QA.md)). Mỗi câu có bối cảnh ngắn và **đáp án nhóm đề xuất**, để thầy chỉ cần xác nhận đúng/sai.

Khi thầy trả lời: chép câu trả lời vào `TEACHER_QA.md`, ghi quyết định vào [`DECISIONS.md`](DECISIONS.md), rồi đổi trạng thái ở đây thành **Đã trả lời**.

| # | Câu hỏi | Bối cảnh | Đề xuất của nhóm | Trạng thái |
|---|---|---|---|---|
| Q1 | Sau khi tách (split), một khối nhỏ 1×1×1 đi lên ô fragile thì ô có vỡ không? | Đề chỉ nói "khối **đứng** trên fragile thì vỡ", không nói về khối nhỏ. Hai bản engine của nhóm đang làm ngược nhau. | Khối nhỏ **làm vỡ** ô fragile (trọng lượng dồn vào 1 ô). | **Đã trả lời** (hỏi đáp câu 16, 2026-10-21): khối nhỏ **không** thua, tức là **không** làm vỡ ô fragile. Ngược với đề xuất của nhóm; engine `develop-refactor` đã làm đúng. Xem D9 trong `DECISIONS.md` |
| Q2 | Khi hai khối nhỏ ghép lại, soft switch mà khối **đứng yên** đang nằm lên có kích hoạt lại không? | Đề nói soft switch kích hoạt khi "bất kỳ phần nào" đè lên, nhưng không nói về lúc ghép. Với switch kiểu toggle, kích hoạt lại sẽ đóng/mở cầu lần nữa. | **Không** kích hoạt lại; chỉ khối vừa di chuyển mới kích hoạt switch. | Chưa hỏi |
| Q3 | Switch "permanent" đặt cầu cố định ở trạng thái **mở** hay **đóng**? | Đề chỉ ghi "set to a fixed state". | Mỗi switch permanent ghi rõ `open` hoặc `close` trong file màn chơi; cả hai đều được. | Chưa hỏi |
| Q4 | Hành động đổi khối điều khiển (phím Space) khi đang split có tính là một nước đi trong **solution length** và trong **cost** không? | Đề không nói rõ. Nó ảnh hưởng tới số liệu thực nghiệm. | **Có**, tính là 1 action, cost bằng 1 bước đi thường; ghi rõ trong báo cáo. | **Nhóm tự chốt** (2026-10-18): có tính, cost = 1. Không cần hỏi thầy. Xem D10 |
| Q5 | Hàm cost không đều do nhóm **tự thiết kế** (ví dụ đi lên ô fragile tốn hơn) kèm giải thích có đủ không, hay cần dữ liệu / ML để chứng minh? | Câu 10 của sheet cho phép dùng ML, nhưng chưa nói ML có bắt buộc không. | Tự thiết kế + lập luận trong báo cáo là **đủ**; ML không bắt buộc. | Gần như đã rõ: PDF mục 3.4 cho phép cost tự thiết kế có giải thích, câu 10 cho phép cả ML. Chỉ hỏi nếu nhóm muốn chắc chắn |
| Q6 | Nếu cầu bị đóng ngay dưới khối do chính nước đi đó kích hoạt switch, khối có rơi không? | Đề không nói thứ tự "di chuyển → kích hoạt switch → kiểm tra sàn". Hai bản engine của nhóm xử lý khác nhau. | Kiểm tra sàn **sau** khi cập nhật cầu: cầu đóng dưới khối thì khối rơi. | Chưa hỏi |

Câu Q2, Q6 cũng có thể tự kiểm chứng bằng cách chơi bản gốc trên Coolmath Games trước khi hỏi.

**Còn cần hỏi (cập nhật 2026-10-21):** Q2, Q3, Q6. Engine hiện tại đang làm: Q2 kích hoạt lại switch khi ghép, Q6 khối rơi.
