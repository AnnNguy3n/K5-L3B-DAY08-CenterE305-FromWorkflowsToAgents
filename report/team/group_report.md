# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Nhóm: **CenterE305**, lớp **K5 — L3B**.
- Thành viên: Triệu Tuấn Minh — `2A202604123`; Nguyễn Hữu An — `2A202604024`.
- Repo: [K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents), nhánh `main`.
- Commit chốt mã nguồn dùng tái lập: `70c00ff884e690a3427f37ae9a85b597adbe3494`, trùng [ADR](decision_adr.md). Benchmark, crash report và ADR được bổ sung trong `68234fa`; báo cáo và ablation R2 được ghi nhận trong đợt cập nhật CP5 sau đó.

## 2. Mục tiêu và cách tiếp cận

Nhóm xử lý claim hoàn phí vận chuyển LogiX-VN theo ba kiến trúc tự triển khai và so sánh với swarm tham chiếu. Mục tiêu là chọn kiến trúc ít tự chủ nhất vẫn xử lý đúng nghiệp vụ, giữ an toàn khi retry/crash và có chi phí mô phỏng hợp lý.

Nhóm dùng order và policy hiện hành làm căn cứ tính tiền. Ticket được xem là dữ liệu khách cung cấp, có thể thiếu hoặc mâu thuẫn với order. Minh triển khai ban đầu single và orchestrator; An triển khai workflow, bổ sung kiểm tra an toàn, tích hợp rồi chạy đánh giá. Swarm có sẵn được giữ làm đối chứng. Nhóm kiểm luồng nghiệp vụ trước, sau đó kiểm retry/crash, approval, handoff và trace, cuối cùng chạy benchmark và ablation R2.

## 3. Giải pháp

| Shape | Luồng xử lý và ranh giới quyết định |
| --- | --- |
| Workflow | Đọc claim qua `get_claim_view`, kiểm quyền xem order, tính quote bằng `compute_compensation`, gọi host khi quote dương. Các bước cố định bằng Python, không gọi model. |
| Single agent | Dùng `run_react` với tối đa 8 bước và `worker=True`. Hàm `decide` ánh xạ observation có cấu trúc sang tool đọc; MockLLM được gọi để ghi nhận lượt xử lý và soạn phản hồi, không sinh số tiền. Shape gọi host sau vòng lặp. |
| Orchestrator | Đọc claim, tạo kế hoạch và handoff qua `make_handoff`. Investigator đọc order, policy, lịch sử refund và tính quote bằng tool chỉ đọc. Orchestrator nhận kết quả và gọi host. |
| Swarm tham chiếu | Dùng bản có sẵn để đo cost và variance. Ở một số seed, nhánh `REFERENCE_WEAKNESS` tin số ngày trễ trong ticket hơn order. |

Cả ba shape truyền **quote đầy đủ** cho `durability.issue_refund`. Host kiểm approval gắn đúng claim, giới hạn tiền được duyệt, trần theo đơn và idempotency; shape không tự trừ khoản đã hoàn. Ví dụ C-014 có entitlement 150.000đ và đã hoàn 30.000đ: proposal giữ 150.000đ, host chỉ ghi thêm 120.000đ. C-013 đã hoàn đủ thì host từ chối và ghi `policy_denied`.

Ledger dùng khóa `refund:{claim_id}` để retry không thêm refund. `crash_at` được chuyển đến host; workflow để exception truyền ra ngoài, single/orchestrator ghi trace rồi ném lại `InjectedCrash`. Sau resume, kết quả đọc refund và audit từ ledger thật qua `finish()`.

Handoff chỉ chứa field trong allowlist và tool đọc. Trace ghi trạng thái, quote, lý do, yêu cầu refund và handoff đã sanitize; không ghi nguyên ticket, claim/order row, parent secret, header, số điện thoại, địa chỉ, ghi chú nội bộ hay tên hàng. Workflow ghi các event `claim`, `order`, `quote`, `refund_requested`, `decision`; single ghi lượt ReAct và kết quả host; orchestrator ghi plan, handoff và dữ kiện điều tra đã chọn lọc. Các nhánh `needs_info` và `escalated` vẫn ghi trace mới, đúng run ID.

## 4. Kết quả

Benchmark dùng cùng 14 claim C-001–C-014, seed `11,22,33,44,55`, public world, `as_of=2026-11-15`, MockLLM và pricing gốc; mỗi trial dùng SQLite mới. Tổng cộng có 280 trial. Số liệu dưới đây lấy từ `by_shape` trong [benchmark.json](../../src/reports/benchmark.json), làm tròn để trình bày.

| Shape | Pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Workflow | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 27.857143 | 4.43 / 5 |
| Single | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 39.340000 | 12.43 / 14 |
| Orchestrator | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 59.424286 | 6.93 / 8 |
| Swarm | 69/70 | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.80 / 3 |

Pass^5 là tỷ lệ claim đúng cả năm seed; variance được tính trên pass rate theo seed. Cost/success gồm chi phí của cả trial fail trong tử số. `Steps` đếm event trace, không biểu diễn thời gian chạy.

Nhóm chọn **workflow** vì có cùng độ đúng public với single/orchestrator và cost/success thấp nhất. Quyết định chỉ áp dụng cho task và các bản triển khai đã đo. Nếu corpus đại diện hơn cho thấy cần lựa chọn tool linh hoạt hoặc điều tra độc lập, nhóm sẽ đánh giá lại với cùng điều kiện kiểm soát và các cổng an toàn. Run ID dẫn chứng gồm `R-workflow-C-001-s11`, `R-workflow-C-007-s11`, `R-workflow-C-013-s11`, `R-workflow-C-014-s11`.

[Crash report](../../src/reports/crash.json) đạt **20/20**, kiểm host và một kịch bản swarm. Ba shape nhóm viết được kiểm riêng bằng T11/T12 và test ba điểm crash. Bộ mặc định có **79 test pass**, ma trận student có **248 test pass**; chạy tất cả bằng `python -m pytest -q -o addopts=` cho **327 test pass**. Trong ma trận student, lỗi swarm C-002/seed 55 được kiểm như một lỗi đã biết, nên số test xanh không đồng nghĩa swarm đúng mọi trial benchmark.

Với nghiên cứu **R2**, nhóm so sánh swarm gốc và biến thể không dùng parsed delay từ ticket để ghi đè order, giữ nguyên topology, MockLLM, bộ tool, corpus, seed, giá và evaluator. [Report ablation](../../src/reports/research_ablation.json) cho kết quả 69/70 → 70/70 trial pass, pass^5 13/14 → 14/14, variance 0,000816327 → 0 và cost/success 49,566957 → 48,715714 VND mô phỏng. Chỉ C-002/seed 55 thay đổi: quote 20.000đ/`resolved` thành 0đ/`denied`; cả hai vẫn có ba model call mỗi trial. Nhóm diễn giải lỗi này theo nhóm task verification của MAST. Phương pháp, trace và giới hạn được trình bày trong [research card](research_card.md).

## 5. Khó khăn và cách xử lý

Các vấn đề dưới đây được tái hiện bằng demo và test; nhóm không coi mọi tình huống kiểm thử là lỗi từng xuất hiện trong code cuối cùng.

| Vấn đề | Bằng chứng và cách xử lý |
| --- | --- |
| Checkpoint đơn lẻ không chống trả trùng | `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2 (the host ledger must stay at 1)`. Nhóm dùng ledger/idempotency của host, kiểm một refund và một audit sau resume. |
| Crash bị chuyển thành kết quả failed thông thường | Test `test_crash_propagates_and_resume_keeps_one_refund` ở hai file test shape buộc `InjectedCrash` truyền ra ngoài tại ba điểm crash; shape đóng connection trong `finally`. |
| Ticket mâu thuẫn order | `R-swarm-C-002-s55` fail `status resolved != denied`. Workflow dùng order có cấu trúc; ablation R2 cô lập tác động của nhánh ghi đè delay. |
| Nhầm proposal với tiền thực trả | T13/T14 và test quote conflict kiểm proposal đầy đủ, ledger thực tế và audit. Nhóm để host áp dụng trần và phần chênh. |
| Rò dữ liệu qua handoff, trace hoặc model prompt | Test injection/handoff kiểm allowlist, tool chỉ đọc, artifact và stdout/stderr. Nhóm chỉ ghi các field cần để giải thích quyết định. |

Các lệnh tái lập chính, chạy trong `src/` với virtual environment đã kích hoạt:

```bash
python -m pytest -q -o addopts=
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.benchmark --extra-shape swarm_order_only=tests.research_ablation:run_claim --shapes swarm,swarm_order_only --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_ablation.json
```

Kết quả sinh lại trong thư mục tạm khớp các report hiện tại; nhóm không sửa tay JSON.

## 6. Tổng hợp đóng góp

Minh triển khai ban đầu single/orchestrator trong `c5289c3`. An triển khai workflow, bổ sung xử lý an toàn và test trong `ff0ea62`, tích hợp ở `70c00ff`, bổ sung report/ADR ở `68234fa`, rồi thực hiện R2 và báo cáo CP5 với hỗ trợ của Codex. Chi tiết tại [TEAM.md](../../TEAM.md) và [báo cáo cá nhân của An](2A202604024_NguyenHuuAn.md). Báo cáo của Minh hiện là bản sao mẫu; lịch sử nhánh chưa ghi nhận test do Minh thêm/sửa, nên phần minh chứng C8 của Minh chưa đầy đủ.

## 7. Hạn chế và hướng cải thiện

MockLLM là mô phỏng; cost không phải hóa đơn API và latency là `unavailable`. Chênh lệch giữa các shape còn phụ thuộc prompt, số tool call và cách ghi trace, nên bảng benchmark chưa tách riêng tác động của topology. Public chỉ có 14 claim; chưa có `student_drop/` hay kết quả grader hidden để xác nhận ngưỡng 0,75 và các counter must-pass chính thức.

R2 xử lý một lỗi được cài có chủ đích, đã biết trước khi đặt hypothesis. Kết quả chưa chứng minh mức cải thiện trên dữ liệu mới hoặc model sản xuất. Nhóm cần đánh giá trên corpus đa dạng hơn, tách biệt dữ liệu đặt giả thuyết với dữ liệu kiểm chứng và giữ nguyên các cổng approval, secret và crash khi so sánh tiếp.

## 8. Tài liệu tham khảo

1. Tài liệu lab: [luật nghiệp vụ](../../docs/business_rules.md), [contract](../../docs/contracts.md), [kiến trúc](../../docs/architecture.md), [metric](../../docs/metrics.md), [rubric](../../RUBRIC.md).
2. Minh chứng của nhóm: [ADR](decision_adr.md), [research card](research_card.md), benchmark/crash/ablation JSON được liên kết ở mục 4.
3. Cemri và cộng sự (2025), *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS, Datasets and Benchmarks Track. [Nguồn chính thức](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html).
