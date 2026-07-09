# STAGE8 single GUI repair and Build sheet

只打开 trial 工程：

`C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.pscx`

不要打开或保存 main 工程 `3IBR.pscx`。

本次只修 Output Channel 可观测性，不改 relay 参数、不改 timer、不改 breaker、不改线路。

## 1. 打开 P3 页面

在页面树进入 `Main -> P1 -> P3`，找到 Stage 7 放置的 `PAPER_OVL1` 输出通道区。

## 2. 只修改一个 Output Channel 标题

找到位于 `x≈2916, y≈1980` 的 Output Channel。

后台组件 ID：

`518433536`

它当前标题是：

`PAPER_OVL1_RELAY_ENABLE`

它左侧输入源已经是：

`PAPER_OVL1_ABOVE_THRESHOLD`

只把这个 Output Channel 的 `Title / Name` 改成：

`PAPER_OVL1_ABOVE_THRESHOLD`

不要改它的输入线。

参数保持：

- `Use Signal Name as Title? = No`
- `Display Title on Icon? = Yes`
- `Scale Factor = 1.0`
- `Multiple Run Save = Last Run Only`
- `Is Input in Polar Form? = No`

## 3. 保留真正的 relay-enable 通道

不要修改位于 `x≈3168, y≈1980` 的另一个 Output Channel。

后台组件 ID：

`865554842`

它必须保持：

- Title：`PAPER_OVL1_RELAY_ENABLE`
- 输入源：`PAPER_OVL1_RELAY_ENABLE`

## 4. 不允许修改的内容

不要改：

- `PAPER_OVL1_RELAY` 模块内部
- `E_28_29_1`
- `BRK_PAPER_OVL1_TRIAL`
- `PAPER_OVL1_BRK_CMD`
- `7.872883989661206`
- `1.1`
- `5.0 s`
- N29 故障
- DFIG / IBR2 / IBR3 / collector / chronology
- 任何已有 TLine P/Q/I Output Channel

## 5. 保存并 Build 一次

保存 trial。

Build 一次。

如果 Build Errors = 0，停止，不要 Run。

完成后只回复：

`阶段八A GUI 修复与 Build 完成`

如果 Build 有错误，停止，不要 Run，回复：

`阶段八A Build 失败：<精确错误文本>`
