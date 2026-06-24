# Type-3 DFIG 5 s 深三相故障电阻电压暂降扫描

## 研究目的与边界

本轮任务用于探索当前 Type-3 DFIG 接入模型在固定 5 s、2.0-2.15 s、ABC-G 故障下，`Fault ON Resistance` 对 POC 电压暂降、DC-link、chopper、Crowbar 逻辑、RSC/GSC 电流和恢复行为的影响。

本轮不是论文工况复现，也不是任何电网规范意义上的 LVRT 通过性认证。除 PSCAD GUI 中现有 `Three Phase Fault` 的 `Fault ON Resistance` 外，没有改变 Type-3 控制、主电路、故障位置、输出通道、Dblk/Vwind 支架、BRK_DFIG、XFMR_DFIG_22_33 或旧 IBR 状态。

原始 `.out`、`.inf`、`.gf46` 生成目录和截图仅保存在本地临时目录，不提交仓库。

## Crowbar 电流语义闭环

- `Crowbar current:1..3` 已由 GUI 确认为来自 `Crowbar_prot` 内部的 `Icrowbar` 支路测量。
- Output Channel 的 `Scale Factor=1.0`，`Unit` 字段为空；`3IBR.inf` 中对应 PGB 单位字段也为空。
- 因此本轮不再把它写成已确认的 kA，只称为“internal crowbar branch current; unit not independently confirmed”。
- `S1` 已由 GUI 证据确认接入 Crowbar 开关输入，可作为 `DFIG_CROWBAR_STATE` 候选/命令状态；本轮所有工况 `S1` 均未变为 1。
- `Crowbar current:1..3` 的正方向与 1..3 到 A/B/C 的严格相序仍未独立确认。

## 固定工况与扫描电阻值

| 项目 | 固定值 |
|---|---|
| 故障位置 | Type-3 支路 22 kV POC / collector-side，`BRK_DFIG` 左侧现有故障点 |
| 故障类型 | ABC-to-ground |
| 故障窗口 | 2.0 s 到 2.15 s |
| Fault OFF Resistance | 1.0E6 ohm |
| 总仿真时间 | 5.0 s |
| 时间步长 | 5 us |
| 风速 | 11 m/s |
| 扫描 `Fault ON Resistance` | 0.01, 0.03, 0.10, 0.30, 1.00 ohm |

`3.00 ohm` 补点未执行，因为 `0.30 ohm` 和 `1.00 ohm` 已使 `VIBR1_2` 最低值高于 0.70 pu，满足自适应停止规则。

## PGB 映射与解析方法

每个场景运行后立即复制当前 `3IBR.gf46` 输出到本地临时场景目录，并由 `analysis/pscad_tools/analyze_type3_dfig_fault_resistance_sweep.py` 重新读取该目录下的 `3IBR.inf` 建立映射。映射规则为：每 10 个 PGB 对应一个 `3IBR_XX.out` 文件，第一列为时间，数据列为 `((PGB-1) mod 10)+2`。

统计窗口固定为：故障前 1.8-2.0 s，故障中 2.0-2.15 s，故障后 4.0-5.0 s。

## 关键结果总表

| R_fault_ohm | run_status | output_end_time_s | V_min_pu | V_min_time_s | V_fault_mean_pu | V_recovery_time_s | Edc_pu_peak | Ecap_Det_peak_kV | BRK_CHOP_active | BRK_CHOP_duration_s | DFIG_CROWBAR_STATE_active | RSC_max_abs_current | GSC_max_abs_current | Crowbar_current_max_abs | Wpu_pre_mean | Wpu_post_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.01 | completed | 4.9966 | 0.0578648 | 2.07915 | 0.137288 | 2.1912 | 1.42778 | 2.07013 | Yes | 0.0083 | No | 1.71533 | 1.53281 | 1.01881e-05 | 1.20563 | 1.20002 |
| 0.03 | completed | 4.9966 | 0.166541 | 2.0501 | 0.242767 | 2.18705 | 1.32984 | 1.92791 | Yes | 0.0083 | No | 1.45797 | 1.29064 | 8.2605e-06 | 1.20563 | 1.2 |
| 0.1 | completed | 4.9966 | 0.514785 | 2.1497 | 0.554227 | 2.17045 | 1.22739 | 1.77906 | Yes | 0.00415 | No | 0.914968 | 0.967103 | 7.65605e-06 | 1.20563 | 1.19996 |
| 0.3 | completed | 4.9966 | 0.837714 | 2.0169 | 0.892083 | 2.158 | 1.07137 | 1.55359 | No | 0 | No | 0.573352 | 0.578193 | 6.48075e-06 | 1.20563 | 1.19998 |
| 1 | completed | 4.9966 | 0.962159 | 2.01275 | 0.986414 | 2.15385 | 1.01727 | 1.47509 | No | 0 | No | 0.399344 | 0.51496 | 4.66847e-06 | 1.20563 | 1.19999 |

## 电压暂降分层说明

极深、深、中等、较浅仅按本轮 `VIBR1_2` 最低值作相对描述，不引用任何外部 LVRT 标准阈值。

- `0.01 ohm`: `VIBR1_2` 最低值 `0.0578648 pu`，相对分类 `extreme_deep_relative_to_this_sweep`。
- `0.03 ohm`: `VIBR1_2` 最低值 `0.166541 pu`，相对分类 `deep_relative_to_this_sweep`。
- `0.1 ohm`: `VIBR1_2` 最低值 `0.514785 pu`，相对分类 `moderate_relative_to_this_sweep`。
- `0.3 ohm`: `VIBR1_2` 最低值 `0.837714 pu`，相对分类 `shallow_relative_to_this_sweep`。
- `1 ohm`: `VIBR1_2` 最低值 `0.962159 pu`，相对分类 `shallow_relative_to_this_sweep`。

## 逐场景解释

### R_fault = 0.01 ohm

- Build/Run：`completed`，Errors=0，Warnings=2，输出末尾时间 `4.9966 s`。
- POC 电压：故障中最低 `0.0578648 pu`，发生于 `2.07915 s`，故障中均值 `0.137288 pu`，恢复判据时间 `2.1912 s`。
- DC-link：`Edc_pu` 峰值 `1.42778`，`Ecap_Det` 峰值 `2.07013 kV candidate`。
- Chopper：`BRK_CHOP_active=True`，有效持续时间 `0.0083 s`。未确认 0/1 物理方向前，仅称 chopper 命令/候选响应。
- Crowbar：`DFIG_CROWBAR_STATE_active=False`，`Crowbar current` 三相最大绝对值 `1.01881e-05`；本场景不支持 Crowbar 实际导通结论。
- 变流器电流：RSC 三相最大绝对值 `1.71533`，GSC 三相最大绝对值 `1.53281`；瞬时三相量不得误称 RMS。
- 机械侧：`Wpu` 故障前均值 `1.20563`，故障后均值 `1.20002`。

### R_fault = 0.03 ohm

- Build/Run：`completed`，Errors=0，Warnings=0，输出末尾时间 `4.9966 s`。
- POC 电压：故障中最低 `0.166541 pu`，发生于 `2.0501 s`，故障中均值 `0.242767 pu`，恢复判据时间 `2.18705 s`。
- DC-link：`Edc_pu` 峰值 `1.32984`，`Ecap_Det` 峰值 `1.92791 kV candidate`。
- Chopper：`BRK_CHOP_active=True`，有效持续时间 `0.0083 s`。未确认 0/1 物理方向前，仅称 chopper 命令/候选响应。
- Crowbar：`DFIG_CROWBAR_STATE_active=False`，`Crowbar current` 三相最大绝对值 `8.2605e-06`；本场景不支持 Crowbar 实际导通结论。
- 变流器电流：RSC 三相最大绝对值 `1.45797`，GSC 三相最大绝对值 `1.29064`；瞬时三相量不得误称 RMS。
- 机械侧：`Wpu` 故障前均值 `1.20563`，故障后均值 `1.2`。

### R_fault = 0.1 ohm

- Build/Run：`completed`，Errors=0，Warnings=2，输出末尾时间 `4.9966 s`。
- POC 电压：故障中最低 `0.514785 pu`，发生于 `2.1497 s`，故障中均值 `0.554227 pu`，恢复判据时间 `2.17045 s`。
- DC-link：`Edc_pu` 峰值 `1.22739`，`Ecap_Det` 峰值 `1.77906 kV candidate`。
- Chopper：`BRK_CHOP_active=True`，有效持续时间 `0.00415 s`。未确认 0/1 物理方向前，仅称 chopper 命令/候选响应。
- Crowbar：`DFIG_CROWBAR_STATE_active=False`，`Crowbar current` 三相最大绝对值 `7.65605e-06`；本场景不支持 Crowbar 实际导通结论。
- 变流器电流：RSC 三相最大绝对值 `0.914968`，GSC 三相最大绝对值 `0.967103`；瞬时三相量不得误称 RMS。
- 机械侧：`Wpu` 故障前均值 `1.20563`，故障后均值 `1.19996`。

### R_fault = 0.3 ohm

- Build/Run：`completed`，Errors=0，Warnings=2，输出末尾时间 `4.9966 s`。
- POC 电压：故障中最低 `0.837714 pu`，发生于 `2.0169 s`，故障中均值 `0.892083 pu`，恢复判据时间 `2.158 s`。
- DC-link：`Edc_pu` 峰值 `1.07137`，`Ecap_Det` 峰值 `1.55359 kV candidate`。
- Chopper：`BRK_CHOP_active=False`，有效持续时间 `0 s`。未确认 0/1 物理方向前，仅称 chopper 命令/候选响应。
- Crowbar：`DFIG_CROWBAR_STATE_active=False`，`Crowbar current` 三相最大绝对值 `6.48075e-06`；本场景不支持 Crowbar 实际导通结论。
- 变流器电流：RSC 三相最大绝对值 `0.573352`，GSC 三相最大绝对值 `0.578193`；瞬时三相量不得误称 RMS。
- 机械侧：`Wpu` 故障前均值 `1.20563`，故障后均值 `1.19998`。

### R_fault = 1 ohm

- Build/Run：`completed`，Errors=0，Warnings=2，输出末尾时间 `4.9966 s`。
- POC 电压：故障中最低 `0.962159 pu`，发生于 `2.01275 s`，故障中均值 `0.986414 pu`，恢复判据时间 `2.15385 s`。
- DC-link：`Edc_pu` 峰值 `1.01727`，`Ecap_Det` 峰值 `1.47509 kV candidate`。
- Chopper：`BRK_CHOP_active=False`，有效持续时间 `0 s`。未确认 0/1 物理方向前，仅称 chopper 命令/候选响应。
- Crowbar：`DFIG_CROWBAR_STATE_active=False`，`Crowbar current` 三相最大绝对值 `4.66847e-06`；本场景不支持 Crowbar 实际导通结论。
- 变流器电流：RSC 三相最大绝对值 `0.399344`，GSC 三相最大绝对值 `0.51496`；瞬时三相量不得误称 RMS。
- 机械侧：`Wpu` 故障前均值 `1.20563`，故障后均值 `1.19999`。

## 已确认事实

- 所有执行场景均为 `0 Errors`，EMTDC 完成，`.out` 末尾时间约为 4.9966 s。
- 随着 `Fault ON Resistance` 从 0.01 增大到 1.00 ohm，`VIBR1_2` 最低值从约 0.0579 pu 提升到约 0.962 pu，电压暂降明显变浅。
- `BRK_CHOP` 在 0.01、0.03、0.10 ohm 工况出现有效脉冲，在 0.30、1.00 ohm 工况未出现。
- `DFIG_CROWBAR_STATE/S1` 在所有扫描工况均未变为 1；Crowbar 支路电流保持近零量级。
- 最终已将 `Fault ON Resistance` 恢复为 0.01 ohm 并完成 5 s 复跑，`VIBR1_2` 最低值恢复到约 0.057865 pu。

## 工程推断

- 本轮结果支持“故障电阻越大，POC 电压跌落越浅，DC-link 抬升和 RSC/GSC 电流应力越低”的趋势判断。
- 0.01-0.10 ohm 的深跌落会触发 `BRK_CHOP` 候选响应；较浅的 0.30 和 1.00 ohm 工况未触发。
- 在当前 Type-3 参数和故障窗口下，Crowbar 开关状态候选 `S1` 未投入，不能把 Crowbar 作为本轮故障恢复的确定机理。

## 限制与不得下的结论

- 本轮不是论文参数复现，也不是 LVRT 标准合规性验证。
- 不得把 `Crowbar current:1..3` 写成已确认 kA、已确认 A/B/C 相序或已确认正方向。
- 不得把外部 `DFIG_IFLT_A/B/C_KA` 当作 RSC、GSC 或 Crowbar 内部电流。
- 不得把 `Freq_PLL` 当作系统频率；系统频率候选仍以 `SPD30` 为外部对照。
- `BRK_CHOP` 与 `S1` 的 0/1 逻辑含义已部分定位，但物理投入结论仍应以 GUI/定义页最终确认和支路电流响应共同支撑。
