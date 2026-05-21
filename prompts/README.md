# AI 提示词说明

项目内所有 Codex/AI 提示词都从本目录读取，并按“日报 / 周报 / 发送”分类管理。

## 目录结构

- `prompts/daily/`
  - `log_generation.txt`：日报内容生成
- `prompts/weekly/`
  - `delivery_progress_analysis.txt`：交付项目周报分析
  - `report_generation.txt`：周报生成
- `prompts/send/`
  - `dingtalk_user_lookup.txt`：钉钉用户检索
  - `dingtalk_daily_log_send.txt`：钉钉日报发送
  - `dingtalk_weekly_report_send.txt`：钉钉周报发送

## 用户自定义提示词

- 页面里保存的“用户自定义提示词”会写入对应模板所在目录，不再保存到数据库。
- 文件名格式为 `用户名__原模板名.txt`，例如：
  - `prompts/daily/alice__log_generation.txt`
  - `prompts/weekly/alice__report_generation.txt`
  - `prompts/send/alice__dingtalk_user_lookup.txt`
- 本地账号优先使用登录用户名作为前缀；没有本地账号时回退为当前用户 `user_id`。
- 历史数据库中的提示词覆盖值不会再被读取或迁移。
- 当自定义内容与系统默认模板完全一致时，对应的用户自定义文件会自动删除，重新回到默认模板。

## 占位符规则

占位符格式为 `{{name}}`，由 `app.py` 在运行时替换。

常用占位符：

- `{{context_json}}`：业务上下文 JSON
- `{{response_format_json}}`：期望返回结构示例
- `{{error_format_json}}`：失败返回结构示例
- `{{payload_json}}`：工具调用参数
- `{{target_name}}`：待检索姓名
- `{{not_found_json}}` / `{{ambiguous_json}}` / `{{matched_json}}`：用户检索返回示例

## 修改建议

1. 只改提示词正文，不要改占位符名字。
2. 如果新增提示词文件，需要同步修改 `app.py` 里的读取路径。
3. 修改提示词文件后，重新触发对应功能即可按新内容执行。
