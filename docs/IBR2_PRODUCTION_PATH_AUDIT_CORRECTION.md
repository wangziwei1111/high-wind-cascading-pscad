# IBR2 Production Path Audit Correction

## Purpose

This correction fixes the audit target used by the final
three-source controlled chronology audit. The earlier final-audit logic read
two module-test harness objects for IBR2 static parameter checks:

- `MODTEST_ONE_SHOT_STIMULUS`
- `MODTEST_OBJECT_EVENT_PACKET`

Those objects are valid only for isolated module-template harness checks. They
are not the production IBR2_TRIAL source-B opening path.

## Corrected production target

The corrected audit resolves the actual production path using read-only XML
and generated `P3.f` evidence:

```text
IBR2_TEST_ENABLE
  -> IBR2_TEST_OPEN_REQ
  -> IBR2_TRIAL_BRK_CMD
  -> BRK_IBR2_TRIAL
  -> IBR2_TRIAL_BRK_STATE / IBR2_CAS_BRK_OPEN
  -> IBR2_CAS_EVT_VALID
  -> IBR2_CAS_CAUSE = 4.0 * IBR2_CAS_EVT_VALID
  -> IBR2_CAS_FIRST_S
  -> IBR2_TRIAL_CASCADE_* Output Channels
```

The harness instances are explicitly excluded because the project hierarchy
places them under `MODULE_TEMPLATE_TEST_HARNESS`.

## Corrected audit result

```text
prior_audit_targeting_status = superseded_harness_target_error
harness_target_exclusion_status = pass
production_target_resolution_status = pass
production_path_trace_status = pass
production_ibr2_test_enable_restored_status = pass
production_ibr2_open_time_restored_status = pass
production_source_b_cause_restored_status = pass
production_source_b_interface_status = pass
production_ibr2_breaker_boundary_status = pass
three_source_dynamic_evidence_recheck_status = pass
final_audit_status = pass
```

## Evidence files

- `analysis/pscad_tools/resolve_ibr2_trial_production_path.py`
- `data/validation/three_source_controlled_chronology_production_target_correction.json`
- `data/validation/three_source_controlled_chronology_production_target_trace.csv`
- `data/validation/three_source_controlled_chronology_final_audit_corrected.json`

## No model or dynamic-data changes

本轮修正的是审计目标，而不是 PSCAD 模型。没有进入 PSCAD GUI，没有
Build，没有 Run，没有保存 PSCAD 工程，也没有修改 `.pscx`、模块定义、
Constant、接线或 Output Channel。

此前三事件受控 Run 的动态输出数据仍保留；本轮没有重跑、修改或覆盖
`three_source_controlled_chronology_run_summary.json`、通道 CSV 或 metrics。
修正后的审计只重新界定：哪些静态参数来自真实 IBR2 production path，哪些
对象只是 module-test harness。

This correction adds no new claim of cascade propagation, physical causality
direction, system stability, protection coordination, MATLAB coupling, or
general applicability.
