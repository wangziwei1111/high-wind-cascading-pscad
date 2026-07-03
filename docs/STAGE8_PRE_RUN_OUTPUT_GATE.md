# STAGE8 pre-run output gate

Status: `pre_run_gate_pass`

This read-only gate is run only after the single GUI repair and Build.

Run is allowed only when all gates are true:

- `git_head_contains_stage7_start`: `True`
- `main_project_sha_unchanged`: `True`
- `p3_f_exists_after_build`: `True`
- `project_map_exists_after_build`: `True`
- `p3_dta_exists_after_build`: `True`
- `all_13_xml_titles_unique`: `True`
- `all_13_generated_pgb_titles_present`: `True`
- `above_threshold_component_repaired`: `True`
- `relay_enable_component_preserved`: `True`
- `paper_ovl1_frozen_line_present`: `True`
- `breaker_command_present`: `True`

If status is `pre_run_gate_pass`, perform exactly one PSCAD Run for Stage 8.
If status is `pre_run_gate_fail`, do not Run; inspect the generated JSON and repair only the failing item.
