# Paper reproduction alignment and minimum cascade plan

## 1. 目标论文身份与原始资料状态

- 题名：《高比例风电系统连锁故障分析与抑制措施研究》
- 作者：许佑欣
- 类型：华北电力大学专业硕士学位论文
- 答辩时间：2024 年 5 月
- 原始 PDF：本地文件存在，SHA-256 记录于 source manifest；53 页均有可提取文本层。
- `paper_source_status = available_primary_paper_source`

## 2. 当前项目的严格复现边界

当前 PNNL 39-bus / 3IBR / DFIG trial 不是论文系统的一比一复现。拓扑族、
一个 Type-3 DFIG 和若干事件接口具有结构对齐价值，但母线替换、源参数、故障
配置、线路保护、减载、常规机组保护和补偿设备均未逐项复现。

## 3. 论文事故链机制拆解

论文直接给出两种机制。与当前 DFIG 基础设施最接近的是脱网主导链：

`初始三相短路 -> PCC 电压扰动 -> 风机电压穿越失败/脱网 -> 功率缺额 -> 潮流大幅转移 -> 线路过负荷候选 -> 线路开断 -> 减载/其余风机或机组保护`。

过载主导链则从短路恢复阶段的线路过载和开断开始，再推动更多潮流转移、
源荷保护和解列。论文明确提醒图示事件并非严格单向因果。

## 4. 当前模型已具备的基础设施

已审计：DFIG LVRT 与本地脱网链、IBR2/IBR3 trial-only 本地开断接口、三源
event packet、collector、chronology，以及三源 V/P/Q monitor-only 记录。
当前三来源受控时序与 V/P/Q Run 属于基础设施验证和记录性动态证据；它们
不构成论文的自然连锁故障复现。

## 5. 当前模型与论文的逐项差距矩阵

完整矩阵见 `data/reference/paper_reproduction_alignment_matrix.csv`。分类计数：
{"partially_aligned": 5, "structurally_aligned_adaptation": 1, "missing": 9, "contradicted": 1}。关键首缺口是：没有面向真实输电支路的
P/Q/I/负载率通道，因而无法观察“源脱网/故障 -> 潮流重分布 -> 支路过载”传播链。

## 6. 当前最安全的项目命名

`controlled-interface validation scaffold`

不能使用 `strict paper reproduction`。在完成线路与保护机制前，也不宜把当前
工程称为完整的 `partial mechanism reproduction`。

## 7. 最小论文式事故链候选方案

首选候选为论文表 2-2 / 图 3-4 支持的脱网主导链。当前 DFIG LVRT 可承接第一
保护动作，但网络传播链缺少真实线路观测。现有固定 DFIG -> IBR2 -> IBR3
定时序列仅为 `controlled interface-validation sequence`，不是 paper cascade chain。

## 8. 下一阶段唯一推荐

`next_stage = branch observability only`

只增加目标线路的 P/Q/I/负载率 monitor-only 输出；不接断路器，不增加 relay。
该顺序由 E003、E010、E012 直接支持：论文把潮流重分布和线路过负荷置于风机
脱网后的传播环节，而 CAP03 证明当前恰缺少这一可观测桥梁。

暂缓 shadow UVRT：当前已有 DFIG LVRT 本地链，下一处论文机制缺口在网络侧。
暂缓 overload shadow relay：尚无可追溯线路量、目标线路边界和验证输入。
暂缓默认基线 Run：重复 Run 不能补齐缺失的线路测量接口。

## 9. 当前不能做的事情

不能把定时开断写成自然级联；不能把未来 shadow 设计写成已实现保护；不能
在缺少线路观测时连接线路断路器；不能先加入 SVC/STATCOM 并宣称抑制效果。

## 10. 结论边界

本轮仅完成原论文证据登记、当前模型静态盘点、逐项差距映射与最小事故链
设计。后续建模应由论文中明确的“故障—保护—网络重分布—后续保护”链条
决定。本轮没有修改 PSCAD、没有 Build、没有 Run，也没有验证自然级联、
物理因果、稳定性、保护协调、电压支撑或 MATLAB 耦合。

## Stage-two branch-observability preflight addendum

The next-stage preflight traced real TLines `E_2_3_1`, `E_1_2_1`,
`E_2_25_1`, and `E_16_19_1`, but none exposes an existing, semantically
confirmed P/Q/I signal path. Because the approved scope prohibited adding
meters or calculations, the stage ended in static fallback without GUI,
Build, Run, or new Output Channels.

P08 therefore remains `missing`; P09 line-overload protection and P10 branch
trip also remain `missing`. The recommended research direction remains
`branch observability only`, but a future task must explicitly authorize
minimal inline meters or establish a native TLine measurement interface.

## Full-network TLine P/Q/I observability implementation addendum

The later full-network TLine measurement stage implemented the previously
recommended branch-observability step as a static, monitor-only trial
extension. All 31 genuine P3 network `TLine` instances now have terminal A/B
native `master:multimeter` P/Q/Crms measurements and six Output Channels per
line, for 186 new branch channels and 448 total XML Output Channels.

This updates P08 from `missing` to `partially_aligned /
implemented_static_only`: the raw line P/Q/I observability bridge now exists,
but no Run has verified power-flow redistribution and no in-model loading
ratio, overload protection, or line trip logic exists. P09 and P10 remain
missing. The safe project name remains `controlled-interface validation
scaffold`; strict paper reproduction remains `not_achieved`.

## Paper-aligned 20 s baseline fault static configuration addendum

The trial project now contains a static paper-aligned baseline fault
configuration. The existing `master:tfaultn` component was reused and configured
for a three-phase fault at the structurally aligned P3 `N29` target, starting at
0.50 s and lasting 2.00 s. The project `Duration of Run` is 20 s. The main
project remains unchanged, the full-network TLine measurement layer remains at
448 XML Output Channels, and PSCAD Build artifacts verify N29 fault branches and
timing code.

This updates P03/P04/P05/P06 to `implemented_static_only` or
`structurally_aligned_adaptation` for the configuration layer. It does not
upgrade the overall reproduction level to strict or dynamic paper reproduction:
no Run was performed, and branch overload, line-trip, UFLS/UVLS, generator
protection, and mitigation mechanisms remain future work.

## Paper-aligned 20 s dynamic Run and full-network TLine response addendum

The approved single PSCAD GUI Run of the already configured 20 s N29
three-phase fault has now been parsed offline. The trial model hash remained
`F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300`, the main
model hash remained
`CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB`, and the
static XML Output Channel count remained 448.

The Run produced a valid 0-20 s time axis and all 31 genuine network TLines
were parsed with terminal A/B P/Q/I metrics, for 186 raw branch signals. This
updates P08 from `implemented_static_only` to
`dynamic_observation_not_causal`: raw power-flow/current redistribution is now
observable in the Run outputs, but loading ratios, overload status, relays,
line trips, and causality remain unavailable.

P09, P10, P11-P15 remain missing. Strict thesis reproduction remains
`not_achieved`; the safe project name remains `controlled-interface validation
scaffold`.

## Full-network TLine rating and offline loading addendum

The next offline audit traced exact generated `.tli` records for all 31 current
network TLines. Each record contains `Total MVA Rating = 100.0`, so the current
project now has a qualified apparent-power rating basis for every audited TLine
and an offline apparent-power loading-ratio reconstruction from the existing
20 s Run.

This refines P08 without upgrading P09/P10: raw redistribution and loading
ratio can be observed for qualified current-model lines, but no inverse-time
relay, thermal time model, protection action, line breaker command, branch
trip, or natural cascade mechanism has been implemented or validated.

The recommended future shadow-overload candidate is `E_28_29_1`; `E_16_19_1`
remains paper-relevant but ranks ninth under the current model's audited
post-clear loading metric. Strict thesis reproduction remains `not_achieved`.

## Stage-five-B semantic correction

The later TLine Total MVA semantic audit reclassified the uniform `100.0 MVA`
field as `uniform_model_value_or_default_parameter`, not a verified continuous
thermal or protection-grade rating. Therefore previous S/100 MVA values must be
read as a `100-MVA-normalized apparent-power response index`, not an overload
ratio. `E_28_29_1` remains only the highest normalized apparent-power response
line. Shadow overload relay modeling is blocked until auditable per-line
continuous thermal limits, or a reproducible paper-to-current-model rating
mapping, are available.
