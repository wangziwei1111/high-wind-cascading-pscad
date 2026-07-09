# Stage 12 single GUI / Build / Run sheet

本页只允许做 Stage 12 的第二线路保护链。不要改 fault、DFIG、PAPER_OVL1、任何已有 TLine 参数或已有 Output Channel。

## 0. 冻结参数

- `PAPER_OVL2_SELECTED_TLINE = E_26_29_1`
- 第二条 `paper-calibrated effective capacity = 18.262873134069956`
- 阈值倍率：`1.1`
- 等效阈值 T：`20.089160447476953`
- definite delay：`5.0 s`
- 预计 pickup：`9.91 s`
- 预计第二条线路开断：`14.91 s`

这些值不许调。

## 1. 新建 PAPER_OVL2_RELAY

按 `PAPER_OVL1_RELAY` 的结构复制语义，不要重新设计。

输入端口：

- `P_A`
- `Q_A`
- `P_B`
- `Q_B`
- `RELAY_ENABLE`

输出端口：

- `S_A_PU`
- `S_B_PU`
- `S_MAX_PU`
- `CAP_PU_OUT`
- `LOAD_IDX`
- `ABOVE_TH`
- `TIMER_STATE`
- `TRIP_REQ`
- `FIRST_TRIP_T`

内部连接：

1. `P_A`、`Q_A` 平方、相加、开方，输出 `S_A_PU`。
2. `P_B`、`Q_B` 平方、相加、开方，输出 `S_B_PU`。
3. 用二选一或 max 逻辑得到 `S_MAX_PU = max(S_A_PU, S_B_PU)`。
4. Constant 填 `18.262873134069956`，输出到 `CAP_PU_OUT`。
5. Divider：`S_MAX_PU / 18.262873134069956`，输出 `LOAD_IDX`。
6. Single Input Comparator：
   - Threshold Input Value = `1.1`
   - Low Output Level = `0.0`
   - High Output Level = `1.0`
   - Interpolation Compatibility = `Disable`
   - Dimension = `1`
   - Convert Output to Nearest Integer = `Yes`
7. Comparator 输出与 `RELAY_ENABLE` 用乘法器相乘，输出 `ABOVE_TH`。
8. Timer / Pick-Up Delay：
   - 输入 `ABOVE_TH`
   - ON delay = `5.0 s`
   - OFF delay = `0.0 s` 或复位为 0
   - 输出 `TIMER_STATE`
9. SR Latch：
   - S 输入接 `TIMER_STATE`
   - R 输入接 Constant `0.0`
   - Q 输出 `TRIP_REQ`
10. `FIRST_TRIP_T` 暂接 Constant `-1.0`，真实开断时间由输出波形离线解析。

禁止接入：fault、DFIG event、PAPER_OVL1 trip、PAPER_OVL1 cmd、TIME、one-shot、人工脉冲。

## 2. 第二条线路真实 breaker

在真实线路 `E_26_29_1` 的串联支路上插入三相 breaker：

- Name / Breaker Name：`PAPER_OVL2_BRK_CMD`
- 实例命名建议：`BRK_PAPER_OVL2_TRIAL`
- 初态 closed
- RON / ROFF / 状态语义照抄 PAPER_OVL1 breaker，不要自行改值
- 控制端只接 `PAPER_OVL2_BRK_CMD`
- 不允许旁路、不允许并联短接

如果插入后看起来断线，不要靠眼睛判断，Build 后用 `tools/stage12_pre_run_gate.cmd` 查。

## 3. 主页面接线

把 `E_26_29_1` 已有双端测量接入 relay：

- `E_26_29_1_A_P` → `PAPER_OVL2_RELAY.P_A`
- `E_26_29_1_A_Q` → `PAPER_OVL2_RELAY.Q_A`
- `E_26_29_1_B_P` → `PAPER_OVL2_RELAY.P_B`
- `E_26_29_1_B_Q` → `PAPER_OVL2_RELAY.Q_B`
- Constant `1.0` → Data Label `PAPER_OVL2_RELAY_ENABLE` → `RELAY_ENABLE`

Relay 输出：

- `TRIP_REQ` → Data Label `PAPER_OVL2_TRIP_REQUEST`
- `PAPER_OVL2_TRIP_REQUEST` → Data Label `PAPER_OVL2_BRK_CMD`
- `PAPER_OVL2_BRK_CMD` → `BRK_PAPER_OVL2_TRIAL` 控制端

Breaker 状态输出经状态适配/REAL 输出为：

- `PAPER_OVL2_BRK_STATE`

## 4. PAPER_OVL2 event packet

按已有 PAPER_OVL1 / monitored object event packet 模式做：

- event valid：来自 `PAPER_OVL2_BRK_STATE` 或 trip latch 后的真实开断状态
- cause code：固定新 code，建议 `2.0`
- object open：来自 `PAPER_OVL2_BRK_STATE`
- source available：开断前 1，开断后 0
- first trip time：可先输出 `-1.0`，离线解析真实时刻

输出 Data Label：

- `PAPER_OVL2_TRIP_EVENT_VALID`
- `PAPER_OVL2_FIRST_TRIP_TIME_S`

## 5. PAPER_CHAIN chronology monitor

本项已按用户确认改为 waiver：不在 PSCAD 模型里新增 `PAPER_CHAIN__CHRONOLOGY_MONITOR`。

原因：该模块只做观测，不参与控制；Run 后由 Codex 后台离线解析 `DFIG / PAPER_OVL1 / PAPER_OVL2` 输出，生成 chronology 结果。

所以本轮不要再新增以下 9 个 PAPER_CHAIN Output Channel，也不要为了它们修改模型：

```text
PAPER_CHAIN_EVENTED_SOURCE_COUNT
PAPER_CHAIN_FIRST_EVENT_TIME_S
PAPER_CHAIN_SECOND_EVENT_TIME_S
PAPER_CHAIN_THIRD_EVENT_TIME_S
PAPER_CHAIN_FIRST_SOURCE_CODE
PAPER_CHAIN_EVENT_ORDER_CLASS_CODE
PAPER_CHAIN_CHRONOLOGY_CONSISTENT
PAPER_CHAIN_FIRST_TO_SECOND_GAP_S
PAPER_CHAIN_SECOND_TO_THIRD_GAP_S
```

## 6. 新增 Output Channel

新增 13 个 PAPER_OVL2：

1. `PAPER_OVL2_S_A_PU`
2. `PAPER_OVL2_S_B_PU`
3. `PAPER_OVL2_S_MAX_PU`
4. `PAPER_OVL2_EFFECTIVE_CAPACITY_PU`
5. `PAPER_OVL2_LOADING_INDEX_EQ`
6. `PAPER_OVL2_ABOVE_THRESHOLD`
7. `PAPER_OVL2_TIMER_OR_CURVE_STATE`
8. `PAPER_OVL2_TRIP_REQUEST`
9. `PAPER_OVL2_BRK_CMD`
10. `PAPER_OVL2_BRK_STATE`
11. `PAPER_OVL2_TRIP_EVENT_VALID`
12. `PAPER_OVL2_FIRST_TRIP_TIME_S`
13. `PAPER_OVL2_RELAY_ENABLE`

所有 Output Channel：Scale Factor = `1.0`，Use Signal Name as Title = `No`，Title 填上述精确名称。

## 7. Build 后一键 gate 和唯一 Run

1. 保存 trial。
2. Build。
3. 只有 Build Errors = 0 时，双击：`tools/stage12_pre_run_gate.cmd`。
4. 如果显示：`STAGE12 PRE-RUN GATE: PASS`，不要再改任何东西，Run 一次到 20.0 s。
5. 如果显示 BLOCKED，把完整输出发给我，不要 Run。
6. Run 完成后只回复：`阶段十二唯一一次 20 s / 50 µs Run 完成`。

不要开 Graph，不要截图，不要重复 Run，不要改参数后重跑。
