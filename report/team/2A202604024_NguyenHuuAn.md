# Báo cáo cá nhân — Nguyễn Hữu An

## 1. Thông tin thành viên

- Họ tên: Nguyễn Hữu An
- MSSV: `2A202604024`
- Email: 26ai.annh2@vinuni.edu.vn
- GitHub: [AnnNguy3n](https://github.com/AnnNguy3n)
- Nhóm: CenterE305 — K5, L3B
- Repo: [K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents), nhánh `main`.

## 2. Phần việc phụ trách

Em phụ trách workflow, tích hợp ba shape, bổ sung test an toàn và đánh giá kết quả. Với single và orchestrator, phần triển khai ban đầu của Minh được tích hợp cùng các bổ sung về crash, tool chỉ đọc, xử lý lỗi và trace. Phần CP5 của em gồm benchmark, crash report, ADR chọn kiến trúc, thí nghiệm R2 và tổng hợp báo cáo, có sử dụng Codex để hỗ trợ viết và kiểm tra.

## 3. Đóng góp cụ thể

| Phần việc | Nội dung và bằng chứng |
| --- | --- |
| Workflow | Trong [ff0ea62](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/ff0ea6238ecee5de3d1d29a96fc70d8366404f05), em triển khai đọc claim/order, tính quote bằng code, gọi host và ghi trace ở các nhánh trả kết quả. |
| Bổ sung an toàn cho single/orchestrator | Cùng commit `ff0ea62`, bổ sung xử lý crash truyền ra ngoài, ranh giới tool đọc, trace trước host call và kết quả lấy từ ledger. Single dùng tối đa 8 bước; orchestrator chuyển handoff qua allowlist. |
| Test | Thêm [test_workflow.py](../../src/tests/test_workflow.py) và [test_agent_shapes.py](../../src/tests/test_agent_shapes.py): unknown claim, crash/resume, thay đổi quote khi retry, approval sai claim, ticket injection, giới hạn bước ReAct, chặn tool ghi và handoff chỉ đọc. |
| Tích hợp | [70c00ff](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/70c00ff884e690a3427f37ae9a85b597adbe3494) tích hợp thay đổi của nhánh nhóm và giữ các kiểm tra an toàn CP3. Đây là mốc mã nguồn tái lập trong ADR. |
| Đánh giá và ADR | [68234fa](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/68234fa950ea71a6c966139f0f971edcda85d819) bổ sung benchmark, crash report do công cụ sinh và ADR chọn workflow theo số liệu public. |
| R2 và báo cáo CP5 | Bổ sung [helper R2](../../src/tests/research_ablation.py), [test R2](../../src/tests/test_research_ablation.py), report ablation, research card, báo cáo nhóm và thông tin đóng góp trong đợt ghi nhận tiến độ CP5 này. |

Quyết định kỹ thuật chính của em là giữ quote đầy đủ và giao host xử lý approval, trần theo đơn, idempotency. C-014 minh họa sự khác nhau giữa proposal 150.000đ với refund thực tế 120.000đ. Em dùng `finish()` để đọc effects/audit thật thay vì tự khai các field kết quả. Với trace, em chỉ ghi trạng thái, quote và dữ kiện đã chọn lọc, tránh đưa ticket hoặc nguyên row vào log.

## 4. Bằng chứng

Kết quả kiểm tra trên phiên bản hiện tại:

| Kiểm tra | Kết quả và nguồn |
| --- | --- |
| Bộ test mặc định | `python -m pytest -q`: 79 passed |
| Ma trận public student | `python -m pytest -q -m student -o addopts=`: 248 passed; gồm T11 retry và T12 crash/resume |
| Toàn bộ test | `python -m pytest -q -o addopts=`: 327 passed |
| Benchmark workflow | 70/70 trial, pass^5=1, variance=0, cost/success=27,857143 VND mô phỏng; [benchmark.json](../../src/reports/benchmark.json) |
| Crash suite | 20/20; [crash.json](../../src/reports/crash.json). Suite kiểm host/swarm; ba shape nhóm viết có test crash riêng. |
| R2 | Swarm 69/70 → order-only 70/70, cost/success 49,566957 → 48,715714; [research_ablation.json](../../src/reports/research_ablation.json) |

Các run ID dẫn chứng:

- `R-workflow-C-001-s11`: hoàn hợp lệ 35.000đ.
- `R-workflow-C-007-s11`: từ chối approval hết hạn.
- `R-workflow-C-013-s11`: từ chối khi đơn đã được hoàn đủ.
- `R-workflow-C-014-s11`: proposal đầy đủ, host hoàn phần chênh.
- `R-swarm-C-002-s55` và `R-swarm_order_only-C-002-s55`: cặp đối chứng R2, quote 20.000đ/`resolved` so với 0đ/`denied`.

Benchmark, crash và ablation được sinh lại vào thư mục tạm để đối chiếu với file report; kết quả JSON khớp. Trace được tái tạo tại `src/traces/<run_id>.json`, không commit vào repo. Lệnh benchmark/crash ghi trong [ADR](decision_adr.md); lệnh R2 ghi trong [research card](research_card.md).

## 5. Công cụ AI đã dùng

Em sử dụng **Codex trong môi trường IDE** để hỗ trợ đọc yêu cầu, rà code và lịch sử commit, đề xuất test, thiết kế/chạy ablation R2 và soạn báo cáo từ minh chứng trong repo. Việc thực thi lệnh, kiểm tra trace và đối chiếu report trong phiên làm việc có sự hỗ trợ trực tiếp của Codex; em không ghi nhận đó là các bước hoàn toàn làm thủ công.

Cách kiểm tra kết quả gồm chạy test host/student, kiểm ledger và audit trong test, so sánh report sinh lại với JSON hiện có, đối chiếu run ID và phân tích cặp trial lỗi. Với R2, nguồn MAST được đối chiếu với trang công bố chính thức, còn phân loại lỗi của lab được ghi rõ là diễn giải của nhóm. Các số liệu trong báo cáo lấy từ test và report thực tế; các mốc mã nguồn và phạm vi chưa có kết quả hidden được nêu riêng.

MockLLM là thành phần mô phỏng của bài lab, khác với Codex dùng hỗ trợ quá trình làm bài. Các shape không gọi model thật hoặc dùng API key.

## 6. Tự đánh giá

Phần việc của em có minh chứng rõ nhất ở workflow, các test an toàn và bộ đánh giá public. Các kết quả hiện có cho thấy phiên bản đã xử lý đúng những tình huống được kiểm: quote do code tính, refund qua host, retry/crash không ghi trùng và handoff giới hạn dữ kiện/tool. Từ đó, em rút ra rằng việc chia thêm agent chỉ có ý nghĩa khi cải thiện được kết quả trên task cụ thể; với bộ public này, workflow đã đủ và có cost/success thấp nhất.

Giới hạn của phần việc là mới đánh giá trên 14 claim với MockLLM. R2 sửa một nhánh lỗi cố ý của swarm và dùng dữ liệu đã quan sát trước, nên chưa chứng minh khả năng tổng quát trên hidden hay model sản xuất. Báo cáo cũng chưa có số đo latency và các counter hidden về leak/bypass. Trong bước tiếp theo, em cần kiểm tra trên dữ liệu mới khi có bộ tự kiểm, giữ riêng dữ liệu phát hiện lỗi và dữ liệu kiểm chứng, đồng thời chốt phiên bản nộp cuối cùng sau khi đủ hồ sơ của các thành viên.
