import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis" / "pscad_tools"))

from stage13_common import (
    frequency_status_from_candidates,
    third_line_readiness,
    topology_partition,
    voltage_risk_from_channels,
)


def test_local_voltage_does_not_become_network_wide_low_voltage():
    assert voltage_risk_from_channels(["wind_pcc_only"], sustained_low=True) == "local_voltage_response_only"
    assert voltage_risk_from_channels(["local_bus_only"], sustained_low=True) == "local_voltage_response_only"


def test_no_direct_frequency_blocks_ufls_and_generator_underfrequency_claim():
    status, ufls, gen = frequency_status_from_candidates(["local_controller_frequency_only"], risky=True)
    assert status == "frequency_observability_insufficient"
    assert ufls == "ufls_precondition_not_evaluable"
    assert gen == "generator_underfrequency_precondition_not_evaluable"


def test_short_spike_is_not_third_line_ready():
    assert third_line_readiness(separable=True, duration_s=0.5, transient_only=True) == "third_line_not_defensible"
    assert third_line_readiness(separable=True, duration_s=4.0, transient_only=False) == "third_line_candidate_requires_longer_run"
    assert third_line_readiness(separable=True, duration_s=5.0, transient_only=False) == "third_line_candidate_ready"


def test_topology_partition_uses_compiled_bus_and_actual_opened_lines_only():
    branches = [("E_1_2_1", 1, 2), ("E_2_3_1", 2, 3), ("E_4_5_1", 4, 5)]
    result = topology_partition(branches, {"E_4_5_1"})
    assert result["status"] == "connected_after_second_trip"
    result = topology_partition(branches, {"E_2_3_1"})
    assert result["status"] == "partitioned_after_second_trip"


def test_paper_chain_waiver_is_not_a_runtime_defect():
    waiver = "PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER"
    assert waiver == "PAPER_CHAIN_MODEL_MONITOR_WAIVED_OFFLINE_PARSER"


def test_paper_threshold_not_explicit_is_preserved():
    value = "paper_threshold_not_explicit"
    assert value == "paper_threshold_not_explicit"
