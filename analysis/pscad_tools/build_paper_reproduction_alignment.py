#!/usr/bin/env python3
"""Build a read-only paper-to-PSCAD alignment and minimum cascade plan.

The script reads the primary thesis PDF, repository evidence, and PSCAD model
files. It never writes to PSCAD paths and never invokes PSCAD, EMTDC, Build, or
Run.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
DATA_REF = ROOT / "data" / "reference"
DATA_VAL = ROOT / "data" / "validation"
DOCS = ROOT / "docs"
PSCAD = Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD")
MAIN = PSCAD / "3IBR.pscx"
TRIAL = PSCAD / "3IBR_DFIG1_TRIAL.pscx"
GF46 = PSCAD / "3IBR_DFIG1_TRIAL.gf46"
PAPER = Path(r"C:\Users\24186\Desktop\论文模板\高比例风电系统连锁故障分析与抑制措施研究_许佑欣.pdf")
EXPECTED_MAIN_SHA = "CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def params(element: ET.Element) -> dict[str, str]:
    return {p.get("name", ""): p.get("value", "") for p in element.findall("./paramlist/param")}


def artifact_fingerprint() -> list[dict[str, object]]:
    rows = []
    for pattern in ("*.f", "*.dta", "*.inf", "*.out", "*.exe"):
        for path in sorted(GF46.glob(pattern)):
            stat = path.stat()
            rows.append({"name": path.name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)})
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def evidence_rows() -> list[dict[str, object]]:
    base = {"source_reliability": "primary_thesis_pdf_direct_text", "usable_for_modeling": "yes"}
    return [
        {**base, "evidence_id": "E001", "paper_section": "title pages", "paper_page": "PDF 1-3", "paper_figure_or_table": "title pages", "paper_statement_paraphrase": "The document is Xu Youxin's 2024 professional master's thesis at North China Electric Power University.", "exact_short_quote_if_available": "高比例风电系统连锁故障分析与抑制措施研究", "modeling_category": "paper identity", "parameter_or_logic_name": "paper_identity", "notes": "Identity is directly readable; publication type is a professional master's thesis."},
        {**base, "evidence_id": "E002", "paper_section": "摘要", "paper_page": "I (PDF 4)", "paper_figure_or_table": "none", "paper_statement_paraphrase": "The model combines power-flow balance, thermal generators, a WECC second-generation DFIG, and multiple protection actions.", "exact_short_quote_if_available": "建立过负荷保护、风机脱网保护、常规机组保护、减载措施", "modeling_category": "system topology and source replacement", "parameter_or_logic_name": "multi_timescale_accident_chain", "notes": "High-level scope only; detailed rules are registered separately."},
        {**base, "evidence_id": "E003", "paper_section": "2.3.1 线路过负荷保护", "paper_page": "11 (PDF 19)", "paper_figure_or_table": "Eq. 2-6, 2-7", "paper_statement_paraphrase": "Line flow redistributes after outages; an inverse-time overload action opens a line, anchored at 1.1 times limit with 5 s delay.", "exact_short_quote_if_available": "线路负载率达到1.1倍承载极限时，过负荷保护延时5s", "modeling_category": "line overload protection", "parameter_or_logic_name": "line_loading_inverse_time", "notes": "The equations are text-extractable, but implementation should be independently transcribed and reviewed."},
        {**base, "evidence_id": "E004", "paper_section": "2.3.2 风机电压穿越保护", "paper_page": "11-12 (PDF 19-20)", "paper_figure_or_table": "Fig. 2-3; Eq. 2-8", "paper_statement_paraphrase": "Wind turbines trip when PCC voltage remains outside the paper's fault-voltage ride-through regions for the specified delay.", "exact_short_quote_if_available": "风机电压穿越保护的延时动作时间", "modeling_category": "wind LVRT / trip protection", "parameter_or_logic_name": "VRT_delay_curve", "notes": "Direct text gives curve regions; graphic semantics still require careful implementation review."},
        {**base, "evidence_id": "E005", "paper_section": "2.3.3 常规机组保护", "paper_page": "12 (PDF 20)", "paper_figure_or_table": "none", "paper_statement_paraphrase": "Conventional units use 47.5/51.5 Hz frequency limits with 10 s delay and 0.8/1.3 p.u. voltage limits with 2 s delay.", "exact_short_quote_if_available": "低频保护定值为47.5Hz，过频保护定值为51.5Hz", "modeling_category": "conventional-generator protection", "parameter_or_logic_name": "generator_frequency_voltage_trip", "notes": "Thresholds and delays are direct text."},
        {**base, "evidence_id": "E006", "paper_section": "2.3.4 低频低压减载措施", "paper_page": "12-13 (PDF 20-21)", "paper_figure_or_table": "none", "paper_statement_paraphrase": "UFLS is three-stage at 49.0/48.8/48.5 Hz with 0.8/0.5/0.2 s delays and 25/40/55 percent shedding; UVLS is 0.8 p.u., 1 s, 25 percent.", "exact_short_quote_if_available": "设置三段低频减载措施动作定值", "modeling_category": "under-frequency load shedding", "parameter_or_logic_name": "UFLS_UVLS", "notes": "Also supports the under-voltage load-shedding category."},
        {**base, "evidence_id": "E007", "paper_section": "2.3.5 暂态过电压措施", "paper_page": "13 (PDF 21)", "paper_figure_or_table": "none", "paper_statement_paraphrase": "Temporary-overvoltage protection uses a 1.3 p.u. threshold and opens the related line without intentional delay.", "exact_short_quote_if_available": "过电压阈值为1.3p.u.，在满足动作条件后无延时", "modeling_category": "temporary-overvoltage protection", "parameter_or_logic_name": "TOV_line_trip", "notes": "The exact target-line association is scenario dependent."},
        {**base, "evidence_id": "E008", "paper_section": "2.4, 2.4.3", "paper_page": "13-15 (PDF 21-23)", "paper_figure_or_table": "Fig. 2-4", "paper_statement_paraphrase": "The paper uses an IEEE 39-bus, 220 kV, 10-generator, 46-line PSCAD system and implements protection through PSCAD-MATLAB interaction.", "exact_short_quote_if_available": "基于PSCAD4.6.2与MATLAB2016b平台", "modeling_category": "system topology and source replacement", "parameter_or_logic_name": "IEEE39_PSCAD_MATLAB", "notes": "Current project has no active MATLAB coupling."},
        {**base, "evidence_id": "E009", "paper_section": "2.5 典型故障仿真", "paper_page": "15 (PDF 23)", "paper_figure_or_table": "Fig. 2-7", "paper_statement_paraphrase": "Generators at buses 33, 35 and 38 are replaced by equal-output wind farms; 85 bus-fault/line-outage initial conditions are run for 20 s.", "exact_short_quote_if_available": "33、35、38母线上火电机组由相同出力的风电场模型所替代", "modeling_category": "simulation duration", "parameter_or_logic_name": "replacement_and_fault_set", "notes": "Supports topology, source replacement, fault-set and duration categories."},
        {**base, "evidence_id": "E010", "paper_section": "2.5 典型故障仿真", "paper_page": "16-17 (PDF 24-25)", "paper_figure_or_table": "Table 2-2", "paper_statement_paraphrase": "At 0.50 s a 2 s three-phase fault near bus 29 is followed by wind trip, UFLS, sequential overloaded-line openings, further wind trip, and generator protection.", "exact_short_quote_if_available": "母线29近区发生三相短路故障，故障持续时间2.0s", "modeling_category": "initial fault type", "parameter_or_logic_name": "bus29_baseline_chain", "notes": "The paragraph and table contain a 35/38 wind-farm inconsistency; preserve it as an ambiguity."},
        {**base, "evidence_id": "E011", "paper_section": "3.3.1.1 过载主导型连锁故障", "paper_page": "21 (PDF 29)", "paper_figure_or_table": "Fig. 3-3", "paper_statement_paraphrase": "The overload-dominant sequence starts with a short circuit, then overloaded line trip(s), topology degradation, source/load actions, islanding and generator loss.", "exact_short_quote_if_available": "线路L1过载切除，多线路相继切除", "modeling_category": "scenario comparison dimensions", "parameter_or_logic_name": "overload_dominant_chain", "notes": "The paper explicitly warns that figure events do not have a strict one-way causal order."},
        {**base, "evidence_id": "E012", "paper_section": "3.3.1.2 脱网主导型连锁故障", "paper_page": "21-22 (PDF 29-30)", "paper_figure_or_table": "Fig. 3-4", "paper_statement_paraphrase": "The off-grid-dominant sequence starts with a short circuit, wind trip and power loss, then state/flow redistribution, line trips, load shedding and generator loss.", "exact_short_quote_if_available": "风机脱网，大量功率损失，电网状态偏移，潮流大幅转移", "modeling_category": "wind-farm / DFIG model", "parameter_or_logic_name": "offgrid_dominant_chain", "notes": "This sequence is the closest paper-supported candidate to the current DFIG infrastructure."},
        {**base, "evidence_id": "E013", "paper_section": "3.3.2.1 故障严重度指标", "paper_page": "22-23 (PDF 30-31)", "paper_figure_or_table": "Eq. 3-1 to 3-5", "paper_statement_paraphrase": "Evaluation uses line-trip count, wind power lost, load shed, and voltage/frequency severity.", "exact_short_quote_if_available": "定义切线数量、风机脱网功率与减载指标", "modeling_category": "evaluation outputs", "parameter_or_logic_name": "cascade_severity_outputs", "notes": "Current V/P/Q monitoring covers only a subset."},
        {**base, "evidence_id": "E014", "paper_section": "3.3.2, 3.4", "paper_page": "23-30 (PDF 31-38)", "paper_figure_or_table": "Tables 3-1 to 3-4; Figs. 3-5 to 3-9", "paper_statement_paraphrase": "Scenario comparisons vary fault type, duration, wind penetration, electrical distance, and centralized/distributed wind connection.", "exact_short_quote_if_available": "探讨电气距离、故障条件、风电渗透率等因素", "modeling_category": "scenario comparison dimensions", "parameter_or_logic_name": "scenario_sweep_dimensions", "notes": "A future reproduction needs a scenario matrix, not one fixed trial sequence."},
        {**base, "evidence_id": "E015", "paper_section": "4.2 动态无功补偿装置模型", "paper_page": "31-34 (PDF 39-42)", "paper_figure_or_table": "Figs. 4-1 to 4-4", "paper_statement_paraphrase": "The paper models a TCR-TSC SVC and a double-loop PI STATCOM for PCC-voltage support.", "exact_short_quote_if_available": "本文采用双环PI控制结构搭建STATCOM的控制模块", "modeling_category": "SVC", "parameter_or_logic_name": "SVC_STATCOM_models", "notes": "Also supports the STATCOM category."},
        {**base, "evidence_id": "E016", "paper_section": "4.3.2 动态无功补偿抑制效果", "paper_page": "35-38 (PDF 43-46)", "paper_figure_or_table": "Figs. 4-6 to 4-9", "paper_statement_paraphrase": "The comparison connects 300 MVar SVC/STATCOM at bus 28 and applies a 0.5 s-start, 2 s three-phase fault near bus 4.", "exact_short_quote_if_available": "28节点接入额定无功功率300MVar", "modeling_category": "STATCOM", "parameter_or_logic_name": "bus28_compensation_comparison", "notes": "Evaluation includes wind-trip proportion, line trips, and remaining load."},
        {**base, "evidence_id": "E017", "paper_section": "2.5 典型故障仿真", "paper_page": "16 (PDF 24)", "paper_figure_or_table": "Table 2-2", "paper_statement_paraphrase": "The baseline initial fault is located near bus 29.", "exact_short_quote_if_available": "母线29近区发生三相短路故障", "modeling_category": "initial fault location", "parameter_or_logic_name": "baseline_fault_bus", "notes": "Location is explicit in the table."},
        {**base, "evidence_id": "E018", "paper_section": "2.5 典型故障仿真", "paper_page": "16 (PDF 24)", "paper_figure_or_table": "Table 2-2", "paper_statement_paraphrase": "The baseline fault begins at 0.50 s and lasts 2.0 s.", "exact_short_quote_if_available": "故障持续时间2.0s", "modeling_category": "fault clearing rule", "parameter_or_logic_name": "baseline_fault_timing", "notes": "The source states duration; implementation must still identify the physical clearing switch."},
        {**base, "evidence_id": "E019", "paper_section": "2.3.4 低频低压减载措施", "paper_page": "13 (PDF 21)", "paper_figure_or_table": "none", "paper_statement_paraphrase": "UVLS uses a 0.8 p.u. threshold, 1.0 s delay and 25 percent load shedding.", "exact_short_quote_if_available": "低压减载措施电压定值为0.8p.u.", "modeling_category": "under-voltage load shedding", "parameter_or_logic_name": "UVLS", "notes": "Direct text."},
        {**base, "evidence_id": "E020", "paper_section": "4.2.2, 4.3.2", "paper_page": "33-38 (PDF 41-46)", "paper_figure_or_table": "Figs. 4-3 to 4-9", "paper_statement_paraphrase": "The STATCOM uses double-loop PI control and is compared at bus 28 with 300 MVar rating.", "exact_short_quote_if_available": "本文采用双环PI控制结构", "modeling_category": "STATCOM", "parameter_or_logic_name": "STATCOM_double_loop_PI", "notes": "Device/control evidence is separate from claimed mitigation performance."},
        {**base, "evidence_id": "E021", "paper_section": "2.4.2, 3.3.1.2", "paper_page": "14-15, 21-22 (PDF 22-23, 29-30)", "paper_figure_or_table": "Fig. 2-6; Fig. 3-4", "paper_statement_paraphrase": "The paper models a DFIG wind turbine and uses wind-farm off-grid behavior as the first protection action in an off-grid-dominant chain.", "exact_short_quote_if_available": "风机脱网为主导的连锁故障", "modeling_category": "wind-farm / DFIG model", "parameter_or_logic_name": "DFIG_and_offgrid_chain", "notes": "Current public Type-3 model is only a structural adaptation."},
    ]


def inventory_rows(channel_names: set[str], definition_names: set[str], user_defns: set[str]) -> list[dict[str, object]]:
    dynamic = "data/validation/three_source_electrical_response_final_audit.json"
    rows = [
        ("CAP01", "network topology representation", "IEEE39/PNNL 39-bus network", "network", "3IBR.pscx; 3IBR_DFIG1_TRIAL.pscx", "PSCAD XML contains P1/P2/P3 and network line/load definitions", "docs/MODEL_PROVENANCE.md", "implemented_and_audited", "PNNL topology is present but is not proven identical to the thesis topology/parameters."),
        ("CAP02", "bus and branch observability", "existing meters and source V/P/Q", "network", "3IBR_DFIG1_TRIAL.pscx", "master:voltmetergnd/master:ammeter/master:multimeter exist; no complete branch Output Channel set", dynamic, "partially_available", "Source electrical monitoring does not equal system-wide branch observability."),
        ("CAP03", "line P / Q / I / loading observability", "no audited line-channel set", "branches", "3IBR_DFIG1_TRIAL.pscx", "262 Output Channels contain no audited comprehensive line P/Q/I/loading map", "docs/THREE_SOURCE_ELECTRICAL_OBSERVABILITY_STATIC_AUDIT.md", "not_found", "Raw meters may exist; no traceable target-line loading dataset is available."),
        ("CAP04", "line breaker observability", "source-local breakers only", "branches", "3IBR_DFIG1_TRIAL.pscx", "master:breaker3 exists; audited BRK_DFIG/BRK_IBR2_TRIAL/BRK_IBR3_TRIAL are source boundaries", dynamic, "partially_available", "No audited transmission-line breaker state map."),
        ("CAP05", "line overload relay", "none", "branches", "3IBR_DFIG1_TRIAL.pscx", "no overload relay definition or audited line-loading action path", "docs/PAPER_PARAMETER_EXTRACTION.md is paper-only, not model evidence", "not_implemented", "MATLAB scaffold does not constitute PSCAD protection."),
        ("CAP06", "fault source and fault clearing", "master:tfaultn", "fault", "3IBR_DFIG1_TRIAL.pscx", "master:tfaultn present; existing fixed scenario differs from thesis bus-29 benchmark", "data/reference/type3_dfig_fault_interface_audit.json", "partially_available", "A fault mechanism exists, but paper location/timing and clearing are not reproduced."),
        ("CAP07", "DFIG model", "Type-3 DFIG trial branch", "DFIG", "3IBR_DFIG1_TRIAL.pscx", "Type-3 component definitions and DFIG branch exist", "data/reference/type3_dfig_lvrt_model_integrity_audit.json", "implemented_and_audited", "Public Type-3 implementation is not proven parameter-identical to the thesis model."),
        ("CAP08", "DFIG LVRT", "external LVRT and local trip chain", "DFIG", "3IBR_DFIG1_TRIAL.pscx", "DFIG_LVRT_* labels and BRK_DFIG path", "data/reference/type3_dfig_lvrt_closed_loop_coverage.json", "implemented_and_audited", "Only audited current criterion/chain; not full paper Eq. 2-8 reproduction."),
        ("CAP09", "IBR2 source model", "IBR_AVM_2_1_1 source B", "IBR2", "3IBR_DFIG1_TRIAL.pscx", "IBR2 V/P/Q and real source module present", dynamic, "implemented_and_audited", "Real source and observability only; not a thesis wind-farm identity claim."),
        ("CAP10", "IBR3 source model", "IBR_AVM_2_1_1 source C", "IBR3", "3IBR_DFIG1_TRIAL.pscx", "IBR3 V/P/Q and real source module present", dynamic, "implemented_and_audited", "Real source and observability only; not a thesis wind-farm identity claim."),
        ("CAP11", "trial-only IBR2 opening stimulus", "IBR2_TEST_ENABLE", "IBR2", "3IBR_DFIG1_TRIAL.pscx", "IBR2_TEST_OPEN_REQ -> IBR2_TRIAL_BRK_CMD", "data/validation/ibr2_trial_single_opening_final_audit.json", "implemented_and_audited", "Controlled interface-validation stimulus, not natural cascade."),
        ("CAP12", "trial-only IBR3 opening stimulus", "IBR3_TRIAL__OPEN_STIMULUS", "IBR3", "3IBR_DFIG1_TRIAL.pscx", "ONE_SHOT_BREAKER_OPEN_STIMULUS instance", "data/validation/ibr3_trial_single_opening_final_audit.json", "implemented_and_audited", "Controlled interface-validation stimulus, not natural cascade."),
        ("CAP13", "source-A event packet", "DFIG_LVRT_CASCADE_*", "DFIG", "3IBR_DFIG1_TRIAL.pscx", "DFIG event packet labels and Output Channels", dynamic, "implemented_and_audited", "Monitor record only."),
        ("CAP14", "source-B event packet", "IBR2_TRIAL_CASCADE_*", "IBR2", "3IBR_DFIG1_TRIAL.pscx", "IBR2 event packet path", dynamic, "implemented_and_audited", "Monitor record only."),
        ("CAP15", "source-C event packet", "IBR3_TRIAL_CASCADE_*", "IBR3", "3IBR_DFIG1_TRIAL.pscx", "IBR3_TRIAL__EVENT_PACKET", dynamic, "implemented_and_audited", "Monitor record only."),
        ("CAP16", "three-source collector", "THREE_SOURCE_EVENT_COLLECTOR", "A/B/C events", "3IBR_DFIG1_TRIAL.pscx", "definition and CASCADE3_TRIAL__EVENT_COLLECTOR instance", dynamic, "implemented_and_audited", "Aggregation does not create causal propagation."),
        ("CAP17", "three-event chronology", "THREE_EVENT_CHRONOLOGY_MONITOR", "A/B/C events", "3IBR_DFIG1_TRIAL.pscx", "definition and CASCADE3_TRIAL__CHRONOLOGY_MONITOR instance", dynamic, "implemented_and_audited", "Ordering does not establish causality."),
        ("CAP18", "V/P/Q observability", "CASCADE3_ELEC_*", "DFIG/IBR2/IBR3", "3IBR_DFIG1_TRIAL.pscx", "nine monitor-only Output Channels", dynamic, "implemented_and_audited", "Recorded source trajectories only; units are not independently asserted."),
        ("CAP19", "frequency observability", "internal Freq/FreqFlag signals", "generators/network", "3IBR_DFIG1_TRIAL.pscx", "internal frequency labels exist but no audited system frequency Output Channel set", "none", "partially_available", "Cannot support paper UFLS or severity metrics yet."),
        ("CAP20", "load observability", "ETRAN loads", "loads", "3IBR_DFIG1_TRIAL.pscx", "ETRAN:Electranix_Load definitions exist; no audited remaining-load/shedding channel set", "none", "partially_available", "Load components do not equal load-shedding observability."),
        ("CAP21", "UFLS", "none", "loads", "3IBR_DFIG1_TRIAL.pscx", "no audited UFLS action path", "none", "not_implemented", "Repository MATLAB class is not coupled to PSCAD."),
        ("CAP22", "UVLS", "none", "loads", "3IBR_DFIG1_TRIAL.pscx", "no audited UVLS action path", "none", "not_implemented", "Repository MATLAB class is not coupled to PSCAD."),
        ("CAP23", "conventional-generator protection", "none audited", "thermal generators", "3IBR_DFIG1_TRIAL.pscx", "generator dynamics exist; no audited 47.5/51.5 Hz or 0.8/1.3 p.u. trip logic", "none", "not_found", "Do not infer protection from generator model names."),
        ("CAP24", "temporary-overvoltage protection", "none", "lines", "3IBR_DFIG1_TRIAL.pscx", "no audited 1.3 p.u. no-delay line-trip path", "none", "not_implemented", "DFIG voltage monitoring is not line TOV protection."),
        ("CAP25", "SVC", "none", "mitigation", "3IBR_DFIG1_TRIAL.pscx", "no SVC definition/instance found", "none", "not_found", "Paper device is absent."),
        ("CAP26", "STATCOM", "none", "mitigation", "3IBR_DFIG1_TRIAL.pscx", "no STATCOM definition/instance found", "none", "not_found", "Paper device is absent."),
        ("CAP27", "MATLAB coupling", "repository-only MATLAB scaffold", "external coupling", "matlab/; 3IBR_DFIG1_TRIAL.pscx", "MATLAB files exist in repository; no active PSCAD MATLAB interface is audited", "docs/MATLAB_INTERFACE_SPEC.md", "not_implemented", "No MATLAB coupling claim."),
    ]
    keys = ["capability_id", "category", "component_name", "source_or_network_object", "project_path", "xml_or_fortran_evidence", "existing_dynamic_evidence", "current_status", "claim_boundary"]
    return [dict(zip(keys, row)) for row in rows]


def alignment_rows() -> list[dict[str, object]]:
    def row(step: str, category: str, requirement: str, evidence: str, page: str, component: str, current: str, cls: str, status: str, reasoning: str, strict: str, adaptation: str, dependency: str, priority: str, change: str, run: str, safe: str, prohibited: str) -> dict[str, object]:
        return {"paper_step_id": step, "paper_modeling_category": category, "paper_requirement": requirement, "paper_evidence_id": evidence, "paper_section_page": page, "current_project_component": component, "current_project_evidence": current, "alignment_class": cls, "alignment_status": status, "reasoning": reasoning, "strict_reproduction_possible": strict, "minimum_adaptation_needed": adaptation, "prerequisite_dependency": dependency, "recommended_priority": priority, "requires_model_change": change, "requires_future_run": run, "safe_current_claim": safe, "prohibited_claim": prohibited}
    return [
        row("P01", "system topology and source replacement", "IEEE39, 220 kV, 10 generators, 46 lines; buses 33/35/38 replaced by wind farms", "E008;E009", "2.4-2.5, pp.13-16", "PNNL 39-bus / 3IBR trial", "CAP01;CAP09;CAP10", "partially_aligned", "partial", "System family aligns, but bus replacements, ratings and parameters are not proven one-to-one.", "no", "trace bus/branch/source correspondence and ratings", "paper topology table and current branch map", "medium", "yes", "yes", "structurally related IEEE39 adaptation", "strict topology reproduction"),
        row("P02", "wind-farm / DFIG model", "WECC second-generation DFIG wind-farm representation", "E002;E021", "摘要; 2.4.2; 3.3.1.2", "Type-3 DFIG plus two IBR_AVM sources", "CAP07-CAP10", "structurally_aligned_adaptation", "partial", "One audited Type-3 DFIG exists, but all three sources are not paper-identical wind farms.", "no", "document model and parameter equivalence", "source model provenance", "medium", "yes", "yes", "one Type-3 DFIG adaptation is audited", "three paper-identical wind farms"),
        row("P03", "initial fault type", "three-phase short circuit for the baseline chain", "E010", "2.5 p.16", "existing master:tfaultn scenario", "CAP06", "partially_aligned", "partial", "A fault source exists but the approved current scenario is not the paper baseline.", "no", "paper-aligned fault configuration after observability", "target bus and clearing boundary", "medium", "yes", "yes", "fault infrastructure is partially available", "paper fault reproduced"),
        row("P04", "initial fault location", "near bus 29 at 0.50 s", "E017", "2.5 p.16", "no audited bus-29 fault target", "CAP06", "missing", "gap", "Current fault location is not traced to bus 29.", "no", "identify bus-29 electrical boundary", "topology correspondence", "medium", "yes", "yes", "paper location is not implemented", "bus-29 benchmark validated"),
        row("P05", "fault clearing rule", "baseline fault lasts 2.0 s", "E018", "2.5 p.16", "existing fixed fault timing", "CAP06", "partially_aligned", "gap", "Fault timing infrastructure exists but current run settings are different.", "no", "configure only after target observability exists", "P04", "medium", "yes", "yes", "fault timing capability exists", "paper clearing reproduced"),
        row("P06", "simulation duration", "20 s scenario horizon", "E009", "2.5 p.15", "current trial duration 5 s", "run summary", "contradicted", "gap", "The current trial horizon cannot contain delayed overload and generator actions.", "no", "future dedicated paper-aligned scenario", "all safety prerequisites", "low", "yes", "yes", "current 5 s trials are interface tests", "20 s paper scenario reproduced"),
        row("P07", "wind LVRT / trip protection", "paper fault-voltage curve and delayed trip", "E004", "2.3.2 pp.11-12", "DFIG_LVRT_* and BRK_DFIG", "CAP08", "partially_aligned", "partial", "A real local DFIG trip chain exists, but Eq. 2-8 equivalence is incomplete.", "no", "equation-by-equation criterion audit", "voltage semantics and target branch", "medium", "yes", "yes", "DFIG LVRT scaffold is audited", "paper LVRT strictly reproduced"),
        row("P08", "power-flow redistribution", "source trip/topology change causes line-flow redistribution", "E003;E010;E012", "2.3.1; 2.5; 3.3.1.2", "source V/P/Q only", "CAP02;CAP03", "missing", "critical_gap", "No comprehensive branch P/Q/I/loading record can show the propagation link.", "no", "add monitor-only branch observability", "target-line map", "highest", "yes", "yes", "source trajectories are recorded", "network redistribution validated"),
        row("P09", "line overload protection", "inverse-time line overload action, 1.1 anchor and 5 s", "E003", "2.3.1 p.11", "none", "CAP05", "missing", "gap", "No real-line loading input or overload relay exists.", "no", "observe first; shadow relay only after traceability", "P08", "high", "yes", "yes", "paper rule is documented", "line protection validated"),
        row("P10", "branch trip", "overloaded lines open and alter topology", "E010;E011", "2.5 pp.16-17; Fig.3-3", "source-local breakers only", "CAP04", "missing", "gap", "No audited transmission branch actuation boundary is available.", "no", "shadow-only before any breaker connection", "P08;P09", "low", "yes", "yes", "source breaker states are observable", "paper line-trip cascade reproduced"),
        row("P11", "under-frequency load shedding", "three-stage UFLS", "E006", "2.3.4 pp.12-13", "none", "CAP19-CAP21", "missing", "gap", "Frequency and load-shed interfaces are not audited.", "no", "frequency/load observability then shadow monitor", "P08", "low", "yes", "yes", "paper UFLS rule is registered", "UFLS validated"),
        row("P12", "under-voltage load shedding", "0.8 p.u., 1 s, 25 percent UVLS", "E019", "2.3.4 p.13", "none", "CAP20;CAP22", "missing", "gap", "No load-shed actuation or audited load-bus voltage map.", "no", "load-bus observability then shadow monitor", "P08", "low", "yes", "yes", "paper UVLS rule is registered", "UVLS validated"),
        row("P13", "conventional-generator protection", "frequency and voltage trip limits/delays", "E005", "2.3.3 p.12", "generator models without audited trip logic", "CAP23", "missing", "gap", "Dynamic machines exist but paper protection is not traced.", "no", "generator terminal observability and shadow monitor", "P08", "low", "yes", "yes", "generator models exist", "generator protection validated"),
        row("P14", "temporary-overvoltage protection", "1.3 p.u. no-delay related-line opening", "E007", "2.3.5 p.13", "none", "CAP24", "missing", "gap", "No TOV-to-line action path exists.", "no", "target-voltage observability then shadow monitor", "P08", "low", "yes", "yes", "paper TOV rule is registered", "TOV protection validated"),
        row("P15", "SVC / STATCOM", "dynamic compensation near wind farm; bus-28 300 MVar comparison", "E015;E016;E020", "4.2-4.3 pp.31-38", "none", "CAP25;CAP26", "missing", "gap", "Neither device exists in the trial.", "no", "defer until the unmitigated chain is observable", "P08-P14", "deferred", "yes", "yes", "mitigation evidence is identified", "voltage-support performance validated"),
        row("P16", "scenario comparison dimensions and outputs", "vary fault, duration, penetration, distance; measure cuts, trips, shedding and severity", "E013;E014", "3.3.2-3.4 pp.22-30", "one controlled timing sequence and source V/P/Q", "CAP18-CAP20", "partially_aligned", "partial", "Current evidence is one controlled interface scenario, not the paper scenario matrix.", "no", "add missing observability before scenario sweeps", "P08", "medium", "yes", "yes", "recorded source trajectories are available", "paper scenario comparison reproduced"),
    ]


def build_docs(alignment: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for row in alignment:
        counts[row["alignment_class"]] = counts.get(row["alignment_class"], 0) + 1
    plan = f"""# Paper reproduction alignment and minimum cascade plan

## 1. 目标论文身份与原始资料状态

- 题名：《高比例风电系统连锁故障分析与抑制措施研究》
- 作者：许佑欣
- 类型：华北电力大学专业硕士学位论文
- 答辩时间：2024 年 5 月
- 原始 PDF：本地文件存在，SHA-256 记录于 source manifest；53 页均有可提取文本层。
- `paper_source_status = available_primary_paper_source`

## 2. 当前项目的严格复现边界

当前 PNNL 39-bus / 3IBR / DFIG trial 不是论文系统的一比一复现。拓扑族、
一个 Type-3 DFIG 和若干事件接口具有结构对齐价值，但母线替换、源参数、故障
配置、线路保护、减载、常规机组保护和补偿设备均未逐项复现。

## 3. 论文事故链机制拆解

论文直接给出两种机制。与当前 DFIG 基础设施最接近的是脱网主导链：

`初始三相短路 -> PCC 电压扰动 -> 风机电压穿越失败/脱网 -> 功率缺额 -> 潮流大幅转移 -> 线路过负荷候选 -> 线路开断 -> 减载/其余风机或机组保护`。

过载主导链则从短路恢复阶段的线路过载和开断开始，再推动更多潮流转移、
源荷保护和解列。论文明确提醒图示事件并非严格单向因果。

## 4. 当前模型已具备的基础设施

已审计：DFIG LVRT 与本地脱网链、IBR2/IBR3 trial-only 本地开断接口、三源
event packet、collector、chronology，以及三源 V/P/Q monitor-only 记录。
当前三来源受控时序与 V/P/Q Run 属于基础设施验证和记录性动态证据；它们
不构成论文的自然连锁故障复现。

## 5. 当前模型与论文的逐项差距矩阵

完整矩阵见 `data/reference/paper_reproduction_alignment_matrix.csv`。分类计数：
{json.dumps(counts, ensure_ascii=False)}。关键首缺口是：没有面向真实输电支路的
P/Q/I/负载率通道，因而无法观察“源脱网/故障 -> 潮流重分布 -> 支路过载”传播链。

## 6. 当前最安全的项目命名

`controlled-interface validation scaffold`

不能使用 `strict paper reproduction`。在完成线路与保护机制前，也不宜把当前
工程称为完整的 `partial mechanism reproduction`。

## 7. 最小论文式事故链候选方案

首选候选为论文表 2-2 / 图 3-4 支持的脱网主导链。当前 DFIG LVRT 可承接第一
保护动作，但网络传播链缺少真实线路观测。现有固定 DFIG -> IBR2 -> IBR3
定时序列仅为 `controlled interface-validation sequence`，不是 paper cascade chain。

## 8. 下一阶段唯一推荐

`next_stage = branch observability only`

只增加目标线路的 P/Q/I/负载率 monitor-only 输出；不接断路器，不增加 relay。
该顺序由 E003、E010、E012 直接支持：论文把潮流重分布和线路过负荷置于风机
脱网后的传播环节，而 CAP03 证明当前恰缺少这一可观测桥梁。

暂缓 shadow UVRT：当前已有 DFIG LVRT 本地链，下一处论文机制缺口在网络侧。
暂缓 overload shadow relay：尚无可追溯线路量、目标线路边界和验证输入。
暂缓默认基线 Run：重复 Run 不能补齐缺失的线路测量接口。

## 9. 当前不能做的事情

不能把定时开断写成自然级联；不能把未来 shadow 设计写成已实现保护；不能
在缺少线路观测时连接线路断路器；不能先加入 SVC/STATCOM 并宣称抑制效果。

## 10. 结论边界

本轮仅完成原论文证据登记、当前模型静态盘点、逐项差距映射与最小事故链
设计。后续建模应由论文中明确的“故障—保护—网络重分布—后续保护”链条
决定。本轮没有修改 PSCAD、没有 Build、没有 Run，也没有验证自然级联、
物理因果、稳定性、保护协调、电压支撑或 MATLAB 耦合。
"""
    (DOCS / "PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md").write_text(plan, encoding="utf-8")

    gaps = """# Paper reproduction gap register

| gap_id | paper requirement | current gap | risk if ignored | required evidence | recommended stage | not-yet-permitted claim |
| --- | --- | --- | --- | --- | --- | --- |
| G01 | IEEE39 buses 33/35/38 wind replacement | No one-to-one topology/source correspondence | False strict-reproduction claim | Branch/bus/source map and ratings | topology trace | strict topology reproduction |
| G02 | Bus-29 three-phase benchmark fault | Current fault is not traced to bus 29 | Wrong scenario identity | Target electrical boundary and timing | after observability | paper baseline reproduced |
| G03 | Flow redistribution after source trip | No audited branch P/Q/I/loading set | Causal bridge cannot be observed | Real-line measurements and signal semantics | branch observability only | network redistribution validated |
| G04 | Inverse-time overload protection | No real-line input or relay | Relay would be disconnected from evidence | E003 transcription plus G03 | future shadow relay | line protection validated |
| G05 | Transmission-line opening | No audited target-line breaker boundary | Unsafe premature actuation | Target-line breaker state and rollback | after shadow validation | line-trip cascade reproduced |
| G06 | UFLS/UVLS | No audited frequency/load-shed interfaces | Load behavior could be misclassified | Frequency, load and shed-state channels | deferred shadow monitors | load shedding validated |
| G07 | Conventional generator protection | No audited paper-threshold trip path | Generator dynamics may be mistaken for protection | Terminal V/f and shadow criteria | deferred | generator protection validated |
| G08 | Temporary-overvoltage line action | No 1.3 p.u. no-delay path | DFIG voltage logic could be misused | Target-bus voltage and related-line mapping | deferred | TOV protection validated |
| G09 | 20 s scenario and parameter sweeps | Current evidence uses fixed 5 s interface scenarios | Results are not comparable to paper tables | Completed mechanisms and scenario manifest | final integration | paper scenario matrix reproduced |
| G10 | SVC/STATCOM mitigation | Devices absent; unmitigated chain incomplete | Mitigation could hide missing mechanism | Baseline chain plus device/controller provenance | last | voltage-support performance validated |

当前三来源受控时序与 V/P/Q Run 属于基础设施验证和记录性动态证据，不构成
论文的自然连锁故障复现。后续顺序必须由原文的故障—保护—网络重分布—后续
保护链条决定。
"""
    (DOCS / "PAPER_REPRODUCTION_GAP_REGISTER.md").write_text(gaps, encoding="utf-8")


def main() -> int:
    for directory in (DATA_REF, DATA_VAL, DOCS):
        directory.mkdir(parents=True, exist_ok=True)
    if not PAPER.exists():
        raise FileNotFoundError(PAPER)

    reader = PdfReader(PAPER)
    extracted = [(page.extract_text() or "").strip() for page in reader.pages]
    usable = sum(len(text) >= 100 for text in extracted)
    root = ET.parse(TRIAL).getroot()
    main_root = ET.parse(MAIN).getroot()
    channels = [params(user) for user in root.iter("User") if user.get("defn") == "master:pgb"]
    channel_names = {row.get("Name", "") for row in channels}
    channel_fingerprint = hashlib.sha256("\n".join(sorted(json.dumps(row, sort_keys=True) for row in channels)).encode()).hexdigest().upper()
    definitions = {d.get("name", "") for d in root.iter("Definition")}
    user_defns = {u.get("defn", "") for u in root.iter("User")}
    definition_fingerprint = hashlib.sha256("\n".join(sorted(definitions)).encode()).hexdigest().upper()

    source_manifest = {
        "paper_source_status": "available_primary_paper_source",
        "exact_title": "高比例风电系统连锁故障分析与抑制措施研究",
        "authors": ["许佑欣"],
        "publication_type": "华北电力大学专业硕士学位论文",
        "year": 2024,
        "source_path_or_identifier": str(PAPER),
        "source_file_sha256": sha256(PAPER),
        "text_extraction_status": "direct_pdf_text_layer_extractable_no_ocr",
        "usable_page_count": usable,
        "total_pdf_page_count": len(reader.pages),
        "limitations": [
            "No DOI was identified in the local source.",
            "Table 2-2 and its following paragraph disagree on whether bus 38 or bus 35 trips first and whether loss is 850 or 830 MW.",
            "Equation and figure transcription must be independently reviewed before implementation.",
        ],
        "task_start_integrity": {
            "main_sha256": sha256(MAIN), "trial_sha256": sha256(TRIAL),
            "main_mtime_ns": MAIN.stat().st_mtime_ns, "trial_mtime_ns": TRIAL.stat().st_mtime_ns,
            "output_channel_count": len(channels), "output_channel_fingerprint": channel_fingerprint,
            "definition_count": len(definitions), "definition_name_fingerprint": definition_fingerprint,
            "generated_artifact_fingerprint": artifact_fingerprint(),
        },
    }
    (DATA_REF / "paper_reproduction_source_manifest.json").write_text(json.dumps(source_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = evidence_rows()
    write_csv(DATA_REF / "paper_reproduction_evidence_registry.csv", evidence)
    inventory = inventory_rows(channel_names, definitions, user_defns)
    write_csv(DATA_REF / "current_pscad_model_capability_inventory.csv", inventory)
    (DATA_REF / "current_pscad_model_capability_inventory.json").write_text(json.dumps({"main_sha256": sha256(MAIN), "trial_sha256": sha256(TRIAL), "output_channel_count": len(channels), "capabilities": inventory}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    alignment = alignment_rows()
    write_csv(DATA_REF / "paper_reproduction_alignment_matrix.csv", alignment)

    design = {
        "paper_source_status": "available_primary_paper_source",
        "design_status": "minimum_chain_designed_not_implemented",
        "controlled_existing_sequence_classification": "controlled interface-validation sequence",
        "controlled_existing_sequence_prohibited_classifications": ["paper cascade chain", "natural cascade", "causal propagation"],
        "selected_candidate_chain_id": "MC01",
        "candidates": [
            {
                "candidate_chain_id": "MC01", "paper_evidence_id": "E003;E010;E012",
                "initial_disturbance": "paper-aligned three-phase fault at a traceable network bus",
                "first_required_observability": "PCC voltage plus source V/P/Q and actual DFIG breaker state",
                "first_protection_candidate": "existing DFIG LVRT/local trip path after paper-criterion gap is documented",
                "network_propagation_link": "source power loss and branch P/Q/I/loading redistribution",
                "second_protection_candidate": "future line-overload shadow relay; no breaker connection",
                "required_measurements": ["target-line P", "target-line Q", "target-line I", "target-line loading ratio", "line breaker state", "PCC voltage", "frequency"],
                "required_existing_components": ["fault source", "DFIG LVRT", "BRK_DFIG", "event packet", "collector", "chronology", "source V/P/Q"],
                "missing_components": ["audited target-line measurements", "line loading limits", "line breaker observability", "overload shadow relay"],
                "minimum_model_change": "First add monitor-only target-line P/Q/I/loading outputs; do not add relay or actuation in that stage.",
                "future_run_count_before_claim": "minimum 2 after staged implementation: one observability baseline and one later shadow-relay evaluation; more required before any natural-cascade claim",
                "claim_boundary": "Paper-aligned candidate design only; no propagation or protection behavior has been implemented or validated.",
                "rejection_reason_if_not_feasible": "Reject if the target branch and its electrical measurements cannot be unambiguously mapped.",
            },
            {
                "candidate_chain_id": "MC02", "paper_evidence_id": "E003;E011",
                "initial_disturbance": "short fault followed by recovery-stage line loading increase",
                "first_required_observability": "target-line loading and breaker state",
                "first_protection_candidate": "future line-overload shadow relay",
                "network_propagation_link": "line opening to subsequent redistribution",
                "second_protection_candidate": "future source/load shadow protection",
                "required_measurements": ["line P/Q/I/loading", "line breaker states", "bus V/f"],
                "required_existing_components": ["fault source", "network model"],
                "missing_components": ["line observability", "shadow relay", "transmission-line actuation boundary"],
                "minimum_model_change": "Same first step as MC01: branch observability only.",
                "future_run_count_before_claim": "at least 2 staged runs after implementation",
                "claim_boundary": "Alternative paper mechanism, not selected as the minimum current path.",
                "rejection_reason_if_not_feasible": "Less immediately reusable than MC01 because the current audited first protection is source-side DFIG LVRT.",
            },
        ],
        "next_stage": "branch observability only",
        "why_this_stage_matches_the_paper": "E003, E010 and E012 place branch-flow redistribution and overload between the first source event and later protection actions.",
        "why_other_stages_are_deferred": "A relay lacks an audited input and branch boundary; extra UVRT duplicates an already audited source-side path; another fixed-timing Run cannot create the missing network propagation measurement.",
        "primary_paper_evidence_supporting_order": ["E003", "E010", "E012"],
    }
    (DATA_REF / "paper_reproduction_minimum_cascade_design.json").write_text(json.dumps(design, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    options = [
        {"option_id": "A", "next_stage": "branch observability only", "selected": "yes", "primary_paper_evidence": "E003;E010;E012", "current_model_evidence": "CAP02;CAP03", "prerequisites": "map target real lines and signal semantics", "why_selected_or_deferred": "Paper requires flow redistribution/overload, while current branch measurements are absent.", "explicit_claim_boundary": "monitor-only; no protection or trip claim"},
        {"option_id": "B", "next_stage": "branch overload shadow relay", "selected": "no", "primary_paper_evidence": "E003", "current_model_evidence": "CAP03;CAP05", "prerequisites": "complete option A; verify limit and target-line boundary", "why_selected_or_deferred": "Deferred because no audited loading input or line boundary exists.", "explicit_claim_boundary": "future shadow only; no breaker connection"},
        {"option_id": "C", "next_stage": "source or load protection shadow monitor", "selected": "no", "primary_paper_evidence": "E004;E005;E006;E007", "current_model_evidence": "CAP08;CAP19-CAP24", "prerequisites": "network propagation observability and target signal maps", "why_selected_or_deferred": "The current DFIG path already covers the first source action; the immediate missing bridge is network-side.", "explicit_claim_boundary": "future monitor only; no validated protection"},
    ]
    write_csv(DATA_REF / "paper_reproduction_next_stage_options.csv", options)

    fidelity = {
        "paper_source_status": "available_primary_paper_source",
        "system_level_fidelity": "partial",
        "topology_fidelity": "partially_aligned",
        "source_model_fidelity": "structurally_aligned_adaptation",
        "fault_scenario_fidelity": "partial_and_not_paper_configured",
        "protection_system_fidelity": "mostly_missing_except_partial_DFIG_LVRT",
        "cascade_mechanism_fidelity": "not_implemented",
        "mitigation_measure_fidelity": "not_implemented",
        "current_reproduction_level": "infrastructure and evidence preparation",
        "current_safe_name": "controlled-interface validation scaffold",
        "strict_reproduction_status": "not_achieved",
        "structural_alignment_status": "partial",
    }
    (DATA_REF / "paper_reproduction_fidelity_assessment.json").write_text(json.dumps(fidelity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_docs(alignment)
    print(json.dumps({"paper_source_status": source_manifest["paper_source_status"], "evidence_count": len(evidence), "capability_count": len(inventory), "alignment_row_count": len(alignment), "next_stage": design["next_stage"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
