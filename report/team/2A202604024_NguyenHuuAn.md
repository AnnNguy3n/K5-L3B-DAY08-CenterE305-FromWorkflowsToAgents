# Báo cáo cá nhân — Nguyễn Hữu An

## 1. Thông tin thành viên

- Họ tên: Nguyễn Hữu An — MSSV: `2A202604024`.
- Email: 26ai.annh2@vinuni.edu.vn; GitHub: [AnnNguy3n](https://github.com/AnnNguy3n).
- Nhóm: CenterE305, lớp K5 — L3B.
- Repo: [K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents), nhánh `main`.

## 2. Phần việc phụ trách

Em phụ trách workflow, tích hợp ba shape, bổ sung test an toàn, chạy đánh giá và tổng hợp báo cáo. Với single/orchestrator do Minh triển khai ban đầu, em bổ sung xử lý crash, giới hạn tool và trace. Em thực hiện R2 để kiểm tra tác động của việc swarm tin dữ kiện ticket hơn order.

## 3. Đóng góp cụ thể

| Commit | Nội dung |
| --- | --- |
| [ff0ea62](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/ff0ea6238ecee5de3d1d29a96fc70d8366404f05) | Triển khai workflow, bổ sung an toàn cho single/orchestrator và thêm hai file test shape. |
| [70c00ff](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/70c00ff884e690a3427f37ae9a85b597adbe3494) | Tích hợp thay đổi của nhóm; mốc mã nguồn tái lập trong ADR. |
| [68234fa](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/68234fa950ea71a6c966139f0f971edcda85d819) | Lưu benchmark, crash report và ADR chọn workflow. |
| [3868fe8](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/3868fe83f0cbbd932805e2b3d39082667f10719d) | Thêm helper/test/report R2, hoàn thiện research card và báo cáo CP5. |

Em giữ quote đầy đủ khi gọi host để tránh trừ khoản đã hoàn hai lần. Với C-014, proposal là 150.000đ nhưng host chỉ hoàn thêm 120.000đ. Kết quả lấy refund/audit từ ledger qua `finish()`; investigator chỉ có tool đọc và trace chỉ ghi dữ kiện đã chọn lọc.

## 4. Bằng chứng

| Test đã thêm | Nội dung kiểm tra |
| --- | --- |
| [test_workflow.py](../../src/tests/test_workflow.py) | Crash/resume tại ba điểm, retry với quote thay đổi, claim không tồn tại và ticket injection. |
| [test_agent_shapes.py](../../src/tests/test_agent_shapes.py) | Crash/resume, approval sai claim, injection, giới hạn 8 bước ReAct, chặn tool ghi và handoff allowlist. |
| [test_research_ablation.py](../../src/tests/test_research_ablation.py) | C-002/seed 55 được sửa khi bỏ ghi đè delay; ledger không có refund, prompt peer/parse giữ nguyên và scoped patch được khôi phục. |

Bộ mặc định đạt **79 passed**, student đạt **248 passed**; `python -m pytest -q -o addopts=` đạt **327 passed**. [Benchmark](../../src/reports/benchmark.json) ghi nhận workflow 70/70 trial, pass^5=1, variance=0 và cost/success 27,857143 VND mô phỏng. Run ID `R-workflow-C-014-s11` minh họa trường hợp hoàn phần chênh. [Crash suite](../../src/reports/crash.json) đạt 20/20 cho host/swarm; ba shape nhóm viết được kiểm bằng test riêng.

Trong [R2](research_card.md), [report ablation](../../src/reports/research_ablation.json) cho thấy swarm 69/70 → order-only 70/70 trial pass. Cặp run ID `R-swarm-C-002-s55` và `R-swarm_order_only-C-002-s55` là minh chứng trực tiếp. Kết quả sinh lại của benchmark, crash và ablation khớp các JSON đã lưu; lệnh tái lập được ghi trong [ADR](decision_adr.md) và research card.

## 5. Công cụ AI đã dùng

Em sử dụng **Codex** để hỗ trợ đọc yêu cầu, rà code, viết test, thực thi thí nghiệm và soạn báo cáo. Kết quả được kiểm bằng test trên ledger/audit, đối chiếu trace và so sánh report sinh lại với JSON đã lưu. Các bước chạy lệnh và đối chiếu này có hỗ trợ của Codex. Model trong bài lab vẫn là MockLLM, không dùng API model thật.

## 6. Tự đánh giá

Phần việc của em đáp ứng các tình huống public đã kiểm, đặc biệt là quote đầy đủ, retry/crash và ranh giới tool/trace. Qua kết quả benchmark, em chọn workflow vì xử lý đúng task hiện tại với cost/success thấp nhất.

Giới hạn là mới đo trên 14 claim và MockLLM; chưa có kết quả hidden, counter leak/bypass hoặc latency thực tế. R2 sửa một nhánh lỗi cố ý trên dữ liệu đã biết. Hướng cải thiện của em là kiểm chứng trên corpus mới trước khi kết luận khả năng tổng quát.
