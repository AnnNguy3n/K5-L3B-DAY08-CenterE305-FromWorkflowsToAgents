# src/reports/

Mọi lệnh dưới đây chạy trong thư mục `src/`, nên file JSON được ghi vào `src/reports/`.

Nhóm **commit** các file do công cụ của lab sinh ra. Đây là bằng chứng nộp bài:

| File | Lệnh tạo | Bắt buộc |
| --- | --- | --- |
| `benchmark.json` | `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` | Có |
| `crash.json` | `python -m lab8.crash_test --count 20 --out reports/crash.json` | Có |
| `research_ablation.json` | `python -m lab8.benchmark --extra-shape swarm_order_only=tests.research_ablation:run_claim --shapes swarm,swarm_order_only --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_ablation.json` | Minh chứng R2 của nhóm |
| `hidden_selfcheck.json` | `python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --seeds 11,22,33,44,55 --out reports/hidden_selfcheck.json` | Không |
| `bonus_*.json` | script bonus của nhóm | Chỉ khi làm bonus |

Không sửa tay file JSON. Giảng viên chạy lại đúng các lệnh trên trên máy chấm. Số không khớp thì mục Reproducibility mất điểm. `hidden_grade.json` chỉ giảng viên tạo và bị gitignore.

`hidden_selfcheck.json` dùng claim không nhãn: chỉ kiểm lỗi chạy, Trace contract v1 và dấu hiệu rò canary; không tính pass rate hay xác nhận các counter hidden chính thức. Tái lập report này cần bộ `student_drop/` do giảng viên phát, không commit bộ dữ liệu đó.
