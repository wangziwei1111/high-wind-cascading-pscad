# Type-3 DFIG 深故障 LVRT 内部信号只读审计

审计时间：2026-06-24

审计范围：只读检查当前仓库材料、本地 PSCAD 快照、`Type3WTG_Lib.pslx`、官方 `Type3_Ave_Nov_2018.pscx`、当前 `3IBR.gf46` 的 `.inf/.map/.out/.f/.dta`。本轮没有打开或操作 PSCAD GUI，没有 Build/Run，没有修改 `.pscx/.pslx/XML`，没有新增任何模型元件或输出通道。

## 一、已确认可用的现有量

当前 `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\3IBR.inf` 已导出以下外部/POC/故障量。它们可用于描述深三相接地故障的外部现象，但不能直接替代 Type-3 内部 LVRT 控制状态。

| 量名 | PGB | 输出文件/列 | 单位 | 已确认用途 | 不能替代的内部量 | 证据 |
|---|---:|---|---|---|---|---|
| `SPD30` | 1 | `3IBR_01.out` col 2 | 未标注，按系统频率候选使用 | 39 节点系统 N30/GBUS30 附近频率候选 | Type-3 内部 PLL 频率 `Freq_PLL` | `3IBR.inf:1`; `3IBR.pscx:20592,20614` |
| `VIBR1_2` | 2 | `3IBR_01.out` col 3 | pu/未标注 | 第一条 Type-3 支路 22 kV 接入点附近电压 | DC-link 电压、定子/转子内部电压、PLL 输入电压 | `3IBR.inf:2`; `3IBR.pscx:24218,24293,24315` |
| `PIBR1_2` | 4 | `3IBR_01.out` col 5 | MW/未标注 | Type-3 支路附近 P 表计 | Type-3 内部 `Pg_pu`、RSC/GSC 功率或机械功率 | `3IBR.inf:4`; `3IBR.pscx:24216,24320,24342` |
| `QIBR1_2` | 6 | `3IBR_01.out` col 7 | MVAr/未标注 | Type-3 支路附近 Q 表计 | Type-3 内部 `Qg_pu`、Q 控制器参考/限幅 | `3IBR.inf:6`; `3IBR.pscx:24217,24347,24369` |
| `DFIG_IFLT_A_KA` | 19 | `3IBR_02.out` col 10 | kA | 新增三相故障元件 A 相故障电流 | 转子电流、RSC 电流、GSC 电流、Crowbar 电流 | `3IBR.inf:19`; `3IBR.pscx:25896,25937` |
| `DFIG_IFLT_B_KA` | 18 | `3IBR_02.out` col 9 | kA | 新增三相故障元件 B 相故障电流 | 转子电流、RSC 电流、GSC 电流、Crowbar 电流 | `3IBR.inf:18`; `3IBR.pscx:25897,25950` |
| `DFIG_IFLT_C_KA` | 17 | `3IBR_02.out` col 8 | kA | 新增三相故障元件 C 相故障电流 | 转子电流、RSC 电流、GSC 电流、Crowbar 电流 | `3IBR.inf:17`; `3IBR.pscx:25898,25974` |
| `DFIG_DBLK_CMD` | 22 | `3IBR_03.out` col 3 | logic | 送入 Type3_WTG_Avg 外部 `Dblk` 的命令 | 内部 `Dblk_Rotor`、`Dblk_VdcCtrl`、RSC/GSC 实际闭锁状态 | `3IBR.inf:22`; `3IBR.pscx:25409,25571` |
| `DFIG_VWIND_MS` | 20 | `3IBR_02.out` col 11 | m/s | 送入 Type3_WTG_Avg 外部 `Vwind` 的风速 | 机械侧功率、转子速度、Pitch、风轮转矩 | `3IBR.inf:20`; `3IBR.pscx:25408,25426,25838` |
| `DFIG_BRK_STATE` | 21 | `3IBR_03.out` col 2 | logic | `BRK_DFIG` A 相状态输出，当前约定 0=闭合 | Crowbar 状态、Type-3 内部并网/同步命令、`BRK ord` | `3IBR.inf:21`; `3IBR.pscx:25600,25726` |

当前 `.inf` 同时包含大量 Type-3 内部 PGB 输出，编号从 `PGB(213)` 至 `PGB(348)`，说明这些内部候选量已经进入当前运行输出索引。由于其中部分名称重复或语义较细，例如 `Pg_pu`、`Qg_pu`、`Iqr_pu` 重复出现，正式解释前仍需要 GUI 对照确认其取样线和方向。

## 二、内部信号候选总表

输出文件列号按 PSCAD 的 10 个 PGB/文件规则计算：`file = floor((PGB-1)/10)+1`，`column = ((PGB-1) mod 10)+2`，第 1 列为时间。

| 信号类别 | 候选真实名称 | Definition / 子模块 | 层级路径 | 证据类型 | 源文件与定位 | 已存在输出 | 可直接作正式解释量 | 后续 GUI 新增/确认 | 单位/方向/逻辑 | 置信度 |
|---|---|---|---|---|---|---|---|---|---|---|
| DC-link 电压 | `Ecap_Det` | `DFIG_Converters_Avg` | `Type3_WTG_Avg -> DFIG_Converters_Avg` | PGB / 生成代码 | `3IBR.inf:256`; `DFIG_Converters_Avg.f:918`; `3IBR.map:653` | 是，`3IBR_26.out` col 7 | 可作为 DC-link kV 候选 | 需 GUI 确认 `Ecap_Det` 是 DC-link 物理电压显示量 | kV，正值为 DC-link 电压 | 高 |
| DC-link 电压 pu | `Edc_pu` | `Grid_side_Controls` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Grid_side_Controls` | PGB / 生成代码 | `3IBR.inf:284`; `Grid_side_Controls.f:818-820`; `Type3WTG_Lib.pslx:6009,8170` | 是，`3IBR_29.out` col 5 | 可与 `Ecap_Det` 互证 | 需 GUI 确认基准 `Vdc_base` 与单位 | pu，`Edc/Vdc_base` | 高 |
| DC-link 参考/阈值 | `Vdc_chop_on`, `Vdc_chop_off` | `Chopper` / `DFIG_Converters_Avg` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Chopper` | 参数 / 比较器 | `Type3WTG_Lib.pslx:680-681,10117-10123`; `Chopper.f:141-148` | 阈值未作为独立 PGB；`BRK_CHOP` 已输出 | 可作参数证据，不是动态量 | 无需新增动态输出；必要时 GUI 截参数 | kV，`Vdc_chop_on=1.6543`, `Vdc_chop_off=1.605` | 高 |
| Crowbar 触发阈值 | `Vdc_crowbar_on`, `Ir_limit`, `Time_crowbar` | `Crowbar_prot` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Crowbar_prot` | 参数 / 端口 | `Type3WTG_Lib.pslx:703-706,10530-10540`; `Crowbar_prot.f:14-15,52-54` | 阈值未独立输出 | 可作触发条件参数证据 | 需 GUI 确认 `Tcrow_bar` 与 `Icrow_bar` 当前数值来源 | kV, kA, s | 高 |
| Crowbar 过流逻辑 | `Iovercur` | `Crowbar_prot` | 同上 | PGB / 比较器 | `3IBR.inf:321`; `Crowbar_prot.f:184-189`; `3IBR.map:718` | 是，`3IBR_33.out` col 2 | 可作为过流触发候选 | 必须 GUI 确认 active-high 和是否等于最终 Crowbar 动作 | logic，疑似 1=过流 | 中 |
| Crowbar 状态/保持逻辑 | `S1`, `Mono_out`, `Reset` | `Crowbar_prot` | 同上 | PGB / flip-flop / monostable | `3IBR.inf:322-324`; `Crowbar_prot.f:226-242,264-284`; `3IBR.map:719-721` | 是，`S1`: `3IBR_33.out` col 4; `Mono_out`: col 5 | 不能单独直接宣称 Crowbar 已动作 | 必须 GUI 对照 Crowbar 定义页确认哪个量代表实际 Crowbar 闭合 | logic，方向待确认 | 中 |
| Crowbar 电流 | `Crowbar current:1..3` / `Icrowbar` | `Crowbar_prot` | 同上 | PGB / 电流表 | `3IBR.inf:318-320`; `Crowbar_prot.f:514-527`; `Type3WTG_Lib.pslx:11110-11156` | 是，`3IBR_32.out` cols 9-11 | 可作为 Crowbar 支路电流候选 | 需 GUI 确认相序和量纲 | 未标注；代码从 `CBR` 读支路电流 | 高 |
| Chopper 状态 | `BRK_CHOP` | `Chopper` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Chopper` | PGB / hysteresis | `3IBR.inf:328`; `Chopper.f:141-148`; `Type3WTG_Lib.pslx:10263,10343` | 是，`3IBR_33.out` col 9 | 可解释 DC-link chopper 动作候选 | 需 GUI 确认 1/0 方向 | logic，疑似 1=chopper on | 高 |
| RSC 三相电流 | `I_RS:1..3` | `DFIG_Converters_Avg` | `Type3_WTG_Avg -> DFIG_Converters_Avg` | PGB / converter input | `3IBR.inf:257-259`; `DFIG_Converters_Avg.f:493-495`; `3IBR.map:654-656` | 是，`3IBR_26.out` cols 8-10 | 可作为 RSC 电流物理候选 | 需 GUI 确认相序和符号方向 | kA | 高 |
| RSC dq 电流 | `Idr_pu`, `Iqr_pu` | `Rotor_side_Controls` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Rotor_side_Controls` | PGB / dq transform | `3IBR.inf:312,298,314`; `Rotor_side_Controls.f:843-846,995-1005,1045-1055`; `Type3WTG_Lib.pslx:13978,14018` | 是，`Idr_pu`: `3IBR_32.out` col 3; `Iqr_pu`: `3IBR_30.out` col 9 and `3IBR_32.out` col 5 | 可作为 dq 电流候选 | 因 `Iqr_pu` 有重复 PGB，必须 GUI 确认选哪一路 | pu，dq 正方向待确认 | 中 |
| RSC 限流状态 | `Imax_pu`, `Imax_d_pu`, `ImaxN_d_pu`, `Low_Cu_Manag` | `Rotor_side_Controls` | 同上 | PGB / limiter / rate limiter | `3IBR.inf:288,305,311,317`; `Rotor_side_Controls.f:390,626-628,840-861,1041-1067` | 是 | 可作为限流器状态候选 | 需 GUI 确认物理意义和使用哪个量解释 LVRT | pu / logic-like management factor | 中 |
| GSC 三相电流 | `Iconv:1..3` | `DFIG_Converters_Avg` | `Type3_WTG_Avg -> DFIG_Converters_Avg` | PGB / converter current | `3IBR.inf:263-265`; `DFIG_Converters_Avg.f:407-408`; `3IBR.map:660-662` | 是，`3IBR_27.out` cols 4-6 | 可作为 GSC 电流物理候选 | 需 GUI 确认相序和符号方向 | kA | 高 |
| GSC dq 电流 | `Id_pu_Gsc`, `Iq_pu_Gsc` | `Grid_side_Controls` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Grid_side_Controls` | PGB / dq transform | `3IBR.inf:275-276`; `Grid_side_Controls.f:556-577,782-788`; `3IBR.map:672-673` | 是，`3IBR_28.out` cols 6-7 | 可作为 GSC dq 电流候选 | 需 GUI 确认 dq 正方向 | pu | 高 |
| GSC 限流/指令 | `Id_ord_pu`, `Iq_ord_pu`, `IdrefMax`, `IqrefMax` | `Grid_side_Controls` | 同上 | PGB / limiter / PI | `3IBR.inf:279,281`; `Grid_side_Controls.f:589-653,798-808` | `Id/Iq_ord_pu` 已输出 | 可作为限流响应候选 | 阈值 `IdrefMax/IqrefMax` 未独立输出；GUI 确认是否需要 | pu | 中 |
| Type-3 PLL 频率 | `Freq_PLL` | `Rotor_side_Controls` | `Type3_WTG_Avg -> DFIG_Converters_Avg -> Rotor_side_Controls` | PGB / PLL | `3IBR.inf:304`; `Rotor_side_Controls.f:713-718,1013-1016`; `Type3WTG_Lib.pslx:14296,17238` | 是，`3IBR_31.out` col 5 | 可与 `SPD30` 区分使用 | 需 GUI 确认单位是 pu 频率还是 Hz-like PLL output | 未标注，按内部 PLL output 候选 | 高 |
| 机械转速 | `Wpu` | `WindTurbine_MechModel` | `Type3_WTG_Avg -> WindTurbine_MechModel` | PGB / mechanical model | `3IBR.inf:254`; `WindTurbine_MechModel.f:14,51,281,520-522`; `3IBR.map:651` | 是，`3IBR_26.out` col 5 | 可解释故障中机械侧转速 | GUI 确认单位标签误写为 kV 的显示问题 | pu，正转速 | 高 |
| 机械/风功率 | `Pwind_pu`, `P_aero`, `TM`, `TE` | `WindTurbine_MechModel` / `Type3_WTG_Avg` | Type-3 外层与机械模型 | PGB | `3IBR.inf:227,229,230,249,250`; `WindTurbine_MechModel.f:474-484,520-522`; `Type3_WTG_Avg.f:543-557` | 是 | 可解释故障后机械-电磁功率恢复 | 需 GUI 确认比例和单位 | pu/未标注 | 中 |
| Type-3 内部 P/Q | `Pg_pu`, `Qg_pu` | `Type3_WTG_Avg` / `Rotor_side_Controls` | Type-3 外层与 RSC 控制 | PGB | `3IBR.inf:232-237,286,292`; `Rotor_side_Controls.f:368-374,540-542` | 是，但重复 | 可辅助对比 POC P/Q | 必须 GUI 确认使用哪个 `Pg_pu/Qg_pu` | pu，方向待确认 | 中 |
| 内部 Dblk 状态 | `Dblk_VdcCtrl`, `Dblk_Rotor` | `Type3_WTG_Avg` | Type-3 外层 | PGB / internal logic | `3IBR.inf:234-235`; `Type3_WTG_Avg.f:63-65,587-589`; `3IBR.map:631-632` | 是，`3IBR_24.out` cols 5-6 | 可解释内部闭锁候选 | 需 GUI 确认逻辑方向和与外部 `DFIG_DBLK_CMD` 的关系 | logic | 中 |

## 三、Crowbar 与限流机理审计

### 已确认事实

1. 当前官方 Type-3 平均值模型包含 Crowbar。证据包括：`Type3WTG_Lib.pslx:3568` 实例化 `Type3WTG_Lib:Crowbar_prot`，`Type3WTG_Lib.pslx:10511` 定义 `Crowbar_prot`，当前生成代码 `DFIG_Converters_Avg.f:538-540` 调用 `Crowbar_protDyn`，并且 `Crowbar_prot.f:7,14-15` 明确生成了 `Crowbar_prot` 子程序。
2. Crowbar 触发输入可静态确认包括 DC-link 电压 `Ecap`、转子电流 `Irotor`、`Vdc_crowbar_on`、`Time_crowbar`、`Ir_limit`、`Rcrow` 和 `Lcrow`。证据：`Crowbar_prot.f:14-15,52-54`；`Type3WTG_Lib.pslx:10530-10550`。
3. Crowbar 逻辑中存在转子电流阈值比较与 DC-link 电压阈值比较。证据：`Crowbar_prot.f:184-189` 将最大电流候选与 `Ir_limit` 比较；`Crowbar_prot.f:202` 将 `Ecap` 与 `Vdc_crowbar_on` 比较。
4. Crowbar 逻辑中存在 flip-flop、monostable 和 timed transition。证据：`Crowbar_prot.f:226-242,264-284`；可输出候选包括 `Iovercur`、`Reset`、`S1`、`Mono_out`、`V-Ecap`、`Ecap`、`Imagn`，见 `3IBR.inf:321-327`。
5. DC chopper 存在，采用 `Ecap` 与 `Vdc_chop_on/off` 的滞环逻辑，输出 `BRK_CHOP`。证据：`Chopper.f:141-148`；`Type3WTG_Lib.pslx:10117-10123,10263`。
6. RSC 控制存在电压跌落检测、PLL、dq 电流、限幅、anti-windup 和限流量。证据：`Rotor_side_Controls.f:507-520,713-718,809-818,897-906,995-1067`。
7. GSC 控制存在 PLL、DC-link 控制、dq 电流、指令限幅和硬限幅。证据：`Grid_side_Controls.f:516-519,561-588,613-653,713-820`。

### 静态推断

1. `Crowbar current:1..3` 是比 `DFIG_IFLT_A/B/C_KA` 更接近 Crowbar 动作的内部电流证据，因为它来自 Crowbar 子模块支路电流 `Icrowbar`，而故障电流来自外部三相故障元件。
2. 若故障期间 `DFIG_BRK_STATE` 保持闭合、`BRK ord` 未跳闸、`VIBR1_2` 跌落后恢复、`PIBR1_2` 恢复到约 199-200 MW，可证明外部并网路径保持；若同时 `Freq_PLL`、`Edc_pu/Ecap_Det`、`I_RS/Iconv`、`Dblk_Rotor/Dblk_VdcCtrl` 有合理响应，则能更完整解释 LVRT 内部行为。
3. `SPD30` 是系统侧频率候选，不应替代 `Rotor_side_Controls:Freq_PLL`。
4. 外部 `DFIG_DBLK_CMD` 只证明给 Type-3 的 enable/disable 命令，没有证明内部 RSC/GSC 实际闭锁状态。

### 待 GUI 确认事项

1. `Crowbar_prot` 中 `S1`、`Mono_out`、`Reset` 哪一个最适合作为正式的 `DFIG_CROWBAR_STATE`，以及 1/0 的方向。
2. `Ecap_Det` 与 `Edc_pu` 的取样位置是否分别对应 DC-link kV 与 pu 电压，二者基准是否与 `Vdc_base` 一致。
3. `I_RS:1..3`、`Iconv:1..3`、`Irotor:1..3` 的相序和正方向。
4. 重复的 `Pg_pu/Qg_pu/Iqr_pu` 中哪一组应作为正式解释曲线。

## 四、推荐的最小 LVRT 解释通道集

这些通道优先使用当前已在 `3IBR.inf` 中存在的内部 PGB；后续 GUI 阶段建议只做“确认取样点/必要时添加清晰命名的镜像通道”，不要改控制逻辑。

| 优先级 | 推荐显示名 | 原始信号 | 应取样位置 | 是否从现有线上分支 | 是否可避免修改 `Type3WTG_Lib` 内部 | 需要用户 GUI 确认 |
|---:|---|---|---|---|---|---|
| 1 | `DFIG_VDC_KV` | `Ecap_Det` | `DFIG_Converters_Avg` 的 DC-link 电压显示/输出 | 已有 PGB，可先解析；若重命名则分支 | 解析现有 PGB 可避免；重命名需要进入定义 | 确认 `Ecap_Det` 单位为 kV |
| 2 | `DFIG_CROWBAR_STATE` | `S1` 或 `Mono_out` | `Crowbar_prot` flip-flop/monostable 输出 | 已有 PGB，但语义需确认 | 可先解析现有 PGB | 确认哪一个量代表实际 Crowbar 投入 |
| 3 | `DFIG_CROWBAR_I_KA` | `Crowbar current:1..3` | `Crowbar_prot` 支路电流输出 | 已有 PGB | 可避免 | 确认单位、相序和符号 |
| 4 | `DFIG_RSC_IABC_KA` | `I_RS:1..3` | `DFIG_Converters_Avg` rotor-side converter 电流 | 已有 PGB | 可避免 | 确认 RSC 电流物理方向 |
| 5 | `DFIG_GSC_IABC_KA` | `Iconv:1..3` | `DFIG_Converters_Avg` grid-side converter 电流 | 已有 PGB | 可避免 | 确认 GSC 电流物理方向 |
| 6 | `DFIG_PLL_FREQ_INTERNAL` | `Freq_PLL` | `Rotor_side_Controls` PLL 输出 | 已有 PGB | 可避免 | 确认输出单位/尺度 |
| 7 | `DFIG_WPU` | `Wpu` | `WindTurbine_MechModel` 机械转速 | 已有 PGB | 可避免 | 确认显示单位标签误写为 kV 不影响数值 |
| 8 | `DFIG_INTERNAL_DBLK` | `Dblk_VdcCtrl`, `Dblk_Rotor` | `Type3_WTG_Avg` 内部闭锁逻辑输出 | 已有 PGB | 可避免 | 确认 1/0 方向和对应 RSC/GSC 范围 |

## 五、明确禁止事项

1. 不得把内部变量名当作已验证输出；必须以 `3IBR.inf`、`.map`、生成代码和 GUI 取样点共同确认。
2. 不得把 `SPD30` 当作 Type-3 PLL；应使用 `Rotor_side_Controls:Freq_PLL` 解释 Type-3 内部同步。
3. 不得把外部 `DFIG_DBLK_CMD` 与内部 `Dblk_VdcCtrl`、`Dblk_Rotor` 或 RSC/GSC 实际闭锁状态混为一谈。
4. 不得将 `DFIG_IFLT_A/B/C_KA` 外部故障电流当作转子电流、RSC 电流、GSC 电流或 Crowbar 电流。
5. 不得在没有 GUI 确认 `S1/Mono_out/Reset` 逻辑方向前宣称 Crowbar 已动作。
6. 不得为了解释深故障而修改 Type-3 内部控制器、Crowbar 参数、Dblk/Vwind 支架、保护、故障或主电路。
7. 不得同时启用风机脱网、过载保护、UFLS/UVLS、线路跳闸、MATLAB 联动或连锁故障逻辑来解释首次受控 LVRT。

## 结论

静态材料足以确认当前官方 Type-3 平均值模型包含 Crowbar、DC chopper、RSC/GSC 限流与 PLL/机械侧候选信号。当前 `3IBR.inf` 已经把大量 Type-3 内部 PGB 纳入输出索引，因此下一阶段可以优先通过本地脚本解析这些已存在通道，而不是立即进 GUI 新增元件。进入正式论文复现实验前，仍需要用户在 PSCAD GUI 中确认 Crowbar 状态量、内部 DC-link 电压量、RSC/GSC 电流方向和重复 P/Q/Iq 候选的具体取样点。
