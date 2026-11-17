# Báo cáo cá nhân — 2A202604123_TrieuTuanMinh

## 1. Thông tin thành viên

- Họ tên: Triệu Tuấn Minh
- MSSV: `2A202604123`
- Email: trieutuanminh004@gmail.com
- GitHub: [ttm4623](https://github.com/ttm4623)
- Nhóm: CenterE305, lớp K5 — L3B.
- Repo: [K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents), nhánh `main`.

## 2. Phần việc phụ trách

Em phụ trách triển khai ban đầu hai shape **single agent** và **orchestrator**. Theo mô tả giải pháp của nhóm, single xử lý theo vòng ReAct có giới hạn; orchestrator chuyển handoff cho investigator với quyền đọc dữ liệu và để orchestrator gọi host khi có quote phù hợp. Workflow, tích hợp các shape, bổ sung kiểm thử an toàn và các đợt benchmark/báo cáo tiếp theo do phần việc của thành viên còn lại đảm nhiệm.

## 3. Đóng góp cụ thể

- Commit kỹ thuật được ghi nhận cho phần triển khai ban đầu: [`c5289c3`](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/c5289c3ce75c471aab7c3de41dec072efdcf8799), gồm single agent và orchestrator.
- Các thay đổi tích hợp và kiểm thử về sau được ghi trong lịch sử đóng góp của nhóm, không tính là commit cá nhân của em.
- Theo bảng đóng góp trong `TEAM.md`, nhánh `main` hiện không ghi nhận commit em thêm hoặc sửa test. Vì vậy em không nhận các test do thành viên khác viết là minh chứng kiểm thử cá nhân; yêu cầu về test trong bảng đóng góp C8 vẫn còn thiếu bằng chứng thuộc phần em.

## 4. Bằng chứng

| Minh chứng | Nội dung |
| --- | --- |
| [Commit `c5289c3`](https://github.com/AnnNguy3n/K5-L3B-DAY08-CenterE305-FromWorkflowsToAgents/commit/c5289c3ce75c471aab7c3de41dec072efdcf8799) | Mốc triển khai ban đầu single agent và orchestrator, theo `TEAM.md`. |
| [Báo cáo nhóm](group_report.md) | Mô tả hành vi ba shape, kết quả benchmark và các hạn chế; số liệu tại đây là kết quả chung của nhóm. |
| [Benchmark nhóm](../../src/reports/benchmark.json) | Benchmark public có 14 claim × 5 seed cho mỗi shape; single và orchestrator đều đạt 70/70 trial. Đây là kết quả của bản tích hợp, không phải phép đo riêng cho commit của em. |
| [Test shape](../../src/tests/test_agent_shapes.py) | Có kiểm tra crash/resume, approval sai claim, injection, giới hạn ReAct và handoff chỉ đọc; file này được nhóm ghi nhận do An thêm, không phải test em viết. |

## 5. Công cụ AI đã dùng

Trong quá trình hoàn thiện báo cáo này, em dùng Copilot để đối chiếu thông tin giữa hồ sơ thành viên, báo cáo nhóm và các minh chứng trong repository, rồi biên tập nội dung cho đúng phạm vi đóng góp. Em không dùng AI để suy đoán commit, số liệu hoặc test thuộc về mình; các thông tin trên được đối chiếu với `TEAM.md`, báo cáo nhóm và các file minh chứng. Theo quy định của lab, model trong code là MockLLM; code lab không gọi model/API thật.

## 6. Tự đánh giá

Em đã đóng góp phần triển khai ban đầu cho hai cách tổ chức agent, tạo cơ sở để nhóm tích hợp và so sánh các shape. Kết quả benchmark chung cho thấy single và orchestrator đều đạt 70/70 trial trên bộ public; tuy nhiên, đây là kết quả của phiên bản tích hợp và không thể quy toàn bộ cho phần việc cá nhân của em.

Điểm em cần hoàn thiện là bổ sung minh chứng test do chính em viết hoặc sửa. Trên nhánh hiện tại, `TEAM.md` chưa ghi nhận test của em, nên đóng góp chưa đáp ứng đầy đủ yêu cầu báo cáo C8. Nếu tiếp tục phát triển, em sẽ bổ sung test tập trung cho hành vi của single/orchestrator và liên kết test đó với commit cụ thể, đồng thời tiếp tục kiểm tra các ranh giới handoff, quyền gọi tool và xử lý crash.
