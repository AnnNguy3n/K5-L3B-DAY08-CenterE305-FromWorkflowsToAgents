"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

MockLLM returns seeded text, not structured tool actions. In this demo, decide
maps structured observations to read actions in code and records each simulated
model turn. Ticket text never supplies tool arguments or the refund amount.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import ToolRejected, run_react
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
    trace = Trace(make_run_id("single", claim_id, seed))
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
            shape="single",
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

        # The runtime keeps only the last observation; retain the scoped order.
        order: dict[str, Any] = {}

        def decide(observation: dict[str, Any]) -> dict[str, Any]:
            nonlocal order
            last_tool = observation.get("last_tool")
            last_result = observation.get("last_result") or {}
            reply = complete(
                budget, seed=seed, purpose="react",
                prompt=f"Select the next read step after {last_tool or 'start'}.",
            )
            trace.add("model", {"purpose": "react", "text": reply})

            if last_tool is None:
                action = {
                    "tool": "lookup_order",
                    "args": {
                        "order_id": claim["order_id"],
                        "principal_id": claim["principal_id"],
                    },
                }
            elif last_tool == "lookup_order":
                trace.add("order", {
                    "visible": last_result["visible"],
                    "reason": last_result["reason"],
                })
                if not last_result["visible"]:
                    action = {"final": {
                        "status": "escalated", "error_reason": last_result["reason"],
                    }}
                else:
                    order = last_result["order"]
                    action = {"tool": "lookup_policy", "args": {}}
            elif last_tool == "lookup_policy":
                trace.add("policy", {"count": len(last_result["policies"])})
                action = {"tool": "compute_compensation", "args": {"order": order}}
            elif last_tool == "compute_compensation":
                trace.add("quote", last_result)
                action = {"final": {"quote": last_result}}
            else:
                action = {"final": {"status": "failed", "error_reason": "unexpected_tool"}}

            # Log action names only, never raw observations, arguments or tickets.
            trace.add("react_action", {"tool": action.get("tool"), "final": "final" in action})
            return action

        try:
            outcome = run_react(
                conn,
                budget,
                observation={"claim": {
                    "claim_id": claim_id,
                    "order_id": claim["order_id"],
                    "principal_id": claim["principal_id"],
                }},
                decide=decide,
                max_steps=8,
                worker=True,
            )
        except ToolRejected:
            return finish_result("failed", error_reason="tool_rejected")

        if outcome["stopped"] != "final":
            return finish_result("failed", error_reason="step_cap")
        final = outcome["final"]
        if "quote" not in final:
            return finish_result(final["status"], error_reason=final.get("error_reason"))

        proposal = int(final["quote"]["amount_vnd"])
        if proposal <= 0:
            return finish_result("denied", error_reason=final["quote"]["reason"])

        # Only shape code reaches the writer, after the read-only loop finishes.
        trace.add("refund_requested", {"proposal_amount": proposal})
        trace.write()
        refund = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        if not refund["ok"]:
            status = "failed" if refund["conflict"] else "denied"
            return finish_result(status, proposal, refund["reason"])
        return finish_result("resolved", proposal)
    finally:
        conn.close()
