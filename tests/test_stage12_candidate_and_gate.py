import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis" / "pscad_tools"))

from stage12_common import detect_bypass_or_isolated, evaluate_second_trip_candidate


def test_candidate_threshold_rejects_pre_pickup_and_short_window():
    t = [i / 100 for i in range(0, 1601)]
    not_above_pre = [12.0 if x <= 7.53 else 11.0 for x in t]
    result = evaluate_second_trip_candidate("E_TEST", t, not_above_pre, first_open_s=7.53)
    assert not result.eligible
    assert result.rejection_reason == "post_5s_floor_not_above_pre_first_trip_max"

    short = [1.0 for _ in t]
    short = [5.0 if 8.0 <= x <= 11.0 else v for x, v in zip(t, short)]
    result = evaluate_second_trip_candidate("E_TEST", t, short, first_open_s=7.53)
    assert not result.eligible


def test_candidate_threshold_freezes_feasible_capacity():
    t = [i / 100 for i in range(0, 1601)]
    s = [1.0 if x <= 7.53 else 4.0 for x in t]
    result = evaluate_second_trip_candidate("E_TEST", t, s, first_open_s=7.53)
    assert result.eligible
    assert result.pre_first_trip_max_s == 1.0
    assert result.post_first_trip_5s_floor_s == 4.0
    assert result.threshold_t == 2.5
    assert abs(result.effective_capacity_c_eff - (2.5 / 1.1)) < 1e-12


def test_pre_run_gate_rejects_isolated_bypass_and_forbidden_driver():
    before = [{"compiled_bus": 1}, {"compiled_bus": 2}]
    isolated = [{"compiled_bus": 1}, {"compiled_bus": 0}]
    result = detect_bypass_or_isolated(before, isolated, True, True, [])
    assert not result["passed"]
    assert not result["no_isolated_bus"]

    forbidden = detect_bypass_or_isolated(before, before, True, True, ["PAPER_OVL2_BRK_CMD = DFIG_LVRT_CASCADE_EVENT_VALID"])
    assert not forbidden["passed"]
    assert forbidden["forbidden_driver_hits"]
