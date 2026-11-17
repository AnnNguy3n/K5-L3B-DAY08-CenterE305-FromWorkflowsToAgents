"""Shape C — orchestrator plus read-only investigators. Student work.

The orchestrator uses a sanitized handoff for investigation. The host remains
the only writer and validates the full compensation quote before refunding.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import dispatch, run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = None
    budget = Budget()
    run_id = make_run_id("orchestrator", claim_id, seed)
    trace = Trace(run_id)
    try:
        conn = connect(store_path)
        claim = dispatch(conn, budget, "get_claim_view", {"claim_id": claim_id}, worker=False)
        if not claim.get("found"):
            trace.add("decision", {"status": "failed", "reason": "unknown_claim"})
            return finish(
                conn,
                shape="orchestrator",
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="unknown_claim",
            )
        if not claim.get("order_id"):
            trace.add("decision", {"status": "needs_info", "reason": "missing_order_id"})
            return finish(
                conn,
                shape="orchestrator",
                claim_id=claim_id,
                seed=seed,
                status="needs_info",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason="missing_order_id",
            )

        complete(
            budget,
            seed=seed,
            purpose="orchestrator",
            prompt="delegate a scoped claim investigation",
        )
        handoff = make_handoff(
            request_id=f"REQ-{claim_id}",
            claim_id=claim_id,
            task="verify_order_and_compute_full_compensation",
            facts={},
            allowed_tools=[
                "lookup_order",
                "lookup_policy",
                "lookup_refund_history",
                "compute_compensation",
            ],
        )
        trace.add("handoff", safe_dump(handoff))
        investigation = run_readonly_investigators(
            conn,
            budget,
            handoff,
            principal_id=claim["principal_id"],
        )
        tools = investigation["tools"]
        order_view = tools.get("lookup_order") or {}
        history = tools.get("lookup_refund_history") or {}
        policies = tools.get("lookup_policy") or {}
        trace.add(
            "investigator",
            {
                "order_visible": bool(order_view.get("visible")),
                "order_reason": order_view.get("reason"),
                "policy_count": len(policies.get("policies") or []),
                "refund_count": history.get("refund_count"),
                "refunded_vnd": history.get("refunded_vnd"),
            },
        )
        if not order_view.get("visible"):
            return finish(
                conn,
                shape="orchestrator",
                claim_id=claim_id,
                seed=seed,
                status="escalated",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=order_view.get("reason"),
            )

        quote: dict[str, Any] = tools["compute_compensation"]
        proposal = int(quote["amount_vnd"])
        trace.add(
            "quote",
            {
                "amount_vnd": proposal,
                "reason": quote.get("reason"),
                "clause_ids": quote.get("clause_ids", []),
                "parts": quote.get("parts", {}),
            },
        )
        if proposal <= 0:
            return finish(
                conn,
                shape="orchestrator",
                claim_id=claim_id,
                seed=seed,
                status="denied",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=quote.get("reason"),
            )

        result = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not result["ok"]:
            status = "failed" if result["conflict"] else "denied"
            error_reason = result["reason"]
        else:
            status = "resolved"
            error_reason = None
        trace.add("host_result", {"status": status, "error_reason": error_reason})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    except Exception as exc:
        error_reason = f"internal_error:{type(exc).__name__}"
        trace.add("error", {"reason": error_reason})
        if conn is None:
            trace_path = trace.write()
            return RunResult(
                run_id=run_id,
                claim_id=claim_id,
                shape="orchestrator",
                seed=seed,
                status="failed",
                proposal_amount=0,
                refund_effects=[],
                committed_audit_count=0,
                model_calls=budget.model_calls,
                tool_calls=budget.tool_calls,
                input_tokens=budget.input_tokens,
                output_tokens=budget.output_tokens,
                cost_estimate=round(budget.cost_estimate, 6),
                trace_path=trace_path,
                error_reason=error_reason,
            )
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )
    finally:
        if conn is not None:
            conn.close()
