# Type-3 DFIG 5 s 深三相接地故障 Smoke Test

日期：2026-06-24  
工程：`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`  
生成目录：`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`  
前置仓库提交：`7455bb3`  

本记录只整理用户已在 PSCAD GUI 中完成并保存的 5 s 深故障 smoke test 结果。没有在仓库中提交 PSCAD 模型、`.gf46`、`.out` 或二进制生成物。

## 工况

- 故障元件：`Three Phase Fault`
- 故障位置：Type-3 支路 22 kV POC / collector-side，位于 `BRK_DFIG` 左侧、`PIBR1_2/QIBR1_2/VIBR1_2` 表计附近
- 控制元件：`Timed Fault Logic`
- 故障类型：ABC-to-ground
- `Fault ON Resistance`：`0.01 [ohm]`
- `Fault OFF Resistance`：`1.0E6 [ohm]`
- 故障开始：`2.0 s`
- 故障持续：`0.15 s`
- 故障窗口：`2.0-2.15 s`
- 总仿真时长：`5.0 s`
- 步长：`5 us`

说明：`0.01 ohm` 是硬短路级别，适合作为极端深电压跌落 smoke test，不应称为轻度故障。

## 运行状态

- 用户截图显示：`0 Errors / 0 Warnings / EMTDC run completed`
- 最新 `.out` 末尾时间：`4.9966 s`
- 结论：5 s 深故障 smoke test 通过

## 输出通道映射

| Signal | PGB | File | Column | Unit | Meaning |
|---|---:|---|---:|---|---|
| `SPD30` | 1 | `3IBR_01.out` | 2 | Hz candidate | 系统频率候选，不等同 Type-3 内部 PLL |
| `VIBR1_2` | 2 | `3IBR_01.out` | 3 | pu-like | Type-3 22 kV POC 电压候选 |
| `PIBR1_2` | 4 | `3IBR_01.out` | 5 | MW | Type-3 支路有功，当前表计方向 |
| `QIBR1_2` | 6 | `3IBR_01.out` | 7 | MVAr | Type-3 支路无功，当前表计方向 |
| `DFIG_IFLT_C_KA` | 17 | `3IBR_02.out` | 8 | kA | 三相故障 C 相电流输出 |
| `DFIG_IFLT_B_KA` | 18 | `3IBR_02.out` | 9 | kA | 三相故障 B 相电流输出 |
| `DFIG_IFLT_A_KA` | 19 | `3IBR_02.out` | 10 | kA | 三相故障 A 相电流输出 |
| `DFIG_VWIND_MS` | 20 | `3IBR_02.out` | 11 | m/s | Type-3 外部风速输入 |
| `DFIG_BRK_STATE` | 21 | `3IBR_03.out` | 2 | logic | `BRK_DFIG` 状态，当前约定 `0=closed` |
| `DFIG_DBLK_CMD` | 22 | `3IBR_03.out` | 3 | logic | Type-3 外部 Dblk 命令 |

注意：新增故障电流通道后，`DFIG_VWIND_MS / DFIG_BRK_STATE / DFIG_DBLK_CMD` 的 PGB 顺序已经变化。以后每次新增通道后都必须重新解析 `3IBR.inf`。

## 统计窗口

- 故障前：`1.8-2.0 s`
- 故障中：`2.0-2.15 s`
- 故障后：`4.0-5.0 s`

## 关键统计

| Signal | Window | Min | Mean | Max | Range |
|---|---|---:|---:|---:|---:|
| `VIBR1_2` | pre | 0.996724 | 0.996876 | 0.996996 | 0.000272 |
| `VIBR1_2` | fault | 0.057865 | 0.137288 | 0.987171 | 0.929307 |
| `VIBR1_2` | post | 0.981453 | 0.996965 | 1.011988 | 0.030535 |
| `PIBR1_2` | pre | 200.919171 | 202.088943 | 202.948992 | 2.029821 |
| `PIBR1_2` | fault | -227.879850 | -150.934048 | 196.831883 | 424.711733 |
| `PIBR1_2` | post | 198.896656 | 199.197421 | 199.469323 | 0.572666 |
| `QIBR1_2` | pre | -13.992370 | -13.826583 | -13.640614 | 0.351756 |
| `QIBR1_2` | fault | -13.211935 | 3.924918 | 12.363727 | 25.575662 |
| `QIBR1_2` | post | -43.591470 | -21.508556 | -12.369631 | 31.221839 |
| `DFIG_IFLT_A_KA` | fault | -106.300202 | 18.604561 | 197.602619 | 303.902821 |
| `DFIG_IFLT_B_KA` | fault | -162.864968 | -7.227925 | 98.558851 | 261.423819 |
| `DFIG_IFLT_C_KA` | fault | -137.139455 | -11.376630 | 87.315819 | 224.455274 |
| `DFIG_VWIND_MS` | fault | 11.000000 | 11.000000 | 11.000000 | 0.000000 |
| `DFIG_BRK_STATE` | fault | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `DFIG_DBLK_CMD` | fault | 1.000000 | 1.000000 | 1.000000 | 0.000000 |
| `SPD30` | fault | 60.000000 | 60.000000 | 60.000000 | 0.000000 |

## 结论

已确认事实：`0.01 ohm` 三相接地故障在 `2.0-2.15 s` 期间造成了深电压跌落，`VIBR1_2` 最低约 `0.058 pu`，平均约 `0.137 pu`。  
已确认事实：故障期间 `DFIG_DBLK_CMD=1`、`DFIG_VWIND_MS=11 m/s`、`DFIG_BRK_STATE=0`，`BRK_DFIG` 未打开。  
已确认事实：故障清除后，`4.0-5.0 s` 窗口内电压恢复到约 `0.997 pu`，有功恢复到约 `199.2 MW`。  
静态/数据推断：这是极端深故障 smoke test，不是轻度 LVRT 工况。后续若要论文对齐或做温和电压跌落，应通过故障阻抗或目标电压跌落深度重新整定。  

## 后续建议

1. 保留该工况作为“深三相接地 smoke test”基线。
2. 若进入正式 LVRT 曲线分析，建议增加图表导出或 CSV 摘要，记录 `VIBR1_2`、`PIBR1_2`、`QIBR1_2`、三相故障电流、`DFIG_BRK_STATE`。
3. 若目标是轻度故障，不要使用 `0.01 ohm`；应尝试更大故障电阻或以目标电压暂降比例为准。
