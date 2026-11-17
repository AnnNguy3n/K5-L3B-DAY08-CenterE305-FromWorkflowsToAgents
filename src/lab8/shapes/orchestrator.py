"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

MockLLM acknowledges the plan, investigator task and draft reply. The tool plan
and all money decisions remain bounded by code; no model text grants a tool.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("orchestrator", claim_id, seed))
    conn = connect(store_path)

    def finish_result(
        status: str,
        proposal_amount: int = 0,
        error_reason: str | None = None,
    ) -> RunResult:
        reply = complete(
            budget, seed=seed, purpose="draft",
            prompt=f"status={status}; proposal_amount={proposal_amount}",
        )
        trace.add("reply", {"text": reply})
        trace.add("decision", {
            "status": status,
            "proposal_amount": proposal_amount,
            "reason": error_reason,
        })
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("claim", {"found": claim["found"]})
        if not claim["found"]:
            return finish_result("failed", error_reason="unknown_claim")
        if not claim.get("order_id"):
            return finish_result("needs_info", error_reason="missing_order_id")

        # Code bounds the plan. The investigator receives no parent context.
        task = "check_applicable_policy"
        allowed_tools = ["lookup_order", "lookup_policy", "compute_compensation"]
        plan = complete(
            budget, seed=seed, purpose="plan",
            prompt=f"task={task}; read_tools={','.join(allowed_tools)}",
        )
        trace.add("plan", {"task": task, "text": plan})
        handoff = make_handoff(
            request_id=f"REQ-{claim_id}",
            claim_id=claim_id,
            task=task,
            facts={},
            allowed_tools=allowed_tools,
        )
        trace.add("handoff", handoff)
        peer = complete(
            budget, seed=seed, purpose="peer",
            prompt=json.dumps(handoff, ensure_ascii=False),
        )
        trace.add("investigator", {"text": peer})
        investigated = run_readonly_investigators(
            conn, budget, handoff, principal_id=claim["principal_id"],
        )
        tools = investigated["tools"]
        order_view = tools["lookup_order"]
        trace.add("order", {
            "visible": order_view["visible"],
            "reason": order_view["reason"],
        })
        if not order_view["visible"]:
            return finish_result("escalated", error_reason=order_view["reason"])

        quote = tools.get("compute_compensation")
        if quote is None:
            return finish_result("failed", error_reason="missing_quote")
        proposal = int(quote["amount_vnd"])
        trace.add("quote", quote)
        if proposal <= 0:
            return finish_result("denied", error_reason=quote["reason"])

        # The investigator cannot write; only the orchestrator calls the host.
        # Keep the full entitlement so the host subtracts prior refunds once.
        trace.add("refund_requested", {"proposal_amount": proposal})
        trace.write()
        refund = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not refund["ok"]:
            status = "failed" if refund["conflict"] else "denied"
            return finish_result(status, proposal, refund["reason"])
        return finish_result("resolved", proposal)
    finally:
        conn.close()
