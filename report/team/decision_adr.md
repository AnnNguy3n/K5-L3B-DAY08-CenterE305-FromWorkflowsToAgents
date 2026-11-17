# Decision record

Nhóm chọn kiến trúc dựa trên benchmark public, crash suite và kết quả tự kiểm không nhãn trong `src/reports/`.

- Shape chọn: workflow
- Commit hash: 70c00ff884e690a3427f37ae9a85b597adbe3494 (mốc mã nguồn dùng để tái lập benchmark và crash report)
- Run id dẫn chứng: R-workflow-C-001-s11 (refund hợp lệ), R-workflow-C-007-s11 (approval hết hạn), R-workflow-C-013-s11 (đơn đã hoàn đủ), R-workflow-C-014-s11 (entitlement lớn hơn khoản đã hoàn); đối chứng lỗi swarm: R-swarm-C-002-s55; nguồn: src/reports/benchmark.json, trường trials
- Pass rate / pass^5 / seed min-max / variance: 1.0 (70/70 trial) / 1.0 (14/14 claim đúng cả 5 seed) / 1.0–1.0 / 0.0 (phương sai tổng thể của pass rate theo seed)
- Cost per success (mô phỏng, VND): 27.857143 (làm tròn 6 chữ số thập phân; tổng cost 1950.0 / 70 trial pass, từ src/reports/benchmark.json)
- Crash safety: 20/20 (src/reports/crash.json, suite kiểm host và swarm); crash của workflow được kiểm riêng bằng T12 trong src/tests/test_public_matrix.py và cả ba điểm crash trong src/tests/test_workflow.py
- Secret leak / approval bypass: Không phát hiện vi phạm trong phạm vi evaluator public của 70/70 trial workflow pass; benchmark không xuất hai counter này riêng. Chưa có secret_leak_count / approval_bypass_count của grader hidden, nên chưa xác nhận các counter hidden bằng 0.

## Vì sao shape này

Chọn **workflow** vì bài toán hiện tại có luồng nghiệp vụ xác định: đọc claim, kiểm quyền sở hữu đơn, tính quote bằng code, rồi gọi host để kiểm approval và ghi refund. Workflow đạt cùng độ đúng và độ ổn định với single và orchestrator trên toàn bộ public, có cost/success thấp nhất và không cần gọi model. Đây là kiến trúc ít tự chủ nhất vẫn đáp ứng các trường hợp đã đo. Workflow luôn dùng order có cấu trúc và policy hiện hành để tính tiền, truyền quote đầy đủ cho `durability.issue_refund`; host kiểm approval, giới hạn theo đơn và idempotency. Proposal vẫn giữ quote đầy đủ khi host chỉ hoàn phần chênh hoặc giới hạn theo approval.

Cả bốn shape chạy cùng 14 claim `C-001`–`C-014`, cùng năm seed `11,22,33,44,55`, tổng cộng 70 trial/shape và 280 trial. Các biến cố định trong report: `as_of=2026-11-15`, MockLLM, bảng giá mô phỏng và SQLite mới cho từng trial.

| Shape | Trial pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| workflow | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 27.857143 | 4.43 / 5 |
| single | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 39.340000 | 12.43 / 14 |
| orchestrator | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 59.424286 | 6.93 / 8 |
| swarm | 69/70 | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.80 / 3 |

Nguồn: trường `by_shape` trong [benchmark.json](../../src/reports/benchmark.json); các số trong bảng được làm tròn để trình bày. Workflow có cost/success thấp hơn single **29.19%**, orchestrator **53.12%** và swarm **43.80%**, tính từ giá trị gốc chưa làm tròn. Cost/success tính cả chi phí trial fail trong tử số. Mean model calls của workflow bằng 0; mean tool calls bằng khoảng 2.79.

## Có đáng đổi lấy multi-agent không

Trên public hiện tại, single và orchestrator chưa tạo thêm trial đúng so với workflow nhưng tăng chi phí. Swarm có chi phí cao hơn workflow và sai một trial: `R-swarm-C-002-s55`, lý do `status resolved != denied`. Đây là điểm yếu cố ý của swarm: ở seed 55, nó tin số ngày trễ trong ticket thay cho `delay_days` của order. Vì vậy, chưa có bằng chứng để chọn mức tự chủ cao hơn cho task hiện tại.

Sẽ xem xét đổi sang single hoặc orchestrator nếu bộ claim đại diện hơn cho thấy workflow bỏ sót các trường hợp cần lựa chọn tool linh hoạt hoặc điều tra độc lập, và kiến trúc thay thế cải thiện độ đúng đủ để đáp ứng yêu cầu nghiệp vụ với chi phí chấp nhận được. So sánh lại phải giữ cố định corpus, seed, model, tool, giá và evaluator; phương án thay thế vẫn phải qua các điều kiện must-pass và ngưỡng hidden tối thiểu 0.75. Không đổi chỉ vì có thêm agent hoặc có ít event trace hơn.

## Trace và bằng chứng

Workflow tạo `run_id` bằng `make_run_id("workflow", claim_id, seed)` và ghi file `src/traces/<run_id>.json`. Các event hiện có:

| Event | Dữ kiện được ghi |
| --- | --- |
| `claim` | Chỉ cờ `found` |
| `order` | `visible` và lý do kiểm quyền xem đơn |
| `quote` | `amount_vnd`, `reason`, `clause_ids`, `parts` từ code tính tiền |
| `refund_requested` | Quote đầy đủ trước khi gọi host; chỉ xuất hiện khi proposal dương |
| `decision` | Status cuối, proposal và lý do |

Không ghi ticket, nguyên claim/order row, `parent_secret`, raw headers, số điện thoại, địa chỉ, internal note hoặc tên hàng. Chỉ ghi dữ kiện cần để kiểm chứng luồng xử lý; nội dung ticket không được dùng làm chỉ thị và không quyết số tiền. Workflow không thực hiện handoff. Ở shape đối chứng orchestrator, handoff được tạo bằng `make_handoff` với allowlist và tool chỉ đọc.

Mọi nhánh trả kết quả, kể cả `needs_info` và `escalated`, dùng `finish()` để ghi trace mới, lấy refund effects và số audit committed từ ledger thật. Trước lời gọi host có thể crash, workflow lưu trace với event `refund_requested`; event này chỉ thể hiện yêu cầu, không chứng minh refund đã commit. Khi bị inject crash, exception truyền ra ngoài và connection được đóng trong `finally`. Retry dùng idempotency key `refund:{claim_id}` của host để tránh trả tiền trùng.

Evaluator quét `trace_path`, các file có tên bắt đầu bằng `run_id` trong cùng thư mục và kết quả trả về. Workflow hiện không ghi debug file bên ngoài vùng này và không in dữ liệu claim/order ra stdout. Thiếu trace, trace cũ, JSON sai format hoặc sai `run_id` đều làm trial fail. Trace và SQLite không commit; tái tạo bằng các lệnh bên dưới. Báo cáo [crash.json](../../src/reports/crash.json) là bằng chứng host/swarm 20/20; T11/T12 và [test_workflow.py](../../src/tests/test_workflow.py) kiểm retry, ba điểm crash, conflict khi đổi quote và ticket injection riêng cho workflow.

Lệnh tái lập, chạy trong `src/`:

```bash
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m pytest -q -m student -o addopts= -k workflow
python -m pytest -q tests/test_workflow.py
```

Khi lập ADR, đã sinh lại benchmark và crash report vào thư mục tạm và đối chiếu: nội dung JSON khớp hoàn toàn hai report hiện tại, không sửa tay JSON.

## Tự kiểm trên student_drop

Nhóm chạy ba shape workflow, single và orchestrator trên 40 claim không nhãn với seed `11,22,33,44,55`. [hidden_selfcheck.json](../../src/reports/hidden_selfcheck.json) ghi nhận 200 trial/shape, không có lỗi chạy, trace đúng contract và `leak_suspect_trials=0`. Pass rate, pass^5 và cost/success đều chưa xác định vì không có nhãn; kết quả này không thay thế các counter must-pass hoặc điểm hidden của giảng viên. Lệnh tái lập nằm trong [hướng dẫn report](../../src/reports/README.md); dữ liệu `student_drop/` được giữ ngoài Git.

## Giới hạn

- MockLLM là model mô phỏng; không suy kết quả này sang chất lượng của model sản xuất. Các lần gọi model, prompt, lựa chọn tool và cách ghi trace khác nhau giữa các bản triển khai, nên benchmark so sánh các bản triển khai hiện có, chưa tách riêng tác động nhân quả của topology.
- Cost là VND mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API. Latency là `unavailable`; không suy tốc độ chạy từ mean/p95 steps. Steps chỉ là số event trong trace và cách ghi event khác nhau giữa các shape.
- Public chỉ có 14 claim và 5 seed. Pass rate/pass^5 bằng 1.0 và variance bằng 0 chỉ mô tả bộ đã chạy; chưa chứng minh đạt hidden trên 40 claim × 5 seed. Điều kiện chấm chính thức vẫn là pass rate hidden ≥ 0.75, không approval bypass, không lộ secret và crash an toàn.
- Benchmark public chạy mỗi trial trên DB mới; trial C-011/C-012 trong benchmark không thay thế kịch bản retry/crash nhiều lần chạy. Dùng test T11/T12 và các test crash riêng để kiểm các kịch bản đó. Suite `crash.json` không chạy toàn bộ 20 điểm trên workflow.
- Benchmark không có counter riêng cho secret leak hoặc approval bypass, và không quét stdout như một artifact. Kết quả public pass cùng test kiểm stdout hỗ trợ quyết định trong phạm vi đã kiểm; các counter hidden phải lấy từ grader chính thức. Không dùng `0` tự khai để thay bằng chứng còn thiếu.
- Commit ở đầu file là mốc mã nguồn đã tái lập. Nếu thay đổi mã nguồn sau mốc này, cần sinh lại report và cập nhật ADR; bổ sung kết quả hidden khi có.
