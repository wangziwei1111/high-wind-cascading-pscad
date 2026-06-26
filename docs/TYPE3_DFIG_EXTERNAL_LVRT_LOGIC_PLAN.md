# Type-3 DFIG 外部 LVRT 脱网逻辑图纸方案设计

## 任务范围与强制限制

本任务只做外部 LVRT 脱网逻辑的设计归档与图纸方案整理。Codex 未使用 Computer Use，未打开或操作 PSCAD，未保存 PSCAD 工程，未 Build/Run，未修改任何 `.pscx/.pslx/.gf46/.inf/.out/XML`、Type3WTG_Lib、`Dblk_DFIG`、`BRK_DFIG`、Three Phase Fault、故障参数、仿真时间、时间步长、现有控制器、主电路、P/Q/V 表计、输出通道或历史波形。

本方案是未来 PSCAD 手工集成前的接口设计。本轮没有把任何 LVRT 信号连到 `BRK_DFIG`，没有在 PSCAD 中实现脱网动作，也没有验证风机切除行为。

## 已有证据与 GUI 侦察结论

本方案吸收了本地未提交草稿 `docs/TYPE3_DFIG_EXTERNAL_LVRT_GUI_RECON_DRAFT.md` 中的用户截图侦察信息，并在本提交中删除该草稿。

已确认的接口事实如下：

1. `VIBR1_2` 的搜索结果显示其关联对象包括 P3 页面中的 multimeter、PGB、curve 和 datalabel。截图中该测量点位于 Type-3 支路 22 kV collector-side、`BRK_DFIG` 上游附近，可作为未来外部 LVRT 原型的候选 `Vs` 观测量。
2. `BRK_DFIG` 元件位于 `VIBR1_2` 测量点下游、`XFMR_DFIG_22_33` 上游。其附近已存在 `BRK_DFIG` 命令标签和 `DFIG_BRK_STATE` 状态输出。

这些事实只确认了图纸位置和观测关系。它们并不证明 `VIBR1_2` 的 PGB 输出标签可以作为 PSCAD 控制模块输入，也不证明 `BRK_DFIG` 的开断极性、控制端口名称或命令语义已被确认。

## 设计目标

未来外部 LVRT 原型的目标是：在不修改 Type3WTG_Lib 内部控制器的前提下，基于 Type-3 支路 POC/collector-side 电压候选量 `Vs` 生成外部 `trip_latch`，并在完成 `BRK_DFIG` 命令极性和合成方式确认后，请求 Type-3 支路开断。

该原型只覆盖低电压穿越脱网逻辑，不包含高电压、频率、过流、UFLS/UVLS、线路跳闸、MATLAB 联动或连锁故障逻辑。

## 外部 LVRT 原型边界规则

项目第一版低电压边界规则为：

```text
Vs <= 0.20 pu:
    immediate_trip_request

0.20 < Vs < 0.90 pu:
    tVRT(Vs) = 0.625 + ((Vs - 0.20) / 0.70) * 1.375

Vs >= 0.90 pu:
    若 trip_latch = 0，则结束连续低电压事件并清除计时状态

trip_latch = 1:
    当前仿真内保持锁存，不自动重合闸
```

其中 `Vs` 为未来外部 LVRT 原型的 POC/collector-side 电压输入，单位为 pu。`trip_latch=1` 的规范语义是“请求 Type-3 支路开断”，但实际接入 `BRK_DFIG` 前仍必须确认断路器命令极性和合成方式。

## 连续低电压事件状态机

本方案采用“连续低电压事件中的最小电压锁存”计时方法：

1. 当 `Vs < 0.90 pu` 且 `trip_latch=0` 时，低电压事件开始或继续。
2. 事件期间持续更新 `Vs_min_latched = min(Vs_min_latched, Vs)`。
3. 若 `Vs_min_latched <= 0.20 pu`，立即置位 `trip_latch=1`，原因为 `immediate_low_voltage`。
4. 若 `0.20 < Vs_min_latched < 0.90`，计算 `t_allow = 0.625 + ((Vs_min_latched - 0.20) / 0.70) * 1.375`。
5. 若 `event_elapsed >= t_allow`，置位 `trip_latch=1`，原因为 `duration_exceeded`。
6. 若 `Vs >= 0.90 pu` 且 `trip_latch=0`，清除本次低电压事件、计时状态和最小电压锁存值。
7. 若 `trip_latch=1`，本次仿真内不自动复归、不自动重合闸。

## 电压测量输入接口方案

`VIBR1_2` 已证明当前模型中存在 Type-3 支路 22 kV collector-side 电压观测量，并且持续时间扫描和离线回放已使用该量作为电压暂降深度比较量。

但未来 PSCAD 集成时不能直接假定 PGB 输出标签或 `.out` 通道就是可接入保护逻辑的实时控制线。实际图纸集成必须从对应物理测量模块的控制输出处并联取样，确认以下事项：

- 取样点确实位于 `BRK_DFIG` 上游、Type-3 支路 22 kV collector-side。
- 输出量的 pu 基准与离线回放中的 `VIBR1_2` 一致。
- 是否需要独立的缩放、限幅、滤波或信号有效性检查。
- 取样不会反向影响既有 PGB、图表或测量链路。
- 控制步长和采样语义适合作为 LVRT 状态机输入。

因此 Mermaid 图中将该接口标为“candidate physical measurement source - GUI confirmation required”。

## BRK_DFIG 命令合成接口方案

未来 LVRT 逻辑的规范输出为 `trip_latch`，含义是请求 Type-3 支路开断。该信号不得直接覆盖现有 `BRK_DFIG` 命令线。

当前仍未确认：

- `BRK_DFIG` 的实际控制端口名称。
- 现有 `BRK_DFIG` 命令路径的 0/1 语义。
- `BRK_DFIG` 开断命令的极性。
- 断路器需要电平保持、脉冲、延时还是其他命令形式。
- 外部 LVRT 请求应以哪种安全合成方式与现有命令共存。

因此本方案只定义抽象接口：

```text
existing BRK_DFIG command path
  -> TBD command combiner / polarity adapter
  -> BRK_DFIG control input

external LVRT trip_latch
  -> TBD command combiner / polarity adapter
```

在完成 GUI 语义确认前，不预设任何门类型、极性或优先级，也不建议删除、替换、旁路现有命令路径。

## Mermaid 逻辑图纸说明

Mermaid 源文件位于：

```text
docs/diagrams/type3_dfig_external_lvrt_logic_plan.mmd
```

图纸分为四个区域：

1. 电压输入区：从 Type-3 22 kV collector-side 物理测量点并联取样，经过 pu 基准与信号有效性检查后输入 LVRT 状态机。
2. 连续低电压事件状态机：实现 `Vs < 0.90 pu` 事件保持、`Vs_min_latched` 更新、立即脱网请求、延时越限请求和锁存。
3. `BRK_DFIG` 命令合成接口区：只画抽象 TBD 合成/极性适配接口，不预设门电路。
4. 验证监测区：只用于观察 `DFIG_BRK_STATE`、`VIBR1_2`、`PIBR1_2`、`QIBR1_2`、`Edc_pu`、`Ecap_Det`、`BRK_CHOP`、`S1`，不得反馈到保护控制逻辑。

## 当前未确认项

1. `VIBR1_2` 对应物理测量模块的实时控制输出端口、单位和 pu 基准。
2. `BRK_DFIG` 控制输入端口名称、开断极性和既有命令来源。
3. `BRK_DFIG` 命令需要持续电平、脉冲还是其他形式。
4. 命令合成/极性适配块的具体实现方式。
5. 接入外部 LVRT 后，是否需要额外输出 `trip_latch`、`event_active`、`Vs_min_latched` 和 `event_elapsed` 以便调试。

## 后续 PSCAD 手动集成顺序

1. 确认 `VIBR1_2` 物理测量模块的实时控制输出位置。
2. 确认电压 pu 基准、缩放和是否需要信号有效性处理。
3. 确认 `BRK_DFIG` 控制端口名称、开断极性和现有命令来源。
4. 确认不破坏原命令路径的安全合成方法。
5. 先搭建外部 LVRT 状态机，但不接入 `BRK_DFIG`，只输出 `trip_latch` 监测量。
6. 验证 0.10 ohm / 0.75 s 场景不误触发。
7. 验证 0.10 ohm / 1.25 s 场景 `trip_latch` 时序接近离线参考。
8. 只有在命令极性与合成方式确认后，才允许把合成命令接入 `BRK_DFIG`。
9. 重新运行 0.75 s、1.00 s、1.25 s 三个场景，比较 `DFIG_BRK_STATE`、P/Q/V、DC-link、chopper 和 crowbar 状态。

## 第一轮验证工况与验收标准

主验证工况：

```text
Fault ON Resistance = 0.10 ohm
Fault OFF Resistance = 1.0E6 ohm
Fault type = ABC-to-ground
Fault start = 2.0 s
Fault duration = 1.25 s
Wind speed = 11 m/s
Solution time step = 5 us
Total simulation time = 8.0 s
```

离线参考预测：

```text
abstract_trip_request time ~= 3.03780 s
trip_cause = duration_exceeded
fault clear time = 3.25 s
```

该预测只来自离线状态机回放，不保证 PSCAD 图纸接线后的实际开断时刻完全一致。实际结果可能受测量缩放、控制块采样点、逻辑极性、命令合成方式和时间步影响。

辅助验证工况：

- 0.10 ohm / 0.75 s：预期 `trip_latch` 不置位，`BRK_DFIG` 不应开断，机组应保持并网并恢复。
- 0.10 ohm / 1.00 s：在连续低电压事件定义下，离线预测 `abstract_trip_request` 约 `3.05025 s`，且发生在故障清除后，用于检查计时解释敏感性。
- 0.10 ohm / 1.25 s：预期 `trip_latch` 在连续低电压事件内置位；若后续人工完成断路器命令合成并通过极性确认，`DFIG_BRK_STATE`、`PIBR1_2`、`QIBR1_2` 应与支路切除一致变化。

## 严格限制与非目标

本方案不实现 PSCAD 逻辑，不接入 `BRK_DFIG`，不修改 Type3WTG_Lib，不修改内部 Dblk，不新增故障、不新增保护、不修改连锁故障逻辑，不代表论文完整模型复现。

监测量 `Edc_pu`、`Ecap_Det`、`BRK_CHOP` 和 `S1` 只用于验证 LVRT 触发后 Type-3 内部响应是否异常，不作为外部 LVRT 脱网原型的输入。
