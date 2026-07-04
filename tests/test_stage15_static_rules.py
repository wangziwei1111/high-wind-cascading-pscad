import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "analysis" / "pscad_tools"
sys.path.insert(0, str(TOOLS))

from stage15_common import OUTPUT_CHANNELS  # noqa: E402


def run_tool(script: str) -> None:
    subprocess.run([sys.executable, str(TOOLS / script)], cwd=REPO, check=True)


def load_json(path: str) -> dict:
    return json.loads((REPO / path).read_text(encoding="utf-8"))


def test_stage15_clean_baseline_has_no_legacy_ovl_relays():
    run_tool("audit_stage15_clean_baseline_and_source_recovery.py")
    manifest = load_json("data/reference/stage15_clean_baseline_selection.json")
    assert manifest["baseline_go_no_go"] == "GO"
    assert manifest["active_PAPER_OVL1_count"] == 0
    assert manifest["active_PAPER_OVL2_count"] == 0


def test_stage15_bus30_recovery_uses_g30_definition_not_parallel_dfig():
    run_tool("audit_stage15_clean_baseline_and_source_recovery.py")
    recovery = load_json("data/reference/stage15_bus30_sync_recovery_map.json")
    assert recovery["definition_name"] == "G_30_0_1_DYR"
    assert recovery["status"] == "recoverable_by_same_class_instance_template"
    assert recovery["parameters"]["P_MW"] == 250.0
    assert "Do not keep bus30 DFIG/IBR in parallel." in recovery["prohibited"]


def test_stage15_windfarm_replacements_are_exactly_three_independent_sources():
    run_tool("audit_stage15_clean_baseline_and_source_recovery.py")
    freeze = load_json("data/reference/stage15_pre_fault_power_balance_freeze.json")
    assert freeze["policy"] == "per_bus_replacement_equivalence"
    assert set(freeze["sources"]) == {"bus30", "WF33", "WF35", "WF38"}
    assert freeze["sources"]["WF33"]["target_bus"] == 33
    assert freeze["sources"]["WF35"]["target_bus"] == 35
    assert freeze["sources"]["WF38"]["target_bus"] == 38


def test_stage15_lvrt_instances_are_independent_and_not_fixed_time():
    run_tool("extract_stage15_paper_wf_layout_and_lvrt.py")
    freeze = load_json("data/reference/stage15_lvrt_module_parameter_freeze.json")
    assert freeze["instances"] == ["WF33_LVRT_TRIP", "WF35_LVRT_TRIP", "WF38_LVRT_TRIP"]
    assert freeze["state_independence_required"] is True
    assert "own PCC voltage" in freeze["input_rule"]
    assert "fixed-time" not in json.dumps(freeze, ensure_ascii=False).lower()


def test_stage15_output_minimum_is_exactly_15_channels():
    run_tool("audit_stage15_clean_baseline_and_source_recovery.py")
    manifest = load_json("data/reference/stage15_output_minimum_manifest.json")
    assert manifest["new_output_channel_count"] == 15
    assert manifest["new_output_channels"] == OUTPUT_CHANNELS


def test_stage15_gui_sheet_excludes_legacy_one_shot_and_ovl_driver_design():
    run_tool("audit_stage15_clean_baseline_and_source_recovery.py")
    sheet = (REPO / "docs/STAGE15_SINGLE_GUI_REFACTOR_BUILD_RUN_SHEET.md").read_text(encoding="utf-8")
    assert "no one-shot" in sheet
    assert "no old OVL signal" in sheet
    assert "PAPER_OVL1_BRK_CMD" not in sheet
    assert "PAPER_OVL2_BRK_CMD" not in sheet


def test_stage15_runtime_parser_is_guarded_before_gui_run():
    result = subprocess.run(
        [sys.executable, str(TOOLS / "analyze_stage15_wf33_35_38_runtime.py")],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 2
    audit = load_json("data/validation/stage15_runtime_input_audit.json")
    assert audit["status"] == "runtime_missing"
