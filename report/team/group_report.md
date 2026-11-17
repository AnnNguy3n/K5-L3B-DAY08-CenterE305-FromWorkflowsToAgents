# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Nhóm: **CenterE305**, lớp **K5 — L3B**.
- Thành viên: Triệu Tuấn Minh — `2A202604123`; Nguyễn Hữu An — `2A202604024`.
- Repo: [K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents), nhánh `main`.
- Mốc mã nguồn tái lập: `70c00ff884e690a3427f37ae9a85b597adbe3494`, theo [ADR](decision_adr.md). Benchmark và crash report được lưu ở `68234fa`; thí nghiệm R2 và báo cáo CP5 ở `3868fe8`.

## 2. Mục tiêu và cách tiếp cận

Nhóm triển khai workflow, single agent và orchestrator để xử lý claim hoàn phí vận chuyển, sau đó so sánh với swarm tham chiếu. Nhóm chọn kiến trúc dựa trên độ đúng, khả năng chống ghi trùng và cost/success. Dữ liệu order và policy hiện hành là căn cứ tính tiền; nội dung ticket được xem là thông tin cần kiểm chứng.

## 3. Giải pháp

| Shape | Cách xử lý |
| --- | --- |
| [Workflow](../../src/lab8/shapes/workflow.py) | Thực hiện các bước cố định: đọc claim, kiểm quyền xem order, tính quote bằng code và gọi host. Không gọi model. |
| [Single](../../src/lab8/shapes/single.py) | Dùng vòng ReAct tối đa 8 bước. Code ánh xạ observation sang tool đọc; MockLLM ghi nhận lượt xử lý và soạn phản hồi. Shape gọi host sau vòng lặp. |
| [Orchestrator](../../src/lab8/shapes/orchestrator.py) | Chuyển handoff qua `make_handoff`; investigator chỉ đọc order, policy, lịch sử refund và tính quote. Orchestrator gọi host khi có quote dương. |

**Nghiệp vụ và approval:** `compute_compensation` tính tiền theo order và policy còn hiệu lực tại `as_of=2026-11-15`. Shape truyền quote đầy đủ cho `durability.issue_refund`; host kiểm approval đúng claim, giới hạn tiền và trần theo đơn. Với C-014, proposal là 150.000đ, đã hoàn 30.000đ nên host chỉ ghi thêm 120.000đ. Khi quote dương nhưng host từ chối, host ghi audit `policy_denied`.

**Retry và crash:** ledger dùng khóa `refund:{claim_id}`; gọi lại hoặc resume vẫn chỉ có một refund và một audit `refund_committed`. Cả ba shape truyền `crash_at` và để `InjectedCrash` truyền ra ngoài. T11/T12 trong [ma trận public](../../src/tests/test_public_matrix.py) và test crash ở [test_workflow.py](../../src/tests/test_workflow.py), [test_agent_shapes.py](../../src/tests/test_agent_shapes.py) kiểm các trường hợp này.

**Handoff và trace:** investigator chỉ nhận field trong allowlist và tool đọc. Trace ghi trạng thái, quote, lý do và handoff đã sanitize; không ghi nguyên ticket, claim/order row, secret, header hay PII. Mỗi kết quả, kể cả `needs_info` và `escalated`, có trace mới với run ID khớp `RunResult` theo Trace contract v1. Test injection/handoff trong hai file test shape kiểm artifact, prompt và stdout/stderr.

## 4. Kết quả

Benchmark dùng cùng 14 claim C-001–C-014, seed `11,22,33,44,55`, public world, MockLLM và pricing gốc; mỗi trial dùng SQLite mới. Tổng cộng có 280 trial. Bảng lấy từ `by_shape` trong [benchmark.json](../../src/reports/benchmark.json), làm tròn để trình bày.

| Shape | Pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Workflow | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 27.857143 | 4.43 / 5 |
| Single | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 39.340000 | 12.43 / 14 |
| Orchestrator | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 59.424286 | 6.93 / 8 |
| Swarm | 69/70 | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.80 / 3 |

Pass^5 là tỷ lệ claim đúng cả năm seed; variance tính trên pass rate theo seed. Cost/success tính cả chi phí trial fail. Steps là số event trace, không phải thời gian chạy.

Nhóm chọn **workflow** vì đạt cùng độ đúng public với single/orchestrator và có cost/success thấp nhất. Hai run ID tiêu biểu là `R-workflow-C-001-s11` (refund hợp lệ) và `R-workflow-C-014-s11` (hoàn phần chênh). Nhóm sẽ xem xét kiến trúc khác nếu dữ liệu mới cho thấy việc chọn tool linh hoạt hoặc điều tra độc lập cải thiện độ đúng với chi phí chấp nhận được.

[Crash suite](../../src/reports/crash.json) đạt **20/20**, kiểm host và một kịch bản swarm; ba shape nhóm viết có test crash riêng nêu ở mục 3. Bộ test mặc định đạt **79 passed**, student đạt **248 passed**, tổng **327 passed**. Ma trận student kiểm lỗi swarm C-002/seed 55 như một lỗi đã biết; vì vậy test xanh vẫn phù hợp với benchmark swarm 69/70.

Trong **R2**, nhóm giữ nguyên topology và điều kiện benchmark, chỉ tắt việc dùng parsed delay từ ticket để ghi đè order. [Report ablation](../../src/reports/research_ablation.json) ghi nhận swarm 69/70 → order-only 70/70 trial pass; cost/success 49,566957 → 48,715714 VND mô phỏng. Cặp `R-swarm-C-002-s55` và `R-swarm_order_only-C-002-s55` chuyển từ quote 20.000đ/`resolved` sang 0đ/`denied`; cả hai vẫn có ba model call. Nhóm phân loại đây là lỗi kiểm chứng dữ kiện theo MAST; phương pháp và phân tích ở [research card](research_card.md).

Lệnh benchmark/crash được ghi tại [hướng dẫn tái lập](../../src/reports/README.md), lệnh R2 tại research card. Ba report sinh lại khớp JSON đã lưu; nhóm không sửa tay số liệu. Trace được tái tạo tại `src/traces/<run_id>.json` và không commit.

## 5. Khó khăn và cách xử lý

Nhóm dùng demo `python -m lab8.demo.buggy_workflow` để kiểm tra giới hạn của checkpoint đơn lẻ: kết quả có hai dòng refund. Nhóm giữ thao tác ghi tiền qua ledger của host và kiểm một refund sau resume bằng T11/T12.

Lỗi swarm tại C-002/seed 55 cho thấy ticket có thể mâu thuẫn với order. Nhóm dùng order có cấu trúc để tính tiền trong ba shape và thực hiện R2 để cô lập tác động của nhánh ghi đè delay.

## 6. Tổng hợp đóng góp

| Thành viên | Phần việc và commit |
| --- | --- |
| Triệu Tuấn Minh | Triển khai ban đầu single/orchestrator: `c5289c3`. |
| Nguyễn Hữu An | Workflow, bổ sung an toàn và test: `ff0ea62`; tích hợp: `70c00ff`; benchmark/ADR: `68234fa`; R2 và báo cáo: `3868fe8`. |

Bằng chứng chi tiết ở [TEAM.md](../../TEAM.md) và [báo cáo cá nhân của An](2A202604024_NguyenHuuAn.md). Báo cáo cá nhân và commit test của Minh chưa hoàn thiện, nên minh chứng C8 của nhóm còn thiếu.

## 7. Hạn chế và hướng cải thiện

Kết quả chỉ phản ánh 14 claim public với MockLLM. Cost là mô phỏng, latency là `unavailable`; chênh lệch prompt, tool call và cách ghi trace chưa cho phép tách riêng tác động của topology. R2 xử lý một lỗi được cài có chủ đích trên dữ liệu đã quan sát, nên chưa chứng minh mức cải thiện trên dữ liệu mới.

Nhóm chưa có kết quả hidden để xác nhận ngưỡng pass rate ≥ 0,75 trên 200 trial và các counter approval bypass, secret/PII leak. Hướng tiếp theo là đánh giá trên corpus mới và giữ riêng dữ liệu phát hiện lỗi với dữ liệu kiểm chứng.

## 8. Tài liệu tham khảo

1. Tài liệu lab: [luật nghiệp vụ](../../docs/business_rules.md), [contract](../../docs/contracts.md), [metric](../../docs/metrics.md), [rubric](../../RUBRIC.md).
2. Cemri và cộng sự (2025), *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS, Datasets and Benchmarks Track. [Nguồn chính thức](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html).
