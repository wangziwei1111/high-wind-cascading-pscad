# Type-3 DFIG 外部 LVRT 脱网逻辑原型设计与历史波形回放

## 任务范围

本轮只做离线设计与历史波形回放。未使用 Computer Use，未打开或操作 PSCAD GUI，未 Build/Run，未修改 `.pscx/.pslx/.gf46/.inf/.out`、故障参数、输出通道、控制器或主电路。

本文中的 `trip_request`、`trip_latch` 均为离线抽象信号，只表示“如果未来在 PSCAD 中接入该外部 LVRT 逻辑，按当前波形会在何时提出脱网请求”。本轮没有把该请求接入 `BRK_DFIG`，没有验证断路器实际打开，没有验证 Type-3 风场实际切除，也不代表 PSCAD 模型已经实现了脱网保护。

## 项目 LVRT 边界规则

依据 `docs/TYPE3_DFIG_LVRT_TRIP_CRITERION_AUDIT.md`，本项目采用的低电压穿越外部原型规则为：

```text
tVRT(Vs) =
  0,                                                        Vs <= 0.20 pu
  0.625 + ((Vs - 0.20) / (0.90 - 0.20)) * (2.0 - 0.625),   0.20 < Vs < 0.90 pu
  no low-voltage trip timing,                              Vs >= 0.90 pu
```

边界处理如下：

- `Vs <= 0.20 pu`：立即产生抽象 `trip_request`，并置位 `trip_latch`。
- `0.20 < Vs < 0.90 pu`：进入低电压事件计时，允许持续时间由 `tVRT(Vs)` 给出。
- `Vs >= 0.90 pu`：低电压事件结束。若此前没有跳闸锁存，则清除本次事件计时状态。
- 一旦 `trip_latch=1`，当前仿真内不自动复归、不自动重合闸。

## 候选输入信号

离线回放使用 `VIBR1_2` 作为候选输入。现有持续时间扫描中，`VIBR1_2` 已作为 Type-3 支路 22 kV 接入侧电压量用于暂降深度比较。

限制必须保留：

- `VIBR1_2` 当前来自保存的 PGB 输出，不是已经接入保护逻辑的 PSCAD 控制线。
- 未来外部 LVRT 模块实际应从哪一个可控制信号取样、是否需要滤波、pu 基准如何保证一致，仍需 GUI 确认。
- 本轮只从历史波形预测抽象 `trip_request`，不代表 `BRK_DFIG` 已接收或执行该请求。

## 状态机设计

本轮采用“连续低电压事件中的最小电压锁存”计时方法。

```text
监视起点：
  本次历史回放从故障开始时刻 2.0 s 开始监视，避免启动暂态被误判为 LVRT 事件。

事件启动：
  若 VIBR1_2 < 0.90 pu，且当前没有低电压事件、trip_latch=0：
    event_active = 1
    event_start_time = now
    Vs_min_latched = VIBR1_2(now)

事件更新：
  当 event_active=1、VIBR1_2 < 0.90 pu、trip_latch=0：
    Vs_min_latched = min(Vs_min_latched, VIBR1_2(now))
    event_elapsed = now - event_start_time

立即脱网请求：
  若 Vs_min_latched <= 0.20 pu：
    trip_request = 1
    trip_latch = 1
    trip_cause = immediate_low_voltage

延时越限脱网请求：
  若 0.20 < Vs_min_latched < 0.90：
    t_allow = tVRT(Vs_min_latched)
    若 event_elapsed >= t_allow：
      trip_request = 1
      trip_latch = 1
      trip_cause = duration_exceeded

事件复位：
  若 VIBR1_2 >= 0.90 pu 且 trip_latch=0：
    event_active = 0
    event_start_time 和 Vs_min_latched 清除

锁存行为：
  若 trip_latch=1：
    不自动复归，不自动重合闸。
```

## 离线回放方法

新增脚本：

```text
analysis/pscad_tools/replay_type3_dfig_external_lvrt_trip.py
```

该脚本只读解析每个场景目录中的 `3IBR.inf` 和 `3IBR_*.out`，重新建立 `VIBR1_2` 的 PGB 到 `.out` 文件和列号的映射。当前映射为：

```text
PGB = 2
Group = P3
out_file = 3IBR_01.out
column = 3
unit = blank in .inf
```

回放源目录：

```text
C:\pscad_work\type3_dfig_duration_sweep_tmp\20260626_134153
```

所有六个场景的输出末尾时间均为 `7.99705 s`，可覆盖 8 s 持续时间扫描所需窗口。

## 六个场景回放结果

| 场景 | 故障电阻 | 故障持续时间 | 低压事件起点 | 低压事件结束 | 锁存最小电压 | 允许时间 | 抽象 trip_request | trip 时间 | trip 原因 | 是否在故障清除前 |
|---|---:|---:|---:|---:|---:|---:|---|---:|---|---|
| `r0p10_d0p15` | 0.10 Ω | 0.15 s | 2.00445 s | 2.17045 s | 0.514785 | 1.243328 s | No |  |  |  |
| `r0p10_d0p50` | 0.10 Ω | 0.50 s | 2.00445 s | 2.51905 s | 0.497339 | 1.209058 s | No |  |  |  |
| `r0p10_d0p75` | 0.10 Ω | 0.75 s | 2.00445 s | 3.09590 s | 0.459160 | 1.134065 s | No |  |  |  |
| `r0p10_d1p00` | 0.10 Ω | 1.00 s | 2.00445 s | 3.38225 s | 0.412492 | 1.042396 s | Yes | 3.05025 s | duration_exceeded | No |
| `r0p10_d1p25` | 0.10 Ω | 1.25 s | 2.00445 s | 3.71425 s | 0.379649 | 0.977883 s | Yes | 3.03780 s | duration_exceeded | Yes |
| `r0p10_d1p50` | 0.10 Ω | 1.50 s | 2.00445 s | 4.17075 s | 0.353510 | 0.926538 s | Yes | 3.03780 s | duration_exceeded | Yes |

本轮没有任何场景达到 `Vs <= 0.20 pu`，因此没有 `immediate_low_voltage` 触发。所有触发均来自 `duration_exceeded`。

## 1.25 s 场景详解

`r0p10_d1p25` 中，低电压事件从 `2.00445 s` 开始，`VIBR1_2` 的锁存最小值为 `0.379649 pu`。按项目规则计算：

```text
t_allow = 0.977883 s
```

离线回放得到：

```text
trip_time = 3.03780 s
event_elapsed_at_trip = 1.03335 s
trip_cause = duration_exceeded
fault_clear_time = 3.25 s
trip_before_fault_clear = True
```

解释：若未来外部 LVRT 逻辑采用本文状态机，并把其输出接入真实脱网执行路径，则该历史波形会在故障尚未清除前提出抽象脱网请求。本轮没有验证真实断路器动作。

## 1.50 s 场景详解

`r0p10_d1p50` 中，低电压事件同样从 `2.00445 s` 开始，`VIBR1_2` 的锁存最小值为 `0.353510 pu`。按项目规则计算：

```text
t_allow = 0.926538 s
```

离线回放得到：

```text
trip_time = 3.03780 s
event_elapsed_at_trip = 1.03335 s
trip_cause = duration_exceeded
fault_clear_time = 3.50 s
trip_before_fault_clear = True
```

解释：该场景比 1.25 s 场景的锁存最低电压更低，允许时间更短，因此同样会产生抽象 `duration_exceeded` 请求，且发生在故障清除之前。

## 与持续时间扫描参考窗口的关系

`data/reference/type3_dfig_lvrt_duration_boundary_summary.csv` 中的参考分类基于“故障窗口内 `VIBR1_2 < 0.90 pu` 的持续时间”与由故障窗口最小电压计算的允许时间之差。该参考对 `r0p10_d1p25` 和 `r0p10_d1p50` 判为 `exceeds_reference_window`，与本轮抽象回放一致。

`r0p10_d1p00` 是一个需要单独说明的边界差异：

- 参考窗口中，故障窗口内低于 0.90 pu 的时间为 `0.99185 s`，参考裕度仍为正，因此此前归为 `within_reference_window`。
- 本轮状态机把故障清除后但电压尚未恢复至 0.90 pu 的低压段继续视为同一个连续低电压事件。
- 因此 `r0p10_d1p00` 在 `3.05025 s` 产生抽象 `duration_exceeded`，但该时刻晚于故障清除时刻 `3.00 s`，早于低压事件结束时刻 `3.38225 s`。

这不是数值冲突，而是计时定义不同：一个只比较故障窗口，另一个模拟连续事件计时器。未来 PSCAD 实现前必须确认论文或项目口径是否允许故障清除后的恢复暂态继续计入低电压事件。

## 已确认事实

- 六个场景的 `3IBR.inf` 和 `3IBR_*.out` 均成功读取。
- 所有场景输出末尾时间均接近 8 s，为 `7.99705 s`。
- 六个场景的最低 `VIBR1_2` 均高于 `0.20 pu`，没有立即低压脱网请求。
- `0.15 s`、`0.50 s`、`0.75 s` 场景在抽象计时器越限前恢复至 `0.90 pu` 以上。
- `1.00 s`、`1.25 s`、`1.50 s` 场景在连续低电压事件计时定义下产生抽象 `duration_exceeded`。

## 工程选择与限制

- 本轮回放从故障开始时刻 `2.0 s` 才开始监视，避免启动阶段电压未建立导致误触发。
- 状态机采用最小电压锁存，而不是用每个采样点的瞬时电压不断放宽允许时间。
- 低压事件恢复阈值为 `0.90 pu`，与项目边界规则一致。
- `trip_request` 与 `BRK_DFIG` 之间尚无 PSCAD 接线关系。
- 没有验证 `BRK_DFIG` 的打开延时、开断能力、状态复归或与现有 `BRK_DFIG` 命令的逻辑合成。
- 没有验证 Type-3 风场脱网后对 P/Q/V、内部 DC-link、RSC/GSC 或系统频率的实际影响。

## 待 GUI 确认事项

下一阶段进入 PSCAD 前，应先手工确认：

1. `VIBR1_2` 对应的可控制电压信号来源在哪里，是否能安全分支给外部 LVRT 模块。
2. 未来外部 `trip_request` 应如何与现有 `BRK_DFIG` 命令合成，且不破坏已有默认闭合逻辑。
3. `trip_latch` 是否应保持到仿真结束，还是由手动复归或场景复位信号清除。
4. 故障清除后、母线电压尚未恢复到 0.90 pu 的恢复暂态是否应继续计入低电压事件。

## 下一步建议

可以进入“外部 LVRT 脱网逻辑 PSCAD 手工设计图审查”阶段，但仍不应立即接入主电路。建议先在图纸空白区画出并核查：`VIBR1_2` 取样、低压事件检测、最小电压锁存、`tVRT` 计算、计时器、`trip_latch`、以及未来到 `BRK_DFIG` 的逻辑接口。待用户确认后，再决定是否进入真实 PSCAD 接线与短时验证。
