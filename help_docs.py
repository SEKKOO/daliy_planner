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
3. **确认钉钉使用目标**：如果你需要发送日报、发送周报、按姓名自动查同事 `userId`，你还需要准备自己的钉钉 MCP。
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
3. 你至少要准备两个 MCP：
   - **日志发送 MCP**：用于读取模板、发送售后日报、发送周报。
   - **通讯录查询 MCP**：用于按姓名查询同事的钉钉 `userId`。
4. 在对应实例详情中找到 **StreamableHttp URL**。
5. 它通常会长得像这样：`https://mcp-gw.dingtalk.com/server/......?key=......`
6. 把两个实例的链接分别复制出来备用，不要混填。

## 4. 怎么把 MCP 配到系统里

1. 回到本系统，点击右上角 **“钉钉MCP”**。
2. 把你刚才复制的两个地址分别填入：
   - **日志发送 MCP 地址**
   - **通讯录查询 MCP 地址**
3. 先点击 **“保存配置”**。
4. 保存成功后，再点击 **“读取模板”**。
5. 系统会使用你填写的 **日志发送 MCP** 去读取当前账号可见的钉钉日志模板。
6. 读取完成后，你需要分别选择：
   - **日报模板**
   - **周报模板**
7. 选好之后，**再点击一次“保存配置”**。

### 重要提醒

- 如果你改了 **日志发送 MCP 地址**，原来已经选过的模板会被清空，你必须重新读取模板、重新选择。
- 如果 **通讯录查询 MCP 地址** 为空，系统就没法按姓名自动查接收人 `userId`。
- 如果模板没有选好，系统会直接禁止发送日报 / 周报。

## 5. 怎么配置提示词

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

## 6. 怎么填写每天的工作内容

1. 登录后先确认页面当前日期是否正确。
2. 页面顶部是 **每周工作安排**，按周维护上午、下午安排和其他待定事项。
3. 这部分通常会 **自动保存**，你改完后不用手动点保存按钮。
4. 页面中间的 **每日事项清单** 支持一日多行，适合把同一天的多个客户、多个项目拆开填写。
5. 填写完成后，请点击 **“保存当天列表”**。
6. 保存成功后，“本周记录”区域会同步展示你这一周已经保存过的记录。

## 7. 怎么发送售后日报

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

## 8. 怎么发送周报

1. 先确认本周数据已经基本完整。
2. 点击 **“发送周报”**。
3. 系统会按你当前周的数据生成周报预览。
4. 确认内容无误后再执行发送。
5. 如果系统提示你没有周报模板，说明你还没有在 **“钉钉MCP”** 里读取并保存周报模板。

## 9. 怎么查看月度汇总和导出 Excel

1. 页面右侧按月区域可以切换月份。
2. 这里会统计：
   - 当月日期数
   - 事项条数
   - 总工时
3. 如果你需要做归档、发给领导或做月度复盘，可以点击 **“导出 Excel”**。

## 10. 推荐的日常使用顺序

1. 登录系统。
2. 先看并更新本周安排。
3. 填写当天的客户事项。
4. 点击 **“保存当天列表”**。
5. 需要时发送 **售后日报**。
6. 周末或周会前发送 **周报**。
7. 月末使用 **导出 Excel** 归档。

## 11. 常见报错怎么理解

- **“当前用户未配置日志发送 MCP”**：你还没有在右上角“钉钉MCP”里保存日志 MCP 地址。
- **“当前用户未配置通讯录查询 MCP”**：系统没法按姓名帮你查收件人的钉钉 `userId`。
- **“当前用户未选择日报模板 / 周报模板”**：你还没有读取模板并保存选择结果。
- **“按姓名找不到人”**：要么通讯录 MCP 没配好，要么你当前钉钉身份对目标同事没有可见权限。

## 12. 最后记住这件事

**背景图、透明度、提示词、钉钉 MCP 地址、模板选择，都是按当前用户单独保存的。**

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

## 4. 怎么筛选成员

### 按部门筛选

- 适合部门周会、部门协同、部门资源协调。

### 按岗位筛选

- 适合只看某类角色，比如售前、交付、服务等。

### 排序与记忆

1. 你拖动过成员顺序后，浏览器会记住当前顺序。
2. 你使用过的部门 / 岗位筛选条件，也会按当前账号保存。
3. 所以你下次再打开，通常还是你习惯的查看方式。

## 5. 为什么有些同事看不到

只有在管理员后台被勾选了 **“在日程管理页展示”** 的账号，才会进入这里的成员列表。

如果你发现某个应该出现的人没有出现，优先让管理员检查：

1. 该账号是否启用。
2. 是否勾选了 **“在日程管理页展示”**。
3. 所属部门和岗位是否配置正确。

## 6. 编辑日志是做什么的

右上角 **“编辑日志”** 用于查看当前查看范围内的代编辑记录。

它适合这些场景：

1. 想确认是谁改了谁的周安排。
2. 想排查某条协同记录为什么和原计划不一致。
3. 想追溯最近谁替别人维护过计划。

## 7. 不同角色在这个页面的差异

### 普通用户

- 重点是看团队安排、维护与自己相关的协同内容。

### 部门管理员

- 通常会看到更完整的协同视角，更适合做部门排班和资源协调。

### 系统管理员

- 除了正常查看外，还可以结合后台一起检查成员显示、部门归属和权限配置是否正确。

## 8. 推荐的协同使用顺序

1. 先切到正确周次。
2. 再按部门 / 岗位筛选。
3. 找到目标成员或目标角色。
4. 查看或调整安排。
5. 如有争议或异常，再打开 **“编辑日志”** 追溯修改来源。

## 9. 和用户页面的关系

你可以把两个页面这样理解：

- **用户页面**：写自己的周计划、日报、周报、配置自己的 MCP 和提示词。
- **日程管理页面**：从团队视角做查看、筛选、协同和排班。

所以：

1. 日常内容录入，以 **用户页面** 为主。
2. 团队协调和整体查看，以 **日程管理页面** 为主。

## 10. 扫码登录的注意事项

如果管理员已经配置了钉钉扫码登录：

1. 本页登录弹窗也会支持扫码。
2. 如果管理员勾选了 **“允许当前组织成员直接登录”**，扫码识别后通常可以直接进入。
3. 如果没有勾选自动登录，扫码识别到的用户仍然需要在系统登录白名单里。

## 11. 最常见的使用误区

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
4. 复制各自的 **StreamableHttp URL**。
5. 回到系统右上角 **“钉钉MCP”**，分别粘贴并保存。
6. 点击 **“读取模板”**。
7. 选择日报模板、周报模板，再次保存。

### 为什么不建议管理员统一代配

因为下面这些能力都跟“当前登录用户自己的钉钉身份”有关：

1. 能看到哪些模板。
2. 能查询哪些通讯录成员。
3. 能不能成功发送某类日志。

统一代配很容易串权限、串可见范围。

## 8. 最近识别到的钉钉用户有什么用

扫码登录成功后，后台会缓存识别到的钉钉身份信息。

这个区域最适合排查：

1. 某个用户最近有没有成功扫码。
2. 识别到的 `userId` 对不对。
3. 角色、手机号、最近更新时间是否正常。

## 9. 常见问题怎么排查

## 9.1 用户扫了码但进不来

按这个顺序查：

1. 钉钉开放平台参数是否正确。
2. 回调基地址手机能不能访问。
3. 是否启用了扫码登录。
4. 是否允许组织成员直接登录。
5. 如果没开自动登录，目标用户是否在登录白名单中。

## 9.2 用户说“看不到自己或同事”

优先检查：

1. 账号是否启用。
2. 是否勾选了 **“在日程管理页展示”**。
3. 所属部门、岗位是否配置正确。

## 9.3 用户说“按姓名发日志找不到人”

按这个顺序判断：

1. 用户自己的 **通讯录查询 MCP** 是否已经配置。
2. 该通讯录 MCP 是否对目标同事有可见权限。
3. 用户是否把 **“钉钉用户查询”** 提示词改坏了。

## 9.4 用户说“读不到模板或发不出日志”

优先检查：

1. 用户自己的 **日志发送 MCP** 地址是否正确。
2. 是否已经点击过 **“读取模板”**。
3. 是否已经保存了日报模板 / 周报模板。
4. 当前模板是否仍然对这个用户可见。

## 10. 最后记住权限边界

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
