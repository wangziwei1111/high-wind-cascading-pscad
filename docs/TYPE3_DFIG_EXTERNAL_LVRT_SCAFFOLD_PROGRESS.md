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
