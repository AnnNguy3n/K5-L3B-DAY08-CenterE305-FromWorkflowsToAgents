# Research card

Nhóm chọn **R2 — Failure taxonomy** và chạy một ablation: giữ nguyên MockLLM, bộ tool, seed, corpus và giá, chỉ thay đổi việc sử dụng parsed delay từ ticket để ghi đè dữ liệu order.

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | **R2 — Failure taxonomy.** Trial lỗi C-002/seed 55 của swarm có phù hợp với nhóm lỗi kiểm chứng nhiệm vụ không? Vô hiệu hóa việc dùng số ngày trễ từ ticket để ghi đè order có sửa được lỗi đó mà không gây thêm lỗi trên public không? |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025, Datasets and Benchmarks Track. [Nguồn chính thức](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html). Bằng chứng: nghiên cứu thực nghiệm trên execution trace và taxonomy MAST; không phải báo cáo triển khai LogiX-VN. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | MAST xác định 14 loại lỗi, gom thành ba nhóm: system design issues, inter-agent misalignment và task verification. Taxonomy giúp phân tích kiểu lỗi thay vì chỉ quan sát kết quả pass/fail. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Paper nghiên cứu MAST-Data gồm hơn 1.600 trace từ 7 framework MAS, với các model và task coding, math, general agent trong nghiên cứu. Paper không kiểm LogiX-VN hay MockLLM; phân loại lỗi của lab dưới đây là diễn giải của nhóm dựa trên code, trace và ablation. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Từ benchmark public đã quan sát, dự đoán tắt việc dùng parsed delay từ ticket sẽ sửa C-002/seed 55: pass rate tăng từ 69/70 lên 70/70 (+1,428571 điểm phần trăm), pass^5 tăng từ 13/14 lên 14/14, seed variance giảm về 0, không thêm trial lỗi. Đây là giả thuyết sau khi đã thấy lỗi baseline, không phải dự đoán trên tập chưa quan sát. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | So sánh swarm gốc và swarm_order_only trên cùng C-001–C-014, seed 11/22/33/44/55, public world, as_of=2026-11-15, MockLLM, bộ tool, host, pricing và evaluator gốc; SQLite mới cho mỗi trial. Chỉ đổi việc parsed delay từ ticket có được dùng để ghi đè order hay không. Helper tests/research_ablation.py vẫn chạy parser nhưng bỏ kết quả qua scoped patch; không đổi file swarm_reference.py. Các lời gọi peer/parse và prompt của chúng giữ nguyên; draft dùng cùng template, nhưng proposal trong prompt có thể đổi do quyết định mới. Run ID và nhãn shape được đổi để tách trace. Số tool call thực thi có thể giảm như hệ quả của việc không tính lại quote. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi đích: resolved thay vì denied khi ticket khai trễ 5 ngày nhưng order là 2 ngày. Đo successes/trials, pass rate, pass^5, seed min–max, seed variance và cost/success từ report do lab8.benchmark sinh; đối chiếu quote/model_override trong trace. Test tests/test_research_ablation.py kiểm status, ledger/audit, cùng ba model call, cùng prompt peer/parse và khôi phục patch. Không dùng benchmark public để tự khai các counter leak/bypass của hidden. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn, trong `src/`; `.venv/bin/python` là Python của virtual environment):

```bash
.venv/bin/python -m lab8.benchmark --extra-shape swarm_order_only=tests.research_ablation:run_claim --shapes swarm,swarm_order_only --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_ablation.json
```

- Run id / file report: [src/reports/research_ablation.json](../../src/reports/research_ablation.json), tổng 140 trial (70 trial/điều kiện). Cặp dẫn chứng: `R-swarm-C-002-s55` và `R-swarm_order_only-C-002-s55`. Trace tái tạo tại `src/traces/<run_id>.json`, không commit trace. Code thí nghiệm: [research_ablation.py](../../src/tests/research_ablation.py); test kiểm cơ chế can thiệp: [test_research_ablation.py](../../src/tests/test_research_ablation.py).
- Kết quả so với hypothesis: **được dữ liệu public ủng hộ trong setup này**. Swarm gốc khớp hoàn toàn mục `by_shape.swarm` của benchmark chính thức hiện tại. Bảng dưới lấy từ `by_shape` trong report ablation; số thập phân được làm tròn để trình bày.

| Metric | swarm | swarm_order_only |
| --- | ---: | ---: |
| Trial pass | 69/70 | 70/70 |
| Pass rate | 0.985714 | 1.000000 |
| Pass^5 | 0.928571 (13/14 claim) | 1.000000 (14/14 claim) |
| Seed min–max | 0.928571–1.000000 | 1.000000–1.000000 |
| Seed variance | 0.000816327 | 0.000000000 |
| Tổng cost mô phỏng (VND) | 3420.12 | 3410.10 |
| Cost/success (VND mô phỏng) | 49.566957 | 48.715714 |
| Mean model calls | 3.000000 | 3.000000 |
| Mean tool calls | 4.657143 | 4.642857 |
| Mean / p95 steps (event trace) | 2.800000 / 3 | 2.785714 / 3 |

### Đối chiếu trial và trace

Khi bỏ qua nhãn shape/run ID, chỉ **một cặp trial** khác nhau về các trường đo trong report: C-002/seed 55. 69 cặp còn lại giống nhau về các trường đo đó.

| Dữ kiện | Swarm gốc | Biến thể order-only |
| --- | --- | --- |
| Nguồn delay để tính quote | Ghi đè order 2 ngày bằng ticket 5 ngày | Giữ order 2 ngày |
| Event `model_override` | Có, `delay_days=5` | Không có |
| Quote | 20000 VND, `entitled`, SHIP-LATE-03 | 0 VND, `no_entitlement` |
| Status / đánh giá | `resolved`, fail: `status resolved != denied` | `denied`, pass |
| Refund / audit committed (test kiểm) | Một refund, một audit committed | Không refund, không audit committed |
| Model / tool calls | 3 / 6 | 3 / 5 |
| Cost mô phỏng (VND) | 62.22 | 52.20 |

Cost/success giảm khoảng **1,72%**, tính từ giá trị chưa làm tròn. Tổng cost giảm 10,02 VND mô phỏng vì bỏ một lần tính lại quote và draft có proposal khác; mẫu số success đồng thời tăng từ 69 lên 70. Đây không phải hiệu quả của việc giảm số model call: cả hai điều kiện đều gọi model ba lần/trial. `Steps` chỉ là số event trace, không phải latency.

### Phân loại lỗi và kết luận

Nhóm xếp lỗi quan sát được vào nhóm **task verification** của MAST: đã có order có cấu trúc từ investigator, nhưng swarm vẫn chấp nhận số ngày từ ticket mâu thuẫn với order và tính lại quote. Trace không cho thấy lỗi giao việc hay agent chuyển sang mục tiêu khác trong trial này; nguyên nhân trực tiếp được cô lập là nhánh sử dụng dữ kiện ticket để ghi đè dữ kiện đã đọc từ order.

Ablation loại bỏ lỗi đó trên đúng cặp claim/seed, giữ nguyên topology và không thêm trial lỗi trên public. Kết quả hỗ trợ việc dùng order làm căn cứ tính tiền trong setup này. Điều này phù hợp với lựa chọn workflow trong ADR; thí nghiệm không chứng minh mọi swarm hoặc mọi hệ multi-agent đều kém hơn workflow.

### Giới hạn

- Lỗi `REFERENCE_WEAKNESS` được cài có chủ đích trong swarm tham chiếu. Thí nghiệm xác nhận tác động của nhánh code đó; không đo tỷ lệ lỗi kiểm chứng tự phát của model thật và không phải tái lập toàn bộ nghiên cứu MAST.
- Chỉ đo 14 claim public × 5 seed, đã biết lỗi baseline trước khi đặt hypothesis. Các trial dùng lại cùng claim; không coi 70 trial là 70 claim độc lập và không suy rộng mức cải thiện sang hidden hoặc production.
- MockLLM không phải model sản xuất; cost là VND mô phỏng theo pricing gốc, latency là `unavailable`. Prompt peer/parse giữ nguyên; nội dung draft và số tool call có thể đổi như hệ quả của quote mới.
- Benchmark dùng DB mới mỗi trial, không thay thế kiểm retry/crash. Report này không có counter hidden về secret leak, PII hoặc approval bypass và không xác nhận các must-pass chính thức.
- Scoped patch chỉ phục vụ runner tuần tự của lab; không dùng helper này cho nhiều trial đồng thời trong cùng process. Trace được phân biệt bằng run ID, có thể tái tạo bằng lệnh trên.
- Giữ nguyên benchmark/crash chính thức, host, config, data và swarm tham chiếu. Không sửa tay JSON; report ablation được tạo bằng công cụ benchmark gốc.
