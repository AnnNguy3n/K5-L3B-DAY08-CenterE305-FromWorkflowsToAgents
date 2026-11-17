"""R2 research variant: ignore ticket delay when deciding compensation.

Loaded only through benchmark --extra-shape. The reference implementation,
MockLLM calls, host and evaluator stay unchanged. Scoped patches are intended
for the lab's sequential runner, not concurrent calls in the same process.
"""

from __future__ import annotations

from unittest.mock import patch

from lab8.schemas import RunResult, make_run_id
from lab8.shapes import swarm_reference

VARIANT = "swarm_order_only"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    parse_ticket = swarm_reference.parse_delay_days

    def ignore_parsed_delay(ticket: str) -> None:
        # Still execute parsing; only its use in the decision is disabled.
        parse_ticket(ticket)
        return None

    def variant_run_id(shape: str, cid: str, trial_seed: int) -> str:
        return make_run_id(VARIANT, cid, trial_seed)

    with (
        patch.object(swarm_reference, "parse_delay_days", side_effect=ignore_parsed_delay),
        patch.object(swarm_reference, "make_run_id", side_effect=variant_run_id),
    ):
        result = swarm_reference.run_claim(
            claim_id, seed=seed, store_path=store_path, crash_at=crash_at
        )

    # Metadata distinguishes results and traces; business logic stays in reference.
    result.shape = VARIANT
    return result
