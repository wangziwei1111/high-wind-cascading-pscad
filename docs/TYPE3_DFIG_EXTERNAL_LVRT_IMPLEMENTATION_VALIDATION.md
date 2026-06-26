# Type-3 DFIG 外部 LVRT 实施与验证安全回退记录

## 本轮范围

本轮目标原本是通过 PSCAD GUI 完整实现外部 LVRT 状态机、接入 `BRK_DFIG` 并完成多场景验证。实际执行中，已完成前置安全检查、Computer Use 连接 PSCAD、当前 P3 支架定位与只读对象核查；但没有继续进行断路器命令线改造。

最终状态按任务中的安全回退规则记录为：

```text
execution_status = monitoring_only_safe_fallback
```

## Computer Use 使用情况

已使用 Computer Use 完成：

- 识别并连接 `PSCAD 4.6.2 (64-bit) Professional` 窗口；
- 捕获当前 P3 页面；
- 确认可见 LVRT 监测支架区域；
- 确认当前 Build Messages 显示 `0 Errors / 44 Warnings / 119 Messages`；
- 辅助核查 `BRK_DFIG` 周边命令线与当前 `LOWV / IMMTRIP / CLEAR / TIMER_S` 支架。

没有通过 Computer Use 执行：

- 新增完整 `t_allow` 计算；
- 新增 `Vs_min_latched` 锁存；
- 新增 `trip_latch`；
- 修改或断开 `BRK_DFIG` 命令线；
- Build 或 Run。

## PSCAD 工程保护

任务开始前已执行：

```text
git pull --ff-only
initial active 3IBR.pscx SHA-256 =
9432E1DC41B1C0979C2B2A4506D5269420A776247880C4036646AEA1A4912319
```

本地回滚备份：

```text
C:\pscad_work\backups\type3_lvrt_full_impl_20260626_191254\3IBR.pscx
```

备份哈希与活动工程一致：

```text
9432E1DC41B1C0979C2B2A4506D5269420A776247880C4036646AEA1A4912319
```

本轮没有保存新的 PSCAD GUI 改动，因此最终活动工程哈希仍为同一值。

## 当前已存在的外部 LVRT 监测支架

当前 P3 页面中已存在以下监测级支架：

| 信号 | 当前来源 | 语义 | 输出通道 |
| --- | --- | --- | --- |
| `DFIG_LVRT_LOWV` | `VIBR1_2` 经 0.90 阈值比较器 | `VIBR1_2 < 0.90 pu` 时为 1 | 已有 |
| `DFIG_LVRT_IMMTRIP` | `VIBR1_2` 经 0.20 阈值比较器 | `VIBR1_2` 跌入立即跳闸区域时为 1 | 已有 |
| `DFIG_LVRT_CLEAR` | `DFIG_LVRT_LOWV` 经 0.5 阈值反向比较器 | 低压事件不活跃时为 1 | 无正式输出要求 |
| `DFIG_LVRT_TIMER_S` | `DFIG_LVRT_LOWV` 输入、`DFIG_LVRT_CLEAR` 复位的积分器 | 连续低电压事件计时，单位 s | 已有 |

当前支架仍然是监测级逻辑，没有接入 `BRK_DFIG`。

## 未实施完整状态机的原因

完整实现要求在无人值守 GUI 操作中完成以下高风险改动：

- 插入 `Vs_min_latched` 事件级最小电压锁存；
- 构造 `t_allow = 0.625 + ((Vs_min_latched - 0.20) / 0.70) * 1.375` 并限幅至 `[0.625, 2.0] s`；
- 生成 `duration_exceeded`、`trip_request`、`trip_latch`；
- 将 `DFIG_LVRT_CLEAR` 从 `NOT LOWV` 改为 `NOT LOWV AND NOT TRIP_LATCH`；
- 追踪并安全截断现有 `BRK_DFIG` 命令线；
- 插入 `DFIG_LVRT_FINAL_BRK_CMD = max(DFIG_LVRT_EXISTING_BRK_CMD, DFIG_LVRT_TRIP_LATCH)`；
- 确保没有悬空端口、重复驱动或错误断路器命令。

当前 PSCAD GUI 画布编辑只能依赖窗口坐标、组件拖放和线段捕捉。对于 `BRK_DFIG` 命令线，若在无人值守情况下直接断线或插入组合器，存在以下不可接受风险：

- 误切断已有断路器命令源；
- 将 LVRT 逻辑接到状态输出而非命令输入；
- 生成重复驱动或隐性悬空信号；
- 让 `BRK_DFIG` 在无故障或 0.75 s 工况中误开断；
- 留下 Build=0 但逻辑语义错误的模型。

因此本轮没有继续实施断路器接入，也没有把 `trip_latch` 出现等同于实际断路器开断。

## Build 状态

Computer Use 侦察时 PSCAD Build Messages 显示：

```text
0 Errors
44 Warnings
119 Messages
```

该状态来自用户此前完成的支架 Build。Codex 本轮没有重新 Build/Run。

## 验证状态

本轮没有新增完整状态机，因此没有执行以下验收：

- 5 s 无故障基准；
- 0.10 ohm / 0.75 s / 8 s；
- 0.10 ohm / 1.00 s / 8 s；
- 0.10 ohm / 1.25 s / 8 s；
- 0.01 ohm / 0.15 s / 5 s；
- `BRK_DFIG` 实际开断验证。

这些场景仍应在后续人工确认安全插入点后执行。

## 最终快照

保留旧快照：

```text
external/pscad_snapshot_20260626_lvrt_scaffold/
```

新增安全回退快照：

```text
external/pscad_snapshot_20260626_lvrt_monitoring_fallback/pnnl_39_3ibr_pscad46_strip5_PSCAD/3IBR.pscx
```

快照 SHA-256：

```text
9432E1DC41B1C0979C2B2A4506D5269420A776247880C4036646AEA1A4912319
```

## 后续建议

下一阶段不应直接接入 `BRK_DFIG`。建议先由用户在 GUI 中确认并截图以下三个对象：

1. `BRK_DFIG` 命令输入端的唯一驱动源；
2. 可安全插入组合器的位置；
3. 插入组合器后 `DFIG_LVRT_EXISTING_BRK_CMD` 与 `DFIG_LVRT_FINAL_BRK_CMD` 的独立监测点。

只有这三项确认后，才应继续完整状态机和断路器接入。
