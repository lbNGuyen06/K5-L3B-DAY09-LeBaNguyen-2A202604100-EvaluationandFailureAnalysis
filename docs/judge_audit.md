# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (backend replay, nhãn judge lưu sẵn trong CSV; FAIL = lớp dương).

| Tiêu chí | n | κ | Precision | Recall | Confusion (tp/fp/fn/tn) | Fail rate quan sát → Rogan-Gladen | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|---|
| tone_ok | 100 | **0.757** | **0.857** | **0.800** | 24 / 4 / 6 / 66 | 0.28 → 0.30 | ✅ PASS (exit 0) | **dùng** (non-blocking, xem Kết luận) |
| helpful | 100 | **0.375** | 1.000 | **0.300** | 9 / 0 / 21 / 70 | 0.09 → 0.30 | ❌ FAIL (exit 1): κ và R dưới sàn | **loại**, không dùng làm gate |

## ≥5 case audit thủ công

Đã đọc toàn bộ 10 bất đồng của `tone` và 21 bất đồng của `helpful`. Dưới đây là các case đại diện cho từng kiểu lỗi.

### tone_ok (10 bất đồng: 6 FN, 4 FP)

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | **Người** | Judge nhầm suồng sã với thân thiện. **Rubric:** bắt buộc xưng "LogiX" và gọi khách "anh/chị"; xưng "em", gọi "bạn", kết câu "nha/nhé" là FAIL. Cùng lỗi: H-017 ("bạn ơi … rồi nha"). |
| 2 | H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | **Người** | Judge chỉ bắt từ khóa lịch sự ("Dạ, vui lòng"). **Rubric:** từ lịch sự không bù cho nội dung ra lệnh hoặc gạt khách ("không cần nhắn thêm"); chấm theo ý cả câu, kèm 1 ví dụ FAIL như vậy trong few-shot. |
| 3 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | **Người** | Judge phạt vì "thiếu xin lỗi". **Rubric:** xin lỗi *không bắt buộc* khi kết quả có lợi cho khách; ngắn gọn, đủ ý là PASS. |
| 4 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | **Người** | CS LogiX cho phép từ "refund". **Rubric:** thêm danh sách từ mượn được phép (refund, ship, voucher…); không phạt chỉ vì có từ tiếng Anh. |
| 5 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** | Ghi chú dữ liệu: người đọc nhầm ticket nên nhãn sai. **Hành động:** sửa nhãn người thành FAIL trong bản nhãn tiếp theo (không sửa replay công khai). Nếu sửa: tp 25 / fp 3, P 0.893, R 0.806, κ 0.784. Bài học: nhãn người cũng cần được audit, không mặc định đúng. |
| 6 | H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | **Người**, nhưng **sai tiêu chí** | Giọng văn ổn; lỗi thật là *hứa ngoài kết quả hệ thống*, một lỗi sự thật/chính sách. **Rubric:** loại khỏi phạm vi tone; chuyển sang grader code (reply không được nêu cam kết tiền ngoài ledger, cùng họ FM-08). |
| 7 | H-070 "… cho đơn O-909 ạ 😂😂" | PASS | FAIL | **Người** | **Rubric:** cấm emoji trong phản hồi khiếu nại. Cùng nhóm "không chuyên nghiệp": H-094 (mất dấu tiếng Việt "Da, LogiX da hoan…"), cần quy định "bắt buộc đủ dấu". |
| 8 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ …" | FAIL | PASS | **Người** (sát ranh giới) | Lặp "Dạ" là lỗi gõ, không phải thái độ. **Rubric:** lỗi chính tả/gõ nhỏ không làm FAIL tone trừ khi gây hiểu sai hoặc thiếu tôn trọng. |

**Quy luật tone:** FN (6) do judge **quá dễ dãi với giọng thân mật hoặc thiếu chuyên nghiệp** khi có từ lịch sự bề mặt; FP (4) do judge **áp quy tắc cứng** (bắt xin lỗi, cấm tiếng Anh, bắt lỗi gõ). Cả hai đều sửa được bằng rubric cụ thể hơn và few-shot ví dụ biên.

### helpful (21 bất đồng, **tất cả là FN**: người FAIL, judge PASS)

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 9 | HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (ledger 40.000đ) | PASS | FAIL | **Người** | Reply trông hoàn hảo nhưng **nói sai số tiền so với ledger** (FM-08). Judge chỉ thấy văn bản, không thấy ledger, nên **về cấu trúc không thể** bắt được. 18/21 FN thuộc loại này (HL-015, 020, 062, 087, 100 …). **Hành động:** không sửa rubric; đưa kiểm tra số tiền ra khỏi judge sang grader code `reply_matches_ledger`. |
| 10 | HL-016 "Dạ, LogiX thành thật xin lỗi … LogiX đã hoàn 55.000đ cho đơn O-404. Một lần nữa LogiX xin lỗi …" (ledger 35.000đ) | PASS | FAIL | **Người** | Ngoài sai tiền còn có **thiên vị độ dài/xin lỗi (verbosity bias)**: 13/18 reply sai tiền được độn bằng câu xin lỗi lặp lại và đều qua judge. **Rubric:** chấm "hữu ích" theo thông tin hành động được (số tiền, mã đơn, thời hạn, bước tiếp theo); câu xin lỗi lặp lại không cộng điểm, lặp nguyên câu là dấu hiệu FAIL. |
| 11 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | **Người** | Không nói *xử lý thế nào*, không số tiền, không thời hạn: khách không biết được hoàn hay không. Cùng lỗi: HL-091, HL-097. **Rubric:** reply phải nêu rõ kết quả (hoàn bao nhiêu / từ chối vì sao / cần thêm gì); "đã xử lý" chung chung là FAIL. |

**Quy luật helpful:** judge chỉ bắt được reply **rỗng một cách hiển nhiên** (9 TP: "Cảm ơn bạn đã liên hệ…", "Bạn gửi lại thông tin đi.", "Đơn O-909 không được hoàn."). Nó bỏ sót 21/30 reply tệ, chia làm 3 nhóm: 18 sai số tiền so với ledger (13 trong đó được độn xin lỗi), và 3 mơ hồ.

## Kết luận

**helpful: LOẠI, không được dùng làm gate.**
- Ma trận nhầm lẫn: tp 9, fp 0, **fn 21**, tn 70. Recall 0.30: judge bỏ sót **70% reply tệ**. κ 0.375 < 0.6.
- **Precision 1.0 là cái bẫy:** judge không bao giờ báo nhầm vì gần như không bao giờ báo FAIL (9/100). Một gate dùng judge này sẽ "xanh" trên hầu hết regression.
- Rogan-Gladen: tỉ lệ fail quan sát 9% → hiệu chỉnh **30%**. Judge che mất khoảng 2/3 số lỗi thật; dashboard dựa vào nó sẽ báo chất lượng tốt gấp 3 lần thực tế.
- Nguyên nhân gốc: 18/21 FN là lỗi **số tiền sai so với ledger**. Đây là việc của code (quy tắc "tiền và approval luôn chấm bằng code"), không phải của judge. Kiểm tra lại: bỏ 18 dòng đó (n=82) thì judge còn tp 9 / fp 0 / fn 3 / tn 70, R 0.75, κ 0.837, tức là **qua sàn**. Hướng sửa vì vậy là **chia trách nhiệm**: grader code `reply_matches_ledger` (M3, FM-08) chấm số tiền; judge helpful chỉ chấm độ đầy đủ/rõ ràng với rubric mới. Phải calibrate lại trên nhãn mới trước khi dùng, vì con số 0.837 tính trên chính dữ liệu đã dùng để chẩn đoán nên lạc quan.

**tone: DÙNG được**, nhưng chỉ là metric **non-blocking** (báo cáo, cảnh báo), vì:
- Qua sàn với biên mỏng: R 0.80 (sàn 0.7), P 0.857 (sàn 0.8); 4 FP nghĩa là cứ 7 lần judge FAIL thì 1 lần chặn nhầm.
- Rogan-Gladen 0.28 → 0.30: sai số nhỏ, ước lượng tỉ lệ lỗi giọng văn đáng tin ở mức tổng.
- Ít nhất 1 nhãn người sai (H-081); 1 case nằm sai tiêu chí (H-063). Áp các sửa rubric ở trên rồi calibrate lại trước khi cân nhắc cho tone quyền blocking.

**Rủi ro còn lại**
- Judge chỉ được kiểm trên dữ liệu **replay đã công khai**; mọi sửa rubric ở trên đều suy ra từ chính 100 dòng này. Cần **nhãn người mới (held-out)** để đo lại κ/P/R một cách trung thực.
- Replay cố định nên không đo được **độ dao động của judge thật** (cùng reply, nhiều lần gọi có thể ra phán quyết khác); cần chạy lặp với LLM thật.
- n = 100 với 30 FAIL: khoảng tin cậy của recall rộng (mỗi FN thay đổi R khoảng 0.033); tone chỉ cần thêm 3 FN là rớt sàn recall.
- Nhãn người có lỗi (H-081): cần ≥ 2 người gán nhãn độc lập và đo κ giữa người với người để biết trần đồng thuận thực tế.
