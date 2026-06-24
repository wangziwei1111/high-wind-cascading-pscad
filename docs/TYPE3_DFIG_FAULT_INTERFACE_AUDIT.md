# Type-3 DFIG 受控故障/LVRT 前接口审计

审计日期：2026-06-24  
审计范围：只读静态解析当前 3IBR、Type3WTG_Lib、官方 Type-3 示例和最新 3IBR.gf46 运行产物。  
禁止动作：未修改 PSCAD 模型，未接线，未添加故障元件，未 Build，未 Run，未使用 Computer Use 操作 PSCAD GUI。

## 证据来源

- 已确认事实：当前工程 `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`
- 已确认事实：当前生成目录 `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46`
- 已确认事实：Type-3 库 `C:\pscad_work\type3_wtg_v46_trial\Type3WTG_Lib.pslx`
- 已确认事实：官方 Type-3 示例 `C:\pscad_work\type3_wtg_v46_trial\Type3_Ave_Nov_2018.pscx`
- 已确认事实：仓库基线文档 `docs/TYPE3_DFIG_NOFAULT_BASELINE.md`
- 已确认事实：仓库基线 JSON `data/reference/type3_dfig_nofault_baseline.json`
- 已确认事实：仓库静态拓扑审计 `analysis/snapshot_audit/PSCAD_STATIC_TOPOLOGY_AUDIT.md`

说明：用户要求读取的 `external/pscad_snapshot_20260623/...` 在当前仓库中未发现对应目录。本审计改用当前本机只读 PSCAD 文件和仓库已有审计材料作为定位依据。

## 当前 Type-3 接入状态

- 已确认事实：Type-3 所在页面为 `3IBR:Main(0):P1(0):P3(0)`。
  - 依据：`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx:75234` 的 call path。
- 已确认事实：`Type3WTG_Lib:Type3_WTG_Avg` 实例 ID 为 `2147003001`，位于 P3 坐标 `x=1080, y=936`。
  - 依据：`3IBR.pscx:25406`。
- 已确认事实：当前 Type-3 支路为 `22 kV collector -> BRK_DFIG -> XFMR_DFIG_22_33 -> Type3_WTG_Avg`。
  - `BRK_DFIG`：`master:breaker3`，ID `521858026`，坐标 `x=864, y=990`，依据 `3IBR.pscx:25606`。
  - `XFMR_DFIG_22_33`：`master:xfmr-3p2w`，ID `113665858`，坐标 `x=990, y=990`，依据 `3IBR.pscx:25647`。
  - Type-3 实例：ID `2147003001`，依据 `3IBR.pscx:25406`。
- 已确认事实：22 kV 接入点附近 P/Q/V 表计为 `master:multimeter` ID `1263266056`，坐标 `x=774, y=990`。
  - 依据：`3IBR.pscx:24198`。
- 已确认事实：上游母线/节点标注包括 `GBUS30` 和 `N30`。
  - 依据：`analysis/snapshot_audit/PSCAD_STATIC_TOPOLOGY_AUDIT.md`；当前模型中 `GBUS30`/`N30` 位于 P3 上游 22 kV 区域。

## 当前 3IBR 中已有故障/事件接口清单

### 1. `E_16_24_1` 线路内置故障参数

- 已确认事实：当前 3IBR 存在 ETRAN 线路/段组件 `3IBR:E_16_24_1`，ID `1298064804`。
  - 位置：P3，XML wrapper 坐标 `x=2430, y=1026`，内部 User 坐标 `x=0, y=0`。
  - 依据：`3IBR.pscx:18918-18919`。
- 已确认事实：该对象参数包含 `sfault=0`、`ManEnab=0`、`VR=230.0 [kV]`、`MVA=100.0 [MVA]`、`linc=10.0 [km]`、`steps=3`。
  - 依据：`3IBR.pscx:18920-18944`。
- 静态推断：`sfault=0` 与 `ManEnab=0` 表明该线路故障功能当前未启用。
- 静态推断：该对象属于 16-24 线路段，不在 Type-3 的 N30/GBUS30 22 kV 接入支路上，不适合作为首次 Type-3 LVRT 的故障接口。
- 待 GUI 确认事项：如果后续研究论文指定 16-24 线路故障，需在 GUI 中确认该线路在 IEEE-39 系统中的位置、故障参数页和是否会触发连锁逻辑；本轮不建议使用。

### 2. `Trip` 三相断路器事件

- 已确认事实：当前 3IBR 存在三相断路器 `Trip`，ID `1700980851`，`defn=master:breaker3`，坐标 `x=1944, y=792`。
  - 依据：`3IBR.pscx:24741`。
- 已确认事实：其参数包括 `NAME=Trip`、`BOpen1=0`、`BOpen2=0`、`BOpen3=0`、`InitStatus=0`，未配置内部电流/状态输出名。
  - 依据：`3IBR.pscx:24742-24779`。
- 已确认事实：附近存在 `master:tbreakn` ID `1750255191`，`TO1=100 [s]`、`TO2=100.1 [s]`，以及 Data Label `Trip` ID `1129460063`。
  - 依据：`3IBR.pscx:24780-24799`。
- 静态推断：该断路器位于 N32/G32 附近的跳闸支路，不是 Type-3 的 N30 22 kV POC 故障接口。
- 静态推断：`TO1=100 s` 大于当前 20 s 基线运行时间，因此该跳闸事件在无故障基线中不触发。
- 待 GUI 确认事项：若未来需要系统跳闸/连锁故障，应确认该 `Trip` 的电气位置和控制信号；首次 LVRT 不应启用。

### 3. `BRK` 三相断路器

- 已确认事实：当前 3IBR 存在三相断路器 `BRK`，ID `202853855`，`defn=master:breaker3`，坐标 `x=2358, y=288`。
  - 依据：`3IBR.pscx:21080`。
- 已确认事实：其参数包括 `NAME=BRK`、`BOpen1=2`、`BOpen2=2`、`BOpen3=2`、`InitStatus=0`，未配置状态输出。
  - 依据：`3IBR.pscx:21081-21118`。
- 静态推断：该对象是已有开关/断路器，不是三相短路故障块；位置远离 Type-3 的 N30 支路。
- 待 GUI 确认事项：不建议在首次 Type-3 LVRT 中使用。若后续需要线路开断研究，需 GUI 确认其实际所在支路。

### 4. `BRK_DFIG` Type-3 支路断路器

- 已确认事实：`BRK_DFIG` 为 Type-3 新支路断路器，ID `521858026`，位于 `22 kV collector -> XFMR_DFIG_22_33` 之间。
  - 依据：`3IBR.pscx:25606`。
- 已确认事实：其内部状态输出 A 相配置为 `SBRA=DFIG_BRK_STATE`。
  - 依据：`3IBR.pscx:25634`。
- 已确认事实：状态输出通道 `DFIG_BRK_STATE` 已导出，PGB(18)，`logic`。
  - 依据：`3IBR.gf46\3IBR.inf:18`、`3IBR.gf46\P3.f:1875-1877`。
- 静态推断：该断路器是 Type-3 接入支路隔离设备，不是故障施加设备；首次 LVRT 应保持闭合。
- 待 GUI 确认事项：首次故障前需在 GUI 中确认 `DFIG_BRK_STATE=0` 对应闭合，且故障期间不被任何逻辑打开。

## 官方 Type-3 示例中的故障接口参考

### POC Fault

- 已确认事实：官方示例包含 `master:tpflt` ID `1730345023`，坐标 `x=828, y=360`。
  - 依据：`C:\pscad_work\type3_wtg_v46_trial\Type3_Ave_Nov_2018.pscx:29145`。
- 已确认事实：其参数包括 `Ctype=1`、`RON=0.01 [ohm]`、`ROFF=1.0E6 [ohm]`、`A=1`、`B=0`、`C=0`、`G=1`。
  - 依据：同一对象参数块。
- 已确认事实：附近控制链包括 `Fault` 开关 ID `1357658967`、`Flt type` 选择器 ID `1204222344`、单稳态 `master:monostable` ID `200029863`，`T=0.150 [s]`。
  - 依据：`Type3_Ave_Nov_2018.pscx:28857`、`29040-29130`。
- 静态推断：该 POC Fault 的“手动 Fault 开关 + Flt type + 单稳态 0.150 s 脉冲 + 三相故障块”控制思想可作为未来 3IBR 故障支架的参考。
- 已确认事实：该 POC Fault 同时依赖官方示例的 standalone `V_source`、`BusPOC`、外部变压器与测试电缆环境。
  - `V_source`：ID `1903262663`，依据 `Type3_Ave_Nov_2018.pscx:28740-28742`。
  - `BusPOC`：依据 `Type3_Ave_Nov_2018.pscx:29262`。
  - 外部源 `master:source3`：ID `505106072`，依据 `Type3_Ave_Nov_2018.pscx:29196`。
  - 外部变压器：ID `1691901178`，依据 `Type3_Ave_Nov_2018.pscx:28442`。
- 静态推断：这些 standalone 元件不得直接复制进 3IBR，否则会引入独立电源/测试系统，破坏 IEEE-39 网络拓扑。

### Terminal Fault

- 已确认事实：官方示例包含第二个 `master:tpflt` ID `1237689905`，坐标 `x=1044, y=360`。
  - 依据：`Type3_Ave_Nov_2018.pscx:29371`。
- 已确认事实：其参数包括 `RON=0.2 [ohm]`，并由 `Fault` 开关 ID `412037280`、`Flt type` 选择器 ID `119363881`、单稳态 ID `161502222` 控制。
  - 依据：`Type3_Ave_Nov_2018.pscx:29371-29669`。
- 静态推断：Terminal Fault 的控制思想可借鉴，但不应迁移官方示例的 `Type3_Ave_Nov_2018:Cable_1` ID `1925710979`、图表和测试面板。
  - 依据：`Type3_Ave_Nov_2018.pscx:29683`。

## 当前可用量测映射

以下量测已在无故障基线中通过最新 `.inf/.map/P3.f` 交叉确认，未来首次故障试验应沿用这些通道。新增故障元件后 PGB 顺序可能变化，因此正式故障运行后必须重新解析 `.inf`，不得沿用旧列号。

| 信号 | 已确认事实 / 静态推断 | 当前 PGB | 当前 `.out` / 列 | 单位与约定 | 定位依据 |
|---|---|---:|---|---|---|
| `SPD30` | 已确认事实 | 1 | `3IBR_01.out` col 2 | Hz 候选；系统频率候选，不等同 Type-3 内部 PLL | `3IBR.gf46\3IBR.inf:1`, `P3.f:1015-1017` |
| `VIBR1_2` | 已确认事实 | 2 | `3IBR_01.out` col 3 | pu-like RMS on 22 kV base | `3IBR.gf46\3IBR.inf:2`, `P3.f:2934-2936` |
| `PIBR1_2` | 已确认事实 | 4 | `3IBR_01.out` col 5 | MW；当前表计方向下 Type-3 出力约 +199 MW | `3IBR.gf46\3IBR.inf:4`, `P3.f:2942-2944` |
| `QIBR1_2` | 已确认事实 | 6 | `3IBR_01.out` col 7 | MVAr；当前无故障约 -18 MVAr | `3IBR.gf46\3IBR.inf:6`, `P3.f:2950-2952` |
| `DFIG_VWIND_MS` | 已确认事实 | 17 | `3IBR_02.out` col 8 | m/s，Rate Limiter 输出到 `Vwind` | `3IBR.gf46\3IBR.inf:17`, `P3.f:1861-1863` |
| `DFIG_BRK_STATE` | 已确认事实 | 18 | `3IBR_02.out` col 9 | logic；当前约定 0=闭合 | `3IBR.gf46\3IBR.inf:18`, `P3.f:1875-1877` |
| `DFIG_DBLK_CMD` | 已确认事实 | 19 | `3IBR_02.out` col 10 | logic；约 0.2 s 后为 1 | `3IBR.gf46\3IBR.inf:19`, `P3.f:1879-1881` |

## 未来首次故障候选接入点

### 候选 A：22 kV Type-3 POC / collector-side 接入点（最推荐）

- 静态推断：最小风险候选点位于 P3 上 `PIBR1_2/QIBR1_2/VIBR1_2` 表计、`3.50133 [uH]` 串联电抗和 `BRK_DFIG` 之间的 22 kV Type-3 collector/POC 区域，约坐标 `x=774-864, y=990`。
- 定位依据：
  - 表计 ID `1263266056`，`3IBR.pscx:24198`；
  - `BRK_DFIG` ID `521858026`，`3IBR.pscx:25606`；
  - `XFMR_DFIG_22_33` ID `113665858`，`3IBR.pscx:25647`；
  - 无故障基线中 `PIBR1_2/QIBR1_2/VIBR1_2` 已能反映 Type-3 接入点响应。
- 优点：直接观察 Type-3 支路 P/Q/V/f 与外部命令响应；不需要动上游系统；不复制官方 standalone 测试源。
- 风险：静态 XML 不能完全确认三相节点端子和表计相对方向，必须 GUI 确认故障块将以三相并联支路接到同一个 22 kV 节点，而不是串入主支路或误接到旧 IBR。
- 待 GUI 确认事项：在 PSCAD 中放大 P3，确认该点与 `BRK_DFIG` 左侧三相节点为同一电气节点，且不是旧 IBR 支路节点。

### 候选 B：33 kV Type-3 terminal-side

- 静态推断：可选位置为 `XFMR_DFIG_22_33` 与 Type-3 `AC_sys` 之间的 33 kV 端，约坐标 `x=990-1080, y=990`。
- 优点：更贴近风机端故障。
- 风险：现有 P/Q/V 表计主要在 22 kV 接入侧，若在 33 kV 端施加故障，可能需要新增明确的 33 kV 电压/功率测量；不适合作为首个最小改动 LVRT 验证。

### 候选 C：N30/GBUS30 上游 22 kV 母线

- 静态推断：可选位置为上游 `GBUS30/N30` 及 345/22 kV 变压器下游 22 kV 母线区域。
- 优点：更接近系统级母线电压跌落。
- 风险：影响范围更大，可能同时扰动更多网络和另外两个 IBR；不适合首次只验证 Type-3 基本 LVRT 响应。

## 最小风险首次 LVRT 验证方案草案（不实施）

以下仅为下一阶段手动设计草案，数值均标为待确认假设；不得伪称为论文参数。

- 待确认假设：故障类型为单次三相接地短路/三相 shunt fault，不伴随线路跳闸。
- 待确认假设：故障位置优先选择候选 A，即 Type-3 22 kV POC / collector-side 接入点。
- 待确认假设：故障开始时间 `t = 2.0 s`，理由是 Dblk 已在约 0.2 s 投入且系统已进入无故障稳态；该数值不是论文参数。
- 待确认假设：故障持续时间 `0.150 s`，仅借鉴官方 Type-3 示例 monostable 的 `T=0.150 [s]` 控制思想；不是论文参数。
- 待确认假设：首次应采用轻度电压跌落目标，而不是直接复制官方示例 `RON=0.01/0.2 ohm`。建议目标为 `VIBR1_2` 暂降但不低于约 `0.8 pu`，实际故障阻抗需 GUI/短时试跑确认。
- 待确认假设：首次总仿真时长可先用 `5 s` 做 smoke test；若通过，再做 `20 s` 留档。
- 已确认事实：观察量必须包括 `PIBR1_2`、`QIBR1_2`、`VIBR1_2`、`SPD30`、`DFIG_DBLK_CMD`、`DFIG_VWIND_MS`、`DFIG_BRK_STATE`。
- 停止判据：`0 Errors/0 Warnings` 之外若出现数值发散、`DFIG_BRK_STATE` 从闭合状态改变、`Dblk` 异常掉为 0、`Vwind` 异常变化、P/Q/V/f 持续漂移或振荡加剧，应停止，不进入更深故障。

## 首次试验禁止启用的逻辑

- 已确认事实/约束：首次试验只验证 Type-3 在受控电压跌落下的基本响应。
- 禁止启用：风机脱网、`BRK_DFIG` 自动打开、过载保护、UFLS/UVLS、线路跳闸、系统连锁故障、MATLAB 联动、官方 standalone `V_source/BusPOC/Cable/Fault` 测试环境。
- 静态推断：当前已有 `Trip`/`BRK`/`E_16_24_1` 等对象不应参与首次 Type-3 LVRT；它们属于其他系统事件或线路功能。

## 下一步必须手动确认的 3 个 GUI 问题

1. 待 GUI 确认事项：在 P3 中确认候选 A 的实际三相节点是否正是 `BRK_DFIG` 左侧、`PIBR1_2/QIBR1_2/VIBR1_2` 表计附近的 22 kV Type-3 POC 节点，且不是旧 IBR 支路。
2. 待 GUI 确认事项：确认未来三相故障块只能作为并联 shunt 接到候选 A，不剪断主线、不串入 `BRK_DFIG`、不影响 `XFMR_DFIG_22_33` 参数。
3. 待 GUI 确认事项：确认 `BRK_DFIG` 在无故障和故障期间保持闭合，`DFIG_BRK_STATE=0` 的闭合约定仍成立，且没有隐藏开关/事件会打开它。

## 审计结论

- 已确认事实：当前 3IBR 内未发现可直接复用的 `master:tpflt` 三相故障元件。
- 已确认事实：当前已有 `E_16_24_1` 内置线路故障参数处于禁用状态，且不位于 Type-3 接入支路。
- 已确认事实：当前已有 `Trip`、`BRK`、`BRK_DFIG` 都是断路器/开关对象，不是首次 Type-3 LVRT 所需的三相短路故障接口。
- 静态推断：未来最小风险首次 LVRT 应在 Type-3 22 kV POC / collector-side 节点新增单次、轻度、可禁用的三相并联故障支架。
- 待 GUI 确认事项：候选 A 的具体三相节点和故障块端子接法必须在 PSCAD GUI 中确认后才能实施。
