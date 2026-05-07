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
