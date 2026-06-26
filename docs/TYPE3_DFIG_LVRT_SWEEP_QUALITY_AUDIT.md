# Type-3 DFIG 故障电阻扫描 warning 只读审计

审计时间：2026-06-26

## 1. 审计范围

本轮只审计 Type-3 DFIG 5 s 故障电阻扫描中出现的 warning。未使用 Computer Use，未打开或操作 PSCAD GUI，未 Build，未 Run，未修改 `.pscx/.pslx/XML`、故障参数、输出通道、控制器、主电路，也未修改既有扫描 Markdown、JSON 或 CSV 中的仿真统计。

本轮读取的主要材料包括：

- `docs/TYPE3_DFIG_LVRT_FAULT_RESISTANCE_SWEEP.md`
- `data/reference/type3_dfig_lvrt_fault_resistance_sweep.json`
- `data/reference/type3_dfig_lvrt_fault_resistance_sweep_summary.csv`
- `docs/TYPE3_DFIG_DEEP_FAULT_INTERNAL_RESPONSE.md`
- `data/reference/type3_dfig_deep_fault_internal_response.json`
- `docs/TYPE3_DFIG_LVRT_GUI_SEMANTIC_CONFIRMATION.md`
- `data/reference/type3_dfig_lvrt_gui_semantic_confirmation.json`
- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx`
- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f`
- `C:\Program Files (x86)\PSCAD46\master.pslx`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\...\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\...\3IBR_*.out`
- 用户此前导出的 Build Messages 文本：`C:\Users\24186\.codex\attachments\60155a35-1396-4e6f-88aa-504c3fe427db\pasted-text.txt`

## 2. Warning 原文及证据来源

在用户此前导出的 Build Messages 文本中，warning 原文为：

| Id | Component | Namespace | Description |
|---:|---|---|---|
| 113665858 | `master:xfmr-3p2w` | `3IBR` | `Suspicious floating terminal at node 'NT_17'.` |
| 113665858 | `master:xfmr-3p2w` | `3IBR` | `Suspicious floating terminal at node 'NT_18'.` |

证据路径：

- `C:\Users\24186\.codex\attachments\60155a35-1396-4e6f-88aa-504c3fe427db\pasted-text.txt:7`
- `C:\Users\24186\.codex\attachments\60155a35-1396-4e6f-88aa-504c3fe427db\pasted-text.txt:8`

同样的两条 warning 也出现在其他已粘贴的 Build Messages 文本中，例如：

- `C:\Users\24186\.codex\attachments\a0d01c06-e732-4c50-8546-a2cf85493f93\pasted-text.txt:7-8`
- `C:\Users\24186\.codex\attachments\a497fe3e-67e2-43cd-b020-80be379134b0\pasted-text.txt:7-8`
- `C:\Users\24186\.codex\attachments\bcd9187e-6f58-4730-8ca5-e89c6a2696a1\pasted-text.txt:7-8`

本地生成目录中的 `.inf/.out/.log/.map/.mak/.f` 文件没有保存 PSCAD Build Messages 面板的完整 warning 原文，因此原文证据主要来自用户此前导出的 Build Messages 文本。

## 3. `XFMR_DFIG_22_33` 与 `NT_17/NT_18` 静态定位

`3IBR.pscx` 中，ID `113665858` 对应当前 Type-3 支路中的 22/33 kV 两绕组变压器：

```xml
<User classid="UserCmp" defn="master:xfmr-3p2w" id="113665858" x="990" y="990" ...>
  <param name="Name" value="XFMR_DFIG_22_33" />
  <param name="Tmva" value="250.0 [MVA]" />
  <param name="f" value="60.0 [Hz]" />
  <param name="YD1" value="0" />
  <param name="YD2" value="0" />
  <param name="Xl" value="0.1 [pu]" />
  <param name="Ideal" value="1" />
  <param name="NLL" value="0.0001 [pu]" />
  <param name="CuL" value="0.005 [pu]" />
  <param name="Tap" value="0" />
  <param name="V1" value="22 [kV]" />
  <param name="V2" value="33 [kV]" />
  <param name="Enab" value="0" />
  <param name="Sat" value="0" />
</User>
```

证据路径：

- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx:25632`
- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.pscx:25634-25655`

当前仓库静态拓扑审计也记录了同一对象：

- `analysis/snapshot_audit/PSCAD_STATIC_TOPOLOGY_AUDIT.md:122`

生成代码中，`P3.f` 将同一组件标记为：

```fortran
! 1:[xfmr-3p2w] 3 Phase 2 Winding Transformer 'XFMR_DFIG_22_33'
CALL COMPONENT_ID(ICALL_NO,113665858)
CALL E_TF2W_CFG((IXFMR + 31),1,...)
CALL E_TF2W_CFG((IXFMR + 32),1,...)
CALL E_TF2W_CFG((IXFMR + 33),1,...)
...
CALL E_BRANCH_CFG((IBRCH(9)+23),...)
...
CALL TSAT2_CFG(2, (IBRCH(9)+29), (IBRCH(9)+30), ...)
```

证据路径：

- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f:2268-2274`
- `C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR.gf46\P3.f:3685-3715`

PSCAD 自带 `master.pslx` 中，`master:xfmr-3p2w` 是标准 `3 Phase 2 Winding Transformer` 组件；该组件参数页包含两绕组接线、理想变压器模型、空载损耗、饱和、磁化支路等参数。组件定义生成代码中会配置三相变压器本体、空载/励磁支路以及饱和例程：

- `C:\Program Files (x86)\PSCAD46\master.pslx:76558-76680`
- `C:\Program Files (x86)\PSCAD46\master.pslx:77335-77420`

### 端子角色判断

本轮没有打开 PSCAD GUI，也没有直接读取到 `NT_17`、`NT_18` 在图形端口上的名称。基于只读静态材料，目前能确认的是：

- `NT_17`、`NT_18` 的 warning 属于 `XFMR_DFIG_22_33` 这个 `master:xfmr-3p2w` 标准变压器实例；
- 生成代码显示该实例除三相变压器主配置外，还配置了空载/励磁相关分支与饱和例程；
- warning 文本为 `Suspicious floating terminal`，不是 unresolved definition、missing signal、compile error 或运行中断类错误；
- 目前没有文件证据表明 `NT_17`、`NT_18` 是 Type-3 控制器、故障控制、`BRK_DFIG` 控制、Dblk/Vwind 支架或 P/Q/V 输出通道的一部分。

因此，`NT_17`、`NT_18` 的端子角色在本轮只能判为：

```text
无法从只读文本完全确认；较可能是 XFMR_DFIG_22_33 标准变压器模型的未接辅助/励磁/饱和相关内部端子或中性/接地相关节点，但仍需后续 GUI 端口页确认。
```

本轮不把它写成已确认的未用中性点、测量端或接地端。

## 4. 各扫描场景运行完整性证据

故障电阻扫描 JSON/CSV 记录了 5 个场景。所有场景均为 5 s 总仿真、故障窗口 2.0-2.15 s、`Fault OFF Resistance=1.0E6 ohm`、风速 11 m/s。只读复核显示，每个场景的 `.out` 文件可严格解析为浮点数，未发现 NaN、Inf、输出截断或末尾时间异常。

| 场景 | Fault ON Resistance | Build errors | Build warnings | EMTDC completed | `.out` 末尾时间 | `.out` 数值检查 |
|---|---:|---:|---:|---|---:|---|
| `r_0p01_restored` | 0.01 ohm | 0 | 2 | true | 4.9966 s | 35 个 `3IBR_*.out` 可解析，无 NaN/Inf |
| `r_0p03` | 0.03 ohm | 0 | 0 | true | 4.9966 s | 35 个 `3IBR_*.out` 可解析，无 NaN/Inf |
| `r_0p10` | 0.10 ohm | 0 | 2 | true | 4.9966 s | 35 个 `3IBR_*.out` 可解析，无 NaN/Inf |
| `r_0p30` | 0.30 ohm | 0 | 2 | true | 4.9966 s | 35 个 `3IBR_*.out` 可解析，无 NaN/Inf |
| `r_1p00` | 1.00 ohm | 0 | 2 | true | 4.9966 s | 35 个 `3IBR_*.out` 可解析，无 NaN/Inf |

证据来源：

- `data/reference/type3_dfig_lvrt_fault_resistance_sweep.json`
- `data/reference/type3_dfig_lvrt_fault_resistance_sweep_summary.csv`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\r_0p01_restored\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\r_0p03\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\r_0p10\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\r_0p30\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\r_1p00\3IBR.inf`
- `C:\pscad_work\type3_dfig_fault_sweep_tmp\...\3IBR_*.out`

只读数值检查结果：

```text
r_0p01_restored: 35 out files, 42175 rows, bad=0, end_time=4.9966 s
r_0p03:          35 out files, 42175 rows, bad=0, end_time=4.9966 s
r_0p10:          35 out files, 42175 rows, bad=0, end_time=4.9966 s
r_0p30:          35 out files, 42175 rows, bad=0, end_time=4.9966 s
r_1p00:          35 out files, 42175 rows, bad=0, end_time=4.9966 s
```

未发现以下风险证据：

- 编译错误；
- unresolved definition；
- missing signal；
- NaN 或 Inf；
- 输出文件截断；
- EMTDC run aborted；
- 时间步崩溃；
- 明显数值发散导致结果不可解析。

## 5. Warning 分类与理由

最终分类：

```text
noncritical_but_unresolved
```

理由：

1. warning 原文可确认是 `XFMR_DFIG_22_33` 的 `Suspicious floating terminal` 类型提示，关联对象 ID 为 `113665858`，组件为 PSCAD 标准 `master:xfmr-3p2w`。
2. 已有扫描场景均记录 `Build errors=0`，`EMTDC completed=true`，`.out` 末尾时间接近 5 s。
3. 当前扫描 `.out` 文件可被解析脚本和本轮只读检查正常读取，未发现 NaN、Inf、输出截断或运行中止。
4. 静态材料没有证据表明 `NT_17/NT_18` 参与 Type-3 DFIG 主电路功率传输、故障控制、`BRK_DFIG` 控制、Dblk/Vwind 支架或输出通道。
5. 但只读文本无法精确确认 `NT_17/NT_18` 是未用中性点、辅助端口、测量端还是接地相关端，因此不能归类为 `known_benign`。

必须保留的结论：

```text
当前证据显示该 warning 未导致 Build/Run 失败或已识别的输出损坏，
但 XFMR_DFIG_22_33 的 NT_17/NT_18 端口物理含义仍应在后续正式模型整理阶段确认。
```

## 6. 对故障电阻扫描结果可信度的影响范围

本轮 warning 审计支持继续使用已有故障电阻扫描结果进行趋势性分析，例如：

- `Fault ON Resistance` 从 0.01 ohm 增加到 1.00 ohm 时，`VIBR1_2` 暂降显著变浅；
- `Edc_pu` 和 `Ecap_Det` 峰值随故障变浅而下降；
- `BRK_CHOP` 在 0.01、0.03、0.10 ohm 场景有 active-high command/state 响应，在 0.30、1.00 ohm 场景未出现；
- `S1 / DFIG_CROWBAR_STATE` 在所有扫描场景未投入。

但该 warning 仍限制以下结论：

- 不能把 `XFMR_DFIG_22_33` 的端子配置写成正式模型已完全整理完成；
- 不能声称 `NT_17/NT_18` 对所有未来工况完全无影响；
- 若后续要做正式论文级模型说明或长期/多事件连锁仿真，应在 PSCAD GUI 中确认 `NT_17/NT_18` 的端口名称、端口类型和连接状态。

## 7. 已确认事实、工程判断、待确认事项

### 已确认事实

- `XFMR_DFIG_22_33` 是当前 Type-3 支路的 `master:xfmr-3p2w` 22/33 kV 两绕组变压器，ID 为 `113665858`。
- warning 原文为 `Suspicious floating terminal at node 'NT_17'.` 和 `Suspicious floating terminal at node 'NT_18'.`。
- 5 个故障电阻扫描场景均为 `0 Build errors`、`EMTDC completed=true`。
- 5 个故障电阻扫描场景的 `.out` 文件末尾时间均为 `4.9966 s`，本轮只读检查未发现 NaN、Inf 或输出截断。

### 工程判断

- 该 warning 当前应按 `noncritical_but_unresolved` 管理，而不是按 `known_benign` 关闭。
- 该 warning 不阻止使用已有故障电阻扫描结果进入论文 LVRT 判据审计或持续时间扫描的准备阶段。
- 后续持续时间扫描仍应保留 warning 监控；如果 warning 数量、对象或文本发生变化，应重新审计。

### 待确认事项

- 在 PSCAD GUI 的 `XFMR_DFIG_22_33` 端口/详情视图中确认 `NT_17`、`NT_18` 对应的实际端口名称。
- 确认 `NT_17`、`NT_18` 是否为未用中性点、辅助端口、测量端、接地相关端、励磁/饱和内部节点，或其他端口。
- 若后续整理正式模型，应决定是否需要调整变压器显示详情、接地/中性点配置或空载/饱和相关设置，以消除该 warning。

## 8. 后续建议

允许进入下一步论文 LVRT 判据审计或持续时间扫描，但建议采用以下保护性规则：

1. 后续 Build/Run 中若 warning 仍仅为同一对象 `113665858` 的 `NT_17/NT_18` 浮空端子提示，且 `Build errors=0`、EMTDC 完成、输出完整，则可继续按 `noncritical_but_unresolved` 记录。
2. 若出现新的 floating terminal 对象、新的 unresolved/missing definition、NaN/Inf、输出截断、仿真中止或数值发散，应立即停止后续扫描并重新审计。
3. 在正式模型整理阶段，应由用户在 PSCAD GUI 中查看 `XFMR_DFIG_22_33` 的端口/详情页，确认 `NT_17/NT_18` 的物理含义。
