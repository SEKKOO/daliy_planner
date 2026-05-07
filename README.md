# 每日计划网页

一个面向个人或小团队的本地工作台账系统，当前版本为 `V1.1.12`。

它把“每日填写、周计划、月度汇总、部门协同、管理员后台、AI 生成、钉钉发送、扫码登录、版本回退”放在同一个轻量应用里，后端仅依赖 Python 标准库，数据默认落在本地 SQLite，适合继续按业务习惯快速迭代。

## 这个项目适合谁

适合：

- 售后 / 交付 / 方案 / 运维类个人工作记录
- 小团队本地部署的日报、周报辅助工具
- 需要浏览器录入、按周统筹、按月汇总的一体化台账
- 已具备本机 `codex` 能力，希望串联 AI 生成与钉钉发送

不适合：

- 追求标准 SaaS、多租户、复杂组织治理的大平台场景
- 需要完整自动化测试、审计、CI/CD、云原生部署规范的企业级系统

## 核心能力

| 模块 | 说明 |
| --- | --- |
| 填写页 `/` | 按天维护事项列表，支持本周记录、周计划、月度统计、Excel 导出、背景与透明度设置 |
| 日程管理 `/department-schedule` | 查看部门周安排与协同视图；普通用户可进入并查看/编辑部门本周安排，部门管理员/管理员可查看更多视角 |
| 管理后台 `/admin` | 本地账号、岗位字段、部门、权限、钉钉 OAuth、钉钉身份缓存等维护 |
| AI 能力 | 生成售后日报、周报、本周兵力盘点、交付进展 |
| 钉钉集成 | 姓名查 `userId`、日志发送、扫码登录、身份映射 |
| 版本管理 | 自动写入版本快照，支持版本回退 |

## 功能细节

### 1. 填写页

- 按天维护事项列表
- 每条事项支持：客户、项目名称、项目类型、销售、服务类型、服务方式、工时、工作内容、遗留事项、风险等字段
- 支持最近客户名称复用
- 支持“本周记录”展示当前所选周内所有已填写记录
- 支持周计划自动保存
- 支持月度统计与 Excel 导出
- 支持白天 / 黑夜模式、背景图、本地图片、Bing 每日图、区域透明度
- 右上角可打开：登录、修改密码、日程管理、管理后台、提示词、钉钉 MCP、背景设置

### 2. 日程管理页 `/department-schedule`

- 与填写页共享主题、背景图、透明度设置
- 支持按周查看部门安排
- 普通用户默认可查看并编辑“部门本周安排”
- 部门管理员 / 系统管理员可查看更多协同视图

### 3. 管理后台 `/admin`

- 管理员密码登录
- 本地账号管理：启停、显示名、岗位、所属部门、管理员权限、部门管理员权限
- 岗位字段限制：按岗位控制销售、项目类型、服务方式、服务类型等可选项
- 钉钉登录权限控制：只控制钉钉 `userId`
- 管理后台权限控制：只控制钉钉 `userId`
- 钉钉 OAuth 配置与扫码登录接入
- 钉钉身份缓存查看

### 4. AI 与导出

依赖本机 `codex` / `node`：

- 售后日报生成、预览、发送
- 周报生成、预览、发送、下载 Word
- 本周兵力盘点生成与导出
- 交付进展分析与缓存读取
- 生成文件默认落到 `logs/`，按用户和类别归档

### 5. 钉钉集成

- 姓名检索钉钉 `userId`
- 钉钉日报 / 周报模板发送
- 钉钉扫码登录
- 钉钉身份映射到本地用户会话
- 支持每个用户单独维护自己的钉钉 MCP 地址

## 技术栈与设计原则

### 技术栈

- 后端：Python 3 标准库（`http.server`、`sqlite3`、`subprocess` 等）
- 数据库：SQLite
- 前端：原生 HTML / CSS / JavaScript，无构建步骤
- AI 调用：本机 `codex` + `node`
- 二维码图片：优先本机 `swift` 生成；不可用时使用公共二维码服务回退

### 设计原则

- 本地可运行，部署简单
- 尽量少依赖，方便复制到新机器继续使用
- 配置文件可注释，可直接按需修改
- 数据尽量留在本地，迁移成本低
- 页面模板、接口、业务逻辑虽然仍较集中，但已逐步拆分

## 目录结构

```text
./
├── app.py
├── admin_page.py
├── auth_service.py
├── department_schedule_page.py
├── project_config.py
├── README.md
├── config.example.json
├── config.json                  # 可选，本地覆盖配置，不建议提交
├── ensure_app_running.sh
├── prompts/
│   ├── README.md
│   ├── daily/
│   ├── weekly/
│   └── send/
├── version_history/
├── data/                        # 运行时生成，默认包含 planner.db
└── logs/                        # 运行时生成，保存 docx/xlsx/巡检日志等
```

### 主要文件职责

- `app.py`
  - 首页模板
  - HTTP 路由
  - 日台账 / 周计划 / 月汇总 / 导出 / AI 编排
  - 版本快照与回退
- `auth_service.py`
  - 用户、本地账号、会话、权限校验
  - 钉钉 OAuth、扫码登录短会话、身份缓存
- `admin_page.py`
  - 管理后台页面模板与前端逻辑
- `department_schedule_page.py`
  - 日程管理页模板与前端逻辑
- `project_config.py`
  - 读取 `config.example.json` 与 `config.json`
  - 解析路径、端口、可执行文件、默认账号等配置
- `prompts/`
  - AI 提示词文件
- `version_history/`
  - 自动保存的版本快照，默认保留最近 5 个版本

## 环境要求

### 基础运行

- Python `3.10+`
- 现代浏览器
- macOS / Linux

说明：

- 如果你只使用台账录入、周计划、月度查看和导出，Python 就够了。
- 项目没有额外 `pip` 依赖。

### AI / 钉钉增强能力

如果还要启用这些能力：

- 售后日报 / 周报生成
- 本周兵力盘点
- 交付进展分析
- 钉钉用户检索
- 钉钉日志发送

还需要本机具备：

- `codex`
- `node`
- 对应网络访问能力

如果要启用钉钉扫码登录，建议再准备：

- 手机可访问当前服务回调地址
- 钉钉开放平台正确配置回调地址与授权范围
- `swift`（可选，用于本地生成二维码 PNG）

## 快速启动

### 1. 复制配置

```bash
cd /path/to/daily_planner_web
cp config.example.json config.json
```

### 2. 按需修改 `config.json`

至少建议修改：

- `server.host`
- `server.port`
- `auth.admin_account_default_password`

### 3. 启动服务

```bash
python3 app.py
```

### 4. 打开页面

- 本机访问：`http://127.0.0.1:<端口>`
- 局域网访问：`http://<你的电脑IP>:<端口>`

前提是：

- `server.host` 不是 `127.0.0.1`
- 系统防火墙允许访问对应端口

### 启动时会自动做什么

程序启动时会：

- 读取 `config.example.json`
- 如果存在 `config.json`，再做覆盖合并
- 自动初始化数据库与运行目录
- 自动比对当前代码与 `version_history/` 中已有快照
- 如果代码内容有变化，自动递增到下一个补丁版本并写入新快照
- 如果代码内容与某个历史版本完全一致，则继续使用那个版本号
- 打印当前使用的配置文件路径、数据库路径、访问地址

## 配置说明

### 配置加载规则

- `config.example.json`：仓库内置模板配置
- `config.json`：本机私有覆盖配置
- 程序会先读模板，再用本地配置覆盖同名字段
- 配置文件支持 `//` 和 `/* ... */` 注释
- `config.json` 不需要复制整份模板，只写需要覆盖的字段即可

### 发布到 GitHub 时建议保留什么

公开仓库建议只保留：

- 源代码文件，例如 `app.py`、`admin_page.py`、`auth_service.py`
- `config.example.json` 这种不含真实密钥的示例配置
- `prompts/` 下的默认提示词模板
- `README.md`、脚本文件和其他通用说明

不要提交：

- `config.json`
- `data/`、`planner.db`、`logs/`、`version_history/`
- 任意真实钉钉 `client_secret`、`corp_id`、MCP 地址、接收人 `userId`
- 任何实际业务记录、生成文档、扫码登录缓存和用户自定义提示词数据

当前仓库的 `.gitignore` 已按上述规则忽略本地运行数据；如果你后续手工导出数据库或日志，也不要再单独提交进去。

### 最小可用示例

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8000
  },
  "auth": {
    "admin_account_default_password": "请改成你自己的管理员密码"
  },
  "dingtalk": {
    "oauth_defaults": {
      "enabled": false
    }
  }
}
```

### 常用配置项

| 路径 | 说明 |
| --- | --- |
| `server.host` / `server.port` | 服务监听地址和端口 |
| `paths.database_path` | SQLite 数据库文件路径 |
| `paths.log_dir` | 导出文件、巡检日志输出目录 |
| `paths.prompts_dir` | 提示词目录 |
| `paths.version_history_dir` | 版本快照目录 |
| `executables.codex_bin` | `codex` 可执行文件绝对路径 |
| `executables.node_bin` | `node` 可执行文件绝对路径 |
| `executables.swift_bin` | `swift` 可执行文件绝对路径，用于本地二维码 PNG 生成 |
| `executables.path_prefixes` | 运行子进程时追加到 PATH 前面的目录 |
| `auth.default_local_user_id` | 未登录时使用的默认本地用户 ID |
| `auth.default_local_user_name` | 未登录时使用的默认本地用户显示名 |
| `auth.admin_account_default_username` | 初始管理员账号 |
| `auth.admin_account_default_password` | 初始管理员密码 |
| `dingtalk.report_source` | 钉钉日志发送来源标识 |
| `dingtalk.report_to_chat_default` | 钉钉日志默认是否发送到单聊 |
| `dingtalk.report_recipients` | 钉钉日志默认接收人 |
| `dingtalk.oauth_defaults` | 钉钉扫码登录默认初始化配置 |
| `launchd.agent_label` | macOS LaunchAgent 标签 |
| `launchd.agent_plist_path` | macOS LaunchAgent plist 路径 |

### 关于钉钉 MCP 配置

当前项目的目标是：

- 所有用户的钉钉 MCP 配置彼此隔离
- 每个用户只维护自己的 MCP 地址
- 默认每个用户的 MCP 配置都为空
- 用户配置为空时，发送日志 / 查询通讯录会直接报错，必须由该用户自己配置

因此当前不再通过项目配置文件集中维护用户级 MCP 地址，更推荐直接在用户页面右上角的“钉钉MCP”弹窗里维护。

## 页面与权限模型

### 1. 默认本地模式

- 未登录时，系统以 `auth.default_local_user_id` 对应的用户运行
- 适合单机自用、临时录入或最小启动场景

### 2. 本地账号密码登录

- 由管理员在 `/admin` 中创建
- 本地账号是否可登录，取决于账号自身启停状态
- 本地账号的管理员权限、部门管理员权限，也完全由本地账号自身配置决定

### 3. 钉钉扫码登录

- 管理员在 `/admin` 中配置 OAuth 参数
- 用户用手机钉钉扫码后完成授权
- 系统会把钉钉身份映射到本地用户体系并建立会话

### 4. 钉钉用户白名单

管理后台里的两组配置：

- 谁可以登录系统
- 谁可以进入管理后台

只控制钉钉 `userId`，不控制本地账号。

也就是说：

- 本地账号能否登录，看本地账号启停状态
- 本地账号是否为管理员，看本地账号管理员勾选状态
- 钉钉用户能否登录 / 进后台，看钉钉 `userId` 白名单

### 5. 角色边界

| 角色 | 能力 |
| --- | --- |
| 普通用户 | 访问填写页、查看自己的数据、编辑自己的提示词与钉钉 MCP、进入日程管理并维护部门本周安排 |
| 部门管理员 | 具备普通用户能力，并可在日程管理查看更多部门协同视图 |
| 系统管理员 | 具备全部能力，可进入 `/admin` |

## 提示词与钉钉 MCP

### 用户级提示词

所有基础提示词文件都在 `prompts/`：

- `prompts/daily/`：日报生成
- `prompts/weekly/`：周报与交付分析
- `prompts/send/`：钉钉查询与发送

当前行为：

- 页面右上角可打开“提示词”弹窗
- 每个用户都可以只修改自己的提示词
- 保存后仅影响当前用户
- 恢复默认后再保存，即可回退到系统提示词版本

相关接口：

- `GET /api/user-prompts`
- `POST /api/user-prompts`

### 用户级钉钉 MCP

当前行为：

- 页面右上角可打开“钉钉MCP”弹窗
- 每个用户都可以配置自己的两个地址：
  - 日志发送 MCP
  - 通讯录查询 MCP
- 每个用户都可以用自己的“日志发送 MCP”读取当前可见的日志模板
- 每个用户都需要分别选择：
  - 日报模板
  - 周报模板
- 默认每个用户都为空
- 留空时，发送日志 / 查询通讯录会直接失败
- 未选择模板时，也会直接禁止发送日报 / 周报
- 保存后仅影响当前用户

相关接口：

- `GET /api/user-dingtalk-mcp`
- `POST /api/user-dingtalk-mcp`
- `GET /api/user-dingtalk-report-templates`

## 钉钉接入说明

### 日志发送依赖什么

要成功发送钉钉日报 / 周报，至少需要：

1. 当前用户已经选择对应的钉钉模板
2. 当前用户可用的日志发送 MCP
3. 正确的接收人 `userId`

其中：

- 模板不再由 `config.json` / `config.example.json` 统一维护
- 当前用户需要先在右上角“钉钉MCP”中读取自己 MCP 可见的模板，再分别选择日报模板、周报模板
- 如果切换了“日志发送 MCP 地址”，原已选模板会被清空，需要重新读取并选择
- 接收人可以通过默认配置 + 最近发送选择组合得到
- 如果按姓名自动查 `userId`，会走当前用户自己的“通讯录查询 MCP”；如果该地址为空，会直接报错并提示先配置

### 扫码登录依赖什么

要成功使用钉钉扫码登录，至少需要：

1. `/admin` 中保存正确的 OAuth 配置
2. 回调地址能被手机访问
3. 钉钉开放平台应用拥有需要的授权范围

默认授权范围见配置：

- `openid`
- `corpid`
- `Contact.User.Read`

## 数据存储与输出目录

### 默认路径

- 数据库：`data/planner.db`
- 导出 / 日志：`logs/`
- 提示词：`prompts/`
- 版本快照：`version_history/`

### 主要数据表

| 表名 | 作用 |
| --- | --- |
| `users` | 用户基础信息 |
| `user_sessions` | 登录会话 |
| `local_accounts` | 本地账号、密码摘要、账号状态、管理员标记 |
| `daily_entries` | 每日事项台账 |
| `weekly_plans` | 按用户、按周保存的周计划 |
| `app_settings` | 页面设置、权限、提示词覆盖、MCP 配置、发送配置等 |
| `dingtalk_user_identities` | 钉钉身份映射缓存 |
| `dingtalk_scan_login_sessions` | 扫码登录短期会话 |

### 输出文件说明

运行过程中生成的 `.docx` / `.xlsx` / 分析结果等会写入 `logs/`。

常见输出包括：

- 日报 Word 文档
- 周报 Word 文档
- 兵力盘点 Excel
- 巡检日志 `logs/monitor.log`

## 常用页面与接口

### 页面

- `/`：填写页
- `/admin`：管理员后台
- `/department-schedule`：日程管理页

### 认证与用户

- `GET /api/auth/me`
- `POST /api/auth/login`
- `POST /api/auth/password-login`
- `POST /api/admin/password-login`
- `POST /api/auth/logout`
- `POST /api/auth/password-update`
- `POST /api/admin/password-update`
- `GET /api/auth/dingtalk-config`
- `POST /api/auth/dingtalk/scan-session`
- `GET /api/auth/dingtalk/scan-entry?login_id=...`
- `GET /api/auth/dingtalk/scan-session?login_id=...`
- `GET /api/auth/dingtalk/scan-qr?login_id=...`
- `GET /api/auth/dingtalk/callback`

### 台账与计划

- `GET /api/entry?date=YYYY-MM-DD`
- `POST /api/entry`
- `DELETE /api/entry?date=YYYY-MM-DD`
- `GET /api/entries?date=YYYY-MM-DD`
- `GET /api/month?month=YYYY-MM`
- `GET /api/weekly-plan?date=YYYY-MM-DD`
- `POST /api/weekly-plan`
- `GET /api/ui-settings`
- `POST /api/ui-settings`

### 提示词与用户级 MCP

- `GET /api/user-prompts`
- `POST /api/user-prompts`
- `GET /api/user-dingtalk-mcp`
- `POST /api/user-dingtalk-mcp`
- `GET /api/user-dingtalk-report-templates`

### AI / 钉钉 / 导出

- `GET /api/dingtalk-user-lookup?name=xxx`
- `GET /api/preview-log?date=YYYY-MM-DD`
- `GET /api/preview-weekly-report?date=YYYY-MM-DD`
- `GET /api/preview-weekly-strength?date=YYYY-MM-DD`
- `GET /api/delivery-progress?date=YYYY-MM-DD`
- `GET /api/delivery-progress-cache?date=YYYY-MM-DD`
- `POST /api/send-daily-log`
- `POST /api/send-weekly-report`
- `GET /api/export?month=YYYY-MM`
- `GET /api/export-log?date=YYYY-MM-DD`
- `GET /api/export-weekly-strength?date=YYYY-MM-DD`
- `GET /api/backgrounds/bing-daily`

### 管理接口

- `GET /api/admin/users`
- `GET /api/admin/account`
- `GET /api/admin/local-accounts`
- `POST /api/admin/local-accounts`
- `GET /api/admin/access-control`
- `POST /api/admin/access-control`
- `GET /api/admin/department-options`
- `POST /api/admin/department-options`
- `GET /api/admin/position-field-scopes`
- `POST /api/admin/position-field-scopes`
- `GET /api/admin/dingtalk-oauth-config`
- `POST /api/admin/dingtalk-oauth-config`
- `GET /api/admin/dingtalk-identities`
- `GET /api/admin/overview`

### 版本管理

- `GET /api/version-history`
- `POST /api/rollback-version`

## 常驻运行与版本回退

### 常驻运行

仓库附带：

- `ensure_app_running.sh`

它会：

- 读取当前配置里的 `launchd.agent_label` / `launchd.agent_plist_path`
- 检查对应 LaunchAgent 是否运行
- 如未运行则尝试 `bootstrap` / `kickstart`
- 把巡检结果写到 `logs/monitor.log`

当前 README 里的常驻运行说明主要面向 macOS；如果你是 Linux 用户，建议自行改成 `systemd` 或 `supervisor`。

### 版本快照与回退

- 每次启动会自动检查当前代码是否和历史快照一致
- 如果当前代码和任一历史版本完全一致，就继续沿用那个版本号
- 如果当前代码和所有历史快照都不同，就自动升到下一个补丁版本，例如 `V1.1.12 -> V1.1.13`
- 第一次生成快照时会以代码里的基线版本作为起点，当前为 `V1.1.12`
- 默认保留最近 5 个版本快照
- 可以通过页面或接口发起回退
- 回退完成后需要重启服务才能完全生效

## 常见问题

### 1. 页面能打开，但 AI 生成功能失败

优先检查：

- `codex` 是否可执行
- `node` 是否可执行
- 当前机器网络是否可访问需要的 MCP 或模型服务
- `config.json` 中是否明确指定了错误的可执行文件路径

### 2. 钉钉日志发送失败 / `Failed to fetch`

优先检查：

- 当前用户是否配置了可用的“日志发送 MCP”
- 钉钉模板 ID、模板字段、接收人 `userId` 是否正确

### 3. 姓名查 `userId` 不准或查不到

优先检查：

- 当前用户自己的“通讯录查询 MCP”是否可用
- 提示词 `prompts/send/dingtalk_user_lookup.txt` 是否被该用户改坏

### 4. 钉钉扫码登录跳不回来

优先检查：

- `redirect_base_url` 是否为手机可访问地址
- 钉钉开放平台里配置的回调地址是否与页面提示一致
- 当前电脑与手机是否在同一网络或可互通

### 5. 背景图切页会刷新吗

- 本地背景图保存在数据库中
- Bing 每日图通过同一代理地址返回，并尽量利用浏览器缓存复用

### 6. 如何备份数据

最重要的是备份：

- `data/planner.db`
- `logs/`
- `config.json`
- `prompts/`（如果你改过默认提示词文件）

## 开发与继续迭代建议

如果后续继续打磨，建议优先做：

1. 继续拆分 `app.py`，把页面模板、路由、数据逻辑、AI 编排进一步分离
2. 给认证、周计划、导出、提示词覆盖、用户级 MCP 增加自动化测试
3. 给管理员关键操作补审计日志
4. 把敏感配置逐步迁移到更安全的配置管理方式
5. 为 Linux 常驻运行补一个 `systemd` 示例

---

如果你把它当作本地业务工具继续迭代，这个项目已经足够实用；
如果你准备把它变成稳定的多人协作系统，下一阶段重点应该放在“模块拆分、测试补齐、权限治理、配置治理”。
