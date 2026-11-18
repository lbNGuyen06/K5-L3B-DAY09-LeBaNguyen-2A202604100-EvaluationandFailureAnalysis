"""M3 FM-08 grader (ReplyMatchesLedger) on hand-built Trials, plus the real C-008 misreport."""
import pytest

pytestmark = pytest.mark.student


def evaluate(reply: str | None, ledger: int) -> bool:
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import ReplyMatchesLedger

    events = [] if reply is None else [{"kind": "reply", "payload": {"text": reply}}]
    trial = {"snapshot": {"refund_vnd": ledger}, "events": events}
    ctx = EvaluatorContext(name="t", inputs={}, metadata=None, expected_output={}, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return ReplyMatchesLedger().evaluate(ctx).value


@pytest.mark.parametrize("reply, ledger", [
    ("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.", 20000),
    ("LogiX đã hoàn phí 120.000đ cho đơn O-515 của anh/chị ạ.", 120000),
    ("Dạ, đơn O-202 chưa đủ điều kiện hoàn theo chính sách hiện hành.", 0),
    (None, 20000),                                       # no reply: nothing to misreport
    ("Anh/chị vui lòng cho LogiX xin mã đơn hàng ạ.", 0),
])
def test_lab9_reply_matches_ledger_passes(reply, ledger):
    assert evaluate(reply, ledger) is True


@pytest.mark.parametrize("reply, ledger", [
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.", 20000),  # C-008: approval caps 20000
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-909.", 0),      # C-007: denied, nothing refunded
    ("Dạ, LogiX đã hoàn 120.000đ cho đơn O-515.", 90000),  # C-014: deducted twice
    ("Đã hoàn 35,000 VND", 20000),
    ("hoàn 35k cho anh nhé", 20000),
    ("Em đã hoàn tiền cho anh rồi nha.", 0),              # claims a refund, no amount, ledger empty
])
def test_lab9_reply_matches_ledger_catches_misreport(reply, ledger):
    assert evaluate(reply, ledger) is False


def test_lab9_reply_matches_ledger_on_real_c008_trace():
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-008", 11)["trial"]
    good = investigate("fixed", "C-008", 11)["trial"]
    assert bad["lab8_pass"] is True            # Lab 8 grader misses it ...
    assert evaluate_trial(bad) is False        # ... the FM-08 grader does not
    assert evaluate_trial(good) is True


def evaluate_trial(trial: dict) -> bool:
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9.graders import ReplyMatchesLedger

    ctx = EvaluatorContext(name="t", inputs={}, metadata=None, expected_output={}, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return ReplyMatchesLedger().evaluate(ctx).value
