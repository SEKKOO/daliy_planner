from __future__ import annotations

import re
from html import escape


HELP_DOCS_CSS = """
    .help-overlay[hidden] { display: none !important; }
    .help-overlay {
      position: fixed;
      inset: 0;
      z-index: 72;
      padding: 24px 16px;
      background: rgba(9, 22, 40, 0.42);
      backdrop-filter: blur(10px);
      overflow-y: auto;
    }
    .help-dialog {
      width: min(980px, 100%);
      margin: 0 auto;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.2);
      background: var(
        --surface,
        var(--boot-region-background, linear-gradient(180deg, rgba(255,255,255,0.96), rgba(244,249,255,0.9)))
      );
      box-shadow: 0 24px 58px rgba(21, 52, 97, 0.18);
      overflow: hidden;
    }
    .help-dialog-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding: 24px 24px 18px;
      border-bottom: 1px solid var(--line-soft, rgba(49, 102, 173, 0.1));
    }
    .help-dialog-title {
      margin: 0;
      font-size: 22px;
      font-weight: 800;
      color: var(--text);
    }
    .help-dialog-subtitle {
      margin-top: 6px;
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.7;
    }
    .help-dialog-body {
      display: grid;
      gap: 16px;
      padding: 20px 24px 24px;
    }
    .help-dialog-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .help-meta-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(46,119,208,0.14);
      background: rgba(223,238,255,0.72);
      color: var(--accent-deep, var(--text));
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
    }
    .help-tab-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .help-tab {
      min-height: 42px;
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(46,119,208,0.12);
      background: rgba(255,255,255,0.74);
      color: var(--accent-deep, var(--text));
      font-size: 13px;
      font-weight: 700;
      line-height: 1.3;
      cursor: pointer;
      box-shadow: none;
      backdrop-filter: blur(10px);
      transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, color 0.18s ease;
    }
    .help-tab:hover {
      transform: translateY(-1px);
      box-shadow: 0 10px 18px rgba(42,111,214,0.12);
    }
    .help-tab.is-active {
      border-color: transparent;
      background: linear-gradient(135deg, var(--primary, #2e77d0), var(--primary-deep, #1e58a0));
      color: #fff;
      box-shadow: 0 14px 26px rgba(42,111,214,0.2);
    }
    body[data-theme="dark"] .help-tab.is-active {
      color: #081a32;
    }
    .help-sections {
      display: grid;
    }
    .help-section[hidden] { display: none !important; }
    .help-markdown {
      padding: 24px 28px;
      border-radius: 24px;
      border: 1px solid var(--line-soft, rgba(49, 102, 173, 0.1));
      background: rgba(var(--surface-soft-rgb, 244, 249, 255), 0.78);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.34);
      color: var(--text-soft);
      line-height: 1.85;
      font-size: 14px;
      overflow-wrap: anywhere;
    }
    .help-markdown > *:first-child { margin-top: 0; }
    .help-markdown > *:last-child { margin-bottom: 0; }
    .help-markdown h1,
    .help-markdown h2,
    .help-markdown h3 {
      margin: 1.25em 0 0.55em;
      color: var(--text);
      line-height: 1.35;
    }
    .help-markdown h1 {
      font-size: 28px;
      font-weight: 900;
      letter-spacing: -0.02em;
    }
    .help-markdown h2 {
      font-size: 20px;
      font-weight: 800;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--line-soft, rgba(49, 102, 173, 0.1));
    }
    .help-markdown h3 {
      font-size: 16px;
      font-weight: 800;
    }
    .help-markdown p {
      margin: 0.75em 0;
    }
    .help-markdown ul,
    .help-markdown ol {
      margin: 0.75em 0 1em;
      padding-left: 1.5em;
    }
    .help-markdown li {
      margin: 0.35em 0;
    }
    .help-markdown strong {
      color: var(--text);
      font-weight: 800;
    }
    .help-markdown code {
      padding: 2px 6px;
      border-radius: 8px;
      background: rgba(46, 119, 208, 0.08);
      color: var(--accent-deep, var(--text));
      font-size: 12px;
      font-family: "SFMono-Regular", "Menlo", "Consolas", monospace;
      word-break: break-all;
    }
    .help-markdown a {
      color: var(--primary, #2e77d0);
      text-decoration: none;
      border-bottom: 1px solid rgba(46, 119, 208, 0.22);
    }
    .help-markdown a:hover {
      border-bottom-color: currentColor;
    }
    body[data-theme="dark"] .help-overlay {
      background: rgba(4, 11, 22, 0.58);
    }
    body[data-theme="dark"] .help-meta-pill {
      border-color: rgba(159, 191, 236, 0.16);
      background: rgba(92, 146, 224, 0.18);
    }
    body[data-theme="dark"] .help-tab {
      border-color: rgba(159, 191, 236, 0.12);
      background: rgba(33, 49, 73, 0.72);
      color: var(--ink, #edf5ff);
    }
    body[data-theme="dark"] .help-markdown {
      background: rgba(27, 42, 64, 0.82);
    }
    body[data-theme="dark"] .help-markdown code {
      background: rgba(125, 183, 255, 0.14);
    }
    @media (max-width: 720px) {
      .help-overlay {
        padding: 12px;
      }
      .help-dialog-head,
      .help-dialog-body {
        padding: 18px 16px;
      }
      .help-dialog-head {
        display: grid;
      }
      .help-dialog-title {
        font-size: 19px;
      }
      .help-meta-pill,
      .help-tab {
        width: 100%;
        justify-content: center;
      }
      .help-markdown {
        padding: 18px 16px;
        font-size: 13px;
      }
      .help-markdown h1 {
        font-size: 24px;
      }
      .help-markdown h2 {
        font-size: 18px;
      }
    }
"""


USER_HELP_MARKDOWN = """
# 用户页面帮助文档

用户页面是你日常最常使用的工作台。你会在这里完成登录、每周安排、每天客户事项填写、月度导出、钉钉 MCP 配置、提示词配置，以及售后日报 / 周报发送。

## 1. 第一次使用前先准备什么

1. **确认账号来源**：你需要有可登录的本地账号，或者管理员已经给你的钉钉账号开通了扫码登录权限。
2. **确认页面权限**：如果你还要进入“日程管理”页面，请让管理员同时勾选你“在日程管理页展示”。
3. **确认钉钉使用目标**：如果你需要发送日报、发送周报、同步日程、按姓名自动查同事 `userId`，你还需要准备自己的钉钉 MCP。
4. **建议准备两个浏览器页签**：一个打开本系统，一个打开钉钉 AIHub / MCP 页面，方便边看边复制链接。

## 2. 怎么登录系统

1. 打开系统首页后，先看右上角按钮区。
2. 点击 **“登录”**。
3. 如果你使用本地账号，就输入管理员给你的账号和密码。
4. 如果管理员已经配置好钉钉扫码登录，登录弹窗里会出现二维码入口，你可以直接扫码。
5. 登录成功后，右上角通常会出现 **“退出”“修改密码”“提示词”“钉钉MCP”** 等按钮，说明当前用户身份已经加载成功。
6. **建议首次登录后立刻点“修改密码”**，先把默认密码换掉，再继续后面的配置。

## 3. 如何获取你自己的钉钉 MCP 链接

1. 打开钉钉 AIHub / MCP 页面，通常可以从 `https://aihub.dingtalk.com/` 进入，或者直接打开管理员发给你的 MCP 实例详情页。
2. **务必使用你自己的钉钉组织身份登录**。因为你后面能看到哪些模板、能查哪些人，跟当前登录的钉钉身份有关。
3. 按实际使用目标准备这些 MCP：
   - **日志发送 MCP**：用于读取模板、发送售后日报、发送周报。
   - **通讯录查询 MCP**：用于按姓名查询同事的钉钉 `userId`。
   - **日历 MCP**：用于读取钉钉日历、把本系统日程同步到钉钉，或把钉钉日程拉取到本系统。
4. 在对应实例详情中找到 **StreamableHttp URL**。
5. 它通常会长得像这样：`https://mcp-gw.dingtalk.com/server/......?key=......`
6. 把对应实例的链接分别复制出来备用，不要混填。

## 4. 怎么把 MCP 配到系统里

1. 回到本系统，点击右上角 **“钉钉MCP”**。
2. 把你刚才复制的地址分别填入：
   - **日志发送 MCP 地址**
   - **通讯录查询 MCP 地址**
   - **日历 MCP 地址**
3. 先点击 **“保存配置”**。
4. 如果要同步日程，先点击 **“读取日历”**，再选择要同步的钉钉日历和同步方向。
5. 日历同步方向有两种：
   - **双向同步**：本系统日程会推到钉钉，钉钉日程也会拉到本系统。
   - **仅本系统同步到钉钉**：只把本系统日程推到钉钉，不从钉钉拉取日程。
6. 如果要发送日报 / 周报，再点击 **“读取模板”**。
7. 系统会使用你填写的 **日志发送 MCP** 去读取当前账号可见的钉钉日志模板。
8. 读取完成后，你需要分别选择：
   - **日报模板**
   - **周报模板**
9. 选好之后，**再点击一次“保存配置”**。

### 重要提醒

- 如果你改了 **日志发送 MCP 地址**，原来已经选过的模板会被清空，你必须重新读取模板、重新选择。
- 如果 **通讯录查询 MCP 地址** 为空，系统就没法按姓名自动查接收人 `userId`。
- 如果 **日历 MCP 地址** 为空，系统就不会启用钉钉日历同步。
- 日历必须是你有 `owner` 或 `writer` 权限的日历，否则系统无法创建、修改或删除钉钉日程。
- 如果模板没有选好，系统会直接禁止发送日报 / 周报。

## 5. 钉钉日程同步和删除规则

### 同步怎么启动

1. 在右上角 **“钉钉MCP”** 中填写 **日历 MCP 地址**。
2. 点击 **“读取日历”**，选择要同步的日历。
3. 选择 **双向同步** 或 **仅本系统同步到钉钉**。
4. 点击 **“保存配置”** 后，系统会为当前用户启用一条日历同步会话。
5. 启用后，后台同步周期是 **3 分钟一次**；调度线程会每 30 秒检查一次是否有到期任务。
6. 你也可以点击 **“立即同步”**，系统会马上处理当前周的待同步任务，并在双向模式下拉取当前周的钉钉日程。

### 同步范围怎么理解

1. 同步按 **当前登录用户自己的日历 MCP** 执行，不会使用其他人的 MCP。
2. 本系统里的新增、编辑、删除会先进入同步队列，状态会显示为 **待同步** 或 **同步中**。
3. 后台自动轮询主要检查启用日之后、未来一段时间内的钉钉变化；历史本地安排不会自动补推。
4. 手动同步会处理当前页面所在周，并按钉钉 `eventId` 去重。
5. 已经被本地删除过的钉钉导入日程，系统会记住它的 `eventId`，以后不会再次导入同一个钉钉日程。

### 两类日程的区别

1. **本系统创建的日程**：来源是本地，保存后会同步到钉钉；同步成功后会显示 **已同步**。
2. **钉钉拉取来的日程**：来源是钉钉，系统会在本地生成一条日程，并显示钉钉同步状态。
3. 页面不会再用不同颜色表达来源；来源和状态会以小字显示，例如 **钉钉、同步状态：已同步**。

### 删除规则

1. **本系统创建并同步到钉钉的日程**：你在本系统删除后，系统会向钉钉发送删除请求；钉钉里对应日程也会被删除。
2. **本系统创建并同步到钉钉的日程**：如果钉钉端先删除或取消，本系统会把这条本地安排移除，避免继续显示已经不存在的本地排班。
3. **从钉钉拉取到本系统的日程**：你在本系统删除后，只删除本地显示，不会删除钉钉里的原始日程。
4. **从钉钉拉取到本系统的日程**：本地删除后，系统会记录原始钉钉 `eventId`，后续同步不会把同一条钉钉日程再拉回来。
5. **从钉钉拉取到本系统的日程**：如果钉钉端先删除或取消，本地不会直接删除，而是显示为 **钉钉已删除** 或 **钉钉已取消**，方便你知道变化来源。

### 状态怎么读

- **未配置**：当前用户没有启用日历 MCP。
- **本地**：本地有日程，但还没有建立钉钉映射。
- **待同步**：已进入同步队列，等待后台处理。
- **同步中**：后台正在调用钉钉日历接口。
- **已同步**：本地和钉钉已经建立映射并同步成功。
- **失败**：调用钉钉失败，需要检查 MCP 地址、日历权限或错误提示。
- **冲突**：本地和钉钉两边都发生过变化，需要人工确认。
- **钉钉已删除 / 钉钉已取消**：钉钉端已经进入终止状态，本地保留状态提示。
- **已删除**：本地删除已经处理完成。

### 什么情况下会出现冲突

1. 本地和钉钉同一条日程都被修改过，系统无法判断以哪边为准。
2. 钉钉端改了日期或时间段，系统不会自动覆盖本地排班时间，会标记为冲突。
3. 钉钉端只改标题、内容或地点，并且本地没有同时修改时，系统会尝试更新到本地。
4. 看到 **冲突** 后，建议先确认钉钉和本系统哪边才是正确内容，再手动调整或重新创建日程。

## 6. 怎么配置提示词

1. 点击右上角 **“提示词”**。
2. 你会看到当前系统支持的提示词类型，通常包括：
   - **售后日报生成**
   - **周报生成**
   - **交付进展分析**
   - **钉钉用户查询**
   - **钉钉日报发送**
   - **钉钉周报发送**
3. 修改提示词后，点击 **“保存提示词”**，只会影响你当前用户。
4. 如果你觉得改坏了，点击 **“恢复默认”**，然后再保存，就会回退到系统默认版本。

### 这些提示词分别影响什么

- **售后日报生成**：影响日报内容结构、措辞和总结方式。
- **周报生成**：影响周报的项目汇总口径和行文风格。
- **交付进展分析**：影响交付进展面板的分析方式。
- **钉钉用户查询**：影响按姓名查询钉钉 `userId` 的提示词逻辑。
- **钉钉日报发送 / 钉钉周报发送**：影响调用钉钉日志 MCP 发送动作时的执行指令。

## 7. 怎么填写每天的工作内容

1. 登录后先确认页面当前日期是否正确。
2. 页面顶部是 **每周工作安排**，按周维护上午、下午安排和其他待定事项。
3. 这部分通常会 **自动保存**，你改完后不用手动点保存按钮。
4. 页面中间的 **每日事项清单** 支持一日多行，适合把同一天的多个客户、多个项目拆开填写。
5. 填写完成后，请点击 **“保存当天列表”**。
6. 保存成功后，“本周记录”区域会同步展示你这一周已经保存过的记录。

## 8. 怎么发送售后日报

1. 先保证当天内容已经填写并点击了 **“保存当天列表”**。
2. 点击 **“发送售后日报”**。
3. 系统会根据你当前日期的数据生成日报草稿，并打开预览。
4. 预览阶段你可以继续微调内容。
5. 如果需要补接收人，系统会优先尝试通过你配置的 **通讯录查询 MCP** 按姓名查 `userId`。
6. 确认后再执行发送。

### 如果发送日报时失败，优先检查这些

1. 是否已经配置 **日志发送 MCP 地址**。
2. 是否已经选择 **日报模板**。
3. 接收人是否能通过你的通讯录查询 MCP 查到对应 `userId`。
4. 相关提示词是否被你改坏。

## 9. 怎么发送周报

1. 先确认本周数据已经基本完整。
2. 点击 **“发送周报”**。
3. 系统会按你当前周的数据生成周报预览。
4. 确认内容无误后再执行发送。
5. 如果系统提示你没有周报模板，说明你还没有在 **“钉钉MCP”** 里读取并保存周报模板。

## 10. 怎么查看月度汇总和导出 Excel

1. 页面右侧按月区域可以切换月份。
2. 这里会统计：
   - 当月日期数
   - 事项条数
   - 总工时
3. 如果你需要做归档、发给领导或做月度复盘，可以点击 **“导出 Excel”**。

## 11. 推荐的日常使用顺序

1. 登录系统。
2. 先看并更新本周安排。
3. 填写当天的客户事项。
4. 点击 **“保存当天列表”**。
5. 需要时发送 **售后日报**。
6. 周末或周会前发送 **周报**。
7. 月末使用 **导出 Excel** 归档。

## 12. 常见报错怎么理解

- **“当前用户未配置日志发送 MCP”**：你还没有在右上角“钉钉MCP”里保存日志 MCP 地址。
- **“当前用户未配置通讯录查询 MCP”**：系统没法按姓名帮你查收件人的钉钉 `userId`。
- **“当前用户未配置日历 MCP”**：你还没有在右上角“钉钉MCP”里保存日历 MCP 地址。
- **“当前用户未选择日报模板 / 周报模板”**：你还没有读取模板并保存选择结果。
- **“按姓名找不到人”**：要么通讯录 MCP 没配好，要么你当前钉钉身份对目标同事没有可见权限。

## 13. 最后记住这件事

**背景图、透明度、提示词、钉钉 MCP 地址、日历同步配置、模板选择，都是按当前用户单独保存的。**

你改自己的配置，不会影响其他同事；其他同事改他们自己的配置，也不会覆盖你的内容。
"""


DEPARTMENT_HELP_MARKDOWN = """
# 日程管理页面帮助文档

日程管理页面主要解决“团队协同查看和排班”问题，而不是代替用户页面写日报。你可以在这里按周查看团队安排、按部门或岗位过滤成员、调整协同视角，并在必要时查看代编辑日志。

## 1. 什么时候应该来这个页面

1. **想看团队一周安排时**：例如周会前确认大家这一周都在做什么。
2. **想协调排班时**：例如安排谁去客户现场、谁远程支持、谁有空档。
3. **想从团队视角复核计划时**：你已经在用户页填了自己的安排，但还想确认是否与团队冲突。

## 2. 进入页面后的基本使用步骤

1. 打开 **“日程管理”** 页面。
2. 先完成登录；如果管理员启用了扫码登录，这里也可以用钉钉扫码。
3. 登录后先确认当前显示的是不是你想看的那一周。
4. 用页面上的日期和前后周按钮切到正确周次。
5. 再去看成员列表、筛选条件和周计划视图。

## 3. 怎么看周视图

1. 页面会按周展示成员安排。
2. 你可以切换周次，查看不同日期所在的一周。
3. 选中某个成员后，可以看到这个成员当前周的安排详情。
4. 如果你只想先做团队级概览，建议先不要点开太多明细，先确认整体分布。

## 4. 团队日程里的钉钉同步和代编辑规则

### 同步按钮会做什么

1. 日程管理页读取的是每个成员自己的周安排和同步状态。
2. 点击 **“同步钉钉”** 时，系统会按当前可见范围处理成员日程。
3. 对已经配置日历 MCP 的成员，系统会把本地待同步日程推送到钉钉。
4. 如果成员的同步方向是 **双向同步**，系统还会把该成员钉钉日历里当前周可读取的日程拉到本系统。
5. 没有配置日历 MCP 的成员会被跳过，不会影响其他成员同步。

### 替别人编辑时的边界

1. 你可以为有权限查看的成员新增本地日程。
2. 你可以删除别人本地创建、尚不属于钉钉导入来源的日程。
3. 你不能删除别人从钉钉同步过来的日程。
4. 你不能修改别人从钉钉同步过来的日程标题、时间、内容或地点。
5. 这些限制同时在页面和后端生效；即使绕过前端提交，后端也会拒绝保存。
6. 你编辑自己的日程时，仍按用户页的同步和删除规则处理。

### 在团队页删除日程时会发生什么

1. 删除 **本系统创建并同步到钉钉的日程**，系统会尝试同步删除钉钉里的对应日程。
2. 删除 **从钉钉拉取到本系统的日程**，只会删除本地显示，不会删除钉钉原始日程；后续也不会再导入同一条钉钉日程。
3. 如果钉钉端删除或取消了本系统创建的同步日程，本地周安排会被移除。
4. 如果钉钉端删除或取消了钉钉导入的日程，本地会保留日程并显示 **钉钉已删除** 或 **钉钉已取消**。

### 多人同时编辑怎么处理

1. 日程管理页保存时会带上当前周安排的更新时间。
2. 如果另一个人已经先保存了同一个成员的本周安排，系统会返回冲突提示。
3. 出现冲突时，页面会要求你刷新后再保存，避免覆盖别人刚刚写入的内容。
4. 手机端日程管理使用同一套校验和权限规则。

## 5. 怎么筛选成员

### 按部门筛选

- 适合部门周会、部门协同、部门资源协调。

### 按岗位筛选

- 适合只看某类角色，比如售前、交付、服务等。

### 排序与记忆

1. 你拖动过成员顺序后，浏览器会记住当前顺序。
2. 你使用过的部门 / 岗位筛选条件，也会按当前账号保存。
3. 所以你下次再打开，通常还是你习惯的查看方式。

## 6. 为什么有些同事看不到

只有在管理员后台被勾选了 **“在日程管理页展示”** 的账号，才会进入这里的成员列表。

如果你发现某个应该出现的人没有出现，优先让管理员检查：

1. 该账号是否启用。
2. 是否勾选了 **“在日程管理页展示”**。
3. 所属部门和岗位是否配置正确。

## 7. 编辑日志是做什么的

右上角 **“编辑日志”** 用于查看当前查看范围内的代编辑记录。

它适合这些场景：

1. 想确认是谁改了谁的周安排。
2. 想排查某条协同记录为什么和原计划不一致。
3. 想追溯最近谁替别人维护过计划。

## 8. 不同角色在这个页面的差异

### 普通用户

- 重点是看团队安排、维护与自己相关的协同内容。

### 部门管理员

- 通常会看到更完整的协同视角，更适合做部门排班和资源协调。

### 系统管理员

- 除了正常查看外，还可以结合后台一起检查成员显示、部门归属和权限配置是否正确。

## 9. 推荐的协同使用顺序

1. 先切到正确周次。
2. 再按部门 / 岗位筛选。
3. 找到目标成员或目标角色。
4. 查看或调整安排。
5. 如有争议或异常，再打开 **“编辑日志”** 追溯修改来源。

## 10. 和用户页面的关系

你可以把两个页面这样理解：

- **用户页面**：写自己的周计划、日报、周报、配置自己的 MCP 和提示词。
- **日程管理页面**：从团队视角做查看、筛选、协同和排班。

所以：

1. 日常内容录入，以 **用户页面** 为主。
2. 团队协调和整体查看，以 **日程管理页面** 为主。

## 11. 扫码登录的注意事项

如果管理员已经配置了钉钉扫码登录：

1. 本页登录弹窗也会支持扫码。
2. 如果管理员勾选了 **“允许当前组织成员直接登录”**，扫码识别后通常可以直接进入。
3. 如果没有勾选自动登录，扫码识别到的用户仍然需要在系统登录白名单里。

## 12. 最常见的使用误区

1. 以为这里只能看不能协同，其实它就是团队协同视图。
2. 以为这里没看到某个同事就是数据丢了，很多时候只是后台没勾选 **“在日程管理页展示”**。
3. 以为这里应该替代用户页面，其实日报、周报、提示词、MCP 仍然应该在用户页面里处理。
"""


ADMIN_HELP_MARKDOWN = """
# 管理员后台帮助文档

管理员后台是整个系统的基础配置中心。它负责岗位字段、部门、本地账号、登录权限、钉钉扫码登录和身份缓存，但**不再统一代替每个用户维护个人 MCP**。当前系统的思路是：管理员搭基础设施，用户自己在右上角维护自己的钉钉 MCP 和提示词。

## 1. 系统初始化推荐顺序

建议你第一次接手系统时，按下面的顺序配置：

1. 先登录管理员后台。
2. 先维护 **字段管理**，把岗位对应的业务选项范围整理好。
3. 再维护 **本地账号管理**，把显示名、岗位、部门、启停状态配齐。
4. 再维护 **钉钉用户权限控制**，确认哪些钉钉 `userId` 能登录、哪些能进后台。
5. 最后维护 **钉钉组织接入与扫码登录**。

这样配置最不容易出现“用户能登录但字段不对”或“能扫码但进来后角色不对”的问题。

## 2. 字段管理是做什么的

字段管理按岗位限制用户在填写页里能看到的业务选项，例如：

- 销售字段
- 项目类型字段
- 服务方式字段
- 服务类型字段

### 配置建议

1. 先想清楚岗位体系，再录入字段范围。
2. 如果一个用户勾选了多个岗位，系统会按岗位做并集。
3. 先把字段规则稳定下来，再大规模给用户分配岗位，会更省事。

## 3. 本地账号管理怎么用

这里负责维护：

- 账号启停
- 显示名称
- 岗位
- 所属部门
- 是否管理员
- 是否部门管理员
- 是否 **在日程管理页展示**

### 给用户开通完整路径时建议这样做

1. 先创建账号。
2. 先分配部门和岗位。
3. 再决定是否勾选：
   - 管理员
   - 部门管理员
   - 在日程管理页展示
4. 最后通知用户去首页登录并配置自己的 MCP。

## 4. 为什么“在日程管理页展示”很重要

这个勾选项决定某个用户会不会出现在 **日程管理页面** 的成员列表里。

如果你没勾：

- 用户自己可能还能登录首页。
- 但团队协同页面里不会看到这个人。

所以当业务方反馈“某人没出现在日程管理页”时，优先检查这里。

## 5. 钉钉用户权限控制怎么理解

这里维护的是 **钉钉身份层面的登录权限**：

1. 哪些钉钉 `userId` 可以登录系统。
2. 哪些钉钉 `userId` 可以进入管理员后台。

### 典型用法

- 想允许普通组织成员扫码登录，就把他们加入登录用户范围。
- 想允许某些人进入后台，就把他们加入管理员 userId 范围。

## 6. 钉钉扫码登录怎么配

在 **“钉钉组织接入与扫码登录”** 中，需要维护：

- `ClientId`
- `ClientSecret`
- `CorpId`
- 回调基地址

### 配置要点

1. **回调基地址必须能被手机访问**。
2. 如果你本地只写了 `127.0.0.1`，手机扫码通常回不来。
3. 建议用局域网地址或公网地址。
4. 钉钉开放平台应用至少需要这些授权范围：
   - `openid`
   - `corpid`
   - `Contact.User.Read`

### 自动登录开关怎么理解

- 勾选 **“允许当前组织成员直接登录”**：扫码识别到的组织成员可直接进入系统。
- 不勾选：扫码用户仍然必须命中系统登录白名单。

## 7. 用户自己的 MCP 到底谁来配

当前系统设计是：

1. **管理员不统一代配所有人的 MCP 地址和模板**。
2. **每个用户自己维护自己的钉钉 MCP 地址和模板**。

### 你要告诉用户的操作步骤

1. 登录用户页面。
2. 打开钉钉 AIHub / MCP 网站，例如 `https://aihub.dingtalk.com/`。
3. 找到自己的：
   - 日志发送 MCP
   - 通讯录查询 MCP
   - 日历 MCP
4. 复制各自的 **StreamableHttp URL**。
5. 回到系统右上角 **“钉钉MCP”**，分别粘贴并保存。
6. 如果要同步日程，点击 **“读取日历”**，选择日历和同步方向。
7. 如果要发送日报 / 周报，点击 **“读取模板”**。
8. 选择日报模板、周报模板，再次保存。

### 为什么不建议管理员统一代配

因为下面这些能力都跟“当前登录用户自己的钉钉身份”有关：

1. 能看到哪些模板。
2. 能查询哪些通讯录成员。
3. 能不能成功发送某类日志。

统一代配很容易串权限、串可见范围。

## 8. 日程同步排查边界

日程同步也遵循“用户自己维护 MCP”的原则。管理员后台主要负责账号、部门、岗位和页面可见性，不直接保存每个人的钉钉日历凭据。

### 先分清三个开关

1. **在日程管理页展示**：只决定这个用户会不会出现在团队日程列表里。
2. **日历 MCP 地址**：决定这个用户能不能和钉钉日历同步。
3. **同步方向**：决定是否允许从钉钉拉取日程；选择 **仅本系统同步到钉钉** 时，不会导入钉钉日程。

### 用户说“钉钉日程没同步过来”时先查这些

1. 用户是否已经在用户页右上角 **“钉钉MCP”** 中保存 **日历 MCP 地址**。
2. 用户是否点击过 **“读取日历”**，并选择了有 `owner` 或 `writer` 权限的日历。
3. 同步方向是否为 **双向同步**。
4. 当前查看的周次是否正确；手动同步只处理当前页面所在周。
5. 这条钉钉日程是否曾经在本系统删除过；如果删过，系统会记住 `eventId`，后续不会再次导入。
6. 页面状态是否显示 **失败** 或 **冲突**；这类情况需要看错误提示或让用户重新确认本地和钉钉哪边为准。

### 删除问题怎么判断

1. 本系统创建并同步到钉钉的日程，本地删除会同步删除钉钉。
2. 钉钉拉取到本系统的日程，本地删除不会删除钉钉，也不会再重复导入。
3. 钉钉端删除本系统创建的同步日程，本地会移除该安排。
4. 钉钉端删除钉钉导入的日程，本地会保留并显示 **钉钉已删除**。

## 9. 数据库 API 密钥和全量导出

系统管理员可以生成用于程序访问的 API key。密钥只在生成接口的响应中显示一次，请立即保存；后台只保存不可逆哈希。

### 生成密钥

管理员登录后调用：

```http
POST /api/admin/api-keys
Cookie: planner_session=<管理员登录会话>
```

响应中的 `api_key.key` 就是明文密钥。普通用户、未登录用户和非管理员会收到 `403`。

### 导出全部数据库信息

```http
GET /api/database/export
X-API-Key: dp_...
```

也支持 `Authorization: Bearer dp_...`。成功响应包含 `tables`，每张表包含表名、建表语句、字段和全部行。`password_hash`、`salt_hex`、`key_hash` 会固定返回 `[REDACTED]`，以免导出结果成为凭据泄露源。

### 吊销密钥

管理员可查看和吊销密钥：

```http
GET /api/admin/api-keys
DELETE /api/admin/api-keys?key_id=1
Cookie: planner_session=<管理员登录会话>
```

请将 API key 放在服务端环境变量或密钥管理系统中，不要写入前端代码、日志、聊天记录或公开仓库。导出接口包含业务全量数据，应仅通过受信网络调用。

## 10. 最近识别到的钉钉用户有什么用

扫码登录成功后，后台会缓存识别到的钉钉身份信息。

这个区域最适合排查：

1. 某个用户最近有没有成功扫码。
2. 识别到的 `userId` 对不对。
3. 角色、手机号、最近更新时间是否正常。

## 11. 常见问题怎么排查

## 11.1 用户扫了码但进不来

按这个顺序查：

1. 钉钉开放平台参数是否正确。
2. 回调基地址手机能不能访问。
3. 是否启用了扫码登录。
4. 是否允许组织成员直接登录。
5. 如果没开自动登录，目标用户是否在登录白名单中。

## 11.2 用户说“看不到自己或同事”

优先检查：

1. 账号是否启用。
2. 是否勾选了 **“在日程管理页展示”**。
3. 所属部门、岗位是否配置正确。

## 11.3 用户说“按姓名发日志找不到人”

按这个顺序判断：

1. 用户自己的 **通讯录查询 MCP** 是否已经配置。
2. 该通讯录 MCP 是否对目标同事有可见权限。
3. 用户是否把 **“钉钉用户查询”** 提示词改坏了。

## 11.4 用户说“读不到模板或发不出日志”

优先检查：

1. 用户自己的 **日志发送 MCP** 地址是否正确。
2. 是否已经点击过 **“读取模板”**。
3. 是否已经保存了日报模板 / 周报模板。
4. 当前模板是否仍然对这个用户可见。

## 12. 最后记住权限边界

你可以这样给自己做区分：

- **管理员后台**：系统级配置。
- **用户页面**：个人数据、个人提示词、个人 MCP、个人发送动作。
- **日程管理页面**：团队协同视图。

只要把这个边界想清楚，后面无论是排查登录、排查模板，还是排查发日志失败，定位都会快很多。
"""


INLINE_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
INLINE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ORDERED_LIST_PATTERN = re.compile(r"^\d+\.\s+")


def _render_inline(text: str) -> str:
    rendered = escape(text, quote=False)
    rendered = INLINE_LINK_PATTERN.sub(
        lambda match: f'<a href="{escape(match.group(2), quote=True)}" target="_blank" rel="noopener">{match.group(1)}</a>',
        rendered,
    )
    rendered = INLINE_CODE_PATTERN.sub(lambda match: f"<code>{match.group(1)}</code>", rendered)
    rendered = INLINE_BOLD_PATTERN.sub(lambda match: f"<strong>{match.group(1)}</strong>", rendered)
    return rendered


def _markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    list_tag = ""

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return
        paragraph = " ".join(item.strip() for item in paragraph_lines if item.strip())
        if paragraph:
            blocks.append(f"<p>{_render_inline(paragraph)}</p>")
        paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items, list_tag
        if not list_items or not list_tag:
            list_items = []
            list_tag = ""
            return
        items_html = "".join(f"<li>{_render_inline(item)}</li>" for item in list_items)
        blocks.append(f"<{list_tag}>{items_html}</{list_tag}>")
        list_items = []
        list_tag = ""

    for raw_line in markdown.strip().splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h3>{_render_inline(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{_render_inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h1>{_render_inline(stripped[2:])}</h1>")
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            if list_tag not in ("", "ul"):
                flush_list()
            list_tag = "ul"
            list_items.append(stripped[2:])
            continue

        if ORDERED_LIST_PATTERN.match(stripped):
            flush_paragraph()
            if list_tag not in ("", "ol"):
                flush_list()
            list_tag = "ol"
            list_items.append(ORDERED_LIST_PATTERN.sub("", stripped, count=1))
            continue

        if list_tag:
            flush_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


HELP_DOCS_OVERLAY_HTML = """
  <div class="help-overlay" id="help-overlay" hidden>
    <section class="help-dialog" role="dialog" aria-modal="true" aria-labelledby="help-dialog-title">
      <div class="help-dialog-head">
        <div>
          <h2 class="help-dialog-title" id="help-dialog-title">帮助文档</h2>
          <div class="help-dialog-subtitle">按当前账号权限展示可查看的文档。每份文档都改成了连续的 Markdown 阅读样式，便于从头到尾照着做。</div>
        </div>
        <button type="button" class="secondary" id="help-overlay-close">关闭</button>
      </div>
      <div class="help-dialog-body">
        <div class="help-dialog-meta">
          <span class="help-meta-pill" id="help-role-pill">当前身份：未登录</span>
          <span class="help-meta-pill" id="help-page-pill">当前页面：用户页面</span>
        </div>
        <div class="help-tab-list" id="help-tab-list" role="tablist" aria-label="帮助文档分类"></div>
        <div class="help-sections" id="help-sections">
          <article class="help-section" data-help-section="user" data-help-tab-label="用户页面" aria-labelledby="help-user-title">
            <div class="help-markdown" id="help-user-title">
__USER_HELP_HTML__
            </div>
          </article>
          <article class="help-section" data-help-section="department" data-help-tab-label="日程管理" aria-labelledby="help-department-title" hidden>
            <div class="help-markdown" id="help-department-title">
__DEPARTMENT_HELP_HTML__
            </div>
          </article>
          <article class="help-section" data-help-section="admin" data-help-tab-label="管理员后台" aria-labelledby="help-admin-title" hidden>
            <div class="help-markdown" id="help-admin-title">
__ADMIN_HELP_HTML__
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
""".replace(
    "__USER_HELP_HTML__", _markdown_to_html(USER_HELP_MARKDOWN)
).replace(
    "__DEPARTMENT_HELP_HTML__", _markdown_to_html(DEPARTMENT_HELP_MARKDOWN)
).replace(
    "__ADMIN_HELP_HTML__", _markdown_to_html(ADMIN_HELP_MARKDOWN)
)
