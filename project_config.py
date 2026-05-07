from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from shutil import which
from typing import Any


LOCAL_CONFIG_FILENAME = "config.json"
EXAMPLE_CONFIG_FILENAME = "config.example.json"


def _strip_json_comments(raw_text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False
    line_comment = False
    block_comment = False
    index = 0

    while index < len(raw_text):
        current = raw_text[index]
        next_char = raw_text[index + 1] if index + 1 < len(raw_text) else ""

        if line_comment:
            if current == "\n":
                line_comment = False
                result.append(current)
            index += 1
            continue

        if block_comment:
            if current == "*" and next_char == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue

        if in_string:
            result.append(current)
            if escape:
                escape = False
            elif current == "\\":
                escape = True
            elif current == '"':
                in_string = False
            index += 1
            continue

        if current == "/" and next_char == "/":
            line_comment = True
            index += 2
            continue

        if current == "/" and next_char == "*":
            block_comment = True
            index += 2
            continue

        result.append(current)
        if current == '"':
            in_string = True
        index += 1

    return "".join(result)


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_strip_json_comments(path.read_text(encoding="utf-8")))
    except FileNotFoundError as error:
        raise RuntimeError(f"配置文件不存在：{path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"配置文件不是合法 JSON：{path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"配置文件根节点必须是对象：{path}")
    return payload


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_path(base_dir: Path, raw_value: object) -> Path:
    value = os.path.expandvars(os.path.expanduser(str(raw_value or "").strip()))
    if not value:
        raise RuntimeError("配置中的路径不能为空。")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    return candidate.resolve()


def _resolve_optional_executable(
    base_dir: Path,
    configured_value: object,
    command_name: str,
    fallback_paths: list[str],
) -> str:
    raw_value = str(configured_value or "").strip()
    if raw_value:
        return str(_resolve_path(base_dir, raw_value))
    discovered = which(command_name)
    if discovered:
        return discovered
    for fallback in fallback_paths:
        candidate = Path(fallback)
        if candidate.exists():
            return str(candidate)
    return ""


def load_app_config(base_dir: Path) -> dict[str, Any]:
    resolved_base_dir = Path(base_dir).resolve()
    example_path = resolved_base_dir / EXAMPLE_CONFIG_FILENAME
    local_path = resolved_base_dir / LOCAL_CONFIG_FILENAME

    example_payload = _read_json_file(example_path)
    config_payload = deepcopy(example_payload)
    using_local_override = False
    if local_path.exists():
        config_payload = _deep_merge(config_payload, _read_json_file(local_path))
        using_local_override = True

    server_payload = config_payload.get("server", {})
    paths_payload = config_payload.get("paths", {})
    executables_payload = config_payload.get("executables", {})
    auth_payload = config_payload.get("auth", {})
    dingtalk_payload = config_payload.get("dingtalk", {})
    launchd_payload = config_payload.get("launchd", {})

    try:
        port = int(server_payload.get("port", 8000))
    except (TypeError, ValueError):
        port = 8000
    if port < 1 or port > 65535:
        raise RuntimeError("配置中的 server.port 必须在 1-65535 之间。")

    path_prefixes: list[str] = []
    for raw_item in executables_payload.get("path_prefixes", []):
        value = str(raw_item or "").strip()
        if not value:
            continue
        path_prefixes.append(str(_resolve_path(resolved_base_dir, value)))

    report_recipients: list[dict[str, str]] = []
    for item in dingtalk_payload.get("report_recipients", []):
        if not isinstance(item, dict):
            continue
        user_id = str(item.get("userId", item.get("user_id", "")) or "").strip()
        name = str(item.get("name", "") or "").strip()
        if not user_id:
            continue
        report_recipients.append({"userId": user_id, "name": name})

    return {
        "config_source_path": local_path if using_local_override else example_path,
        "using_local_override": using_local_override,
        "server": {
            "host": str(server_payload.get("host", "0.0.0.0") or "0.0.0.0").strip(),
            "port": port,
        },
        "paths": {
            "database_path": _resolve_path(resolved_base_dir, paths_payload.get("database_path", "data/planner.db")),
            "log_dir": _resolve_path(resolved_base_dir, paths_payload.get("log_dir", "logs")),
            "prompts_dir": _resolve_path(resolved_base_dir, paths_payload.get("prompts_dir", "prompts")),
            "version_history_dir": _resolve_path(
                resolved_base_dir,
                paths_payload.get("version_history_dir", "version_history"),
            ),
        },
        "executables": {
            "codex_bin": _resolve_optional_executable(
                resolved_base_dir,
                executables_payload.get("codex_bin", ""),
                "codex",
                ["/opt/homebrew/bin/codex"],
            ),
            "node_bin": _resolve_optional_executable(
                resolved_base_dir,
                executables_payload.get("node_bin", ""),
                "node",
                ["/opt/homebrew/bin/node"],
            ),
            "swift_bin": _resolve_optional_executable(
                resolved_base_dir,
                executables_payload.get("swift_bin", ""),
                "swift",
                ["/usr/bin/swift"],
            ),
            "path_prefixes": path_prefixes,
        },
        "auth": {
            "default_local_user_id": str(auth_payload.get("default_local_user_id", "local_default_user")).strip()
            or "local_default_user",
            "default_local_user_name": str(auth_payload.get("default_local_user_name", "本地默认用户")).strip()
            or "本地默认用户",
            "session_cookie_name": str(auth_payload.get("session_cookie_name", "dp_session")).strip() or "dp_session",
            "session_duration_days": int(auth_payload.get("session_duration_days", 7) or 7),
            "admin_account_default_username": str(
                auth_payload.get("admin_account_default_username", "admin")
            ).strip()
            or "admin",
            "admin_account_default_password": str(
                auth_payload.get("admin_account_default_password", "ChangeMe123!")
            ),
            "admin_password_pbkdf2_iterations": int(
                auth_payload.get("admin_password_pbkdf2_iterations", 210000) or 210000
            ),
        },
        "dingtalk": {
            "report_source": str(dingtalk_payload.get("report_source", "daily_planner_web") or "").strip()
            or "daily_planner_web",
            "report_to_chat_default": bool(dingtalk_payload.get("report_to_chat_default", False)),
            "report_recipients": report_recipients,
            "oauth": deepcopy(dingtalk_payload.get("oauth", {})),
            "oauth_defaults": deepcopy(dingtalk_payload.get("oauth_defaults", {})),
        },
        "launchd": {
            "agent_label": str(launchd_payload.get("agent_label", "com.dailyplanner.app") or "").strip()
            or "com.dailyplanner.app",
            "agent_plist_path": _resolve_path(
                resolved_base_dir,
                launchd_payload.get("agent_plist_path", "~/Library/LaunchAgents/com.dailyplanner.app.plist"),
            ),
        },
    }
