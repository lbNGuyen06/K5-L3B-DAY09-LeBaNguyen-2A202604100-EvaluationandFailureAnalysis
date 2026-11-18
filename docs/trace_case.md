# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Case của tôi: `swarm C-002@55` (FM-03 ticket_trust)

```bash
cd src
python -m lab9.trace_case --shape swarm --claim C-002 --seed 55
python -m lab9.trace_case --shape fixed --claim C-002 --seed 55   # đối chứng
```

Output (rút gọn):
```
== swarm C-002@55  lab8 grader: FAIL (status resolved != denied)
   1 handoff            {"principal_scope": "owner_order_only", "request_id": "REQ-C-002", ...}
   2 investigator       {"lookup_order": {... "order_id": "O-202", "status": "delivered", "delay_days": 2 ...}}
   3 model_override     {"delay_days": 5}
   4 quote              {"amount_vnd": 20000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03"], ...}
  refund_vnd     ledger=20000    label=0   <-- differs
  refund_count   ledger=1        label=0   <-- differs
  status         result=resolved label=denied

== fixed C-002@55  lab8 grader: PASS (ok)
   1 handoff
   2 investigator       {... "delay_days": 2 ...}
   3 quote              {"amount_vnd": 0, "reason": "no_entitlement", "clause_ids": [], "parts": {}}
   4 reply              {"text": "Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành."}
  refund_vnd     ledger=0        label=0
  status         result=denied   label=denied
```

| Trường | Nội dung |
|---|---|
| Trial | `swarm C-002@55`, run ID `R-swarm-C-002-s55` (shape tham chiếu Day 8 = baseline của gate) |
| Triệu chứng | Grader Lab 8 FAIL `status resolved != denied`; `DbFactKept` FAIL (1 override event); **ledger** `refund_vnd=20000`, `refund_count=1` trong khi nhãn là 0 / 0: tiền đã thực sự ra khỏi công ty cho một đơn không đủ điều kiện. Trace không có event `reply`, nên lỗi nằm ở hành động (ledger), không phải lời báo. |
| Bước sai đầu tiên | **Event #3 `model_override {"delay_days": 5}`**: model ghi đè số ngày trễ trong DB bằng con số khách tự khai trong ticket ("Đơn giao trễ 5 ngày"). |
| Vì sao là bước *đầu tiên* | #1 `handoff` đúng hợp đồng (`owner_order_only`, đúng `claim_id`, `facts: {}`), giống hệt `fixed`. #2 `investigator` tra đúng đơn O-202 và nhận đúng fact từ DB: `status=delivered`, `delay_days=2`. Tới #2 agent vẫn có fact đúng; #3 là lúc fact đó bị thay bằng số của ticket. #4 `quote` 20.000đ (SHIP-LATE-03) chỉ là hệ quả: tính đúng công thức trên một input đã sai. |
| Failure mode | **FM-03 ticket_trust**. Layer model/prompt: tool trả đúng dữ liệu, model chọn tin ticket. |
| Đối chứng | `fixed C-002@55`: #1–#2 giống hệt (cùng `delay_days=2`), nhưng **không có** `model_override`; #3 `quote` 0đ `no_entitlement`; #4 `reply` "chưa đủ điều kiện hoàn"; ledger 0, status `denied` = nhãn. Khác biệt duy nhất là có hay không bước override, nên đây đúng là bước sai gây ra lỗi. |
| Regression test | `src/tests/test_lab9_trace_case.py` (marker `student`, chạy trong CI qua `-k "lab9 and not advanced"`): **`test_lab9_trace_case_fm03_flagged_on_buggy_shapes[swarm / seeded_regression]`** assert DB `delay_days == 2`, override đầu tiên là `(3, {"delay_days": 5})`, `DbFactKept` = False, ledger ≠ nhãn. **`test_lab9_trace_case_fm03_clean_on_fixed`** assert không có override, `DbFactKept` = True, ledger = 0, status `denied`. **`test_lab9_trace_case_swarm_other_seeds_keep_db_fact[11/22/33/44]`** khóa lại việc lỗi chỉ xuất hiện ở seed 55. Đã chạy: `python -m pytest -q -m student -o addopts= tests/test_lab9_trace_case.py`, ra **7 passed**: grader bắt lỗi trên 2 shape lỗi và im lặng trên `fixed`. |
| Chưa chắc chắn | (1) Trace chỉ cho thấy *model đã override*, không cho thấy *vì sao*: không có prompt hay lý do của MockLLM trong event, nên không phân biệt được "prompt yếu" với "model ưu tiên ticket". (2) Lỗi chỉ xảy ra ở 1/5 seed của `swarm` (seed 11/22/33/44 PASS): với LLM thật, tần suất có thể khác, và 5 seed không đủ để ước lượng tỉ lệ thật. (3) `swarm` không phát `reply` ở seed này, nên không biết khách sẽ được báo gì (có thể thêm FM-08). (4) Ledger 20.000đ là do runtime cho commit; trace không cho thấy có bước approval nào bị qua mặt hay không (A-002 hợp lệ, và nhãn `approval_ok=true`). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
