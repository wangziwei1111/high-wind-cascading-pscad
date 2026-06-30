# Type-3 DFIG 外部 LVRT 支架当前进度

## 范围

本文记录 2026-06-26 至 2026-06-27 在 PSCAD `3IBR:Main(0):P1(0):P3(0)` 页面上手工搭建并通过 Build 静态检查的外部 LVRT 前置支架。该支架目前只用于监测与后续验证，尚未接入 `BRK_DFIG`，尚未实现实际脱网。

本次归档包含当前 `3IBR.pscx` 的轻量快照：

```text
external/pscad_snapshot_20260627_lvrt_vsmin_mem/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

未上传新的 `.gf46`、`.out`、`.inf`、截图、安装包或二进制生成物。

## 已确认接口

### VIBR1_2 测量源

`VIBR1_2` 已通过 PSCAD GUI 确认为 Type-3 支路 22 kV collector-side、`BRK_DFIG` 上游 multimeter 的 RMS voltage 输出。

已确认参数：

```text
RMS Voltage = Yes, Digital
Frequency = 60 Hz
Base Voltage = 22 kV
Active Power output = PIBR1_2
Reactive Power output = QIBR1_2
RMS Voltage output = VIBR1_2
```

工程含义：`VIBR1_2` 可作为未来外部 LVRT 原型的候选 `Vs` 输入来源。正式接线时仍应从对应测量模块的实时输出侧并联取样，不应从 `.out` 文件或 PGB 结果回接。

### BRK_DFIG 控制语义

`BRK_DFIG` 已通过组件说明和 GUI 参数确认为三相联动断路器的命名控制输入。

已确认语义：

```text
BRK_DFIG = 0 -> breaker ON / closed
BRK_DFIG = 1 -> breaker OFF / open
Single Pole Operation = No
Open Possible at any Current = Yes
Breaker Open Resistance = 1.0e6 ohm
Breaker Closed Resistance = 1.0e-3 ohm
DFIG_BRK_STATE = Breaker A Status output, used as three-phase breaker state monitor in this linked mode
```

当前 LVRT 支架未接入 `BRK_DFIG`，因此没有改变断路器命令。

## 已搭建的 LVRT 监测支架

### 低电压事件标志

```text
VIBR1_2 -> Single Input Level Comparator
Threshold Input Value = 0.9
Low output level = 1
High output level = 0
Convert output to nearest integer = Yes
-> DFIG_LVRT_LOWV
-> Output Channel DFIG_LVRT_LOWV
```

语义：

```text
VIBR1_2 < 0.90 pu -> DFIG_LVRT_LOWV = 1
VIBR1_2 > 0.90 pu -> DFIG_LVRT_LOWV = 0
```

### 立即脱网候选标志

```text
VIBR1_2 -> Single Input Level Comparator
Threshold Input Value = 0.2
Low output level = 1
High output level = 0
Convert output to nearest integer = Yes
-> DFIG_LVRT_IMMTRIP
-> Output Channel DFIG_LVRT_IMMTRIP
```

语义：

```text
VIBR1_2 <= 0.20 pu 附近 -> DFIG_LVRT_IMMTRIP = 1
VIBR1_2 > 0.20 pu       -> DFIG_LVRT_IMMTRIP = 0
```

该信号只是监测候选，尚未驱动断路器。

### 低电压事件清零信号

```text
DFIG_LVRT_LOWV -> Single Input Level Comparator
Threshold Input Value = 0.5
Low output level = 1
High output level = 0
Convert output to nearest integer = Yes
-> DFIG_LVRT_CLEAR
```

语义：

```text
DFIG_LVRT_LOWV = 0 -> DFIG_LVRT_CLEAR = 1
DFIG_LVRT_LOWV = 1 -> DFIG_LVRT_CLEAR = 0
```

### 连续低电压事件计时器

```text
DFIG_LVRT_LOWV  -> Resettable Integrator input
DFIG_LVRT_CLEAR -> Integrator Clear input
Integrator output -> DFIG_LVRT_TIMER_S
                 -> Output Channel DFIG_LVRT_TIMER_S
```

Integrator 参数：

```text
Limits = Internal
Resettable = Yes
Integration Method = Trapezoidal
Interpolated Reset = No
Time Constant = 1 s
Initial Output Value = 0
Output Value After Reset = 0
Upper Limit = 10
Lower Limit = 0
```

语义：

```text
低电压事件期间 DFIG_LVRT_TIMER_S 以秒为单位递增。
低电压事件结束时 DFIG_LVRT_CLEAR = 1，计时器复位到 0。
```

### 最低电压反馈记忆支架

2026-06-27 在 PSCAD GUI 中继续搭建 `Vs_min` 相关支架，并引入 Feedback Loop Selector 形成反馈记忆路径。当前结构已通过 Build，但新增 `DFIG_LVRT_VSMIN_MEM` 输出通道后尚未重新 Run，因此仍只能称为待动态验证的反馈记忆支架，不得用于断路器脱网命令。

已搭建结构：

```text
VIBR1_2 - DFIG_LVRT_VSMIN_MEM
    -> Single Input Level Comparator
       Threshold Input Value = 0
       Low output level = 1
       High output level = 0
       Convert output to nearest integer = Yes
    -> DFIG_LVRT_UPDATE_MIN

Two Input Selector #1:
    Ctrl = DFIG_LVRT_UPDATE_MIN
    A = VIBR1_2
    B = DFIG_LVRT_VSMIN_MEM
    Output = DFIG_LVRT_VSMIN_CAND

Two Input Selector #2:
    Ctrl = DFIG_LVRT_CLEAR
    A = 1.0
    B = DFIG_LVRT_VSMIN_CAND
    Output = DFIG_LVRT_VSMIN_PU

DFIG_LVRT_VSMIN_PU
    -> Feedback Loop Selector
       Data Type = Real
       Dimension = 1
       Specify Initial Values = Yes
       Initial Real Value = 1.0
    -> DFIG_LVRT_VSMIN_MEM
       -> Output Channel DFIG_LVRT_VSMIN_MEM
```

新增 Output Channel：

```text
Title = DFIG_LVRT_VSMIN_MEM
Unit = pu
Scale Factor = 1.0
Transfer data = Yes
Display title on icon = Yes
Multiple Run Save = All runs
Default Maximum Display Limit = 1.2
Default Minimum Display Limit = 0
```

图纸旁仍保留早期支架注释，其中文字“Feedback latch still pending”已不再准确描述当前 Build-safe 结构，后续整理图纸时应更新，但本次归档未为此再次修改模型。

```text
LVRT VSMIN scaffold:
current build-safe candidate/reset logic.
Feedback latch still pending before breaker trip use.
```

重要限制：

```text
当前反馈结构已能 Build，但 `DFIG_LVRT_VSMIN_MEM` 的动态最低值保持、复位时刻和启动初值尚未通过输出波形确认。
此前出现的 Feedback Loop Selector `Unused` source 错误已通过把反馈输出改为独立信号 `DFIG_LVRT_VSMIN_MEM` 解决。
在完成 8 s 动态验证之前，不得把该信号升级为已确认的 `Vs_min_latched`，更不得接入 `BRK_DFIG`。
```

## 静态检查状态

用户手工执行 Build 后，PSCAD Build Messages 显示：

```text
0 Errors
2 Warnings
13 Messages
```

两个 warning 为已审计的 `XFMR_DFIG_22_33` 浮空端子提示。本轮新增 Feedback Loop Selector、`DFIG_LVRT_VSMIN_MEM` 信号和输出通道未引入红色 Build errors。该检查只代表静态 Build 通过，尚未代表 VSMIN 反馈记忆语义正确。

在增加 `DFIG_LVRT_VSMIN_MEM` 输出通道之前，用户完成过一次 8 s 运行，最新 `.out` 末尾时间为 `7.99705 s`。该次运行确认 `DFIG_LVRT_LOWV`、`DFIG_LVRT_CLEAR` 和 `DFIG_LVRT_TIMER_S` 有合理时序，但由于当时尚无 `DFIG_LVRT_VSMIN_MEM` 输出通道，不能作为最低电压记忆闭环的验证证据。新增通道后的 8 s Run 尚未执行。

## 当前未完成项

尚未搭建：

- `tVRT(Vs_min_latched)` 允许持续时间计算；
- `Vs_min_latched` 反馈记忆结构的动态验证与正式语义确认；
- `duration_exceeded` 比较；
- `trip_latch` 锁存；
- `trip_latch` 输出通道；
- `trip_latch` 与 `BRK_DFIG` 命令合成。

尚未执行：

- 新增 `DFIG_LVRT_VSMIN_MEM` 输出后的 8 s Run 验证；
- 0.10 ohm / 0.75 s 无误触发验证；
- 0.10 ohm / 1.25 s 脱网请求时序验证；
- 任何实际 `BRK_DFIG` 开断验证。

## 下一步建议

1. 运行当前已配置的 8 s、`0.10 ohm`、`2.0 s / 0.75 s` 故障工况，验证 `DFIG_LVRT_VSMIN_MEM` 是否从 1.0 降至事件最低电压、在事件期间保持，并在 `DFIG_LVRT_CLEAR` 有效后复位。
2. 只有动态结果正确，才将 `DFIG_LVRT_VSMIN_MEM` 确认为 `Vs_min_latched`。
3. 再搭建 `tVRT(Vs_min_latched)` 计算与 `duration_exceeded` 比较。
4. 先只输出 `DFIG_LVRT_TRIP_LATCH` 监测通道，不接 `BRK_DFIG`。
5. 完成 0.75 s、1.00 s、1.25 s 三个工况的只监测验证后，再讨论断路器命令合成。

## 2026-06-27 后续记录

后续无人值守尝试见：

```text
docs/TYPE3_DFIG_LVRT_MONITORING_FULL_VALIDATION.md
data/reference/type3_dfig_lvrt_monitoring_full_validation.json
```

该后续尝试进入 `monitoring_logic_safe_fallback`：完整 `TALLOW / DURATION_EXCEEDED / TRIP_REQUEST / TRIP_LATCH` 监测逻辑未保留在最终 PSCAD 工程中，活动工程恢复到本文记录的 Build=0 VSMIN 支架状态。本文此前记录的历史事实不变。

## 2026-06-28 Trip-Request Manual Validation Update

Manual PSCAD matrix validation for `DFIG_LVRT_TALLOW_S`,
`DFIG_LVRT_DURATION_EXCEEDED`, and `DFIG_LVRT_TRIP_REQUEST` is recorded in:

```text
docs/TYPE3_DFIG_LVRT_TRIP_REQUEST_MANUAL_VALIDATION.md
data/reference/type3_dfig_lvrt_trip_request_manual_validation.json
data/reference/type3_dfig_lvrt_trip_request_manual_validation_summary.csv
```

R1-R5 parsed successfully and passed.  R5 confirmed the immediate-trip path:
`DFIG_LVRT_IMMTRIP` and `DFIG_LVRT_TRIP_REQUEST` first asserted at 2.02 s,
while `DFIG_LVRT_DURATION_EXCEEDED` did not assert.  The final active project
SHA-256 for the successful R5 validation scenario is
`17AEB3DE4C7BBAD5D69DF94AD07BF6681FEF193A70228B57DCBBE0E0E5A1A38B`.

No `TRIP_LATCH` implementation, `DFIG_LVRT_CLEAR` modification, `BRK_DFIG`
command integration, physical breaker opening, or MATLAB coupling was added.

## 2026-06-29 Main Project SHA Delta Audit

The main-project SHA delta after trial project creation is audited in:

```text
docs/MAIN_PROJECT_SHA_DELTA_AUDIT.md
data/reference/main_project_sha_delta_audit.json
data/reference/main_project_sha_delta_audit_summary.csv
data/reference/main_project_sha_delta_raw_differences.csv
```

Result:

```text
functional_equivalence_status = supported
main_project_integrity_status = main_project_nonfunctional_metadata_difference
trial_resumption_eligibility = eligible_for_separate_task
```

The audit was zero GUI, zero Build, zero Run, and read-only. It did not resume
`IBR2_TRIAL` local breaker construction.

## 2026-06-28 Trip-Latch Minimal Validation Update

Manual PSCAD R5 minimal validation for `DFIG_LVRT_TRIP_LATCH` and trip-aware
`DFIG_LVRT_CLEAR` is recorded in:

```text
docs/TYPE3_DFIG_LVRT_TRIP_LATCH_MINIMAL_VALIDATION.md
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation.json
data/reference/type3_dfig_lvrt_trip_latch_minimal_validation_summary.csv
```

The repaired single R5 run completed, parsed, and passed the trip-latch/CLEAR
minimal acceptance checks:

```text
execution_status = trip_latch_minimal_validation_pass
VIBR1_2 minimum = 0.057826191277082 pu at 2.08 s
VSMIN_MEM minimum = 0.057823195871257 pu at 2.09 s
TRIP_REQUEST first = 2.02 s
TRIP_LATCH first high from 0 s = 2.02 s
TRIP_LATCH prefault max from 0.03 s to 1.99 s = 0.0
CLEAR post-LOWV max = 0.0
DFIG_BRK_STATE changed after startup = false
```

The fix adds a `TIME > 0.5 s` armed gate before the latch input:
`DFIG_LVRT_TRIP_REQUEST_ARMED = DFIG_LVRT_TRIP_REQUEST * DFIG_LVRT_ARMED`.
This blocks the known startup pulse at 0.01-0.02 s from setting the latch.
The old CLEAR output channel is now `DFIG_LVRT_CLEAR_BASE`, while final
`DFIG_LVRT_CLEAR` is measured at the trip-aware CLEAR output.

Safety boundary for this minimal validation:

```text
No BRK_DFIG command integration.
No physical breaker opening.
No actual turbine disconnection.
No MATLAB coupling.
```

## 2026-06-28 Breaker Command Validation Update

The breaker-command integration and single R5 validation are recorded in:

```text
docs/TYPE3_DFIG_LVRT_BRK_COMMAND_VALIDATION.md
data/reference/type3_dfig_lvrt_brk_command_validation.json
data/reference/type3_dfig_lvrt_brk_command_validation_summary.csv
```

The final static command path is:

```text
DFIG_LVRT_EXISTING_BRK_CMD_BOOL
+ DFIG_LVRT_TRIP_LATCH_BOOL
-> Hard Limiter [0, 1]
-> DFIG_LVRT_FINAL_BRK_CMD
-> Gain 1
-> BRK_DFIG
```

The single R5 run reached 5.0 s. `TRIP_REQUEST`, `TRIP_LATCH`, and
`DFIG_BRK_STATE` first asserted at 2.02 s, and the breaker state held open.
The measured `DFIG_LVRT_FINAL_BRK_CMD` channel was absent from that run's
`3IBR.inf`, so the overall acceptance status is `unavailable`. The missing
Output Channel was added after the run and passed a final static Build; no
second run was performed.

Final active project SHA-256:

```text
DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6
```

## 2026-06-28 FINAL_BRK_CMD Dynamic Recheck

The single permitted R5 evidence-recheck run completed without any model
change. Its `3IBR.inf` contains `DFIG_LVRT_FINAL_BRK_CMD`, and all B1-B13
checks pass:

```text
execution_status = brk_command_state_validation_pass
TRIP_REQUEST first = 2.02 s
TRIP_LATCH first = 2.02 s
FINAL_BRK_CMD first = 2.02 s
BRK_STATE first open = 2.02 s
TRIP_LATCH -> FINAL_BRK_CMD delay = 0.0 s
FINAL_BRK_CMD -> BRK_STATE delay = 0.0 s
startup FINAL_BRK_CMD max = 0.0
startup BRK_STATE max = 0.0
BRK_STATE holds open = true
```

This supersedes the preceding `unavailable` dynamic result. The active PSCAD
SHA-256 remained `DA4518483523C1BCAFF2A74AAC356B29B53F9642A8E9D7E9E44FCDA2E96F90E6`.
No second recheck Run was performed.

## 2026-06-28 Closed-Loop Coverage Closeout

The C1/C2/C3 coverage closeout is recorded in:

```text
docs/TYPE3_DFIG_LVRT_CLOSED_LOOP_COVERAGE.md
data/reference/type3_dfig_lvrt_closed_loop_coverage.json
data/reference/type3_dfig_lvrt_closed_loop_coverage_summary.csv
```

The result is partial. C1 completed to 5.0 s and passed all no-fault,
no-false-opening checks with all 15 required channels present. C2 was not Run
because its Build reported a floating input on `master:gain` ID `65646757`;
C3 was skipped by the mandatory stop rule. The historical R5 immediate-trip
result remains pass and is not overwritten.

Task-start parameters were restored through PSCAD GUI, but the final Build
reported two errors on the same gain and the final project SHA-256
`10A3B91EE96B8C3BC6FB32D049D6EEB28C9F0923CFFB72BFDBB1F5EC257A9CEB`
does not match the task-start SHA. Model integrity is recorded as
`model_integrity_needs_explanation`; no direct XML repair was attempted.

## 2026-06-29 Supplemental C2/C3 Runs

After the floating Gain was restored manually, the recovery Build showed
`0 Errors / 46 Warnings / 119 Messages`. C2 and C3 were then run manually and
analyzed from independently archived outputs.

```text
C1 = pass
C2 ride-through = pass
C3 formal acceptance = fail
C3 command-and-state sequence = pass
```

C2 completed without false trip or breaker opening. In C3,
`DURATION_EXCEEDED`, `TRIP_REQUEST`, `TRIP_LATCH`, `FINAL_BRK_CMD`, and
`BRK_STATE` all first asserted at 3.04 s, with zero measured adjacent delay and
the latch/final/state outputs holding through 8.0 s. C3 remains formally failed
because its `VSMIN_MEM` minimum of `0.3301161303713 pu` differs from the
specified `0.379649 pu` reference by more than `0.02 pu`.

The restored active project SHA-256 is
`0FB0F7E3927C1E5863F0692F6223DCF8152987BAE99AB83134DF1955C2713F17` and
still differs from the original task-start SHA, so model integrity remains
`model_integrity_needs_explanation`.

## 2026-06-29 Zero-Run Comparability And Integrity Audit

No PSCAD GUI, Build, Run, save, or model edit was performed. The raw
historical R4 archive was found and compared with current C3 using the same
`[LOWV, TRIP_REQUEST)` window. Both decision-window VSMIN minima are
`0.40784436868089 pu at 3.03 s`, so the like-for-like decision check passes.

The original full-run C3 fail remains unchanged. Its `0.3301161303713 pu`
minimum occurs after BRK_STATE opens, while historical R4 has no equivalent
breaker-open event; reference comparability is `needs_explanation`.

The exact task-start backup and current active project were also parsed and
compared structurally. All 128 differences are nonfunctional metadata/display
differences, with zero functional, test-parameter, Output Channel, wire, or
unclassified differences. Gain ID `65646757` is absent from both files.

```text
model_integrity_status = model_integrity_nonfunctional_metadata_difference
```

Reports:

```text
docs/TYPE3_DFIG_LVRT_C3_VSMIN_COMPARABILITY_AUDIT.md
docs/TYPE3_DFIG_LVRT_MODEL_INTEGRITY_AUDIT.md
```

## 2026-06-29 Protection-State / Cascade-Export Interface

The monitor-only protection-state and cascade-export interface was manually
constructed and passed a final static Build with zero errors. Eight new Output
Channels expose the two cause latches, cause code, original/final command
states, breaker-open state, trip confirmation, and cascade availability.

```text
Protection-state / cascade-export interface: static Build-verified
Dynamic validation: deferred
Final project SHA-256: 891DE753AE9C76AF3F7196278C80AAEC324BDB40EED84F552AAE1F2950E4836C
```

The generated Fortran confirms `TRIP_CAUSE_CODE = 2*IMM + 1*DURATION`,
`TRIP_CONFIRMED = TRIP_LATCH_BOOL * FINAL_CMD_BOOL * BRK_OPEN_BOOL`, and
`CASCADE_AVAILABLE = NOT BRK_OPEN_BOOL`. `BRK_DFIG` remains driven solely by
`DFIG_LVRT_FINAL_BRK_CMD`. No new PSCAD Run was performed and the interface
does not feed back into the existing protection chain.

Historical results remain unchanged: C1 pass, C2 pass, R5 immediate-trip
chain pass, C3 command/state chain pass, legacy C3 full-run VSMIN reference
check fail, and overall closed-loop coverage partial.

## 2026-06-29 Cascade-Event Bus And Single-Source Collector

The monitor-only cascade-event source packet and current single-source
collector are recorded in:

```text
docs/TYPE3_DFIG_LVRT_CASCADE_EVENT_BUS.md
data/reference/type3_dfig_lvrt_cascade_event_bus.json
data/reference/type3_dfig_lvrt_cascade_event_bus_summary.csv
```

The final static audit result is:

```text
structure_status = pass
control_path_isolation_status = pass
output_channel_status = pass
dynamic_behavior_status = unavailable
multi_source_behavior_status = unavailable
```

The collector currently represents only the real `TYPE3_DFIG_1` source. No
second source, synthetic source, new dynamic PSCAD Run, multi-machine cascade
validation, or MATLAB coupling was added. Existing LVRT, `FINAL_BRK_CMD`, and
`BRK_DFIG` control paths remain outside the new monitor-only outputs.

## 2026-06-30 IBR2 Trial-Local Breaker Boundary

Only the independent `3IBR_DFIG1_TRIAL.pscx` project was changed. A physical
three-phase `BRK_IBR2_TRIAL` boundary, closed command, actual state,
standardized open state, source availability, and four Output Channels passed
static XML/Fortran/network-map audit and a zero-error Build.

The protected main project SHA remained
`97AE9A99E199734510352DACBDE6120BBC411356C244C3DEA0ED8B01AB2B7906`.
No Run was performed. This trial boundary is not a qualified monitor-only
second source: no second-source event packet or dual-source collector exists,
and no dynamic breaker action, real source isolation, event timing,
multi-machine propagation, cascade behavior, or MATLAB behavior was validated.
