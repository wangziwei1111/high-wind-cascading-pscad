# STAGE7 single GUI / Build / Run sheet

本清单只用于 `3IBR_DFIG1_TRIAL.pscx`。不要打开、保存或修改 main 工程 `3IBR.pscx`。

本阶段只允许你完成一次完整 PSCAD GUI 阶段：改 trial → 保存 → Build 一次 → 若 Build Errors = 0，则 Run 一次 20 s。不要截图、不要打开 Graph、不要复制 `.out/.inf`，不要第二次 Build/Run。

## 0. 冻结参数

- 选中真实线路：`E_28_29_1`
- 参数名：`paper_calibrated_effective_capacity_pu_on_100MVA_base`
- 参数值：`7.872883990`
- 阈值倍数：`1.1`
- 保护时间：`5.0 s definite-time fallback`
- 本参数是“论文标定等效承载能力”，不是 PNNL 真实线路连续热容量，也不是真实保护整定。

## 1. 只打开 trial 工程

打开：

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx`

不要打开 main 工程。

## 2. 在 `E_28_29_1` 上插入真实三相断路器

目标：新增 `BRK_PAPER_OVL1_TRIAL`，串联在 `E_28_29_1` 的真实电气路径上。

要求：

- 元件类型：Three-Phase Breaker。
- 实例名 / Name：`BRK_PAPER_OVL1_TRIAL`。
- 初始状态：闭合。
- 控制信号：只接 `PAPER_OVL1_BRK_CMD`。
- 不改 `E_28_29_1` 的 R/X/B、长度、两端节点、并联身份。
- 保留原来的 A 端和 B 端 multimeter / P/Q/I 测量。
- 不新增第三个线路测量元件。
- 断路器周围不能有并联旁路。

断路器命令极性不要凭空猜。请按 trial 里已成功 Build/Run 的 `BRK_IBR2_TRIAL` 或 `BRK_IBR3_TRIAL` 查同类 Three-Phase Breaker 的控制含义：沿用同一种“命令为 1 时打开 / 命令为 0 时闭合”的受审计语义。如果你看到该 breaker 参数显示相反极性，必须按已有 trial breaker 的实际参数保持一致。

## 3. 新建 Page Module：`PAPER_CALIBRATED_OVERLOAD_RELAY`

模块输入端口：

- `P_A`
- `Q_A`
- `P_B`
- `Q_B`
- `RELAY_ENABLE`

模块参数：

- `EFFECTIVE_CAPACITY_PU = 7.872883990`
- `THRESHOLD_MULTIPLIER = 1.1`
- `PROTECTION_TIME_PARAMETERS = 5.0`

模块输出端口：

- `S_A_PU`
- `S_B_PU`
- `S_MAX_PU`
- `EFFECTIVE_CAPACITY_PU_OUT`
- `LOADING_INDEX_EQ`
- `ABOVE_THRESHOLD`
- `TIMER_OR_CURVE_STATE`
- `TRIP_REQUEST`
- `FIRST_TRIP_TIME_S`

内部逻辑：

1. `S_A_PU = sqrt(P_A*P_A + Q_A*Q_A)`
2. `S_B_PU = sqrt(P_B*P_B + Q_B*Q_B)`
3. `S_MAX_PU = max(S_A_PU, S_B_PU)`
4. `EFFECTIVE_CAPACITY_PU_OUT = EFFECTIVE_CAPACITY_PU`
5. `LOADING_INDEX_EQ = S_MAX_PU / EFFECTIVE_CAPACITY_PU`
6. `ABOVE_THRESHOLD = RELAY_ENABLE AND (LOADING_INDEX_EQ >= 1.1)`
7. `TIMER_OR_CURVE_STATE` 只由 `ABOVE_THRESHOLD` 累计；`ABOVE_THRESHOLD = 0` 时复位为 0。
8. `TRIP_REQUEST` 在 `ABOVE_THRESHOLD` 连续保持 5.0 s 后置 1，并锁存到本次 Run 结束。
9. `FIRST_TRIP_TIME_S` 只在 `TRIP_REQUEST` 第一次从 0 到 1 时锁存当前仿真时间。

禁止接入任何固定绝对时间、故障时刻、DFIG event time、外部 one-shot stimulus 或人工定时源。

## 4. 放置 relay 实例并接线

在 `E_28_29_1` 附近或一个清晰的新页面放置 `PAPER_CALIBRATED_OVERLOAD_RELAY` 实例。

接线：

- `E_28_29_1` A 端真实 P → relay `P_A`
- `E_28_29_1` A 端真实 Q → relay `Q_A`
- `E_28_29_1` B 端真实 P → relay `P_B`
- `E_28_29_1` B 端真实 Q → relay `Q_B`
- 常数 `1.0` → Data Label `PAPER_OVL1_RELAY_ENABLE` → relay `RELAY_ENABLE`
- relay `TRIP_REQUEST` → Data Label `PAPER_OVL1_TRIP_REQUEST`
- `PAPER_OVL1_TRIP_REQUEST` → 按已审计 breaker 极性形成 `PAPER_OVL1_BRK_CMD`
- `PAPER_OVL1_BRK_CMD` → `BRK_PAPER_OVL1_TRIAL` 控制端

## 5. 新增 13 个 Output Channel

只新增，不删除、不重命名、不重连已有 448 个 Output Channel。

每个 Output Channel 参数建议：

- `Use Signal Name as Title? = No`
- `Display Title on Icon? = Yes`
- `Scale Factor = 1.0`
- `Multiple Run Save = Last Run Only`
- `Is Input in Polar Form? = No`

新增通道 Title / 信号：

1. `PAPER_OVL1_S_A_PU`
2. `PAPER_OVL1_S_B_PU`
3. `PAPER_OVL1_S_MAX_PU`
4. `PAPER_OVL1_EFFECTIVE_CAPACITY_PU`
5. `PAPER_OVL1_LOADING_INDEX_EQ`
6. `PAPER_OVL1_ABOVE_THRESHOLD`
7. `PAPER_OVL1_TIMER_OR_CURVE_STATE`
8. `PAPER_OVL1_TRIP_REQUEST`
9. `PAPER_OVL1_BRK_CMD`
10. `PAPER_OVL1_BRK_STATE`
11. `PAPER_OVL1_TRIP_EVENT_VALID`
12. `PAPER_OVL1_FIRST_TRIP_TIME_S`
13. `PAPER_OVL1_RELAY_ENABLE`

语义：

- `PAPER_OVL1_BRK_STATE` 必须来自 `BRK_PAPER_OVL1_TRIAL` 的实际状态/状态适配输出，不允许直接复制命令当状态。
- `PAPER_OVL1_TRIP_EVENT_VALID` 可由实际 breaker open 状态或 `TRIP_REQUEST` 锁存后形成，但审计时会以实际 breaker state 为准。

## 6. 保存、Build、Run

1. 保存 trial。
2. Build 一次。
3. 如果 Build Errors 不等于 0：立刻停止，不要 Run，只把精确错误文本发给我。
4. 如果 Build Errors = 0：Run 一次，Duration of Run 保持 `20 s`。
5. 等唯一一次 20 s Run 完整结束。
6. 不打开 Graph，不截图，不复制 `.out/.inf`，不再次 Build，不第二次 Run。
7. 回到 Codex 只回复：

`阶段一 GUI / Build / Run 完成`
