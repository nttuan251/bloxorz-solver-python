# Hỏi đáp với thầy

Nguồn: Google Sheet hỏi đáp của lớp
<https://docs.google.com/spreadsheets/d/1TnszUnuuSB9D9AaQElMcXMhnW2XBPEpmFX08W3t_evg/edit?gid=0#gid=0>

Chép lại ngày **2026-10-17** (13 câu). Câu trả lời của thầy được ưu tiên hơn cách hiểu từ PDF. Khi sheet có câu mới, cập nhật file này và ghi ngày.

| # | Câu hỏi (tóm tắt) | Thầy trả lời | Ảnh hưởng đến nhóm |
|---|---|---|---|
| 1 | Test case dùng nguồn có sẵn được không? | Được. | Được lấy màn chơi có sẵn, nhưng ghi nguồn trong References. |
| 2 | Số lượng test case? | Tối thiểu 10. | Cần ≥ 10 màn, phủ đủ: cơ bản, fragile, switch/bridge, split, kết hợp. |
| 3 | Báo cáo tiếng Anh hay tiếng Việt? | Tùy, nhưng thống nhất, không nửa Việt nửa Anh. | Chốt một ngôn ngữ cho `Report.pdf`. |
| 4 | Bấm Solve thì GUI hiện đáp án thế nào? | GUI tự cho khối lăn đến đích. | Cần chức năng replay lời giải trên GUI. |
| 5 | Dùng source code game có sẵn được không? | Được (nhớ cite đầy đủ). | Ghi nguồn mọi đoạn code lấy từ ngoài. |
| 6 | Tiêu chí GUI? | 3D. | Ursina (3D) đạt; Pygame/Tkinter (2D) không đạt. |
| 7 | GUI viết bằng ngôn ngữ khác được không? | Được, chỉ cần thuật toán bằng Python. | Solver + engine bắt buộc Python; GUI tùy chọn. |
| 8 | Lớp chưa có mô tả project. | Thầy đã đăng. | Không ảnh hưởng. |
| 9 | Cần thiết kế bao nhiêu màn chơi? | Tương ứng số test case ở câu 2. | ≥ 10 màn. |
| 10 | Dùng ML đơn giản để suy ra bộ trọng số cost cho UCS/A* có tính là justified không? | Được, trình bày rõ trong báo cáo. | Không bắt buộc ML; hàm cost tự thiết kế vẫn cần giải thích hợp lý. |
| 11 | "Fully observable": agent nhận đủ thông tin (switch toggle/permanent, switch nào điều khiển ô nào, vị trí teleport) hay phải tự khám phá? | Được cho agent nhận đầy đủ thông tin, không trừ điểm. | File màn chơi ghi sẵn mọi thông tin là đúng hướng. |
| 12 | Dùng Quick Bloxorz (JS) làm GUI, hoặc dùng AI code phần 3.1, solver tự code? | Giống câu 5: dùng được, nhớ cite. | Dùng AI phải khai báo trong Appendix ([`AI_USAGE.md`](AI_USAGE.md)). |
| 13 | Một bạn chưa có nhóm. | Gửi mail sinh viên cho thầy. | Không liên quan. |

Các câu nhóm đang muốn hỏi thêm: xem [`QUESTIONS_FOR_TEACHER.md`](QUESTIONS_FOR_TEACHER.md).
