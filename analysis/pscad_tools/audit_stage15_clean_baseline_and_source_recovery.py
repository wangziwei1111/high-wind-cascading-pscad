#!/usr/bin/env python3
"""Stage 15 static baseline/source recovery audit and GUI sheet generator."""

from __future__ import annotations

import json
from datetime import datetime

from stage15_common import (
    BACKUP,
    EXPECTED_MAIN_SHA,
    GENERATOR_TARGETS,
    LEGACY_TRIAL,
    LEGACY_TRIAL_SHA,
    MAIN,
    NEW_TRIAL,
    OUTPUT_CHANNELS,
    PAPER_WIND_POWER,
    REPO,
    STAGE7_BASELINE,
    count_defs,
    count_user_refs,
    definition_params,
    p3_tline_edges,
    sha256,
    shortest_path,
    stage7_gf46,
    static_status_ready,
    write_csv,
    write_json,
)


def baseline_manifest(now: str) -> dict:
    active_ovl1 = count_user_refs(STAGE7_BASELINE, "PAPER_OVL1")
    active_ovl2 = count_user_refs(STAGE7_BASELINE, "PAPER_OVL2")
    return {
        "audit_name": "stage15_clean_baseline_selection",
        "generated_at_local": now,
        "selected_baseline_path": str(STAGE7_BASELINE),
        "selected_baseline_trial_sha": sha256(STAGE7_BASELINE),
        "selection_reason": "Stage7 backup is the latest clean local trial with full-network TLine measurement preparation and no active PAPER_OVL1/PAPER_OVL2 relay.",
        "why_not_stage12_or_stage13_trial": "Legacy Stage12/13 trial contains PAPER_OVL1/PAPER_OVL2, one-shot stimuli and legacy bus30 source/protection paths, so it is retained only as legacy_bus30_source_layout_protection_experiment.",
        "existing_tline_observability_count": 31,
        "existing_output_channel_count": "full-network TLine P/Q/I layer expected from Stage7 lineage; exact new trial count deferred to pre-run gate",
        "active_PAPER_OVL1_count": active_ovl1,
        "active_PAPER_OVL2_count": active_ovl2,
        "bus30_source_state": "G_30_0_1_DYR definition present; no active instance in current canvas; restore by copying a same-class synchronous-generator instance shell and binding it to G_30_0_1_DYR, per user clarification.",
        "bus33_source_state": "active synchronous generator G_33_0_1_DYR in baseline; to be replaced by WF33",
        "bus35_source_state": "active synchronous generator G_35_0_1_DYR in baseline; to be replaced by WF35",
        "bus38_source_state": "active synchronous generator G_38_0_1_DYR in baseline; to be replaced by WF38",
        "baseline_go_no_go": "GO" if active_ovl1 == 0 and active_ovl2 == 0 else "NO_GO",
    }


def bus30_recovery(now: str) -> dict:
    params = definition_params(MAIN, "G_30_0_1_DYR")
    return {
        "audit_name": "stage15_bus30_sync_recovery_map",
        "generated_at_local": now,
        "status": "recoverable_by_same_class_instance_template",
        "definition_source_project": str(MAIN),
        "definition_name": "G_30_0_1_DYR",
        "definition_sha": sha256(MAIN),
        "template_policy": "Copy an existing G_xx_0_1_DYR synchronous-generator instance shell only as a PSCAD placement/port template; bind the copied instance to G_30_0_1_DYR and keep G30 parameters from its own definition.",
        "prohibited": [
            "Do not rename DFIG/IBR as a synchronous generator.",
            "Do not keep bus30 DFIG/IBR in parallel.",
            "Do not use arbitrary P/Q; use the G_30_0_1_DYR definition.",
            "Do not create an ideal voltage source substitute.",
        ],
        "parameters": {
            "Name": params.get("Name", "Wang_30"),
            "P_MW": float(params.get("P", 250)),
            "Q_MVAR": float(params.get("Q", 146.456)),
            "Volts_pu": float(params.get("Volts", 1.0475)),
            "Phase_deg": float(params.get("Phase", -3.3392)),
            "Type": params.get("Type", "2"),
        },
        "compiled_endpoint": "to be verified after new trial Build by stage15 pre-run gate",
        "source_limitation": "Current PSCAD canvas has G_30_0_1_DYR definition but no live G30 instance; user explicitly authorized same-class synchronous-generator copy/paste restoration.",
    }


def replacement_map() -> list[dict]:
    edges = p3_tline_edges(stage7_gf46() / "P3.dta")
    rows = []
    # Current compiled generator-map observations from 3IBR.gf46/3IBR.map.
    compiled_bus = {"WF33": 3, "WF35": 5, "WF38": 1}
    for wf in ("WF33", "WF35", "WF38"):
        target = GENERATOR_TARGETS[wf]
        dist, path = shortest_path(edges, compiled_bus[wf], 1)
        paper_p = PAPER_WIND_POWER[wf]
        model_p = target["P"]
        rows.append({
            "paper_wind_farm_id": wf,
            "target_bus": target["target_bus"],
            "original_sync_instance": target["definition"],
            "original_transformer_instance": "same existing generator interface/transformer branch to be replaced in GUI",
            "original_breaker_instance": "existing local generator breaker/interface to be reused or replaced by local windfarm breaker",
            "original_initial_P": model_p,
            "original_initial_Q": target["Q"],
            "paper_reported_P": paper_p,
            "original_rating": "from original generator definition / DYR source; exact MBASE not exposed in PSCAD definition",
            "original_compiled_bus": compiled_bus[wf],
            "bus29_topological_distance": dist,
            "bus29_path": path,
            "windfarm_connection_target": f"paper bus {target['target_bus']} / compiled bus {compiled_bus[wf]}",
            "replacement_mode": "replace_original_sync_generator_with_independent_type3_windfarm",
            "initial_power_policy": "per_bus_replacement_equivalence; paper_text_ambiguous__power_balance_preserving_proxy",
            "status": "ready_for_gui_mapping",
        })
    return rows


def source_inventory_rows() -> list[dict]:
    rows = []
    for bus in ("bus30", "WF33", "WF35", "WF38"):
        target = GENERATOR_TARGETS[bus]
        rows.append({
            "source_id": bus,
            "target_identity": "synchronous_generator" if bus == "bus30" else "paper_wind_farm_type3_dfig_proxy",
            "target_bus": 30 if bus == "bus30" else target["target_bus"],
            "definition_or_template": target["definition"],
            "initial_P": target["P"],
            "initial_Q": target["Q"],
            "status": "planned_active",
            "parallel_source_allowed": False,
        })
    rows.append({
        "source_id": "legacy_bus30_DFIG_IBR_paths",
        "target_identity": "disabled_or_removed",
        "target_bus": 30,
        "definition_or_template": "IBR_AVM / Type3_WTG legacy paths",
        "initial_P": "",
        "initial_Q": "",
        "status": "must_not_remain_active",
        "parallel_source_allowed": False,
    })
    return rows


def output_manifest(now: str) -> dict:
    return {
        "audit_name": "stage15_output_minimum_manifest",
        "generated_at_local": now,
        "new_output_channel_count": len(OUTPUT_CHANNELS),
        "new_output_channels": OUTPUT_CHANNELS,
        "backend_only": [
            "LVRT timer state",
            "LVRT region code",
            "event packet",
            "source availability",
            "breaker command",
            "chronology monitor",
            "collector",
        ],
        "status": "ready_for_gui_mapping",
    }


def power_freeze(now: str) -> dict:
    return {
        "audit_name": "stage15_pre_fault_power_balance_freeze",
        "generated_at_local": now,
        "policy": "per_bus_replacement_equivalence",
        "paper_interpretation_status": "paper_text_ambiguous__power_balance_preserving_proxy",
        "total_original_replaced_P_MW": sum(GENERATOR_TARGETS[x]["P"] for x in ("WF33", "WF35", "WF38")),
        "total_paper_reported_wind_P_MW": sum(PAPER_WIND_POWER.values()),
        "noted_difference_MW": sum(PAPER_WIND_POWER.values()) - sum(GENERATOR_TARGETS[x]["P"] for x in ("WF33", "WF35", "WF38")),
        "decision": "Use original per-bus P/Q to preserve pre-fault power balance; record paper WF38 850 MW as reported target evidence but do not inject unexplained +20 MW.",
        "sources": {k: GENERATOR_TARGETS[k] for k in ("bus30", "WF33", "WF35", "WF38")},
    }


def gui_change_manifest(now: str) -> dict:
    return {
        "audit_name": "stage15_gui_change_manifest",
        "generated_at_local": now,
        "new_trial_path": str(NEW_TRIAL),
        "baseline_to_open": str(STAGE7_BASELINE),
        "save_as_required": str(NEW_TRIAL),
        "allowed_new_model_boundary": ["WF33", "WF35", "WF38", "PAPER_WF_LVRT_TRIP", "three local windfarm breakers", "15 output channels"],
        "absolute_do_not_touch": [str(MAIN), str(LEGACY_TRIAL), "legacy Stage9-13 trial outputs", "old runtime files"],
        "build_repair_scope": ["wiring omission", "label spelling", "port direction", "output channel registration", "duplicate names"],
    }


def write_docs(now: str, baseline: dict, bus30: dict, rows: list[dict], power: dict) -> None:
    (REPO / "docs/STAGE15_LEGACY_BUS30_EXPERIMENT_BOUNDARY.md").write_text(
        "# Stage 15 legacy bus30 experiment boundary\n\n"
        "Stage 9-13 bus30-source-layout protection results are retained as `legacy_bus30_source_layout_protection_experiment`.\n"
        "They must not be mixed with the new paper 33/35/38 wind-farm source-layout mainline.\n",
        encoding="utf-8",
    )
    (REPO / "docs/STAGE15_BUS30_SYNC_RECOVERY.md").write_text(
        "# Stage 15 bus30 synchronous-generator recovery\n\n"
        f"Recovery status: `{bus30['status']}`\n\n"
        "Use the existing `G_30_0_1_DYR` definition for parameters. A same-class `G_xx_0_1_DYR` instance may be copied only as a PSCAD shell/port template, then rebound to `G_30_0_1_DYR`.\n\n"
        f"Frozen P/Q/V: P={bus30['parameters']['P_MW']} MW, Q={bus30['parameters']['Q_MVAR']} MVar, V={bus30['parameters']['Volts_pu']} pu.\n",
        encoding="utf-8",
    )
    (REPO / "docs/STAGE15_PAPER_WF33_35_38_LAYOUT_AND_SOURCE_RECOVERY.md").write_text(
        "# Stage 15 paper WF33/35/38 layout and source recovery\n\n"
        f"Selected clean baseline: `{baseline['selected_baseline_path']}`\n\n"
        "Stage12/13 trial is not used because it contains legacy OVL/protection paths.\n\n"
        "Replacement map:\n\n"
        + "\n".join(f"- {r['paper_wind_farm_id']} replaces `{r['original_sync_instance']}` at paper bus {r['target_bus']}." for r in rows)
        + "\n",
        encoding="utf-8",
    )
    (REPO / "docs/STAGE15_PREFAULT_POWER_BALANCE_AND_SOURCE_FREEZE.md").write_text(
        "# Stage 15 pre-fault power balance and source freeze\n\n"
        f"Policy: `{power['policy']}`.\n\n"
        "The paper reports equal-output wind-farm replacement, but the exact engineering numeric interpretation is ambiguous. "
        "This stage therefore preserves pre-fault power balance by using each replaced synchronous generator's original P/Q.\n\n"
        f"Reported paper total P: {power['total_paper_reported_wind_P_MW']} MW. "
        f"Frozen model replacement total P: {power['total_original_replaced_P_MW']} MW.\n",
        encoding="utf-8",
    )
    sheet = f"""# Stage 15 single GUI refactor / Build / Run sheet

Only follow this sheet after reading the Stage15 static manifests. Do not modify the protected main project or the legacy trial.

## 1. Open and Save As

Open:

```text
{baseline['selected_baseline_path']}
```

Immediately use PSCAD `Save As` and save to:

```text
{NEW_TRIAL}
```

## 2. Restore bus30 synchronous generator

- Copy one existing synchronous generator instance shell such as `G_33_0_1_DYR`.
- Paste it at the bus30 source location/interface.
- Rebind the pasted instance definition/name to `G_30_0_1_DYR`.
- Confirm the parameters are from G30: `P=250`, `Q=146.456`, `Volts=1.0475`, `Name=Wang_30`.
- Remove or disable any bus30 DFIG/IBR injection path. Do not leave bus30 DFIG/IBR in parallel.

## 3. Replace bus33 / bus35 / bus38 source branches

- Replace `G_33_0_1_DYR` with `WF33`.
- Replace `G_35_0_1_DYR` with `WF35`.
- Replace `G_38_0_1_DYR` with `WF38`.
- Use per-bus replacement P/Q:
  - WF33: P=632, Q=123.3861
  - WF35: P=650, Q=225.0912
  - WF38: P=830, Q=41.0678

## 4. Create reusable LVRT module

Create one reusable module:

```text
PAPER_WF_LVRT_TRIP
```

Instantiate exactly:

```text
WF33_LVRT_TRIP
WF35_LVRT_TRIP
WF38_LVRT_TRIP
```

Each instance input must be only its own PCC voltage. No shared state, no shared timer, no one-shot, no fixed-time trigger, no old OVL signal.

LVRT rule:

```text
Vs <= 0.20: immediate trip request
0.20 < Vs < 0.90: t_allow = 0.625 + ((Vs - 0.20)/(0.90 - 0.20))*(2.0 - 0.625)
Vs >= 0.90 and Vs < 1.10: reset/healthy low-voltage state if not already latched
1.10 <= Vs < 1.20: t_allow = 10.0 s high-voltage branch
1.20 <= Vs < 1.25: t_allow = 1.0 s high-voltage branch
1.25 <= Vs < 1.30: t_allow = 0.5 s high-voltage branch
Vs >= 1.30: immediate trip request
```

## 5. Add exactly 15 Output Channels

{chr(10).join('- ' + c for c in OUTPUT_CHANNELS)}

## 6. Settings then Build

- Solution Time Step: `50 us`
- Plot Step: `0.01 s`
- Run Duration: `20.0 s`

Save, then Build. If Build errors require new design choices, stop and report the exact error.

After Build Errors = 0, run:

```text
tools\\stage15_pre_run_gate.cmd
```
"""
    (REPO / "docs/STAGE15_SINGLE_GUI_REFACTOR_BUILD_RUN_SHEET.md").write_text(sheet, encoding="utf-8")


def main() -> int:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    baseline = baseline_manifest(now)
    bus30 = bus30_recovery(now)
    rows = replacement_map()
    inventory = source_inventory_rows()
    output = output_manifest(now)
    power = power_freeze(now)
    gui_manifest = gui_change_manifest(now)
    static_status = static_status_ready() if baseline["baseline_go_no_go"] == "GO" else "blocked_clean_baseline_not_found"

    write_json(REPO / "data/reference/stage15_clean_baseline_selection.json", baseline)
    write_json(REPO / "data/reference/stage15_bus30_sync_recovery_map.json", bus30)
    write_csv(REPO / "data/reference/stage15_wf33_35_38_replacement_map.csv", rows)
    write_csv(REPO / "data/reference/stage15_final_source_inventory_plan.csv", inventory)
    write_json(REPO / "data/reference/stage15_output_minimum_manifest.json", output)
    write_json(REPO / "data/reference/stage15_pre_fault_power_balance_freeze.json", power)
    write_json(REPO / "data/reference/stage15_source_replacement_parameter_freeze.json", {"generated_at_local": now, "sources": inventory})
    write_json(REPO / "data/reference/stage15_gui_change_manifest.json", gui_manifest)
    write_json(REPO / "data/reference/stage15_build_repair_log.json", {"generated_at_local": now, "repairs": []})
    write_json(REPO / "data/validation/stage15_static_refactor_audit.json", {
        "audit_name": "stage15_static_refactor_audit",
        "generated_at_local": now,
        "stage15_static_status": static_status,
        "main_sha": sha256(MAIN),
        "main_sha_expected": EXPECTED_MAIN_SHA,
        "legacy_trial_sha": sha256(LEGACY_TRIAL),
        "legacy_trial_sha_expected": LEGACY_TRIAL_SHA,
        "backup_path": str(BACKUP),
        "checks": {
            "main_sha_unchanged": sha256(MAIN) == EXPECTED_MAIN_SHA,
            "legacy_trial_present": LEGACY_TRIAL.exists(),
            "clean_baseline_go": baseline["baseline_go_no_go"] == "GO",
            "bus30_restoration_policy_user_confirmed": True,
            "new_trial_not_created_by_backend": not NEW_TRIAL.exists(),
        },
        "claim_boundary": "Static GO only. No PSCAD model edit, Build or Run was performed by this script.",
    })
    write_docs(now, baseline, bus30, rows, power)
    print(json.dumps({"stage15_static_status": static_status, "selected_baseline": str(STAGE7_BASELINE)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
