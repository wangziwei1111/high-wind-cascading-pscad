# Type-3 Library Import Procedure

```text
前置条件：
1. 关闭所有正在运行的 PSCAD 仿真。
2. Type3_Ave_Nov_2018 Case 已能独立运行。
3. Type3WTG_Lib 是 Library Project，不是 Case Project。
4. Type3_Ave_Nov_2018 和 Type3WTG_Lib 同时加载在同一个 PSCAD Workspace。
5. 不打开、不编辑 3IBR 原始基线；如需验证，只使用 3IBR_DFIG1_TRIAL。
6. 临时导出的 .psdx 放在 Git 仓库外，例如：
   C:\pscad_work\type3_wtg_v46_trial\Type3_WTG_Avg_with_dependents.psdx

步骤 1：
当前应位于哪个工程：
  Type3_Ave_Nov_2018 Case 工程。

点击哪个位置：
  左侧/工作区 Primary Window -> Projects -> Type3_Ave_Nov_2018 -> Definitions。

应看到什么：
  Definitions 列表中有 Type3_WTG_Avg 或与 “Type 3 Average” 对应的模块定义。

不应做什么：
  不要在 Main 页面直接复制外层模块。
  不要点 Copy as Meta-File。

步骤 2：
当前应位于哪个工程：
  Type3_Ave_Nov_2018 的 Definitions 分支。

点击哪个菜单：
  右键 Type3_WTG_Avg -> Export with Dependents。

选择哪个文件：
  保存为：
  C:\pscad_work\type3_wtg_v46_trial\Type3_WTG_Avg_with_dependents.psdx

出现什么窗口：
  Save Definition As 或类似保存对话框。

应选什么：
  文件类型应为 PSCAD Definition File (*.psdx)。

不应选什么：
  不要选择 Export As... 作为最终方案，除非只是做单定义诊断。

验证：
  确认 .psdx 文件被创建。

失败处理：
  如果没有 Export with Dependents，停止，截图右键菜单和 Definitions 树。

步骤 3：
当前应位于哪个工程：
  Type3WTG_Lib Library 工程。

点击哪个菜单：
  Projects -> Type3WTG_Lib -> Definitions。
  右键 Definitions 分支 -> Import Definition(s)...

选择哪个文件：
  C:\pscad_work\type3_wtg_v46_trial\Type3_WTG_Avg_with_dependents.psdx

出现什么窗口：
  Open/import definition 对话框；如出现重名/覆盖/重命名提示，立即停止。

应选什么：
  选择刚导出的 .psdx。

不应选什么：
  不要导入 .pscx、.pslx、.lib、.gf46。

验证：
  Type3WTG_Lib 的 Definitions 分支应出现 Type3_WTG_Avg 及其依赖定义。

失败处理：
  若提示重复定义、缺失依赖或命名冲突，取消导入，截图提示窗口。

步骤 4：
当前应位于哪个工程：
  Type3WTG_Lib Library 工程。

点击哪个菜单：
  展开 Definitions，双击 Type3_WTG_Avg。

验证：
  能打开定义页面。
  能看到 AC_sys 三相接口。
  能看到参数 Dblk、freq、Vbase、UN、Rated_MW、Vwind、Machine_MVA。

不应做什么：
  不要编辑定义内容。
  不要保存对参数/图纸的任何修改。

步骤 5：
当前应位于哪个工程：
  Type3WTG_Lib Library 工程。

点击哪个菜单：
  File -> Save Project 或保存 Library。

验证：
  Type3WTG_Lib 保存后重新打开仍包含 Type3_WTG_Avg。

失败处理：
  如果保存失败，关闭 Library 不保存，保留 .psdx 和截图。

步骤 6：
当前应位于哪个工程：
  可选：空白 scratch Case 或 3IBR_DFIG1_TRIAL，但不要接线。

点击哪个菜单：
  确保 Type3WTG_Lib 已加载。
  在 Type3WTG_Lib -> Definitions 中右键 Type3_WTG_Avg -> Create Instance。
  在空白页或未接线临时区域右键 -> Paste。

验证：
  实例来源/引用应指向 Type3WTG_Lib:Type3_WTG_Avg。
  不应再出现 “definition resides in another case project”。

失败处理：
  如果仍引用 Type3_Ave_Nov_2018，停止，截图实例属性和 Reference 信息。
```

## Notes

Use `Switch Reference...` only after the library has a verified `Type3_WTG_Avg` definition. It is a relinking tool, not a substitute for importing definitions into the library.
