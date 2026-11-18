"""M1 trace case regression (docs/trace_case.md): swarm C-002@55, FM-03 ticket_trust.

The first wrong step is event #3 `model_override {"delay_days": 5}`: the ticket says 5 days late,
the DB (event #2) says 2. These tests pin that the step-level grader DbFactKept and the ledger
check both flag the bad trace, and stay quiet on `fixed` for the same claim@seed.
"""
import pytest

pytestmark = pytest.mark.student

CLAIM, SEED = "C-002", 55


def run(shape: str, seed: int = SEED) -> dict:
    from lab9.trace_case import investigate

    return investigate(shape, CLAIM, seed)


def db_fact_kept(trial: dict) -> bool:
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import DbFactKept

    ctx = EvaluatorContext(name="trace_case", inputs={}, metadata=None, expected_output=None, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return DbFactKept().evaluate(ctx).value


def first_override(trial: dict) -> tuple[int, dict] | None:
    for i, e in enumerate(trial["events"], 1):
        if e.get("kind") == "model_override":
            return i, e["payload"]
    return None


@pytest.mark.parametrize("shape", ["swarm", "seeded_regression"])
def test_lab9_trace_case_fm03_flagged_on_buggy_shapes(shape):
    case = run(shape)
    trial, label = case["trial"], case["label"]
    db_delay = trial["events"][1]["payload"]["lookup_order"]["order"]["delay_days"]
    assert db_delay == 2
    assert first_override(trial) == (3, {"delay_days": 5}), "first wrong step moved"
    assert db_fact_kept(trial) is False
    assert trial["snapshot"]["refund_vnd"] != label["refund_vnd"]  # ledger 20000, label 0


def test_lab9_trace_case_fm03_clean_on_fixed():
    case = run("fixed")
    trial, label = case["trial"], case["label"]
    assert first_override(trial) is None
    assert db_fact_kept(trial) is True
    assert trial["snapshot"]["refund_vnd"] == label["refund_vnd"] == 0
    assert trial["result"]["status"] == label["status"] == "denied"


@pytest.mark.parametrize("seed", [11, 22, 33, 44])
def test_lab9_trace_case_swarm_other_seeds_keep_db_fact(seed):
    # The baseline only overrides at seed 55: a 1-in-5 failure a single-seed eval would miss.
    assert db_fact_kept(run("swarm", seed)["trial"]) is True
