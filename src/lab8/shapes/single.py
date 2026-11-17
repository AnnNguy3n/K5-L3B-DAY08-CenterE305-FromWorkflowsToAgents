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

MockLLM returns seeded text, not structured tool actions. The demo maps
structured observations to allowlisted read actions in code; ticket text never
supplies tool arguments or the refund amount.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import ToolRejected, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
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
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    def draft_reply(status: str, proposal: int = 0) -> None:
        reply = complete(
            budget, seed=seed, purpose="draft",
            prompt=f"status={status}; proposal_amount={proposal}",
        )
        trace.add("reply", {"text": reply})

    try:
        conn = connect(store_path)
        order: dict[str, Any] | None = None
        principal_id: str | None = None

        def decide(observation: dict[str, Any]) -> dict[str, Any]:
            nonlocal order, principal_id
            step = budget.model_calls + 1
            reply = complete(
                budget,
                seed=seed,
                purpose="react",
                prompt=f"single-agent step={step}",
            )
            trace.add("model", {"purpose": "react", "text": reply})

            last_tool = observation.get("last_tool")
            result = observation.get("last_result") or {}
            if last_tool is None:
                action = {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
            elif last_tool == "get_claim_view":
                if not result.get("found"):
                    action = {"final": {"status": "failed", "error_reason": "unknown_claim"}}
                elif not result.get("order_id"):
                    action = {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}
                else:
                    principal_id = result["principal_id"]
                    action = {
                        "tool": "lookup_order",
                        "args": {
                            "order_id": result["order_id"],
                            "principal_id": result["principal_id"],
                        },
                    }
            elif last_tool == "lookup_order":
                if not result.get("visible"):
                    action = {
                        "final": {
                            "status": "escalated",
                            "error_reason": result.get("reason"),
                        }
                    }
                else:
                    order = result["order"]
                    action = {
                        "tool": "lookup_refund_history",
                        "args": {
                            "order_id": order["order_id"],
                            "principal_id": principal_id,
                        },
                    }
            elif last_tool == "lookup_refund_history":
                if not result.get("visible"):
                    action = {
                        "final": {
                            "status": "escalated",
                            "error_reason": result.get("reason"),
                        }
                    }
                elif order is None or principal_id is None:
                    action = {"final": {"status": "failed", "error_reason": "missing_order"}}
                else:
                    action = {"tool": "compute_compensation", "args": {"order": order}}
            elif last_tool == "compute_compensation":
                amount = int(result["amount_vnd"])
                action = {
                    "final": {
                        "status": "denied" if amount <= 0 else "quoted",
                        "proposal_amount": amount,
                        "quote": result,
                        "error_reason": result.get("reason") if amount <= 0 else None,
                    }
                }
            else:
                action = {"final": {"status": "failed", "error_reason": "unexpected_react_step"}}

            if "tool" in action:
                trace.add("react_step", {"step": step, "tool": action["tool"]})
            else:
                final = action["final"]
                trace.add("react_decision", {
                    "step": step,
                    "status": final["status"],
                    "error_reason": final.get("error_reason"),
                })
            return action

        outcome = run_react(
            conn,
            budget,
            observation={},
            decide=decide,
            max_steps=8,
            worker=True,
        )
        decision = outcome["final"]
        status = decision["status"]
        proposal = int(decision.get("proposal_amount", 0))
        if "quote" in decision:
            quote = decision["quote"]
            trace.add(
                "quote",
                {
                    "amount_vnd": proposal,
                    "reason": quote.get("reason"),
                    "clause_ids": quote.get("clause_ids", []),
                    "parts": quote.get("parts", {}),
                },
            )

        if status != "quoted":
            draft_reply(status, proposal)
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status=status,
                proposal_amount=proposal,
                budget=budget,
                trace=trace,
                error_reason=decision.get("error_reason"),
            )

        # Persist safe progress; only code outside ReAct calls the host writer.
        trace.add("refund_requested", {"proposal_amount": proposal})
        trace.write()
        result = issue_refund(conn, claim_id, proposal, crash_at=crash_at)

        if not result["ok"]:
            status = "failed" if result["conflict"] else "denied"
            error_reason = result["reason"]
        else:
            status = "resolved"
            error_reason = None
        trace.add("host_result", {"status": status, "error_reason": error_reason})
        draft_reply(status, proposal)
        return finish(
            conn,
            shape="single",
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
        error_reason = "tool_rejected" if isinstance(exc, ToolRejected) else f"internal_error:{type(exc).__name__}"
        trace.add("error", {"reason": error_reason})
        if conn is None:
            trace_path = trace.write()
            return RunResult(
                run_id=run_id,
                claim_id=claim_id,
                shape="single",
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
            shape="single",
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
