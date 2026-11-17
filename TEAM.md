# Team — CenterE305

## Thông tin nhóm

- Tên nhóm: CenterE305
- Lớp: K5 — L3B
- Repo nhóm: `K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents`
- URL repo: https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents
- Nhánh nộp: `main`
- Commit chốt mã nguồn và minh chứng: `cdbad20bca37355086539d0472850edb7ed38404`, trùng mốc tái lập trong [ADR](report/team/decision_adr.md).
- Các mốc đóng góp: tích hợp ba shape ở `70c00ff`, benchmark/crash/ADR ở `68234fa`, R2 ở `3868fe8`, tự kiểm không nhãn và chốt minh chứng ở `cdbad20`.

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Triệu Tuấn Minh | 2A202604123 | trieutuanminh004@gmail.com | [ttm4623](https://github.com/ttm4623) | Triển khai ban đầu single agent và orchestrator |
| 2 | Nguyễn Hữu An | 2A202604024 | 26ai.annh2@vinuni.edu.vn | [AnnNguy3n](https://github.com/AnnNguy3n) | Workflow, tích hợp ba shape, kiểm thử an toàn, benchmark và báo cáo |

## Bảng đóng góp

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Triệu Tuấn Minh | Triển khai single agent và orchestrator; bổ sung thông tin thành viên | [c5289c3](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/c5289c3ce75c471aab7c3de41dec072efdcf8799) | Chưa có commit thêm hoặc sửa test được ghi nhận trên nhánh `main` hiện tại. |
| Nguyễn Hữu An | Triển khai workflow; bổ sung xử lý crash, ranh giới tool và trace cho ba shape; tích hợp, đánh giá và báo cáo | [ff0ea62](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/ff0ea6238ecee5de3d1d29a96fc70d8366404f05), [70c00ff](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/70c00ff884e690a3427f37ae9a85b597adbe3494), [68234fa](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/68234fa950ea71a6c966139f0f971edcda85d819) | Thêm [test_workflow.py](src/tests/test_workflow.py), [test_agent_shapes.py](src/tests/test_agent_shapes.py) trong `ff0ea62`: crash/resume, quote conflict, ticket injection, approval sai claim, giới hạn ReAct và handoff chỉ đọc. Bổ sung [test_research_ablation.py](src/tests/test_research_ablation.py) cho R2 trong đợt CP5. |

Bảng trên ghi theo lịch sử commit hiện có. Phần test của Minh chưa có bằng chứng để xác nhận đáp ứng đầy đủ yêu cầu đóng góp C8; nhóm không tính các test do An thêm thành đóng góp test của Minh.

## Báo cáo và minh chứng

- [Báo cáo nhóm](report/team/group_report.md).
- [Quyết định kiến trúc](report/team/decision_adr.md): chọn workflow theo kết quả public.
- [Research card R2](report/team/research_card.md): phân tích lỗi kiểm chứng dữ kiện của swarm và ablation order-only.
- [Benchmark bốn shape](src/reports/benchmark.json), [crash suite](src/reports/crash.json), [report R2](src/reports/research_ablation.json), [tự kiểm không nhãn](src/reports/hidden_selfcheck.json).

## Cá nhân

| Thành viên | Báo cáo | Tình trạng |
| --- | --- | --- |
| Nguyễn Hữu An | [2A202604024_NguyenHuuAn.md](report/team/2A202604024_NguyenHuuAn.md) | Đã điền nội dung và minh chứng |
| Triệu Tuấn Minh | [2A202604123_TrieuTuanMinh.md](report/team/2A202604123_TrieuTuanMinh.md) | Bản sao nguyên mẫu, Đã điền nội dung |
