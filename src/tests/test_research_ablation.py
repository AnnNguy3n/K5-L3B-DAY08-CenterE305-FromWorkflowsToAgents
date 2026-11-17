"""Verify the R2 intervention on the published conflicting-ticket case."""

import json
from pathlib import Path
from unittest.mock import patch

from lab8.db import connect, init_store
from lab8.metrics import trial_pass
from lab8.shapes import swarm_reference
from tests.conftest import BY_ID, CLAIMS, WORLD
from tests.research_ablation import VARIANT, run_claim


def test_order_only_fixes_conflicting_ticket_without_changing_upstream_model_calls(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    original_parser = swarm_reference.parse_delay_days
    original_run_id = swarm_reference.make_run_id
    results = {}
    prompts = {}

    for name, runner in (("swarm", swarm_reference.run_claim), (VARIANT, run_claim)):
        store = tmp_path / f"{name}.sqlite"
        init_store(store, WORLD, CLAIMS).close()
        with patch.object(swarm_reference, "complete", wraps=swarm_reference.complete) as model:
            result = runner("C-002", seed=55, store_path=str(store))
        prompts[name] = [call.kwargs for call in model.call_args_list]
        conn = connect(store)
        try:
            grade = trial_pass(result.as_dict(), BY_ID["C-002"]["expected"], conn)
        finally:
            conn.close()
        trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        results[name] = result, grade, trace

    baseline, baseline_grade, baseline_trace = results["swarm"]
    variant, variant_grade, variant_trace = results[VARIANT]
    assert baseline_grade == (False, "status resolved != denied")
    assert baseline.status == "resolved"
    assert len(baseline.refund_effects) == 1
    assert baseline.committed_audit_count == 1
    assert variant_grade == (True, "ok")
    assert variant.status == "denied"
    assert variant.proposal_amount == 0
    assert variant.refund_effects == []
    assert variant.committed_audit_count == 0
    assert baseline.model_calls == variant.model_calls == 3
    assert prompts["swarm"][:2] == prompts[VARIANT][:2]
    assert [call["purpose"] for call in prompts["swarm"]] == [
        call["purpose"] for call in prompts[VARIANT]
    ]
    assert any(event["kind"] == "model_override" for event in baseline_trace["events"])
    assert not any(event["kind"] == "model_override" for event in variant_trace["events"])
    assert baseline.run_id != variant.run_id
    assert variant_trace["run_id"] == variant.run_id
    assert swarm_reference.parse_delay_days is original_parser
    assert swarm_reference.make_run_id is original_run_id
