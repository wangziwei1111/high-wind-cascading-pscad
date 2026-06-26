# Type-3 DFIG 外部 LVRT 支架当前进度

## 范围

本文记录 2026-06-26 在 PSCAD `3IBR:Main(0):P1(0):P3(0)` 页面上已经手工搭建并通过 Build 静态检查的外部 LVRT 前置支架。该支架目前只用于监测与后续验证，尚未接入 `BRK_DFIG`，尚未实现实际脱网。

本次归档包含当前 `3IBR.pscx` 的轻量快照：

```text
external/pscad_snapshot_20260626_lvrt_scaffold/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
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

## 静态检查状态

用户手工执行 Build 后，PSCAD Build Messages 显示：

```text
0 Errors
44 Warnings
119 Messages
```

其中 44 warnings 属于当前工程已有 warning 水平；本轮新增支架未引入红色 Build errors。

## 当前未完成项

尚未搭建：

- `tVRT(Vs_min_latched)` 允许持续时间计算；
- `Vs_min_latched` 最小电压锁存；
- `duration_exceeded` 比较；
- `trip_latch` 锁存；
- `trip_latch` 输出通道；
- `trip_latch` 与 `BRK_DFIG` 命令合成。

尚未执行：

- 新支架 5 s 基准 Run 验证；
- 0.10 ohm / 0.75 s 无误触发验证；
- 0.10 ohm / 1.25 s 脱网请求时序验证；
- 任何实际 `BRK_DFIG` 开断验证。

## 下一步建议

1. 先运行 5 s 基准，确认 `DFIG_LVRT_LOWV=0`、`DFIG_LVRT_IMMTRIP=0`、`DFIG_LVRT_TIMER_S=0`。
2. 再搭建 `Vs_min_latched` 与 `tVRT` 计算。
3. 先只输出 `DFIG_LVRT_TRIP_LATCH` 监测通道，不接 `BRK_DFIG`。
4. 完成 0.75 s、1.00 s、1.25 s 三个工况的只监测验证后，再讨论断路器命令合成。
