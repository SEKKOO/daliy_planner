#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from shutil import copy2, rmtree
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

import auth_service
from admin_page import render_admin_html as render_admin_page_html
from department_schedule_page import (
    render_department_schedule_html as render_department_schedule_page_html,
)
from project_config import load_app_config


BASE_DIR = Path(__file__).resolve().parent
APP_CONFIG = load_app_config(BASE_DIR)
CONFIG_SOURCE_PATH = Path(APP_CONFIG["config_source_path"])
DATA_DIR = Path(APP_CONFIG["paths"]["database_path"]).parent
DB_PATH = Path(APP_CONFIG["paths"]["database_path"])
LOG_DIR = Path(APP_CONFIG["paths"]["log_dir"])
PROMPTS_DIR = Path(APP_CONFIG["paths"]["prompts_dir"])
APP_VERSION_BASELINE = "V1.1.12"
APP_VERSION = APP_VERSION_BASELINE
VERSION_ARCHIVE_DIR = Path(APP_CONFIG["paths"]["version_history_dir"])
VERSION_PRIMARY_SNAPSHOT_FILENAME = "app.py"
VERSION_SNAPSHOT_ROOTS = (
    VERSION_PRIMARY_SNAPSHOT_FILENAME,
    "admin_page.py",
    "auth_service.py",
    "department_schedule_page.py",
    "project_config.py",
    "config.example.json",
    "ensure_app_running.sh",
    "prompts",
)
VERSION_META_FILENAME = "meta.json"
VERSION_HISTORY_RETENTION = 5
HOST = str(APP_CONFIG["server"]["host"])
PORT = int(APP_CONFIG["server"]["port"])
CODEX_BIN = str(APP_CONFIG["executables"]["codex_bin"])
NODE_BIN = str(APP_CONFIG["executables"]["node_bin"])
COMMAND_PATH_PREFIXES = tuple(str(item) for item in APP_CONFIG["executables"]["path_prefixes"])
DINGTALK_REPORT_SOURCE = str(APP_CONFIG["dingtalk"]["report_source"])
DINGTALK_REPORT_TO_CHAT_DEFAULT = bool(APP_CONFIG["dingtalk"]["report_to_chat_default"])
DINGTALK_REPORT_RECIPIENTS: tuple[dict[str, str], ...] = tuple(
    {"userId": str(item.get("userId", "")).strip(), "name": str(item.get("name", "")).strip()}
    for item in APP_CONFIG["dingtalk"]["report_recipients"]
)
DINGTALK_SEND_CONFIG_SETTING_KEY = "dingtalk_daily_log_send_config_json"
DINGTALK_WEEKLY_REPORT_SEND_CONFIG_SETTING_KEY = "dingtalk_weekly_report_send_config_json"
DINGTALK_USER_MCP_CONFIG_SETTING_KEY = "dingtalk_user_mcp_config_json"
DINGTALK_LOG_MCP_REQUIRED_ERROR = "当前用户未配置日志发送 MCP，请先在右上角“钉钉MCP”中配置。"
DINGTALK_DIRECTORY_MCP_REQUIRED_ERROR = "当前用户未配置通讯录查询 MCP，请先在右上角“钉钉MCP”中配置。"
DINGTALK_DAILY_TEMPLATE_REQUIRED_ERROR = "当前用户未选择日报模板，请先在右上角“钉钉MCP”中读取并选择。"
DINGTALK_WEEKLY_TEMPLATE_REQUIRED_ERROR = "当前用户未选择周报模板，请先在右上角“钉钉MCP”中读取并选择。"
DINGTALK_OAUTH_CONFIG_SETTING_KEY = "dingtalk_oauth_config_json"
DINGTALK_OAUTH_AUTHORIZE_URL = str(APP_CONFIG["dingtalk"]["oauth"].get("authorize_url", "")).strip()
DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL = str(APP_CONFIG["dingtalk"]["oauth"].get("user_access_token_url", "")).strip()
DINGTALK_OAUTH_USER_ME_URL = str(APP_CONFIG["dingtalk"]["oauth"].get("user_me_url", "")).strip()
DINGTALK_OAUTH_DEFAULT_SCOPE = str(APP_CONFIG["dingtalk"]["oauth"].get("default_scope", "")).strip()
DINGTALK_SCAN_SESSION_TTL_MINUTES = int(APP_CONFIG["dingtalk"]["oauth"].get("scan_session_ttl_minutes", 5))
DINGTALK_PUBLIC_QR_SERVICE_TEMPLATE = str(
    APP_CONFIG["dingtalk"]["oauth"].get("public_qr_service_template", "")
).strip()
DINGTALK_DAILY_LOG_SECTION_TITLES = (
    "今日工作",
    "明日计划",
    "风险和需要协助",
    "思考和其他",
)
DINGTALK_WEEKLY_REPORT_SECTION_TITLES = (
    "本周工作",
    "下周计划",
    "问题和风险",
    "需要协助",
    "学习和思考",
)
DINGTALK_DEFAULT_OAUTH_CONFIG = dict(APP_CONFIG["dingtalk"]["oauth_defaults"])
DEFAULT_PAGE_SETTINGS = {
    "weekly_monday_am": "",
    "weekly_monday_pm": "",
    "weekly_tuesday_am": "",
    "weekly_tuesday_pm": "",
    "weekly_wednesday_am": "",
    "weekly_wednesday_pm": "",
    "weekly_thursday_am": "",
    "weekly_thursday_pm": "",
    "weekly_friday_am": "",
    "weekly_friday_pm": "",
    "weekly_saturday_am": "",
    "weekly_saturday_pm": "",
    "weekly_sunday_am": "",
    "weekly_sunday_pm": "",
    "weekly_other_pending": "",
}
WEEKLY_PLAN_KEYS = tuple(DEFAULT_PAGE_SETTINGS.keys())
WEEKLY_PLAN_FIELD_LABELS = {
    "weekly_monday_am": "周一上午",
    "weekly_monday_pm": "周一下午",
    "weekly_tuesday_am": "周二上午",
    "weekly_tuesday_pm": "周二下午",
    "weekly_wednesday_am": "周三上午",
    "weekly_wednesday_pm": "周三下午",
    "weekly_thursday_am": "周四上午",
    "weekly_thursday_pm": "周四下午",
    "weekly_friday_am": "周五上午",
    "weekly_friday_pm": "周五下午",
    "weekly_saturday_am": "周六上午",
    "weekly_saturday_pm": "周六下午",
    "weekly_sunday_am": "周日上午",
    "weekly_sunday_pm": "周日下午",
    "weekly_other_pending": "其他待办",
}
DEFAULT_UI_SETTINGS = {
    "background_image": "",
    "background_mode": "cover",
    "region_opacity": 0.94,
}
BING_DAILY_BACKGROUND_PROXY_PATH = "/api/backgrounds/bing-daily"
BING_DAILY_IMAGE_METADATA_URL = "https://www.bing.com/HPImageArchive.aspx"
BING_DAILY_IMAGE_MARKET = "zh-CN"
DEFAULT_LOCAL_USER_ID = str(APP_CONFIG["auth"]["default_local_user_id"])
DEFAULT_LOCAL_USER_NAME = str(APP_CONFIG["auth"]["default_local_user_name"])
SESSION_COOKIE_NAME = str(APP_CONFIG["auth"]["session_cookie_name"])
SESSION_DURATION_DAYS = int(APP_CONFIG["auth"]["session_duration_days"])
LOGIN_ALLOWED_USERS_SETTING_KEY = "auth_login_allowed_users_json"
ADMIN_ALLOWED_USERS_SETTING_KEY = "auth_admin_allowed_users_json"
ADMIN_ACCOUNT_SETTING_KEY = "admin_account_credentials_json"
ADMIN_ACCOUNT_DEFAULT_USERNAME = str(APP_CONFIG["auth"]["admin_account_default_username"])
ADMIN_ACCOUNT_DEFAULT_PASSWORD = str(APP_CONFIG["auth"]["admin_account_default_password"])
ADMIN_PASSWORD_PBKDF2_ITERATIONS = int(APP_CONFIG["auth"]["admin_password_pbkdf2_iterations"])
PROMPT_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
USER_PROMPT_TEMPLATE_DEFINITIONS = (
    {
        "id": "daily_log_generation",
        "filename": "daily/log_generation.txt",
        "title": "售后日报生成",
        "description": "控制“发送售后日报”时的日志生成结构、语言风格和输出重点。",
    },
    {
        "id": "weekly_report_generation",
        "filename": "weekly/report_generation.txt",
        "title": "周报生成",
        "description": "控制“发送周报”时的周报结构、项目汇总方式和文本表达。",
    },
    {
        "id": "weekly_delivery_progress_analysis",
        "filename": "weekly/delivery_progress_analysis.txt",
        "title": "交付进展分析",
        "description": "控制“交付进展”分析面板的总结口径、风险判断和输出内容。",
    },
    {
        "id": "dingtalk_user_lookup",
        "filename": "send/dingtalk_user_lookup.txt",
        "title": "钉钉用户查询",
        "description": "按姓名自动查询钉钉 userId 时使用，影响发送日志时接收人的自动匹配。",
    },
    {
        "id": "dingtalk_daily_log_send",
        "filename": "send/dingtalk_daily_log_send.txt",
        "title": "钉钉日报发送",
        "description": "控制调用钉钉日志发送动作时的执行提示词与结果格式要求。",
    },
    {
        "id": "dingtalk_weekly_report_send",
        "filename": "send/dingtalk_weekly_report_send.txt",
        "title": "钉钉周报发送",
        "description": "控制调用钉钉周报发送动作时的执行提示词与结果格式要求。",
    },
)
USER_PROMPT_TEMPLATE_BY_ID = {
    str(item["id"]): dict(item)
    for item in USER_PROMPT_TEMPLATE_DEFINITIONS
}
USER_PROMPT_TEMPLATE_BY_FILENAME = {
    str(item["filename"]): dict(item)
    for item in USER_PROMPT_TEMPLATE_DEFINITIONS
}
USER_PROMPT_TEMPLATE_SETTING_KEY_PREFIX = "prompt_template_override"
SWIFT_BIN = str(APP_CONFIG["executables"]["swift_bin"])

auth_service.configure(
    db_path=DB_PATH,
    default_local_user_id=DEFAULT_LOCAL_USER_ID,
    default_local_user_name=DEFAULT_LOCAL_USER_NAME,
    session_duration_days=SESSION_DURATION_DAYS,
    admin_password_pbkdf2_iterations=ADMIN_PASSWORD_PBKDF2_ITERATIONS,
    admin_account_default_username=ADMIN_ACCOUNT_DEFAULT_USERNAME,
    admin_account_default_password=ADMIN_ACCOUNT_DEFAULT_PASSWORD,
    login_allowed_users_setting_key=LOGIN_ALLOWED_USERS_SETTING_KEY,
    admin_allowed_users_setting_key=ADMIN_ALLOWED_USERS_SETTING_KEY,
    admin_account_setting_key=ADMIN_ACCOUNT_SETTING_KEY,
    dingtalk_oauth_config_setting_key=DINGTALK_OAUTH_CONFIG_SETTING_KEY,
    dingtalk_oauth_authorize_url=DINGTALK_OAUTH_AUTHORIZE_URL,
    dingtalk_oauth_user_access_token_url=DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL,
    dingtalk_oauth_user_me_url=DINGTALK_OAUTH_USER_ME_URL,
    dingtalk_oauth_default_scope=DINGTALK_OAUTH_DEFAULT_SCOPE,
    dingtalk_scan_session_ttl_minutes=DINGTALK_SCAN_SESSION_TTL_MINUTES,
    default_dingtalk_oauth_config=DINGTALK_DEFAULT_OAUTH_CONFIG,
)


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>每日计划台账</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%232e77d0'/%3E%3Cstop offset='1' stop-color='%2358a8ff'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect x='10' y='8' width='44' height='48' rx='12' fill='url(%23g)'/%3E%3Crect x='16' y='17' width='32' height='26' rx='7' fill='white' fill-opacity='.96'/%3E%3Crect x='20' y='22' width='18' height='4' rx='2' fill='%23d5e7ff'/%3E%3Crect x='20' y='30' width='12' height='4' rx='2' fill='%23d5e7ff'/%3E%3Cpath d='M23 38l5 5 11-12' fill='none' stroke='%232e77d0' stroke-width='4.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
  <style>
    :root {
      color-scheme: light;
      --bg: #eef5ff;
      --bg-soft: #f8fbff;
      --bg-deep: #e2edfb;
      --panel: rgba(255, 255, 255, 0.46);
      --panel-strong: rgba(255, 255, 255, 0.3);
      --panel-soft: rgba(244, 249, 255, 0.2);
      --ink: #12304f;
      --muted: #5c7592;
      --line: rgba(49, 102, 173, 0.16);
      --line-soft: rgba(49, 102, 173, 0.1);
      --accent: #2e77d0;
      --accent-deep: #1e58a0;
      --accent-soft: #dfeeff;
      --accent-glow: rgba(46, 119, 208, 0.14);
      --accent-strong: #1957ab;
      --ok: #1e8a64;
      --warn: #b17610;
      --danger: #be3c45;
      --shadow: 0 18px 45px rgba(37, 90, 160, 0.12);
      --shadow-strong: 0 24px 55px rgba(30, 88, 160, 0.11), 0 6px 18px rgba(46, 119, 208, 0.06);
      --card-shadow: 0 14px 30px rgba(35, 86, 156, 0.09);
      --button-shadow: 0 10px 20px rgba(46, 119, 208, 0.12);
      --radius: 24px;
      --fs-xxs: 11px;
      --fs-xs: 12px;
      --fs-sm: 13px;
      --fs-md: 14px;
      --fs-lg: 16px;
    }

    body[data-theme="dark"] {
      color-scheme: dark;
      --bg: #172437;
      --bg-soft: #213149;
      --bg-deep: #101a29;
      --panel: rgba(34, 50, 76, 0.68);
      --panel-strong: rgba(48, 69, 101, 0.54);
      --panel-soft: rgba(65, 90, 128, 0.3);
      --ink: #edf5ff;
      --muted: #e1ebf8;
      --line: rgba(159, 191, 236, 0.22);
      --line-soft: rgba(159, 191, 236, 0.14);
      --accent: #7db7ff;
      --accent-deep: #f8fbff;
      --accent-soft: rgba(92, 146, 224, 0.28);
      --accent-glow: rgba(125, 183, 255, 0.24);
      --accent-strong: #edf5ff;
      --ok: #61ddb1;
      --warn: #ffd27a;
      --danger: #ff9aa4;
      --shadow: 0 22px 46px rgba(4, 10, 22, 0.32);
      --shadow-strong: 0 28px 60px rgba(4, 10, 22, 0.34), 0 8px 22px rgba(125, 183, 255, 0.08);
      --card-shadow: 0 18px 34px rgba(4, 10, 22, 0.24);
      --button-shadow: 0 12px 24px rgba(7, 15, 30, 0.18);
    }

    html {
      min-height: 100%;
      background-color: var(--boot-page-background-color, #e2edfb);
      background-image: var(--boot-viewport-background);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      position: relative;
      overflow-x: hidden;
      color: var(--ink);
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      background: transparent;
      padding: 34px 16px 46px;
      transition: background 0.25s ease, color 0.2s ease;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }

    .page-background {
      position: fixed;
      inset: -22vh 0 -22vh 0;
      z-index: 0;
      pointer-events: none;
      background-color: var(--boot-page-background-color, var(--bg-deep));
      background-image: var(--boot-page-background-image, none);
      background-repeat: var(--boot-page-background-repeat, no-repeat, no-repeat, no-repeat);
      background-position: var(--boot-page-background-position, center, center, center);
      background-size: var(--boot-page-background-size, cover, auto, auto);
      transform: translate3d(0, 0, 0) scale3d(1, 1, 1);
      transform-origin: center top;
      transition: background-image 0.25s ease, background-color 0.25s ease, transform 0.2s ease-out, filter 0.2s ease-out;
      will-change: transform, filter;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      inset: auto;
      pointer-events: none;
      z-index: 0;
    }

    body::before {
      top: 108px;
      right: -100px;
      width: 300px;
      height: 300px;
      border-radius: 36% 64% 60% 40%;
      background: radial-gradient(circle at 35% 35%, rgba(46, 119, 208, 0.14), rgba(46, 119, 208, 0.02) 68%, transparent 74%);
      filter: blur(12px);
    }

    body::after {
      left: -150px;
      bottom: 42px;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(94, 168, 255, 0.1), transparent 70%);
    }

    .shell {
      width: min(1220px, calc(100vw - 32px));
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }

    .page-theme-toggle {
      position: fixed;
      top: 16px;
      right: 20px;
      z-index: 20;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
    }

    .page-user-badge {
      position: fixed;
      top: 16px;
      left: 20px;
      z-index: 20;
      min-width: 200px;
      max-width: min(360px, calc(100vw - 40px));
      padding: 12px 14px;
      border-radius: 20px;
      border: 1px solid rgba(49, 102, 173, 0.14);
      background: var(--boot-region-background, linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,249,255,0.84)));
      box-shadow: 0 16px 36px rgba(35, 86, 156, 0.12);
      backdrop-filter: blur(14px);
    }

    .page-user-badge-label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent-strong);
    }

    .page-user-badge-name {
      margin-top: 4px;
      font-size: 20px;
      font-weight: 800;
      line-height: 1.2;
      color: var(--accent-deep);
      word-break: break-word;
    }

    .page-user-badge-meta {
      margin-top: 4px;
      font-size: 12px;
      line-height: 1.5;
      color: var(--muted);
      word-break: break-word;
    }

    .visual-file-name {
      min-height: 40px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: rgba(246, 250, 255, 0.88);
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.5;
      overflow-wrap: anywhere;
    }

    .background-settings-button {
      min-width: 108px;
    }

    .background-settings-menu {
      width: min(360px, calc(100vw - 24px));
      padding: 16px;
      border-radius: 22px;
      border: 1px solid rgba(255,255,255,0.24);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.42), rgba(244,249,255,0.24)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 72%);
      box-shadow: 0 18px 34px rgba(41, 91, 156, 0.08);
      backdrop-filter: blur(16px);
      display: grid;
      gap: 14px;
    }

    .background-settings-menu[hidden] {
      display: none;
    }

    .background-settings-head {
      display: grid;
      gap: 4px;
    }

    .background-settings-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .background-settings-note {
      margin: 0;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .background-settings-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .background-settings-group {
      display: grid;
      gap: 10px;
      padding: 14px;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.18), rgba(247,250,255,0.08));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
    }

    .background-settings-group-title {
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.02em;
    }

    .visual-slider-row {
      display: grid;
      gap: 8px;
    }

    .visual-slider-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
      font-weight: 700;
    }

    .visual-slider-value {
      min-width: 46px;
      text-align: right;
      color: var(--muted);
      font-weight: 600;
    }

    .visual-slider {
      accent-color: var(--accent);
      padding: 0;
      min-height: 0;
      box-shadow: none;
      background: transparent;
      border: 0;
    }

    .hero {
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
      margin: 22px 0 22px;
      width: 100%;
    }

    .hero-card,
    .panel {
      border-radius: var(--radius);
      border: 1px solid rgba(255, 255, 255, 0.28);
      box-shadow: 0 18px 40px rgba(38, 86, 150, 0.06);
      backdrop-filter: blur(20px) saturate(120%);
      width: 100%;
    }

    .hero-card {
      background: var(--boot-panel-background, var(--panel));
      position: relative;
      overflow: hidden;
      padding: 22px;
    }

    .panel {
      background: var(--boot-region-background, var(--panel));
      position: relative;
      overflow: hidden;
      padding: 26px;
    }

    .hero-card::before,
    .panel::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 1px;
      background: linear-gradient(90deg, rgba(46, 119, 208, 0.2), rgba(46, 119, 208, 0.02));
      pointer-events: none;
    }

    .hero-card::after {
      content: "";
      position: absolute;
      right: -44px;
      bottom: -60px;
      width: 220px;
      height: 220px;
      border-radius: 44px;
      transform: rotate(18deg);
      background: linear-gradient(140deg, rgba(46, 119, 208, 0.16), rgba(126, 192, 255, 0.08));
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      letter-spacing: 0.06em;
    }

    h1 {
      margin: 12px 0 8px;
      font-size: clamp(22px, 3vw, 30px);
      line-height: 1.15;
      letter-spacing: -0.03em;
    }

    .lead {
      margin: 0;
      max-width: 55ch;
      color: var(--muted);
      line-height: 1.65;
      font-size: var(--fs-sm);
    }

    .hero-side {
      display: block;
      padding: 0;
    }

    .metric,
    .weekly-plan {
      padding: 20px;
      border-radius: 22px;
      background: var(
        --boot-region-background,
        linear-gradient(180deg, rgba(255,255,255,0.28), rgba(244,249,255,0.14)),
        linear-gradient(135deg, rgba(46,119,208,0.06), rgba(46,119,208,0))
      );
      border: 1px solid rgba(255,255,255,0.22);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.2),
        0 14px 30px rgba(35, 86, 156, 0.05);
      backdrop-filter: blur(18px) saturate(120%);
    }

    .weekly-plan-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(49, 102, 173, 0.09);
    }

    .weekly-plan-meta {
      display: grid;
      gap: 4px;
    }

    .weekly-plan-subtitle {
      color: var(--accent-strong);
      font-size: 15px;
      font-weight: 700;
      line-height: 1.5;
      max-width: 72ch;
    }

    .weekly-plan-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .weekly-plan-saved-at {
      font-size: var(--fs-xs);
      color: var(--muted);
      white-space: nowrap;
      padding-right: 4px;
    }

    .theme-toggle {
      min-width: 108px;
      justify-content: center;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.88));
      color: var(--accent-deep);
      border: 1px solid rgba(49, 102, 173, 0.12);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.48);
      backdrop-filter: blur(10px);
    }

    .tiny-btn {
      padding: 7px 12px;
      font-size: 12px;
      line-height: 1;
    }

    .weekly-board-scroll {
      overflow-x: auto;
      padding-bottom: 4px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(240, 247, 255, 0.08));
      border: 1px solid rgba(255,255,255,0.18);
      padding: 12px;
      backdrop-filter: blur(12px);
    }

    .weekly-board {
      min-width: 1280px;
      display: grid;
      grid-template-columns: 62px repeat(5, minmax(96px, 0.8fr)) repeat(2, minmax(82px, 0.68fr)) minmax(230px, 1.2fr);
      gap: 8px;
      align-items: stretch;
    }

    .weekly-head,
    .weekly-label,
    .weekly-cell,
    .weekly-pending {
      border-radius: 18px;
      border: 1px solid var(--line-soft);
      background: linear-gradient(180deg, var(--panel-strong), var(--panel-soft));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), var(--card-shadow);
    }

    .weekly-corner {
      border-radius: 18px;
      background: linear-gradient(135deg, var(--accent-soft), transparent);
      border: 1px dashed var(--line);
    }

    .weekly-head {
      padding: 12px 10px;
      text-align: center;
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
    }

    .weekly-head.workday,
    .weekly-cell.workday {
      background:
        linear-gradient(180deg, rgba(236, 245, 255, 0.96), rgba(248, 251, 255, 0.92));
    }

    .weekly-head.weekend,
    .weekly-cell.weekend {
      background:
        linear-gradient(180deg, rgba(255, 244, 230, 0.94), rgba(255, 249, 240, 0.9));
      border-color: rgba(214, 154, 72, 0.18);
    }

    .weekly-head.pending-head,
    .weekly-pending {
      background:
        linear-gradient(180deg, rgba(232, 244, 255, 0.96), rgba(242, 249, 255, 0.94));
    }

    .weekly-label {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 4px;
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.04em;
    }

    .weekly-cell {
      padding: 10px;
    }

    .weekly-cell textarea,
    .weekly-pending textarea {
      min-height: 88px;
      height: 100%;
      border-radius: 14px;
    }

    .weekly-pending {
      grid-column: 9;
      grid-row: 2 / span 2;
      padding: 10px;
    }

    .weekly-pending textarea {
      min-height: 188px;
    }

    .metric-label {
      font-size: var(--fs-xxs);
      color: var(--muted);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .metric-value {
      font-size: var(--fs-lg);
      font-weight: 700;
      margin-bottom: 4px;
    }

    .metric-note {
      color: var(--muted);
      line-height: 1.55;
      font-size: var(--fs-sm);
    }

    .layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      align-items: start;
      width: 100%;
    }

    .panel {
      padding: 26px;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 14px;
      margin-bottom: 18px;
    }

    .panel-title {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .panel-subtitle {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.6;
    }

    .toolbar-title .panel-subtitle {
      max-width: 58ch;
    }

    .toolbar,
    .field-row,
    .month-toolbar,
    .stats-grid {
      display: grid;
      gap: 14px;
    }

    .toolbar {
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      margin-bottom: 14px;
      padding: 16px 18px;
      border-radius: 20px;
      position: relative;
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.34), rgba(246,250,255,0.16)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 70%);
      border: 1px solid rgba(255,255,255,0.22);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), 0 8px 18px rgba(46, 119, 208, 0.03);
      backdrop-filter: blur(16px);
    }

    .toolbar::after {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: linear-gradient(180deg, var(--accent), rgba(46, 119, 208, 0.12));
    }

    .toolbar-title {
      min-width: 0;
    }

    .toolbar-title .panel-title {
      text-transform: none;
      letter-spacing: 0;
      font-size: 16px;
      line-height: 1.45;
    }

    .toolbar-date {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(244,249,255,0.08));
      white-space: nowrap;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
      backdrop-filter: blur(12px);
    }

    .toolbar-date label {
      margin: 0;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
    }

    .toolbar-date input {
      width: 154px;
      min-width: 154px;
      padding: 6px 8px;
      border-radius: 12px;
    }

    .editor-list-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin: 0 0 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(49, 102, 173, 0.08);
    }

    .editor-list-title {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .editor-list-note {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.55;
    }

    .editor-workbench {
      margin-top: 14px;
      padding: 16px;
      border-radius: 22px;
      border: 1px solid rgba(49, 102, 173, 0.1);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.28), rgba(244,249,255,0.12)),
        linear-gradient(135deg, rgba(46,119,208,0.035), transparent 72%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 12px 28px rgba(46, 119, 208, 0.04);
      backdrop-filter: blur(18px);
    }

    .week-toolbar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
      padding: 12px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.24), rgba(246,250,255,0.1)),
        linear-gradient(135deg, rgba(46,119,208,0.03), transparent);
      border: 1px solid rgba(255,255,255,0.18);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(14px);
    }

    .week-strip {
      display: grid;
      grid-template-columns: repeat(7, minmax(110px, 1fr));
      gap: 10px;
    }

    .week-btn {
      border-radius: 18px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, var(--panel-strong), var(--panel-soft));
      color: var(--ink);
      text-align: left;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }

    .week-btn.weekend {
      background: linear-gradient(180deg, rgba(255, 244, 230, 0.94), rgba(255, 249, 240, 0.9));
      border-color: rgba(214, 154, 72, 0.18);
    }

    .week-btn:hover {
      border-color: rgba(46, 119, 208, 0.24);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.85),
        0 10px 18px rgba(46, 119, 208, 0.08);
    }

    .week-btn.active {
      background: linear-gradient(135deg, var(--accent), #56a8ff);
      color: #fff;
      border-color: transparent;
      box-shadow: 0 10px 24px rgba(46, 119, 208, 0.2);
    }

    .week-btn.weekend.active {
      background: linear-gradient(135deg, #f0a14a, #f5bf76);
      color: #fff;
      border-color: transparent;
      box-shadow: 0 10px 24px rgba(214, 154, 72, 0.22);
    }

    .week-btn-name {
      display: block;
      font-size: var(--fs-xs);
      font-weight: 700;
      margin-bottom: 2px;
    }

    .week-btn-date {
      display: block;
      font-size: var(--fs-xxs);
      opacity: 0.9;
    }

    .week-range {
      font-size: var(--fs-xs);
      color: var(--muted);
      margin-bottom: 0;
      display: none;
    }

    .field-row {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .month-toolbar {
      grid-template-columns: 1fr auto auto;
      align-items: end;
      margin-bottom: 16px;
      padding: 14px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.26), rgba(243,249,255,0.1)),
        linear-gradient(135deg, rgba(46,119,208,0.06), transparent 75%);
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(16px);
    }

    .stats-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-bottom: 14px;
    }

    .field,
    .stack {
      display: grid;
      gap: 8px;
    }

    label {
      font-size: var(--fs-xs);
      font-weight: 700;
    }

    input,
    select,
    textarea,
    button {
      font: inherit;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }

    input,
    select,
    textarea {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,0.26);
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(247,250,255,0.12));
      color: var(--ink);
      padding: 9px 11px;
      font-size: var(--fs-xs);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.14);
      backdrop-filter: blur(10px);
      -webkit-text-fill-color: currentColor;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease;
    }

    input::placeholder,
    textarea::placeholder {
      color: var(--muted);
      opacity: 0.82;
    }

    input:focus,
    select:focus,
    textarea:focus {
      outline: none;
      border-color: rgba(46, 119, 208, 0.58);
      box-shadow: 0 0 0 4px rgba(46, 119, 208, 0.12);
      transform: translateY(-1px);
    }

    textarea {
      min-height: 72px;
      resize: vertical;
      line-height: 1.6;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      font-weight: 400;
      letter-spacing: 0;
    }

    button {
      border: 0;
      border-radius: 14px;
      padding: 9px 14px;
      font-size: var(--fs-xxs);
      font-weight: 600;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
      white-space: nowrap;
    }

    button:hover {
      opacity: 0.98;
      transform: translateY(-0.5px);
      box-shadow: var(--button-shadow);
    }

    .primary {
      background: linear-gradient(135deg, #2b74cd, #4c97f6);
      color: #fff;
      border: 1px solid rgba(46, 119, 208, 0.18);
      box-shadow: 0 10px 18px rgba(46, 119, 208, 0.14);
    }

    .secondary {
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(245,249,255,0.12));
      color: var(--ink);
      border: 1px solid rgba(255,255,255,0.22);
      backdrop-filter: blur(10px);
    }

    .danger {
      background: linear-gradient(180deg, #fff4f4, #ffe9ea);
      color: var(--danger);
      border: 1px solid rgba(190, 60, 69, 0.16);
    }

    .soft {
      background: linear-gradient(180deg, rgba(235,245,255,0.28), rgba(229, 240, 255, 0.14));
      color: var(--accent-deep);
      border: 1px solid rgba(255,255,255,0.2);
      backdrop-filter: blur(10px);
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }

    .editor-actions {
      display: grid;
      gap: 10px;
      margin-top: 16px;
      padding: 12px 14px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(247, 251, 255, 0.26), rgba(242, 248, 255, 0.14));
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(14px);
    }

    .editor-actions .actions {
      margin-top: 0;
    }

    .editor-actions-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: nowrap;
    }

    .editor-actions-left,
    .editor-actions-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 0;
    }

    .editor-actions-left {
      flex: 0 0 auto;
    }

    .editor-actions-right {
      justify-content: flex-end;
      flex: 1 1 auto;
    }

    .editor-actions .actions button {
      width: 118px;
      min-width: 118px;
      justify-content: center;
      padding: 7px 10px;
      border-radius: 12px;
      font-size: 12px;
      line-height: 1.15;
    }

    .status {
      min-height: 24px;
      margin-top: 10px;
      color: var(--muted);
      font-size: var(--fs-xs);
      padding-left: 2px;
    }

    .status.success { color: var(--ok); }
    .status.warning { color: var(--warn); }
    .status.error { color: var(--danger); }

    .version-badge {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 18;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.26);
      background: rgba(255,255,255,0.74);
      box-shadow: 0 12px 28px rgba(28, 65, 116, 0.12);
      backdrop-filter: blur(14px);
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      pointer-events: none;
      user-select: none;
    }

    .delivery-progress-overlay[hidden] {
      display: none;
    }

    .delivery-progress-overlay {
      position: fixed;
      inset: 0;
      z-index: 40;
      display: flex;
      align-items: stretch;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.44);
      backdrop-filter: blur(12px);
    }

    .delivery-progress-dialog {
      width: min(1080px, 100%);
      max-height: 100%;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 14px;
      padding: 22px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.92), rgba(241, 247, 255, 0.82)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
      overflow: hidden;
    }

    .delivery-progress-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
    }

    .delivery-progress-title {
      margin: 0;
      font-size: 24px;
      color: var(--accent-deep);
    }

    .delivery-progress-subtitle {
      margin-top: 6px;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .delivery-progress-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .delivery-meta-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.52);
      border: 1px solid rgba(255,255,255,0.26);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
    }

    .delivery-progress-list {
      overflow: auto;
      display: grid;
      gap: 12px;
      padding-right: 4px;
    }

    .delivery-report-card {
      border-radius: 22px;
      padding: 18px;
      border: 1px solid rgba(255,255,255,0.2);
      background: linear-gradient(180deg, rgba(255,255,255,0.54), rgba(245,249,255,0.34));
      box-shadow: 0 14px 28px rgba(41, 87, 148, 0.08);
    }

    .delivery-report-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }

    .delivery-report-name {
      margin: 0;
      font-size: 18px;
      color: var(--accent-deep);
    }

    .delivery-report-summary {
      margin-top: 10px;
      color: var(--ink);
      line-height: 1.7;
      font-size: var(--fs-xs);
    }

    .delivery-report-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .delivery-status-badge,
    .delivery-report-badges span {
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    .delivery-status-badge.green {
      background: rgba(39, 158, 102, 0.14);
      color: #18744c;
    }

    .delivery-status-badge.yellow {
      background: rgba(210, 150, 37, 0.16);
      color: #9a6100;
    }

    .delivery-status-badge.red {
      background: rgba(192, 60, 71, 0.14);
      color: #a63842;
    }

    .delivery-report-badges span {
      background: rgba(255,255,255,0.48);
      color: var(--accent-deep);
      border: 1px solid rgba(255,255,255,0.24);
    }

    .delivery-report-grid {
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .delivery-report-section {
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.42);
      border: 1px solid rgba(255,255,255,0.22);
    }

    .delivery-report-section h4 {
      margin: 0 0 10px;
      font-size: 13px;
      color: var(--accent-deep);
    }

    .delivery-report-section ul {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
      color: var(--ink);
      font-size: var(--fs-xs);
      line-height: 1.65;
    }

    .preview-overlay[hidden] {
      display: none;
    }

    .preview-overlay {
      position: fixed;
      inset: 0;
      z-index: 38;
      display: flex;
      align-items: stretch;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.44);
      backdrop-filter: blur(12px);
    }

    .send-result-toast[hidden] {
      display: none;
    }

    .send-result-toast {
      position: fixed;
      top: 24px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 48;
      width: min(480px, calc(100vw - 32px));
      padding: 14px 18px;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.28);
      box-shadow: 0 20px 40px rgba(16, 37, 68, 0.18);
      backdrop-filter: blur(16px);
      background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(242,247,255,0.9));
      color: var(--accent-deep);
      display: grid;
      gap: 4px;
    }

    .send-result-toast.success {
      border-color: rgba(30, 138, 100, 0.22);
      background: linear-gradient(180deg, rgba(241, 255, 248, 0.96), rgba(229, 248, 239, 0.92));
    }

    .send-result-toast.error {
      border-color: rgba(190, 60, 69, 0.24);
      background: linear-gradient(180deg, rgba(255, 245, 246, 0.96), rgba(252, 235, 238, 0.92));
    }

    .send-result-toast-title {
      font-size: 15px;
      font-weight: 700;
      line-height: 1.35;
    }

    .send-result-toast-message {
      font-size: var(--fs-xs);
      line-height: 1.6;
      color: var(--muted);
    }

    .preview-dialog {
      width: min(1120px, 100%);
      max-height: 100%;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 14px;
      padding: 22px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.94), rgba(241, 247, 255, 0.84)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
      overflow: hidden;
    }

    .send-confirm-overlay[hidden] {
      display: none;
    }

    .send-confirm-overlay {
      position: fixed;
      inset: 0;
      z-index: 42;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.38);
      backdrop-filter: blur(10px);
    }

    .send-confirm-dialog {
      width: min(620px, 100%);
      display: grid;
      gap: 16px;
      padding: 22px;
      border-radius: 24px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.96), rgba(241, 247, 255, 0.88)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
    }

    .send-confirm-head,
    .send-confirm-foot {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .send-confirm-title {
      margin: 0;
      font-size: 22px;
      color: var(--accent-deep);
    }

    .send-confirm-content {
      display: grid;
      gap: 12px;
    }

    .send-confirm-summary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px 20px;
    }

    .auth-overlay[hidden] {
      display: none;
    }

    .auth-overlay {
      position: fixed;
      inset: 0;
      z-index: 41;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.4);
      backdrop-filter: blur(12px);
    }

    .auth-dialog {
      width: min(980px, 100%);
      display: grid;
      gap: 18px;
      padding: 24px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.96), rgba(241, 247, 255, 0.88)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
    }

    .auth-sections {
      display: grid;
      grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
      gap: 16px;
    }

    .auth-sections.local-only {
      grid-template-columns: 1fr;
    }

    .auth-section {
      display: grid;
      gap: 12px;
      padding: 16px;
      border-radius: 22px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(244,249,255,0.48));
      box-shadow: var(--card-shadow);
    }

    .auth-section[hidden] {
      display: none;
    }

    .auth-section-title {
      margin: 0;
      font-size: 18px;
      color: var(--accent-deep);
    }

    .auth-field {
      display: grid;
      gap: 6px;
      font-size: var(--fs-xs);
      color: var(--muted);
    }

    .auth-field input {
      width: 100%;
      border: 1px solid rgba(46, 119, 208, 0.18);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(255,255,255,0.92);
      color: var(--ink);
      font: inherit;
    }

    .password-input-wrap {
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
    }

    .password-input-wrap > input {
      padding-right: 52px;
    }

    .password-toggle-btn {
      position: absolute;
      top: 50%;
      right: 8px;
      width: 34px;
      height: 34px;
      min-height: 34px;
      padding: 0;
      border-radius: 12px;
      border: 1px solid rgba(46, 119, 208, 0.18);
      background: rgba(255,255,255,0.76);
      color: var(--accent-deep);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transform: translateY(-50%);
      box-shadow: none;
      cursor: pointer;
      transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease;
    }

    .password-toggle-btn:hover {
      transform: translateY(-50%);
      border-color: rgba(46, 119, 208, 0.3);
      background: rgba(235, 244, 255, 0.96);
    }

    .password-toggle-btn:focus-visible {
      outline: none;
      border-color: rgba(46, 119, 208, 0.46);
      box-shadow: 0 0 0 4px rgba(46, 119, 208, 0.12);
    }

    .password-toggle-btn.is-visible {
      border-color: rgba(46, 119, 208, 0.34);
      background: rgba(225, 238, 255, 0.98);
      color: var(--accent);
    }

    .password-toggle-btn span {
      font-size: 16px;
      line-height: 1;
      pointer-events: none;
    }

    .auth-qr-wrap {
      min-height: 320px;
      display: grid;
      place-items: center;
      border-radius: 20px;
      border: 1px dashed rgba(46, 119, 208, 0.22);
      background:
        radial-gradient(circle at top, rgba(223, 238, 255, 0.6), rgba(255,255,255,0.86) 54%),
        rgba(255,255,255,0.92);
      padding: 18px;
      text-align: center;
    }

    .auth-qr-image {
      width: min(320px, 100%);
      aspect-ratio: 1;
      object-fit: contain;
      border-radius: 18px;
      background: #fff;
      box-shadow: 0 18px 32px rgba(26, 70, 126, 0.14);
      padding: 10px;
    }

    .auth-status-text {
      min-height: 22px;
      font-size: var(--fs-xs);
      line-height: 1.6;
      color: var(--muted);
      white-space: pre-wrap;
    }

    .auth-login-link {
      font-size: var(--fs-xs);
      line-height: 1.6;
      color: var(--accent);
      overflow-wrap: anywhere;
      text-decoration: none;
    }

    .auth-login-link:hover {
      text-decoration: underline;
    }

    .password-overlay[hidden] {
      display: none;
    }

    .password-overlay {
      position: fixed;
      inset: 0;
      z-index: 42;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.42);
      backdrop-filter: blur(12px);
    }

    .password-dialog {
      width: min(520px, 100%);
      display: grid;
      gap: 16px;
      padding: 24px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.96), rgba(241, 247, 255, 0.88)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
    }

    .password-dialog-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .password-dialog-title {
      margin: 0;
      font-size: 22px;
      color: var(--accent-deep);
    }

    .password-dialog-body {
      display: grid;
      gap: 12px;
    }

    .prompt-overlay[hidden] {
      display: none;
    }

    .prompt-overlay {
      position: fixed;
      inset: 0;
      z-index: 42;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(9, 17, 31, 0.42);
      backdrop-filter: blur(12px);
    }

    .prompt-dialog {
      width: min(980px, 100%);
      max-height: min(88vh, 920px);
      display: grid;
      gap: 16px;
      padding: 24px;
      border-radius: 28px;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        linear-gradient(180deg, rgba(252, 253, 255, 0.96), rgba(241, 247, 255, 0.88)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
      box-shadow: 0 28px 70px rgba(15, 36, 66, 0.2);
      overflow: hidden;
    }

    .prompt-dialog-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .prompt-dialog-title {
      margin: 0;
      font-size: 22px;
      color: var(--accent-deep);
    }

    .prompt-dialog-body {
      min-height: 0;
      display: grid;
      gap: 12px;
    }

    .prompt-dialog-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .prompt-meta-pill {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(49, 102, 173, 0.14);
      background: rgba(255,255,255,0.56);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      font-weight: 700;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }

    .prompt-dialog-note {
      padding: 12px 14px;
      border-radius: 16px;
      border: 1px solid rgba(49, 102, 173, 0.12);
      background: rgba(255,255,255,0.44);
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .prompt-editor-textarea {
      min-height: min(52vh, 480px);
      resize: vertical;
      font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
      font-size: 13px;
      line-height: 1.65;
      white-space: pre-wrap;
    }

    .send-confirm-summary-item,
    .send-confirm-recipient-line {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .send-confirm-label {
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.5;
      flex: 0 0 auto;
    }

    .send-confirm-value {
      color: var(--accent-deep);
      font-size: 15px;
      font-weight: 700;
      line-height: 1.5;
      word-break: break-word;
      min-width: 0;
    }

    .send-confirm-toggle {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      width: fit-content;
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(49, 102, 173, 0.12);
      background: rgba(255,255,255,0.46);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      font-weight: 700;
      cursor: pointer;
    }

    .send-confirm-toggle input {
      width: 18px;
      height: 18px;
      margin: 0;
      accent-color: var(--accent);
      cursor: pointer;
    }

    .send-confirm-recipient-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .send-confirm-recipient-editor {
      display: grid;
      gap: 10px;
    }

    .send-confirm-recipient-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr) auto;
      gap: 10px;
      align-items: center;
    }

    .send-confirm-recipient-row input {
      min-width: 0;
    }

    .daily-log-intro-card {
      padding: 10px 14px;
    }

    .daily-log-intro-text {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }

    .preview-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
    }

    .preview-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    .preview-title {
      margin: 0;
      font-size: 24px;
      color: var(--accent-deep);
    }

    .preview-subtitle {
      margin-top: 6px;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .preview-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .preview-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.52);
      border: 1px solid rgba(255,255,255,0.26);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
    }

    .preview-content {
      overflow: auto;
      display: grid;
      gap: 14px;
      padding-right: 4px;
    }

    .preview-card {
      border-radius: 22px;
      padding: 18px;
      border: 1px solid rgba(255,255,255,0.2);
      background: linear-gradient(180deg, rgba(255,255,255,0.54), rgba(245,249,255,0.34));
      box-shadow: 0 14px 28px rgba(41, 87, 148, 0.08);
    }

    .preview-richtext {
      display: grid;
      gap: 10px;
      color: var(--ink);
      line-height: 1.75;
      font-size: var(--fs-xs);
      white-space: pre-wrap;
    }

    .preview-richtext h3 {
      margin: 0;
      font-size: 16px;
      color: var(--accent-deep);
    }

    .preview-richtext p {
      margin: 0;
    }

    .preview-richtext pre {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: inherit;
      color: inherit;
    }

    .daily-log-editor {
      display: grid;
      gap: 14px;
    }

    .weekly-report-editor {
      display: grid;
      gap: 14px;
    }

    .daily-log-send-config {
      display: grid;
      gap: 14px;
    }

    .daily-log-send-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
    }

    .daily-log-send-title {
      margin: 0;
      font-size: 15px;
      color: var(--accent-deep);
    }

    .daily-log-send-note {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .daily-log-chat-toggle {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(49, 102, 173, 0.12);
      background: rgba(255,255,255,0.46);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      font-weight: 700;
      cursor: pointer;
    }

    .daily-log-chat-toggle input {
      width: 18px;
      height: 18px;
      margin: 0;
      accent-color: var(--accent);
      cursor: pointer;
    }

    .daily-log-recipient-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .daily-log-recipient-pill {
      display: inline-flex;
      align-items: center;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.52);
      border: 1px solid rgba(255,255,255,0.26);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
    }

    .daily-log-recipient-empty {
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .daily-log-section {
      display: grid;
      gap: 12px;
    }

    .weekly-report-section {
      display: grid;
      gap: 12px;
    }

    .daily-log-section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .daily-log-section-title {
      margin: 0;
      font-size: 16px;
      color: var(--accent-deep);
    }

    .daily-log-section-note {
      margin: 0;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .weekly-report-section-textarea {
      min-height: 150px;
      resize: vertical;
      font-family: "SFMono-Regular", "Menlo", "Monaco", "PingFang SC", "Microsoft YaHei", monospace;
      line-height: 1.65;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .daily-log-lines {
      display: grid;
      gap: 10px;
    }

    .daily-log-line {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 10px;
      align-items: flex-start;
      padding: 12px;
      border-radius: 16px;
      background: rgba(255,255,255,0.34);
      border: 1px solid rgba(255,255,255,0.2);
    }

    .daily-log-line-index {
      min-width: 30px;
      padding-top: 10px;
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      font-weight: 700;
      text-align: center;
    }

    .daily-log-line textarea {
      min-height: 82px;
      resize: vertical;
    }

    .daily-log-empty {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: rgba(255,255,255,0.22);
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.7;
    }

    .daily-log-output-head {
      margin: 0 0 10px;
      font-size: 15px;
      color: var(--accent-deep);
    }

    .preview-table-wrap {
      overflow: auto;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.22);
      background: rgba(255,255,255,0.3);
    }

    .preview-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
      color: var(--ink);
      font-size: var(--fs-xs);
    }

    .preview-table th,
    .preview-table td {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(49, 102, 173, 0.08);
      border-right: 1px solid rgba(49, 102, 173, 0.08);
      text-align: left;
      vertical-align: top;
      line-height: 1.6;
    }

    .preview-table th:last-child,
    .preview-table td:last-child {
      border-right: 0;
    }

    .preview-table th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: linear-gradient(180deg, rgba(239, 246, 255, 0.94), rgba(230, 239, 251, 0.86));
      color: var(--accent-deep);
      font-weight: 700;
    }

    .preview-list {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
      color: var(--ink);
      font-size: var(--fs-xs);
      line-height: 1.65;
    }

    .list-editor,
    .recent-list,
    .month-list {
      display: grid;
      gap: 12px;
    }

    .item-card,
    .entry-card,
    .stat-card {
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,0.22);
      background: linear-gradient(180deg, rgba(255,255,255,0.2), rgba(244,249,255,0.1));
      box-shadow: 0 12px 24px rgba(35, 86, 156, 0.04);
      backdrop-filter: blur(14px);
    }

    .table-scroll {
      overflow-x: visible;
      padding: 0;
      border-radius: 18px;
      border: 0;
      background: transparent;
      box-shadow: none;
    }

    .table-editor {
      width: 100%;
      min-width: 0;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.22);
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12));
      overflow: hidden;
      box-shadow: 0 14px 28px rgba(43, 91, 158, 0.04);
      backdrop-filter: blur(18px);
    }

    .table-header,
    .item-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 0.92fr) minmax(0, 1.38fr) minmax(0, 1.04fr) 56px;
      gap: 0;
      align-items: stretch;
    }

    .table-header {
      background:
        linear-gradient(180deg, rgba(239, 246, 255, 0.28), rgba(230, 239, 251, 0.14)),
        linear-gradient(90deg, rgba(46,119,208,0.05), transparent);
      border-bottom: 1px solid rgba(255,255,255,0.16);
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.02em;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .table-header > div:last-child,
    .item-row > div:last-child {
      border-right: 0;
    }

    .table-header > div {
      min-width: 0;
      padding: 10px 10px;
      border-right: 1px solid rgba(49, 102, 173, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1.15;
    }

    .item-row > div {
      padding: 12px 10px;
      border-right: 1px solid rgba(49, 102, 173, 0.08);
      min-width: 0;
    }

    .item-row {
      border-bottom: 1px solid rgba(255,255,255,0.14);
      background: rgba(255, 255, 255, 0.14);
      transition: background 0.18s ease, box-shadow 0.18s ease;
    }

    .item-row:nth-child(even) {
      background: rgba(249, 252, 255, 0.08);
    }

    .item-row:hover {
      background: rgba(242, 248, 255, 0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.22);
    }

    .item-row:last-child {
      border-bottom: 0;
    }

    .item-row input,
    .item-row select,
    .item-row textarea {
      min-width: 0;
      border-radius: 12px;
      padding: 10px 12px;
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(248,251,255,0.12));
    }

    .item-row textarea {
      min-height: 92px;
      resize: vertical;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .base-info-cell,
    .service-content-cell,
    .issue-risk-cell {
      display: flex;
      align-items: stretch;
    }

    .base-info-stack,
    .service-content-stack,
    .issue-risk-stack {
      width: 100%;
      display: grid;
      gap: 8px;
    }

    .issue-risk-stack {
      gap: 6px;
    }

    .base-info-line,
    .service-content-line,
    .issue-risk-line {
      display: grid;
      grid-template-columns: 64px minmax(0, 1fr);
      align-items: center;
      gap: 6px;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
    }

    .base-info-line span,
    .service-content-line span,
    .issue-risk-line span {
      white-space: nowrap;
    }

    .base-info-line input,
    .base-info-line select,
    .service-content-line input,
    .service-content-line select,
    .issue-risk-line textarea {
      width: 100%;
      padding: 8px 10px;
      font-size: var(--fs-xs);
    }

    .customer-profile-helper {
      margin-top: -2px;
      padding-left: 70px;
      display: grid;
      gap: 4px;
    }

    .customer-profile-helper[hidden] {
      display: none;
    }

    .customer-profile-tip {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
    }

    .customer-profile-select {
      width: 100%;
      font-size: var(--fs-xs);
      padding: 7px 10px;
    }

    .issue-risk-line {
      align-items: start;
    }

    .issue-risk-line textarea {
      min-height: 52px;
      padding: 8px 10px;
      resize: vertical;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .weekly-plan textarea {
      border-radius: 14px;
    }

    .mini-help {
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.55;
      margin-top: 10px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px dashed rgba(49, 102, 173, 0.12);
      background: rgba(241, 248, 255, 0.82);
    }

    .table-empty {
      padding: 20px;
      color: var(--muted);
      line-height: 1.7;
    }

    .row-action {
      display: flex;
      align-items: center;
      justify-content: center;
      padding-left: 4px;
      padding-right: 4px;
    }

    .mini-btn {
      padding: 4px 5px;
      min-width: 0;
      border-radius: 8px;
      font-size: 10px;
      line-height: 1;
    }

    .entry-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }

    .entry-date {
      font-weight: 700;
      font-size: var(--fs-md);
    }

    .entry-card {
      width: 100%;
      text-align: left;
      padding: 18px;
      position: relative;
      overflow: hidden;
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12));
      transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }

    .entry-card::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: linear-gradient(180deg, var(--accent), rgba(46, 119, 208, 0.08));
    }

    .entry-card:hover {
      transform: translateY(-2px);
      border-color: rgba(46, 119, 208, 0.22);
      box-shadow: 0 16px 30px rgba(46, 119, 208, 0.08);
    }

    .entry-badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: var(--fs-xxs);
      background: var(--accent-soft);
      color: var(--accent-deep);
    }

    .entry-snippet {
      margin-top: 10px;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.65;
      white-space: pre-wrap;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .entry-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
      color: var(--muted);
      font-size: var(--fs-xxs);
    }

    .stat-card {
      padding: 16px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 72%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 10px 20px rgba(46, 119, 208, 0.03);
    }

    .stat-name {
      margin-bottom: 8px;
      font-size: var(--fs-xxs);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .stat-value {
      font-size: var(--fs-lg);
      font-weight: 700;
      color: var(--accent-strong);
    }

    .empty {
      padding: 18px;
      border-radius: 20px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.76), rgba(246,250,255,0.68));
      color: var(--muted);
      line-height: 1.7;
      font-size: var(--fs-sm);
    }

    body[data-theme="dark"]::before {
      background: radial-gradient(circle at 35% 35%, rgba(125, 183, 255, 0.18), rgba(125, 183, 255, 0.04) 70%, transparent 76%);
      filter: blur(10px);
    }

    body[data-theme="dark"]::after {
      background: radial-gradient(circle, rgba(114, 183, 255, 0.14), transparent 72%);
    }

    body[data-theme="dark"] .hero-card,
    body[data-theme="dark"] .panel,
    body[data-theme="dark"] .weekly-plan {
      border-color: rgba(255,255,255,0.1);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.06),
        0 20px 42px rgba(4, 10, 22, 0.18);
    }

    body[data-theme="dark"] .hero-card::after {
      background: linear-gradient(140deg, rgba(125, 183, 255, 0.24), rgba(52, 82, 132, 0.1));
    }

    body[data-theme="dark"] .weekly-corner {
      background: linear-gradient(135deg, rgba(125, 183, 255, 0.22), rgba(50, 74, 113, 0.34));
    }

    body[data-theme="dark"] .weekly-head.workday,
    body[data-theme="dark"] .weekly-cell.workday {
      background: linear-gradient(180deg, rgba(44, 66, 101, 0.94), rgba(31, 48, 76, 0.9));
    }

    body[data-theme="dark"] .weekly-head.weekend,
    body[data-theme="dark"] .weekly-cell.weekend {
      background: linear-gradient(180deg, rgba(110, 82, 44, 0.86), rgba(77, 58, 32, 0.84));
      border-color: rgba(255, 210, 122, 0.2);
    }

    body[data-theme="dark"] .weekly-head.pending-head,
    body[data-theme="dark"] .weekly-pending {
      background: linear-gradient(180deg, rgba(42, 64, 99, 0.92), rgba(30, 48, 77, 0.88));
    }

    body[data-theme="dark"] .primary {
      background: linear-gradient(135deg, #70adff, #9bc7ff);
      border-color: rgba(222, 236, 255, 0.24);
      color: #0d1a2a;
    }

    body[data-theme="dark"] .page-theme-toggle {
      background: transparent;
      border-color: transparent;
      box-shadow: none;
    }

    body[data-theme="dark"] .page-user-badge {
      border-color: rgba(255,255,255,0.12);
      box-shadow: 0 18px 42px rgba(5, 10, 18, 0.34);
    }

    body[data-theme="dark"] .background-settings-menu,
    body[data-theme="dark"] .background-settings-group {
      background:
        linear-gradient(180deg, rgba(40, 58, 88, 0.72), rgba(26, 40, 63, 0.56)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }

    body[data-theme="dark"] .visual-file-name {
      background: rgba(25, 38, 59, 0.78);
      border-color: rgba(159, 191, 236, 0.18);
      color: var(--muted);
    }

    body[data-theme="dark"] .theme-toggle {
      background: linear-gradient(180deg, rgba(52, 76, 112, 0.62), rgba(35, 53, 81, 0.42));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
    }

    body[data-theme="dark"] .editor-workbench {
      background:
        linear-gradient(180deg, rgba(39, 57, 87, 0.54), rgba(25, 39, 61, 0.34)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.06), transparent 72%);
      border-color: rgba(159, 191, 236, 0.14);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 14px 30px rgba(4, 10, 22, 0.14);
    }

    body[data-theme="dark"] .weekly-board-scroll,
    body[data-theme="dark"] .toolbar,
    body[data-theme="dark"] .month-toolbar,
    body[data-theme="dark"] .week-toolbar,
    body[data-theme="dark"] .editor-actions,
    body[data-theme="dark"] .stat-card,
    body[data-theme="dark"] .item-card,
    body[data-theme="dark"] .entry-card,
    body[data-theme="dark"] .empty,
    body[data-theme="dark"] .table-editor {
      border-color: rgba(255,255,255,0.08);
      background:
        linear-gradient(180deg, rgba(48, 69, 101, 0.54), rgba(30, 46, 71, 0.3)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.05), transparent 74%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 14px 28px rgba(4, 10, 22, 0.12);
    }

    body[data-theme="dark"] input,
    body[data-theme="dark"] select,
    body[data-theme="dark"] textarea {
      background: linear-gradient(180deg, rgba(36, 53, 82, 0.76), rgba(25, 39, 61, 0.62));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }

    body[data-theme="dark"] .password-toggle-btn {
      border-color: rgba(255,255,255,0.12);
      background: linear-gradient(180deg, rgba(48, 69, 101, 0.92), rgba(29, 44, 69, 0.84));
      color: var(--ink);
    }

    body[data-theme="dark"] .password-toggle-btn:hover,
    body[data-theme="dark"] .password-toggle-btn.is-visible {
      border-color: rgba(125, 183, 255, 0.28);
      background: linear-gradient(180deg, rgba(70, 102, 150, 0.96), rgba(42, 63, 95, 0.9));
      color: #f8fbff;
    }

    body[data-theme="dark"] input::placeholder,
    body[data-theme="dark"] textarea::placeholder {
      color: rgba(178, 193, 218, 0.86);
    }

    body[data-theme="dark"] .item-row input,
    body[data-theme="dark"] .item-row select,
    body[data-theme="dark"] .item-row textarea,
    body[data-theme="dark"] .weekly-cell textarea,
    body[data-theme="dark"] .weekly-pending textarea {
      background: linear-gradient(180deg, rgba(34, 50, 76, 0.82), rgba(23, 35, 55, 0.68));
      border-color: rgba(255,255,255,0.08);
    }

    body[data-theme="dark"] .secondary {
      background: linear-gradient(180deg, rgba(55, 80, 118, 0.62), rgba(36, 54, 82, 0.44));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
    }

    body[data-theme="dark"] .soft {
      background: linear-gradient(180deg, rgba(77, 114, 165, 0.58), rgba(51, 77, 114, 0.38));
      border-color: rgba(255,255,255,0.1);
      color: #eff6ff;
    }

    body[data-theme="dark"] .danger {
      background: linear-gradient(180deg, rgba(123, 49, 60, 0.9), rgba(86, 35, 43, 0.84));
      border-color: rgba(255, 154, 164, 0.22);
      color: #ffe6e8;
    }

    body[data-theme="dark"] .table-scroll {
      background: transparent;
    }

    body[data-theme="dark"] .toolbar::after,
    body[data-theme="dark"] .entry-card::before {
      opacity: 0.9;
    }

    body[data-theme="dark"] .week-btn {
      background: linear-gradient(180deg, rgba(53, 77, 113, 0.82), rgba(37, 56, 84, 0.7));
      border-color: rgba(159, 191, 236, 0.18);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
    }

    body[data-theme="dark"] .week-btn.active {
      background: linear-gradient(180deg, rgba(248, 252, 255, 0.98), rgba(224, 238, 255, 0.92));
      color: #163a62;
      border-color: rgba(125, 183, 255, 0.42);
      box-shadow:
        0 12px 28px rgba(6, 14, 28, 0.2),
        inset 0 1px 0 rgba(255,255,255,0.86);
      transform: translateY(-1px);
    }

    body[data-theme="dark"] .week-btn.active .week-btn-name {
      color: #15375d;
    }

    body[data-theme="dark"] .week-btn.active .week-btn-date {
      color: #4f7399;
      opacity: 1;
      font-weight: 700;
    }

    body[data-theme="dark"] .week-btn.weekend {
      background: linear-gradient(180deg, rgba(111, 83, 45, 0.86), rgba(77, 58, 32, 0.82));
      border-color: rgba(255, 210, 122, 0.2);
    }

    body[data-theme="dark"] .week-btn.weekend.active {
      background: linear-gradient(180deg, rgba(255, 247, 237, 0.98), rgba(255, 232, 198, 0.92));
      color: #754818;
      border-color: rgba(255, 210, 122, 0.36);
      box-shadow:
        0 12px 28px rgba(42, 25, 7, 0.18),
        inset 0 1px 0 rgba(255,255,255,0.88);
    }

    body[data-theme="dark"] .week-btn.weekend.active .week-btn-name {
      color: #754818;
    }

    body[data-theme="dark"] .week-btn.weekend.active .week-btn-date {
      color: #9b692c;
      opacity: 1;
      font-weight: 700;
    }

    body[data-theme="dark"] .table-header {
      background: linear-gradient(180deg, rgba(56, 81, 119, 0.9), rgba(39, 58, 88, 0.86));
    }

    body[data-theme="dark"] .item-row {
      background: rgba(35, 51, 77, 0.72);
    }

    body[data-theme="dark"] .item-row:nth-child(even) {
      background: rgba(29, 43, 66, 0.8);
    }

    body[data-theme="dark"] .item-row:hover {
      background: rgba(49, 71, 106, 0.74);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }

    body[data-theme="dark"] .empty {
      color: rgba(220, 231, 246, 0.88);
    }

    body[data-theme="dark"] .delivery-progress-dialog {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.96), rgba(28, 43, 66, 0.92)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .delivery-progress-overlay,
    body[data-theme="dark"] .preview-overlay,
    body[data-theme="dark"] .send-confirm-overlay,
    body[data-theme="dark"] .auth-overlay,
    body[data-theme="dark"] .prompt-overlay {
      background: rgba(12, 19, 31, 0.28);
      backdrop-filter: blur(14px);
    }

    body[data-theme="dark"] .delivery-meta-pill,
    body[data-theme="dark"] .delivery-report-badges span,
    body[data-theme="dark"] .delivery-report-section,
    body[data-theme="dark"] .delivery-report-card {
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
      color: var(--ink);
    }

    body[data-theme="dark"] .delivery-status-badge.green {
      background: rgba(97, 221, 177, 0.18);
      color: #c5f6df;
    }

    body[data-theme="dark"] .delivery-status-badge.yellow {
      background: rgba(255, 210, 122, 0.18);
      color: #ffe7b5;
    }

    body[data-theme="dark"] .delivery-status-badge.red {
      background: rgba(255, 154, 164, 0.18);
      color: #ffd0d5;
    }

    body[data-theme="dark"] .version-badge {
      border-color: rgba(255,255,255,0.1);
      background: rgba(28, 42, 64, 0.8);
      box-shadow: 0 14px 30px rgba(4, 10, 22, 0.22);
      color: rgba(229, 238, 250, 0.9);
    }

    body[data-theme="dark"] .preview-dialog {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.96), rgba(28, 43, 66, 0.92)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .send-confirm-dialog {
      background:
        linear-gradient(180deg, rgba(48, 70, 106, 0.96), rgba(31, 46, 71, 0.92)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .auth-dialog,
    body[data-theme="dark"] .auth-section {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.94), rgba(28, 43, 66, 0.9)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .auth-qr-wrap {
      background:
        radial-gradient(circle at top, rgba(70, 102, 148, 0.45), rgba(27, 42, 64, 0.88) 58%),
        rgba(27, 42, 64, 0.92);
      border-color: rgba(255,255,255,0.12);
    }

    body[data-theme="dark"] .password-dialog {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.94), rgba(28, 43, 66, 0.9)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .prompt-dialog {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.94), rgba(28, 43, 66, 0.9)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }

    body[data-theme="dark"] .prompt-meta-pill,
    body[data-theme="dark"] .prompt-dialog-note {
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
      color: var(--ink);
    }

    body[data-theme="dark"] .send-result-toast {
      border-color: rgba(255,255,255,0.1);
      background: linear-gradient(180deg, rgba(47, 69, 104, 0.96), rgba(30, 46, 70, 0.92));
      color: var(--ink);
    }

    body[data-theme="dark"] .send-result-toast.success {
      border-color: rgba(97, 221, 177, 0.24);
      background: linear-gradient(180deg, rgba(31, 82, 67, 0.96), rgba(22, 57, 47, 0.92));
    }

    body[data-theme="dark"] .send-result-toast.error {
      border-color: rgba(255, 154, 164, 0.26);
      background: linear-gradient(180deg, rgba(99, 42, 51, 0.96), rgba(69, 29, 36, 0.92));
    }

    body[data-theme="dark"] .send-result-toast-message {
      color: rgba(220, 231, 246, 0.82);
    }

    body[data-theme="dark"] .preview-pill,
    body[data-theme="dark"] .preview-card,
    body[data-theme="dark"] .preview-table-wrap {
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
      color: var(--ink);
    }

    body[data-theme="dark"] .daily-log-line,
    body[data-theme="dark"] .daily-log-empty {
      background: rgba(35, 52, 79, 0.64);
      border-color: rgba(255,255,255,0.08);
    }

    body[data-theme="dark"] .daily-log-chat-toggle,
    body[data-theme="dark"] .daily-log-recipient-pill {
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
      color: var(--ink);
    }

    body[data-theme="dark"] .send-confirm-toggle {
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
      color: var(--ink);
    }

    body[data-theme="dark"] .daily-log-recipient-empty,
    body[data-theme="dark"] .daily-log-send-note,
    body[data-theme="dark"] .send-confirm-label {
      color: rgba(220, 231, 246, 0.82);
    }

    body[data-theme="dark"] .daily-log-intro-text {
      color: rgba(220, 231, 246, 0.82);
    }

    body[data-theme="dark"] .preview-table th {
      background: linear-gradient(180deg, rgba(56, 81, 119, 0.9), rgba(39, 58, 88, 0.86));
      color: var(--ink);
    }

    @media (max-width: 980px) {
      .toolbar,
      .week-toolbar,
      .week-strip,
      .field-row,
      .month-toolbar,
      .stats-grid {
        grid-template-columns: 1fr;
      }

      .weekly-plan-head {
        align-items: flex-start;
        flex-direction: column;
      }

      .weekly-plan-actions {
        flex-wrap: wrap;
      }

      .page-theme-toggle {
        position: static;
        margin-bottom: 12px;
        align-items: stretch;
        gap: 10px;
      }

      .page-user-badge {
        position: static;
        margin-bottom: 12px;
        max-width: none;
      }

      .version-badge {
        right: 12px;
        bottom: 12px;
        font-size: 11px;
      }

      .toolbar-date {
        width: 100%;
        justify-content: space-between;
      }

      .toolbar-date input {
        width: 100%;
        min-width: 0;
      }

      .editor-actions {
        align-items: stretch;
      }

      .editor-actions-row {
        flex-direction: column;
        align-items: stretch;
      }

      .editor-actions-left,
      .editor-actions-right {
        width: 100%;
        justify-content: stretch;
      }

      .editor-actions .actions button {
        width: 100%;
        min-width: 0;
      }

      .hero {
        margin-top: 0;
      }

      body { padding: 16px 12px 28px; }
      .hero-card,
      .hero-side,
      .panel { padding: 18px; }

      .toolbar,
      .month-toolbar,
      .editor-actions,
      .editor-workbench,
      .background-settings-menu {
        padding: 14px;
      }

      .background-settings-menu {
        width: 100%;
      }

      .delivery-progress-overlay {
        padding: 12px;
      }

      .delivery-progress-dialog {
        padding: 16px;
      }

      .preview-overlay {
        padding: 12px;
      }

      .preview-dialog {
        padding: 16px;
      }

      .auth-overlay {
        padding: 12px;
      }

      .auth-dialog {
        padding: 16px;
      }

      .prompt-overlay {
        padding: 12px;
      }

      .prompt-dialog {
        padding: 16px;
      }

      .delivery-progress-head {
        flex-direction: column;
      }

      .preview-head {
        flex-direction: column;
      }

      .prompt-dialog-head {
        flex-direction: column;
      }

      .auth-sections {
        grid-template-columns: 1fr;
      }

      .delivery-report-grid {
        grid-template-columns: 1fr;
      }

    }
</style>
</head>
<body>
  <script>
    window.__bootUiSettings = __INITIAL_UI_SETTINGS_PAYLOAD__;
    window.__bootFieldOptions = __INITIAL_FIELD_OPTIONS_PAYLOAD__;
    window.__publicQrServiceTemplate = __PUBLIC_QR_SERVICE_TEMPLATE_JSON__;
    (() => {
      const source = window.__bootUiSettings && typeof window.__bootUiSettings === "object" ? window.__bootUiSettings : {};
      const firstDefinedValue = function () {
        for (let index = 0; index < arguments.length; index += 1) {
          const value = arguments[index];
          if (value !== undefined && value !== null) {
            return value;
          }
        }
        return undefined;
      };
      const replaceLiteral = (value, search, replacement) => String(value).split(search).join(replacement);
      const normalizeOpacity = (value, fallback) => {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) {
          return fallback;
        }
        return Math.min(1, Math.max(0.25, Math.round(numeric * 100) / 100));
      };
      const uiSettings = {
        background_image: typeof source.background_image === "string" ? source.background_image : "",
        background_mode: ["cover", "contain", "repeat"].includes(source.background_mode) ? source.background_mode : "cover",
        region_opacity: normalizeOpacity(
          firstDefinedValue(
            source.region_opacity,
            source.weekly_region_opacity,
            source.editor_region_opacity,
            source.month_region_opacity
          ),
          0.94
        )
      };
      const THEME_PREFERENCE_STORAGE_KEY = "daily_planner_theme_preference";
      const readStoredThemePreference = () => {
        try {
          const value = window.localStorage.getItem(THEME_PREFERENCE_STORAGE_KEY);
          return value === "dark" || value === "light" ? value : "";
        } catch (error) {
          return "";
        }
      };
      const getAutoTheme = (currentDate = new Date()) => {
        const hour = currentDate.getHours();
        return hour >= 6 && hour < 19 ? "light" : "dark";
      };
      const theme = readStoredThemePreference() || getAutoTheme();
      const buildBodyBackgroundImage = (currentTheme, backgroundImage) => {
        const baseLayers = currentTheme === "dark"
          ? [
              "radial-gradient(circle at 10% 8%, rgba(125, 183, 255, 0.18), transparent 24%)",
              "radial-gradient(circle at 88% 10%, rgba(125, 183, 255, 0.12), transparent 18%)",
              "linear-gradient(180deg, #243754 0%, #172437 42%, #101a29 100%)"
            ]
          : [
              "radial-gradient(circle at 10% 8%, rgba(46, 119, 208, 0.14), transparent 24%)",
              "radial-gradient(circle at 88% 10%, rgba(86, 168, 255, 0.18), transparent 18%)",
              "linear-gradient(180deg, #f8fbff 0%, #eef5ff 42%, #e2edfb 100%)"
            ];
        if (!backgroundImage) {
          return baseLayers.join(", ");
        }
        const safeBackgroundImage = replaceLiteral(
          replaceLiteral(backgroundImage, "\\\\", "\\\\\\\\"),
          '"',
          '\\"'
        );
        return [`url("${safeBackgroundImage}")`, ...baseLayers].join(", ");
      };
      const buildViewportFallback = (currentTheme) => {
        if (currentTheme === "dark") {
          return [
            "radial-gradient(circle at 14% 10%, rgba(125, 183, 255, 0.18), transparent 26%)",
            "radial-gradient(circle at 86% 88%, rgba(90, 139, 212, 0.2), transparent 30%)",
            "linear-gradient(180deg, #243754 0%, #172437 42%, #101a29 100%)"
          ].join(", ");
        }
        return [
          "radial-gradient(circle at 14% 10%, rgba(107, 176, 255, 0.16), transparent 24%)",
          "radial-gradient(circle at 82% 92%, rgba(58, 122, 203, 0.12), transparent 26%)",
          "linear-gradient(180deg, #f9fcff 0%, #eef5ff 40%, #dce8f8 100%)"
        ].join(", ");
      };
      const buildRegionSurface = (currentTheme, opacity) => {
        const start = opacity;
        const end = Math.max(0.16, opacity - 0.08);
        if (currentTheme === "dark") {
          return `linear-gradient(180deg, rgba(38, 56, 84, ${start}), rgba(25, 39, 60, ${end}))`;
        }
        return `linear-gradient(180deg, rgba(255, 255, 255, ${start}), rgba(244, 249, 255, ${end}))`;
      };
      const buildBackgroundLayerStyle = (backgroundImage, backgroundMode) => {
        if (!backgroundImage) {
          return {
            size: "cover, auto, auto",
            position: "center, center, center",
            repeat: "no-repeat, no-repeat, no-repeat",
          };
        }
        if (backgroundMode === "contain") {
          return {
            size: "contain, cover, auto, auto",
            position: "center, center, center, center",
            repeat: "no-repeat, no-repeat, no-repeat, no-repeat",
          };
        }
        if (backgroundMode === "repeat") {
          return {
            size: "auto, cover, auto, auto",
            position: "left top, center, center, center",
            repeat: "repeat, no-repeat, no-repeat, no-repeat",
          };
        }
        return {
          size: "cover, cover, auto, auto",
          position: "center, center, center, center",
          repeat: "no-repeat, no-repeat, no-repeat, no-repeat",
        };
      };

      document.body.dataset.theme = theme;
      const root = document.documentElement;
      const backgroundLayerStyle = buildBackgroundLayerStyle(uiSettings.background_image, uiSettings.background_mode);
      root.style.setProperty("--boot-page-background-color", theme === "dark" ? "#101a29" : "#e2edfb");
      root.style.setProperty("--boot-viewport-background", buildViewportFallback(theme));
      root.style.setProperty("--boot-page-background-image", buildBodyBackgroundImage(theme, uiSettings.background_image));
      root.style.setProperty("--boot-page-background-size", backgroundLayerStyle.size);
      root.style.setProperty("--boot-page-background-position", backgroundLayerStyle.position);
      root.style.setProperty("--boot-page-background-repeat", backgroundLayerStyle.repeat);
      root.style.setProperty("--boot-panel-background", buildRegionSurface(theme, Math.max(0.18, uiSettings.region_opacity - 0.04)));
      root.style.setProperty("--boot-region-background", buildRegionSurface(theme, uiSettings.region_opacity));
    })();
  </script>
  <div class="page-background" id="page-background" aria-hidden="true"></div>
  <datalist id="customer-name-options"></datalist>
  <div class="page-user-badge" id="page-user-badge">
    <div class="page-user-badge-label" id="page-user-badge-label">当前用户</div>
    <div class="page-user-badge-name" id="page-user-display-name">默认用户</div>
    <div class="page-user-badge-meta" id="page-user-display-meta">未登录 · 默认用户模式</div>
  </div>
  <main class="shell">
    <div class="page-theme-toggle">
      <button type="button" class="theme-toggle tiny-btn" id="auth-login-button">登录</button>
      <button type="button" class="theme-toggle tiny-btn" id="auth-logout-button" hidden>退出</button>
      <button type="button" class="theme-toggle tiny-btn" id="auth-password-button" hidden>修改密码</button>
      <button type="button" class="theme-toggle tiny-btn" id="auth-department-schedule-button" hidden>日程管理</button>
      <button type="button" class="theme-toggle tiny-btn" id="auth-admin-page-button" hidden>管理后台</button>
      <button type="button" class="theme-toggle tiny-btn" id="theme-toggle">黑夜模式</button>
      <button type="button" class="theme-toggle tiny-btn background-settings-button" id="background-settings-button" aria-expanded="false" aria-controls="background-settings-menu">背景设置</button>
      <div class="background-settings-menu" id="background-settings-menu" hidden>
        <div class="background-settings-head">
          <h2 class="background-settings-title">背景与透明度</h2>
          <p class="background-settings-note">在这里设置本地背景图或 Bing 每日图片，并单独调整周计划区、每日编辑区、月度区域的透明度。</p>
        </div>
        <div class="background-settings-group">
          <div class="background-settings-group-title">页面背景图</div>
          <input id="background-image-input" type="file" accept="image/*" hidden>
          <div class="background-settings-actions">
            <button type="button" class="secondary" id="select-background-image">选择背景图</button>
            <button type="button" class="secondary" id="use-bing-background">使用 Bing 每日图</button>
            <button type="button" class="soft" id="clear-background-image">清除背景图</button>
          </div>
          <div class="visual-file-name" id="background-image-name">未设置背景图</div>
          <label class="stack">
            <span class="background-settings-group-title">背景模式</span>
            <select id="background-mode-select">
              <option value="cover">缩放铺满</option>
              <option value="contain">完整显示</option>
              <option value="repeat">平铺</option>
            </select>
          </label>
        </div>
        <div class="background-settings-group">
          <div class="visual-slider-row">
            <div class="visual-slider-top">
              <span>区域透明度</span>
              <span class="visual-slider-value" id="region-opacity-value">94%</span>
            </div>
            <input class="visual-slider" id="region-opacity-input" type="range" min="25" max="100" step="1" value="94">
          </div>
        </div>
      </div>
      <button type="button" class="theme-toggle tiny-btn" id="prompt-editor-button" hidden>提示词</button>
      <button type="button" class="theme-toggle tiny-btn" id="user-dingtalk-mcp-button" hidden>钉钉MCP</button>
    </div>
    <section class="hero">
      <aside class="hero-card hero-side">
        <div class="weekly-plan" id="weekly-plan-box">
          <div class="weekly-plan-head">
            <div class="weekly-plan-meta">
              <div class="weekly-plan-subtitle" id="weekly-plan-range">每周工作安排：按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。</div>
            </div>
            <div class="weekly-plan-actions">
              <div class="weekly-plan-saved-at" id="weekly-plan-saved-at">最近保存：未保存</div>
              <button type="button" class="danger tiny-btn" id="clear-weekly-plan">清除本周安排</button>
            </div>
          </div>
            <div class="weekly-board-scroll">
            <div class="weekly-board">
              <div class="weekly-corner"></div>
              <div class="weekly-head workday">周一</div>
              <div class="weekly-head workday">周二</div>
              <div class="weekly-head workday">周三</div>
              <div class="weekly-head workday">周四</div>
              <div class="weekly-head workday">周五</div>
              <div class="weekly-head weekend">周六</div>
              <div class="weekly-head weekend">周日</div>
              <div class="weekly-head pending-head">其他待定安排</div>

              <div class="weekly-label">上午</div>
              <div class="weekly-cell workday"><textarea id="weekly-monday-am" placeholder="周一上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-tuesday-am" placeholder="周二上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-wednesday-am" placeholder="周三上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-thursday-am" placeholder="周四上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-friday-am" placeholder="周五上午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-saturday-am" placeholder="周六上午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-sunday-am" placeholder="周日上午安排"></textarea></div>
              <div class="weekly-pending"><textarea id="weekly-other-pending" placeholder="填写本周其他待定安排、临时事项或未定计划"></textarea></div>

              <div class="weekly-label">下午</div>
              <div class="weekly-cell workday"><textarea id="weekly-monday-pm" placeholder="周一下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-tuesday-pm" placeholder="周二下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-wednesday-pm" placeholder="周三下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-thursday-pm" placeholder="周四下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-friday-pm" placeholder="周五下午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-saturday-pm" placeholder="周六下午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-sunday-pm" placeholder="周日下午安排"></textarea></div>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="layout">
      <article class="panel" id="editor-panel">
        <div class="toolbar">
          <div class="toolbar-title">
            <h2 class="panel-title">每日计划编辑区：选择日期后，按列表填写当天的多个客户事项。</h2>
            <p class="panel-subtitle">像工作台一样集中维护日期、周切换、事项清单与保存动作，减少跳转和视觉干扰。</p>
          </div>
          <div class="toolbar-date">
            <label for="work-date">日期：</label>
            <input id="work-date" type="date" value="__INITIAL_DATE__" required>
          </div>
        </div>

        <div class="editor-workbench">
          <div class="week-range" id="week-range"></div>
          <div class="week-toolbar">
            <button type="button" class="secondary" id="prev-week">上一周</button>
            <div class="week-strip" id="week-strip"></div>
            <button type="button" class="secondary" id="next-week">下一周</button>
          </div>

          <div class="editor-list-head">
            <div>
              <h3 class="editor-list-title">每日事项清单</h3>
              <p class="editor-list-note">基础信息、服务内容、工作内容与遗留风险在同一工作台完成维护。</p>
            </div>
          </div>

          <div class="table-scroll">
            <div id="list-editor" class="list-editor"></div>
          </div>
          <div class="status" id="status"></div>

          <div class="editor-actions">
            <div class="editor-actions-row">
              <div class="actions editor-actions-left">
                <button type="button" class="primary" id="save-entry">保存当天列表</button>
              </div>
              <div class="actions editor-actions-right">
                <button type="button" class="soft" id="add-row">新增一行</button>
                <button type="button" class="secondary" id="reload-date">重新载入当天</button>
                <button type="button" class="secondary" id="clear-form">清空表单</button>
                <button type="button" class="danger" id="delete-entry">删除当天记录</button>
              </div>
            </div>
            <div class="editor-actions-row">
              <div class="actions editor-actions-left">
                <button type="button" class="secondary" id="export-daily-log">发送售后日报</button>
                <button type="button" class="secondary" id="export-weekly-report">发送周报</button>
              </div>
              <div class="actions editor-actions-right">
                <button type="button" class="secondary" id="export-weekly-strength">本周兵力盘点</button>
                <button type="button" class="secondary" id="show-delivery-progress">交付进展</button>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top: 24px;">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">本周记录</h2>
              <p class="panel-subtitle">展示当前所选日期所在周内所有已填写记录，点击任意一天可快速回填当天的列表。</p>
            </div>
          </div>
          <div class="recent-list" id="recent-list">
            <div class="empty">正在载入本周记录...</div>
          </div>
        </div>
      </article>

      <section class="panel" id="month-panel">
        <div class="panel-header">
          <div>
            <h2 class="panel-title">按月查看与导出：查看当月每周汇总、总工时，并导出 Excel。</h2>
          </div>
        </div>

        <div class="month-toolbar">
          <div class="field">
            <label for="month-picker">月份</label>
            <input id="month-picker" type="month" value="__INITIAL_MONTH__">
          </div>
          <button type="button" class="secondary" id="refresh-month">刷新月份</button>
          <button type="button" class="primary" id="export-month">导出 Excel</button>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-name">当月日期数</div>
            <div class="stat-value" id="stat-days">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-name">事项条数</div>
            <div class="stat-value" id="stat-items">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-name">总工时</div>
            <div class="stat-value" id="stat-hours">0</div>
          </div>
        </div>

        <div class="month-list" id="month-list">
          <div class="empty">正在载入月份数据...</div>
        </div>
      </section>
    </section>
  </main>
  <div class="version-badge" aria-hidden="true">__APP_VERSION__</div>
  <div class="delivery-progress-overlay" id="delivery-progress-overlay" hidden>
    <section class="delivery-progress-dialog" role="dialog" aria-modal="true" aria-labelledby="delivery-progress-title">
      <div class="delivery-progress-head">
        <div>
          <h2 class="delivery-progress-title" id="delivery-progress-title">交付进展</h2>
          <div class="delivery-progress-subtitle" id="delivery-progress-subtitle">查看当前所选日期所在周内，所有交付项目的周报分析。</div>
        </div>
        <div class="actions" style="margin-top: 0;">
          <button type="button" class="soft" id="delivery-progress-regenerate">重新生成</button>
          <button type="button" class="secondary" id="delivery-progress-close">关闭</button>
        </div>
      </div>
      <div class="delivery-progress-meta" id="delivery-progress-meta"></div>
      <div class="delivery-progress-list" id="delivery-progress-list">
        <div class="empty">请选择日期后查看交付进展。</div>
      </div>
    </section>
  </div>
  <div class="auth-overlay" id="auth-overlay" hidden>
    <section class="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-dialog-title">
      <div class="send-confirm-head">
        <div>
          <h2 class="send-confirm-title" id="auth-dialog-title">登录当前工作台</h2>
          <div class="preview-subtitle" id="auth-dialog-subtitle">请输入本地账号密码登录当前工作台。</div>
        </div>
        <button type="button" class="secondary" id="auth-overlay-close">关闭</button>
      </div>
      <div class="auth-sections local-only" id="auth-sections">
        <section class="auth-section">
          <h3 class="auth-section-title">本地账号登录</h3>
          <div class="muted">默认账号为姓名全拼，密码为姓名全拼@123。</div>
          <label class="auth-field">
            <span>账号</span>
            <input id="auth-local-username" type="text" autocomplete="username" placeholder="例如 zhangsan">
          </label>
          <label class="auth-field">
            <span>密码</span>
            <input id="auth-local-password" type="password" autocomplete="current-password" placeholder="例如 zhangsan@123" data-password-toggle>
          </label>
          <div class="actions" style="margin-top:0;">
            <button type="button" class="primary" id="auth-local-submit">登录</button>
          </div>
          <div class="auth-status-text" id="auth-local-status"></div>
        </section>
        <section class="auth-section" id="dingtalk-auth-section" hidden>
          <h3 class="auth-section-title">钉钉扫码登录</h3>
          <div class="muted" id="dingtalk-scan-hint">管理员完成钉钉组织配置后，这里会生成扫码二维码。</div>
          <div class="auth-qr-wrap" id="dingtalk-scan-qr-wrap">
            <div class="muted">点击下方按钮生成二维码</div>
          </div>
          <div class="actions" style="margin-top:0;">
            <button type="button" class="primary" id="start-dingtalk-scan-login">生成二维码</button>
            <button type="button" class="secondary" id="refresh-dingtalk-scan-login">刷新二维码</button>
          </div>
          <div class="auth-status-text" id="dingtalk-scan-status">二维码默认 5 分钟有效。</div>
          <a class="auth-login-link" id="dingtalk-scan-link" href="#" target="_blank" rel="noopener" hidden></a>
        </section>
      </div>
    </section>
  </div>
  <div class="password-overlay" id="password-overlay" hidden>
    <section class="password-dialog" role="dialog" aria-modal="true" aria-labelledby="password-dialog-title">
      <div class="password-dialog-head">
        <div>
          <h2 class="password-dialog-title" id="password-dialog-title">修改登录密码</h2>
          <div class="muted" id="password-dialog-account">当前账号：未登录</div>
        </div>
        <button type="button" class="secondary" id="password-overlay-close">关闭</button>
      </div>
      <div class="password-dialog-body">
        <label class="auth-field">
          <span>当前密码</span>
          <input id="password-current-input" type="password" autocomplete="current-password" placeholder="请输入当前密码" data-password-toggle>
        </label>
        <label class="auth-field">
          <span>新密码</span>
          <input id="password-new-input" type="password" autocomplete="new-password" placeholder="至少 8 位" data-password-toggle>
        </label>
        <label class="auth-field">
          <span>确认新密码</span>
          <input id="password-confirm-input" type="password" autocomplete="new-password" placeholder="再次输入新密码" data-password-toggle>
        </label>
        <div class="actions" style="margin-top:0;">
          <button type="button" class="primary" id="password-submit-button">保存新密码</button>
        </div>
        <div class="auth-status-text" id="password-status"></div>
      </div>
    </section>
  </div>
  <div class="prompt-overlay" id="prompt-overlay" hidden>
    <section class="prompt-dialog" role="dialog" aria-modal="true" aria-labelledby="prompt-dialog-title">
      <div class="prompt-dialog-head">
        <div>
          <h2 class="prompt-dialog-title" id="prompt-dialog-title">提示词</h2>
          <div class="muted">当前登录用户单独维护 AI 提示词；保存后仅影响当前用户，恢复默认后保存即可回退系统版本。</div>
        </div>
        <button type="button" class="secondary" id="prompt-overlay-close">关闭</button>
      </div>
      <div class="prompt-dialog-body">
        <label class="auth-field">
          <span>提示词类型</span>
          <select id="prompt-template-select"></select>
        </label>
        <div class="prompt-dialog-meta">
          <span class="prompt-meta-pill" id="prompt-template-scope">当前用户专属</span>
          <span class="prompt-meta-pill" id="prompt-template-filename">提示词文件</span>
          <span class="prompt-meta-pill" id="prompt-template-updated-at">当前使用系统默认</span>
        </div>
        <div class="prompt-dialog-note" id="prompt-template-description">请选择要编辑的提示词。</div>
        <label class="auth-field">
          <span>提示词内容</span>
          <textarea id="prompt-template-content" class="prompt-editor-textarea" spellcheck="false" placeholder="正在加载提示词..."></textarea>
        </label>
        <div class="actions" style="margin-top:0;">
          <button type="button" class="soft" id="prompt-template-reset-button">恢复默认</button>
          <button type="button" class="primary" id="prompt-template-save-button">保存提示词</button>
        </div>
        <div class="auth-status-text" id="prompt-template-status"></div>
      </div>
    </section>
  </div>
  <div class="prompt-overlay" id="user-dingtalk-mcp-overlay" hidden>
    <section class="prompt-dialog" role="dialog" aria-modal="true" aria-labelledby="user-dingtalk-mcp-title">
      <div class="prompt-dialog-head">
        <div>
          <h2 class="prompt-dialog-title" id="user-dingtalk-mcp-title">钉钉 MCP</h2>
          <div class="muted">当前用户单独维护自己的钉钉 MCP 地址；留空时，相关发送和查询会直接失败。</div>
        </div>
        <button type="button" class="secondary" id="user-dingtalk-mcp-overlay-close">关闭</button>
      </div>
      <div class="prompt-dialog-body">
        <div class="prompt-dialog-meta">
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-scope">当前用户专属</span>
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-log-state">日志发送：未配置</span>
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-directory-state">通讯录查询：未配置</span>
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-daily-template-state">日报模板：未选择</span>
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-weekly-template-state">周报模板：未选择</span>
          <span class="prompt-meta-pill" id="user-dingtalk-mcp-updated-at">当前未配置</span>
        </div>
        <div class="prompt-dialog-note" id="user-dingtalk-mcp-description">请填写当前用户要使用的钉钉 MCP 地址；保存后可读取该 MCP 可见的日志模板，并分别选择日报与周报模板。</div>
        <label class="auth-field">
          <span>日志发送 MCP 地址</span>
          <input id="user-dingtalk-log-mcp-input" type="url" placeholder="例如：https://your-log-mcp.example.com/sse">
        </label>
        <label class="auth-field">
          <span>通讯录查询 MCP 地址</span>
          <input id="user-dingtalk-directory-mcp-input" type="url" placeholder="例如：https://your-directory-mcp.example.com/sse">
        </label>
        <div class="actions" style="margin-top:0;">
          <button type="button" class="secondary" id="user-dingtalk-mcp-load-templates-button">读取模板</button>
        </div>
        <label class="auth-field">
          <span>日报模板</span>
          <select id="user-dingtalk-daily-template-select">
            <option value="">请选择日报模板</option>
          </select>
        </label>
        <label class="auth-field">
          <span>周报模板</span>
          <select id="user-dingtalk-weekly-template-select">
            <option value="">请选择周报模板</option>
          </select>
        </label>
        <div class="actions" style="margin-top:0;">
          <button type="button" class="soft" id="user-dingtalk-mcp-reset-button">清空配置</button>
          <button type="button" class="primary" id="user-dingtalk-mcp-save-button">保存配置</button>
        </div>
        <div class="auth-status-text" id="user-dingtalk-mcp-status"></div>
      </div>
    </section>
  </div>
  <div class="preview-overlay" id="preview-overlay" hidden>
    <section class="preview-dialog" role="dialog" aria-modal="true" aria-labelledby="preview-title">
      <div class="preview-head">
        <div>
          <h2 class="preview-title" id="preview-title">内容预览</h2>
          <div class="preview-subtitle" id="preview-subtitle">查看生成内容，并将原始文件保存到 logs/用户名/类型 目录。</div>
        </div>
      <div class="preview-actions">
        <button type="button" class="primary" id="preview-send-log" hidden>发送日志</button>
        <button type="button" class="secondary" id="preview-download-log" hidden>下载日志</button>
        <button type="button" class="secondary" id="preview-close">关闭</button>
      </div>
      </div>
      <div class="preview-meta" id="preview-meta"></div>
      <div class="preview-content" id="preview-content">
        <div class="empty">请选择要预览的内容。</div>
      </div>
    </section>
  </div>
  <div class="send-result-toast" id="send-result-toast" hidden>
    <div class="send-result-toast-title" id="send-result-toast-title">发送成功</div>
    <div class="send-result-toast-message" id="send-result-toast-message">日志已发送。</div>
  </div>
  <div class="send-confirm-overlay" id="send-confirm-overlay" hidden>
    <section class="send-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="send-confirm-title">
      <div class="send-confirm-head">
        <h2 class="send-confirm-title" id="send-confirm-title">确认发送日志</h2>
        <button type="button" class="secondary" id="send-confirm-close">关闭</button>
      </div>
      <div class="send-confirm-content" id="send-confirm-content"></div>
      <div class="send-confirm-foot">
        <button type="button" class="secondary" id="send-confirm-cancel">取消</button>
        <button type="button" class="primary" id="send-confirm-submit">确定发送</button>
      </div>
    </section>
  </div>

  <script>
    const initialPageSettings = __INITIAL_SETTINGS_PAYLOAD__;
    const initialUiSettings = window.__bootUiSettings || {};
    const defaultFieldOptions = {
      item_types: ["方案交流", "方案汇报", "POC1", "POC2", "交付", "服务", "基建"],
      project_types: ["A", "B+", "B", "C"],
      sales: ["张泽恒", "秦瑞", "王晖", "王鑫泽"],
      service_modes: ["客户现场", "远程支持"],
    };
    function normalizeFieldOptions(fieldKey, source) {
      const normalized = [];
      const seen = new Set();
      (Array.isArray(source) ? source : []).forEach((item) => {
        const label = String(item || "").trim();
        const key = label.toLowerCase();
        if (!label || seen.has(key)) {
          return;
        }
        seen.add(key);
        normalized.push(label);
      });
      const fallback = Array.isArray(defaultFieldOptions[fieldKey]) ? defaultFieldOptions[fieldKey] : [];
      return normalized.length ? normalized : fallback.slice();
    }
    function readBootFieldOptions(fieldKey) {
      const source = window.__bootFieldOptions && typeof window.__bootFieldOptions === "object"
        ? window.__bootFieldOptions[fieldKey]
        : [];
      return normalizeFieldOptions(fieldKey, source);
    }
    const itemTypeOptions = readBootFieldOptions("item_types");
    const projectTypeOptions = readBootFieldOptions("project_types");
    const salesOptions = readBootFieldOptions("sales");
    const serviceModeOptions = readBootFieldOptions("service_modes");
    function applyFieldOptionsPayload(payload) {
      const source = payload && typeof payload === "object" ? payload : {};
      const nextOptions = {
        item_types: normalizeFieldOptions("item_types", source.item_types),
        project_types: normalizeFieldOptions("project_types", source.project_types),
        sales: normalizeFieldOptions("sales", source.sales),
        service_modes: normalizeFieldOptions("service_modes", source.service_modes),
      };
      itemTypeOptions.splice(0, itemTypeOptions.length, ...nextOptions.item_types);
      projectTypeOptions.splice(0, projectTypeOptions.length, ...nextOptions.project_types);
      salesOptions.splice(0, salesOptions.length, ...nextOptions.sales);
      serviceModeOptions.splice(0, serviceModeOptions.length, ...nextOptions.service_modes);
      window.__bootFieldOptions = nextOptions;
    }

    const dateInput = document.getElementById("work-date");
    const monthInput = document.getElementById("month-picker");
    const listEditor = document.getElementById("list-editor");
    const recentList = document.getElementById("recent-list");
    const monthList = document.getElementById("month-list");
    const statusEl = document.getElementById("status");
    const weekStrip = document.getElementById("week-strip");
    const weekRange = document.getElementById("week-range");
    const weeklyPlanRange = document.getElementById("weekly-plan-range");
    const prevWeekButton = document.getElementById("prev-week");
    const nextWeekButton = document.getElementById("next-week");
    const themeToggleButton = document.getElementById("theme-toggle");
    const backgroundSettingsButton = document.getElementById("background-settings-button");
    const backgroundSettingsMenu = document.getElementById("background-settings-menu");
    const promptEditorButton = document.getElementById("prompt-editor-button");
    const userDingtalkMcpButton = document.getElementById("user-dingtalk-mcp-button");
    const weeklyPlanSavedAt = document.getElementById("weekly-plan-saved-at");
    const clearWeeklyPlanButton = document.getElementById("clear-weekly-plan");
    const weeklyPlanBox = document.getElementById("weekly-plan-box");
    const weeklyPlanPanel = weeklyPlanBox.closest(".hero-card");
    const weeklyBoardScroll = weeklyPlanBox.querySelector(".weekly-board-scroll");
    const editorPanel = document.getElementById("editor-panel");
    const monthPanel = document.getElementById("month-panel");
    const pageBackground = document.getElementById("page-background");
    const pageUserBadge = document.getElementById("page-user-badge");
    const customerNameOptions = document.getElementById("customer-name-options");
    const pageUserBadgeLabel = document.getElementById("page-user-badge-label");
    const pageUserDisplayName = document.getElementById("page-user-display-name");
    const pageUserDisplayMeta = document.getElementById("page-user-display-meta");
    const backgroundImageInput = document.getElementById("background-image-input");
    const selectBackgroundImageButton = document.getElementById("select-background-image");
    const useBingBackgroundButton = document.getElementById("use-bing-background");
    const clearBackgroundImageButton = document.getElementById("clear-background-image");
    const backgroundImageName = document.getElementById("background-image-name");
    const backgroundModeSelect = document.getElementById("background-mode-select");
    const regionOpacityInput = document.getElementById("region-opacity-input");
    const regionOpacityValue = document.getElementById("region-opacity-value");
    const authLoginButton = document.getElementById("auth-login-button");
    const authLogoutButton = document.getElementById("auth-logout-button");
    const authPasswordButton = document.getElementById("auth-password-button");
    const authDepartmentScheduleButton = document.getElementById("auth-department-schedule-button");
    const authAdminPageButton = document.getElementById("auth-admin-page-button");
    const authOverlay = document.getElementById("auth-overlay");
    const authSections = document.getElementById("auth-sections");
    const authOverlayCloseButton = document.getElementById("auth-overlay-close");
    const BING_DAILY_BACKGROUND_PATH = "/api/backgrounds/bing-daily";
    const authLocalUsernameInput = document.getElementById("auth-local-username");
    const authLocalPasswordInput = document.getElementById("auth-local-password");
    const authLocalSubmitButton = document.getElementById("auth-local-submit");
    const authLocalStatus = document.getElementById("auth-local-status");
    const authDialogSubtitle = document.getElementById("auth-dialog-subtitle");
    const dingtalkAuthSection = document.getElementById("dingtalk-auth-section");
    const dingtalkScanHint = document.getElementById("dingtalk-scan-hint");
    const dingtalkScanQrWrap = document.getElementById("dingtalk-scan-qr-wrap");
    const dingtalkScanStatus = document.getElementById("dingtalk-scan-status");
    const dingtalkScanLink = document.getElementById("dingtalk-scan-link");
    const startDingtalkScanLoginButton = document.getElementById("start-dingtalk-scan-login");
    const refreshDingtalkScanLoginButton = document.getElementById("refresh-dingtalk-scan-login");
    const passwordOverlay = document.getElementById("password-overlay");
    const passwordOverlayCloseButton = document.getElementById("password-overlay-close");
    const passwordDialogAccount = document.getElementById("password-dialog-account");
    const passwordCurrentInput = document.getElementById("password-current-input");
    const passwordNewInput = document.getElementById("password-new-input");
    const passwordConfirmInput = document.getElementById("password-confirm-input");
    const passwordSubmitButton = document.getElementById("password-submit-button");
    const passwordStatus = document.getElementById("password-status");
    const promptOverlay = document.getElementById("prompt-overlay");
    const promptOverlayCloseButton = document.getElementById("prompt-overlay-close");
    const promptTemplateSelect = document.getElementById("prompt-template-select");
    const promptTemplateScope = document.getElementById("prompt-template-scope");
    const promptTemplateFilename = document.getElementById("prompt-template-filename");
    const promptTemplateUpdatedAt = document.getElementById("prompt-template-updated-at");
    const promptTemplateDescription = document.getElementById("prompt-template-description");
    const promptTemplateContent = document.getElementById("prompt-template-content");
    const promptTemplateResetButton = document.getElementById("prompt-template-reset-button");
    const promptTemplateSaveButton = document.getElementById("prompt-template-save-button");
    const promptTemplateStatus = document.getElementById("prompt-template-status");
    const userDingtalkMcpOverlay = document.getElementById("user-dingtalk-mcp-overlay");
    const userDingtalkMcpOverlayCloseButton = document.getElementById("user-dingtalk-mcp-overlay-close");
    const userDingtalkMcpScope = document.getElementById("user-dingtalk-mcp-scope");
    const userDingtalkMcpLogState = document.getElementById("user-dingtalk-mcp-log-state");
    const userDingtalkMcpDirectoryState = document.getElementById("user-dingtalk-mcp-directory-state");
    const userDingtalkMcpDailyTemplateState = document.getElementById("user-dingtalk-mcp-daily-template-state");
    const userDingtalkMcpWeeklyTemplateState = document.getElementById("user-dingtalk-mcp-weekly-template-state");
    const userDingtalkMcpUpdatedAt = document.getElementById("user-dingtalk-mcp-updated-at");
    const userDingtalkMcpDescription = document.getElementById("user-dingtalk-mcp-description");
    const userDingtalkLogMcpInput = document.getElementById("user-dingtalk-log-mcp-input");
    const userDingtalkDirectoryMcpInput = document.getElementById("user-dingtalk-directory-mcp-input");
    const userDingtalkMcpLoadTemplatesButton = document.getElementById("user-dingtalk-mcp-load-templates-button");
    const userDingtalkDailyTemplateSelect = document.getElementById("user-dingtalk-daily-template-select");
    const userDingtalkWeeklyTemplateSelect = document.getElementById("user-dingtalk-weekly-template-select");
    const userDingtalkMcpResetButton = document.getElementById("user-dingtalk-mcp-reset-button");
    const userDingtalkMcpSaveButton = document.getElementById("user-dingtalk-mcp-save-button");
    const userDingtalkMcpStatus = document.getElementById("user-dingtalk-mcp-status");

    const addRowButton = document.getElementById("add-row");
    const reloadButton = document.getElementById("reload-date");
    const clearButton = document.getElementById("clear-form");
    const deleteButton = document.getElementById("delete-entry");
    const saveButton = document.getElementById("save-entry");
    const exportDailyLogButton = document.getElementById("export-daily-log");
    const exportWeeklyReportButton = document.getElementById("export-weekly-report");
    const exportWeeklyStrengthButton = document.getElementById("export-weekly-strength");
    const showDeliveryProgressButton = document.getElementById("show-delivery-progress");
    const refreshMonthButton = document.getElementById("refresh-month");
    const exportMonthButton = document.getElementById("export-month");
    const deliveryProgressOverlay = document.getElementById("delivery-progress-overlay");
    const deliveryProgressCloseButton = document.getElementById("delivery-progress-close");
    const deliveryProgressRegenerateButton = document.getElementById("delivery-progress-regenerate");
    const deliveryProgressMeta = document.getElementById("delivery-progress-meta");
    const deliveryProgressList = document.getElementById("delivery-progress-list");
    const deliveryProgressSubtitle = document.getElementById("delivery-progress-subtitle");
    const previewOverlay = document.getElementById("preview-overlay");
    const previewSendLogButton = document.getElementById("preview-send-log");
    const previewDownloadLogButton = document.getElementById("preview-download-log");
    const previewCloseButton = document.getElementById("preview-close");
    const previewMeta = document.getElementById("preview-meta");
    const previewContent = document.getElementById("preview-content");
    const previewTitle = document.getElementById("preview-title");
    const previewSubtitle = document.getElementById("preview-subtitle");
    const sendResultToast = document.getElementById("send-result-toast");
    const sendResultToastTitle = document.getElementById("send-result-toast-title");
    const sendResultToastMessage = document.getElementById("send-result-toast-message");
    const sendConfirmOverlay = document.getElementById("send-confirm-overlay");
    const sendConfirmContent = document.getElementById("send-confirm-content");
    const sendConfirmCloseButton = document.getElementById("send-confirm-close");
    const sendConfirmCancelButton = document.getElementById("send-confirm-cancel");
    const sendConfirmSubmitButton = document.getElementById("send-confirm-submit");
    const AUTO_THEME_DAY_START_HOUR = 6;
    const AUTO_THEME_NIGHT_START_HOUR = 19;
    const DEFAULT_STORAGE_SCOPE_TOKEN = "__default__";
    const DELIVERY_PROGRESS_CACHE_PREFIX = "delivery_progress_cache::";
    const LAST_SELECTED_DATE_STORAGE_PREFIX = "daily_planner_last_selected_date::";
    const DAILY_ENTRY_DRAFT_PREFIX = "daily_entry_draft::";
    const WEEKLY_PLAN_DRAFT_PREFIX = "weekly_plan_draft::";
    const WEEKLY_PLAN_SYNC_SIGNAL_STORAGE_KEY = "daily_planner_weekly_plan_sync_signal_v1";
    const WEEKLY_PLAN_AUTOSAVE_DELAY_MS = 800;
    const VISUAL_SETTINGS_AUTOSAVE_DELAY_MS = 260;
    const MAX_BACKGROUND_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
    let currentWeeklyPlanWeekStart = "";
    let weeklyPlanAutosaveTimer = null;
    let visualSettingsAutosaveTimer = null;
    let weeklyPlanSaveSequence = 0;
    let isBackgroundSettingsOpen = false;
    let isDeliveryProgressOpen = false;
    let isDeliveryProgressLoading = false;
    let isPreviewOpen = false;
    let isSendConfirmOpen = false;
    let isSendingDailyLog = false;
    let isAuthOverlayOpen = false;
    let isPasswordOverlayOpen = false;
    let isPromptOverlayOpen = false;
    let isUserDingtalkMcpOverlayOpen = false;
    let dailyLogEditorState = null;
    let sendResultToastTimer = null;
    let backgroundStretchFrame = 0;
    let currentEditorWorkDate = dateInput.value;
    let currentUiSettings = normalizeUiSettings(initialUiSettings);
    let knownCustomerNames = [];
    let knownCustomerProfiles = {};
    let authState = {
      authenticated: false,
      user: null,
      users: [],
      isAdmin: false,
      isDepartmentAdmin: false,
      scopeUserId: ""
    };
    let dingtalkAuthConfig = {
      enabled: false,
      configured: false,
      allow_org_auto_login: false,
      redirect_base_url: "",
      effective_redirect_base_url: "",
      callback_url: "",
      scan_qr_supported: false
    };
    let promptEditorState = {
      loaded: false,
      loading: false,
      saving: false,
      prompts: [],
      selectedPromptId: ""
    };
    let userDingtalkMcpState = {
      loaded: false,
      loading: false,
      saving: false,
      templatesLoaded: false,
      templatesLoading: false,
      availableTemplates: [],
      config: null,
      savedConfig: null
    };
    let currentDingtalkScanSessionId = "";
    let dingtalkScanPollTimer = null;
    const savedEntrySnapshots = new Map();
    const weeklyPlanSavedSnapshots = new Map();
    const weeklyPlanSavedUpdatedAts = new Map();
    const weeklyPlanLatestRequestIds = new Map();
    let scopedAsyncRequestSequence = 0;
    let scopeAsyncGeneration = 0;
    const latestScopedAsyncRequests = new Map();
    let previewSessionCounter = 0;
    let activePreviewSessionId = 0;
    let activeSendOperationId = 0;
    let deliveryProgressSessionCounter = 0;
    let activeDeliveryProgressSessionId = 0;
    const weeklyScheduleInputs = {
      weekly_monday_am: document.getElementById("weekly-monday-am"),
      weekly_monday_pm: document.getElementById("weekly-monday-pm"),
      weekly_tuesday_am: document.getElementById("weekly-tuesday-am"),
      weekly_tuesday_pm: document.getElementById("weekly-tuesday-pm"),
      weekly_wednesday_am: document.getElementById("weekly-wednesday-am"),
      weekly_wednesday_pm: document.getElementById("weekly-wednesday-pm"),
      weekly_thursday_am: document.getElementById("weekly-thursday-am"),
      weekly_thursday_pm: document.getElementById("weekly-thursday-pm"),
      weekly_friday_am: document.getElementById("weekly-friday-am"),
      weekly_friday_pm: document.getElementById("weekly-friday-pm"),
      weekly_saturday_am: document.getElementById("weekly-saturday-am"),
      weekly_saturday_pm: document.getElementById("weekly-saturday-pm"),
      weekly_sunday_am: document.getElementById("weekly-sunday-am"),
      weekly_sunday_pm: document.getElementById("weekly-sunday-pm"),
      weekly_other_pending: document.getElementById("weekly-other-pending")
    };

    function initializePasswordToggleFields() {
      document.querySelectorAll('input[type="password"][data-password-toggle]').forEach((input) => {
        if (!(input instanceof HTMLInputElement) || input.dataset.passwordToggleReady === "true") {
          return;
        }
        const parent = input.parentNode;
        if (!parent) {
          return;
        }
        input.dataset.passwordToggleReady = "true";
        const wrapper = document.createElement("span");
        wrapper.className = "password-input-wrap";
        parent.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        const toggleButton = document.createElement("button");
        toggleButton.type = "button";
        toggleButton.className = "password-toggle-btn";
        toggleButton.innerHTML = '<span aria-hidden="true">&#128065;</span>';
        if (input.id) {
          toggleButton.setAttribute("aria-controls", input.id);
        }
        const syncToggleState = () => {
          const isVisible = input.type === "text";
          toggleButton.classList.toggle("is-visible", isVisible);
          toggleButton.setAttribute("aria-pressed", isVisible ? "true" : "false");
          const label = isVisible ? "隐藏密码" : "显示密码";
          toggleButton.setAttribute("aria-label", label);
          toggleButton.title = label;
        };
        toggleButton.addEventListener("mousedown", (event) => {
          event.preventDefault();
        });
        toggleButton.addEventListener("click", () => {
          const selectionStart = typeof input.selectionStart === "number" ? input.selectionStart : null;
          const selectionEnd = typeof input.selectionEnd === "number" ? input.selectionEnd : null;
          input.type = input.type === "password" ? "text" : "password";
          syncToggleState();
          input.focus({ preventScroll: true });
          if (selectionStart !== null && selectionEnd !== null) {
            try {
              input.setSelectionRange(selectionStart, selectionEnd);
            } catch (error) {
              // Ignore inputs that do not allow cursor restoration.
            }
          }
        });
        wrapper.appendChild(toggleButton);
        syncToggleState();
      });
    }

    function firstDefinedValue() {
      for (let index = 0; index < arguments.length; index += 1) {
        const value = arguments[index];
        if (value !== undefined && value !== null) {
          return value;
        }
      }
      return undefined;
    }

    function replaceLiteral(value, search, replacement) {
      return String(value).split(search).join(replacement);
    }

    function getActiveScopeUserId() {
      if (!authState.isAdmin) {
        return "";
      }
      const persistedScopeUserId = String(authState.scopeUserId || "").trim();
      if (persistedScopeUserId) {
        return persistedScopeUserId;
      }
      return String(authState.scopeUserId || authState.user && authState.user.user_id || "").trim();
    }

    function getCurrentScopeUser() {
      const currentUser = authState.user;
      if (!authState.authenticated || !currentUser) {
        return null;
      }
      const scopeUserId = getActiveScopeUserId();
      if (!authState.isAdmin || !scopeUserId) {
        return currentUser;
      }
      const matchedUser = (Array.isArray(authState.users) ? authState.users : []).find(
        (item) => String(item && item.user_id || "").trim() === scopeUserId
      );
      return matchedUser || currentUser;
    }

    function getStorageScopeToken() {
      const scopeUser = getCurrentScopeUser();
      const scopeUserId = String(
        scopeUser && scopeUser.user_id || authState.user && authState.user.user_id || ""
      ).trim();
      return scopeUserId || DEFAULT_STORAGE_SCOPE_TOKEN;
    }

    function buildScopedStorageKey(prefix, suffix = "") {
      const scopeToken = getStorageScopeToken();
      return suffix ? `${prefix}${scopeToken}::${suffix}` : `${prefix}${scopeToken}`;
    }

    function getCurrentScopeAsyncMarker() {
      return `${getStorageScopeToken()}::${scopeAsyncGeneration}`;
    }

    function invalidateScopedAsyncRequests() {
      scopeAsyncGeneration += 1;
      latestScopedAsyncRequests.clear();
    }

    function registerScopedAsyncRequest(channel, identity = "") {
      const scopeMarker = getCurrentScopeAsyncMarker();
      const requestKey = `${channel}::${identity}::${scopeMarker}::${++scopedAsyncRequestSequence}`;
      latestScopedAsyncRequests.set(channel, requestKey);
      return { channel, requestKey, scopeMarker };
    }

    function isScopedAsyncRequestActive(requestMeta) {
      return Boolean(
        requestMeta
          && latestScopedAsyncRequests.get(requestMeta.channel) === requestMeta.requestKey
          && requestMeta.scopeMarker === getCurrentScopeAsyncMarker()
      );
    }

    function resetScopedInMemoryCaches() {
      savedEntrySnapshots.clear();
      weeklyPlanSavedSnapshots.clear();
      weeklyPlanSavedUpdatedAts.clear();
      weeklyPlanLatestRequestIds.clear();
    }

    function beginPreviewSession() {
      previewSessionCounter += 1;
      activePreviewSessionId = previewSessionCounter;
      activeSendOperationId = 0;
      dailyLogEditorState = null;
      setDailyLogSendState(false);
      if (sendResultToastTimer) {
        window.clearTimeout(sendResultToastTimer);
        sendResultToastTimer = null;
      }
      sendResultToast.hidden = true;
      syncPreviewActionButtons();
      return {
        previewSessionId: activePreviewSessionId,
        scopeMarker: getCurrentScopeAsyncMarker(),
      };
    }

    function isPreviewSessionActive(previewSessionId, scopeMarker) {
      return previewSessionId === activePreviewSessionId && scopeMarker === getCurrentScopeAsyncMarker();
    }

    function resetPreviewState(options = {}) {
      const closeOverlay = options.closeOverlay !== false;
      beginPreviewSession();
      renderPreviewMeta([]);
      if (isSendConfirmOpen) {
        isSendConfirmOpen = false;
        sendConfirmOverlay.hidden = true;
      }
      if (closeOverlay) {
        isPreviewOpen = false;
        previewOverlay.hidden = true;
      }
      updateBodyOverlayState();
    }

    function beginDeliveryProgressSession() {
      deliveryProgressSessionCounter += 1;
      activeDeliveryProgressSessionId = deliveryProgressSessionCounter;
      return {
        deliveryProgressSessionId: activeDeliveryProgressSessionId,
        scopeMarker: getCurrentScopeAsyncMarker(),
      };
    }

    function isDeliveryProgressSessionActive(deliveryProgressSessionId, scopeMarker) {
      return (
        deliveryProgressSessionId === activeDeliveryProgressSessionId
        && scopeMarker === getCurrentScopeAsyncMarker()
      );
    }

    function resetDeliveryProgressState(options = {}) {
      const closeOverlay = options.closeOverlay !== false;
      deliveryProgressSessionCounter += 1;
      activeDeliveryProgressSessionId = deliveryProgressSessionCounter;
      setDeliveryProgressLoading(false);
      if (closeOverlay) {
        isDeliveryProgressOpen = false;
        deliveryProgressOverlay.hidden = true;
      }
      deliveryProgressMeta.innerHTML = "";
      deliveryProgressList.innerHTML = "";
      updateBodyOverlayState();
    }

    function persistScopeLocalState() {
      const targetDate = isValidDateString(currentEditorWorkDate) ? currentEditorWorkDate : dateInput.value;
      if (isValidDateString(targetDate)) {
        rememberWorkDate(targetDate);
        saveDailyEntryDraft(targetDate, collectItems());
      }
      const weekStart = currentWeeklyPlanWeekStart || getWeekStartString(targetDate || dateInput.value);
      if (weekStart) {
        saveWeeklyPlanDraft(weekStart, getCurrentSettings());
      }
    }

    function prepareForScopeChange(options = {}) {
      if (options.persist !== false) {
        persistScopeLocalState();
      }
      cancelWeeklyPlanAutosave();
      cancelVisualSettingsAutosave();
      invalidateScopedAsyncRequests();
      resetScopedInMemoryCaches();
      resetPreviewState();
      resetDeliveryProgressState();
      if (isPasswordOverlayOpen) {
        closePasswordOverlay();
      }
      if (isPromptOverlayOpen) {
        closePromptOverlay();
      }
      if (isUserDingtalkMcpOverlayOpen) {
        closeUserDingtalkMcpOverlay();
      }
      if (isBackgroundSettingsOpen) {
        setBackgroundSettingsOpen(false);
      }
      resetPromptEditorState();
      resetUserDingtalkMcpEditorState();
      stopDingtalkScanPolling();
      currentDingtalkScanSessionId = "";
    }

    function canCurrentUserChangePassword() {
      const currentUser = authState.user;
      if (!authState.authenticated || !currentUser) {
        return false;
      }
      return String(currentUser.user_id || "").trim().startsWith("local");
    }

    function canAccessDepartmentSchedule() {
      return Boolean(authState.authenticated && authState.user);
    }

    function normalizeUserPromptTemplate(prompt) {
      const source = prompt && typeof prompt === "object" ? prompt : {};
      return {
        id: String(source.id || "").trim(),
        title: String(source.title || source.filename || "未命名提示词").trim(),
        description: String(source.description || "").trim(),
        filename: String(source.filename || "").trim(),
        content: String(source.content || ""),
        saved_content: String(source.content || ""),
        default_content: String(source.default_content || ""),
        updated_at: String(source.updated_at || "").trim(),
        customized: Boolean(source.customized),
      };
    }

    function resetPromptEditorState() {
      promptEditorState = {
        loaded: false,
        loading: false,
        saving: false,
        prompts: [],
        selectedPromptId: ""
      };
      setInlineStatus(promptTemplateStatus, "", false);
    }

    function getPromptEditorCurrentUserLabel() {
      const scopeUser = getCurrentScopeUser() || authState.user;
      if (!scopeUser) {
        return "当前用户专属";
      }
      return `当前用户：${scopeUser.display_name || scopeUser.user_id || "未命名用户"}`;
    }

    function getPromptEditorSelectedTemplate() {
      const selectedPromptId = String(promptEditorState.selectedPromptId || "").trim();
      if (selectedPromptId) {
        const matchedPrompt = promptEditorState.prompts.find((prompt) => prompt.id === selectedPromptId);
        if (matchedPrompt) {
          return matchedPrompt;
        }
      }
      return promptEditorState.prompts[0] || null;
    }

    function hasPromptEditorPendingChanges() {
      return promptEditorState.prompts.some((prompt) => String(prompt.content || "") !== String(prompt.saved_content || ""));
    }

    function buildPromptTemplateStateText(prompt) {
      if (!prompt) {
        return "暂无提示词";
      }
      if (String(prompt.content || "") !== String(prompt.saved_content || "")) {
        return String(prompt.content || "") === String(prompt.default_content || "")
          ? "已恢复默认，待保存"
          : "已修改，待保存";
      }
      if (String(prompt.saved_content || "") === String(prompt.default_content || "")) {
        return "当前使用系统默认";
      }
      return prompt.updated_at ? `最近保存：${prompt.updated_at}` : "当前使用自定义版本";
    }

    function renderPromptEditor() {
      promptTemplateScope.textContent = getPromptEditorCurrentUserLabel();
      const currentPrompt = getPromptEditorSelectedTemplate();
      const selectedPromptId = currentPrompt ? currentPrompt.id : "";
      if (selectedPromptId) {
        promptEditorState.selectedPromptId = selectedPromptId;
      }
      const optionMarkup = promptEditorState.prompts.length
        ? promptEditorState.prompts.map((prompt) => (
          `<option value="${escapeHtml(prompt.id)}">${escapeHtml(prompt.title)}</option>`
        )).join("")
        : '<option value="">暂无可编辑提示词</option>';
      if (promptTemplateSelect.innerHTML !== optionMarkup) {
        promptTemplateSelect.innerHTML = optionMarkup;
      }
      if (promptTemplateSelect.value !== selectedPromptId) {
        promptTemplateSelect.value = selectedPromptId;
      }

      if (!currentPrompt) {
        promptTemplateFilename.textContent = "提示词文件";
        promptTemplateUpdatedAt.textContent = promptEditorState.loading ? "正在加载提示词..." : "暂无可编辑提示词";
        promptTemplateDescription.textContent = promptEditorState.loading
          ? "正在读取当前用户的提示词配置，请稍候。"
          : "当前没有可编辑的提示词。";
        if (promptTemplateContent.value) {
          promptTemplateContent.value = "";
        }
        promptTemplateContent.placeholder = promptEditorState.loading ? "正在加载提示词..." : "暂无可编辑提示词";
      } else {
        promptTemplateFilename.textContent = `文件：${currentPrompt.filename}`;
        promptTemplateUpdatedAt.textContent = buildPromptTemplateStateText(currentPrompt);
        promptTemplateDescription.textContent = currentPrompt.description || "当前提示词未配置说明。";
        if (promptTemplateContent.value !== currentPrompt.content) {
          promptTemplateContent.value = currentPrompt.content;
        }
        promptTemplateContent.placeholder = "请输入提示词内容";
      }

      const contentDisabled = promptEditorState.loading || promptEditorState.saving || !currentPrompt;
      promptTemplateSelect.disabled = promptEditorState.loading || promptEditorState.saving || promptEditorState.prompts.length <= 1;
      promptTemplateContent.disabled = contentDisabled;
      promptTemplateResetButton.disabled = contentDisabled || String(currentPrompt && currentPrompt.content || "") === String(currentPrompt && currentPrompt.default_content || "");
      promptTemplateSaveButton.disabled = promptEditorState.loading || promptEditorState.saving || !currentPrompt || !hasPromptEditorPendingChanges();
    }

    async function loadPromptEditorTemplates(force = false) {
      if (promptEditorState.loading || (promptEditorState.loaded && !force)) {
        renderPromptEditor();
        return;
      }
      promptEditorState.loading = true;
      renderPromptEditor();
      setInlineStatus(promptTemplateStatus, "正在加载提示词...", false);
      try {
        const response = await fetch("/api/user-prompts");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取提示词失败");
        }
        const previousPromptId = String(promptEditorState.selectedPromptId || "").trim();
        promptEditorState.prompts = (Array.isArray(payload.prompts) ? payload.prompts : []).map((prompt) => normalizeUserPromptTemplate(prompt));
        promptEditorState.selectedPromptId = promptEditorState.prompts.some((prompt) => prompt.id === previousPromptId)
          ? previousPromptId
          : (promptEditorState.prompts[0] && promptEditorState.prompts[0].id || "");
        promptEditorState.loaded = true;
        setInlineStatus(promptTemplateStatus, "", false);
      } catch (error) {
        promptEditorState.prompts = [];
        promptEditorState.selectedPromptId = "";
        promptEditorState.loaded = false;
        setInlineStatus(promptTemplateStatus, error.message || "读取提示词失败。", true);
      } finally {
        promptEditorState.loading = false;
        renderPromptEditor();
      }
    }

    function openPromptOverlay() {
      if (!(authState.authenticated && authState.user)) {
        return;
      }
      isPromptOverlayOpen = true;
      promptOverlay.hidden = false;
      updateBodyOverlayState();
      renderPromptEditor();
      loadPromptEditorTemplates().catch(() => {});
      window.setTimeout(() => {
        if (!promptTemplateSelect.disabled) {
          promptTemplateSelect.focus();
        } else {
          promptTemplateContent.focus();
        }
      }, 0);
    }

    function closePromptOverlay() {
      isPromptOverlayOpen = false;
      promptOverlay.hidden = true;
      updateBodyOverlayState();
    }

    function restoreSelectedPromptTemplateDefault() {
      const currentPrompt = getPromptEditorSelectedTemplate();
      if (!currentPrompt) {
        return;
      }
      currentPrompt.content = String(currentPrompt.default_content || "");
      setInlineStatus(promptTemplateStatus, "已恢复为系统默认内容，点击“保存提示词”后生效。", false);
      renderPromptEditor();
    }

    async function savePromptEditorTemplates() {
      const currentPrompt = getPromptEditorSelectedTemplate();
      if (!currentPrompt || promptEditorState.saving || !hasPromptEditorPendingChanges()) {
        return;
      }
      promptEditorState.saving = true;
      renderPromptEditor();
      setInlineStatus(promptTemplateStatus, "正在保存提示词...", false);
      try {
        const response = await fetch("/api/user-prompts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompts: promptEditorState.prompts.map((prompt) => ({
              id: prompt.id,
              content: prompt.content,
            })),
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "保存提示词失败");
        }
        const selectedPromptId = String(promptEditorState.selectedPromptId || currentPrompt.id || "").trim();
        promptEditorState.prompts = (Array.isArray(payload.prompts) ? payload.prompts : []).map((prompt) => normalizeUserPromptTemplate(prompt));
        promptEditorState.selectedPromptId = promptEditorState.prompts.some((prompt) => prompt.id === selectedPromptId)
          ? selectedPromptId
          : (promptEditorState.prompts[0] && promptEditorState.prompts[0].id || "");
        promptEditorState.loaded = true;
        setInlineStatus(promptTemplateStatus, "提示词已保存，仅对当前用户生效。", false);
      } catch (error) {
        setInlineStatus(promptTemplateStatus, error.message || "保存提示词失败。", true);
      } finally {
        promptEditorState.saving = false;
        renderPromptEditor();
      }
    }

    function normalizeUserDingtalkTemplateConfig(template) {
      const source = template && typeof template === "object" ? template : {};
      const fields = Array.isArray(source.fields)
        ? source.fields
          .map((field) => ({
            field_name: String(field && field.field_name || "").trim(),
            field_sort: Number(field && field.field_sort || 0) || 0,
            field_type: Number(field && field.field_type || 0) || 0
          }))
          .filter((field) => field.field_name)
          .sort((left, right) => (
            left.field_sort - right.field_sort
            || String(left.field_name).localeCompare(String(right.field_name), "zh-Hans-CN")
          ))
        : [];
      return {
        template_id: String(source.template_id || source.templateId || "").trim(),
        template_name: String(source.template_name || source.templateName || source.name || "").trim(),
        fields,
        field_count: Number(source.field_count || fields.length || 0) || fields.length || 0,
        daily_supported: Boolean(source.daily_supported),
        daily_support_error: String(source.daily_support_error || "").trim(),
        weekly_supported: Boolean(source.weekly_supported),
        weekly_support_error: String(source.weekly_support_error || "").trim(),
        source: String(source.source || "").trim()
      };
    }

    function buildUserDingtalkTemplatePayload(template) {
      const normalized = normalizeUserDingtalkTemplateConfig(template);
      if (!normalized.template_id && !normalized.template_name && !normalized.fields.length) {
        return {};
      }
      return {
        template_id: normalized.template_id,
        template_name: normalized.template_name,
        fields: normalized.fields.map((field) => ({
          field_name: String(field.field_name || "").trim(),
          field_sort: Number(field.field_sort || 0) || 0,
          field_type: Number(field.field_type || 0) || 0
        }))
      };
    }

    function normalizeUserDingtalkMcpEditorConfig(config) {
      const source = config && typeof config === "object" ? config : {};
      return {
        user_id: String(source.user_id || "").trim(),
        display_name: String(source.display_name || "").trim(),
        log_mcp_url: String(source.log_mcp_url || "").trim(),
        directory_mcp_url: String(source.directory_mcp_url || "").trim(),
        daily_template: normalizeUserDingtalkTemplateConfig(source.daily_template),
        weekly_template: normalizeUserDingtalkTemplateConfig(source.weekly_template),
        effective_daily_template: normalizeUserDingtalkTemplateConfig(source.effective_daily_template),
        effective_weekly_template: normalizeUserDingtalkTemplateConfig(source.effective_weekly_template),
        daily_template_source: String(source.daily_template_source || "missing").trim() || "missing",
        weekly_template_source: String(source.weekly_template_source || "missing").trim() || "missing",
        uses_custom_log_mcp: Boolean(source.uses_custom_log_mcp),
        uses_custom_directory_mcp: Boolean(source.uses_custom_directory_mcp),
        log_mcp_source: String(source.log_mcp_source || "missing").trim() || "missing",
        directory_mcp_source: String(source.directory_mcp_source || "missing").trim() || "missing",
        updated_at: String(source.updated_at || "").trim(),
      };
    }

    function cloneUserDingtalkMcpEditorConfig(config) {
      return config ? JSON.parse(JSON.stringify(config)) : null;
    }

    function isUserDingtalkTemplateEmpty(template) {
      const normalized = normalizeUserDingtalkTemplateConfig(template);
      return !normalized.template_id && !normalized.template_name && !normalized.fields.length;
    }

    function buildUserDingtalkTemplateSelectionValue(template) {
      const normalized = normalizeUserDingtalkTemplateConfig(template);
      return String(normalized.template_id || normalized.template_name || "").trim();
    }

    function buildUserDingtalkMcpComparableConfig(config) {
      const source = config && typeof config === "object" ? config : {};
      return {
        log_mcp_url: String(source.log_mcp_url || "").trim(),
        directory_mcp_url: String(source.directory_mcp_url || "").trim(),
        daily_template: buildUserDingtalkTemplatePayload(source.daily_template),
        weekly_template: buildUserDingtalkTemplatePayload(source.weekly_template)
      };
    }

    function resetUserDingtalkMcpEditorState() {
      userDingtalkMcpState = {
        loaded: false,
        loading: false,
        saving: false,
        templatesLoaded: false,
        templatesLoading: false,
        availableTemplates: [],
        config: null,
        savedConfig: null
      };
      setInlineStatus(userDingtalkMcpStatus, "", false);
    }

    function getUserDingtalkMcpCurrentUserLabel() {
      const currentUser = authState.user;
      if (!currentUser) {
        return "当前用户专属";
      }
      return `当前用户：${currentUser.display_name || currentUser.user_id || "未命名用户"}`;
    }

    function hasUserDingtalkMcpPendingChanges() {
      const currentConfig = userDingtalkMcpState.config;
      const savedConfig = userDingtalkMcpState.savedConfig;
      if (!currentConfig || !savedConfig) {
        return false;
      }
      return JSON.stringify(buildUserDingtalkMcpComparableConfig(currentConfig))
        !== JSON.stringify(buildUserDingtalkMcpComparableConfig(savedConfig));
    }

    function hasUserDingtalkLogMcpPendingChanges() {
      const currentConfig = userDingtalkMcpState.config;
      const savedConfig = userDingtalkMcpState.savedConfig;
      if (!currentConfig || !savedConfig) {
        return false;
      }
      return String(currentConfig.log_mcp_url || "") !== String(savedConfig.log_mcp_url || "");
    }

    function describeEffectiveMcpSource(source) {
      if (source === "user") {
        return "当前用户自定义";
      }
      return "未配置";
    }

    function getUserDingtalkTemplateDisplayName(template, fallbackText = "未选择") {
      const normalized = normalizeUserDingtalkTemplateConfig(template);
      return normalized.template_name || normalized.template_id || fallbackText;
    }

    function buildUserDingtalkTemplateStateLabel(config, kind) {
      const isDaily = kind === "daily";
      const label = isDaily ? "日报模板" : "周报模板";
      const selectedTemplate = normalizeUserDingtalkTemplateConfig(
        isDaily ? config && config.daily_template : config && config.weekly_template
      );
      if (!isUserDingtalkTemplateEmpty(selectedTemplate)) {
        return `${label}：已选 ${getUserDingtalkTemplateDisplayName(selectedTemplate, "未命名模板")}`;
      }
      return `${label}：未选择`;
    }

    function collectUserDingtalkTemplateOptions(kind, currentConfig) {
      const isDaily = kind === "daily";
      const selectedTemplate = normalizeUserDingtalkTemplateConfig(
        isDaily ? currentConfig && currentConfig.daily_template : currentConfig && currentConfig.weekly_template
      );
      const options = [];
      const seen = new Set();
      const templates = Array.isArray(userDingtalkMcpState.availableTemplates) ? userDingtalkMcpState.availableTemplates : [];
      templates.forEach((template) => {
        const normalized = normalizeUserDingtalkTemplateConfig(template);
        const supported = isDaily ? normalized.daily_supported : normalized.weekly_supported;
        const value = buildUserDingtalkTemplateSelectionValue(normalized);
        if (!supported || !value || seen.has(value)) {
          return;
        }
        seen.add(value);
        options.push(normalized);
      });
      if (!isUserDingtalkTemplateEmpty(selectedTemplate)) {
        const selectedValue = buildUserDingtalkTemplateSelectionValue(selectedTemplate);
        if (selectedValue && !seen.has(selectedValue)) {
          seen.add(selectedValue);
          options.unshift({
            ...selectedTemplate,
            detached: true
          });
        }
      }
      return options;
    }

    function renderUserDingtalkTemplateSelect(selectElement, kind, currentConfig) {
      const isDaily = kind === "daily";
      const placeholderText = isDaily ? "请选择日报模板" : "请选择周报模板";
      const selectedTemplate = normalizeUserDingtalkTemplateConfig(
        isDaily ? currentConfig && currentConfig.daily_template : currentConfig && currentConfig.weekly_template
      );
      const selectedValue = isUserDingtalkTemplateEmpty(selectedTemplate)
        ? ""
        : buildUserDingtalkTemplateSelectionValue(selectedTemplate);
      const options = collectUserDingtalkTemplateOptions(kind, currentConfig);
      selectElement.textContent = "";

      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = placeholderText;
      selectElement.appendChild(defaultOption);

      options.forEach((template) => {
        const option = document.createElement("option");
        option.value = buildUserDingtalkTemplateSelectionValue(template);
        option.textContent = `${template.detached ? "已保存：" : ""}${getUserDingtalkTemplateDisplayName(template, "未命名模板")}`;
        selectElement.appendChild(option);
      });

      selectElement.value = selectedValue;
    }

    function buildUserDingtalkMcpStateText(config) {
      if (!config) {
        return "暂无配置";
      }
      const hasTemplateSelection = !isUserDingtalkTemplateEmpty(config.daily_template)
        || !isUserDingtalkTemplateEmpty(config.weekly_template);
      if (hasUserDingtalkMcpPendingChanges()) {
        return config.log_mcp_url || config.directory_mcp_url || hasTemplateSelection
          ? "已修改，待保存"
          : "已清空配置，待保存";
      }
      if (!config.log_mcp_url && !config.directory_mcp_url && !hasTemplateSelection) {
        return "当前未配置";
      }
      return config.updated_at ? `最近保存：${config.updated_at}` : "当前使用自定义版本";
    }

    function renderUserDingtalkMcpEditor() {
      userDingtalkMcpScope.textContent = getUserDingtalkMcpCurrentUserLabel();
      const currentConfig = userDingtalkMcpState.config;
      if (!currentConfig) {
        userDingtalkMcpLogState.textContent = userDingtalkMcpState.loading ? "日志发送：正在加载" : "日志发送：未配置";
        userDingtalkMcpDirectoryState.textContent = userDingtalkMcpState.loading ? "通讯录查询：正在加载" : "通讯录查询：未配置";
        userDingtalkMcpDailyTemplateState.textContent = userDingtalkMcpState.loading ? "日报模板：正在加载" : "日报模板：未选择";
        userDingtalkMcpWeeklyTemplateState.textContent = userDingtalkMcpState.loading ? "周报模板：正在加载" : "周报模板：未选择";
        userDingtalkMcpUpdatedAt.textContent = userDingtalkMcpState.loading ? "正在加载配置..." : "当前未配置";
        userDingtalkMcpDescription.textContent = userDingtalkMcpState.loading
          ? "正在读取当前用户的钉钉 MCP 配置，请稍候。"
          : "请填写当前用户要使用的钉钉 MCP 地址；保存后可读取该 MCP 可见的日志模板，并分别选择日报与周报模板。";
        if (userDingtalkLogMcpInput.value) {
          userDingtalkLogMcpInput.value = "";
        }
        if (userDingtalkDirectoryMcpInput.value) {
          userDingtalkDirectoryMcpInput.value = "";
        }
      } else {
        if (userDingtalkLogMcpInput.value !== currentConfig.log_mcp_url) {
          userDingtalkLogMcpInput.value = currentConfig.log_mcp_url;
        }
        if (userDingtalkDirectoryMcpInput.value !== currentConfig.directory_mcp_url) {
          userDingtalkDirectoryMcpInput.value = currentConfig.directory_mcp_url;
        }
        userDingtalkMcpLogState.textContent = currentConfig.log_mcp_url
          ? "日志发送：当前用户自定义"
          : `日志发送：${describeEffectiveMcpSource(currentConfig.log_mcp_source)}`;
        userDingtalkMcpDirectoryState.textContent = currentConfig.directory_mcp_url
          ? "通讯录查询：当前用户自定义"
          : `通讯录查询：${describeEffectiveMcpSource(currentConfig.directory_mcp_source)}`;
        userDingtalkMcpDailyTemplateState.textContent = buildUserDingtalkTemplateStateLabel(currentConfig, "daily");
        userDingtalkMcpWeeklyTemplateState.textContent = buildUserDingtalkTemplateStateLabel(currentConfig, "weekly");
        userDingtalkMcpUpdatedAt.textContent = buildUserDingtalkMcpStateText(currentConfig);
        if (hasUserDingtalkLogMcpPendingChanges() && currentConfig.log_mcp_url) {
          userDingtalkMcpDescription.textContent = "日志发送 MCP 地址已修改，保存后会清空已选模板；请重新读取并选择日报、周报模板。";
        } else if (!currentConfig.log_mcp_url) {
          userDingtalkMcpDescription.textContent = "请先填写并保存“日志发送 MCP 地址”，再读取模板；未选择模板时将无法发送日报或周报。";
        } else {
          userDingtalkMcpDescription.textContent = "每个用户单独维护自己的钉钉 MCP 地址和日志模板；当前仅支持选择纯文本字段的 4 段日报模板、5 段周报模板，未选择时禁止发送。";
        }
      }

      renderUserDingtalkTemplateSelect(userDingtalkDailyTemplateSelect, "daily", currentConfig);
      renderUserDingtalkTemplateSelect(userDingtalkWeeklyTemplateSelect, "weekly", currentConfig);

      const inputsDisabled = userDingtalkMcpState.loading || userDingtalkMcpState.saving || !currentConfig;
      const dailyTemplateEmpty = isUserDingtalkTemplateEmpty(currentConfig && currentConfig.daily_template);
      const weeklyTemplateEmpty = isUserDingtalkTemplateEmpty(currentConfig && currentConfig.weekly_template);
      const hasAvailableTemplates = Array.isArray(userDingtalkMcpState.availableTemplates)
        && userDingtalkMcpState.availableTemplates.length > 0;
      userDingtalkLogMcpInput.disabled = inputsDisabled;
      userDingtalkDirectoryMcpInput.disabled = inputsDisabled;
      userDingtalkMcpLoadTemplatesButton.disabled = (
        userDingtalkMcpState.loading
        || userDingtalkMcpState.saving
        || userDingtalkMcpState.templatesLoading
        || !currentConfig
        || !currentConfig.log_mcp_url
        || hasUserDingtalkLogMcpPendingChanges()
      );
      userDingtalkMcpLoadTemplatesButton.textContent = userDingtalkMcpState.templatesLoading ? "正在读取模板..." : "读取模板";
      userDingtalkDailyTemplateSelect.disabled = inputsDisabled || (!hasAvailableTemplates && dailyTemplateEmpty);
      userDingtalkWeeklyTemplateSelect.disabled = inputsDisabled || (!hasAvailableTemplates && weeklyTemplateEmpty);
      userDingtalkMcpResetButton.disabled = inputsDisabled || (
        !currentConfig.log_mcp_url
        && !currentConfig.directory_mcp_url
        && dailyTemplateEmpty
        && weeklyTemplateEmpty
      );
      userDingtalkMcpSaveButton.disabled = (
        userDingtalkMcpState.loading
        || userDingtalkMcpState.saving
        || !currentConfig
        || !hasUserDingtalkMcpPendingChanges()
      );
    }

    async function loadUserDingtalkMcpConfig(force = false) {
      if (userDingtalkMcpState.loading || (userDingtalkMcpState.loaded && !force)) {
        renderUserDingtalkMcpEditor();
        return;
      }
      userDingtalkMcpState.loading = true;
      renderUserDingtalkMcpEditor();
      setInlineStatus(userDingtalkMcpStatus, "正在加载钉钉 MCP 配置...", false);
      try {
        const previousLogMcpUrl = userDingtalkMcpState.savedConfig
          ? String(userDingtalkMcpState.savedConfig.log_mcp_url || "")
          : "";
        const response = await fetch("/api/user-dingtalk-mcp");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取钉钉 MCP 配置失败");
        }
        const normalizedConfig = normalizeUserDingtalkMcpEditorConfig(payload.config || {});
        if (String(normalizedConfig.log_mcp_url || "") !== previousLogMcpUrl) {
          userDingtalkMcpState.availableTemplates = [];
          userDingtalkMcpState.templatesLoaded = false;
        }
        userDingtalkMcpState.config = normalizedConfig;
        userDingtalkMcpState.savedConfig = cloneUserDingtalkMcpEditorConfig(normalizedConfig);
        userDingtalkMcpState.loaded = true;
        setInlineStatus(userDingtalkMcpStatus, "", false);
      } catch (error) {
        userDingtalkMcpState.config = null;
        userDingtalkMcpState.savedConfig = null;
        userDingtalkMcpState.loaded = false;
        userDingtalkMcpState.availableTemplates = [];
        userDingtalkMcpState.templatesLoaded = false;
        setInlineStatus(userDingtalkMcpStatus, error.message || "读取钉钉 MCP 配置失败。", true);
      } finally {
        userDingtalkMcpState.loading = false;
        renderUserDingtalkMcpEditor();
      }
    }

    async function loadUserDingtalkReportTemplates(force = false) {
      const currentConfig = userDingtalkMcpState.config;
      if (!currentConfig || userDingtalkMcpState.templatesLoading || (userDingtalkMcpState.templatesLoaded && !force)) {
        renderUserDingtalkMcpEditor();
        return;
      }
      if (hasUserDingtalkLogMcpPendingChanges()) {
        setInlineStatus(userDingtalkMcpStatus, "日志发送 MCP 地址已修改，请先保存后再读取模板。", true);
        renderUserDingtalkMcpEditor();
        return;
      }
      if (!currentConfig.log_mcp_url) {
        setInlineStatus(userDingtalkMcpStatus, "请先配置并保存日志发送 MCP 地址，再读取模板。", true);
        renderUserDingtalkMcpEditor();
        return;
      }
      userDingtalkMcpState.templatesLoading = true;
      renderUserDingtalkMcpEditor();
      setInlineStatus(userDingtalkMcpStatus, "正在读取当前用户可见的钉钉日志模板...", false);
      try {
        const response = await fetch("/api/user-dingtalk-report-templates");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取日志模板失败");
        }
        const templates = Array.isArray(payload.templates)
          ? payload.templates.map((template) => normalizeUserDingtalkTemplateConfig(template))
          : [];
        userDingtalkMcpState.availableTemplates = templates;
        userDingtalkMcpState.templatesLoaded = true;
        const dailyCount = templates.filter((template) => template.daily_supported).length;
        const weeklyCount = templates.filter((template) => template.weekly_supported).length;
        setInlineStatus(
          userDingtalkMcpStatus,
          `已读取 ${templates.length} 个模板，可用于日报 ${dailyCount} 个、周报 ${weeklyCount} 个。`,
          false
        );
      } catch (error) {
        setInlineStatus(userDingtalkMcpStatus, error.message || "读取日志模板失败。", true);
      } finally {
        userDingtalkMcpState.templatesLoading = false;
        renderUserDingtalkMcpEditor();
      }
    }

    function openUserDingtalkMcpOverlay() {
      if (!(authState.authenticated && authState.user)) {
        return;
      }
      isUserDingtalkMcpOverlayOpen = true;
      userDingtalkMcpOverlay.hidden = false;
      updateBodyOverlayState();
      renderUserDingtalkMcpEditor();
      loadUserDingtalkMcpConfig().catch(() => {});
      window.setTimeout(() => {
        if (!userDingtalkLogMcpInput.disabled) {
          userDingtalkLogMcpInput.focus();
        }
      }, 0);
    }

    function closeUserDingtalkMcpOverlay() {
      isUserDingtalkMcpOverlayOpen = false;
      userDingtalkMcpOverlay.hidden = true;
      updateBodyOverlayState();
    }

    function restoreUserDingtalkMcpConfigDefault() {
      if (!userDingtalkMcpState.config) {
        return;
      }
      userDingtalkMcpState.config.log_mcp_url = "";
      userDingtalkMcpState.config.directory_mcp_url = "";
      userDingtalkMcpState.config.daily_template = normalizeUserDingtalkTemplateConfig({});
      userDingtalkMcpState.config.weekly_template = normalizeUserDingtalkTemplateConfig({});
      setInlineStatus(userDingtalkMcpStatus, "已清空 MCP 地址和模板选择，点击“保存配置”后生效。", false);
      renderUserDingtalkMcpEditor();
    }

    async function saveUserDingtalkMcpEditorConfig() {
      const currentConfig = userDingtalkMcpState.config;
      if (!currentConfig || userDingtalkMcpState.saving || !hasUserDingtalkMcpPendingChanges()) {
        return;
      }
      const previousSavedLogMcpUrl = userDingtalkMcpState.savedConfig
        ? String(userDingtalkMcpState.savedConfig.log_mcp_url || "")
        : "";
      userDingtalkMcpState.saving = true;
      renderUserDingtalkMcpEditor();
      setInlineStatus(userDingtalkMcpStatus, "正在保存钉钉 MCP 配置...", false);
      try {
        const response = await fetch("/api/user-dingtalk-mcp", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            log_mcp_url: String(currentConfig.log_mcp_url || "").trim(),
            directory_mcp_url: String(currentConfig.directory_mcp_url || "").trim(),
            daily_template: buildUserDingtalkTemplatePayload(currentConfig.daily_template),
            weekly_template: buildUserDingtalkTemplatePayload(currentConfig.weekly_template),
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "保存钉钉 MCP 配置失败");
        }
        const normalizedConfig = normalizeUserDingtalkMcpEditorConfig(payload.config || {});
        if (String(normalizedConfig.log_mcp_url || "") !== previousSavedLogMcpUrl) {
          userDingtalkMcpState.availableTemplates = [];
          userDingtalkMcpState.templatesLoaded = false;
        }
        userDingtalkMcpState.config = normalizedConfig;
        userDingtalkMcpState.savedConfig = cloneUserDingtalkMcpEditorConfig(normalizedConfig);
        userDingtalkMcpState.loaded = true;
        setInlineStatus(userDingtalkMcpStatus, "钉钉 MCP 与模板配置已保存，仅对当前用户生效。", false);
      } catch (error) {
        setInlineStatus(userDingtalkMcpStatus, error.message || "保存钉钉 MCP 配置失败。", true);
      } finally {
        userDingtalkMcpState.saving = false;
        renderUserDingtalkMcpEditor();
      }
    }

    function renderPageUserBadge() {
      const currentUser = authState.user;
      const scopeUser = getCurrentScopeUser() || currentUser;
      if (!authState.authenticated || !currentUser) {
        pageUserBadgeLabel.textContent = "当前用户";
        pageUserDisplayName.textContent = "默认用户";
        pageUserDisplayMeta.textContent = "未登录 · 默认用户模式";
        return;
      }
      const scopeDisplayName = String(scopeUser.display_name || scopeUser.user_id || "未命名用户").trim();
      const scopeUserId = String(scopeUser.user_id || "").trim();
      const loginDisplayName = String(currentUser.display_name || currentUser.user_id || "未命名用户").trim();
      const isViewingOtherUser = authState.isAdmin && scopeUserId && scopeUserId !== String(currentUser.user_id || "").trim();

      pageUserBadgeLabel.textContent = isViewingOtherUser ? "当前查看用户" : "当前用户";
      pageUserDisplayName.textContent = scopeDisplayName || scopeUserId || "未命名用户";
      if (isViewingOtherUser) {
        pageUserDisplayMeta.textContent = `登录身份：${loginDisplayName}（管理员） · 用户ID：${scopeUserId || "未记录"}`;
      } else {
        const roleText = authState.isAdmin
          ? "管理员"
          : (authState.isDepartmentAdmin ? "部门管理员" : "普通用户");
        pageUserDisplayMeta.textContent = `${roleText} · 用户ID：${scopeUserId || String(currentUser.user_id || "").trim() || "未记录"}`;
      }
    }

    const nativeFetch = window.fetch.bind(window);
    window.fetch = (input, init) => {
      const requestUrl = typeof input === "string"
        ? new URL(input, window.location.origin)
        : new URL(input.url, window.location.origin);
      const isApiRequest = requestUrl.pathname.startsWith("/api/");
      if (!isApiRequest) {
        return nativeFetch(input, init);
      }
      const effectiveUserId = getActiveScopeUserId();
      if (!effectiveUserId) {
        return nativeFetch(input, init);
      }
      const nextInit = { ...(init || {}) };
      const headers = new Headers(nextInit.headers || (typeof input !== "string" ? input.headers : undefined) || {});
      headers.set("X-User-Id", effectiveUserId);
      nextInit.headers = headers;
      return nativeFetch(input, nextInit);
    };

    async function loadFieldOptionsForCurrentScope() {
      const response = await nativeFetch("/api/field-options");
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "读取字段配置失败");
      }
      applyFieldOptionsPayload(payload);
      return payload;
    }

    function renderAuthControls() {
      const user = authState.user;
      if (authState.authenticated && user) {
        authLoginButton.hidden = true;
        authLogoutButton.hidden = false;
        authPasswordButton.hidden = !canCurrentUserChangePassword();
        authDepartmentScheduleButton.hidden = !canAccessDepartmentSchedule();
        authAdminPageButton.hidden = !authState.isAdmin;
        promptEditorButton.hidden = false;
        userDingtalkMcpButton.hidden = false;
      } else {
        authLoginButton.hidden = false;
        authLogoutButton.hidden = true;
        authPasswordButton.hidden = true;
        authDepartmentScheduleButton.hidden = true;
        authAdminPageButton.hidden = true;
        promptEditorButton.hidden = true;
        userDingtalkMcpButton.hidden = true;
      }
      if (!canCurrentUserChangePassword() && isPasswordOverlayOpen) {
        closePasswordOverlay();
      }
      if ((!authState.authenticated || !user) && isPromptOverlayOpen) {
        closePromptOverlay();
      }
      if ((!authState.authenticated || !user) && isUserDingtalkMcpOverlayOpen) {
        closeUserDingtalkMcpOverlay();
      }
      renderPageUserBadge();
    }

    async function refreshAuthState() {
      const previousScopeUserId = String(
        getActiveScopeUserId() || authState.scopeUserId || authState.user && authState.user.user_id || ""
      ).trim();
      try {
        const response = await nativeFetch("/api/auth/me");
        const payload = await response.json();
        authState.authenticated = Boolean(payload && payload.authenticated && payload.user);
        authState.user = authState.authenticated ? payload.user : null;
        authState.isAdmin = Boolean(authState.user && authState.user.role === "admin");
        authState.isDepartmentAdmin = Boolean(authState.user && authState.user.is_department_admin);
        authState.users = [];
        authState.scopeUserId = String(authState.user && authState.user.user_id || "").trim();
        if (authState.isAdmin) {
          const usersResponse = await nativeFetch("/api/admin/users");
          const usersPayload = await usersResponse.json();
          if (usersResponse.ok && usersPayload && Array.isArray(usersPayload.users)) {
            authState.users = usersPayload.users;
            const availableUserIds = new Set(
              usersPayload.users
                .map((item) => String(item && item.user_id || "").trim())
                .filter((item) => item)
            );
            if (previousScopeUserId && availableUserIds.has(previousScopeUserId)) {
              authState.scopeUserId = previousScopeUserId;
            }
          }
        }
      } catch (error) {
        authState = {
          authenticated: false,
          user: null,
          users: [],
          isAdmin: false,
          isDepartmentAdmin: false,
          scopeUserId: ""
        };
      }
      renderAuthControls();
    }

    function normalizeDingtalkAuthConfig(payload) {
      return {
        enabled: Boolean(payload && payload.enabled),
        configured: Boolean(payload && payload.configured),
        allow_org_auto_login: Boolean(payload && payload.allow_org_auto_login),
        corp_id: String(payload && payload.corp_id || "").trim(),
        redirect_base_url: String(payload && payload.redirect_base_url || "").trim(),
        effective_redirect_base_url: String(payload && payload.effective_redirect_base_url || "").trim(),
        callback_url: String(payload && payload.callback_url || "").trim(),
        callback_path: String(payload && payload.callback_path || "").trim(),
        scan_qr_supported: Boolean(payload && payload.scan_qr_supported),
      };
    }

    function setInlineStatus(target, text, isError) {
      target.textContent = text || "";
      target.style.color = isError ? "#c33636" : "#5c7592";
    }

    function buildPublicQrFallbackUrl(content) {
      const encoded = encodeURIComponent(String(content || "").trim());
      if (!encoded) {
        return "";
      }
      const template = String(window.__publicQrServiceTemplate || "").trim();
      if (!template || !template.includes("{data}")) {
        return "";
      }
      return template.replace("{data}", encoded);
    }

    function stopDingtalkScanPolling() {
      if (dingtalkScanPollTimer) {
        window.clearTimeout(dingtalkScanPollTimer);
        dingtalkScanPollTimer = null;
      }
    }

    function renderDingtalkScanPlaceholder(message) {
      dingtalkScanQrWrap.innerHTML = `<div class="muted">${escapeHtml(message || "点击下方按钮生成二维码")}</div>`;
    }

    function getDingtalkScanWarning(baseUrl) {
      const targetBaseUrl = String(baseUrl || "").trim().toLowerCase();
      if (!targetBaseUrl) {
        return "请先在管理员页面配置回调基地址，再生成二维码。";
      }
      if (targetBaseUrl.includes("127.0.0.1") || targetBaseUrl.includes("localhost")) {
        return "当前回调地址仍是本机回环地址；若要让手机扫码回调成功，请改成电脑可被手机访问的局域网或公网地址。";
      }
      return "";
    }

    function renderDingtalkAuthSection() {
      const enabled = dingtalkAuthConfig.enabled && dingtalkAuthConfig.configured;
      dingtalkAuthSection.hidden = !enabled;
      authSections.classList.toggle("local-only", !enabled);
      authDialogSubtitle.textContent = enabled
        ? "支持本地账号密码登录，也支持钉钉扫码登录。"
        : "请输入本地账号密码登录当前工作台。";
      if (!enabled) {
        currentDingtalkScanSessionId = "";
        stopDingtalkScanPolling();
        startDingtalkScanLoginButton.disabled = true;
        refreshDingtalkScanLoginButton.disabled = true;
        dingtalkScanHint.textContent = "管理员尚未完成钉钉 ClientId / ClientSecret 配置。";
        dingtalkScanLink.hidden = true;
        dingtalkScanLink.href = "#";
        renderDingtalkScanPlaceholder("管理员尚未启用钉钉扫码登录");
        setInlineStatus(dingtalkScanStatus, "完成管理员配置后，这里会生成二维码。", false);
        return;
      }
      startDingtalkScanLoginButton.disabled = false;
      refreshDingtalkScanLoginButton.disabled = false;
      dingtalkScanHint.textContent = dingtalkAuthConfig.allow_org_auto_login
        ? "扫码成功后，会自动以当前钉钉组织成员身份创建/更新本地账号并登录。"
        : "管理员关闭了“组织成员直接登录”，扫码识别到的用户仍需加入登录白名单后才能进入系统。";
      if (!currentDingtalkScanSessionId) {
        renderDingtalkScanPlaceholder("点击“生成二维码”后，用手机钉钉扫一扫完成登录");
      }
      const warning = getDingtalkScanWarning(dingtalkAuthConfig.effective_redirect_base_url || dingtalkAuthConfig.redirect_base_url);
      if (warning) {
        setInlineStatus(dingtalkScanStatus, warning, true);
      } else if (!dingtalkAuthConfig.scan_qr_supported) {
        setInlineStatus(
          dingtalkScanStatus,
          "当前二维码图片会通过公共二维码服务生成；如果你不希望外部服务接触短期登录链接，可直接用手机打开下方授权链接。",
          false
        );
      } else if (!dingtalkScanStatus.textContent.trim()) {
        setInlineStatus(dingtalkScanStatus, "二维码默认 5 分钟有效。", false);
      }
    }

    async function loadDingtalkAuthConfig() {
      try {
        const response = await nativeFetch(`/api/auth/dingtalk-config?origin=${encodeURIComponent(window.location.origin)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取钉钉登录配置失败");
        }
        dingtalkAuthConfig = normalizeDingtalkAuthConfig(payload);
      } catch (error) {
        dingtalkAuthConfig = normalizeDingtalkAuthConfig({});
        setInlineStatus(dingtalkScanStatus, error.message || "读取钉钉配置失败。", true);
      }
      renderDingtalkAuthSection();
      return dingtalkAuthConfig;
    }

    function openAuthOverlay() {
      isAuthOverlayOpen = true;
      authOverlay.hidden = false;
      currentDingtalkScanSessionId = "";
      stopDingtalkScanPolling();
      const rememberedUsername = applyStoredLocalLoginUsername();
      authLocalPasswordInput.value = "";
      setInlineStatus(authLocalStatus, "", false);
      dingtalkScanLink.hidden = true;
      dingtalkScanLink.href = "#";
      setInlineStatus(dingtalkScanStatus, "", false);
      loadDingtalkAuthConfig().catch(() => {});
      updateBodyOverlayState();
      window.setTimeout(() => {
        if (rememberedUsername) {
          authLocalPasswordInput.focus();
        } else {
          authLocalUsernameInput.focus();
        }
      }, 0);
    }

    function closeAuthOverlay() {
      isAuthOverlayOpen = false;
      authOverlay.hidden = true;
      currentDingtalkScanSessionId = "";
      stopDingtalkScanPolling();
      dingtalkScanLink.hidden = true;
      dingtalkScanLink.href = "#";
      applyStoredLocalLoginUsername();
      authLocalPasswordInput.value = "";
      setInlineStatus(authLocalStatus, "", false);
      setInlineStatus(dingtalkScanStatus, "", false);
      renderDingtalkAuthSection();
      updateBodyOverlayState();
    }

    async function submitLocalPasswordLogin() {
      const username = String(authLocalUsernameInput.value || "").trim();
      const password = String(authLocalPasswordInput.value || "");
      if (!username || !password) {
        setInlineStatus(authLocalStatus, "请输入账号和密码。", true);
        return;
      }
      try {
        setInlineStatus(authLocalStatus, "正在登录...", false);
        const response = await nativeFetch("/api/auth/password-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "登录失败");
        }
        writeStoredLocalLoginUsername(username);
        prepareForScopeChange();
        await reloadDataForCurrentScope();
        closeAuthOverlay();
        setStatus("", "");
      } catch (error) {
        setInlineStatus(authLocalStatus, error.message || "登录失败。", true);
      }
    }

    function openPasswordOverlay() {
      if (!canCurrentUserChangePassword()) {
        return;
      }
      const currentUser = authState.user || {};
      isPasswordOverlayOpen = true;
      passwordOverlay.hidden = false;
      passwordDialogAccount.textContent = `当前账号：${currentUser.display_name || currentUser.user_id || "未登录"}`;
      passwordCurrentInput.value = "";
      passwordNewInput.value = "";
      passwordConfirmInput.value = "";
      setInlineStatus(passwordStatus, "", false);
      updateBodyOverlayState();
      window.setTimeout(() => passwordCurrentInput.focus(), 0);
    }

    function closePasswordOverlay() {
      isPasswordOverlayOpen = false;
      passwordOverlay.hidden = true;
      passwordCurrentInput.value = "";
      passwordNewInput.value = "";
      passwordConfirmInput.value = "";
      setInlineStatus(passwordStatus, "", false);
      updateBodyOverlayState();
    }

    async function submitPasswordUpdate() {
      const currentPassword = String(passwordCurrentInput.value || "");
      const newPassword = String(passwordNewInput.value || "");
      const confirmPassword = String(passwordConfirmInput.value || "");
      if (!currentPassword || !newPassword || !confirmPassword) {
        setInlineStatus(passwordStatus, "请完整填写当前密码、新密码和确认密码。", true);
        return;
      }
      if (newPassword !== confirmPassword) {
        setInlineStatus(passwordStatus, "两次输入的新密码不一致。", true);
        return;
      }
      try {
        setInlineStatus(passwordStatus, "正在保存新密码...", false);
        const response = await nativeFetch("/api/auth/password-update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "密码修改失败");
        }
        closePasswordOverlay();
        setStatus("密码修改成功。", "success");
      } catch (error) {
        setInlineStatus(passwordStatus, error.message || "密码修改失败。", true);
      }
    }

    async function pollDingtalkScanSession() {
      if (!currentDingtalkScanSessionId) {
        return;
      }
      try {
        const response = await nativeFetch(`/api/auth/dingtalk/scan-session?login_id=${encodeURIComponent(currentDingtalkScanSessionId)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取扫码状态失败");
        }
        if (payload.status === "completed" && payload.user) {
          stopDingtalkScanPolling();
          prepareForScopeChange();
          await reloadDataForCurrentScope();
          closeAuthOverlay();
          setStatus("", "");
          return;
        }
        if (payload.status === "error" || payload.status === "denied") {
          stopDingtalkScanPolling();
          setInlineStatus(dingtalkScanStatus, payload.error_message || "扫码登录失败，请重新生成二维码。", true);
          return;
        }
        if (payload.status === "expired") {
          stopDingtalkScanPolling();
          setInlineStatus(dingtalkScanStatus, "二维码已过期，请点击“刷新二维码”重新生成。", true);
          renderDingtalkScanPlaceholder("二维码已过期，请刷新后重新扫码");
          return;
        }
      } catch (error) {
        stopDingtalkScanPolling();
        setInlineStatus(dingtalkScanStatus, error.message || "读取扫码状态失败。", true);
        return;
      }
      dingtalkScanPollTimer = window.setTimeout(pollDingtalkScanSession, 1800);
    }

    async function startDingtalkScanLogin() {
      await loadDingtalkAuthConfig();
      if (!(dingtalkAuthConfig.enabled && dingtalkAuthConfig.configured)) {
        return;
      }
      stopDingtalkScanPolling();
      currentDingtalkScanSessionId = "";
      renderDingtalkScanPlaceholder("正在生成二维码，请稍候...");
      setInlineStatus(dingtalkScanStatus, "正在生成钉钉扫码二维码...", false);
      dingtalkScanLink.hidden = true;
      try {
        const response = await nativeFetch("/api/auth/dingtalk/scan-session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ current_origin: window.location.origin }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "生成扫码二维码失败");
        }
        currentDingtalkScanSessionId = String(payload.login_id || "").trim();
        const qrImageUrl = String(payload.qr_image_url || "").trim() || buildPublicQrFallbackUrl(payload.scan_entry_url || payload.auth_url || "");
        if (qrImageUrl) {
          dingtalkScanQrWrap.innerHTML = `<img class="auth-qr-image" src="${escapeHtml(qrImageUrl)}" alt="钉钉扫码登录二维码">`;
        } else {
          renderDingtalkScanPlaceholder("当前服务端暂未开启本地二维码图片生成，请直接在手机中打开下方登录链接。");
        }
        const scanLink = String(payload.scan_entry_url || payload.auth_url || "").trim();
        if (scanLink) {
          dingtalkScanLink.hidden = false;
          dingtalkScanLink.href = scanLink;
          dingtalkScanLink.textContent = `如果二维码无法识别，可直接在手机打开：${scanLink}`;
        }
        const statusLines = [];
        if (payload.expires_at) {
          statusLines.push(`二维码有效期至：${payload.expires_at}`);
        }
        if (!payload.qr_image_url) {
          statusLines.push("当前二维码图片由公共二维码服务生成，登录链接本身仍由当前服务签发且 5 分钟后失效。");
        }
        const warning = getDingtalkScanWarning(payload.redirect_base_url || dingtalkAuthConfig.effective_redirect_base_url);
        if (warning) {
          statusLines.push(warning);
        } else {
          statusLines.push("请使用手机钉钉扫一扫，授权成功后网页会自动完成登录。");
        }
        setInlineStatus(dingtalkScanStatus, statusLines.join("\\n"), Boolean(warning));
        dingtalkScanPollTimer = window.setTimeout(pollDingtalkScanSession, 1500);
      } catch (error) {
        renderDingtalkScanPlaceholder("二维码生成失败，请检查管理员配置后重试");
        setInlineStatus(dingtalkScanStatus, error.message || "二维码生成失败。", true);
      }
    }

    async function logoutCurrentUser() {
      persistScopeLocalState();
      cancelWeeklyPlanAutosave();
      cancelVisualSettingsAutosave();
      try {
        await nativeFetch("/api/auth/logout", { method: "POST" });
        prepareForScopeChange({ persist: false });
        await reloadDataForCurrentScope();
        setStatus("已退出登录。", "success");
      } catch (error) {
        setStatus("退出失败，请稍后重试。", "error");
      }
    }

    async function reloadDataForCurrentScope() {
      cancelWeeklyPlanAutosave();
      cancelVisualSettingsAutosave();
      invalidateScopedAsyncRequests();
      resetScopedInMemoryCaches();
      await refreshAuthState();
      await loadFieldOptionsForCurrentScope().catch(() => {});
      await loadVisualSettings({ silent: true });
      await loadDingtalkAuthConfig().catch(() => {});
      knownCustomerNames = [];
      knownCustomerProfiles = {};
      updateCustomerNameOptions();
      currentEditorWorkDate = dateInput.value;
      syncMonthFromDate();
      renderWeekButtons(dateInput.value);
      loadWeeklyPlan(dateInput.value);
      loadDateEntry(dateInput.value, false);
      refreshRecentEntries();
      refreshMonthEntries();
      loadCustomerNames();
      warmDeliveryProgressCache(dateInput.value);
    }

    const THEME_PREFERENCE_STORAGE_KEY = "daily_planner_theme_preference";
    const LOCAL_LOGIN_USERNAME_STORAGE_KEY = "daily_planner_last_local_login_username";

    function readStoredThemePreference() {
      try {
        const value = window.localStorage.getItem(THEME_PREFERENCE_STORAGE_KEY);
        return value === "dark" || value === "light" ? value : "";
      } catch (error) {
        return "";
      }
    }

    function writeStoredThemePreference(theme) {
      try {
        if (theme === "dark" || theme === "light") {
          window.localStorage.setItem(THEME_PREFERENCE_STORAGE_KEY, theme);
        } else {
          window.localStorage.removeItem(THEME_PREFERENCE_STORAGE_KEY);
        }
      } catch (error) {
        // Ignore storage failures.
      }
    }

    function readStoredLocalLoginUsername() {
      try {
        return String(window.localStorage.getItem(LOCAL_LOGIN_USERNAME_STORAGE_KEY) || "").trim();
      } catch (error) {
        return "";
      }
    }

    function writeStoredLocalLoginUsername(username) {
      const normalizedUsername = String(username || "").trim();
      try {
        if (normalizedUsername) {
          window.localStorage.setItem(LOCAL_LOGIN_USERNAME_STORAGE_KEY, normalizedUsername);
        } else {
          window.localStorage.removeItem(LOCAL_LOGIN_USERNAME_STORAGE_KEY);
        }
      } catch (error) {
        // Ignore storage failures.
      }
      return normalizedUsername;
    }

    function applyStoredLocalLoginUsername() {
      const rememberedUsername = readStoredLocalLoginUsername();
      authLocalUsernameInput.value = rememberedUsername;
      return rememberedUsername;
    }

    function getAutoTheme(currentDate = new Date()) {
      const hour = currentDate.getHours();
      return hour >= AUTO_THEME_DAY_START_HOUR && hour < AUTO_THEME_NIGHT_START_HOUR ? "light" : "dark";
    }

    function getNextAutoThemeSwitchDelay(currentDate = new Date()) {
      const nextSwitch = new Date(currentDate);
      if (currentDate.getHours() >= AUTO_THEME_NIGHT_START_HOUR) {
        nextSwitch.setDate(nextSwitch.getDate() + 1);
        nextSwitch.setHours(AUTO_THEME_DAY_START_HOUR, 0, 0, 0);
      } else if (currentDate.getHours() >= AUTO_THEME_DAY_START_HOUR) {
        nextSwitch.setHours(AUTO_THEME_NIGHT_START_HOUR, 0, 0, 0);
      } else {
        nextSwitch.setHours(AUTO_THEME_DAY_START_HOUR, 0, 0, 0);
      }
      return Math.max(1000, nextSwitch.getTime() - currentDate.getTime());
    }

    function scheduleAutoThemeRefresh() {
      window.clearTimeout(scheduleAutoThemeRefresh.timerId);
      if (readStoredThemePreference()) {
        return;
      }
      scheduleAutoThemeRefresh.timerId = window.setTimeout(() => {
        applyTheme(getAutoTheme());
        scheduleAutoThemeRefresh();
      }, getNextAutoThemeSwitchDelay());
    }

    function applyTheme(theme) {
      const nextTheme = theme === "dark" ? "dark" : "light";
      document.body.dataset.theme = nextTheme;
      themeToggleButton.textContent = nextTheme === "dark" ? "白天模式" : "黑夜模式";
      themeToggleButton.setAttribute("aria-label", nextTheme === "dark" ? "切换到白天模式" : "切换到黑夜模式");
      applyVisualSettings(currentUiSettings);
    }

    function initTheme() {
      applyTheme(readStoredThemePreference() || getAutoTheme());
      scheduleAutoThemeRefresh();
    }

    function setBackgroundSettingsOpen(isOpen) {
      isBackgroundSettingsOpen = Boolean(isOpen);
      backgroundSettingsMenu.hidden = !isBackgroundSettingsOpen;
      backgroundSettingsButton.setAttribute("aria-expanded", isBackgroundSettingsOpen ? "true" : "false");
    }

    function normalizeUiSettings(settings) {
      const source = settings && typeof settings === "object" ? settings : {};
      const normalizeOpacity = (value, fallback) => {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) {
          return fallback;
        }
        return Math.min(1, Math.max(0.25, Math.round(numeric * 100) / 100));
      };
      return {
        background_image: typeof source.background_image === "string" ? source.background_image : "",
        background_mode: ["cover", "contain", "repeat"].includes(source.background_mode) ? source.background_mode : "cover",
        region_opacity: normalizeOpacity(
          firstDefinedValue(
            source.region_opacity,
            source.weekly_region_opacity,
            source.editor_region_opacity,
            source.month_region_opacity
          ),
          0.94
        )
      };
    }

    function formatOpacityPercent(value) {
      return `${Math.round(value * 100)}%`;
    }

    function isBingDailyBackgroundValue(value) {
      const normalized = String(value || "").trim();
      return normalized === BING_DAILY_BACKGROUND_PATH || normalized.startsWith(`${BING_DAILY_BACKGROUND_PATH}?`);
    }

    function describeBackgroundSetting(value) {
      if (isBingDailyBackgroundValue(value)) {
        return "已使用 Bing 每日图片";
      }
      return value ? "已设置本地背景图" : "未设置背景图";
    }

    function buildBodyBackgroundImage(theme, backgroundImage) {
      const baseLayers = theme === "dark"
        ? [
            "radial-gradient(circle at 10% 8%, rgba(125, 183, 255, 0.18), transparent 24%)",
            "radial-gradient(circle at 88% 10%, rgba(125, 183, 255, 0.12), transparent 18%)",
            "linear-gradient(180deg, #243754 0%, #172437 42%, #101a29 100%)"
          ]
        : [
            "radial-gradient(circle at 10% 8%, rgba(46, 119, 208, 0.14), transparent 24%)",
            "radial-gradient(circle at 88% 10%, rgba(86, 168, 255, 0.18), transparent 18%)",
            "linear-gradient(180deg, #f8fbff 0%, #eef5ff 42%, #e2edfb 100%)"
          ];
      if (!backgroundImage) {
        return baseLayers.join(", ");
      }
      const safeBackgroundImage = replaceLiteral(
        replaceLiteral(backgroundImage, "\\\\", "\\\\\\\\"),
        '"',
        '\\"'
      );
      return [`url("${safeBackgroundImage}")`, ...baseLayers].join(", ");
    }

    function buildViewportFallback(theme) {
      if (theme === "dark") {
        return [
          "radial-gradient(circle at 14% 10%, rgba(125, 183, 255, 0.18), transparent 26%)",
          "radial-gradient(circle at 86% 88%, rgba(90, 139, 212, 0.2), transparent 30%)",
          "linear-gradient(180deg, #243754 0%, #172437 42%, #101a29 100%)"
        ].join(", ");
      }
      return [
        "radial-gradient(circle at 14% 10%, rgba(107, 176, 255, 0.16), transparent 24%)",
        "radial-gradient(circle at 82% 92%, rgba(58, 122, 203, 0.12), transparent 26%)",
        "linear-gradient(180deg, #f9fcff 0%, #eef5ff 40%, #dce8f8 100%)"
      ].join(", ");
    }

    function buildRegionSurface(theme, opacity) {
      const start = opacity;
      const end = Math.max(0.16, opacity - 0.08);
      if (theme === "dark") {
        return `linear-gradient(180deg, rgba(38, 56, 84, ${start}), rgba(25, 39, 60, ${end}))`;
      }
      return `linear-gradient(180deg, rgba(255, 255, 255, ${start}), rgba(244, 249, 255, ${end}))`;
    }

    function buildBackgroundLayerStyle(backgroundImage, backgroundMode) {
      if (!backgroundImage) {
        return {
          size: "cover, auto, auto",
          position: "center, center, center",
          repeat: "no-repeat, no-repeat, no-repeat",
        };
      }
      if (backgroundMode === "contain") {
        return {
          size: "contain, cover, auto, auto",
          position: "center, center, center, center",
          repeat: "no-repeat, no-repeat, no-repeat, no-repeat",
        };
      }
      if (backgroundMode === "repeat") {
        return {
          size: "auto, cover, auto, auto",
          position: "left top, center, center, center",
          repeat: "repeat, no-repeat, no-repeat, no-repeat",
        };
      }
      return {
        size: "cover, cover, auto, auto",
        position: "center, center, center, center",
        repeat: "no-repeat, no-repeat, no-repeat, no-repeat",
      };
    }

    function updateBackgroundStretch() {
      backgroundStretchFrame = 0;
      const rawScrollTop = Number(
        firstDefinedValue(window.scrollY, window.pageYOffset, document.documentElement.scrollTop, 0)
      );
      const scrollTop = Number.isFinite(rawScrollTop) ? rawScrollTop : 0;
      const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      const overscrollTop = Math.min(180, Math.max(0, -scrollTop));
      const overscrollBottom = Math.min(180, Math.max(0, scrollTop - maxScroll));
      const viewportHeight = Math.max(1, window.innerHeight || document.documentElement.clientHeight || 0);
      const reserveOffset = Math.round(Math.min(220, Math.max(120, viewportHeight * 0.18)));
      const scrollRatio = maxScroll > 0 ? Math.min(1, Math.max(0, scrollTop / maxScroll)) : 0.5;
      const parallaxOffset = (0.5 - scrollRatio) * reserveOffset * 0.9;
      const overscrollOffset = overscrollTop > 0
        ? overscrollTop * 0.72
        : overscrollBottom > 0
          ? -overscrollBottom * 0.72
          : 0;
      const translateY = Math.max(-reserveOffset, Math.min(reserveOffset, parallaxOffset + overscrollOffset));

      pageBackground.style.transformOrigin = "center center";
      pageBackground.style.transform = `translate3d(0, ${translateY.toFixed(2)}px, 0)`;
      pageBackground.style.filter = "";
    }

    function scheduleBackgroundStretch() {
      if (backgroundStretchFrame) {
        return;
      }
      backgroundStretchFrame = window.requestAnimationFrame(updateBackgroundStretch);
    }

    function applyVisualSettings(settings) {
      currentUiSettings = normalizeUiSettings(settings);
      const theme = document.body.dataset.theme === "dark" ? "dark" : "light";
      const root = document.documentElement;
      const regionSurface = buildRegionSurface(theme, currentUiSettings.region_opacity);
      const panelSurface = buildRegionSurface(theme, Math.max(0.18, currentUiSettings.region_opacity - 0.04));
      document.documentElement.style.backgroundImage = buildViewportFallback(theme);
      document.documentElement.style.backgroundColor = theme === "dark" ? "#101a29" : "#e2edfb";
      pageBackground.style.backgroundColor = theme === "dark" ? "#101a29" : "#e2edfb";
      pageBackground.style.backgroundImage = buildBodyBackgroundImage(theme, currentUiSettings.background_image);
      const backgroundLayerStyle = buildBackgroundLayerStyle(
        currentUiSettings.background_image,
        currentUiSettings.background_mode
      );
      pageBackground.style.backgroundSize = backgroundLayerStyle.size;
      pageBackground.style.backgroundPosition = backgroundLayerStyle.position;
      pageBackground.style.backgroundRepeat = backgroundLayerStyle.repeat;
      scheduleBackgroundStretch();
      root.style.setProperty("--boot-panel-background", panelSurface);
      root.style.setProperty("--boot-region-background", regionSurface);

      weeklyPlanPanel.style.background = panelSurface;
      weeklyPlanBox.style.background = regionSurface;
      weeklyBoardScroll.style.background = "";
      editorPanel.style.background = regionSurface;
      monthPanel.style.background = regionSurface;
      if (pageUserBadge) {
        pageUserBadge.style.background = regionSurface;
      }
      weeklyPlanBox.querySelectorAll(".weekly-head, .weekly-cell, .weekly-label, .weekly-pending").forEach((element) => {
        element.style.background = "";
      });
      weeklyPlanBox.querySelectorAll(".weekly-cell textarea, .weekly-pending textarea").forEach((element) => {
        element.style.background = "";
      });

      regionOpacityInput.value = String(Math.round(currentUiSettings.region_opacity * 100));
      regionOpacityValue.textContent = formatOpacityPercent(currentUiSettings.region_opacity);
      backgroundImageName.textContent = describeBackgroundSetting(currentUiSettings.background_image);
      backgroundModeSelect.value = currentUiSettings.background_mode;
      useBingBackgroundButton.setAttribute(
        "aria-pressed",
        isBingDailyBackgroundValue(currentUiSettings.background_image) ? "true" : "false"
      );
      clearBackgroundImageButton.disabled = !currentUiSettings.background_image;
    }

    async function loadVisualSettings(options = {}) {
      const silent = Boolean(options.silent);
      const requestMeta = registerScopedAsyncRequest("ui-settings-load");
      try {
        const response = await fetch("/api/ui-settings");
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取视觉设置失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        applyVisualSettings(data.settings || currentUiSettings);
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        if (!silent) {
          setStatus(error.message || "读取视觉设置失败。", "error");
        }
      }
    }

    function cancelVisualSettingsAutosave() {
      if (!visualSettingsAutosaveTimer) {
        return;
      }
      clearTimeout(visualSettingsAutosaveTimer);
      visualSettingsAutosaveTimer = null;
    }

    async function saveVisualSettings(showMessage = false) {
      const requestMeta = registerScopedAsyncRequest("ui-settings-save");
      try {
        const response = await fetch("/api/ui-settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(currentUiSettings)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存视觉设置失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return false;
        }
        currentUiSettings = normalizeUiSettings(data.settings || currentUiSettings);
        applyVisualSettings(currentUiSettings);
        if (showMessage) {
          setStatus("视觉设置已保存。", "success");
        }
        return true;
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return false;
        }
        setStatus(error.message || "视觉设置保存失败。", "error");
        return false;
      }
    }

    function scheduleVisualSettingsSave(showMessage = false) {
      cancelVisualSettingsAutosave();
      visualSettingsAutosaveTimer = window.setTimeout(() => {
        visualSettingsAutosaveTimer = null;
        saveVisualSettings(showMessage);
      }, VISUAL_SETTINGS_AUTOSAVE_DELAY_MS);
    }

    function updateOpacitySetting(value) {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, region_opacity: Number(value) / 100 });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    }

    function handleBackgroundImageSelection(file) {
      if (!file) {
        return;
      }
      if (!file.type.startsWith("image/")) {
        setStatus("请选择图片文件作为页面背景。", "warning");
        return;
      }
      if (file.size > MAX_BACKGROUND_IMAGE_SIZE_BYTES) {
        setStatus("背景图请控制在 5MB 以内。", "warning");
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: String(reader.result || "") });
        applyVisualSettings(currentUiSettings);
        scheduleVisualSettingsSave(true);
      };
      reader.onerror = () => {
        setStatus("读取背景图失败，请重试。", "error");
      };
      reader.readAsDataURL(file);
    }

    function setStatus(message, type = "") {
      statusEl.textContent = message;
      statusEl.className = "status" + (type ? " " + type : "");
    }

    function isValidDateString(value) {
      return /^\d{4}-\d{2}-\d{2}$/.test(String(value || ""));
    }

    function getRememberedWorkDate() {
      try {
        const value = window.localStorage.getItem(buildScopedStorageKey(LAST_SELECTED_DATE_STORAGE_PREFIX));
        return isValidDateString(value) ? value : "";
      } catch (error) {
        return "";
      }
    }

    function rememberWorkDate(value) {
      if (!isValidDateString(value)) {
        return;
      }
      try {
        window.localStorage.setItem(buildScopedStorageKey(LAST_SELECTED_DATE_STORAGE_PREFIX), value);
      } catch (error) {
        // Ignore storage failures.
      }
    }

    function applyRememberedWorkDateForCurrentScope() {
      const rememberedDate = getRememberedWorkDate();
      if (!rememberedDate || rememberedDate === dateInput.value) {
        return false;
      }
      dateInput.value = rememberedDate;
      currentEditorWorkDate = rememberedDate;
      syncMonthFromDate();
      return true;
    }

    function getStorageJson(key) {
      try {
        const rawValue = window.localStorage.getItem(key);
        if (!rawValue) {
          return null;
        }
        const payload = JSON.parse(rawValue);
        return payload && typeof payload === "object" ? payload : null;
      } catch (error) {
        return null;
      }
    }

    function setStorageJson(key, payload) {
      try {
        window.localStorage.setItem(key, JSON.stringify(payload));
        return true;
      } catch (error) {
        return false;
      }
    }

    function removeStorageValue(key) {
      try {
        window.localStorage.removeItem(key);
      } catch (error) {
        // Ignore storage failures.
      }
    }

    function normalizeItemPayload(item) {
      const source = item && typeof item === "object" ? item : {};
      return {
        customer_name: String(source.customer_name || "").trim(),
        project_type: String(source.project_type || "").trim(),
        sales: String(source.sales || "").trim(),
        item_type: String(source.item_type || "").trim(),
        service_mode: String(source.service_mode || "").trim(),
        work_hours: String(firstDefinedValue(source.work_hours, "")).trim(),
        work_content: String(source.work_content || "").trim(),
        pending_issues: String(source.pending_issues || "").trim(),
        risk: String(source.risk || "").trim()
      };
    }

    function hasMeaningfulItemContent(item) {
      return Object.values(normalizeItemPayload(item)).some((value) => String(value || "").trim());
    }

    function normalizeEntryItems(items) {
      return (Array.isArray(items) ? items : [])
        .map((item) => normalizeItemPayload(item))
        .filter((item) => hasMeaningfulItemContent(item));
    }

    function buildEntrySnapshot(workDate, items) {
      return JSON.stringify({
        work_date: isValidDateString(workDate) ? workDate : "",
        items: normalizeEntryItems(items)
      });
    }

    function buildDailyEntryDraftKey(workDate) {
      return buildScopedStorageKey(DAILY_ENTRY_DRAFT_PREFIX, workDate);
    }

    function loadDailyEntryDraft(workDate) {
      if (!isValidDateString(workDate)) {
        return null;
      }
      const payload = getStorageJson(buildDailyEntryDraftKey(workDate));
      if (!payload || !isValidDateString(payload.work_date)) {
        return null;
      }
      return {
        work_date: payload.work_date,
        items: normalizeEntryItems(payload.items),
        updated_at: String(payload.updated_at || "")
      };
    }

    function saveDailyEntryDraft(workDate, items) {
      if (!isValidDateString(workDate)) {
        return;
      }
      const normalizedItems = normalizeEntryItems(items);
      if (!normalizedItems.length) {
        removeStorageValue(buildDailyEntryDraftKey(workDate));
        return;
      }
      setStorageJson(buildDailyEntryDraftKey(workDate), {
        work_date: workDate,
        items: normalizedItems,
        updated_at: formatDateTime(new Date())
      });
    }

    function clearDailyEntryDraft(workDate) {
      if (!isValidDateString(workDate)) {
        return;
      }
      removeStorageValue(buildDailyEntryDraftKey(workDate));
    }

    function rememberSavedEntry(entry) {
      if (!entry || !isValidDateString(entry.work_date)) {
        return;
      }
      savedEntrySnapshots.set(entry.work_date, buildEntrySnapshot(entry.work_date, entry.items || []));
    }

    function applyEntryData(workDate, items, options = {}) {
      const normalizedDate = isValidDateString(workDate) ? workDate : dateInput.value;
      if (!normalizedDate) {
        return;
      }
      currentEditorWorkDate = normalizedDate;
      dateInput.value = normalizedDate;
      rememberWorkDate(normalizedDate);
      syncMonthFromDate();
      renderWeekButtons(normalizedDate);
      if (!options.skipWeeklyPlan) {
        loadWeeklyPlan(normalizedDate);
      }
      renderItems((Array.isArray(items) && items.length ? items : [makeBlankItem()]).map((item) => normalizeItemPayload(item)));
    }

    function applyDailyEntryDraft(draft, options = {}) {
      if (!draft || !isValidDateString(draft.work_date)) {
        return false;
      }
      applyEntryData(draft.work_date, draft.items || [], options);
      return true;
    }

    function persistCurrentEntryDraft() {
      const targetDate = isValidDateString(currentEditorWorkDate) ? currentEditorWorkDate : dateInput.value;
      if (!isValidDateString(targetDate)) {
        return;
      }
      saveDailyEntryDraft(targetDate, collectItems());
    }

    function buildWeeklyPlanDraftKey(weekStart) {
      return buildScopedStorageKey(WEEKLY_PLAN_DRAFT_PREFIX, weekStart);
    }

    function hasMeaningfulWeeklyPlanContent(settings) {
      return Object.keys(weeklyScheduleInputs).some((key) => String(settings && settings[key] || "").trim());
    }

    function loadWeeklyPlanDraft(weekStart) {
      if (!isValidDateString(weekStart)) {
        return null;
      }
      const payload = getStorageJson(buildWeeklyPlanDraftKey(weekStart));
      if (!payload || !isValidDateString(payload.week_start)) {
        return null;
      }
      return {
        week_start: payload.week_start,
        settings: normalizeWeeklyPlanPayload(payload.settings),
        updated_at: String(payload.updated_at || ""),
        base_updated_at: String(payload.base_updated_at || payload.server_updated_at || ""),
        base_snapshot: String(payload.base_snapshot || "")
      };
    }

    function saveWeeklyPlanDraft(weekStart, settings) {
      if (!isValidDateString(weekStart)) {
        return;
      }
      const normalizedSettings = normalizeWeeklyPlanPayload(settings);
      if (!hasMeaningfulWeeklyPlanContent(normalizedSettings)) {
        removeStorageValue(buildWeeklyPlanDraftKey(weekStart));
        return;
      }
      setStorageJson(buildWeeklyPlanDraftKey(weekStart), {
        week_start: weekStart,
        settings: normalizedSettings,
        updated_at: formatDateTime(new Date()),
        base_updated_at: String(weeklyPlanSavedUpdatedAts.get(weekStart) || ""),
        base_snapshot: String(weeklyPlanSavedSnapshots.get(weekStart) || "")
      });
    }

    function clearWeeklyPlanDraft(weekStart) {
      if (!isValidDateString(weekStart)) {
        return;
      }
      removeStorageValue(buildWeeklyPlanDraftKey(weekStart));
    }

    function parseComparableTime(value) {
      const normalized = String(value || "").trim().replace(" ", "T");
      const timestamp = normalized ? Date.parse(normalized) : NaN;
      return Number.isFinite(timestamp) ? timestamp : 0;
    }

    function announceWeeklyPlanSync(userId, weekStart, updatedAt) {
      const scopeUser = getCurrentScopeUser();
      const normalizedUserId = String(
        userId
        || scopeUser && scopeUser.user_id
        || authState.user && authState.user.user_id
        || ""
      ).trim();
      const normalizedWeekStart = String(weekStart || "").trim();
      if (!normalizedUserId || !isValidDateString(normalizedWeekStart)) {
        return;
      }
      try {
        window.localStorage.setItem(
          WEEKLY_PLAN_SYNC_SIGNAL_STORAGE_KEY,
          JSON.stringify({
            user_id: normalizedUserId,
            week_start: normalizedWeekStart,
            updated_at: String(updatedAt || "").trim(),
            emitted_at: formatDateTime(new Date()),
            nonce: `${Date.now()}-${Math.random().toString(16).slice(2)}`
          })
        );
      } catch (error) {
        // Ignore cross-tab sync storage failures.
      }
    }

    function handleWeeklyPlanSyncSignal(event) {
      if (!event || event.key !== WEEKLY_PLAN_SYNC_SIGNAL_STORAGE_KEY || !event.newValue) {
        return;
      }
      let payload = null;
      try {
        payload = JSON.parse(event.newValue);
      } catch (error) {
        return;
      }
      const scopeUser = getCurrentScopeUser();
      const currentScopeUserId = String(
        scopeUser && scopeUser.user_id
        || authState.user && authState.user.user_id
        || ""
      ).trim();
      const targetUserId = String(payload && payload.user_id || "").trim();
      const targetWeekStart = String(payload && payload.week_start || "").trim();
      const currentWeekStart = String(currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value) || "").trim();
      const incomingUpdatedAt = String(payload && payload.updated_at || "").trim();
      const knownUpdatedAt = String(weeklyPlanSavedUpdatedAts.get(targetWeekStart) || "").trim();
      if (!currentScopeUserId || !targetUserId || currentScopeUserId !== targetUserId) {
        return;
      }
      if (!targetWeekStart || !currentWeekStart || targetWeekStart !== currentWeekStart) {
        return;
      }
      if (incomingUpdatedAt && knownUpdatedAt && incomingUpdatedAt === knownUpdatedAt) {
        return;
      }
      loadWeeklyPlan(dateInput.value || targetWeekStart, false);
    }

    function setDeliveryProgressOpen(isOpen) {
      isDeliveryProgressOpen = Boolean(isOpen);
      deliveryProgressOverlay.hidden = !isDeliveryProgressOpen;
      updateBodyOverlayState();
    }

    function updateBodyOverlayState() {
      document.body.style.overflow = (
        isDeliveryProgressOpen
        || isPreviewOpen
        || isSendConfirmOpen
        || isAuthOverlayOpen
        || isPasswordOverlayOpen
        || isPromptOverlayOpen
        || isUserDingtalkMcpOverlayOpen
      ) ? "hidden" : "";
    }

    function setPreviewOpen(isOpen) {
      isPreviewOpen = Boolean(isOpen);
      previewOverlay.hidden = !isPreviewOpen;
      if (!isPreviewOpen && isSendConfirmOpen) {
        isSendConfirmOpen = false;
        sendConfirmOverlay.hidden = true;
      }
      syncPreviewActionButtons();
      updateBodyOverlayState();
    }

    function normalizeDailyLogRecipient(recipient) {
      const source = recipient && typeof recipient === "object" ? recipient : {};
      return {
        name: String(source.name || "").trim(),
        user_id: String(source.user_id || source.userId || "").trim(),
      };
    }

    function getCombinedDailyLogRecipients() {
      if (!dailyLogEditorState) {
        return [];
      }
      const merged = [
        ...(Array.isArray(dailyLogEditorState.configuredRecipients) ? dailyLogEditorState.configuredRecipients : []),
        ...(Array.isArray(dailyLogEditorState.extraRecipients) ? dailyLogEditorState.extraRecipients : []),
      ].map((recipient) => normalizeDailyLogRecipient(recipient));
      const seen = new Set();
      return merged.filter((recipient) => {
        const key = recipient.user_id || recipient.name;
        if (!key || seen.has(key)) {
          return false;
        }
        seen.add(key);
        return true;
      });
    }

    function getDailyLogRecipientDisplayText() {
      const recipients = getCombinedDailyLogRecipients();
      if (!recipients.length) {
        return "按模板默认范围";
      }
      return recipients
        .map((recipient) => recipient.name || recipient.user_id || "未命名接收人")
        .join("、");
    }

    function getCurrentReportDisplayName() {
      if (!dailyLogEditorState) {
        return "日志";
      }
      return dailyLogEditorState.kind === "weekly_report" ? "周报" : "售后日报";
    }

    function normalizeWeeklyReportTemplateDisplayName(templateName) {
      const normalized = String(templateName || "").replace(/售后/g, "").replace(/\s{2,}/g, " ").trim();
      return normalized || "未选择模板";
    }

    function getCurrentReportPeriodText() {
      if (!dailyLogEditorState) {
        return "";
      }
      if (dailyLogEditorState.kind === "weekly_report") {
        return `${dailyLogEditorState.week_start || ""} 至 ${dailyLogEditorState.week_end || ""}`;
      }
      return dailyLogEditorState.work_date || "";
    }

    function syncSendConfirmButtons() {
      sendConfirmSubmitButton.disabled = (
        !dailyLogEditorState
        || isSendingDailyLog
        || dailyLogEditorState.templateConfigured === false
      );
      sendConfirmSubmitButton.textContent = isSendingDailyLog ? "发送中..." : "确定发送";
      sendConfirmCloseButton.disabled = isSendingDailyLog;
      sendConfirmCancelButton.disabled = isSendingDailyLog;
    }

    function updateSendConfirmRecipientSummary() {
      const summary = sendConfirmContent.querySelector("#send-confirm-recipient-summary");
      if (summary) {
        summary.textContent = getDailyLogRecipientDisplayText();
      }
    }

    async function lookupDailyLogRecipientByName(recipientIndex, name) {
      if (!dailyLogEditorState) {
        return;
      }
      const previewSessionId = Number(dailyLogEditorState.previewSessionId || 0);
      const scopeMarker = getCurrentScopeAsyncMarker();
      const trimmedName = String(name || "").trim();
      if (!trimmedName) {
        if (dailyLogEditorState.extraRecipients[recipientIndex]) {
          dailyLogEditorState.extraRecipients[recipientIndex].user_id = "";
          renderDailyLogPreviewMeta();
          updateSendConfirmRecipientSummary();
        }
        return;
      }
      setStatus(`正在查询 ${trimmedName} 的钉钉 userId...`, "success");
      try {
        const response = await fetch(`/api/dingtalk-user-lookup?name=${encodeURIComponent(trimmedName)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "钉钉通讯录查询失败");
        }
        if (!isPreviewSessionActive(previewSessionId, scopeMarker)) {
          return;
        }
        if (!dailyLogEditorState.extraRecipients[recipientIndex]) {
          return;
        }
        dailyLogEditorState.extraRecipients[recipientIndex] = {
          name: payload.name || trimmedName,
          user_id: payload.user_id || "",
        };
        renderDailyLogPreviewMeta();
        renderSendConfirmDialog();
        setStatus(
          payload.source === "cache"
            ? `已从本地缓存带出 ${payload.name || trimmedName} 的 userId。`
            : `已从钉钉通讯录获取 ${payload.name || trimmedName} 的 userId，并写入本地数据库。`,
          "success"
        );
      } catch (error) {
        if (!isPreviewSessionActive(previewSessionId, scopeMarker)) {
          return;
        }
        if (dailyLogEditorState.extraRecipients[recipientIndex]) {
          dailyLogEditorState.extraRecipients[recipientIndex].user_id = "";
          renderDailyLogPreviewMeta();
          updateSendConfirmRecipientSummary();
        }
        setStatus(error.message || "钉钉通讯录查询失败。", "error");
        showSendResultToast("人员查询失败", error.message || "钉钉通讯录查询失败。", "error");
      }
    }

    function renderSendConfirmDialog() {
      if (!dailyLogEditorState) {
        sendConfirmContent.innerHTML = '<div class="empty">暂无可发送的内容。</div>';
        syncSendConfirmButtons();
        return;
      }
      const extraRecipients = Array.isArray(dailyLogEditorState.extraRecipients) ? dailyLogEditorState.extraRecipients : [];
      const recipientRows = extraRecipients.length
        ? `
          <div class="send-confirm-recipient-editor">
            ${extraRecipients.map((recipient, index) => `
              <div class="send-confirm-recipient-row">
                <input type="text" data-send-confirm-field="name" data-recipient-index="${index}" value="${escapeHtml(recipient.name || "")}" placeholder="输入人员姓名后自动查询">
                <input type="text" data-send-confirm-field="user_id" data-recipient-index="${index}" value="${escapeHtml(recipient.user_id || "")}" placeholder="userId 自动带出，可手动调整">
                <button type="button" class="danger tiny-btn" data-send-confirm-action="remove-recipient" data-recipient-index="${index}">删除</button>
              </div>
            `).join("")}
          </div>
        `
        : "";
      sendConfirmContent.innerHTML = `
        <div class="send-confirm-summary-grid">
          <div class="send-confirm-summary-item">
            <span class="send-confirm-label">当前日志模版：</span>
            <span class="send-confirm-value">${escapeHtml(dailyLogEditorState.templateName || "未选择模板")}</span>
          </div>
          <div class="send-confirm-summary-item">
            <span class="send-confirm-label">是否发送聊天：</span>
            <label class="send-confirm-toggle">
              <input type="checkbox" id="send-confirm-to-chat" ${dailyLogEditorState.toChat ? "checked" : ""}>
              <span>${dailyLogEditorState.toChat ? "是" : "否"}</span>
            </label>
          </div>
        </div>
        <div class="send-confirm-recipient-top">
          <div class="send-confirm-recipient-line">
            <span class="send-confirm-label">发送到人</span>
            <span class="send-confirm-value" id="send-confirm-recipient-summary">${escapeHtml(getDailyLogRecipientDisplayText())}</span>
          </div>
          <button type="button" class="soft" data-send-confirm-action="add-recipient">增加人员</button>
        </div>
        ${recipientRows}
      `;
      syncSendConfirmButtons();
    }

    function setSendConfirmOpen(isOpen) {
      isSendConfirmOpen = Boolean(isOpen);
      sendConfirmOverlay.hidden = !isSendConfirmOpen;
      if (isSendConfirmOpen) {
        renderSendConfirmDialog();
      }
      updateBodyOverlayState();
    }

    function syncPreviewActionButtons() {
      const canSendDailyLog = Boolean(
        isPreviewOpen
          && dailyLogEditorState
          && ["daily_log", "weekly_report"].includes(dailyLogEditorState.kind)
      );
      const canDownloadWeeklyReport = Boolean(
        isPreviewOpen
          && dailyLogEditorState
          && dailyLogEditorState.kind === "weekly_report"
          && dailyLogEditorState.savedFilename
      );
      const missingTemplateSelection = Boolean(
        canSendDailyLog
          && dailyLogEditorState
          && dailyLogEditorState.templateConfigured === false
      );
      previewSendLogButton.hidden = !canSendDailyLog;
      previewSendLogButton.disabled = !canSendDailyLog || isSendingDailyLog || missingTemplateSelection;
      previewSendLogButton.textContent = isSendingDailyLog ? "发送中..." : "发送日志";
      previewDownloadLogButton.hidden = !canDownloadWeeklyReport;
      previewDownloadLogButton.disabled = !canDownloadWeeklyReport;
    }

    function setDailyLogSendState(isSending) {
      isSendingDailyLog = Boolean(isSending);
      syncPreviewActionButtons();
    }

    function downloadCurrentWeeklyReport() {
      if (!dailyLogEditorState || dailyLogEditorState.kind !== "weekly_report" || !dailyLogEditorState.savedFilename) {
        setStatus("请先生成周报后再下载。", "warning");
        return;
      }
      const downloadUrl = `/api/download-weekly-report-file?filename=${encodeURIComponent(dailyLogEditorState.savedFilename)}`;
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setStatus(`正在下载 ${dailyLogEditorState.savedFilename}。`, "success");
    }

    function showSendResultToast(title, message, type) {
      if (sendResultToastTimer) {
        window.clearTimeout(sendResultToastTimer);
        sendResultToastTimer = null;
      }
      sendResultToast.className = `send-result-toast ${type === "error" ? "error" : "success"}`;
      sendResultToastTitle.textContent = title || "发送成功";
      sendResultToastMessage.textContent = message || "";
      sendResultToast.hidden = false;
      sendResultToastTimer = window.setTimeout(() => {
        sendResultToast.hidden = true;
        sendResultToastTimer = null;
      }, 2600);
    }

    function setDeliveryProgressLoading(isLoading, forceRefresh = false) {
      isDeliveryProgressLoading = Boolean(isLoading);
      deliveryProgressRegenerateButton.disabled = isDeliveryProgressLoading;
      deliveryProgressRegenerateButton.textContent = isDeliveryProgressLoading
        ? (forceRefresh ? "重新生成中..." : "加载中...")
        : "重新生成";
    }

    function normalizeDeliveryStatusClass(status) {
      if (status === "红灯") {
        return "red";
      }
      if (status === "黄灯") {
        return "yellow";
      }
      return "green";
    }

    function buildDeliveryProgressCacheKey(targetDate) {
      return buildScopedStorageKey(DELIVERY_PROGRESS_CACHE_PREFIX, getWeekStartString(targetDate));
    }

    function loadDeliveryProgressCache(targetDate) {
      if (!targetDate) {
        return null;
      }
      try {
        const rawValue = window.localStorage.getItem(buildDeliveryProgressCacheKey(targetDate));
        if (!rawValue) {
          return null;
        }
        const payload = JSON.parse(rawValue);
        if (!payload || typeof payload !== "object") {
          return null;
        }
        return { ...payload, source: "local-cache" };
      } catch (error) {
        return null;
      }
    }

    function saveDeliveryProgressCache(targetDate, payload) {
      if (!targetDate || !payload || typeof payload !== "object") {
        return;
      }
      try {
        window.localStorage.setItem(buildDeliveryProgressCacheKey(targetDate), JSON.stringify(payload));
      } catch (error) {
        // Ignore storage failures and keep the in-memory UI usable.
      }
    }

    async function fetchDeliveryProgressServerCache(targetDate) {
      if (!targetDate) {
        return null;
      }
      const response = await fetch(`/api/delivery-progress-cache?date=${encodeURIComponent(targetDate)}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "交付进展缓存读取失败");
      }
      if (!payload || payload.cached !== true) {
        return null;
      }
      return payload;
    }

    async function warmDeliveryProgressCache(targetDate) {
      if (!targetDate || loadDeliveryProgressCache(targetDate)) {
        return;
      }
      const requestMeta = registerScopedAsyncRequest(
        "delivery-progress-cache-warm",
        getWeekStartString(targetDate) || String(targetDate || "")
      );
      try {
        const payload = await fetchDeliveryProgressServerCache(targetDate);
        if (!payload) {
          return;
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        saveDeliveryProgressCache(targetDate, payload);
      } catch (error) {
        // Background cache warming is optional.
      }
    }

    function renderDeliveryList(items, emptyText) {
      const list = Array.isArray(items) ? items.filter((item) => String(item || "").trim()) : [];
      const safeItems = (list.length ? list : [emptyText]).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
      return `<ul>${safeItems}</ul>`;
    }

    function renderDeliveryProgressReports(payload) {
      const sourceText = payload.source === "local-cache"
        ? "已直接加载上次分析结果"
        : payload.source === "cache"
          ? "已优先加载上次分析结果"
          : "已按最新数据重新生成";
      const generatedAtText = payload.generated_at ? `分析时间 ${payload.generated_at}` : "分析时间未知";
      const anchorDateText = payload.anchor_date ? `基于 ${payload.anchor_date} 的数据生成` : "基于当前周数据生成";
      deliveryProgressSubtitle.textContent = `${payload.week_start} 至 ${payload.week_end} · ${sourceText}。`;
      deliveryProgressMeta.innerHTML = `
        <span class="delivery-meta-pill">交付项目 ${escapeHtml(String(payload.project_count || 0))} 个</span>
        <span class="delivery-meta-pill">统计周期 ${escapeHtml(payload.week_start || "")} 至 ${escapeHtml(payload.week_end || "")}</span>
        <span class="delivery-meta-pill">${escapeHtml(anchorDateText)}</span>
        <span class="delivery-meta-pill">${escapeHtml(generatedAtText)}</span>
      `;

      const reports = Array.isArray(payload.reports) ? payload.reports : [];
      if (!reports.length) {
        deliveryProgressList.innerHTML = '<div class="empty">这周没有可展示的交付项目周报。</div>';
        return;
      }

      deliveryProgressList.innerHTML = reports.map((report) => {
        const statusClass = normalizeDeliveryStatusClass(report.overall_status);
        const serviceModes = Array.isArray(report.service_modes) && report.service_modes.length
          ? report.service_modes.join("、")
          : "未标注";
        const dates = Array.isArray(report.dates) && report.dates.length
          ? `${report.dates[0]} 至 ${report.dates[report.dates.length - 1]}`
          : "本周";
        return `
          <article class="delivery-report-card">
            <div class="delivery-report-head">
              <div>
                <h3 class="delivery-report-name">${escapeHtml(report.project_name || "未命名项目")}</h3>
                <div class="delivery-report-badges">
                  <span>${escapeHtml(serviceModes)}</span>
                  <span>${escapeHtml(String(report.total_hours || "0"))} 小时</span>
                  <span>${escapeHtml(dates)}</span>
                </div>
              </div>
              <span class="delivery-status-badge ${statusClass}">${escapeHtml(report.overall_status || "绿灯")}</span>
            </div>
            <div class="delivery-report-summary">${escapeHtml(report.summary || "暂无总结。")}</div>
            <div class="delivery-report-grid">
              <section class="delivery-report-section">
                <h4>本周工作</h4>
                ${renderDeliveryList(report.weekly_work, "暂无")}
              </section>
              <section class="delivery-report-section">
                <h4>风险</h4>
                ${renderDeliveryList(report.risks, "暂无")}
              </section>
              <section class="delivery-report-section">
                <h4>遗留事项</h4>
                ${renderDeliveryList(report.pending_items, "暂无")}
              </section>
              <section class="delivery-report-section">
                <h4>下周建议</h4>
                ${renderDeliveryList(report.next_actions, "持续跟进")}
              </section>
            </div>
          </article>
        `;
      }).join("");
    }

    function renderPreviewMeta(pills) {
      previewMeta.innerHTML = (Array.isArray(pills) ? pills : [])
        .filter((item) => String(item || "").trim())
        .map((item) => `<span class="preview-pill">${escapeHtml(item)}</span>`)
        .join("");
    }

    function renderDailyLogPreviewMeta() {
      if (!dailyLogEditorState) {
        renderPreviewMeta([]);
        return;
      }
      const periodText = dailyLogEditorState.kind === "weekly_report"
        ? `周期 ${dailyLogEditorState.week_start || ""} 至 ${dailyLogEditorState.week_end || ""}`
        : `日期 ${dailyLogEditorState.work_date || ""}`;
      renderPreviewMeta([
        periodText,
        `已保存 ${dailyLogEditorState.savedFilename || ""}`,
        dailyLogEditorState.savedPath || "",
        dailyLogEditorState.sentTemplateName ? `已发送 ${dailyLogEditorState.sentTemplateName}` : "",
        dailyLogEditorState.sentAt ? `发送时间 ${dailyLogEditorState.sentAt}` : "",
        dailyLogEditorState.reportId ? `日志ID ${dailyLogEditorState.reportId}` : "",
      ]);
    }

    function getDefaultDailyLogSections() {
      return [
        { title: "1、今日工作：", items: [] },
        { title: "2、明日计划：", items: [] },
        { title: "3、风险和需要协助：", items: [] },
        { title: "4、思考和其他：", items: [] },
      ];
    }

    function normalizeDailyLogItemText(value) {
      return String(value || "").trim().replace(/^\d+\.\s*/, "");
    }

    function parseDailyLogSections(content) {
      const sections = getDefaultDailyLogSections();
      const sectionMap = new Map(sections.map((section) => [section.title, section]));
      const lines = String(content || "")
        .split(/\\r?\\n+/)
        .map((line) => line.trim())
        .filter(Boolean);
      let currentSection = null;
      let matchedSectionCount = 0;

      lines.forEach((line) => {
        if (sectionMap.has(line)) {
          currentSection = sectionMap.get(line);
          matchedSectionCount += 1;
          return;
        }
        if (!currentSection) {
          return;
        }
        currentSection.items.push(normalizeDailyLogItemText(line));
      });

      if (!matchedSectionCount && lines.length) {
        sections[0].items = lines.map((line) => normalizeDailyLogItemText(line));
      }

      return sections.map((section) => ({
        title: section.title,
        items: section.items.filter((item) => String(item || "").trim()),
      }));
    }

    function getDailyLogOutputText(section) {
      const items = Array.isArray(section && section.items)
        ? section.items.map((item) => String(item || "").trim()).filter(Boolean)
        : [];
      return items.length ? items : ["暂无"];
    }

    function renderDailyLogOutputHtml(sections) {
      return (Array.isArray(sections) ? sections : []).map((section) => {
        const blocks = getDailyLogOutputText(section)
          .map((item, index) => `<p>${index + 1}. ${escapeHtml(item)}</p>`)
          .join("");
        return `<h3>${escapeHtml(section.title || "")}</h3>${blocks}`;
      }).join("");
    }

    function renderDailyLogEditor() {
      if (!dailyLogEditorState) {
        previewContent.innerHTML = '<div class="empty">暂无可编辑的售后日报内容。</div>';
        return;
      }

      const sectionCards = dailyLogEditorState.sections.map((section, sectionIndex) => {
        const items = Array.isArray(section.items) ? section.items : [];
        const lineHtml = items.length
          ? items.map((item, itemIndex) => `
              <div class="daily-log-line">
                <div class="daily-log-line-index">${itemIndex + 1}.</div>
                <textarea
                  data-daily-log-action="edit-item"
                  data-section-index="${sectionIndex}"
                  data-item-index="${itemIndex}"
                  placeholder="请输入这一条日报内容">${escapeHtml(item)}</textarea>
                <button
                  type="button"
                  class="danger mini-btn"
                  data-daily-log-action="remove-item"
                  data-section-index="${sectionIndex}"
                  data-item-index="${itemIndex}">删除</button>
              </div>
            `).join("")
          : '<div class="daily-log-empty">当前小节暂无内容，可点击右侧“新增一条”继续补充。</div>';

        return `
          <section class="preview-card daily-log-section">
            <div class="daily-log-section-head">
              <div>
                <h3 class="daily-log-section-title">${escapeHtml(section.title || "")}</h3>
                <p class="daily-log-section-note">支持直接修改文案，也可以新增或删除条目后再发送。</p>
              </div>
              <button
                type="button"
                class="soft"
                data-daily-log-action="add-item"
                data-section-index="${sectionIndex}">新增一条</button>
            </div>
            <div class="daily-log-lines">${lineHtml}</div>
          </section>
        `;
      }).join("");

      previewContent.innerHTML = `
        <section class="preview-card daily-log-intro-card">
          <p class="daily-log-intro-text">已生成 ${escapeHtml(dailyLogEditorState.work_date || "")} 的售后日报草稿，可直接在下方修改四个固定小节，底部同步预览发送内容。</p>
        </section>
        <div class="daily-log-editor">${sectionCards}</div>
        <section class="preview-card">
          <h3 class="daily-log-output-head">发送前预览</h3>
          <div class="preview-richtext">${renderDailyLogOutputHtml(dailyLogEditorState.sections)}</div>
        </section>
      `;
    }

    function renderDailyLogPreview(payload, previewSessionId = activePreviewSessionId) {
      dailyLogEditorState = {
        kind: "daily_log",
        previewSessionId,
        work_date: payload.work_date || "",
        sections: parseDailyLogSections(payload.content || ""),
        rawContent: String(payload.content || ""),
        savedFilename: payload.saved_filename || "",
        savedPath: payload.saved_path || "",
        templateName: payload.send_config && payload.send_config.template_name || "未选择模板",
        templateConfigured: Boolean(payload.send_config && payload.send_config.template_source === "user"),
        sentTemplateName: "",
        sentAt: "",
        reportId: "",
        toChat: Boolean(payload.send_config && payload.send_config.to_chat),
        configuredRecipients: Array.isArray(payload.send_config && payload.send_config.base_recipients)
          ? payload.send_config.base_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : [],
        extraRecipients: Array.isArray(payload.send_config && payload.send_config.last_recipients)
          ? payload.send_config.last_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : [],
      };
      previewTitle.textContent = payload.title || "发送售后日报";
      previewSubtitle.textContent = `${payload.work_date || ""} 的售后日报已生成，可在弹窗内增删和修改内容；原始 Word 文件已保存到 logs/用户名/daily_logs 目录。${dailyLogEditorState.templateConfigured ? "" : " 当前用户尚未选择日报模板，暂时无法发送。"}`;
      renderDailyLogPreviewMeta();
      syncPreviewActionButtons();
      renderDailyLogEditor();
    }

    function renderWeeklyReportOutputHtml(sections) {
      return (Array.isArray(sections) ? sections : []).map((section) => `
        <h3>${escapeHtml(section.title || "")}</h3>
        <pre>${escapeHtml(String(section.content || "").trim() || "暂无")}</pre>
      `).join("");
    }

    function renderWeeklyReportEditor() {
      if (!dailyLogEditorState || dailyLogEditorState.kind !== "weekly_report") {
        previewContent.innerHTML = '<div class="empty">暂无可编辑的周报内容。</div>';
        return;
      }

      const sectionCards = dailyLogEditorState.sections.map((section, sectionIndex) => `
        <section class="preview-card weekly-report-section">
          <div class="daily-log-section-head">
            <div>
              <h3 class="daily-log-section-title">${escapeHtml(section.title || "")}</h3>
              <p class="daily-log-section-note">支持直接修改这一小节内容，发送前预览会同步更新。</p>
            </div>
          </div>
          <textarea
            class="weekly-report-section-textarea"
            data-weekly-report-field="content"
            data-section-index="${sectionIndex}"
            placeholder="请输入这一小节周报内容">${escapeHtml(section.content || "")}</textarea>
        </section>
      `).join("");

      previewContent.innerHTML = `
        <section class="preview-card daily-log-intro-card">
          <p class="daily-log-intro-text">已为 ${escapeHtml(dailyLogEditorState.week_start || "")} 至 ${escapeHtml(dailyLogEditorState.week_end || "")} 生成周报草稿。你可以继续调整五个固定小节，底部会同步展示整理后的发送内容。</p>
        </section>
        <div class="weekly-report-editor">${sectionCards}</div>
        <section class="preview-card">
          <h3 class="daily-log-output-head">发送前预览</h3>
          <div class="preview-richtext" id="weekly-report-output">${renderWeeklyReportOutputHtml(dailyLogEditorState.sections)}</div>
        </section>
      `;
    }

    function renderWeeklyReportPreview(payload, previewSessionId = activePreviewSessionId) {
      dailyLogEditorState = {
        kind: "weekly_report",
        previewSessionId,
        anchorDate: payload.anchor_date || dateInput.value || "",
        requestedAnchorDate: payload.requested_anchor_date || payload.anchor_date || dateInput.value || "",
        requestedWeekStart: payload.requested_week_start || payload.week_start || "",
        usedFallbackWeek: Boolean(payload.used_fallback_week),
        usedGeneratedFallback: Boolean(payload.used_generated_fallback),
        generationNotice: String(payload.generation_notice || "").trim(),
        week_start: payload.week_start || "",
        week_end: payload.week_end || "",
        sections: Array.isArray(payload.sections)
          ? payload.sections.map((section) => ({
              title: String(section && section.title || "").trim(),
              content: String(section && section.content || "").trim(),
            }))
          : [],
        rawContent: String(payload.content || ""),
        savedFilename: payload.saved_filename || "",
        savedPath: payload.saved_path || "",
        templateName: normalizeWeeklyReportTemplateDisplayName(payload.send_config && payload.send_config.template_name),
        templateConfigured: Boolean(payload.send_config && payload.send_config.template_source === "user"),
        sentTemplateName: "",
        sentAt: "",
        reportId: "",
        toChat: Boolean(payload.send_config && payload.send_config.to_chat),
        configuredRecipients: Array.isArray(payload.send_config && payload.send_config.base_recipients)
          ? payload.send_config.base_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : [],
        extraRecipients: Array.isArray(payload.send_config && payload.send_config.last_recipients)
          ? payload.send_config.last_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : [],
      };
      previewTitle.textContent = payload.title || "发送周报";
      const subtitleParts = [
        payload.used_fallback_week
          ? `${payload.week_start || ""} 至 ${payload.week_end || ""} 的周报已生成；当前所选日期所在周暂无记录，已自动切换到最近有记录的一周。`
          : `${payload.week_start || ""} 至 ${payload.week_end || ""} 的周报已生成，可在弹窗内继续调整内容。`,
      ];
      if (payload.generation_notice) {
        subtitleParts.push(String(payload.generation_notice || "").trim());
      }
      subtitleParts.push("原始 Word 文件已保存到 logs/用户名/weekly_reports 目录。");
      if (!dailyLogEditorState.templateConfigured) {
        subtitleParts.push("当前用户尚未选择周报模板，暂时无法发送。");
      }
      previewSubtitle.textContent = subtitleParts.join("");
      renderDailyLogPreviewMeta();
      syncPreviewActionButtons();
      renderWeeklyReportEditor();
    }

    function renderWeeklyStrengthPreview(payload) {
      dailyLogEditorState = null;
      syncPreviewActionButtons();
      previewTitle.textContent = payload.title || "本周兵力盘点预览";
      previewSubtitle.textContent = `${payload.week_start || ""} 至 ${payload.week_end || ""} 的兵力盘点预览，原始 Excel 文件已保存到 logs/用户名/weekly_strength 目录。`;
      renderPreviewMeta([
        `周期 ${payload.week_start || ""} 至 ${payload.week_end || ""}`,
        `已保存 ${payload.saved_filename || ""}`,
        payload.saved_path || "",
      ]);

      const summaryList = (payload.summary_lines || [])
        .filter((line) => String(line || "").trim())
        .map((line) => `<li>${escapeHtml(line)}</li>`)
        .join("");
      const headerHtml = (payload.headers || []).map((header) => `<th>${escapeHtml(header)}</th>`).join("");
      const rowHtml = (payload.rows || []).map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
      const footerList = (payload.footer_lines || [])
        .filter((line) => String(line || "").trim())
        .map((line) => `<li>${escapeHtml(line)}</li>`)
        .join("");

      previewContent.innerHTML = `
        <section class="preview-card">
          <ul class="preview-list">${summaryList || "<li>暂无摘要。</li>"}</ul>
        </section>
        <section class="preview-card">
          <div class="preview-table-wrap">
            <table class="preview-table">
              <thead><tr>${headerHtml}</tr></thead>
              <tbody>${rowHtml || '<tr><td colspan="5">暂无数据。</td></tr>'}</tbody>
            </table>
          </div>
        </section>
        <section class="preview-card">
          <ul class="preview-list">${footerList || "<li>暂无补充说明。</li>"}</ul>
        </section>
      `;
    }

    async function openDailyLogPreview() {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择要查看日志的日期。", "warning");
        return;
      }
      const previewSession = beginPreviewSession();
      setPreviewOpen(true);
      previewTitle.textContent = "发送售后日报";
      previewSubtitle.textContent = `${targetDate} 的售后日报正在生成，请稍候。`;
      renderPreviewMeta([]);
      previewContent.innerHTML = '<div class="empty">Codex 正在生成售后日报草稿，并保存 Word 文件到 logs/用户名/daily_logs 目录，请稍候...</div>';
      try {
        const response = await fetch(`/api/preview-log?date=${encodeURIComponent(targetDate)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "售后日报生成失败");
        }
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        renderDailyLogPreview(payload, previewSession.previewSessionId);
        setStatus(`已打开 ${targetDate} 的售后日报，可继续在弹窗内编辑内容。`, "success");
      } catch (error) {
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        previewSubtitle.textContent = "售后日报生成失败。";
        previewContent.innerHTML = `<div class="empty">${escapeHtml(error.message || "售后日报生成失败。")}</div>`;
        setStatus(error.message || "售后日报生成失败。", "error");
      }
    }

    async function openWeeklyReportPreview() {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择要查看周报的日期。", "warning");
        return;
      }
      const previewSession = beginPreviewSession();
      setPreviewOpen(true);
      previewTitle.textContent = "发送周报";
      previewSubtitle.textContent = `${targetDate} 所在周的周报正在生成，请稍候。`;
      renderPreviewMeta([]);
      previewContent.innerHTML = '<div class="empty">Codex 正在分析本周事项并生成周报草稿，请稍候...</div>';
      try {
        const response = await fetch(`/api/preview-weekly-report?date=${encodeURIComponent(targetDate)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "周报生成失败");
        }
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        renderWeeklyReportPreview(payload, previewSession.previewSessionId);
        const successMessages = [];
        if (payload.used_fallback_week) {
          successMessages.push(`当前所选日期所在周暂无记录，已自动打开最近有记录的一周：${payload.week_start} 至 ${payload.week_end}。`);
        } else {
          successMessages.push(`已打开 ${payload.week_start} 至 ${payload.week_end} 的周报，可继续在弹窗内编辑内容。`);
        }
        if (payload.generation_notice) {
          successMessages.push(String(payload.generation_notice || "").trim());
        }
        setStatus(successMessages.join(" "), "success");
      } catch (error) {
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        previewSubtitle.textContent = "周报生成失败。";
        previewContent.innerHTML = `<div class="empty">${escapeHtml(error.message || "周报生成失败。")}</div>`;
        setStatus(error.message || "周报生成失败。", "error");
      }
    }

    async function openWeeklyStrengthPreview() {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择要查看兵力盘点的日期。", "warning");
        return;
      }
      const previewSession = beginPreviewSession();
      setPreviewOpen(true);
      previewTitle.textContent = "本周兵力盘点预览";
      previewSubtitle.textContent = `${targetDate} 所在周的兵力盘点正在生成，请稍候。`;
      renderPreviewMeta([]);
      previewContent.innerHTML = '<div class="empty">正在生成本周兵力盘点预览，并保存原始 Excel 文件到 logs/用户名/weekly_strength 目录，请稍候...</div>';
      try {
        const response = await fetch(`/api/preview-weekly-strength?date=${encodeURIComponent(targetDate)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "本周兵力盘点预览生成失败");
        }
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        renderWeeklyStrengthPreview(payload);
        setStatus(`已生成 ${payload.week_start} 至 ${payload.week_end} 的兵力盘点预览，并保存原始文件到 logs/用户名/weekly_strength 目录。`, "success");
      } catch (error) {
        if (!isPreviewSessionActive(previewSession.previewSessionId, previewSession.scopeMarker)) {
          return;
        }
        previewSubtitle.textContent = "本周兵力盘点预览生成失败。";
        previewContent.innerHTML = `<div class="empty">${escapeHtml(error.message || "本周兵力盘点预览生成失败。")}</div>`;
        setStatus(error.message || "本周兵力盘点预览生成失败。", "error");
      }
    }

    async function sendDailyLogToDingtalk() {
      if (!dailyLogEditorState || !["daily_log", "weekly_report"].includes(dailyLogEditorState.kind)) {
        setStatus("请先生成并确认要发送的日志内容。", "warning");
        return;
      }
      setSendConfirmOpen(true);
    }

    async function confirmDailyLogSend() {
      if (!dailyLogEditorState || !["daily_log", "weekly_report"].includes(dailyLogEditorState.kind)) {
        setStatus("请先生成并确认要发送的日志内容。", "warning");
        return;
      }
      const previewSessionId = Number(dailyLogEditorState.previewSessionId || 0);
      const scopeMarker = getCurrentScopeAsyncMarker();
      const sendOperationId = activeSendOperationId + 1;
      activeSendOperationId = sendOperationId;
      const invalidRecipient = (dailyLogEditorState.extraRecipients || []).find((recipient) => {
        const normalized = normalizeDailyLogRecipient(recipient);
        return (normalized.name || normalized.user_id) && !normalized.user_id;
      });
      if (invalidRecipient) {
        setStatus("新增人员至少需要填写 userId，姓名可选。", "warning");
        showSendResultToast("发送前请完善信息", "新增人员至少需要填写 userId，姓名可选。", "error");
        return;
      }
      const isWeeklyReport = dailyLogEditorState.kind === "weekly_report";
      const reportName = isWeeklyReport ? "周报" : "售后日报";
      if (dailyLogEditorState.templateConfigured === false) {
        const templateWarning = isWeeklyReport
          ? "当前用户还未选择周报模板，请先到右上角“钉钉MCP”里读取并选择。"
          : "当前用户还未选择日报模板，请先到右上角“钉钉MCP”里读取并选择。";
        setStatus(templateWarning, "warning");
        showSendResultToast("无法发送", templateWarning, "error");
        return;
      }
      setDailyLogSendState(true);
      syncSendConfirmButtons();
      setStatus("正在发送日志到钉钉...", "success");
      previewSubtitle.textContent = isWeeklyReport
        ? `${dailyLogEditorState.week_start || ""} 至 ${dailyLogEditorState.week_end || ""} 的周报正在通过所选钉钉模板发送，请稍候。`
        : `${dailyLogEditorState.work_date || ""} 的售后日报正在通过所选钉钉模板发送，请稍候。`;
      try {
        const response = await fetch(isWeeklyReport ? "/api/send-weekly-report" : "/api/send-daily-log", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            isWeeklyReport
              ? {
                  work_date: dailyLogEditorState.anchorDate || dateInput.value,
                  week_start: dailyLogEditorState.week_start || "",
                  week_end: dailyLogEditorState.week_end || "",
                  sections: dailyLogEditorState.sections || [],
                  to_chat: Boolean(dailyLogEditorState.toChat),
                  recipients: dailyLogEditorState.extraRecipients || [],
                }
              : {
                  work_date: dailyLogEditorState.work_date || dateInput.value,
                  sections: dailyLogEditorState.sections || [],
                  to_chat: Boolean(dailyLogEditorState.toChat),
                  recipients: dailyLogEditorState.extraRecipients || [],
                }
          )
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "发送日志失败");
        }
        if (
          !isPreviewSessionActive(previewSessionId, scopeMarker)
          || activeSendOperationId !== sendOperationId
        ) {
          return;
        }
        dailyLogEditorState.sentTemplateName = isWeeklyReport
          ? normalizeWeeklyReportTemplateDisplayName(payload.template_name)
          : (payload.template_name || "未选择模板");
        dailyLogEditorState.sentAt = payload.sent_at || "";
        dailyLogEditorState.reportId = payload.report_id || "";
        dailyLogEditorState.toChat = Boolean(payload.to_chat);
        dailyLogEditorState.templateConfigured = Boolean(payload.template_id);
        dailyLogEditorState.configuredRecipients = Array.isArray(payload.base_recipients)
          ? payload.base_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : dailyLogEditorState.configuredRecipients;
        dailyLogEditorState.extraRecipients = Array.isArray(payload.last_recipients)
          ? payload.last_recipients.map((recipient) => normalizeDailyLogRecipient(recipient))
          : dailyLogEditorState.extraRecipients;
        renderDailyLogPreviewMeta();
        setSendConfirmOpen(false);
        previewSubtitle.textContent = isWeeklyReport
          ? `${dailyLogEditorState.week_start || ""} 至 ${dailyLogEditorState.week_end || ""} 的周报已通过所选钉钉模板发送。`
          : `${dailyLogEditorState.work_date || ""} 的售后日报已通过所选钉钉模板发送。`;
        setStatus(payload.message || "日志已发送。", "success");
        showSendResultToast("发送成功", payload.message || `${reportName}发送成功。`, "success");
      } catch (error) {
        if (
          !isPreviewSessionActive(previewSessionId, scopeMarker)
          || activeSendOperationId !== sendOperationId
        ) {
          return;
        }
        previewSubtitle.textContent = isWeeklyReport
          ? `${dailyLogEditorState.week_start || ""} 至 ${dailyLogEditorState.week_end || ""} 的周报发送失败，请检查后重试。`
          : `${dailyLogEditorState.work_date || ""} 的售后日报发送失败，请检查后重试。`;
        setStatus(error.message || "发送日志失败。", "error");
        showSendResultToast("发送失败", error.message || "发送日志失败，请稍后重试。", "error");
      } finally {
        if (
          isPreviewSessionActive(previewSessionId, scopeMarker)
          && activeSendOperationId === sendOperationId
        ) {
          setDailyLogSendState(false);
          syncSendConfirmButtons();
        }
      }
    }

    async function openDeliveryProgress(forceRefresh = false) {
      const shouldForceRefresh = forceRefresh === true;
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择要查看交付进展的日期。", "warning");
        return;
      }

      const deliverySession = beginDeliveryProgressSession();
      setDeliveryProgressOpen(true);
      setDeliveryProgressLoading(true, shouldForceRefresh);
      deliveryProgressSubtitle.textContent = shouldForceRefresh
        ? `${targetDate} 所在周正在根据最新情况重新生成交付项目周报，请稍候。`
        : `${targetDate} 所在周正在读取上次生成的交付项目周报，请稍候。`;
      deliveryProgressMeta.innerHTML = "";
      deliveryProgressList.innerHTML = `<div class="empty">${shouldForceRefresh ? "Codex 正在根据最新记录重新分析本周交付项目，请稍候..." : "正在优先读取本周已生成的交付项目周报，如无历史结果再自动生成，请稍候..."}</div>`;

      try {
        if (!shouldForceRefresh) {
          const serverCachedPayload = await fetchDeliveryProgressServerCache(targetDate);
          if (!isDeliveryProgressSessionActive(deliverySession.deliveryProgressSessionId, deliverySession.scopeMarker)) {
            return;
          }
          if (serverCachedPayload) {
            saveDeliveryProgressCache(targetDate, serverCachedPayload);
            renderDeliveryProgressReports(serverCachedPayload);
            setStatus(`已加载 ${serverCachedPayload.week_start} 至 ${serverCachedPayload.week_end} 的上次交付项目分析结果。`, "success");
            return;
          }
        }

        if (!shouldForceRefresh) {
          deliveryProgressSubtitle.textContent = `${targetDate} 所在周暂无已生成的交付项目周报，正在根据本周记录生成，请稍候。`;
          deliveryProgressList.innerHTML = '<div class="empty">本周暂无已生成的交付项目周报，Codex 正在根据本周交付记录生成，请稍候...</div>';
        }

        const query = shouldForceRefresh ? `date=${encodeURIComponent(targetDate)}&force=1` : `date=${encodeURIComponent(targetDate)}`;
        const response = await fetch(`/api/delivery-progress?${query}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "交付进展读取失败");
        }
        if (!isDeliveryProgressSessionActive(deliverySession.deliveryProgressSessionId, deliverySession.scopeMarker)) {
          return;
        }
        saveDeliveryProgressCache(targetDate, payload);
        renderDeliveryProgressReports(payload);
        setStatus(
          payload.source === "cache"
            ? `已加载 ${payload.week_start} 至 ${payload.week_end} 的上次交付项目分析结果。`
            : `已重新生成 ${payload.week_start} 至 ${payload.week_end} 的交付项目周报。`,
          "success"
        );
      } catch (error) {
        if (!isDeliveryProgressSessionActive(deliverySession.deliveryProgressSessionId, deliverySession.scopeMarker)) {
          return;
        }
        const localCachedPayload = !shouldForceRefresh ? loadDeliveryProgressCache(targetDate) : null;
        if (localCachedPayload) {
          renderDeliveryProgressReports(localCachedPayload);
          setStatus(`服务器缓存读取失败，已回退展示 ${localCachedPayload.week_start} 至 ${localCachedPayload.week_end} 的本地交付项目分析结果。`, "warning");
          return;
        }
        deliveryProgressSubtitle.textContent = "交付项目周报生成失败。";
        deliveryProgressMeta.innerHTML = "";
        deliveryProgressList.innerHTML = `<div class="empty">${escapeHtml(error.message || "交付进展生成失败。")}</div>`;
        setStatus(error.message || "交付进展生成失败。", "error");
      } finally {
        if (isDeliveryProgressSessionActive(deliverySession.deliveryProgressSessionId, deliverySession.scopeMarker)) {
          setDeliveryProgressLoading(false);
        }
      }
    }

    function getWeekStartString(value) {
      if (!value) {
        return "";
      }
      return formatDate(getMonday(parseDateString(value)));
    }

    function updateWeeklyPlanRange(anchorDate) {
      if (!anchorDate) {
        weeklyPlanRange.textContent = "每周工作安排：按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。";
        return;
      }
      const monday = getMonday(parseDateString(anchorDate));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      weeklyPlanRange.textContent = `每周工作安排：${formatDate(monday)} 至 ${formatDate(sunday)} · 按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。`;
    }

    function setWeeklyPlanSavedAtText(text) {
      weeklyPlanSavedAt.textContent = text;
    }

    function updateWeeklyPlanSavedAt(value) {
      setWeeklyPlanSavedAtText(value ? `最近保存：${value}` : "最近保存：未保存");
    }

    function parseDateString(value) {
      const [year, month, day] = value.split("-").map(Number);
      return new Date(year, month - 1, day);
    }

    function formatDate(dateValue) {
      const year = dateValue.getFullYear();
      const month = String(dateValue.getMonth() + 1).padStart(2, "0");
      const day = String(dateValue.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    }

    function formatDateTime(dateValue) {
      return `${formatDate(dateValue)} ${String(dateValue.getHours()).padStart(2, "0")}:${String(dateValue.getMinutes()).padStart(2, "0")}:${String(dateValue.getSeconds()).padStart(2, "0")}`;
    }

    function getMonday(dateValue) {
      const result = new Date(dateValue);
      const offset = (result.getDay() + 6) % 7;
      result.setDate(result.getDate() - offset);
      return result;
    }

    function getCurrentSettings() {
      const payload = {};
      Object.entries(weeklyScheduleInputs).forEach(([key, input]) => {
        payload[key] = input.value.trim();
      });
      return payload;
    }

    function normalizeWeeklyPlanPayload(settings) {
      const payload = {};
      Object.keys(weeklyScheduleInputs).forEach((key) => {
        payload[key] = String(settings && settings[key] || "").trim();
      });
      return payload;
    }

    function applyPageSettings(settings) {
      const normalizedSettings = normalizeWeeklyPlanPayload(settings);
      Object.entries(weeklyScheduleInputs).forEach(([key, input]) => {
        input.value = normalizedSettings[key] || "";
      });
    }

    function getWeeklyPlanSnapshot(weekStart, settings) {
      return JSON.stringify({
        week_start: weekStart || "",
        settings: normalizeWeeklyPlanPayload(settings)
      });
    }

    function rememberWeeklyPlanServerBaseline(weekStart, settings, updatedAt) {
      if (!weekStart) {
        return;
      }
      const snapshot = getWeeklyPlanSnapshot(weekStart, settings);
      weeklyPlanSavedSnapshots.set(weekStart, snapshot);
      weeklyPlanSavedUpdatedAts.set(weekStart, String(updatedAt || ""));
    }

    function rememberWeeklyPlanState(weekStart, settings, updatedAt) {
      if (!weekStart) {
        return;
      }
      const snapshot = getWeeklyPlanSnapshot(weekStart, settings);
      rememberWeeklyPlanServerBaseline(weekStart, settings, updatedAt);
      const localDraft = loadWeeklyPlanDraft(weekStart);
      if (snapshot === getWeeklyPlanSnapshot(weekStart, localDraft && localDraft.settings || {})) {
        clearWeeklyPlanDraft(weekStart);
      }
      if (currentWeeklyPlanWeekStart === weekStart) {
        updateWeeklyPlanSavedAt(updatedAt || "");
      }
    }

    function cancelWeeklyPlanAutosave() {
      if (weeklyPlanAutosaveTimer) {
        window.clearTimeout(weeklyPlanAutosaveTimer);
        weeklyPlanAutosaveTimer = null;
      }
    }

    async function savePageSettings(options = {}) {
      const weekStart = options.weekStart || currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      const settings = normalizeWeeklyPlanPayload(options.settings || getCurrentSettings());
      const silent = Boolean(options.silent);
      const force = Boolean(options.force);
      const payload = {
        week_start: weekStart,
        settings
      };
      if (!weekStart) {
        if (!silent) {
          setStatus("未找到当前周信息。", "warning");
        }
        return false;
      }
      const snapshot = getWeeklyPlanSnapshot(weekStart, settings);
      if (!force && snapshot === (weeklyPlanSavedSnapshots.get(weekStart) || "")) {
        if (!silent) {
          setStatus("每周工作安排已是最新。", "success");
        }
        return true;
      }
      const requestMeta = registerScopedAsyncRequest("weekly-plan-save", weekStart);
      const requestId = ++weeklyPlanSaveSequence;
      weeklyPlanLatestRequestIds.set(weekStart, requestId);
      if (silent && currentWeeklyPlanWeekStart === weekStart) {
        setWeeklyPlanSavedAtText("自动保存中...");
      }
      try {
        const response = await fetch("/api/weekly-plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存每周工作安排失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return true;
        }
        const savedWeekStart = data.week_start || weekStart;
        const savedSettings = data.settings || {};
        if (weeklyPlanLatestRequestIds.get(savedWeekStart) !== requestId) {
          return true;
        }
        rememberWeeklyPlanState(savedWeekStart, savedSettings, data.updated_at || "");
        announceWeeklyPlanSync(getActiveScopeUserId(), savedWeekStart, data.updated_at || "");
        if (currentWeeklyPlanWeekStart === savedWeekStart) {
          applyPageSettings(savedSettings);
          if (!silent) {
            setStatus("每周工作安排已保存。", "success");
          }
        }
        return true;
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return false;
        }
        if (currentWeeklyPlanWeekStart === weekStart) {
          setWeeklyPlanSavedAtText("自动保存失败，请稍后重试");
        }
        setStatus(error.message || "保存每周工作安排失败。", "error");
        return false;
      }
    }

    function scheduleWeeklyPlanAutosave() {
      const weekStart = currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      if (!weekStart) {
        return;
      }
      const settings = getCurrentSettings();
      if (getWeeklyPlanSnapshot(weekStart, settings) === (weeklyPlanSavedSnapshots.get(weekStart) || "")) {
        cancelWeeklyPlanAutosave();
        return;
      }
      cancelWeeklyPlanAutosave();
      setWeeklyPlanSavedAtText("自动保存中...");
      weeklyPlanAutosaveTimer = window.setTimeout(() => {
        weeklyPlanAutosaveTimer = null;
        savePageSettings({
          weekStart,
          settings,
          silent: true
        });
      }, WEEKLY_PLAN_AUTOSAVE_DELAY_MS);
    }

    async function clearWeeklyPlan() {
      const weekStart = currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      if (!weekStart) {
        setStatus("未找到当前周信息。", "warning");
        return;
      }
      if (!window.confirm(`确认清除 ${weekStart} 这一周的全部工作安排吗？`)) {
        return;
      }
      cancelWeeklyPlanAutosave();
      const requestMeta = registerScopedAsyncRequest("weekly-plan-clear", weekStart);
      try {
        const response = await fetch("/api/weekly-plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            week_start: weekStart,
            settings: {}
          })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "清除本周安排失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        const clearedWeekStart = data.week_start || weekStart;
        const clearedSettings = data.settings || {};
        rememberWeeklyPlanState(clearedWeekStart, clearedSettings, data.updated_at || "");
        clearWeeklyPlanDraft(clearedWeekStart);
        announceWeeklyPlanSync(getActiveScopeUserId(), clearedWeekStart, data.updated_at || "");
        if (currentWeeklyPlanWeekStart === clearedWeekStart) {
          currentWeeklyPlanWeekStart = clearedWeekStart;
          applyPageSettings(clearedSettings);
        }
        setStatus("本周工作安排已清除。", "success");
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        setStatus(error.message || "清除本周安排失败。", "error");
      }
    }

    async function loadWeeklyPlan(anchorDate, showMessage = false) {
      if (!anchorDate) {
        return;
      }
      const weekStart = getWeekStartString(anchorDate);
      const localDraft = loadWeeklyPlanDraft(weekStart);
      currentWeeklyPlanWeekStart = weekStart;
      updateWeeklyPlanRange(anchorDate);
      const requestMeta = registerScopedAsyncRequest("weekly-plan-load", weekStart);
      try {
        const response = await fetch(`/api/weekly-plan?date=${encodeURIComponent(anchorDate)}`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取每周工作安排失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        currentWeeklyPlanWeekStart = data.week_start || weekStart;
        const serverSettings = normalizeWeeklyPlanPayload(data.settings || {});
        const serverUpdatedAt = String(data.updated_at || "");
        const localDraftSnapshot = localDraft ? getWeeklyPlanSnapshot(localDraft.week_start, localDraft.settings || {}) : "";
        const serverSnapshot = getWeeklyPlanSnapshot(currentWeeklyPlanWeekStart, serverSettings);
        const localDraftHasContent = Boolean(localDraft && hasMeaningfulWeeklyPlanContent(localDraft.settings || {}));
        const serverHasContent = hasMeaningfulWeeklyPlanContent(serverSettings);
        const draftBaseSnapshot = String(localDraft && localDraft.base_snapshot || "");
        const draftBaseUpdatedAt = String(localDraft && localDraft.base_updated_at || "");
        rememberWeeklyPlanServerBaseline(currentWeeklyPlanWeekStart, serverSettings, serverUpdatedAt);
        const draftStillMatchesServerBaseline = Boolean(
          localDraft
            && (
              (draftBaseSnapshot && draftBaseSnapshot === serverSnapshot)
              || (!draftBaseSnapshot && draftBaseUpdatedAt && draftBaseUpdatedAt === serverUpdatedAt)
              || (!draftBaseSnapshot && !draftBaseUpdatedAt && !serverHasContent)
            )
        );
        const shouldRestoreLocalDraft = Boolean(
          localDraft
            && localDraft.week_start === currentWeeklyPlanWeekStart
            && localDraftHasContent
            && localDraftSnapshot !== serverSnapshot
            && draftStillMatchesServerBaseline
        );

        if (shouldRestoreLocalDraft) {
          applyPageSettings(localDraft.settings || {});
          updateWeeklyPlanSavedAt(localDraft.updated_at || "");
        } else {
          if (localDraft && (!localDraftHasContent || !draftStillMatchesServerBaseline) && serverHasContent) {
            clearWeeklyPlanDraft(currentWeeklyPlanWeekStart);
          }
          applyPageSettings(serverSettings);
          rememberWeeklyPlanState(currentWeeklyPlanWeekStart, serverSettings, serverUpdatedAt);
        }
        if (showMessage) {
          setStatus(
            shouldRestoreLocalDraft
              ? `已恢复 ${currentWeeklyPlanWeekStart} 本周安排的本地暂存内容。`
              : `已读取 ${currentWeeklyPlanWeekStart} 所在周的工作安排。`,
            "success"
          );
        }
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        if (localDraft && localDraft.week_start === weekStart) {
          applyPageSettings(localDraft.settings || {});
          updateWeeklyPlanSavedAt(localDraft.updated_at || "");
          if (showMessage) {
            setStatus(`接口读取失败，已恢复 ${weekStart} 本周安排的本地暂存内容。`, "warning");
          }
          return;
        }
        applyPageSettings({});
        weeklyPlanSavedSnapshots.delete(weekStart);
        weeklyPlanSavedUpdatedAts.delete(weekStart);
        updateWeeklyPlanSavedAt("");
        if (showMessage) {
          setStatus(error.message || "读取每周工作安排失败。", "error");
        }
      }
    }

    function makeBlankItem() {
      return {
        customer_name: "",
        project_type: "",
        sales: "",
        item_type: "",
        service_mode: "",
        work_hours: "",
        work_content: "",
        pending_issues: "",
        risk: ""
      };
    }

    function syncMonthFromDate() {
      if (dateInput.value) {
        monthInput.value = dateInput.value.slice(0, 7);
      }
    }

    function renderWeekButtons(anchorDateString = dateInput.value) {
      if (!anchorDateString) {
        return;
      }

      const weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
      const monday = getMonday(parseDateString(anchorDateString));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      weekRange.textContent = `${formatDate(monday)} 至 ${formatDate(sunday)}`;
      weekStrip.innerHTML = "";

      weekdays.forEach((label, index) => {
        const day = new Date(monday);
        day.setDate(monday.getDate() + index);
        const value = formatDate(day);
        const button = document.createElement("button");
        button.type = "button";
        const isWeekend = index >= 5;
        button.className = "week-btn" + (isWeekend ? " weekend" : "") + (value === dateInput.value ? " active" : "");
        button.innerHTML = `
          <span class="week-btn-name">${label}</span>
          <span class="week-btn-date">${value.slice(5)}</span>
        `;
        button.addEventListener("click", () => {
          persistCurrentEntryDraft();
          dateInput.value = value;
          rememberWorkDate(value);
          syncMonthFromDate();
          renderWeekButtons(value);
          loadWeeklyPlan(value);
          loadDateEntry(value);
          refreshRecentEntries(value);
          refreshMonthEntries();
          warmDeliveryProgressCache(value);
        });
        weekStrip.appendChild(button);
      });
    }

    function shiftWeek(offsetDays) {
      persistCurrentEntryDraft();
      const current = dateInput.value ? parseDateString(dateInput.value) : new Date();
      current.setDate(current.getDate() + offsetDays);
      const nextDate = formatDate(current);
      dateInput.value = nextDate;
      rememberWorkDate(nextDate);
      syncMonthFromDate();
      renderWeekButtons(nextDate);
      loadWeeklyPlan(nextDate, true);
      loadDateEntry(nextDate);
      refreshRecentEntries(nextDate);
      refreshMonthEntries();
      warmDeliveryProgressCache(nextDate);
    }

    function rowTemplate(item = makeBlankItem(), index = 0) {
      const row = document.createElement("div");
      row.className = "item-row";
      const projectType = item.project_type || "";
      const hasCustomProjectType = projectType && !projectTypeOptions.includes(projectType);
      const projectTypeHtml = projectTypeOptions.map((option) => {
        const selected = option === projectType ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const sales = item.sales || "";
      const hasCustomSales = sales && !salesOptions.includes(sales);
      const salesHtml = salesOptions.map((option) => {
        const selected = option === sales ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const itemType = item.item_type || "";
      const hasCustomType = itemType && !itemTypeOptions.includes(itemType);
      const optionsHtml = itemTypeOptions.map((option) => {
        const selected = option === itemType ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const serviceMode = item.service_mode || "";
      const hasCustomServiceMode = serviceMode && !serviceModeOptions.includes(serviceMode);
      const serviceModeHtml = serviceModeOptions.map((option) => {
        const selected = option === serviceMode ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      row.innerHTML = `
        <div class="base-info-cell">
          <div class="base-info-stack">
            <label class="base-info-line">
              <span>客户名称：</span>
              <input type="text" data-field="customer_name" list="customer-name-options" autocomplete="off" value="${escapeHtml(item.customer_name || "")}" placeholder="请输入客户名称">
            </label>
            <label class="base-info-line">
              <span>项目类型：</span>
              <select data-field="project_type">
                <option value="">请选择项目类型</option>
                ${projectTypeHtml}
                ${hasCustomProjectType ? `<option value="${escapeHtml(projectType)}" selected>${escapeHtml(projectType)}</option>` : ""}
              </select>
            </label>
            <label class="base-info-line">
              <span>销售：</span>
              <select data-field="sales">
                <option value="">请选择销售</option>
                ${salesHtml}
                ${hasCustomSales ? `<option value="${escapeHtml(sales)}" selected>${escapeHtml(sales)}</option>` : ""}
              </select>
            </label>
          </div>
        </div>
        <div class="service-content-cell">
          <div class="service-content-stack">
            <label class="service-content-line">
              <span>类型：</span>
              <select data-field="item_type">
                <option value="">请选择类型</option>
                ${optionsHtml}
                ${hasCustomType ? `<option value="${escapeHtml(itemType)}" selected>${escapeHtml(itemType)}</option>` : ""}
              </select>
            </label>
            <label class="service-content-line">
              <span>服务方式：</span>
              <select data-field="service_mode">
                <option value="">请选择服务方式</option>
                ${serviceModeHtml}
                ${hasCustomServiceMode ? `<option value="${escapeHtml(serviceMode)}" selected>${escapeHtml(serviceMode)}</option>` : ""}
              </select>
            </label>
            <label class="service-content-line">
              <span>工时：</span>
              <input type="number" data-field="work_hours" min="0" step="0.5" value="${escapeHtml(String(firstDefinedValue(item.work_hours, "")))}" placeholder="请输入工时">
            </label>
          </div>
        </div>
        <div><textarea data-field="work_content" placeholder="工作内容">${escapeHtml(item.work_content || "")}</textarea></div>
        <div class="issue-risk-cell">
          <div class="issue-risk-stack">
            <label class="issue-risk-line">
              <span>遗留事项</span>
              <textarea data-field="pending_issues" placeholder="请输入遗留事项">${escapeHtml(item.pending_issues || "")}</textarea>
            </label>
            <label class="issue-risk-line">
              <span>存在风险</span>
              <textarea data-field="risk" placeholder="请输入存在风险">${escapeHtml(item.risk || "")}</textarea>
            </label>
          </div>
        </div>
        <div class="row-action"><button type="button" class="danger mini-btn remove-row">删除</button></div>
      `;
      return row;
    }

    function escapeHtml(value) {
      return String(value)
        .split("&").join("&amp;")
        .split("<").join("&lt;")
        .split(">").join("&gt;")
        .split('"').join("&quot;");
    }

    function renderItems(items) {
      listEditor.innerHTML = "";
      const header = document.createElement("div");
      header.className = "table-editor";
      header.innerHTML = `
        <div class="table-header">
          <div>基础信息</div>
          <div>服务内容</div>
          <div>工作内容</div>
          <div>遗留&amp;风险</div>
          <div>操作</div>
        </div>
      `;

      const body = document.createElement("div");
      body.className = "table-body";
      const source = items && items.length ? items : [makeBlankItem()];
      source.forEach((item, index) => {
        body.appendChild(rowTemplate(item, index));
      });
      header.appendChild(body);
      listEditor.appendChild(header);
      attachRemoveHandlers();
      attachCustomerNameInputs();
    }

    function attachRemoveHandlers() {
      listEditor.querySelectorAll(".remove-row").forEach((button) => {
        button.onclick = () => {
          const rows = [...listEditor.querySelectorAll(".item-row")];
          if (rows.length === 1) {
            renderItems([makeBlankItem()]);
            persistCurrentEntryDraft();
            setStatus("至少保留一行，已重置为空白事项。", "warning");
            return;
          }
          button.closest(".item-row").remove();
          persistCurrentEntryDraft();
        };
      });
    }

    function normalizeCustomerNameValue(value) {
      return String(value || "").trim().toLowerCase().replace(/\s+/g, "");
    }

    function dedupeCustomerNames(names) {
      const seen = new Set();
      const result = [];
      names.forEach((name) => {
        const trimmed = String(name || "").trim();
        const normalized = normalizeCustomerNameValue(trimmed);
        if (!normalized || seen.has(normalized)) {
          return;
        }
        seen.add(normalized);
        result.push(trimmed);
      });
      return result;
    }

    function normalizeProfileCombination(profile) {
      const projectType = String(profile && profile.project_type || "").trim();
      const sales = String(profile && profile.sales || "").trim();
      const itemType = String(profile && profile.item_type || "").trim();
      if (!projectType && !sales && !itemType) {
        return "";
      }
      return `${projectType}__${sales}__${itemType}`;
    }

    function updateCustomerNameOptions() {
      customerNameOptions.innerHTML = knownCustomerNames
        .map((name) => `<option value="${escapeHtml(name)}"></option>`)
        .join("");
    }

    function setKnownCustomerDirectory(names, profiles = {}) {
      knownCustomerNames = dedupeCustomerNames(names);
      const nextProfiles = {};
      Object.entries(profiles || {}).forEach(([key, profileList]) => {
        const normalizedKey = normalizeCustomerNameValue(key);
        if (!normalizedKey) {
          return;
        }
        const dedupedProfiles = [];
        const seenProfileKeys = new Set();
        (Array.isArray(profileList) ? profileList : []).forEach((profile) => {
          const normalizedProfileKey = normalizeProfileCombination(profile);
          if (!normalizedProfileKey || seenProfileKeys.has(normalizedProfileKey)) {
            return;
          }
          seenProfileKeys.add(normalizedProfileKey);
          dedupedProfiles.push({
            customer_name: String(profile.customer_name || "").trim(),
            project_type: String(profile.project_type || "").trim(),
            sales: String(profile.sales || "").trim(),
            item_type: String(profile.item_type || "").trim(),
          });
        });
        nextProfiles[normalizedKey] = dedupedProfiles;
      });
      knownCustomerProfiles = nextProfiles;
      updateCustomerNameOptions();
    }

    function mergeKnownCustomerDirectory(names, profiles = {}) {
      const mergedProfiles = { ...knownCustomerProfiles };
      Object.entries(profiles || {}).forEach(([key, profileList]) => {
        const normalizedKey = normalizeCustomerNameValue(key);
        if (!normalizedKey) {
          return;
        }
        const currentProfiles = mergedProfiles[normalizedKey] || [];
        const seenProfileKeys = new Set(currentProfiles.map((profile) => normalizeProfileCombination(profile)));
        (Array.isArray(profileList) ? profileList : []).forEach((profile) => {
          const normalizedProfileKey = normalizeProfileCombination(profile);
          if (!normalizedProfileKey || seenProfileKeys.has(normalizedProfileKey)) {
            return;
          }
          seenProfileKeys.add(normalizedProfileKey);
          currentProfiles.push({
            customer_name: String(profile.customer_name || "").trim(),
            project_type: String(profile.project_type || "").trim(),
            sales: String(profile.sales || "").trim(),
            item_type: String(profile.item_type || "").trim(),
          });
        });
        mergedProfiles[normalizedKey] = currentProfiles;
      });
      setKnownCustomerDirectory([...knownCustomerNames, ...names], mergedProfiles);
    }

    function extractCustomerNamesFromItems(items) {
      return (Array.isArray(items) ? items : [])
        .map((item) => item && item.customer_name)
        .filter(Boolean);
    }

    function extractCustomerProfilesFromItems(items) {
      const profiles = {};
      (Array.isArray(items) ? items : []).forEach((item) => {
        const customerName = String(item && item.customer_name || "").trim();
        const normalizedName = normalizeCustomerNameValue(customerName);
        const projectType = String(item && item.project_type || "").trim();
        const sales = String(item && item.sales || "").trim();
        const itemType = String(item && item.item_type || "").trim();
        if (!normalizedName) {
          return;
        }
        if (!projectType && !sales && !itemType) {
          return;
        }
        profiles[normalizedName] = profiles[normalizedName] || [];
        profiles[normalizedName].push({
          customer_name: customerName,
          project_type: projectType,
          sales,
          item_type: itemType,
        });
      });
      return profiles;
    }

    function getCustomerProfilesByName(name) {
      return knownCustomerProfiles[normalizeCustomerNameValue(name)] || [];
    }

    function levenshteinDistance(source, target) {
      const rows = source.length + 1;
      const cols = target.length + 1;
      const matrix = Array.from({ length: rows }, () => Array(cols).fill(0));

      for (let row = 0; row < rows; row += 1) {
        matrix[row][0] = row;
      }
      for (let col = 0; col < cols; col += 1) {
        matrix[0][col] = col;
      }

      for (let row = 1; row < rows; row += 1) {
        for (let col = 1; col < cols; col += 1) {
          const cost = source[row - 1] === target[col - 1] ? 0 : 1;
          matrix[row][col] = Math.min(
            matrix[row - 1][col] + 1,
            matrix[row][col - 1] + 1,
            matrix[row - 1][col - 1] + cost
          );
        }
      }
      return matrix[source.length][target.length];
    }

    function findBestCustomerNameMatch(value) {
      const query = normalizeCustomerNameValue(value);
      if (!query || !knownCustomerNames.length) {
        return "";
      }

      let bestName = "";
      let bestScore = -Infinity;
      knownCustomerNames.forEach((candidate) => {
        const normalizedCandidate = normalizeCustomerNameValue(candidate);
        if (!normalizedCandidate) {
          return;
        }

        let score = 0;
        if (normalizedCandidate === query) {
          score = 1000;
        } else {
          const maxLength = Math.max(query.length, normalizedCandidate.length);
          const distance = levenshteinDistance(query, normalizedCandidate);
          score = maxLength ? (maxLength - distance) * 12 : 0;
          if (normalizedCandidate.startsWith(query) || query.startsWith(normalizedCandidate)) {
            score += 60;
          } else if (normalizedCandidate.includes(query) || query.includes(normalizedCandidate)) {
            score += 35;
          }
          const uniqueCommonChars = [...new Set(query)].filter((char) => normalizedCandidate.includes(char)).length;
          score += uniqueCommonChars * 4;
          score -= Math.abs(normalizedCandidate.length - query.length) * 2;
        }

        if (score > bestScore) {
          bestScore = score;
          bestName = candidate;
        }
      });

      return bestScore >= 12 ? bestName : "";
    }

    function handleCustomerNameKeydown(event) {
      if (event.key !== "Enter") {
        return;
      }

      const input = event.currentTarget;
      const currentValue = input.value.trim();
      if (!currentValue) {
        return;
      }

      const matchedName = findBestCustomerNameMatch(currentValue);
      if (!matchedName) {
        return;
      }

      event.preventDefault();
      if (normalizeCustomerNameValue(matchedName) !== normalizeCustomerNameValue(currentValue)) {
        input.value = matchedName;
        mergeKnownCustomerDirectory([matchedName]);
        syncCustomerRelatedFields(input, { showStatus: true });
        setStatus(`已匹配历史客户名称：${matchedName}`, "success");
        return;
      }
      syncCustomerRelatedFields(input, { showStatus: true });
    }

    function fillCustomerProfileFields(row, profile) {
      const projectTypeSelect = row.querySelector('select[data-field="project_type"]');
      const salesSelect = row.querySelector('select[data-field="sales"]');
      const itemTypeSelect = row.querySelector('select[data-field="item_type"]');
      if (projectTypeSelect && profile.project_type) {
        projectTypeSelect.value = profile.project_type;
      }
      if (salesSelect && profile.sales) {
        salesSelect.value = profile.sales;
      }
      if (itemTypeSelect && profile.item_type) {
        itemTypeSelect.value = profile.item_type;
      }
    }

    function syncCustomerRelatedFields(input, options = {}) {
      const row = input.closest(".item-row");
      if (!row) {
        return;
      }

      const customerName = input.value.trim();
      if (!customerName) {
        return;
      }

      const profiles = getCustomerProfilesByName(customerName);
      if (!profiles.length) {
        return;
      }

      fillCustomerProfileFields(row, profiles[0]);
      if (options.showStatus) {
        setStatus(`已自动带出 ${customerName} 最近一次的项目类型、销售和类型。`, "success");
      }
    }

    function attachCustomerNameInputs() {
      listEditor.querySelectorAll(".item-row").forEach((row) => {
        const input = row.querySelector('input[data-field="customer_name"]');
        if (!input) {
          return;
        }
        input.onkeydown = handleCustomerNameKeydown;
        input.onchange = () => {
          mergeKnownCustomerDirectory([input.value]);
          syncCustomerRelatedFields(input, { showStatus: false });
        };
        input.onblur = () => syncCustomerRelatedFields(input, { showStatus: false });
        syncCustomerRelatedFields(input, { showStatus: false });
      });
    }

    function collectItems() {
      return [...listEditor.querySelectorAll(".item-row")].map((card) => {
        const item = {};
        card.querySelectorAll("[data-field]").forEach((input) => {
          item[input.dataset.field] = input.value.trim();
        });
        return item;
      });
    }

    function validateItems(items) {
      for (const item of items) {
        const value = item.work_hours;
        if (!value) {
          continue;
        }
        const hours = Number(value);
        const halfStep = Math.round(hours * 2);
        if (!Number.isFinite(hours) || hours < 0 || Math.abs(hours * 2 - halfStep) > 1e-9) {
          throw new Error("工时仅支持输入大于等于 0 的整数或 0.5。");
        }
      }
    }

    function summarizeEntry(entry) {
      if (!entry.items.length) {
        return "暂无事项";
      }
      const names = entry.items.slice(0, 2).map((item) => item.customer_name || "未填客户").join("、");
      const more = entry.items.length > 2 ? ` 等 ${entry.items.length} 项` : "";
      return `${names}${more}`;
    }

    function createEntryCard(entry, tipText) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "entry-card";

      const head = document.createElement("div");
      head.className = "entry-head";

      const dateEl = document.createElement("div");
      dateEl.className = "entry-date";
      dateEl.textContent = entry.work_date;

      const badges = document.createElement("div");
      badges.className = "entry-badges";
      badges.innerHTML = `
        <span class="badge">${entry.item_count} 条事项</span>
        <span class="badge">${entry.total_hours} 小时</span>
      `;

      head.appendChild(dateEl);
      head.appendChild(badges);

      const snippet = document.createElement("div");
      snippet.className = "entry-snippet";
      snippet.textContent = summarizeEntry(entry);

      const meta = document.createElement("div");
      meta.className = "entry-meta";
      const updatedEl = document.createElement("span");
      updatedEl.textContent = `更新于 ${entry.updated_at}`;
      const tipEl = document.createElement("span");
      tipEl.textContent = tipText;
      meta.appendChild(updatedEl);
      meta.appendChild(tipEl);

      button.appendChild(head);
      button.appendChild(snippet);
      button.appendChild(meta);

      button.addEventListener("click", () => {
        persistCurrentEntryDraft();
        fillEditor(entry);
        refreshRecentEntries(entry.work_date);
        setStatus("已载入所选日期的列表记录。", "success");
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      return button;
    }

    function formatHoursValue(value) {
      const number = Number(value || 0);
      if (!Number.isFinite(number)) {
        return "0";
      }
      const rounded = Math.round(number * 100) / 100;
      return Number.isInteger(rounded) ? String(rounded) : String(rounded).replace(/\.?0+$/, "");
    }

    function shortenSummaryText(value, maxLength = 24) {
      const normalized = String(value || "").trim().replace(/\s+/g, " ");
      if (!normalized) {
        return "";
      }
      if (normalized.length <= maxLength) {
        return normalized;
      }
      return `${normalized.slice(0, Math.max(0, maxLength - 3)).trim()}...`;
    }

    function buildMonthWeeklySummaries(entries, month) {
      if (!/^\d{4}-\d{2}$/.test(String(month || ""))) {
        return [];
      }
      const [yearValue, monthValue] = month.split("-").map(Number);
      const monthStart = `${month}-01`;
      const monthEnd = formatDate(new Date(yearValue, monthValue, 0));
      const groups = new Map();

      (Array.isArray(entries) ? entries : []).forEach((entry) => {
        const workDate = String(entry && entry.work_date || "").trim();
        if (!isValidDateString(workDate)) {
          return;
        }
        const weekStart = getWeekStartString(workDate);
        if (!weekStart) {
          return;
        }
        let group = groups.get(weekStart);
        if (!group) {
          const weekEndDate = parseDateString(weekStart);
          weekEndDate.setDate(weekEndDate.getDate() + 6);
          group = {
            week_start: weekStart,
            week_end: formatDate(weekEndDate),
            display_start: "",
            display_end: "",
            week_index: 0,
            total_days: 0,
            item_count: 0,
            total_hours_number: 0,
            total_hours: "0",
            pending_count: 0,
            risk_count: 0,
            updated_at: "",
            latest_work_date: "",
            customer_names: [],
            work_contents: [],
            customer_name_seen: new Set(),
            work_content_seen: new Set(),
          };
          groups.set(weekStart, group);
        }

        const items = normalizeEntryItems(entry && entry.items || []);
        group.total_days += 1;
        group.item_count += Number(entry && entry.item_count || items.length || 0);
        group.total_hours_number += Number(entry && entry.total_hours || 0);
        if (!group.updated_at || String(entry && entry.updated_at || "") > group.updated_at) {
          group.updated_at = String(entry && entry.updated_at || "");
        }
        if (!group.latest_work_date || workDate > group.latest_work_date) {
          group.latest_work_date = workDate;
        }

        items.forEach((item) => {
          const customerName = String(item.customer_name || "").trim();
          if (customerName && !group.customer_name_seen.has(customerName)) {
            group.customer_name_seen.add(customerName);
            group.customer_names.push(customerName);
          }
          const workContent = String(item.work_content || "").trim();
          if (workContent && !group.work_content_seen.has(workContent)) {
            group.work_content_seen.add(workContent);
            group.work_contents.push(workContent);
          }
          if (String(item.pending_issues || "").trim()) {
            group.pending_count += 1;
          }
          if (String(item.risk || "").trim()) {
            group.risk_count += 1;
          }
        });
      });

      const summaries = Array.from(groups.values()).sort((left, right) => left.week_start.localeCompare(right.week_start));
      summaries.forEach((summary, index) => {
        summary.week_index = index + 1;
        summary.display_start = summary.week_start < monthStart ? monthStart : summary.week_start;
        summary.display_end = summary.week_end > monthEnd ? monthEnd : summary.week_end;
        summary.total_hours = formatHoursValue(summary.total_hours_number);
      });
      return summaries.reverse();
    }

    function summarizeMonthWeek(summary) {
      const customerText = summary.customer_names.length
        ? `${summary.customer_names.slice(0, 3).join("、")}${summary.customer_names.length > 3 ? ` 等 ${summary.customer_names.length} 个客户` : ""}`
        : "暂无客户汇总";
      const contentText = summary.work_contents.length
        ? summary.work_contents
          .slice(0, 3)
          .map((content, index) => `${index + 1}. ${shortenSummaryText(content, 22)}`)
          .join("；")
        : "暂无事项摘要";
      return `客户：${customerText}\n事项：${contentText}`;
    }

    function createMonthWeekCard(summary) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "entry-card";

      const head = document.createElement("div");
      head.className = "entry-head";

      const dateEl = document.createElement("div");
      dateEl.className = "entry-date";
      dateEl.textContent = `第 ${summary.week_index} 周 · ${summary.display_start.slice(5)} 至 ${summary.display_end.slice(5)}`;

      const badges = document.createElement("div");
      badges.className = "entry-badges";
      badges.innerHTML = `
        <span class="badge">${summary.total_days} 天记录</span>
        <span class="badge">${summary.item_count} 条事项</span>
        <span class="badge">${summary.total_hours} 小时</span>
      `;

      head.appendChild(dateEl);
      head.appendChild(badges);

      const snippet = document.createElement("div");
      snippet.className = "entry-snippet";
      snippet.textContent = summarizeMonthWeek(summary);

      const meta = document.createElement("div");
      meta.className = "entry-meta";
      const updatedEl = document.createElement("span");
      updatedEl.textContent = summary.updated_at ? `最近更新 ${summary.updated_at}` : "最近更新未知";
      const tipEl = document.createElement("span");
      tipEl.textContent = `遗留 ${summary.pending_count} 条 · 风险 ${summary.risk_count} 条`;
      meta.appendChild(updatedEl);
      meta.appendChild(tipEl);

      button.appendChild(head);
      button.appendChild(snippet);
      button.appendChild(meta);

      button.addEventListener("click", () => {
        if (!isValidDateString(summary.latest_work_date)) {
          return;
        }
        persistCurrentEntryDraft();
        dateInput.value = summary.latest_work_date;
        rememberWorkDate(summary.latest_work_date);
        syncMonthFromDate();
        renderWeekButtons(summary.latest_work_date);
        loadDateEntry(summary.latest_work_date);
        refreshRecentEntries(summary.latest_work_date);
        warmDeliveryProgressCache(summary.latest_work_date);
        setStatus(`已切换到 ${summary.latest_work_date}，可继续查看本周详细记录。`, "success");
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      return button;
    }

    function fillEditor(entry) {
      applyEntryData(entry.work_date, entry.items || [], { skipWeeklyPlan: false });
    }

    function clearEditor(keepDate = true, options = {}) {
      const currentDate = currentEditorWorkDate || dateInput.value;
      renderItems([makeBlankItem()]);
      if (keepDate) {
        dateInput.value = currentDate;
        currentEditorWorkDate = currentDate;
      } else {
        currentEditorWorkDate = "";
      }
      if (options.clearDraft) {
        clearDailyEntryDraft(currentDate);
      }
    }

    async function loadDateEntry(targetDate, showMessage = true) {
      if (!targetDate) {
        return;
      }
      rememberWorkDate(targetDate);
      const draft = loadDailyEntryDraft(targetDate);
      const requestMeta = registerScopedAsyncRequest("entry-load", targetDate);
      try {
        const response = await fetch(`/api/entry?date=${encodeURIComponent(targetDate)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "读取当天记录失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        if (payload.entry) {
          rememberSavedEntry(payload.entry);
          const serverSnapshot = buildEntrySnapshot(payload.entry.work_date, payload.entry.items || []);
          if (draft && buildEntrySnapshot(draft.work_date, draft.items || []) !== serverSnapshot) {
            applyDailyEntryDraft(draft);
            if (showMessage) {
              setStatus("已恢复当天未保存的本地暂存内容。", "success");
            }
            return;
          }
          clearDailyEntryDraft(payload.entry.work_date);
          fillEditor(payload.entry);
          if (showMessage) {
            setStatus("已读取当天已保存的列表。", "success");
          }
        } else if (draft) {
          applyDailyEntryDraft(draft);
          if (showMessage) {
            setStatus("已恢复当天未保存的本地暂存内容。", "success");
          }
        } else {
          clearEditor(true);
          dateInput.value = targetDate;
          currentEditorWorkDate = targetDate;
          if (showMessage) {
            setStatus("这一天还没有保存记录。", "warning");
          }
        }
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        if (draft) {
          applyDailyEntryDraft(draft);
          setStatus("读取接口失败，已恢复当天未保存的本地暂存内容。", "warning");
          return;
        }
        setStatus("读取当天记录失败。", "error");
      }
    }

    async function refreshRecentEntries(anchorDate = dateInput.value) {
      const effectiveDate = isValidDateString(anchorDate) ? anchorDate : dateInput.value;
      const requestMeta = registerScopedAsyncRequest(
        "recent-entries",
        getWeekStartString(effectiveDate) || String(effectiveDate || "")
      );
      try {
        const response = await fetch(`/api/entries?date=${encodeURIComponent(effectiveDate)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "最近记录读取失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        const entries = Array.isArray(payload.entries) ? payload.entries : [];
        recentList.innerHTML = "";
        if (!entries.length) {
          recentList.innerHTML = '<div class="empty">本周还没有任何记录，先保存一份当天列表吧。</div>';
          return;
        }
        entries.forEach((entry) => {
          recentList.appendChild(createEntryCard(entry, "点击回填"));
        });
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        recentList.innerHTML = '<div class="empty">本周记录加载失败。</div>';
      }
    }

    async function loadCustomerNames() {
      const requestMeta = registerScopedAsyncRequest("customer-directory");
      try {
        const response = await fetch("/api/customer-names");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "客户名称读取失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        setKnownCustomerDirectory(payload.customer_names || [], payload.customer_profiles || {});
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        setKnownCustomerDirectory(knownCustomerNames, knownCustomerProfiles);
      }
    }

    async function refreshMonthEntries(showMessage = false) {
      const month = monthInput.value;
      if (!month) {
        monthList.innerHTML = '<div class="empty">请先选择月份。</div>';
        return;
      }

      const requestMeta = registerScopedAsyncRequest("month-entries", month);
      try {
        const response = await fetch(`/api/month?month=${encodeURIComponent(month)}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "月份数据读取失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        const stats = payload.stats || {};
        document.getElementById("stat-days").textContent = stats.total_days;
        document.getElementById("stat-items").textContent = stats.total_items;
        document.getElementById("stat-hours").textContent = stats.total_hours;

        monthList.innerHTML = "";
        const entries = Array.isArray(payload.entries) ? payload.entries : [];
        const weeklySummaries = buildMonthWeeklySummaries(entries, month);
        if (!weeklySummaries.length) {
          monthList.innerHTML = '<div class="empty">这个月份还没有保存任何记录。</div>';
        } else {
          weeklySummaries.forEach((summary) => {
            monthList.appendChild(createMonthWeekCard(summary));
          });
        }

        if (showMessage) {
          setStatus(`已刷新 ${month} 的月度数据。`, "success");
        }
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        monthList.innerHTML = '<div class="empty">月份数据加载失败。</div>';
        setStatus("月份数据读取失败。", "error");
      }
    }

    async function saveEntry() {
      const items = collectItems();
      try {
        validateItems(items);
      } catch (error) {
        setStatus(error.message || "工时格式不正确。", "error");
        return;
      }
      const payload = {
        work_date: dateInput.value,
        items
      };
      const requestMeta = registerScopedAsyncRequest("entry-save", payload.work_date);
      setStatus("正在保存...");
      try {
        const response = await fetch("/api/entry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        clearDailyEntryDraft(data.entry.work_date);
        rememberSavedEntry(data.entry);
        fillEditor(data.entry);
        mergeKnownCustomerDirectory(
          extractCustomerNamesFromItems(data.entry.items || []),
          extractCustomerProfilesFromItems(data.entry.items || [])
        );
        setStatus("已保存到本地数据库。", "success");
        refreshRecentEntries();
        refreshMonthEntries();
        loadCustomerNames();
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        setStatus(error.message || "保存失败。", "error");
      }
    }

    async function deleteEntry() {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择日期。", "warning");
        return;
      }
      if (!window.confirm(`确认删除 ${targetDate} 的整天记录吗？`)) {
        return;
      }
      const requestMeta = registerScopedAsyncRequest("entry-delete", targetDate);
      try {
        const response = await fetch(`/api/entry?date=${encodeURIComponent(targetDate)}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "删除失败");
        }
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        clearDailyEntryDraft(targetDate);
        savedEntrySnapshots.delete(targetDate);
        clearEditor(true, { clearDraft: true });
        dateInput.value = targetDate;
        setStatus("当天记录已删除。", "success");
        refreshRecentEntries();
        refreshMonthEntries();
        loadCustomerNames();
      } catch (error) {
        if (!isScopedAsyncRequestActive(requestMeta)) {
          return;
        }
        setStatus(error.message || "删除失败。", "error");
      }
    }

    addRowButton.addEventListener("click", () => {
      const table = listEditor.querySelector(".table-editor");
      if (!table) {
        renderItems([makeBlankItem()]);
        persistCurrentEntryDraft();
        return;
      }
      const body = table.querySelector(".table-body") || table;
      body.appendChild(rowTemplate(makeBlankItem(), listEditor.querySelectorAll(".item-row").length));
      attachRemoveHandlers();
      attachCustomerNameInputs();
      persistCurrentEntryDraft();
    });
    reloadButton.addEventListener("click", () => loadDateEntry(dateInput.value));
    clearButton.addEventListener("click", () => {
      clearEditor(true, { clearDraft: true });
      setStatus("表单已清空。", "warning");
    });
    deleteButton.addEventListener("click", deleteEntry);
    saveButton.addEventListener("click", saveEntry);
    exportDailyLogButton.addEventListener("click", openDailyLogPreview);
    exportWeeklyReportButton.addEventListener("click", openWeeklyReportPreview);
    exportWeeklyStrengthButton.addEventListener("click", openWeeklyStrengthPreview);
    showDeliveryProgressButton.addEventListener("click", () => openDeliveryProgress(false));
    deliveryProgressRegenerateButton.addEventListener("click", () => openDeliveryProgress(true));
    authLoginButton.addEventListener("click", openAuthOverlay);
    authLogoutButton.addEventListener("click", logoutCurrentUser);
    authPasswordButton.addEventListener("click", openPasswordOverlay);
    authDepartmentScheduleButton.addEventListener("click", () => {
      window.location.href = "/department-schedule";
    });
    authAdminPageButton.addEventListener("click", () => {
      window.location.href = "/admin";
    });
    authOverlayCloseButton.addEventListener("click", closeAuthOverlay);
    authOverlay.addEventListener("click", (event) => {
      if (event.target === authOverlay) {
        closeAuthOverlay();
      }
    });
    passwordOverlayCloseButton.addEventListener("click", closePasswordOverlay);
    passwordOverlay.addEventListener("click", (event) => {
      if (event.target === passwordOverlay) {
        closePasswordOverlay();
      }
    });
    promptEditorButton.addEventListener("click", openPromptOverlay);
    userDingtalkMcpButton.addEventListener("click", openUserDingtalkMcpOverlay);
    promptOverlayCloseButton.addEventListener("click", closePromptOverlay);
    promptOverlay.addEventListener("click", (event) => {
      if (event.target === promptOverlay) {
        closePromptOverlay();
      }
    });
    userDingtalkMcpOverlayCloseButton.addEventListener("click", closeUserDingtalkMcpOverlay);
    userDingtalkMcpOverlay.addEventListener("click", (event) => {
      if (event.target === userDingtalkMcpOverlay) {
        closeUserDingtalkMcpOverlay();
      }
    });
    authLocalSubmitButton.addEventListener("click", submitLocalPasswordLogin);
    authLocalUsernameInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (String(authLocalPasswordInput.value || "")) {
          submitLocalPasswordLogin();
        } else {
          authLocalPasswordInput.focus();
        }
      }
    });
    authLocalPasswordInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        submitLocalPasswordLogin();
      }
    });
    passwordSubmitButton.addEventListener("click", submitPasswordUpdate);
    [passwordCurrentInput, passwordNewInput, passwordConfirmInput].forEach((input) => {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          submitPasswordUpdate();
        }
      });
    });
    promptTemplateSelect.addEventListener("change", (event) => {
      promptEditorState.selectedPromptId = String(event.target.value || "").trim();
      renderPromptEditor();
    });
    promptTemplateContent.addEventListener("input", () => {
      const currentPrompt = getPromptEditorSelectedTemplate();
      if (!currentPrompt) {
        return;
      }
      currentPrompt.content = promptTemplateContent.value;
      renderPromptEditor();
    });
    promptTemplateContent.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        savePromptEditorTemplates();
      }
    });
    promptTemplateResetButton.addEventListener("click", restoreSelectedPromptTemplateDefault);
    promptTemplateSaveButton.addEventListener("click", savePromptEditorTemplates);
    userDingtalkLogMcpInput.addEventListener("input", () => {
      if (!userDingtalkMcpState.config) {
        return;
      }
      const nextValue = String(userDingtalkLogMcpInput.value || "").trim();
      const previousSavedValue = userDingtalkMcpState.savedConfig
        ? String(userDingtalkMcpState.savedConfig.log_mcp_url || "")
        : "";
      userDingtalkMcpState.config.log_mcp_url = nextValue;
      if (nextValue !== previousSavedValue) {
        userDingtalkMcpState.config.daily_template = normalizeUserDingtalkTemplateConfig({});
        userDingtalkMcpState.config.weekly_template = normalizeUserDingtalkTemplateConfig({});
        userDingtalkMcpState.availableTemplates = [];
        userDingtalkMcpState.templatesLoaded = false;
      }
      renderUserDingtalkMcpEditor();
    });
    userDingtalkDirectoryMcpInput.addEventListener("input", () => {
      if (!userDingtalkMcpState.config) {
        return;
      }
      userDingtalkMcpState.config.directory_mcp_url = String(userDingtalkDirectoryMcpInput.value || "").trim();
      renderUserDingtalkMcpEditor();
    });
    userDingtalkDailyTemplateSelect.addEventListener("change", (event) => {
      if (!userDingtalkMcpState.config) {
        return;
      }
      const selectedValue = String(event.target.value || "").trim();
      if (!selectedValue) {
        userDingtalkMcpState.config.daily_template = normalizeUserDingtalkTemplateConfig({});
      } else {
        const selectedTemplate = collectUserDingtalkTemplateOptions("daily", userDingtalkMcpState.config)
          .find((template) => buildUserDingtalkTemplateSelectionValue(template) === selectedValue);
        if (selectedTemplate) {
          userDingtalkMcpState.config.daily_template = normalizeUserDingtalkTemplateConfig(selectedTemplate);
        }
      }
      renderUserDingtalkMcpEditor();
    });
    userDingtalkWeeklyTemplateSelect.addEventListener("change", (event) => {
      if (!userDingtalkMcpState.config) {
        return;
      }
      const selectedValue = String(event.target.value || "").trim();
      if (!selectedValue) {
        userDingtalkMcpState.config.weekly_template = normalizeUserDingtalkTemplateConfig({});
      } else {
        const selectedTemplate = collectUserDingtalkTemplateOptions("weekly", userDingtalkMcpState.config)
          .find((template) => buildUserDingtalkTemplateSelectionValue(template) === selectedValue);
        if (selectedTemplate) {
          userDingtalkMcpState.config.weekly_template = normalizeUserDingtalkTemplateConfig(selectedTemplate);
        }
      }
      renderUserDingtalkMcpEditor();
    });
    [userDingtalkLogMcpInput, userDingtalkDirectoryMcpInput, userDingtalkDailyTemplateSelect, userDingtalkWeeklyTemplateSelect].forEach((input) => {
      input.addEventListener("keydown", (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
          event.preventDefault();
          saveUserDingtalkMcpEditorConfig();
        }
      });
    });
    userDingtalkMcpLoadTemplatesButton.addEventListener("click", () => {
      loadUserDingtalkReportTemplates(true);
    });
    userDingtalkMcpResetButton.addEventListener("click", restoreUserDingtalkMcpConfigDefault);
    userDingtalkMcpSaveButton.addEventListener("click", saveUserDingtalkMcpEditorConfig);
    startDingtalkScanLoginButton.addEventListener("click", startDingtalkScanLogin);
    refreshDingtalkScanLoginButton.addEventListener("click", startDingtalkScanLogin);
    deliveryProgressCloseButton.addEventListener("click", () => setDeliveryProgressOpen(false));
    deliveryProgressOverlay.addEventListener("click", (event) => {
      if (event.target === deliveryProgressOverlay) {
        setDeliveryProgressOpen(false);
      }
    });
    previewSendLogButton.addEventListener("click", sendDailyLogToDingtalk);
    previewDownloadLogButton.addEventListener("click", downloadCurrentWeeklyReport);
    sendConfirmSubmitButton.addEventListener("click", confirmDailyLogSend);
    sendConfirmCloseButton.addEventListener("click", () => setSendConfirmOpen(false));
    sendConfirmCancelButton.addEventListener("click", () => setSendConfirmOpen(false));
    sendConfirmOverlay.addEventListener("click", (event) => {
      if (event.target === sendConfirmOverlay && !isSendingDailyLog) {
        setSendConfirmOpen(false);
      }
    });
    previewCloseButton.addEventListener("click", () => setPreviewOpen(false));
    previewOverlay.addEventListener("click", (event) => {
      if (event.target === previewOverlay) {
        setPreviewOpen(false);
      }
    });
    previewContent.addEventListener("click", (event) => {
      const button = event.target.closest("[data-daily-log-action]");
      if (!button || !dailyLogEditorState) {
        return;
      }
      const action = button.dataset.dailyLogAction;
      const sectionIndex = Number(button.dataset.sectionIndex);
      const itemIndex = Number(button.dataset.itemIndex);
      if (!Number.isInteger(sectionIndex) || sectionIndex < 0 || sectionIndex >= dailyLogEditorState.sections.length) {
        return;
      }
      const section = dailyLogEditorState.sections[sectionIndex];
      if (action === "add-item") {
        section.items.push("");
        renderDailyLogEditor();
        setStatus(`已在“${section.title}”中新增一条内容。`, "success");
        return;
      }
      if (action === "remove-item") {
        if (!Number.isInteger(itemIndex) || itemIndex < 0 || itemIndex >= section.items.length) {
          return;
        }
        section.items.splice(itemIndex, 1);
        renderDailyLogEditor();
        setStatus(`已从“${section.title}”中删除一条内容。`, "warning");
      }
    });
    previewContent.addEventListener("input", (event) => {
      const input = event.target.closest('textarea[data-daily-log-action="edit-item"]');
      if (input && dailyLogEditorState) {
        const sectionIndex = Number(input.dataset.sectionIndex);
        const itemIndex = Number(input.dataset.itemIndex);
        if (!Number.isInteger(sectionIndex) || !Number.isInteger(itemIndex)) {
          return;
        }
        const section = dailyLogEditorState.sections[sectionIndex];
        if (!section || itemIndex < 0 || itemIndex >= section.items.length) {
          return;
        }
        section.items[itemIndex] = input.value;
        const output = previewContent.querySelector(".preview-card:last-child .preview-richtext");
        if (output) {
          output.innerHTML = renderDailyLogOutputHtml(dailyLogEditorState.sections);
        }
        return;
      }

      const weeklyField = event.target.closest('textarea[data-weekly-report-field="content"]');
      if (!weeklyField || !dailyLogEditorState || dailyLogEditorState.kind !== "weekly_report") {
        return;
      }
      const sectionIndex = Number(weeklyField.dataset.sectionIndex);
      if (!Number.isInteger(sectionIndex) || sectionIndex < 0 || sectionIndex >= dailyLogEditorState.sections.length) {
        return;
      }
      dailyLogEditorState.sections[sectionIndex].content = weeklyField.value;
      const output = previewContent.querySelector("#weekly-report-output");
      if (output) {
        output.innerHTML = renderWeeklyReportOutputHtml(dailyLogEditorState.sections);
      }
    });
    sendConfirmContent.addEventListener("click", (event) => {
      const button = event.target.closest("[data-send-confirm-action]");
      if (!button || !dailyLogEditorState || isSendingDailyLog) {
        return;
      }
      const action = button.dataset.sendConfirmAction;
      const recipientIndex = Number(button.dataset.recipientIndex);
      if (action === "add-recipient") {
        dailyLogEditorState.extraRecipients.push({ name: "", user_id: "" });
        renderSendConfirmDialog();
        return;
      }
      if (action === "remove-recipient") {
        if (!Number.isInteger(recipientIndex) || recipientIndex < 0 || recipientIndex >= dailyLogEditorState.extraRecipients.length) {
          return;
        }
        dailyLogEditorState.extraRecipients.splice(recipientIndex, 1);
        renderSendConfirmDialog();
      }
    });
    sendConfirmContent.addEventListener("change", (event) => {
      const toChatCheckbox = event.target.closest("#send-confirm-to-chat");
      if (toChatCheckbox && dailyLogEditorState) {
        dailyLogEditorState.toChat = Boolean(toChatCheckbox.checked);
        renderSendConfirmDialog();
        renderDailyLogPreviewMeta();
        setStatus(
          dailyLogEditorState.toChat ? "已开启发送到聊天。" : "已关闭发送到聊天。",
          "success"
        );
        return;
      }
      const nameInput = event.target.closest('[data-send-confirm-field="name"]');
      if (!nameInput || !dailyLogEditorState) {
        return;
      }
      const recipientIndex = Number(nameInput.dataset.recipientIndex);
      if (!Number.isInteger(recipientIndex) || recipientIndex < 0 || recipientIndex >= dailyLogEditorState.extraRecipients.length) {
        return;
      }
      lookupDailyLogRecipientByName(recipientIndex, nameInput.value);
    });
    sendConfirmContent.addEventListener("input", (event) => {
      const input = event.target.closest("[data-send-confirm-field]");
      if (!input || !dailyLogEditorState) {
        return;
      }
      const recipientIndex = Number(input.dataset.recipientIndex);
      if (!Number.isInteger(recipientIndex) || recipientIndex < 0 || recipientIndex >= dailyLogEditorState.extraRecipients.length) {
        return;
      }
      const field = input.dataset.sendConfirmField;
      if (!field) {
        return;
      }
      dailyLogEditorState.extraRecipients[recipientIndex][field] = input.value;
      updateSendConfirmRecipientSummary();
      renderDailyLogPreviewMeta();
    });
    clearWeeklyPlanButton.addEventListener("click", clearWeeklyPlan);
    listEditor.addEventListener("input", persistCurrentEntryDraft);
    listEditor.addEventListener("change", persistCurrentEntryDraft);
    Object.values(weeklyScheduleInputs).forEach((input) => {
      input.addEventListener("input", () => {
        saveWeeklyPlanDraft(currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value), getCurrentSettings());
        scheduleWeeklyPlanAutosave();
      });
    });
    refreshMonthButton.addEventListener("click", () => refreshMonthEntries(true));
    exportMonthButton.addEventListener("click", () => {
      const month = monthInput.value;
      if (!month) {
        setStatus("请先选择要导出的月份。", "warning");
        return;
      }
      const scopeUserId = getActiveScopeUserId();
      const userQuery = scopeUserId ? `&user_id=${encodeURIComponent(scopeUserId)}` : "";
      window.location.href = `/api/export?month=${encodeURIComponent(month)}${userQuery}`;
      setStatus(`正在导出 ${month} 的 Excel 文件。`, "success");
    });
    dateInput.addEventListener("change", () => {
      persistCurrentEntryDraft();
      rememberWorkDate(dateInput.value);
      syncMonthFromDate();
      renderWeekButtons(dateInput.value);
      loadWeeklyPlan(dateInput.value);
      loadDateEntry(dateInput.value);
      refreshRecentEntries(dateInput.value);
      refreshMonthEntries();
      warmDeliveryProgressCache(dateInput.value);
    });
    monthInput.addEventListener("change", () => refreshMonthEntries(true));
    prevWeekButton.addEventListener("click", () => shiftWeek(-7));
    nextWeekButton.addEventListener("click", () => shiftWeek(7));
    themeToggleButton.addEventListener("click", () => {
      const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
      writeStoredThemePreference(nextTheme);
      applyTheme(nextTheme);
      scheduleAutoThemeRefresh();
    });
    backgroundSettingsButton.addEventListener("click", (event) => {
      event.stopPropagation();
      setBackgroundSettingsOpen(!isBackgroundSettingsOpen);
    });
    backgroundSettingsMenu.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    selectBackgroundImageButton.addEventListener("click", () => backgroundImageInput.click());
    useBingBackgroundButton.addEventListener("click", () => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: BING_DAILY_BACKGROUND_PATH });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave(true);
    });
    backgroundImageInput.addEventListener("change", (event) => {
      const [file] = event.target.files || [];
      handleBackgroundImageSelection(file);
      backgroundImageInput.value = "";
    });
    clearBackgroundImageButton.addEventListener("click", () => {
      if (!currentUiSettings.background_image) {
        return;
      }
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: "" });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave(true);
    });
    backgroundModeSelect.addEventListener("change", (event) => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_mode: event.target.value });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave(true);
    });
    regionOpacityInput.addEventListener("input", (event) => updateOpacitySetting(event.target.value));
    document.addEventListener("click", () => {
      if (isBackgroundSettingsOpen) {
        setBackgroundSettingsOpen(false);
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isSendConfirmOpen && !isSendingDailyLog) {
        setSendConfirmOpen(false);
        return;
      }
      if (event.key === "Escape" && isPromptOverlayOpen) {
        closePromptOverlay();
        return;
      }
      if (event.key === "Escape" && isUserDingtalkMcpOverlayOpen) {
        closeUserDingtalkMcpOverlay();
        return;
      }
      if (event.key === "Escape" && isPasswordOverlayOpen) {
        closePasswordOverlay();
        return;
      }
      if (event.key === "Escape" && isPreviewOpen) {
        setPreviewOpen(false);
        return;
      }
      if (event.key === "Escape" && isDeliveryProgressOpen) {
        setDeliveryProgressOpen(false);
        return;
      }
      if (event.key === "Escape" && isBackgroundSettingsOpen) {
        setBackgroundSettingsOpen(false);
      }
    });
    window.addEventListener("scroll", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("resize", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("touchmove", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("touchend", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("storage", handleWeeklyPlanSyncSignal);
    window.addEventListener("beforeunload", () => {
      persistCurrentEntryDraft();
      saveWeeklyPlanDraft(currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value), getCurrentSettings());
    });

    initializePasswordToggleFields();

    async function bootstrapApp() {
      initTheme();
      dateInput.value = "__INITIAL_DATE__";
      currentEditorWorkDate = dateInput.value;
      syncMonthFromDate();
      applyPageSettings(initialPageSettings);
      applyVisualSettings(initialUiSettings);
      scheduleBackgroundStretch();
      renderItems([makeBlankItem()]);
      await refreshAuthState();
      await loadFieldOptionsForCurrentScope().catch(() => {});
      dateInput.value = "__INITIAL_DATE__";
      currentEditorWorkDate = dateInput.value;
      syncMonthFromDate();
      await loadVisualSettings({ silent: true });
      await loadDingtalkAuthConfig().catch(() => {});
      loadCustomerNames();
      warmDeliveryProgressCache(dateInput.value);
      renderWeekButtons(dateInput.value);
      loadWeeklyPlan(dateInput.value);
      refreshRecentEntries();
      refreshMonthEntries();
      loadDateEntry(dateInput.value, false);
    }
    bootstrapApp();
  </script>
</body>
</html>
"""




# Centralize auth/account/DingTalk state management in the dedicated service module.
get_connection = auth_service.get_connection
normalize_user_id = auth_service.normalize_user_id
ensure_user = auth_service.ensure_user
get_default_user_id = auth_service.get_default_user_id
get_user_by_id = auth_service.get_user_by_id
list_all_users = auth_service.list_all_users
normalize_user_id_list = auth_service.normalize_user_id_list
get_business_field_options = auth_service.get_business_field_options
get_position_field_scopes = auth_service.get_position_field_scopes
save_position_field_scopes = auth_service.save_position_field_scopes
get_business_field_options_for_positions = auth_service.get_business_field_options_for_positions
get_business_field_options_for_user_id = auth_service.get_business_field_options_for_user_id
get_access_control_settings = auth_service.get_access_control_settings
save_access_control_settings = auth_service.save_access_control_settings
is_user_allowed_to_login = auth_service.is_user_allowed_to_login
is_admin_user_id = auth_service.is_admin_user_id
has_admin_access = auth_service.has_admin_access
is_department_admin_user_id = auth_service.is_department_admin_user_id
normalize_local_username = auth_service.normalize_local_username
build_local_account_user_id = auth_service.build_local_account_user_id
get_local_account_by_username = auth_service.get_local_account_by_username
get_local_account_by_user_id = auth_service.get_local_account_by_user_id
list_local_accounts = auth_service.list_local_accounts
save_local_account = auth_service.save_local_account
get_local_account_position_options = auth_service.get_local_account_position_options
get_department_options = auth_service.get_department_options
save_department_options = auth_service.save_department_options
verify_local_account_password = auth_service.verify_local_account_password
update_local_account_password = auth_service.update_local_account_password
normalize_external_base_url = auth_service.normalize_external_base_url
build_request_origin_from_headers = auth_service.build_request_origin_from_headers
normalize_dingtalk_oauth_config = auth_service.normalize_dingtalk_oauth_config
build_dingtalk_oauth_public_config = auth_service.build_dingtalk_oauth_public_config
get_dingtalk_oauth_config = auth_service.get_dingtalk_oauth_config
get_dingtalk_oauth_config_with_updated_at = auth_service.get_dingtalk_oauth_config_with_updated_at
save_dingtalk_oauth_config = auth_service.save_dingtalk_oauth_config
normalize_dingtalk_login_session_id = auth_service.normalize_dingtalk_login_session_id
purge_expired_dingtalk_scan_login_sessions = auth_service.purge_expired_dingtalk_scan_login_sessions
create_dingtalk_scan_login_session = auth_service.create_dingtalk_scan_login_session
get_dingtalk_scan_login_session = auth_service.get_dingtalk_scan_login_session
update_dingtalk_scan_login_session = auth_service.update_dingtalk_scan_login_session
build_dingtalk_oauth_callback_url = auth_service.build_dingtalk_oauth_callback_url
build_dingtalk_scan_entry_url = auth_service.build_dingtalk_scan_entry_url
build_dingtalk_oauth_authorize_url = auth_service.build_dingtalk_oauth_authorize_url
extract_http_error_message = auth_service.extract_http_error_message
request_json = auth_service.request_json
exchange_dingtalk_user_access_token = auth_service.exchange_dingtalk_user_access_token
fetch_dingtalk_current_user = auth_service.fetch_dingtalk_current_user
build_dingtalk_local_user_id = auth_service.build_dingtalk_local_user_id
save_dingtalk_identity = auth_service.save_dingtalk_identity
list_dingtalk_user_identities = auth_service.list_dingtalk_user_identities
resolve_dingtalk_scan_login_user = auth_service.resolve_dingtalk_scan_login_user
build_dingtalk_callback_result_html = auth_service.build_dingtalk_callback_result_html


def build_qr_png_via_swift(content: str, size: int = 320) -> bytes:
    if not SWIFT_BIN or not Path(SWIFT_BIN).exists():
        raise RuntimeError("当前环境未安装 swift，无法生成二维码图片。")
    script = r'''
import Foundation
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write(Data("Missing arguments".utf8))
    exit(1)
}
let text = args[1]
let targetSize = CGFloat(Double(args[2]) ?? 320.0)
guard let textData = text.data(using: .utf8) else {
    FileHandle.standardError.write(Data("Invalid UTF8 content".utf8))
    exit(1)
}
guard let filter = CIFilter(name: "CIQRCodeGenerator") else {
    FileHandle.standardError.write(Data("CIQRCodeGenerator unavailable".utf8))
    exit(1)
}
filter.setValue(textData, forKey: "inputMessage")
filter.setValue("M", forKey: "inputCorrectionLevel")
guard let outputImage = filter.outputImage else {
    FileHandle.standardError.write(Data("QR generation failed".utf8))
    exit(1)
}
let extent = outputImage.extent.integral
let scale = max(1.0, floor(targetSize / max(extent.width, extent.height)))
let transformed = outputImage.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
let context = CIContext(options: nil)
guard let cgImage = context.createCGImage(transformed, from: transformed.extent) else {
    FileHandle.standardError.write(Data("Cannot create CGImage".utf8))
    exit(1)
}
let rep = NSBitmapImageRep(cgImage: cgImage)
guard let pngData = rep.representation(using: .png, properties: [:]) else {
    FileHandle.standardError.write(Data("Cannot encode PNG".utf8))
    exit(1)
}
FileHandle.standardOutput.write(pngData)
'''
    completed = subprocess.run(
        [SWIFT_BIN, "-e", script, str(content or ""), str(max(160, min(size, 720)))],
        capture_output=True,
        check=False,
        timeout=20,
        env={**os.environ, "PATH": f"/usr/bin:/bin:/usr/sbin:/sbin:{os.environ.get('PATH', '')}"},
    )
    if completed.returncode != 0 or not completed.stdout:
        error_text = (completed.stderr or completed.stdout or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(error_text or "生成二维码图片失败。")
    return completed.stdout


def build_admin_overview_payload(anchor_date: str, month: str | None = None) -> dict:
    target_date = validate_date(anchor_date)
    target_month = validate_month(month or target_date[:7])
    users = list_all_users()
    entries_by_user: list[dict] = []
    for user in users:
        user_id = user["user_id"]
        day_entry = fetch_entry(target_date, user_id=user_id)
        week_start, weekly_plan, weekly_updated_at = get_weekly_plan_settings(target_date, user_id=user_id)
        month_entries = fetch_month_entries(target_month, user_id=user_id)
        month_stats = build_month_stats(month_entries)
        entries_by_user.append(
            {
                "user": user,
                "day_entry": day_entry,
                "month_stats": month_stats,
                "week_start": week_start,
                "weekly_plan_updated_at": weekly_updated_at,
                "weekly_plan": weekly_plan,
            }
        )
    return {
        "anchor_date": target_date,
        "month": target_month,
        "users": entries_by_user,
    }


DEPARTMENT_SCHEDULE_WEEKDAY_LABELS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
DEPARTMENT_SCHEDULE_PLAN_FIELD_MAP = (
    ("周一", "weekly_monday_am", "weekly_monday_pm"),
    ("周二", "weekly_tuesday_am", "weekly_tuesday_pm"),
    ("周三", "weekly_wednesday_am", "weekly_wednesday_pm"),
    ("周四", "weekly_thursday_am", "weekly_thursday_pm"),
    ("周五", "weekly_friday_am", "weekly_friday_pm"),
    ("周六", "weekly_saturday_am", "weekly_saturday_pm"),
    ("周日", "weekly_sunday_am", "weekly_sunday_pm"),
)


def _normalize_department_label(value: object) -> str:
    return str(value or "").strip()


def _department_label_key(value: object) -> str:
    return _normalize_department_label(value).casefold()


def _dedupe_department_labels(values: list[object]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        label = _normalize_department_label(raw_value)
        if not label:
            continue
        label_key = label.casefold()
        if label_key in seen:
            continue
        seen.add(label_key)
        labels.append(label)
    return labels


def _can_access_department_schedule(user: dict | None) -> bool:
    return isinstance(user, dict)


def _can_edit_department_schedule_weekly_plan(user: dict | None) -> bool:
    if not isinstance(user, dict):
        return False
    if str(user.get("role") or "") == "admin":
        return True
    if bool(user.get("is_department_admin")):
        return True
    return bool(_normalize_department_label(user.get("department")))


def _can_view_department_schedule_daily_details(user: dict | None) -> bool:
    if not isinstance(user, dict):
        return False
    if str(user.get("role") or "") == "admin":
        return True
    return bool(user.get("is_department_admin"))


def _match_department_label(label: str, expected: str) -> bool:
    return _department_label_key(label) == _department_label_key(expected)


def _split_schedule_filter_values(raw_values: object) -> list[str]:
    if isinstance(raw_values, str):
        values = [raw_values]
    elif isinstance(raw_values, (list, tuple, set)):
        values = list(raw_values)
    else:
        values = []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        for part in re.split(r"[\n,，]+", str(raw_value or "")):
            label = str(part or "").strip()
            if not label:
                continue
            key = label.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(label)
    return normalized


def _collect_user_position_labels(user: dict | None) -> list[str]:
    if not isinstance(user, dict):
        return []
    values: list[str] = []
    seen: set[str] = set()
    raw_positions = user.get("positions")
    if isinstance(raw_positions, (list, tuple, set)):
        for raw_position in raw_positions:
            label = str(raw_position or "").strip()
            if not label:
                continue
            key = label.casefold()
            if key in seen:
                continue
            seen.add(key)
            values.append(label)
    fallback_position = str(user.get("position") or "").strip()
    if fallback_position and fallback_position.casefold() not in seen:
        values.append(fallback_position)
    return values


def _collect_available_position_labels(users: list[dict]) -> list[str]:
    configured_options = list(get_local_account_position_options().get("options") or [])
    configured_keys = {item.casefold() for item in configured_options if str(item or "").strip()}
    discovered: dict[str, str] = {}
    for user in users:
        for label in _collect_user_position_labels(user):
            discovered.setdefault(label.casefold(), label)
    ordered = [item for item in configured_options if item.casefold() in discovered]
    extras = sorted(
        (label for key, label in discovered.items() if key not in configured_keys),
        key=lambda item: item.casefold(),
    )
    return ordered + extras


def _match_position_label(label: str, expected: str) -> bool:
    return str(label or "").strip().casefold() == str(expected or "").strip().casefold()


def _build_schedule_filter_label(
    selected_values: list[str],
    available_values: list[str],
    *,
    all_label: str,
    unit_label: str,
) -> str:
    available_count = len(available_values)
    selected_count = len(selected_values)
    if not available_count:
        return all_label
    if selected_count == 1:
        return selected_values[0]
    if selected_count >= available_count:
        return all_label
    return f"已筛选 {selected_count} 个{unit_label}"


def build_department_weekly_plan_rows(settings: dict | None) -> list[dict[str, str]]:
    source = normalize_weekly_plan_settings(settings if isinstance(settings, dict) else {})
    return [
        {
            "weekday_label": weekday_label,
            "am": str(source.get(am_key, "") or "").strip(),
            "pm": str(source.get(pm_key, "") or "").strip(),
        }
        for weekday_label, am_key, pm_key in DEPARTMENT_SCHEDULE_PLAN_FIELD_MAP
    ]


def build_department_weekly_plan_settings_from_rows(
    weekly_plan_rows: object,
    *,
    weekly_other_pending: object = "",
) -> dict[str, str]:
    settings = DEFAULT_PAGE_SETTINGS.copy()
    row_list = weekly_plan_rows if isinstance(weekly_plan_rows, list) else []
    for index, (_, am_key, pm_key) in enumerate(DEPARTMENT_SCHEDULE_PLAN_FIELD_MAP):
        row = row_list[index] if index < len(row_list) and isinstance(row_list[index], dict) else {}
        settings[am_key] = str(row.get("am", "") or "").strip()
        settings[pm_key] = str(row.get("pm", "") or "").strip()
    settings["weekly_other_pending"] = str(weekly_other_pending or "").strip()
    return normalize_weekly_plan_settings(settings)


def _is_department_schedule_visible_user(user: dict | None) -> bool:
    if not isinstance(user, dict):
        return False
    if bool(user.get("has_local_account")) and not bool(user.get("enabled", True)):
        return False
    return bool(user.get("show_in_department_schedule"))


def resolve_department_schedule_target_user(
    current_user: dict | None,
    target_user_id: str | None,
) -> dict[str, Any]:
    if not current_user:
        raise PermissionError("请先登录后再维护部门安排。")
    if not _can_edit_department_schedule_weekly_plan(current_user):
        raise PermissionError("当前账号没有维护部门安排的权限。")
    normalized_target_user_id = normalize_user_id(target_user_id)
    target_user = get_user_by_id(normalized_target_user_id)
    if not target_user:
        raise ValueError("目标用户不存在。")
    if not _is_department_schedule_visible_user(target_user):
        raise ValueError("目标用户当前未开启日程管理展示，无法维护其日程安排。")
    if str(current_user.get("role") or "") == "admin":
        return target_user

    viewer_department = _normalize_department_label(current_user.get("department"))
    target_department = _normalize_department_label(target_user.get("department"))
    if not viewer_department:
        raise PermissionError("当前账号尚未配置所属部门，暂无法维护本部门安排。")
    if not target_department or not _match_department_label(target_department, viewer_department):
        raise PermissionError("当前账号只能维护自己所属部门的用户安排。")
    return target_user


def resolve_department_schedule_scope(
    current_user: dict | None,
    requested_department: str | None = None,
    requested_departments: object | None = None,
    requested_positions: object | None = None,
) -> dict[str, Any]:
    if not current_user:
        raise PermissionError("请先登录后再访问部门日程页面。")
    if not _can_access_department_schedule(current_user):
        raise PermissionError("当前账号没有访问部门日程页面的权限。")

    viewer_is_admin = str(current_user.get("role") or "") == "admin"
    viewer_can_view_daily_details = _can_view_department_schedule_daily_details(current_user)
    viewer_department = _normalize_department_label(current_user.get("department"))

    all_visible_users = [user for user in list_all_users() if _is_department_schedule_visible_user(user)]
    if viewer_is_admin:
        accessible_users = list(all_visible_users)
        available_departments = _dedupe_department_labels([item.get("department") for item in accessible_users])
    else:
        if not viewer_department:
            raise PermissionError("当前账号尚未配置所属部门，暂无法查看部门日程。")
        accessible_users = [
            user
            for user in all_visible_users
            if _match_department_label(_normalize_department_label(user.get("department")), viewer_department)
        ]
        available_departments = [viewer_department]
    available_positions = _collect_available_position_labels(accessible_users)

    default_selected_departments: list[str] = []
    if viewer_department:
        matched_default_department = next(
            (label for label in available_departments if _match_department_label(label, viewer_department)),
            "",
        )
        if matched_default_department:
            default_selected_departments = [matched_default_department]
    if not default_selected_departments:
        default_selected_departments = list(available_departments)
    default_selected_positions = list(available_positions)

    requested_label = _normalize_department_label(requested_department)
    requested_department_labels = _split_schedule_filter_values(requested_departments)
    requested_all_departments = any(
        str(item or "").strip() == "__all__" for item in requested_department_labels
    )
    if requested_label == "__all__" and not requested_department_labels:
        requested_all_departments = True
    if requested_label and requested_label != "__all__":
        requested_department_labels.append(requested_label)
        requested_department_labels = _dedupe_department_labels(requested_department_labels)

    selected_departments: list[str] = []
    if requested_department_labels and not requested_all_departments:
        for raw_label in requested_department_labels:
            normalized_label = _normalize_department_label(raw_label)
            matched_label = next(
                (label for label in available_departments if _match_department_label(label, normalized_label)),
                "",
            )
            if not matched_label:
                if not viewer_is_admin and viewer_department:
                    raise PermissionError("当前账号只能查看自己所属部门的日程。")
                raise ValueError("所选部门不存在，请刷新后重试。")
            if matched_label not in selected_departments:
                selected_departments.append(matched_label)
    else:
        selected_departments = list(default_selected_departments)

    requested_position_labels = _split_schedule_filter_values(requested_positions)
    requested_all_positions = any(str(item or "").strip() == "__all__" for item in requested_position_labels)
    selected_positions: list[str] = []
    if requested_position_labels and not requested_all_positions:
        for raw_label in requested_position_labels:
            normalized_label = str(raw_label or "").strip()
            matched_label = next(
                (label for label in available_positions if _match_position_label(label, normalized_label)),
                "",
            )
            if not matched_label:
                raise ValueError("所选岗位不存在，请刷新后重试。")
            if matched_label not in selected_positions:
                selected_positions.append(matched_label)
    else:
        selected_positions = list(default_selected_positions)

    department_filter_active = bool(available_departments) and 0 < len(selected_departments) < len(available_departments)
    position_filter_active = bool(available_positions) and 0 < len(selected_positions) < len(available_positions)

    department_users: list[dict] = []
    for user in accessible_users:
        user_department = _normalize_department_label(user.get("department"))
        if not user_department:
            continue
        if department_filter_active and not any(
            _match_department_label(user_department, selected_department) for selected_department in selected_departments
        ):
            continue
        if position_filter_active:
            user_positions = _collect_user_position_labels(user)
            if not any(
                any(_match_position_label(user_position, selected_position) for selected_position in selected_positions)
                for user_position in user_positions
            ):
                continue
        department_users.append(user)
    department_users.sort(
        key=lambda item: (
            _normalize_department_label(item.get("department")),
            _normalize_department_label(item.get("display_name")) or _normalize_department_label(item.get("user_id")),
        )
    )

    selected_department = selected_departments[0] if len(selected_departments) == 1 else ""
    selected_department_label = _build_schedule_filter_label(
        selected_departments,
        available_departments,
        all_label="全部部门",
        unit_label="部门",
    )
    selected_position_label = _build_schedule_filter_label(
        selected_positions,
        available_positions,
        all_label="全部岗位",
        unit_label="岗位",
    )

    return {
        "viewer_is_admin": viewer_is_admin,
        "viewer_can_view_daily_details": viewer_can_view_daily_details,
        "available_departments": available_departments,
        "available_positions": available_positions,
        "default_selected_departments": default_selected_departments,
        "default_selected_positions": default_selected_positions,
        "selected_department": selected_department,
        "selected_departments": selected_departments,
        "selected_department_label": selected_department_label,
        "selected_positions": selected_positions,
        "selected_position_label": selected_position_label,
        "department_filter_active": department_filter_active,
        "position_filter_active": position_filter_active,
        "department_users": department_users,
    }


def build_department_schedule_payload(
    current_user: dict | None,
    anchor_date: str,
    requested_department: str | None = None,
    requested_departments: object | None = None,
    requested_positions: object | None = None,
) -> dict:
    target_date = validate_date(anchor_date)
    week_start, week_end, week_dates = build_week_window(target_date)
    scope = resolve_department_schedule_scope(
        current_user,
        requested_department,
        requested_departments=requested_departments,
        requested_positions=requested_positions,
    )
    viewer_is_admin = bool(scope["viewer_is_admin"])
    viewer_can_view_daily_details = bool(scope["viewer_can_view_daily_details"])
    available_departments = list(scope["available_departments"])
    available_positions = list(scope["available_positions"])
    selected_department = str(scope["selected_department"])
    selected_departments = list(scope["selected_departments"])
    selected_positions = list(scope["selected_positions"])
    department_users = list(scope["department_users"])
    department_user_ids = [str(item.get("user_id") or "").strip() for item in department_users if str(item.get("user_id") or "").strip()]
    weekly_plan_edit_logs_map = list_weekly_plan_edit_logs_for_targets(
        week_start,
        department_user_ids,
        limit_per_target=3,
    )

    daily_totals = [
        {"work_date": work_date, "weekday_label": DEPARTMENT_SCHEDULE_WEEKDAY_LABELS[index], "filled_users": 0, "total_items": 0, "total_hours": 0.0}
        for index, work_date in enumerate(week_dates)
    ]
    members: list[dict] = []
    department_total_hours = 0.0
    department_total_items = 0
    department_filled_days = 0

    for member in department_users:
        member_user_id = str(member.get("user_id") or "").strip()
        _, weekly_plan_settings, weekly_plan_updated_at = get_weekly_plan_settings(target_date, user_id=member_user_id)
        weekly_plan_rows = build_department_weekly_plan_rows(weekly_plan_settings)
        weekly_plan_edit_logs = list(weekly_plan_edit_logs_map.get(member_user_id) or [])
        week_entries = fetch_week_entries(target_date, user_id=member_user_id) if viewer_can_view_daily_details else []
        entry_map = {str(entry["work_date"]): entry for entry in week_entries if entry}
        member_total_hours = 0.0
        member_total_items = 0
        member_filled_days = 0
        days: list[dict] = []

        if viewer_can_view_daily_details:
            for index, work_date in enumerate(week_dates):
                entry = entry_map.get(work_date)
                if entry:
                    entry_total_hours = float(entry.get("total_hours") or 0)
                    entry_item_count = int(entry.get("item_count") or len(entry.get("items") or []))
                    member_total_hours += entry_total_hours
                    member_total_items += entry_item_count
                    member_filled_days += 1
                    daily_totals[index]["filled_users"] += 1
                    daily_totals[index]["total_items"] += entry_item_count
                    daily_totals[index]["total_hours"] += entry_total_hours
                    days.append(
                        {
                            "work_date": work_date,
                            "weekday_label": DEPARTMENT_SCHEDULE_WEEKDAY_LABELS[index],
                            "has_entry": True,
                            "item_count": entry_item_count,
                            "total_hours": str(entry.get("total_hours") or ""),
                            "updated_at": str(entry.get("updated_at") or ""),
                            "items": list(entry.get("items") or []),
                        }
                    )
                else:
                    days.append(
                        {
                            "work_date": work_date,
                            "weekday_label": DEPARTMENT_SCHEDULE_WEEKDAY_LABELS[index],
                            "has_entry": False,
                            "item_count": 0,
                            "total_hours": "",
                            "updated_at": "",
                            "items": [],
                        }
                    )

        department_total_hours += member_total_hours
        department_total_items += member_total_items
        department_filled_days += member_filled_days
        members.append(
            {
                "user": member,
                "weekly_plan_rows": weekly_plan_rows,
                "weekly_other_pending": str(weekly_plan_settings.get("weekly_other_pending", "") or "").strip(),
                "weekly_plan_updated_at": weekly_plan_updated_at,
                "weekly_plan_last_editor": weekly_plan_edit_logs[0] if weekly_plan_edit_logs else None,
                "weekly_plan_edit_logs": weekly_plan_edit_logs,
                "days": days,
                "week_stats": {
                    "total_hours": format_hours(member_total_hours),
                    "total_items": member_total_items,
                    "filled_days": member_filled_days,
                },
            }
        )

    for summary in daily_totals:
        summary["total_hours"] = format_hours(summary["total_hours"])

    return {
        "anchor_date": target_date,
        "week_start": week_start,
        "week_end": week_end,
        "viewer": current_user,
        "can_edit_weekly_plan": _can_edit_department_schedule_weekly_plan(current_user),
        "show_daily_section": viewer_can_view_daily_details,
        "show_admin_button": viewer_is_admin,
        "can_switch_department": viewer_is_admin,
        "allow_all_departments": viewer_is_admin,
        "departments": available_departments,
        "available_positions": available_positions,
        "selected_department": selected_department,
        "selected_departments": selected_departments,
        "selected_department_label": str(scope["selected_department_label"]),
        "selected_positions": selected_positions,
        "selected_position_label": str(scope["selected_position_label"]),
        "default_selected_departments": list(scope["default_selected_departments"]),
        "default_selected_positions": list(scope["default_selected_positions"]),
        "member_count": len(members),
        "summary": {
            "member_count": len(members),
            "total_hours": format_hours(department_total_hours),
            "total_items": department_total_items,
            "filled_days": department_filled_days,
        },
        "daily_totals": daily_totals,
        "members": members,
    }


def list_department_schedule_edit_logs(
    target_user_ids: list[str] | tuple[str, ...],
) -> list[dict]:
    normalized_user_ids: list[str] = []
    for item in target_user_ids:
        normalized_user_id = normalize_user_id(item)
        if normalized_user_id and normalized_user_id not in normalized_user_ids:
            normalized_user_ids.append(normalized_user_id)
    if not normalized_user_ids:
        return []
    placeholders = ", ".join("?" for _ in normalized_user_ids)
    query = f"""
        SELECT week_start, target_user_id, target_display_name, editor_user_id, editor_display_name, change_details_json, edited_at
        FROM weekly_plan_edit_logs
        WHERE target_user_id IN ({placeholders}) AND editor_user_id != target_user_id
        ORDER BY edited_at DESC, id DESC
    """
    with get_connection() as connection:
        rows = connection.execute(query, normalized_user_ids).fetchall()
    return [build_weekly_plan_edit_log_payload(row) for row in rows]


def build_department_schedule_edit_logs_payload(
    current_user: dict | None,
    requested_department: str | None = None,
    requested_departments: object | None = None,
    requested_positions: object | None = None,
) -> dict[str, Any]:
    if not current_user:
        raise PermissionError("请先登录后再查看日程编辑日志。")

    scope = resolve_department_schedule_scope(
        current_user,
        requested_department,
        requested_departments=requested_departments,
        requested_positions=requested_positions,
    )
    can_view_all_logs = bool(scope["viewer_is_admin"]) or bool(current_user.get("is_department_admin"))
    viewer_user_id = normalize_user_id(current_user.get("user_id"))
    viewer_display_name = str(current_user.get("display_name") or viewer_user_id).strip() or viewer_user_id
    if can_view_all_logs:
        target_user_ids = [
            str(item.get("user_id") or "").strip()
            for item in scope["department_users"]
            if str(item.get("user_id") or "").strip()
        ]
        logs = list_department_schedule_edit_logs(target_user_ids)
        scope_mode = "department"
        scope_label = str(scope["selected_department_label"])
    else:
        logs = list_department_schedule_edit_logs([viewer_user_id])
        scope_mode = "self"
        scope_label = viewer_display_name

    return {
        "viewer": current_user,
        "can_view_all": can_view_all_logs,
        "scope_mode": scope_mode,
        "scope_label": scope_label,
        "selected_department": str(scope["selected_department"]),
        "selected_departments": list(scope["selected_departments"]),
        "selected_department_label": str(scope["selected_department_label"]),
        "selected_positions": list(scope["selected_positions"]),
        "selected_position_label": str(scope["selected_position_label"]),
        "log_count": len(logs),
        "logs": logs,
    }


save_admin_account_credentials = auth_service.save_admin_account_credentials
verify_admin_account_password = auth_service.verify_admin_account_password
get_admin_account_public_info = auth_service.get_admin_account_public_info
get_admin_account_credentials = auth_service.get_admin_account_credentials
ensure_default_admin_account_credentials = auth_service.ensure_default_admin_account_credentials
create_user_session = auth_service.create_user_session
delete_user_session = auth_service.delete_user_session
get_user_by_session = auth_service.get_user_by_session


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    auth_service.init_auth_storage()
    with get_connection() as connection:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT 'local_default_user',
                work_date TEXT NOT NULL UNIQUE,
                plan_content TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                items_json TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        daily_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(daily_entries)").fetchall()
        }
        if "items_json" not in daily_columns:
            connection.execute(
                "ALTER TABLE daily_entries ADD COLUMN items_json TEXT NOT NULL DEFAULT '[]'"
            )
            daily_columns.add("items_json")
        if "user_id" not in daily_columns or "progress_content" in daily_columns:
            connection.executescript(
                """
                CREATE TABLE daily_entries_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    work_date TEXT NOT NULL,
                    plan_content TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    items_json TEXT NOT NULL DEFAULT '[]',
                    UNIQUE(user_id, work_date)
                );
                INSERT INTO daily_entries_v2 (
                    id, user_id, work_date, plan_content, notes, created_at, updated_at, items_json
                )
                SELECT id, 'local_default_user', work_date, plan_content, notes, created_at, updated_at, items_json
                FROM daily_entries;
                DROP TABLE daily_entries;
                ALTER TABLE daily_entries_v2 RENAME TO daily_entries;
                """
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_daily_entries_user_date ON daily_entries(user_id, work_date)"
        )
        existing_keys = {
            row["setting_key"]
            for row in connection.execute("SELECT setting_key FROM app_settings").fetchall()
        }
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for key, value in DEFAULT_PAGE_SETTINGS.items():
            if key not in existing_keys:
                connection.execute(
                    """
                    INSERT INTO app_settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (key, value, timestamp),
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_plans (
                user_id TEXT NOT NULL DEFAULT 'local_default_user',
                week_start TEXT NOT NULL,
                settings_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, week_start)
            )
            """
        )
        weekly_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(weekly_plans)").fetchall()
        }
        if "user_id" not in weekly_columns:
            connection.executescript(
                """
                CREATE TABLE weekly_plans_v2 (
                    user_id TEXT NOT NULL,
                    week_start TEXT NOT NULL,
                    settings_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, week_start)
                );
                INSERT INTO weekly_plans_v2 (
                    user_id, week_start, settings_json, created_at, updated_at
                )
                SELECT 'local_default_user', week_start, settings_json, created_at, updated_at
                FROM weekly_plans;
                DROP TABLE weekly_plans;
                ALTER TABLE weekly_plans_v2 RENAME TO weekly_plans;
                """
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_week ON weekly_plans(user_id, week_start)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_plan_edit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                target_user_id TEXT NOT NULL,
                target_display_name TEXT NOT NULL DEFAULT '',
                editor_user_id TEXT NOT NULL,
                editor_display_name TEXT NOT NULL DEFAULT '',
                change_details_json TEXT NOT NULL DEFAULT '[]',
                edited_at TEXT NOT NULL
            )
            """
        )
        weekly_edit_log_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(weekly_plan_edit_logs)").fetchall()
        }
        if "change_details_json" not in weekly_edit_log_columns:
            connection.execute(
                "ALTER TABLE weekly_plan_edit_logs ADD COLUMN change_details_json TEXT NOT NULL DEFAULT '[]'"
            )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weekly_plan_edit_logs_target_week
            ON weekly_plan_edit_logs(target_user_id, week_start, edited_at DESC, id DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weekly_plan_edit_logs_target_time
            ON weekly_plan_edit_logs(target_user_id, edited_at DESC, id DESC)
            """
        )
        existing_weekly_rows = connection.execute(
            "SELECT COUNT(*) AS row_count FROM weekly_plans WHERE user_id = ?",
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()["row_count"]
        if existing_weekly_rows == 0:
            legacy_rows = connection.execute(
                "SELECT setting_key, setting_value FROM app_settings WHERE setting_key LIKE 'weekly_%'"
            ).fetchall()
            legacy_settings = DEFAULT_PAGE_SETTINGS.copy()
            has_legacy_content = False
            for row in legacy_rows:
                key = row["setting_key"]
                if key in legacy_settings:
                    value = str(row["setting_value"] or "").strip()
                    legacy_settings[key] = value
                    has_legacy_content = has_legacy_content or bool(value)
            if has_legacy_content:
                current_week_start = get_week_start(date.today().isoformat())
                connection.execute(
                    """
                    INSERT OR REPLACE INTO weekly_plans (user_id, week_start, settings_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        DEFAULT_LOCAL_USER_ID,
                        current_week_start,
                        json.dumps(legacy_settings, ensure_ascii=False),
                        timestamp,
                        timestamp,
                    ),
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dingtalk_user_directory_cache (
                name_key TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                raw_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

def get_week_start(value: str) -> str:
    target = validate_date(value)
    target_date = datetime.strptime(target, "%Y-%m-%d")
    monday = target_date - timedelta(days=target_date.weekday())
    return monday.strftime("%Y-%m-%d")


def normalize_weekly_plan_settings(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    settings = {}
    for key in WEEKLY_PLAN_KEYS:
        settings[key] = str(source.get(key, DEFAULT_PAGE_SETTINGS[key])).strip()
    return settings


def get_weekly_plan_settings(anchor_date: str, user_id: str | None = None) -> tuple[str, dict, str]:
    week_start = get_week_start(anchor_date)
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT settings_json, updated_at FROM weekly_plans WHERE user_id = ? AND week_start = ?",
            (normalized_user_id, week_start),
        ).fetchone()
    if not row:
        return week_start, DEFAULT_PAGE_SETTINGS.copy(), ""
    try:
        loaded = json.loads(row["settings_json"] or "{}")
    except json.JSONDecodeError:
        loaded = {}
    return week_start, normalize_weekly_plan_settings(loaded), str(row["updated_at"] or "")


def save_weekly_plan_settings(
    week_start: str, payload: dict | None, user_id: str | None = None
) -> tuple[str, dict, str]:
    normalized_week_start = get_week_start(week_start)
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    settings = normalize_weekly_plan_settings(payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT created_at FROM weekly_plans WHERE user_id = ? AND week_start = ?",
            (normalized_user_id, normalized_week_start),
        ).fetchone()
        created_at = existing["created_at"] if existing else timestamp
        connection.execute(
            """
            INSERT INTO weekly_plans (user_id, week_start, settings_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, week_start) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = excluded.updated_at
            """,
            (
                normalized_user_id,
                normalized_week_start,
                json.dumps(settings, ensure_ascii=False),
                created_at,
                timestamp,
            ),
        )
    return normalized_week_start, settings, timestamp


def build_weekly_plan_change_details(previous_settings: dict | None, next_settings: dict | None) -> list[str]:
    previous = normalize_weekly_plan_settings(previous_settings)
    current = normalize_weekly_plan_settings(next_settings)
    details: list[str] = []
    for key in WEEKLY_PLAN_KEYS:
        before_value = str(previous.get(key, "") or "").strip()
        after_value = str(current.get(key, "") or "").strip()
        if before_value == after_value:
            continue
        field_label = WEEKLY_PLAN_FIELD_LABELS.get(key, key)
        if not before_value and after_value:
            details.append(f"新增{field_label}：{after_value}")
        elif before_value and not after_value:
            details.append(f"删除{field_label}：{before_value}")
        else:
            details.append(f"修改{field_label}：原“{before_value}”改为“{after_value}”")
    return details


def build_weekly_plan_edit_log_payload(row: sqlite3.Row | dict | None) -> dict:
    if isinstance(row, sqlite3.Row):
        source = {key: row[key] for key in row.keys()}
    elif isinstance(row, dict):
        source = row
    else:
        source = {}
    editor_user_id = str(source.get("editor_user_id") or "").strip()
    target_user_id = str(source.get("target_user_id") or "").strip()
    raw_change_details = source.get("change_details_json")
    if isinstance(raw_change_details, str):
        try:
            parsed_change_details = json.loads(raw_change_details or "[]")
        except json.JSONDecodeError:
            parsed_change_details = []
    elif isinstance(raw_change_details, list):
        parsed_change_details = raw_change_details
    else:
        parsed_change_details = []
    change_details = [str(item or "").strip() for item in parsed_change_details if str(item or "").strip()]
    return {
        "week_start": str(source.get("week_start") or "").strip(),
        "editor_user_id": editor_user_id,
        "editor_display_name": str(source.get("editor_display_name") or editor_user_id).strip() or editor_user_id,
        "target_user_id": target_user_id,
        "target_display_name": str(source.get("target_display_name") or target_user_id).strip() or target_user_id,
        "edited_at": str(source.get("edited_at") or "").strip(),
        "is_self_edit": bool(editor_user_id and target_user_id and editor_user_id == target_user_id),
        "change_details": change_details,
    }


def record_weekly_plan_edit_log(
    week_start: str,
    *,
    target_user: dict | None,
    editor_user: dict | None,
    change_details: list[str] | tuple[str, ...] | None = None,
    edited_at: str | None = None,
) -> dict | None:
    normalized_week_start = get_week_start(week_start)
    target_user_id = normalize_user_id(str(target_user.get("user_id") or "") if isinstance(target_user, dict) else "")
    editor_user_id = normalize_user_id(str(editor_user.get("user_id") or "") if isinstance(editor_user, dict) else "")
    if not target_user_id or not editor_user_id or target_user_id == editor_user_id:
        return None
    normalized_change_details = [str(item or "").strip() for item in (change_details or []) if str(item or "").strip()]
    if not normalized_change_details:
        return None
    timestamp = str(edited_at or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "week_start": normalized_week_start,
        "target_user_id": target_user_id,
        "target_display_name": str(
            (target_user.get("display_name") or target_user_id) if isinstance(target_user, dict) else target_user_id
        ).strip()
        or target_user_id,
        "editor_user_id": editor_user_id,
        "editor_display_name": str(
            (editor_user.get("display_name") or editor_user_id) if isinstance(editor_user, dict) else editor_user_id
        ).strip()
        or editor_user_id,
        "change_details_json": json.dumps(normalized_change_details, ensure_ascii=False),
        "edited_at": timestamp,
    }
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO weekly_plan_edit_logs (
                week_start,
                target_user_id,
                target_display_name,
                editor_user_id,
                editor_display_name,
                change_details_json,
                edited_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["week_start"],
                payload["target_user_id"],
                payload["target_display_name"],
                payload["editor_user_id"],
                payload["editor_display_name"],
                payload["change_details_json"],
                payload["edited_at"],
            ),
        )
    return build_weekly_plan_edit_log_payload(payload)


def list_weekly_plan_edit_logs(
    week_start: str,
    *,
    target_user_id: str | None = None,
    limit: int = 3,
) -> list[dict]:
    normalized_week_start = get_week_start(week_start)
    normalized_target_user_id = normalize_user_id(target_user_id)
    resolved_limit = max(1, int(limit or 0))
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT week_start, target_user_id, target_display_name, editor_user_id, editor_display_name, change_details_json, edited_at
            FROM weekly_plan_edit_logs
            WHERE week_start = ? AND target_user_id = ? AND editor_user_id != target_user_id
            ORDER BY edited_at DESC, id DESC
            LIMIT ?
            """,
            (normalized_week_start, normalized_target_user_id, resolved_limit),
        ).fetchall()
    return [build_weekly_plan_edit_log_payload(row) for row in rows]


def list_weekly_plan_edit_logs_for_targets(
    week_start: str,
    target_user_ids: list[str] | tuple[str, ...],
    *,
    limit_per_target: int = 3,
) -> dict[str, list[dict]]:
    normalized_week_start = get_week_start(week_start)
    normalized_user_ids = []
    for item in target_user_ids:
        normalized_user_id = normalize_user_id(item)
        if normalized_user_id and normalized_user_id not in normalized_user_ids:
            normalized_user_ids.append(normalized_user_id)
    if not normalized_user_ids:
        return {}
    placeholders = ", ".join("?" for _ in normalized_user_ids)
    params = [normalized_week_start, *normalized_user_ids]
    query = f"""
        SELECT week_start, target_user_id, target_display_name, editor_user_id, editor_display_name, change_details_json, edited_at
        FROM weekly_plan_edit_logs
        WHERE week_start = ? AND target_user_id IN ({placeholders}) AND editor_user_id != target_user_id
        ORDER BY target_user_id ASC, edited_at DESC, id DESC
    """
    grouped: dict[str, list[dict]] = {user_id: [] for user_id in normalized_user_ids}
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    for row in rows:
        target_user_id = normalize_user_id(row["target_user_id"])
        bucket = grouped.setdefault(target_user_id, [])
        if len(bucket) >= max(1, int(limit_per_target or 0)):
            continue
        bucket.append(build_weekly_plan_edit_log_payload(row))
    return grouped


def normalize_ui_settings(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    background_image = str(source.get("background_image", DEFAULT_UI_SETTINGS["background_image"])).strip()
    background_mode = str(source.get("background_mode", DEFAULT_UI_SETTINGS["background_mode"])).strip()
    if background_image.startswith(BING_DAILY_BACKGROUND_PROXY_PATH):
        background_image = BING_DAILY_BACKGROUND_PROXY_PATH
    if background_image and not (
        background_image.startswith("data:image/")
        or background_image == BING_DAILY_BACKGROUND_PROXY_PATH
    ):
        raise ValueError("背景图必须是本地图片，或使用 Bing 每日图片。")
    if len(background_image.encode("utf-8")) > 8 * 1024 * 1024:
        raise ValueError("背景图数据过大，请选择 5MB 左右以内的图片。")
    if background_mode not in {"cover", "contain", "repeat"}:
        background_mode = DEFAULT_UI_SETTINGS["background_mode"]

    def normalize_opacity(value: object, fallback: float) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = float(fallback)
        value = max(0.25, min(1.0, value))
        return round(value, 2)

    legacy_values = [
        source.get("region_opacity"),
        source.get("weekly_region_opacity"),
        source.get("editor_region_opacity"),
        source.get("month_region_opacity"),
    ]
    opacity_source = next((value for value in legacy_values if value not in (None, "")), DEFAULT_UI_SETTINGS["region_opacity"])

    return {
        "background_image": background_image,
        "background_mode": background_mode,
        "region_opacity": normalize_opacity(opacity_source, DEFAULT_UI_SETTINGS["region_opacity"]),
    }


def build_bing_daily_background_client_url(target_date: date | None = None) -> str:
    resolved_date = target_date or date.today()
    return f"{BING_DAILY_BACKGROUND_PROXY_PATH}?day={resolved_date.isoformat()}"


def build_client_ui_settings(settings: dict | None, *, target_date: date | None = None) -> dict:
    normalized = normalize_ui_settings(settings)
    client_settings = dict(normalized)
    if client_settings.get("background_image") == BING_DAILY_BACKGROUND_PROXY_PATH:
        client_settings["background_image"] = build_bing_daily_background_client_url(target_date)
    return client_settings


def fetch_remote_json(url: str, *, timeout: int = 15, headers: dict[str, str] | None = None) -> dict[str, object]:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": f"DailyPlanner/{APP_VERSION}",
    }
    for key, value in (headers or {}).items():
        request_headers[str(key)] = str(value)
    request = Request(url, headers=request_headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as error:
        raise RuntimeError(f"Bing 每日图片服务暂时不可用（HTTP {error.code}）。") from error
    except URLError as error:
        raise RuntimeError("无法连接 Bing 每日图片服务，请检查网络。") from error
    try:
        payload = json.loads(raw_body or "{}")
    except json.JSONDecodeError as error:
        raise RuntimeError("Bing 每日图片服务返回了无法解析的数据。") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Bing 每日图片服务返回格式不正确。")
    return payload


def resolve_bing_daily_background_url(market: str = BING_DAILY_IMAGE_MARKET) -> str:
    normalized_market = re.sub(r"[^A-Za-z-]", "", str(market or "").strip()) or BING_DAILY_IMAGE_MARKET
    payload = fetch_remote_json(
        f"{BING_DAILY_IMAGE_METADATA_URL}?{urlencode({'format': 'js', 'idx': 0, 'n': 1, 'mkt': normalized_market})}"
    )
    images = payload.get("images")
    if not isinstance(images, list) or not images:
        raise RuntimeError("Bing 每日图片服务未返回可用图片。")
    image_payload = images[0] if isinstance(images[0], dict) else {}
    image_url = str(image_payload.get("url") or "").strip()
    if not image_url:
        image_urlbase = str(image_payload.get("urlbase") or "").strip()
        if image_urlbase:
            image_url = f"{image_urlbase}_1920x1080.jpg"
    if not image_url:
        raise RuntimeError("Bing 每日图片服务未返回图片地址。")
    if image_url.startswith("//"):
        return f"https:{image_url}"
    if image_url.startswith("/"):
        return f"https://www.bing.com{image_url}"
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    raise RuntimeError("Bing 每日图片地址格式不正确。")


def get_ui_settings(user_id: str | None = None) -> tuple[dict, str]:
    normalized_user_id = normalize_user_id(user_id)
    setting_key = f"user:{normalized_user_id}:ui_settings_json"
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    if not row:
        return build_client_ui_settings(DEFAULT_UI_SETTINGS), ""
    try:
        loaded = json.loads(row["setting_value"] or "{}")
    except json.JSONDecodeError:
        loaded = {}
    return build_client_ui_settings(loaded), str(row["updated_at"] or "")


def save_ui_settings(payload: dict | None, user_id: str | None = None) -> tuple[dict, str]:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    setting_key = f"user:{normalized_user_id}:ui_settings_json"
    settings = normalize_ui_settings(payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (setting_key, json.dumps(settings, ensure_ascii=False), timestamp),
        )
    return build_client_ui_settings(settings), timestamp


def normalize_prompt_template_text(value: object) -> str:
    return str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")


def build_user_prompt_template_setting_key(user_id: str, filename: str) -> str:
    normalized_user_id = normalize_user_id(user_id)
    return f"user:{normalized_user_id}:{USER_PROMPT_TEMPLATE_SETTING_KEY_PREFIX}:{filename}"


def load_default_prompt_template(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    try:
        return normalize_prompt_template_text(prompt_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise RuntimeError(f"无法读取 AI 提示词文件：{prompt_path}") from error


def get_user_prompt_template_override(filename: str, user_id: str | None = None) -> tuple[str | None, str]:
    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        return None, ""
    setting_key = build_user_prompt_template_setting_key(normalized_user_id, filename)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    if not row:
        return None, ""
    return normalize_prompt_template_text(row["setting_value"] or ""), str(row["updated_at"] or "")


def list_user_prompt_templates(user_id: str | None = None) -> list[dict]:
    normalized_user_id = normalize_user_id(user_id)
    prompt_templates: list[dict] = []
    for definition in USER_PROMPT_TEMPLATE_DEFINITIONS:
        filename = str(definition["filename"])
        default_content = load_default_prompt_template(filename)
        override_content, updated_at = get_user_prompt_template_override(filename, user_id=normalized_user_id)
        customized = override_content is not None
        prompt_templates.append(
            {
                "id": str(definition["id"]),
                "title": str(definition["title"]),
                "description": str(definition["description"]),
                "filename": filename,
                "content": override_content if customized else default_content,
                "default_content": default_content,
                "updated_at": updated_at,
                "customized": customized,
            }
        )
    return prompt_templates


def save_user_prompt_templates(payload: dict | None, user_id: str | None = None) -> dict:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    payload_map = payload if isinstance(payload, dict) else {}
    raw_prompts = payload_map.get("prompts")
    prompt_updates: list[tuple[str, object]] = []
    if isinstance(raw_prompts, list):
        for item in raw_prompts:
            if not isinstance(item, dict):
                continue
            prompt_id = str(item.get("id") or item.get("prompt_id") or "").strip()
            if not prompt_id:
                continue
            prompt_updates.append((prompt_id, item.get("content", "")))
    else:
        prompt_id = str(payload_map.get("prompt_id", "")).strip()
        if prompt_id:
            prompt_updates.append((prompt_id, payload_map.get("content", "")))
    if not prompt_updates:
        raise ValueError("请至少提交一个提示词。")

    unique_prompt_updates: dict[str, str] = {}
    for prompt_id, raw_content in prompt_updates:
        definition = USER_PROMPT_TEMPLATE_BY_ID.get(prompt_id)
        if not definition:
            raise ValueError(f"未找到提示词：{prompt_id}")
        normalized_content = normalize_prompt_template_text(raw_content)
        if not normalized_content.strip():
            raise ValueError(f"提示词“{definition['title']}”不能为空。")
        unique_prompt_updates[prompt_id] = normalized_content

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        for prompt_id, content in unique_prompt_updates.items():
            definition = USER_PROMPT_TEMPLATE_BY_ID[prompt_id]
            filename = str(definition["filename"])
            setting_key = build_user_prompt_template_setting_key(normalized_user_id, filename)
            default_content = load_default_prompt_template(filename)
            if content == default_content:
                connection.execute("DELETE FROM app_settings WHERE setting_key = ?", (setting_key,))
                continue
            connection.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    updated_at = excluded.updated_at
                """,
                (setting_key, content, timestamp),
            )
    return {
        "prompts": list_user_prompt_templates(normalized_user_id),
        "updated_at": timestamp,
    }


def build_user_dingtalk_mcp_setting_key(user_id: str) -> str:
    normalized_user_id = normalize_user_id(user_id)
    return f"user:{normalized_user_id}:{DINGTALK_USER_MCP_CONFIG_SETTING_KEY}"


def normalize_dingtalk_template_field(payload: object) -> dict | None:
    if not isinstance(payload, dict):
        return None
    field_name = str(payload.get("field_name", payload.get("key", "")) or "").strip()
    if not field_name:
        return None
    try:
        field_sort = int(payload.get("field_sort", payload.get("sort", 0)) or 0)
    except (TypeError, ValueError):
        field_sort = 0
    try:
        field_type = int(payload.get("field_type", payload.get("type", 0)) or 0)
    except (TypeError, ValueError):
        field_type = 0
    return {
        "field_name": field_name,
        "field_sort": field_sort,
        "field_type": field_type,
    }


def normalize_dingtalk_template_config(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    template_id = str(source.get("template_id", source.get("templateId", "")) or "").strip()
    template_name = str(
        source.get("template_name", source.get("templateName", source.get("name", ""))) or ""
    ).strip()
    fields: list[dict] = []
    seen_fields: set[tuple[int, str]] = set()
    for item in source.get("fields", []):
        field = normalize_dingtalk_template_field(item)
        if not field:
            continue
        identity = (int(field["field_sort"]), str(field["field_name"]))
        if identity in seen_fields:
            continue
        seen_fields.add(identity)
        fields.append(field)
    fields.sort(key=lambda item: (int(item["field_sort"]), str(item["field_name"])))
    return {
        "template_id": template_id,
        "template_name": template_name,
        "fields": fields,
    }


def has_dingtalk_template_selection(payload: object) -> bool:
    template = normalize_dingtalk_template_config(payload)
    return bool(template["template_id"] or template["template_name"] or template["fields"])


def get_dingtalk_template_support_error(template_config: object, *, report_kind: str) -> str | None:
    normalized = normalize_dingtalk_template_config(template_config)
    report_label = "日报" if report_kind == "daily" else "周报"
    expected_count = (
        len(DINGTALK_DAILY_LOG_SECTION_TITLES)
        if report_kind == "daily"
        else len(DINGTALK_WEEKLY_REPORT_SECTION_TITLES)
    )
    if not normalized["template_id"]:
        return f"所选{report_label}模板缺少模板 ID。"
    if not normalized["template_name"]:
        return f"所选{report_label}模板缺少模板名称。"
    if len(normalized["fields"]) != expected_count:
        return f"所选{report_label}模板字段数量需为 {expected_count} 个，当前为 {len(normalized['fields'])} 个。"
    invalid_fields = [
        str(field.get("field_name") or f"字段{index}")
        for index, field in enumerate(normalized["fields"], start=1)
        if int(field.get("field_type", 0) or 0) != 1
    ]
    if invalid_fields:
        return f"所选{report_label}模板仅支持文本字段，以下字段类型暂不兼容：{'、'.join(invalid_fields)}。"
    return None


def annotate_dingtalk_template_support(template_config: object) -> dict:
    normalized = normalize_dingtalk_template_config(template_config)
    daily_support_error = get_dingtalk_template_support_error(normalized, report_kind="daily")
    weekly_support_error = get_dingtalk_template_support_error(normalized, report_kind="weekly")
    return {
        **normalized,
        "field_count": len(normalized["fields"]),
        "daily_supported": daily_support_error is None,
        "daily_support_error": daily_support_error or "",
        "weekly_supported": weekly_support_error is None,
        "weekly_support_error": weekly_support_error or "",
    }


def normalize_user_dingtalk_mcp_config(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    daily_template = normalize_dingtalk_template_config(source.get("daily_template", {}))
    weekly_template = normalize_dingtalk_template_config(source.get("weekly_template", {}))
    return {
        "log_mcp_url": str(source.get("log_mcp_url", "") or "").strip(),
        "directory_mcp_url": str(source.get("directory_mcp_url", "") or "").strip(),
        "daily_template": daily_template if has_dingtalk_template_selection(daily_template) else {},
        "weekly_template": weekly_template if has_dingtalk_template_selection(weekly_template) else {},
    }


def has_user_dingtalk_mcp_config_values(config: dict | None) -> bool:
    payload = config if isinstance(config, dict) else {}
    return any(
        (
            str(payload.get("log_mcp_url") or "").strip(),
            str(payload.get("directory_mcp_url") or "").strip(),
            has_dingtalk_template_selection(payload.get("daily_template")),
            has_dingtalk_template_selection(payload.get("weekly_template")),
        )
    )


def get_user_dingtalk_mcp_config(user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    setting_key = build_user_dingtalk_mcp_setting_key(normalized_user_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    loaded_payload: dict = {}
    updated_at = ""
    if row:
        try:
            payload = json.loads(row["setting_value"] or "{}")
            if isinstance(payload, dict):
                loaded_payload = payload
        except json.JSONDecodeError:
            loaded_payload = {}
        updated_at = str(row["updated_at"] or "")
    config = normalize_user_dingtalk_mcp_config(loaded_payload)
    return {
        "user_id": normalized_user_id,
        "log_mcp_url": config["log_mcp_url"],
        "directory_mcp_url": config["directory_mcp_url"],
        "daily_template": config["daily_template"],
        "weekly_template": config["weekly_template"],
        "uses_custom_log_mcp": bool(config["log_mcp_url"]),
        "uses_custom_directory_mcp": bool(config["directory_mcp_url"]),
        "updated_at": updated_at if has_user_dingtalk_mcp_config_values(config) else "",
    }


def get_effective_dingtalk_report_template_config(
    *, user_id: str | None = None, report_kind: str
) -> dict:
    user_config = get_user_dingtalk_mcp_config(user_id=user_id)
    selected_template = user_config.get("daily_template" if report_kind == "daily" else "weekly_template", {})
    normalized_selected = normalize_dingtalk_template_config(selected_template)
    if has_dingtalk_template_selection(normalized_selected):
        support_error = get_dingtalk_template_support_error(normalized_selected, report_kind=report_kind)
        return {
            **normalized_selected,
            "source": "user" if support_error is None else "invalid",
            "support_error": support_error or "",
        }
    return {
        "template_id": "",
        "template_name": "",
        "fields": [],
        "source": "missing",
        "support_error": "",
    }


def get_effective_dingtalk_daily_template_config(user_id: str | None = None) -> dict:
    return get_effective_dingtalk_report_template_config(user_id=user_id, report_kind="daily")


def get_effective_dingtalk_weekly_template_config(user_id: str | None = None) -> dict:
    return get_effective_dingtalk_report_template_config(user_id=user_id, report_kind="weekly")


def require_selected_dingtalk_report_template_config(
    user_id: str | None = None,
    *,
    report_kind: str,
) -> dict:
    template_config = get_effective_dingtalk_report_template_config(user_id=user_id, report_kind=report_kind)
    support_error = str(template_config.get("support_error") or "").strip()
    if support_error:
        raise RuntimeError(support_error)
    if not has_dingtalk_template_selection(template_config):
        raise RuntimeError(
            DINGTALK_DAILY_TEMPLATE_REQUIRED_ERROR
            if report_kind == "daily"
            else DINGTALK_WEEKLY_TEMPLATE_REQUIRED_ERROR
        )
    return normalize_dingtalk_template_config(template_config)


def save_user_dingtalk_mcp_config(user_id: str | None, payload: dict | None) -> dict:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    setting_key = build_user_dingtalk_mcp_setting_key(normalized_user_id)
    existing_config = get_user_dingtalk_mcp_config(normalized_user_id)
    config = normalize_user_dingtalk_mcp_config(payload)
    if str(config.get("log_mcp_url") or "").strip() != str(existing_config.get("log_mcp_url") or "").strip():
        config["daily_template"] = {}
        config["weekly_template"] = {}
    if has_dingtalk_template_selection(config["daily_template"]):
        validation_error = get_dingtalk_template_support_error(config["daily_template"], report_kind="daily")
        if validation_error:
            raise ValueError(validation_error)
    if has_dingtalk_template_selection(config["weekly_template"]):
        validation_error = get_dingtalk_template_support_error(config["weekly_template"], report_kind="weekly")
        if validation_error:
            raise ValueError(validation_error)
    with get_connection() as connection:
        if has_user_dingtalk_mcp_config_values(config):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    updated_at = excluded.updated_at
                """,
                (setting_key, json.dumps(config, ensure_ascii=False), timestamp),
            )
        else:
            connection.execute("DELETE FROM app_settings WHERE setting_key = ?", (setting_key,))
    return get_user_dingtalk_mcp_config_summary(normalized_user_id)


def build_user_dingtalk_mcp_config_summary(user: dict | None) -> dict:
    row = user if isinstance(user, dict) else {}
    normalized_user_id = normalize_user_id(str(row.get("user_id", "")).strip())
    config = get_user_dingtalk_mcp_config(normalized_user_id)
    effective_config = get_effective_dingtalk_mcp_config(normalized_user_id)
    effective_daily_template = get_effective_dingtalk_daily_template_config(normalized_user_id)
    effective_weekly_template = get_effective_dingtalk_weekly_template_config(normalized_user_id)
    return {
        **config,
        "display_name": str(row.get("display_name", "") or normalized_user_id).strip() or normalized_user_id,
        "role": str(row.get("role", "") or "user").strip() or "user",
        "department": str(row.get("department", "") or "").strip(),
        "position": str(row.get("position", "") or "").strip(),
        "positions": [str(item or "").strip() for item in row.get("positions", []) if str(item or "").strip()],
        "position_labels": str(row.get("position_labels", "") or "").strip(),
        "log_mcp_source": str(effective_config.get("log_mcp_source") or "missing").strip() or "missing",
        "directory_mcp_source": str(effective_config.get("directory_mcp_source") or "missing").strip()
        or "missing",
        "effective_daily_template": effective_daily_template,
        "effective_weekly_template": effective_weekly_template,
        "daily_template_source": str(effective_daily_template.get("source") or "missing").strip() or "missing",
        "weekly_template_source": str(effective_weekly_template.get("source") or "missing").strip()
        or "missing",
    }


def get_user_dingtalk_mcp_config_summary(user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    user = get_user_by_id(normalized_user_id)
    if not user:
        user = {"user_id": normalized_user_id}
    return build_user_dingtalk_mcp_config_summary(user)


def get_effective_dingtalk_mcp_config(user_id: str | None = None) -> dict:
    user_config = get_user_dingtalk_mcp_config(user_id=user_id)
    log_mcp_url = str(user_config.get("log_mcp_url") or "").strip()
    directory_mcp_url = str(user_config.get("directory_mcp_url") or "").strip()
    return {
        "user_id": str(user_config.get("user_id") or "").strip(),
        "log_mcp_url": log_mcp_url,
        "directory_mcp_url": directory_mcp_url,
        "log_mcp_source": "user" if user_config.get("uses_custom_log_mcp") else "missing",
        "directory_mcp_source": "user" if user_config.get("uses_custom_directory_mcp") else "missing",
        "updated_at": str(user_config.get("updated_at") or "").strip(),
    }


def require_dingtalk_mcp_config(
    user_id: str | None = None,
    *,
    include_log: bool = False,
    include_directory: bool = False,
) -> dict:
    effective_config = get_effective_dingtalk_mcp_config(user_id=user_id)
    if include_log and not str(effective_config.get("log_mcp_url") or "").strip():
        raise RuntimeError(DINGTALK_LOG_MCP_REQUIRED_ERROR)
    if include_directory and not str(effective_config.get("directory_mcp_url") or "").strip():
        raise RuntimeError(DINGTALK_DIRECTORY_MCP_REQUIRED_ERROR)
    return effective_config


def build_codex_config_override(key: str, value: object) -> str:
    return f"{str(key).strip()}={json.dumps(str(value or ''), ensure_ascii=False)}"


def build_dingtalk_mcp_extra_config(
    user_id: str | None = None,
    *,
    include_log: bool = False,
    include_directory: bool = False,
) -> list[str]:
    effective_config = require_dingtalk_mcp_config(
        user_id=user_id,
        include_log=include_log,
        include_directory=include_directory,
    )
    extra_config: list[str] = []
    if include_log and str(effective_config.get("log_mcp_url") or "").strip():
        extra_config.append(
            build_codex_config_override(
                "mcp_servers.dingtalk-log.url",
                effective_config["log_mcp_url"],
            )
        )
    if include_directory and str(effective_config.get("directory_mcp_url") or "").strip():
        extra_config.append(
            build_codex_config_override(
                "mcp_servers.dingtalk-directory.url",
                effective_config["directory_mcp_url"],
            )
        )
    return extra_config


def build_dingtalk_report_template_list_prompt() -> str:
    success_format = {
        "ok": True,
        "templates": [
            {
                "template_id": "模板ID",
                "template_name": "模板名称",
                "fields": [
                    {
                        "field_name": "字段名称",
                        "field_sort": 0,
                        "field_type": 1,
                    }
                ],
            }
        ],
    }
    error_format = {
        "ok": False,
        "error": "失败原因",
        "templates": [],
    }
    return "\n".join(
        [
            "你是一个钉钉日志模板读取助手。",
            "",
            "任务目标：",
            "1. 先调用一次 `get_available_report_templates`，读取当前 MCP 可以看到的所有日志模板。",
            "2. 再针对每一个可见模板，按模板名称调用 `get_template_details_by_name` 获取字段详情。",
            "3. 最终只输出一个 JSON 对象，不要输出任何额外解释、前言或 markdown 代码块。",
            "",
            "严格要求：",
            "1. `get_available_report_templates` 只能调用一次。",
            "2. `get_template_details_by_name` 必须使用模板名称参数 `report_template_name`。",
            "3. 输出里的 `template_id`、`template_name`、`fields.field_name`、`fields.field_sort`、`fields.field_type` 必须严格来自工具返回结果，不要自行猜测或补字段。",
            "4. 如果读取成功，输出格式必须类似：",
            json.dumps(success_format, ensure_ascii=False, indent=2),
            "5. 如果读取失败，输出格式必须类似：",
            json.dumps(error_format, ensure_ascii=False, indent=2),
        ]
    )


def list_user_available_dingtalk_report_templates(user_id: str | None = None) -> list[dict]:
    result = parse_codex_json_output(
        run_codex_action_prompt(
            build_dingtalk_report_template_list_prompt(),
            extra_config=build_dingtalk_mcp_extra_config(user_id=user_id, include_log=True),
        )
    )
    if result.get("ok") is False or result.get("success") is False:
        raise RuntimeError(str(result.get("error") or result.get("message") or "读取钉钉日志模板失败。"))

    templates: list[dict] = []
    seen: set[str] = set()
    for item in result.get("templates", []):
        normalized = annotate_dingtalk_template_support(item)
        identity = str(normalized.get("template_id") or normalized.get("template_name") or "").strip()
        if not identity or identity in seen:
            continue
        seen.add(identity)
        templates.append(normalized)
    templates.sort(
        key=lambda item: (
            0 if item.get("daily_supported") or item.get("weekly_supported") else 1,
            str(item.get("template_name") or item.get("template_id") or ""),
        )
    )
    return templates


def validate_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def validate_month(value: str) -> str:
    datetime.strptime(value, "%Y-%m")
    return value


def normalize_item(raw_item: dict) -> dict:
    return {
        "customer_name": str(raw_item.get("customer_name", "")).strip(),
        "project_type": str(raw_item.get("project_type", "")).strip(),
        "sales": str(raw_item.get("sales", "")).strip(),
        "item_type": str(raw_item.get("item_type", "")).strip(),
        "service_mode": str(raw_item.get("service_mode", "")).strip(),
        "work_hours": format_hours(raw_item.get("work_hours", "")),
        "work_content": str(raw_item.get("work_content", "")).strip(),
        "pending_issues": str(raw_item.get("pending_issues", raw_item.get("notes", ""))).strip(),
        "risk": str(raw_item.get("risk", "")).strip(),
    }


def format_hours(value: object) -> str:
    if value in (None, ""):
        return ""
    number = float(value)
    if number < 0:
        raise ValueError("工时不能小于 0。")
    doubled = round(number * 2)
    if abs(number * 2 - doubled) > 1e-9:
        raise ValueError("工时仅支持输入整数或 0.5。")
    if number.is_integer():
        return str(int(number))
    return (f"{number:.2f}").rstrip("0").rstrip(".")


def parse_items(items_json: str, fallback_row: sqlite3.Row | None = None) -> list[dict]:
    try:
        items = json.loads(items_json or "[]")
    except json.JSONDecodeError:
        items = []

    if isinstance(items, list) and items:
        return [normalize_item(item if isinstance(item, dict) else {}) for item in items]

    if fallback_row is not None:
        plan_content = str(fallback_row["plan_content"] or "").strip()
        notes = str(fallback_row["notes"] or "").strip()
        if plan_content or notes:
            return [
                {
                    "customer_name": "旧记录",
                    "project_type": "",
                    "sales": "",
                    "item_type": "历史数据",
                    "service_mode": "",
                    "work_hours": "",
                    "work_content": plan_content,
                    "pending_issues": notes,
                    "risk": "",
                }
            ]

    return []


def total_hours(items: list[dict]) -> str:
    total = 0.0
    for item in items:
        value = item.get("work_hours", "")
        if value not in (None, ""):
            total += float(value)
    if total.is_integer():
        return str(int(total))
    return (f"{total:.2f}").rstrip("0").rstrip(".")


def normalize_entry(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    items = parse_items(row["items_json"], row)
    return {
        "work_date": row["work_date"],
        "items": items,
        "item_count": len(items),
        "total_hours": total_hours(items),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def fetch_entry(work_date: str, user_id: str | None = None) -> dict | None:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            WHERE user_id = ? AND work_date = ?
            """,
            (normalized_user_id, work_date),
        ).fetchone()
    return normalize_entry(row)


def fetch_recent_entries(
    limit: int | None = None, anchor_date: str | None = None, user_id: str | None = None
) -> list[dict]:
    target_date = validate_date(anchor_date or date.today().isoformat())
    entries = list(reversed(fetch_week_entries(target_date, user_id=user_id)))
    if limit is None:
        return entries
    return entries[: max(0, int(limit))]


def fetch_customer_names(user_id: str | None = None) -> list[str]:
    return fetch_customer_directory(user_id=user_id)["customer_names"]


def fetch_customer_directory(user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT items_json, plan_content, notes
            FROM daily_entries
            WHERE user_id = ?
            ORDER BY work_date DESC, updated_at DESC
            """,
            (normalized_user_id,),
        ).fetchall()

    seen: set[str] = set()
    customer_names: list[str] = []
    customer_profiles: dict[str, list[dict]] = {}
    for row in rows:
        for item in parse_items(row["items_json"], row):
            customer_name = str(item.get("customer_name", "")).strip()
            normalized = customer_name.casefold()
            if not customer_name or normalized in seen or customer_name == "旧记录":
                if not customer_name or customer_name == "旧记录":
                    continue
            if normalized not in customer_profiles:
                customer_profiles[normalized] = []
            if normalized not in seen:
                seen.add(normalized)
                customer_names.append(customer_name)

            project_type = str(item.get("project_type", "")).strip()
            sales = str(item.get("sales", "")).strip()
            item_type = str(item.get("item_type", "")).strip()
            if not project_type and not sales and not item_type:
                continue
            profile_key = f"{project_type}\u0000{sales}\u0000{item_type}"
            existing_keys = {
                f"{profile.get('project_type', '')}\u0000{profile.get('sales', '')}\u0000{profile.get('item_type', '')}"
                for profile in customer_profiles[normalized]
            }
            if profile_key in existing_keys:
                continue
            customer_profiles[normalized].append(
                {
                    "customer_name": customer_name,
                    "project_type": project_type,
                    "sales": sales,
                    "item_type": item_type,
                }
            )
    return {
        "customer_names": customer_names,
        "customer_profiles": customer_profiles,
    }


def build_week_window(anchor_date: str) -> tuple[str, str, list[str]]:
    week_start = get_week_start(anchor_date)
    week_start_date = datetime.strptime(week_start, "%Y-%m-%d")
    week_dates = [(week_start_date + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(7)]
    return week_start, week_dates[-1], week_dates


def fetch_week_entries(anchor_date: str, user_id: str | None = None) -> list[dict]:
    normalized_user_id = normalize_user_id(user_id)
    week_start, _, week_dates = build_week_window(anchor_date)
    next_week_start = (
        datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=len(week_dates))
    ).strftime("%Y-%m-%d")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            WHERE user_id = ? AND work_date >= ? AND work_date < ?
            ORDER BY work_date ASC
            """,
            (normalized_user_id, week_start, next_week_start),
        ).fetchall()
    return [normalize_entry(row) for row in rows]


def fetch_month_entries(month: str, user_id: str | None = None) -> list[dict]:
    normalized_user_id = normalize_user_id(user_id)
    month = validate_month(month)
    month_start = f"{month}-01"
    if month.endswith("-12"):
        next_month = f"{int(month[:4]) + 1}-01"
    else:
        year, month_number = month.split("-")
        next_month = f"{year}-{int(month_number) + 1:02d}"
    next_month_start = f"{next_month}-01"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            WHERE user_id = ? AND work_date >= ? AND work_date < ?
            ORDER BY work_date DESC
            """,
            (normalized_user_id, month_start, next_month_start),
        ).fetchall()
    return [normalize_entry(row) for row in rows]


def build_month_stats(entries: list[dict]) -> dict:
    item_count = sum(entry["item_count"] for entry in entries)
    total = sum((float(entry["total_hours"] or 0) for entry in entries), 0.0)
    if total.is_integer():
        hours = str(int(total))
    else:
        hours = (f"{total:.2f}").rstrip("0").rstrip(".")
    return {
        "total_days": len(entries),
        "total_items": item_count,
        "total_hours": hours,
    }


def normalize_items_payload(items: object) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("事项列表格式不正确。")

    normalized: list[dict] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        item = normalize_item(raw_item)
        if not any(item.values()):
            continue
        if not item["customer_name"]:
            raise ValueError("每条事项都需要填写客户名称。")
        if not item["work_content"]:
            raise ValueError("每条事项都需要填写工作内容。")
        normalized.append(item)

    if not normalized:
        raise ValueError("请至少填写一条有效事项。")
    return normalized


def upsert_entry(payload: dict, user_id: str | None = None) -> dict:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    work_date = validate_date(str(payload.get("work_date", "")).strip())
    items = normalize_items_payload(payload.get("items", []))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items_json = json.dumps(items, ensure_ascii=False)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO daily_entries (
                user_id, work_date, plan_content, notes, created_at, updated_at, items_json
            )
            VALUES (?, ?, '', '', ?, ?, ?)
            ON CONFLICT(user_id, work_date) DO UPDATE SET
                items_json = excluded.items_json,
                updated_at = excluded.updated_at
            """,
            (normalized_user_id, work_date, timestamp, timestamp, items_json),
        )
    return fetch_entry(work_date, user_id=normalized_user_id)


def delete_entry(work_date: str, user_id: str | None = None) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    work_date = validate_date(work_date)
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM daily_entries WHERE user_id = ? AND work_date = ?",
            (normalized_user_id, work_date),
        )
    return cursor.rowcount > 0


def xml_cell(reference: str, value: str) -> str:
    safe_value = escape(value or "")
    return (
        f'<c r="{reference}" t="inlineStr">'
        f'<is><t xml:space="preserve">{safe_value}</t></is>'
        f'</c>'
    )


# Build a small XLSX file without extra dependencies.
def build_excel_file(entries: list[dict], month: str) -> bytes:
    headers = [
        "日期",
        "客户名称",
        "项目类型",
        "销售",
        "类型",
        "服务方式",
        "工时",
        "工作内容",
        "遗留事项",
        "存在风险",
        "创建时间",
        "更新时间",
    ]
    rows = [headers]
    for entry in reversed(entries):
        for item in entry["items"]:
            rows.append(
                [
                    entry["work_date"],
                    item["customer_name"],
                    item["project_type"],
                    item["sales"],
                    item["item_type"],
                    item["service_mode"],
                    item["work_hours"],
                    item["work_content"],
                    item["pending_issues"],
                    item["risk"],
                    entry["created_at"],
                    entry["updated_at"],
                ]
            )

    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            column_name = ""
            current = col_index
            while current:
                current, remainder = divmod(current - 1, 26)
                column_name = chr(65 + remainder) + column_name
            cells.append(xml_cell(f"{column_name}{row_index}", value))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="20"/>
  <cols>
    <col min="1" max="1" width="14" customWidth="1"/>
    <col min="2" max="4" width="18" customWidth="1"/>
    <col min="5" max="5" width="12" customWidth="1"/>
    <col min="6" max="8" width="34" customWidth="1"/>
    <col min="9" max="11" width="22" customWidth="1"/>
  </cols>
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>
"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="月度工作台账" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

    root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{escape(month)} 工作台账导出</dc:title>
  <dc:creator>Codex Daily Planner</dc:creator>
  <cp:lastModifiedBy>Codex Daily Planner</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:modified>
</cp:coreProperties>
"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Excel</Application>
</Properties>
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/styles.xml", styles_xml)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return buffer.getvalue()


def build_daily_log_context(work_date: str, user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    target_date = validate_date(work_date)
    today_entry = fetch_entry(target_date, user_id=normalized_user_id)
    if not today_entry:
        raise ValueError("该日期没有可导出的记录。")

    tomorrow_date = (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_entry = fetch_entry(tomorrow_date, user_id=normalized_user_id)
    tomorrow_week_start, tomorrow_weekly_settings, tomorrow_weekly_updated_at = get_weekly_plan_settings(
        tomorrow_date, user_id=normalized_user_id
    )
    return {
        "work_date": target_date,
        "today": enrich_entry_for_log(today_entry),
        "tomorrow_date": tomorrow_date,
        "tomorrow": enrich_entry_for_log(tomorrow_entry),
        "tomorrow_weekly_plan": build_weekly_day_plan_for_log(
            tomorrow_date,
            tomorrow_week_start,
            tomorrow_weekly_settings,
            tomorrow_weekly_updated_at,
        ),
    }


def classify_service_type_for_log(item_type: str) -> str:
    normalized = str(item_type or "").strip()
    if not normalized:
        return ""

    lowered = normalized.lower()
    if "交付" in normalized:
        return "交付客户"
    if "服务" in normalized:
        return "服务客户"
    if "poc" in lowered:
        return "POC客户"
    if "方案" in normalized:
        return "方案类客户"
    if "基建" in normalized:
        return "基建类工作"
    return f"{normalized}类事项"


def enrich_entry_for_log(entry: dict | None) -> dict | None:
    if not entry:
        return None

    items: list[dict] = []
    for item in entry.get("items", []):
        enriched_item = dict(item)
        enriched_item["service_type_label"] = classify_service_type_for_log(enriched_item.get("item_type", ""))
        items.append(enriched_item)

    enriched_entry = dict(entry)
    enriched_entry["items"] = items
    return enriched_entry


def build_weekly_day_plan_for_log(
    target_date: str,
    week_start: str,
    settings: dict | None,
    updated_at: str,
) -> dict:
    normalized_settings = normalize_weekly_plan_settings(settings)
    target = datetime.strptime(validate_date(target_date), "%Y-%m-%d")
    day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_key = day_keys[target.weekday()]
    return {
        "week_start": week_start,
        "target_date": target_date,
        "day_name": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target.weekday()],
        "am": normalized_settings.get(f"weekly_{day_key}_am", ""),
        "pm": normalized_settings.get(f"weekly_{day_key}_pm", ""),
        "other_pending": normalized_settings.get("weekly_other_pending", ""),
        "updated_at": updated_at,
    }


def build_weekly_plan_overview_for_report(week_start: str, settings: dict | None, updated_at: str) -> dict:
    normalized_settings = normalize_weekly_plan_settings(settings)
    ordered_days = [
        ("周一", "monday"),
        ("周二", "tuesday"),
        ("周三", "wednesday"),
        ("周四", "thursday"),
        ("周五", "friday"),
        ("周六", "saturday"),
        ("周日", "sunday"),
    ]
    day_plans = []
    for day_name, day_key in ordered_days:
        day_plans.append(
            {
                "day_name": day_name,
                "am": normalized_settings.get(f"weekly_{day_key}_am", ""),
                "pm": normalized_settings.get(f"weekly_{day_key}_pm", ""),
            }
        )
    return {
        "week_start": week_start,
        "other_pending": normalized_settings.get("weekly_other_pending", ""),
        "updated_at": updated_at,
        "days": day_plans,
    }


def classify_item_type_for_weekly_strength(item_type: str) -> str:
    normalized = str(item_type or "").strip()
    lowered = normalized.lower()
    if "poc" in lowered:
        return "POC"
    if "交付" in normalized:
        return "交付"
    if "服务" in normalized:
        return "服务"
    if "基建" in normalized:
        return "基建"
    return ""


def classify_service_type_for_weekly_report(item_type: str) -> str:
    normalized = str(item_type or "").strip()
    if not normalized:
        return "未标注"
    return normalized


def classify_service_mode_for_weekly_strength(service_mode: str) -> str:
    normalized = str(service_mode or "").strip()
    if "现场" in normalized:
        return "现场"
    if "远程" in normalized:
        return "远程"
    return "未标注"


def strip_work_item_marker(text: str) -> str:
    return re.sub(r"^\s*(?:\d+\s*[、.．)\]]\s*|[-*]\s*)", "", text).strip()


def summarize_work_content_brief(work_content: str, limit: int = 4) -> list[str]:
    summaries: list[str] = []
    for raw_part in re.split(r"[\n；;。]+", str(work_content or "")):
        part = strip_work_item_marker(raw_part).strip(" ，,;；。")
        if not part:
            continue

        for separator in ("，", ",", "：", ":"):
            if separator in part:
                leading, trailing = [section.strip() for section in part.split(separator, 1)]
                if separator in {"，", ","} and leading.endswith(("后", "前", "时", "中")) and "问题" in trailing:
                    part = trailing
                    break
                if len(leading) >= 8:
                    part = leading
                break

        part = re.sub(r"\s+", " ", part).strip(" ，,;；。")
        if len(part) > 24:
            part = part[:24].rstrip(" ，,;；。") + "..."
        if not part or part in summaries:
            continue
        summaries.append(part)
        if len(summaries) >= limit:
            break
    return summaries


def extract_work_content_detail_items(work_content: str, limit: int = 4) -> list[str]:
    details: list[str] = []
    seen: set[str] = set()
    for raw_part in re.split(r"[\n；;。]+", str(work_content or "")):
        part = strip_work_item_marker(raw_part).strip(" ，,;；。")
        if not part:
            continue
        part = re.sub(r"\s+", " ", part).strip(" ，,;；。")
        if not part or part in seen:
            continue
        seen.add(part)
        details.append(part)
        if len(details) >= limit:
            break
    return details


def normalize_report_labels(values: object) -> list[str]:
    labels = sorted({str(value).strip() for value in values if str(value).strip()})
    if len(labels) > 1:
        labels = [label for label in labels if label != "未标注"] or labels
    return labels


def format_mode_hours(mode_hours: dict[str, float]) -> str:
    ordered_modes = ["远程", "现场", "未标注"]
    parts: list[str] = []
    total = 0.0
    nonzero_count = 0
    for mode in ordered_modes:
        hours = float(mode_hours.get(mode, 0) or 0)
        if hours <= 0:
            continue
        nonzero_count += 1
        total += hours
        parts.append(f"{mode} {format_hours(hours)}小时")
    if nonzero_count >= 2:
        parts.append(f"合计 {format_hours(total)}小时")
    if parts:
        return "，".join(parts)
    return "0小时"


def build_weekly_strength_context(work_date: str, user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    target_date = validate_date(work_date)
    week_start, week_end, _ = build_week_window(target_date)
    week_entries = fetch_week_entries(target_date, user_id=normalized_user_id)
    category_order = ["POC", "交付", "服务", "基建"]
    group_summary: dict[tuple[str, str], dict] = {}
    category_summary = {
        category: {"item_count": 0, "total_hours": 0.0, "customers": set()}
        for category in category_order
    }
    active_dates: set[str] = set()
    customer_names: set[str] = set()
    omitted_item_count = 0

    for entry in week_entries:
        for item in entry.get("items", []):
            category = classify_item_type_for_weekly_strength(item.get("item_type", ""))
            if not category:
                omitted_item_count += 1
                continue

            customer_name = str(item.get("customer_name", "")).strip() or "未命名客户"
            hours = float(item.get("work_hours", 0) or 0)
            service_mode = classify_service_mode_for_weekly_strength(item.get("service_mode", ""))
            work_date = str(entry.get("work_date", "")).strip()
            summaries = summarize_work_content_brief(item.get("work_content", ""))
            customer_names.add(customer_name)
            group = group_summary.setdefault(
                (customer_name, service_mode),
                {
                    "customer_name": customer_name,
                    "service_mode": service_mode,
                    "category_hours": {name: 0.0 for name in category_order},
                    "category_item_counts": {name: 0 for name in category_order},
                    "category_summaries": {name: [] for name in category_order},
                    "total_hours": 0.0,
                    "dates": set(),
                },
            )
            group["total_hours"] += hours
            group["dates"].add(work_date)
            group["category_item_counts"][category] += 1
            group["category_hours"][category] += hours
            for summary in summaries:
                if summary not in group["category_summaries"][category]:
                    group["category_summaries"][category].append(summary)

            category_summary[category]["item_count"] += 1
            category_summary[category]["total_hours"] += hours
            category_summary[category]["customers"].add(customer_name)
            active_dates.add(work_date)

    if not group_summary:
        raise ValueError("该周没有可统计的 POC、交付、服务、基建记录。")

    customer_service_groups = sorted(
        (
            {
                "customer_name": group["customer_name"],
                "service_mode": group["service_mode"],
                "total_hours": format_hours(group["total_hours"]),
                "dates": sorted(date_value for date_value in group["dates"] if date_value),
                "category_hours": {
                    category: format_hours(group["category_hours"][category])
                    for category in category_order
                },
                "category_item_counts": dict(group["category_item_counts"]),
                "category_summaries": {
                    category: group["category_summaries"][category][:4]
                    for category in category_order
                },
            }
            for group in group_summary.values()
        ),
        key=lambda item: (-float(item["total_hours"] or 0), item["customer_name"], item["service_mode"]),
    )

    categories = {
        category: {
            "item_count": category_summary[category]["item_count"],
            "total_hours": format_hours(category_summary[category]["total_hours"]),
            "customer_count": len(category_summary[category]["customers"]),
        }
        for category in category_order
    }

    return {
        "anchor_date": target_date,
        "week_start": week_start,
        "week_end": week_end,
        "active_days": len(active_dates),
        "customer_count": len(customer_names),
        "group_count": len(customer_service_groups),
        "categories": categories,
        "customer_service_groups": customer_service_groups,
        "omitted_item_count": omitted_item_count,
    }


def build_weekly_delivery_progress_context(work_date: str, user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    target_date = validate_date(work_date)
    week_start, week_end, _ = build_week_window(target_date)
    week_entries = fetch_week_entries(target_date, user_id=normalized_user_id)
    projects: dict[str, dict] = {}

    for entry in week_entries:
        work_date_value = str(entry.get("work_date", "")).strip()
        for item in entry.get("items", []):
            if classify_item_type_for_weekly_strength(item.get("item_type", "")) != "交付":
                continue

            project_name = str(item.get("customer_name", "")).strip() or "未命名项目"
            service_mode = str(item.get("service_mode", "")).strip() or "未标注"
            work_hours = float(item.get("work_hours", 0) or 0)
            work_content = str(item.get("work_content", "")).strip()
            pending_issues = str(item.get("pending_issues", "")).strip()
            risk = str(item.get("risk", "")).strip()

            project = projects.setdefault(
                project_name,
                {
                    "project_name": project_name,
                    "service_modes": set(),
                    "dates": set(),
                    "total_hours": 0.0,
                    "items": [],
                    "pending_items": [],
                    "risk_items": [],
                },
            )
            project["service_modes"].add(service_mode)
            project["dates"].add(work_date_value)
            project["total_hours"] += work_hours
            project["items"].append(
                {
                    "work_date": work_date_value,
                    "service_mode": service_mode,
                    "work_hours": format_hours(work_hours),
                    "work_content": work_content,
                    "work_summary": summarize_work_content_brief(work_content, limit=3),
                    "pending_issues": pending_issues,
                    "risk": risk,
                }
            )
            if pending_issues:
                project["pending_items"].append(
                    {
                        "work_date": work_date_value,
                        "content": pending_issues,
                    }
                )
            if risk:
                project["risk_items"].append(
                    {
                        "work_date": work_date_value,
                        "content": risk,
                    }
                )

    if not projects:
        raise ValueError("该周没有可分析的交付项目。")

    ordered_projects = sorted(
        (
            {
                "project_name": project["project_name"],
                "service_modes": sorted(project["service_modes"]),
                "dates": sorted(project["dates"]),
                "total_hours": format_hours(project["total_hours"]),
                "items": project["items"],
                "pending_items": project["pending_items"],
                "risk_items": project["risk_items"],
            }
            for project in projects.values()
        ),
        key=lambda item: (-float(item["total_hours"] or 0), item["project_name"]),
    )
    return {
        "anchor_date": target_date,
        "week_start": week_start,
        "week_end": week_end,
        "project_count": len(ordered_projects),
        "projects": ordered_projects,
    }


def build_weekly_delivery_progress_cache_key(week_start: str, user_id: str | None = None) -> str:
    normalized_user_id = normalize_user_id(user_id)
    return f"user:{normalized_user_id}:delivery_progress::{validate_date(week_start)}"


def get_cached_weekly_delivery_progress(week_start: str, user_id: str | None = None) -> tuple[dict | None, str]:
    cache_key = build_weekly_delivery_progress_cache_key(week_start, user_id=user_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (cache_key,),
        ).fetchone()
    if not row:
        return None, ""
    try:
        payload = json.loads(row["setting_value"] or "{}")
    except json.JSONDecodeError:
        return None, ""
    if not isinstance(payload, dict):
        return None, ""
    return payload, str(row["updated_at"] or "")


def save_weekly_delivery_progress_cache(week_start: str, payload: dict, user_id: str | None = None) -> str:
    cache_key = build_weekly_delivery_progress_cache_key(week_start, user_id=user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (cache_key, json.dumps(payload, ensure_ascii=False), timestamp),
        )
    return timestamp


def load_prompt_template(filename: str, user_id: str | None = None) -> str:
    override_content, _ = get_user_prompt_template_override(filename, user_id=user_id)
    if override_content is not None:
        return override_content
    return load_default_prompt_template(filename)


def render_prompt_template(filename: str, *, user_id: str | None = None, **values: object) -> str:
    template = load_prompt_template(filename, user_id=user_id)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise RuntimeError(f"AI 提示词文件 {filename} 缺少占位符参数：{key}")
        return str(values[key])

    rendered = PROMPT_PLACEHOLDER_PATTERN.sub(replace, template)
    unresolved = sorted(set(PROMPT_PLACEHOLDER_PATTERN.findall(rendered)))
    if unresolved:
        missing = ", ".join(unresolved)
        raise RuntimeError(f"AI 提示词文件 {filename} 存在未替换占位符：{missing}")
    return rendered


def build_weekly_delivery_progress_prompt(context: dict, user_id: str | None = None) -> str:
    return render_prompt_template(
        "weekly/delivery_progress_analysis.txt",
        user_id=user_id,
        context_json=json.dumps(context, ensure_ascii=False, indent=2),
    )


def parse_codex_json_output(raw_text: str) -> dict:
    text = str(raw_text or "").strip()
    if not text:
        raise RuntimeError("codex 没有返回内容。")

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.S)
    if fenced_match:
        text = fenced_match.group(1).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError("codex 返回的内容不是合法 JSON。")
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError as error:
            raise RuntimeError("codex 返回的 JSON 无法解析。") from error

    if not isinstance(payload, dict):
        raise RuntimeError("codex 返回的 JSON 结构不正确。")
    return payload


def infer_delivery_report_status(project: dict) -> str:
    if project.get("risk_items"):
        return "黄灯"
    if project.get("pending_items"):
        return "黄灯"
    return "绿灯"


def fallback_delivery_report(project: dict) -> dict:
    weekly_work: list[str] = []
    for item in project.get("items", []):
        work_bits = item.get("work_summary") or summarize_work_content_brief(item.get("work_content", ""), limit=2)
        if not work_bits:
            continue
        weekly_work.append(f"{item.get('work_date', '')}：{'、'.join(work_bits)}")
        if len(weekly_work) >= 4:
            break

    pending_items = [
        f"{entry.get('work_date', '')}：{str(entry.get('content', '')).strip()}"
        for entry in project.get("pending_items", [])[:3]
        if str(entry.get("content", "")).strip()
    ] or ["暂无"]
    risk_items = [
        f"{entry.get('work_date', '')}：{str(entry.get('content', '')).strip()}"
        for entry in project.get("risk_items", [])[:3]
        if str(entry.get("content", "")).strip()
    ] or ["暂无"]

    summary = (
        f"本周围绕{project['project_name']}项目持续推进交付事项，累计投入{project['total_hours']}小时，"
        f"主要聚焦测试验证、环境处理与业务沟通。"
    )
    return {
        "project_name": project["project_name"],
        "overall_status": infer_delivery_report_status(project),
        "summary": summary,
        "weekly_work": weekly_work or ["本周已推进交付相关工作。"],
        "risks": risk_items,
        "pending_items": pending_items,
        "next_actions": pending_items if pending_items != ["暂无"] else ["持续跟进项目推进情况。"],
    }


def normalize_delivery_progress_response(context: dict, payload: dict) -> dict:
    project_map = {project["project_name"]: project for project in context["projects"]}
    raw_reports = payload.get("reports", []) if isinstance(payload, dict) else []
    normalized_reports_by_name: dict[str, dict] = {}

    if isinstance(raw_reports, list):
        for report in raw_reports:
            if not isinstance(report, dict):
                continue
            project_name = str(report.get("project_name", "")).strip()
            if not project_name or project_name not in project_map:
                continue

            def normalize_list(value: object, fallback: list[str]) -> list[str]:
                if not isinstance(value, list):
                    return fallback
                items = [str(item).strip() for item in value if str(item).strip()]
                return items or fallback

            status = str(report.get("overall_status", "")).strip()
            if status not in {"绿灯", "黄灯", "红灯"}:
                status = infer_delivery_report_status(project_map[project_name])
            normalized_reports_by_name[project_name] = {
                "project_name": project_name,
                "overall_status": status,
                "summary": str(report.get("summary", "")).strip() or fallback_delivery_report(project_map[project_name])["summary"],
                "weekly_work": normalize_list(report.get("weekly_work"), ["暂无"]),
                "risks": normalize_list(report.get("risks"), ["暂无"]),
                "pending_items": normalize_list(report.get("pending_items"), ["暂无"]),
                "next_actions": normalize_list(report.get("next_actions"), ["持续跟进"]),
            }

    reports = []
    for project in context["projects"]:
        report = normalized_reports_by_name.get(project["project_name"], fallback_delivery_report(project))
        report["service_modes"] = project["service_modes"]
        report["dates"] = project["dates"]
        report["total_hours"] = project["total_hours"]
        reports.append(report)

    return {
        "week_start": context["week_start"],
        "week_end": context["week_end"],
        "anchor_date": str(payload.get("anchor_date", "")).strip() or context["anchor_date"],
        "project_count": context["project_count"],
        "reports": reports,
    }


def build_codex_log_prompt(context: dict, user_id: str | None = None) -> str:
    return render_prompt_template(
        "daily/log_generation.txt",
        user_id=user_id,
        context_json=json.dumps(context, ensure_ascii=False, indent=2),
    )


def build_weekly_strength_summary_lines(context: dict) -> list[str]:
    categories = context["categories"]
    return [
        "1、本周兵力盘点：",
        f"1. 统计周期：{context['week_start']} 至 {context['week_end']}。",
        (
            f"2. 分类汇总：POC {categories['POC']['item_count']}项 / {categories['POC']['total_hours']}小时，"
            f"交付 {categories['交付']['item_count']}项 / {categories['交付']['total_hours']}小时，"
            f"服务 {categories['服务']['item_count']}项 / {categories['服务']['total_hours']}小时，"
            f"基建 {categories['基建']['item_count']}项 / {categories['基建']['total_hours']}小时。"
        ),
        f"3. 活跃工作日：{context['active_days']}天；覆盖客户：{context['customer_count']}个。",
        "",
        "2、客户维度工作表：",
    ]

def build_weekly_strength_table_rows(context: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for group in context["customer_service_groups"]:
        for category in ["POC", "交付", "服务", "基建"]:
            if int(group["category_item_counts"].get(category, 0) or 0) <= 0:
                continue
            summaries = group["category_summaries"].get(category, [])
            rows.append(
                [
                    group["customer_name"],
                    group["service_mode"],
                    category,
                    str(group["category_hours"].get(category, "0")),
                    "；".join(summaries) if summaries else "无具体描述",
                ]
            )
    return rows


def get_weekly_strength_table_headers() -> list[str]:
    return ["客户", "服务方式", "类型", "工时", "工作摘要"]


def build_weekly_strength_footer_lines(context: dict) -> list[str]:
    categories = context["categories"]
    lines = [
        "",
        "3、按类型汇总：",
        f"1. POC：{categories['POC']['customer_count']}个客户，{categories['POC']['item_count']}项，{categories['POC']['total_hours']}小时。",
        f"2. 交付：{categories['交付']['customer_count']}个客户，{categories['交付']['item_count']}项，{categories['交付']['total_hours']}小时。",
        f"3. 服务：{categories['服务']['customer_count']}个客户，{categories['服务']['item_count']}项，{categories['服务']['total_hours']}小时。",
        f"4. 基建：{categories['基建']['customer_count']}个客户，{categories['基建']['item_count']}项，{categories['基建']['total_hours']}小时。",
    ]
    if context["omitted_item_count"] > 0:
        lines.extend(
            [
                "",
                "4、说明：",
                f"1. 未纳入本次盘点的事项共 {context['omitted_item_count']} 条，主要为方案或未标注类型。",
            ]
        )
    return lines


def build_weekly_strength_excel_file(context: dict) -> bytes:
    rows = [
        ["统计周期", f"{context['week_start']} 至 {context['week_end']}"],
        [
            "分类汇总",
            (
                f"POC {context['categories']['POC']['item_count']}项 / {context['categories']['POC']['total_hours']}小时；"
                f"交付 {context['categories']['交付']['item_count']}项 / {context['categories']['交付']['total_hours']}小时；"
                f"服务 {context['categories']['服务']['item_count']}项 / {context['categories']['服务']['total_hours']}小时；"
                f"基建 {context['categories']['基建']['item_count']}项 / {context['categories']['基建']['total_hours']}小时"
            ),
        ],
        ["活跃工作日", str(context["active_days"])],
        ["覆盖客户", str(context["customer_count"])],
        ["统计分组", str(context["group_count"])],
        [],
        get_weekly_strength_table_headers(),
    ]
    rows.extend(build_weekly_strength_table_rows(context))
    rows.append([])
    rows.extend(
        [
            ["类型汇总", "客户数", "事项数", "总工时"],
            ["POC", str(context["categories"]["POC"]["customer_count"]), str(context["categories"]["POC"]["item_count"]), str(context["categories"]["POC"]["total_hours"])],
            ["交付", str(context["categories"]["交付"]["customer_count"]), str(context["categories"]["交付"]["item_count"]), str(context["categories"]["交付"]["total_hours"])],
            ["服务", str(context["categories"]["服务"]["customer_count"]), str(context["categories"]["服务"]["item_count"]), str(context["categories"]["服务"]["total_hours"])],
            ["基建", str(context["categories"]["基建"]["customer_count"]), str(context["categories"]["基建"]["item_count"]), str(context["categories"]["基建"]["total_hours"])],
        ]
    )
    if context["omitted_item_count"] > 0:
        rows.append([])
        rows.append(["说明", f"未纳入本次盘点的事项共 {context['omitted_item_count']} 条，主要为方案或未标注类型。"])

    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            column_name = ""
            current = col_index
            while current:
                current, remainder = divmod(current - 1, 26)
                column_name = chr(65 + remainder) + column_name
            cells.append(xml_cell(f"{column_name}{row_index}", str(value) if value is not None else ""))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="20"/>
  <cols>
    <col min="1" max="1" width="16" customWidth="1"/>
    <col min="2" max="2" width="12" customWidth="1"/>
    <col min="3" max="4" width="12" customWidth="1"/>
    <col min="5" max="5" width="52" customWidth="1"/>
  </cols>
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>
"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="本周兵力盘点" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

    root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    title = f"{context['week_start']} 至 {context['week_end']} 本周兵力盘点"
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{escape(title)}</dc:title>
  <dc:creator>Codex Daily Planner</dc:creator>
  <cp:lastModifiedBy>Codex Daily Planner</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:modified>
</cp:coreProperties>
"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Excel</Application>
</Properties>
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/styles.xml", styles_xml)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return buffer.getvalue()


def build_word_paragraph_xml(line: str, *, bold: bool | None = None, font_size: int | None = None) -> str:
    normalized_line = line.replace("\t", "    ")
    if not normalized_line.strip():
        return "<w:p/>"

    text = escape(normalized_line)
    preserve_space = ' xml:space="preserve"' if normalized_line != normalized_line.strip() or "  " in normalized_line else ""
    is_heading = re.match(r"^\d+、.+：$", normalized_line.strip()) is not None if bold is None else bold
    size_value = 28 if is_heading else 24
    if font_size is not None:
        size_value = font_size
    bold_xml = "<w:b/>" if is_heading else ""
    run_props = f"<w:rPr>{bold_xml}<w:sz w:val=\"{size_value}\"/></w:rPr>"
    return f"<w:p><w:r>{run_props}<w:t{preserve_space}>{text}</w:t></w:r></w:p>"


def build_word_package(body_xml: str, title: str) -> bytes:
    created_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    safe_title = escape(title)
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Daily Planner</Application>
</Properties>
"""
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{safe_title}</dc:title>
  <dc:creator>Codex Daily Planner</dc:creator>
  <cp:lastModifiedBy>Codex Daily Planner</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created_at}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created_at}</dcterms:modified>
</cp:coreProperties>
"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei" w:cs="Calibri"/>
        <w:sz w:val="24"/>
        <w:lang w:val="zh-CN" w:eastAsia="zh-CN"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>
"""
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body_xml}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
    return buffer.getvalue()


def build_word_document(content: str, title: str) -> bytes:
    paragraphs_xml = "".join(build_word_paragraph_xml(line) for line in content.splitlines())
    return build_word_package(paragraphs_xml, title)


def build_word_table_xml(headers: list[str], rows: list[list[str]], column_widths: list[int] | None = None) -> str:
    widths = column_widths or [1900, 1100, 1100, 1100, 1100, 4500]
    if len(widths) != len(headers):
        raise ValueError("表格列宽数量与表头数量不一致。")

    def build_table_cell_xml(text: str, width: int, *, is_header: bool = False) -> str:
        escaped_text = escape(str(text or ""))
        preserve_space = ' xml:space="preserve"' if "  " in str(text or "") else ""
        shading_xml = '<w:shd w:val="clear" w:color="auto" w:fill="DCEAF8"/>' if is_header else ""
        bold_xml = "<w:b/>" if is_header else ""
        font_size = 22 if is_header else 21
        return (
            f"<w:tc>"
            f"<w:tcPr><w:tcW w:w=\"{width}\" w:type=\"dxa\"/>{shading_xml}</w:tcPr>"
            f"<w:p><w:r><w:rPr>{bold_xml}<w:sz w:val=\"{font_size}\"/></w:rPr>"
            f"<w:t{preserve_space}>{escaped_text}</w:t></w:r></w:p>"
            f"</w:tc>"
        )

    grid_xml = "".join(f"<w:gridCol w:w=\"{width}\"/>" for width in widths)
    header_row_xml = "<w:tr>" + "".join(
        build_table_cell_xml(header, widths[index], is_header=True) for index, header in enumerate(headers)
    ) + "</w:tr>"
    body_rows_xml = "".join(
        "<w:tr>" + "".join(build_table_cell_xml(cell, widths[index]) for index, cell in enumerate(row)) + "</w:tr>"
        for row in rows
    )
    return f"""
<w:tbl>
  <w:tblPr>
    <w:tblW w:w="10800" w:type="dxa"/>
    <w:tblLayout w:type="fixed"/>
    <w:tblBorders>
      <w:top w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:left w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:bottom w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:right w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:insideH w:val="single" w:sz="6" w:space="0" w:color="D5E1EB"/>
      <w:insideV w:val="single" w:sz="6" w:space="0" w:color="D5E1EB"/>
    </w:tblBorders>
  </w:tblPr>
  <w:tblGrid>{grid_xml}</w:tblGrid>
  {header_row_xml}
  {body_rows_xml}
</w:tbl>
"""


def build_word_table_document(
    title: str,
    intro_lines: list[str],
    headers: list[str],
    rows: list[list[str]],
    footer_lines: list[str] | None = None,
) -> bytes:
    body_parts = ["".join(build_word_paragraph_xml(line) for line in intro_lines)]
    body_parts.append(build_word_table_xml(headers, rows))
    if footer_lines:
        body_parts.append("".join(build_word_paragraph_xml(line) for line in footer_lines))
    return build_word_package("".join(body_parts), title)


def build_word_table_cell_block_xml(
    lines: list[str],
    width: int,
    *,
    is_header: bool = False,
    grid_span: int = 1,
    fill_color: str = "",
) -> str:
    effective_lines = lines or [""]
    tc_props = [f"<w:tcW w:w=\"{width}\" w:type=\"dxa\"/>"]
    if grid_span > 1:
        tc_props.append(f"<w:gridSpan w:val=\"{grid_span}\"/>")
    if fill_color:
        tc_props.append(f"<w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"{fill_color}\"/>")
    paragraphs_xml = "".join(
        build_word_paragraph_xml(
            line,
            bold=is_header,
            font_size=22 if is_header else 21,
        )
        for line in effective_lines
    )
    return f"<w:tc><w:tcPr>{''.join(tc_props)}</w:tcPr>{paragraphs_xml}</w:tc>"


def build_weekly_report_word_table_xml(context: dict, project_notes: dict[str, str]) -> str:
    headers = ["项目名称", "服务类型", "工时", "项目类型", "销售"]
    widths = [2600, 1600, 900, 1600, 1800]
    total_width = sum(widths)
    grid_xml = "".join(f"<w:gridCol w:w=\"{width}\"/>" for width in widths)
    header_row_xml = "<w:tr>" + "".join(
        build_word_table_cell_block_xml([header], widths[index], is_header=True, fill_color="DCEAF8")
        for index, header in enumerate(headers)
    ) + "</w:tr>"

    body_rows: list[str] = []
    for project in context.get("projects", []):
        project_name = str(project.get("project_name", "")).strip() or "未命名项目"
        service_types = "、".join(
            str(item).strip() for item in project.get("service_types", []) if str(item).strip()
        ) or "未标注"
        project_type = "、".join(
            str(item).strip() for item in project.get("project_types", []) if str(item).strip()
        ) or "未标注"
        sales = "、".join(
            str(item).strip() for item in project.get("sales", []) if str(item).strip()
        ) or "未标注"
        total_hours = str(project.get("total_hours", "")).strip() or "0"
        data_row_values = [project_name, service_types, total_hours, project_type, sales]
        body_rows.append(
            "<w:tr>" + "".join(
                build_word_table_cell_block_xml([value], widths[index])
                for index, value in enumerate(data_row_values)
            ) + "</w:tr>"
        )
        note_text = project_notes.get(project_name) or "暂无"
        merged_lines = ["本周工作"]
        merged_lines.extend(str(note_text).splitlines() or ["暂无"])
        body_rows.append(
            "<w:tr>"
            + build_word_table_cell_block_xml(merged_lines, total_width, grid_span=len(widths))
            + "</w:tr>"
        )

    return f"""
<w:tbl>
  <w:tblPr>
    <w:tblW w:w="10800" w:type="dxa"/>
    <w:tblLayout w:type="fixed"/>
    <w:tblBorders>
      <w:top w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:left w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:bottom w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:right w:val="single" w:sz="8" w:space="0" w:color="B7C9DA"/>
      <w:insideH w:val="single" w:sz="6" w:space="0" w:color="D5E1EB"/>
      <w:insideV w:val="single" w:sz="6" w:space="0" w:color="D5E1EB"/>
    </w:tblBorders>
  </w:tblPr>
  <w:tblGrid>{grid_xml}</w:tblGrid>
  {header_row_xml}
  {''.join(body_rows)}
</w:tbl>
"""


def build_weekly_report_word_document(context: dict, sections: list[dict], project_notes: dict[str, str]) -> bytes:
    body_parts = [
        build_word_paragraph_xml("一、本周工作", bold=True, font_size=28),
        build_weekly_report_word_table_xml(context, project_notes),
    ]
    ordered_sections = [section for section in sections if normalize_weekly_report_section_title(section.get("title", "")) != normalize_weekly_report_section_title("本周工作")]
    for index, section in enumerate(ordered_sections, start=2):
        title = str(section.get("title", "")).strip() or f"第{index}部分"
        content = str(section.get("content", "")).strip() or "暂无"
        body_parts.append("<w:p/>")
        body_parts.append(build_word_paragraph_xml(f"{index}、{title}", bold=True, font_size=28))
        body_parts.extend(build_word_paragraph_xml(line) for line in content.splitlines())
    return build_word_package("".join(body_parts), f"{context['week_start']} 至 {context['week_end']} 周报")


def generate_daily_log_via_codex(work_date: str, user_id: str | None = None) -> bytes:
    context = build_daily_log_context(work_date, user_id=user_id)
    prompt = build_codex_log_prompt(context, user_id=user_id)
    return generate_codex_document(prompt, f"{work_date} 工作日志")


def generate_weekly_strength_report_spreadsheet(work_date: str, user_id: str | None = None) -> bytes:
    context = build_weekly_strength_context(work_date, user_id=user_id)
    return build_weekly_strength_excel_file(context)


def execute_codex_prompt(
    prompt: str,
    *,
    dangerously_bypass: bool = False,
    extra_config: list[str] | None = None,
    timeout_seconds: int = 180,
) -> str:
    if not CODEX_BIN or not Path(CODEX_BIN).exists():
        raise RuntimeError("未找到 codex 命令，无法生成内容。")
    if not NODE_BIN or not Path(NODE_BIN).exists():
        raise RuntimeError("未找到 node 命令，无法调用 codex 生成内容。")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_file:
        output_path = output_file.name

    command = [
        NODE_BIN,
        CODEX_BIN,
        "exec",
    ]
    path_entries = [entry for entry in COMMAND_PATH_PREFIXES if str(entry).strip()]
    current_path = os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    if current_path:
        path_entries.append(current_path)
    subprocess_path = os.pathsep.join(dict.fromkeys(path_entries))
    if dangerously_bypass:
        command.append("--dangerously-bypass-approvals-and-sandbox")
    for config_item in extra_config or []:
        command.extend(["-c", config_item])
    command.extend(
        [
            "--skip-git-repo-check",
            "-C",
            str(BASE_DIR),
            "--sandbox",
            "danger-full-access" if dangerously_bypass else "read-only",
            "--output-last-message",
            output_path,
            prompt,
        ]
    )

    try:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=max(1, int(timeout_seconds or 180)),
                check=False,
                env={**os.environ, "PATH": subprocess_path},
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"codex 生成内容超时（>{max(1, int(timeout_seconds or 180))}秒），请稍后重试。"
            ) from error
        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(error_text or "codex 生成内容失败。")

        content = Path(output_path).read_text(encoding="utf-8").strip()
        if not content:
            raise RuntimeError("codex 没有返回内容。")
        return content
    finally:
        try:
            Path(output_path).unlink(missing_ok=True)
        except OSError:
            pass


def run_codex_prompt(prompt: str, *, timeout_seconds: int = 180) -> str:
    return execute_codex_prompt(prompt, dangerously_bypass=False, timeout_seconds=timeout_seconds)


def run_codex_action_prompt(prompt: str, *, extra_config: list[str] | None = None) -> str:
    return execute_codex_prompt(prompt, dangerously_bypass=True, extra_config=extra_config)


def run_codex_directory_prompt(prompt: str, *, extra_config: list[str] | None = None) -> str:
    return execute_codex_prompt(
        prompt,
        dangerously_bypass=True,
        extra_config=list(extra_config or []),
    )


def generate_weekly_delivery_progress_reports(
    work_date: str, force_refresh: bool = False, user_id: str | None = None
) -> dict:
    context = build_weekly_delivery_progress_context(work_date, user_id=user_id)
    if not force_refresh:
        cached_payload, cached_updated_at = get_cached_weekly_delivery_progress(context["week_start"], user_id=user_id)
        if cached_payload:
            normalized_cached = normalize_delivery_progress_response(context, cached_payload)
            normalized_cached["generated_at"] = cached_updated_at
            normalized_cached["source"] = "cache"
            return normalized_cached

    payload = parse_codex_json_output(run_codex_prompt(build_weekly_delivery_progress_prompt(context, user_id=user_id)))
    normalized_payload = normalize_delivery_progress_response(context, payload)
    generated_at = save_weekly_delivery_progress_cache(context["week_start"], normalized_payload, user_id=user_id)
    normalized_payload["generated_at"] = generated_at
    normalized_payload["source"] = "fresh"
    return normalized_payload


def load_weekly_delivery_progress_cache_only(work_date: str, user_id: str | None = None) -> dict:
    context = build_weekly_delivery_progress_context(work_date, user_id=user_id)
    cached_payload, cached_updated_at = get_cached_weekly_delivery_progress(context["week_start"], user_id=user_id)
    if not cached_payload:
        return {
            "week_start": context["week_start"],
            "week_end": context["week_end"],
            "anchor_date": context["anchor_date"],
            "cached": False,
        }
    normalized_cached = normalize_delivery_progress_response(context, cached_payload)
    normalized_cached["generated_at"] = cached_updated_at
    normalized_cached["source"] = "cache"
    normalized_cached["cached"] = True
    return normalized_cached


def build_weekly_report_context(work_date: str, user_id: str | None = None) -> dict:
    normalized_user_id = normalize_user_id(user_id)
    requested_date = validate_date(work_date)
    requested_week_start, _, _ = build_week_window(requested_date)
    candidate_dates = [requested_date]
    candidate_dates.extend(list_previous_weekly_report_candidate_dates(requested_week_start, normalized_user_id))
    last_error_message = "该周没有可生成周报的记录。"

    for candidate_date in candidate_dates:
        try:
            context = build_weekly_report_context_for_anchor(candidate_date, normalized_user_id)
        except ValueError as error:
            last_error_message = str(error)
            continue
        context["requested_anchor_date"] = requested_date
        context["requested_week_start"] = requested_week_start
        context["used_fallback_week"] = context["week_start"] != requested_week_start
        return context

    raise ValueError(last_error_message)


def list_previous_weekly_report_candidate_dates(requested_week_start: str, normalized_user_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT work_date
            FROM daily_entries
            WHERE user_id = ? AND work_date < ?
            ORDER BY work_date DESC
            LIMIT 90
            """,
            (normalized_user_id, requested_week_start),
        ).fetchall()

    candidate_dates: list[str] = []
    seen_week_starts: set[str] = set()
    for row in rows:
        candidate_date = str(row["work_date"] or "").strip()
        if not candidate_date:
            continue
        candidate_week_start = get_week_start(candidate_date)
        if candidate_week_start in seen_week_starts:
            continue
        seen_week_starts.add(candidate_week_start)
        candidate_dates.append(candidate_date)
    return candidate_dates


def build_weekly_report_context_for_anchor(anchor_date: str, normalized_user_id: str) -> dict:
    target_date = validate_date(anchor_date)
    week_start, week_end, _ = build_week_window(target_date)
    week_entries = fetch_week_entries(target_date, user_id=normalized_user_id)
    if not week_entries:
        raise ValueError("该周没有可生成周报的记录。")
    next_week_anchor = (datetime.strptime(week_end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week_start, next_week_settings, next_week_updated_at = get_weekly_plan_settings(
        next_week_anchor, user_id=normalized_user_id
    )

    projects: dict[str, dict] = {}
    total_hours = 0.0
    total_items = 0

    for entry in week_entries:
        work_date_value = str(entry.get("work_date", "")).strip()
        for item in entry.get("items", []):
            customer_name = str(item.get("customer_name", "")).strip()
            if not customer_name or customer_name == "旧记录":
                continue
            project_type = str(item.get("project_type", "")).strip() or "未标注"
            item_type = str(item.get("item_type", "")).strip() or "未标注"
            service_type = classify_service_type_for_weekly_report(item_type)
            sales = str(item.get("sales", "")).strip() or "未标注"
            work_content = str(item.get("work_content", "")).strip()
            pending_issues = str(item.get("pending_issues", "")).strip()
            risk = str(item.get("risk", "")).strip()
            work_hours = float(item.get("work_hours", 0) or 0)
            total_hours += work_hours
            total_items += 1

            project = projects.setdefault(
                customer_name,
                {
                    "project_name": customer_name,
                    "service_types": set(),
                    "project_types": set(),
                    "sales": set(),
                    "dates": set(),
                    "total_hours": 0.0,
                    "weekly_work": [],
                    "pending_items": [],
                    "risks": [],
                    "work_items": [],
                },
            )
            project["service_types"].add(service_type)
            project["project_types"].add(project_type)
            project["sales"].add(sales)
            project["dates"].add(work_date_value)
            project["total_hours"] += work_hours
            project["work_items"].append(
                {
                    "work_date": work_date_value,
                    "service_type": service_type,
                    "item_type": item_type,
                    "project_type": project_type,
                    "sales": sales,
                    "work_hours": format_hours(work_hours),
                    "work_content": work_content,
                    "pending_issues": pending_issues,
                    "risk": risk,
                }
            )
            for detail in extract_work_content_detail_items(work_content, limit=4):
                if detail not in project["weekly_work"]:
                    project["weekly_work"].append(detail)
            if pending_issues and pending_issues not in project["pending_items"]:
                project["pending_items"].append(pending_issues)
            if risk and risk not in project["risks"]:
                project["risks"].append(risk)

    if not projects:
        raise ValueError("该周没有可生成周报的有效客户事项。")

    ordered_projects = sorted(
        (
            {
                "project_name": project["project_name"],
                "service_types": normalize_report_labels(project["service_types"]),
                "project_types": normalize_report_labels(project["project_types"]),
                "sales": normalize_report_labels(project["sales"]),
                "dates": sorted(project["dates"]),
                "total_hours": format_hours(project["total_hours"]),
                "weekly_work": project["weekly_work"][:6],
                "pending_items": project["pending_items"][:4],
                "risks": project["risks"][:4],
                "work_items": project["work_items"],
            }
            for project in projects.values()
        ),
        key=lambda item: (-float(item["total_hours"] or 0), item["project_name"]),
    )
    return {
        "anchor_date": target_date,
        "week_start": week_start,
        "week_end": week_end,
        "project_count": len(ordered_projects),
        "item_count": total_items,
        "total_hours": format_hours(total_hours),
        "table_headers": ["项目名称", "服务类型", "工时", "项目类型", "销售"],
        "projects": ordered_projects,
        "next_week_plan": build_weekly_plan_overview_for_report(next_week_start, next_week_settings, next_week_updated_at),
    }


def build_weekly_report_prompt(context: dict, user_id: str | None = None) -> str:
    return render_prompt_template(
        "weekly/report_generation.txt",
        user_id=user_id,
        context_json=json.dumps(context, ensure_ascii=False, indent=2),
    )


def split_project_detail_items(values: list[object], limit: int = 3) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        for part in re.split(r"[\n；;]+", str(raw_value or "")):
            item = re.sub(r"\s+", " ", str(part or "")).strip().strip("，,;；。")
            if not item:
                continue
            key = re.sub(r"\s+", "", item)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(item)
            if len(normalized) >= limit:
                return normalized
    return normalized


def build_default_weekly_report_project_note(project: dict) -> str:
    work_item_details = []
    for item in project.get("work_items", []):
        work_item_details.extend(extract_work_content_detail_items(item.get("work_content", ""), limit=4))
    summaries = split_project_detail_items(work_item_details, limit=4)
    pending_items = split_project_detail_items(project.get("pending_items", []), limit=3)
    risks = split_project_detail_items(project.get("risks", []), limit=2)
    parts: list[str] = []
    if summaries:
        parts.append(f"本周已完成：{'；'.join(summaries)}。")
    if pending_items:
        parts.append(f"Todo：{'；'.join(pending_items)}。")
    if risks:
        parts.append(f"需关注：{'；'.join(risks)}。")
    return "".join(parts) or "暂无"


def build_weekly_report_project_notes_map(
    context: dict,
    project_notes: dict[str, str] | None = None,
) -> dict[str, str]:
    provided_notes = {
        str(key or "").strip(): str(value or "").strip()
        for key, value in (project_notes or {}).items()
        if str(key or "").strip()
    }
    normalized_notes: dict[str, str] = {}
    for project in context.get("projects", []):
        project_name = str(project.get("project_name", "")).strip()
        if not project_name:
            continue
        normalized_notes[project_name] = provided_notes.get(project_name) or build_default_weekly_report_project_note(project)
    return normalized_notes


def sanitize_weekly_report_table_cell(value: object) -> str:
    text = str(value or "").strip()
    text = text.replace("|", "｜")
    text = re.sub(r"\s*\n+\s*", "；", text)
    return text or "暂无"


def parse_weekly_report_text_sections(raw_text: str) -> dict[str, str]:
    field_names = list(DINGTALK_WEEKLY_REPORT_SECTION_TITLES)
    normalized_keys = {normalize_weekly_report_section_title(name): name for name in field_names}
    collected_lines = {key: [] for key in normalized_keys}
    current_key = ""
    for raw_line in str(raw_text or "").splitlines():
        stripped = raw_line.strip()
        matched = re.match(r"^【(.+?)】$", stripped)
        if matched:
            normalized_key = normalize_weekly_report_section_title(matched.group(1))
            current_key = normalized_key if normalized_key in collected_lines else ""
            continue
        if current_key:
            collected_lines[current_key].append(raw_line.rstrip())
    return {
        key: "\n".join(lines).strip()
        for key, lines in collected_lines.items()
    }


def parse_weekly_report_project_notes(section_text: str) -> dict[str, str]:
    project_notes: dict[str, str] = {}
    current_project_name = ""
    current_lines: list[str] = []

    def commit_current_note() -> None:
        nonlocal current_project_name, current_lines
        if not current_project_name:
            current_lines = []
            return
        content = "\n".join(line for line in current_lines if str(line or "").strip()).strip()
        if content:
            project_notes[current_project_name] = content
        current_lines = []

    for raw_line in str(section_text or "").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if current_project_name and current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue
        matched_project = re.match(r"^\[项目名称\]\s*(.+)$", stripped)
        if matched_project:
            commit_current_note()
            current_project_name = matched_project.group(1).strip()
            current_lines = []
            continue
        matched_note = re.match(r"^\[工作和Todo\]\s*(.*)$", stripped)
        if matched_note:
            note_text = matched_note.group(1).strip()
            if note_text:
                current_lines.append(note_text)
            continue
        if current_project_name:
            current_lines.append(stripped)
    commit_current_note()
    return project_notes


def build_weekly_report_sections_from_text(raw_text: str, context: dict) -> tuple[list[dict], dict[str, str]]:
    parsed_sections = parse_weekly_report_text_sections(raw_text)
    parsed_project_notes = parse_weekly_report_project_notes(
        parsed_sections.get(normalize_weekly_report_section_title("本周工作"), "")
    )
    project_notes = build_weekly_report_project_notes_map(context, parsed_project_notes)
    fallback_sections = {
        normalize_weekly_report_section_title(section["title"]): section
        for section in fallback_weekly_report_sections(context)
    }
    completed_sections: list[dict] = []
    for field_name in DINGTALK_WEEKLY_REPORT_SECTION_TITLES:
        title_key = normalize_weekly_report_section_title(field_name)
        if title_key == normalize_weekly_report_section_title("本周工作"):
            content = build_weekly_report_work_summary_content(context, project_notes=project_notes)
        else:
            content = str(parsed_sections.get(title_key, "")).strip()
            if not content:
                content = fallback_sections[title_key]["content"]
        completed_sections.append({"title": field_name, "content": content})
    return completed_sections, project_notes


def fallback_weekly_report_sections(context: dict) -> list[dict]:
    weekly_work_content = build_weekly_report_work_summary_content(context)

    next_actions = []
    next_week_plan = context.get("next_week_plan", {})
    for day_plan in next_week_plan.get("days", []):
        day_name = str(day_plan.get("day_name", "")).strip()
        am_plan = str(day_plan.get("am", "")).strip()
        pm_plan = str(day_plan.get("pm", "")).strip()
        if am_plan:
            next_actions.append(f"{len(next_actions) + 1}. {day_name}上午：{am_plan}")
        if pm_plan:
            next_actions.append(f"{len(next_actions) + 1}. {day_name}下午：{pm_plan}")
    other_pending = str(next_week_plan.get("other_pending", "")).strip()
    if other_pending:
        next_actions.append(f"{len(next_actions) + 1}. 其他待定：{other_pending}")

    risks = []
    for project in context["projects"]:
        if project["risks"]:
            risks.append(f"{len(risks) + 1}. {project['project_name']}：{project['risks'][0]}")
    if not risks:
        risks = ["暂无"]

    assists = []
    for project in context["projects"]:
        if project["pending_items"]:
            assists.append(f"{len(assists) + 1}. {project['project_name']}：需要相关方协同推进“{project['pending_items'][0]}”。")
        if len(assists) >= 3:
            break
    if not assists:
        assists = ["暂无"]

    thoughts = [
        f"本周覆盖 {context['project_count']} 个项目/客户，共投入 {context['total_hours']} 小时，后续需继续提升事项闭环和风险前置识别。",
    ]
    return [
        {"title": "本周工作", "content": weekly_work_content},
        {"title": "下周计划", "content": "\n".join(next_actions or ["暂无"])},
        {"title": "问题和风险", "content": "\n".join(risks)},
        {"title": "需要协助", "content": "\n".join(assists)},
        {"title": "学习和思考", "content": "\n".join(thoughts)},
    ]


def build_weekly_report_work_summary_content(
    context: dict,
    project_notes: dict[str, str] | None = None,
) -> str:
    note_map = build_weekly_report_project_notes_map(context, project_notes)
    blocks = [
        "# 项目工作",
        "",
        "| 项目名称 | 服务类型 | 工时 | 项目类型 | 销售 |",
        "|----------|----------|------|----------|------|",
    ]

    for project in context.get("projects", []):
        project_name = str(project.get("project_name", "")).strip() or "未命名项目"
        service_types = "、".join(
            str(item).strip() for item in project.get("service_types", []) if str(item).strip()
        ) or "未标注"
        project_type = "、".join(
            str(item).strip() for item in project.get("project_types", []) if str(item).strip()
        ) or "未标注"
        sales = "、".join(
            str(item).strip() for item in project.get("sales", []) if str(item).strip()
        ) or "未标注"
        total_hours = str(project.get("total_hours", "")).strip() or "0"
        project_note = note_map.get(project_name) or "暂无"
        blocks.append(
            f"| {sanitize_weekly_report_table_cell(project_name)} | "
            f"{sanitize_weekly_report_table_cell(service_types)} | "
            f"{sanitize_weekly_report_table_cell(total_hours)} | "
            f"{sanitize_weekly_report_table_cell(project_type)} | "
            f"{sanitize_weekly_report_table_cell(sales)} |"
        )
        blocks.append(
            f"| {sanitize_weekly_report_table_cell(f'本周工作：{project_note}')} |  |  |  |  |"
        )

    return "\n".join(blocks)


def normalize_weekly_report_work_summary_markdown(content: str) -> str:
    text = str(content or "").strip()
    if not text:
        return ""

    raw_lines = text.splitlines()
    normalized_lines: list[str] = []
    line_index = 0
    while line_index < len(raw_lines):
        raw_line = raw_lines[line_index]
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "## 本周总结：" and normalized_lines and normalized_lines[-1] != "":
            normalized_lines.append("")
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
            if len(cells) == 5 and cells[0] != "项目名称" and cells[0] != "----------":
                cells[2] = re.sub(r"\s*(?:h|小时)\s*$", "", cells[2], flags=re.IGNORECASE).strip()
                line = f"| {' | '.join(cells)} |"
        normalized_lines.append(line)
        line_index += 1
    return "\n".join(normalized_lines).strip()


def is_valid_weekly_report_work_summary_markdown(content: str) -> bool:
    text = str(content or "").strip()
    if not text:
        return False
    required_title = "# 项目工作"
    required_header = "| 项目名称 | 服务类型 | 工时 | 项目类型 | 销售 |"
    required_divider = "|----------|----------|------|----------|------|"
    return (
        required_title in text
        and required_header in text
        and required_divider in text
        and "## 本周总结：" in text
        and "项目情况与Todo" not in text
    )


def normalize_weekly_report_section_title(title: str) -> str:
    normalized = re.sub(r"\s+", "", str(title or "").strip())
    normalized = re.sub(r"^\d+\s*[、.．:：]?\s*", "", normalized)
    normalized = normalized.rstrip(":：")
    return normalized


def normalize_weekly_report_sections_payload(raw_sections: object) -> list[dict]:
    field_names = list(DINGTALK_WEEKLY_REPORT_SECTION_TITLES)
    normalized_sections = {normalize_weekly_report_section_title(name): {"title": name, "content": ""} for name in field_names}
    if isinstance(raw_sections, list):
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            normalized_title = normalize_weekly_report_section_title(section.get("title", ""))
            if normalized_title not in normalized_sections:
                continue
            normalized_sections[normalized_title]["content"] = str(section.get("content", "")).strip()
    return [normalized_sections[normalize_weekly_report_section_title(name)] for name in field_names]


def normalize_weekly_report_response(context: dict, payload: dict) -> dict:
    raw_sections = payload.get("sections", []) if isinstance(payload, dict) else []
    normalized_sections = normalize_weekly_report_sections_payload(raw_sections)
    fallback_sections = {
        normalize_weekly_report_section_title(section["title"]): section
        for section in fallback_weekly_report_sections(context)
    }
    completed_sections = []
    for section in normalized_sections:
        title_key = normalize_weekly_report_section_title(section["title"])
        if title_key == normalize_weekly_report_section_title("本周工作"):
            content = normalize_weekly_report_work_summary_markdown(section.get("content", ""))
            if not is_valid_weekly_report_work_summary_markdown(content):
                content = build_weekly_report_work_summary_content(context)
        else:
            content = str(section.get("content", "")).strip()
        if not content:
            content = fallback_sections[title_key]["content"]
        completed_sections.append({"title": section["title"], "content": content})
    return {
        "week_start": str(payload.get("week_start") or context["week_start"]),
        "week_end": str(payload.get("week_end") or context["week_end"]),
        "sections": completed_sections,
    }


def build_weekly_report_content_text(sections: list[dict]) -> str:
    blocks: list[str] = []
    for section in sections:
        title = str(section.get("title", "")).strip()
        content = str(section.get("content", "")).strip() or "暂无"
        blocks.append(f"{title}\n{content}")
    return "\n\n".join(blocks)


def build_weekly_report_docx_filename(work_date: str) -> str:
    week_start, week_end, _ = build_week_window(work_date)
    return f"{week_start.replace('-', '')}-{week_end.replace('-', '')}周报.docx"


def generate_weekly_report_preview(work_date: str, user_id: str | None = None) -> dict:
    context = build_weekly_report_context(work_date, user_id=user_id)
    generation_notice = ""
    used_generated_fallback = False
    try:
        raw_content = run_codex_prompt(build_weekly_report_prompt(context, user_id=user_id), timeout_seconds=45)
        normalized_sections, project_notes = build_weekly_report_sections_from_text(raw_content, context)
        normalized_payload = {
            "week_start": context["week_start"],
            "week_end": context["week_end"],
            "sections": normalized_sections,
        }
    except RuntimeError:
        project_notes = build_weekly_report_project_notes_map(context)
        normalized_payload = {
            "week_start": context["week_start"],
            "week_end": context["week_end"],
            "sections": fallback_weekly_report_sections(context),
        }
        generation_notice = "智能周报生成超时，已自动切换为系统整理版周报。"
        used_generated_fallback = True
    filename = build_weekly_report_docx_filename(context["anchor_date"])
    saved_path = save_generated_file_to_logs(
        filename,
        build_weekly_report_word_document(context, normalized_payload["sections"], project_notes),
        user_id=user_id,
        category="weekly_report",
    )
    return {
        "kind": "weekly_report",
        "title": f"{normalized_payload['week_start']} 至 {normalized_payload['week_end']} 发送周报",
        "anchor_date": context["anchor_date"],
        "requested_anchor_date": context.get("requested_anchor_date", context["anchor_date"]),
        "requested_week_start": context.get("requested_week_start", context["week_start"]),
        "used_fallback_week": bool(context.get("used_fallback_week")),
        "used_generated_fallback": used_generated_fallback,
        "generation_notice": generation_notice,
        "week_start": normalized_payload["week_start"],
        "week_end": normalized_payload["week_end"],
        "sections": normalized_payload["sections"],
        "content": build_weekly_report_content_text(normalized_payload["sections"]),
        "saved_filename": saved_path.name,
        "saved_path": str(saved_path),
        "send_config": get_dingtalk_weekly_report_send_config(user_id=user_id),
    }


def generate_daily_log_preview(work_date: str, user_id: str | None = None) -> dict:
    validated_date = validate_date(work_date)
    content = run_codex_prompt(
        build_codex_log_prompt(build_daily_log_context(validated_date, user_id=user_id), user_id=user_id)
    )
    filename = build_daily_log_docx_filename(validated_date)
    saved_path = save_generated_file_to_logs(
        filename,
        build_word_document(content, f"{validated_date} 工作日志"),
        user_id=user_id,
        category="daily_log",
    )
    return {
        "kind": "daily_log",
        "title": f"{validated_date} 发送售后日报",
        "work_date": validated_date,
        "content": content,
        "saved_filename": saved_path.name,
        "saved_path": str(saved_path),
        "send_config": get_dingtalk_daily_log_send_config(user_id=user_id),
    }


def get_dingtalk_daily_log_send_config(user_id: str | None = None) -> dict:
    base_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    normalized_user_id = normalize_user_id(user_id)
    mcp_config = get_effective_dingtalk_mcp_config(user_id=normalized_user_id)
    template_config = get_effective_dingtalk_daily_template_config(normalized_user_id)
    setting_key = f"user:{normalized_user_id}:{DINGTALK_SEND_CONFIG_SETTING_KEY}"
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    saved_payload: dict = {}
    saved_updated_at = ""
    if row:
        try:
            loaded = json.loads(row["setting_value"] or "{}")
            if isinstance(loaded, dict):
                saved_payload = loaded
        except json.JSONDecodeError:
            saved_payload = {}
        saved_updated_at = str(row["updated_at"] or "")
    last_recipients = normalize_dingtalk_report_recipients(saved_payload.get("recipients", []))
    to_chat = (
        bool(saved_payload.get("to_chat"))
        if "to_chat" in saved_payload
        else DINGTALK_REPORT_TO_CHAT_DEFAULT
    )
    return {
        "template_id": str(template_config.get("template_id") or "").strip(),
        "template_name": str(template_config.get("template_name") or "").strip(),
        "template_source": str(template_config.get("source") or "missing"),
        "to_chat": to_chat,
        "base_recipients": base_recipients,
        "last_recipients": last_recipients,
        "log_mcp_source": str(mcp_config.get("log_mcp_source") or "missing"),
        "directory_mcp_source": str(mcp_config.get("directory_mcp_source") or "missing"),
        "updated_at": saved_updated_at,
    }


def save_dingtalk_daily_log_send_config(
    to_chat: bool, recipients: object | None = None, user_id: str | None = None
) -> tuple[dict, str]:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    setting_key = f"user:{normalized_user_id}:{DINGTALK_SEND_CONFIG_SETTING_KEY}"
    payload = {
        "to_chat": bool(to_chat),
        "recipients": normalize_dingtalk_report_recipients(recipients),
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (setting_key, json.dumps(payload, ensure_ascii=False), timestamp),
        )
    return payload, timestamp


def get_dingtalk_weekly_report_send_config(user_id: str | None = None) -> dict:
    base_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    normalized_user_id = normalize_user_id(user_id)
    mcp_config = get_effective_dingtalk_mcp_config(user_id=normalized_user_id)
    template_config = get_effective_dingtalk_weekly_template_config(normalized_user_id)
    setting_key = f"user:{normalized_user_id}:{DINGTALK_WEEKLY_REPORT_SEND_CONFIG_SETTING_KEY}"
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    saved_payload: dict = {}
    saved_updated_at = ""
    if row:
        try:
            loaded = json.loads(row["setting_value"] or "{}")
            if isinstance(loaded, dict):
                saved_payload = loaded
        except json.JSONDecodeError:
            saved_payload = {}
        saved_updated_at = str(row["updated_at"] or "")
    last_recipients = normalize_dingtalk_report_recipients(saved_payload.get("recipients", []))
    to_chat = (
        bool(saved_payload.get("to_chat"))
        if "to_chat" in saved_payload
        else DINGTALK_REPORT_TO_CHAT_DEFAULT
    )
    return {
        "template_id": str(template_config.get("template_id") or "").strip(),
        "template_name": str(template_config.get("template_name") or "").strip(),
        "template_source": str(template_config.get("source") or "missing"),
        "to_chat": to_chat,
        "base_recipients": base_recipients,
        "last_recipients": last_recipients,
        "log_mcp_source": str(mcp_config.get("log_mcp_source") or "missing"),
        "directory_mcp_source": str(mcp_config.get("directory_mcp_source") or "missing"),
        "updated_at": saved_updated_at,
    }


def save_dingtalk_weekly_report_send_config(
    to_chat: bool, recipients: object | None = None, user_id: str | None = None
) -> tuple[dict, str]:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    setting_key = f"user:{normalized_user_id}:{DINGTALK_WEEKLY_REPORT_SEND_CONFIG_SETTING_KEY}"
    payload = {
        "to_chat": bool(to_chat),
        "recipients": normalize_dingtalk_report_recipients(recipients),
    }
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (
                setting_key,
                json.dumps(payload, ensure_ascii=False),
                timestamp,
            ),
        )
    return payload, timestamp


def normalize_daily_log_section_title(title: str) -> str:
    normalized = str(title or "").strip()
    normalized = re.sub(r"^\d+\s*[、.．:：]?\s*", "", normalized)
    normalized = re.sub(r"\s*[:：]\s*$", "", normalized)
    return normalized.strip()


def normalize_daily_log_sections_payload(raw_sections: object) -> list[dict]:
    field_names = list(DINGTALK_DAILY_LOG_SECTION_TITLES)
    normalized_sections_by_name: dict[str, list[str]] = {field_name: [] for field_name in field_names}

    if isinstance(raw_sections, list):
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            section_name = normalize_daily_log_section_title(str(section.get("title", "")))
            if section_name not in normalized_sections_by_name:
                continue
            raw_items = section.get("items", [])
            items = [
                str(item).strip()
                for item in (raw_items if isinstance(raw_items, list) else [])
                if str(item).strip()
            ]
            normalized_sections_by_name[section_name] = items

    return [
        {
            "title": field_name,
            "items": normalized_sections_by_name[field_name],
        }
        for field_name in field_names
    ]


def normalize_dingtalk_report_recipients(raw_recipients: object) -> list[dict]:
    normalized: list[dict] = []
    seen: set[str] = set()
    if not isinstance(raw_recipients, (list, tuple)):
        return normalized
    for recipient in raw_recipients:
        if not isinstance(recipient, dict):
            continue
        user_id = str(recipient.get("user_id", recipient.get("userId", ""))).strip()
        name = str(recipient.get("name", "")).strip()
        identity = user_id or name
        if not identity or identity in seen:
            continue
        seen.add(identity)
        normalized.append({"user_id": user_id, "name": name})
    return normalized


def normalize_dingtalk_user_name_key(name: str) -> str:
    return re.sub(r"\s+", "", str(name or "").strip()).lower()


def get_cached_dingtalk_user_by_name(name: str) -> dict | None:
    name_key = normalize_dingtalk_user_name_key(name)
    if not name_key:
        return None
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT display_name, user_id, raw_json, updated_at
            FROM dingtalk_user_directory_cache
            WHERE name_key = ?
            """,
            (name_key,),
        ).fetchone()
    if not row:
        return None
    try:
        raw_payload = json.loads(row["raw_json"] or "{}")
    except json.JSONDecodeError:
        raw_payload = {}
    return {
        "name": str(row["display_name"] or "").strip(),
        "user_id": str(row["user_id"] or "").strip(),
        "source": "cache",
        "updated_at": str(row["updated_at"] or ""),
        "raw": raw_payload,
    }


def save_dingtalk_user_cache(name: str, user_id: str, raw_payload: dict | None = None) -> dict:
    display_name = str(name or "").strip()
    normalized_user_id = str(user_id or "").strip()
    if not display_name or not normalized_user_id:
        raise ValueError("缓存钉钉通讯录用户时，姓名和 userId 不能为空。")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dingtalk_user_directory_cache (name_key, display_name, user_id, raw_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name_key) DO UPDATE SET
                display_name = excluded.display_name,
                user_id = excluded.user_id,
                raw_json = excluded.raw_json,
                updated_at = excluded.updated_at
            """,
            (
                normalize_dingtalk_user_name_key(display_name),
                display_name,
                normalized_user_id,
                json.dumps(payload, ensure_ascii=False),
                timestamp,
                timestamp,
            ),
        )
    return {
        "name": display_name,
        "user_id": normalized_user_id,
        "source": "directory",
        "updated_at": timestamp,
        "raw": payload,
    }


def build_dingtalk_user_lookup_prompt(name: str, user_id: str | None = None) -> str:
    target_name = str(name or "").strip()
    return render_prompt_template(
        "send/dingtalk_user_lookup.txt",
        user_id=user_id,
        target_name=target_name,
        not_found_json=json.dumps({"matched": False, "reason": "not_found", "name": target_name, "candidates": []}, ensure_ascii=False),
        ambiguous_json=json.dumps(
            {"matched": False, "reason": "ambiguous", "name": target_name, "candidates": [{"name": "候选姓名", "user_id": "候选userId"}]},
            ensure_ascii=False,
        ),
        matched_json=json.dumps(
            {"matched": True, "name": target_name, "user_id": "匹配到的userId", "resolved_name": "通讯录正式姓名"},
            ensure_ascii=False,
        ),
    )


def lookup_dingtalk_user_by_name_via_directory(name: str, user_id: str | None = None) -> dict:
    target_name = str(name or "").strip()
    if not target_name:
        raise ValueError("姓名不能为空。")
    result = parse_codex_json_output(
        run_codex_directory_prompt(
            build_dingtalk_user_lookup_prompt(target_name, user_id=user_id),
            extra_config=build_dingtalk_mcp_extra_config(user_id=user_id, include_directory=True),
        )
    )
    if result.get("matched") is True:
        resolved_name = str(result.get("resolved_name") or result.get("name") or target_name).strip()
        user_id = str(result.get("user_id") or "").strip()
        if not user_id:
            raise RuntimeError("钉钉通讯录查询未返回有效 userId。")
        return save_dingtalk_user_cache(resolved_name, user_id, result)
    reason = str(result.get("reason") or "not_found").strip() or "not_found"
    candidates = normalize_dingtalk_report_recipients(result.get("candidates", []))
    if reason == "ambiguous" and candidates:
        candidate_text = "、".join(
            f"{item.get('name') or item.get('user_id')}（{item.get('user_id')}）"
            for item in candidates[:5]
        )
        raise RuntimeError(f"钉钉通讯录中找到多个同名人员，请明确选择：{candidate_text}")
    raise RuntimeError(f"钉钉通讯录中未找到“{target_name}”对应的 userId。")


def resolve_dingtalk_user_by_name(name: str, user_id: str | None = None) -> dict:
    require_dingtalk_mcp_config(user_id=user_id, include_directory=True)
    prompt_override, _ = get_user_prompt_template_override("send/dingtalk_user_lookup.txt", user_id=user_id)
    cached = None if prompt_override is not None else get_cached_dingtalk_user_by_name(name)
    if cached:
        return cached
    return lookup_dingtalk_user_by_name_via_directory(name, user_id=user_id)


def format_daily_log_section_content(items: list[str]) -> str:
    cleaned_items = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned_items:
        return "暂无"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(cleaned_items, start=1))


def build_dingtalk_daily_log_contents(sections: list[dict], template_config: dict | None = None) -> list[dict]:
    resolved_template = normalize_dingtalk_template_config(template_config)
    normalized_sections = normalize_daily_log_sections_payload(sections)
    contents: list[dict] = []
    for index, field in enumerate(resolved_template["fields"]):
        raw_items = normalized_sections[index].get("items", []) if index < len(normalized_sections) else []
        items = [
            str(item).strip()
            for item in (raw_items if isinstance(raw_items, list) else [])
            if str(item).strip()
        ]
        field_name = str(field["field_name"])
        contents.append(
            {
                "key": field_name,
                "sort": str(field["field_sort"]),
                "type": str(field["field_type"]),
                "contentType": "markdown",
                "content": format_daily_log_section_content(items),
            }
        )
    return contents


def build_dingtalk_daily_log_send_payload(
    contents: list[dict],
    to_chat: bool,
    recipients: object | None = None,
    template_config: dict | None = None,
) -> dict:
    resolved_template = normalize_dingtalk_template_config(template_config)
    payload = {
        "templateId": str(resolved_template.get("template_id") or "").strip(),
        "ddFrom": DINGTALK_REPORT_SOURCE,
        "toChat": bool(to_chat),
        "contents": contents,
    }
    merged_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    for recipient in normalize_dingtalk_report_recipients(recipients):
        if all(existing.get("user_id") != recipient.get("user_id") and existing.get("name") != recipient.get("name") for existing in merged_recipients):
            merged_recipients.append(recipient)
    recipient_ids = [recipient["user_id"] for recipient in merged_recipients if recipient.get("user_id")]
    if recipient_ids:
        payload["toUserIds"] = recipient_ids
    return payload


def build_dingtalk_daily_log_send_prompt(
    work_date: str,
    contents: list[dict],
    to_chat: bool,
    recipients: object | None = None,
    user_id: str | None = None,
    template_config: dict | None = None,
) -> str:
    resolved_template = normalize_dingtalk_template_config(template_config)
    payload = build_dingtalk_daily_log_send_payload(contents, to_chat, recipients, resolved_template)
    response_format = {
        "ok": True,
        "message": f"{work_date} 日志已发送",
        "template_id": str(resolved_template.get("template_id") or "").strip(),
        "template_name": str(resolved_template.get("template_name") or "").strip(),
        "report_id": "日志ID",
    }
    error_format = {
        "ok": False,
        "message": "失败原因",
        "template_id": str(resolved_template.get("template_id") or "").strip(),
        "template_name": str(resolved_template.get("template_name") or "").strip(),
        "report_id": "",
    }
    return render_prompt_template(
        "send/dingtalk_daily_log_send.txt",
        user_id=user_id,
        response_format_json=json.dumps(response_format, ensure_ascii=False),
        error_format_json=json.dumps(error_format, ensure_ascii=False),
        payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
    )


def send_daily_log_to_dingtalk(
    work_date: str,
    raw_sections: object,
    to_chat: bool | None = None,
    recipients: object | None = None,
    user_id: str | None = None,
) -> dict:
    validated_date = validate_date(work_date)
    sections = normalize_daily_log_sections_payload(raw_sections)
    template_config = require_selected_dingtalk_report_template_config(user_id=user_id, report_kind="daily")
    contents = build_dingtalk_daily_log_contents(sections, template_config)
    send_to_chat = DINGTALK_REPORT_TO_CHAT_DEFAULT if to_chat is None else bool(to_chat)
    merged_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    normalized_last_recipients = normalize_dingtalk_report_recipients(recipients)
    for recipient in normalized_last_recipients:
        if all(existing.get("user_id") != recipient.get("user_id") and existing.get("name") != recipient.get("name") for existing in merged_recipients):
            merged_recipients.append(recipient)
    result = parse_codex_json_output(
        run_codex_action_prompt(
            build_dingtalk_daily_log_send_prompt(
                validated_date,
                contents,
                send_to_chat,
                merged_recipients,
                user_id=user_id,
                template_config=template_config,
            ),
            extra_config=build_dingtalk_mcp_extra_config(user_id=user_id, include_log=True),
        )
    )

    if result.get("ok") is False or result.get("success") is False:
        raise RuntimeError(str(result.get("message") or "钉钉日志发送失败。"))

    saved_config, saved_updated_at = save_dingtalk_daily_log_send_config(
        send_to_chat, normalized_last_recipients, user_id=user_id
    )

    return {
        "ok": True,
        "work_date": validated_date,
        "template_id": str(result.get("template_id") or template_config.get("template_id") or "").strip(),
        "template_name": str(result.get("template_name") or template_config.get("template_name") or "").strip(),
        "message": str(result.get("message") or f"{validated_date} 的日志已发送到钉钉模板。"),
        "report_id": str(result.get("reportId") or result.get("report_id") or ""),
        "to_chat": send_to_chat,
        "base_recipients": normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS),
        "last_recipients": saved_config["recipients"],
        "recipients": merged_recipients,
        "send_config_updated_at": saved_updated_at,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_dingtalk_weekly_report_contents(
    sections: list[dict], template_config: dict | None = None
) -> list[dict]:
    resolved_template = normalize_dingtalk_template_config(template_config)
    normalized_sections = normalize_weekly_report_sections_payload(sections)
    contents: list[dict] = []
    for index, field in enumerate(resolved_template["fields"]):
        field_name = str(field["field_name"])
        content = ""
        if index < len(normalized_sections):
            content = str(normalized_sections[index].get("content", "")).strip()
        contents.append(
            {
                "key": field_name,
                "sort": str(field["field_sort"]),
                "type": str(field["field_type"]),
                "contentType": "markdown",
                "content": content or "暂无",
            }
        )
    return contents


def build_dingtalk_weekly_report_send_payload(
    contents: list[dict],
    to_chat: bool,
    recipients: object | None = None,
    template_config: dict | None = None,
) -> dict:
    resolved_template = normalize_dingtalk_template_config(template_config)
    payload = {
        "templateId": str(resolved_template.get("template_id") or "").strip(),
        "ddFrom": DINGTALK_REPORT_SOURCE,
        "toChat": bool(to_chat),
        "contents": contents,
    }
    merged_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    for recipient in normalize_dingtalk_report_recipients(recipients):
        if all(existing.get("user_id") != recipient.get("user_id") and existing.get("name") != recipient.get("name") for existing in merged_recipients):
            merged_recipients.append(recipient)
    recipient_ids = [recipient["user_id"] for recipient in merged_recipients if recipient.get("user_id")]
    if recipient_ids:
        payload["toUserIds"] = recipient_ids
    return payload


def build_dingtalk_weekly_report_send_prompt(
    week_start: str,
    week_end: str,
    contents: list[dict],
    to_chat: bool,
    recipients: object | None = None,
    user_id: str | None = None,
    template_config: dict | None = None,
) -> str:
    resolved_template = normalize_dingtalk_template_config(template_config)
    payload = build_dingtalk_weekly_report_send_payload(contents, to_chat, recipients, resolved_template)
    response_format = {
        "ok": True,
        "message": f"{week_start} 至 {week_end} 周报已发送",
        "template_id": str(resolved_template.get("template_id") or "").strip(),
        "template_name": str(resolved_template.get("template_name") or "").strip(),
        "report_id": "日志ID",
    }
    error_format = {
        "ok": False,
        "message": "失败原因",
        "template_id": str(resolved_template.get("template_id") or "").strip(),
        "template_name": str(resolved_template.get("template_name") or "").strip(),
        "report_id": "",
    }
    return render_prompt_template(
        "send/dingtalk_weekly_report_send.txt",
        user_id=user_id,
        response_format_json=json.dumps(response_format, ensure_ascii=False),
        error_format_json=json.dumps(error_format, ensure_ascii=False),
        payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
    )


def send_weekly_report_to_dingtalk(
    work_date: str,
    raw_sections: object,
    to_chat: bool | None = None,
    recipients: object | None = None,
    user_id: str | None = None,
) -> dict:
    validated_date = validate_date(work_date)
    week_start, week_end, _ = build_week_window(validated_date)
    sections = normalize_weekly_report_sections_payload(raw_sections)
    template_config = require_selected_dingtalk_report_template_config(user_id=user_id, report_kind="weekly")
    contents = build_dingtalk_weekly_report_contents(sections, template_config)
    send_to_chat = DINGTALK_REPORT_TO_CHAT_DEFAULT if to_chat is None else bool(to_chat)
    merged_recipients = normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS)
    normalized_last_recipients = normalize_dingtalk_report_recipients(recipients)
    for recipient in normalized_last_recipients:
        if all(existing.get("user_id") != recipient.get("user_id") and existing.get("name") != recipient.get("name") for existing in merged_recipients):
            merged_recipients.append(recipient)
    result = parse_codex_json_output(
        run_codex_action_prompt(
            build_dingtalk_weekly_report_send_prompt(
                week_start,
                week_end,
                contents,
                send_to_chat,
                merged_recipients,
                user_id=user_id,
                template_config=template_config,
            ),
            extra_config=build_dingtalk_mcp_extra_config(user_id=user_id, include_log=True),
        )
    )

    if result.get("ok") is False or result.get("success") is False:
        raise RuntimeError(str(result.get("message") or "钉钉周报发送失败。"))

    saved_config, saved_updated_at = save_dingtalk_weekly_report_send_config(
        send_to_chat, normalized_last_recipients, user_id=user_id
    )

    return {
        "ok": True,
        "work_date": validated_date,
        "week_start": week_start,
        "week_end": week_end,
        "template_id": str(result.get("template_id") or template_config.get("template_id") or "").strip(),
        "template_name": str(result.get("template_name") or template_config.get("template_name") or "").strip(),
        "message": str(result.get("message") or f"{week_start} 至 {week_end} 的周报已发送到钉钉模板。"),
        "report_id": str(result.get("reportId") or result.get("report_id") or ""),
        "to_chat": send_to_chat,
        "base_recipients": normalize_dingtalk_report_recipients(DINGTALK_REPORT_RECIPIENTS),
        "last_recipients": saved_config["recipients"],
        "recipients": merged_recipients,
        "send_config_updated_at": saved_updated_at,
        "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_weekly_strength_preview(work_date: str, user_id: str | None = None) -> dict:
    context = build_weekly_strength_context(work_date, user_id=user_id)
    filename = build_weekly_strength_xlsx_filename(work_date)
    saved_path = save_generated_file_to_logs(
        filename,
        build_weekly_strength_excel_file(context),
        user_id=user_id,
        category="weekly_strength",
    )
    return {
        "kind": "weekly_strength",
        "title": f"{context['week_start']} 至 {context['week_end']} 本周兵力盘点预览",
        "week_start": context["week_start"],
        "week_end": context["week_end"],
        "summary_lines": build_weekly_strength_summary_lines(context),
        "headers": get_weekly_strength_table_headers(),
        "rows": build_weekly_strength_table_rows(context),
        "footer_lines": build_weekly_strength_footer_lines(context),
        "saved_filename": saved_path.name,
        "saved_path": str(saved_path),
    }


def generate_codex_document(prompt: str, title: str) -> bytes:
    return build_word_document(run_codex_prompt(prompt), title)


def build_daily_log_docx_filename(work_date: str) -> str:
    normalized_date = validate_date(work_date).replace("-", "")
    return f"{normalized_date}日志.docx"


def build_weekly_strength_xlsx_filename(work_date: str) -> str:
    week_start, week_end, _ = build_week_window(work_date)
    return f"{week_start.replace('-', '')}-{week_end.replace('-', '')}本周兵力盘点.xlsx"


def build_month_export_xlsx_filename(month: str) -> str:
    normalized_month = validate_month(month)
    return f"daily-planner-{normalized_month}.xlsx"


def sanitize_log_path_segment(value: str, fallback: str) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return fallback
    sanitized = re.sub(r'[<>:"/\\\\|?*]+', "_", raw_value)
    sanitized = re.sub(r"\s+", "_", sanitized).strip(" ._")
    return sanitized or fallback


def resolve_log_owner_folder_name(user_id: str | None = None) -> str:
    try:
        normalized_user_id = normalize_user_id(user_id)
    except ValueError:
        normalized_user_id = DEFAULT_LOCAL_USER_ID
    with get_connection() as connection:
        row = connection.execute(
            "SELECT username FROM local_accounts WHERE user_id = ?",
            (normalized_user_id,),
        ).fetchone()
    if row and str(row["username"] or "").strip():
        return sanitize_log_path_segment(str(row["username"] or "").strip(), "default_user")
    return sanitize_log_path_segment(normalized_user_id, "default_user")


def resolve_log_category_folder_name(category: str) -> str:
    normalized_category = str(category or "").strip().lower()
    category_map = {
        "daily_log": "daily_logs",
        "weekly_report": "weekly_reports",
        "weekly_strength": "weekly_strength",
        "monthly_export": "monthly_exports",
        "misc": "misc",
    }
    return sanitize_log_path_segment(category_map.get(normalized_category, normalized_category), "misc")


def build_log_storage_filename(owner_folder: str, filename: str, timestamp: str) -> str:
    base_name = str(filename or "").strip() or "unnamed"
    owner_prefix = sanitize_log_path_segment(owner_folder, "default_user")
    if base_name.startswith(f"{owner_prefix}_"):
        return base_name
    return f"{owner_prefix}_{timestamp}_{base_name}"


def save_generated_file_to_logs(
    filename: str,
    content: bytes,
    *,
    user_id: str | None = None,
    category: str = "misc",
) -> Path:
    owner_folder = resolve_log_owner_folder_name(user_id)
    category_folder = resolve_log_category_folder_name(category)
    target_dir = LOG_DIR / owner_folder / category_folder
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_path = target_dir / build_log_storage_filename(owner_folder, filename, timestamp)
    target_path.write_bytes(content)
    return target_path


def resolve_generated_log_file_path(
    filename: str,
    *,
    user_id: str | None = None,
    category: str,
) -> Path:
    requested_name = str(filename or "").strip()
    if not requested_name:
        raise ValueError("缺少文件名。")
    if Path(requested_name).name != requested_name:
        raise ValueError("文件名格式不合法。")
    owner_folder = resolve_log_owner_folder_name(user_id)
    category_folder = resolve_log_category_folder_name(category)
    target_dir = (LOG_DIR / owner_folder / category_folder).resolve()
    target_path = (target_dir / requested_name).resolve()
    if target_path.parent != target_dir:
        raise ValueError("文件路径不合法。")
    if not target_path.exists() or not target_path.is_file():
        raise RuntimeError("日志文件不存在或已被清理。")
    return target_path


def escape_sql_like_pattern(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def delete_local_account_with_all_history(
    username: str,
    *,
    acting_user_id: str | None = None,
) -> dict:
    normalized_username = normalize_local_username(username)
    account = get_local_account_by_username(normalized_username)
    if not account:
        raise ValueError("未找到该本地账号。")

    target_user_id = normalize_user_id(str(account.get("user_id") or "").strip())
    if (
        target_user_id == DEFAULT_LOCAL_USER_ID
        or normalized_username == normalize_local_username(ADMIN_ACCOUNT_DEFAULT_USERNAME)
    ):
        raise ValueError("默认管理员账号不允许删除。")

    if str(acting_user_id or "").strip():
        normalized_actor_user_id = normalize_user_id(acting_user_id)
        if normalized_actor_user_id == target_user_id:
            raise ValueError("当前登录账号不能直接删除，请先使用其他管理员账号登录后再删除。")

    owner_folder = resolve_log_owner_folder_name(target_user_id)
    setting_key_prefix = f"user:{target_user_id}:"
    setting_key_pattern = f"{escape_sql_like_pattern(setting_key_prefix)}%"

    with get_connection() as connection:
        deleted_daily_entries = connection.execute(
            "DELETE FROM daily_entries WHERE user_id = ?",
            (target_user_id,),
        ).rowcount
        deleted_weekly_plans = connection.execute(
            "DELETE FROM weekly_plans WHERE user_id = ?",
            (target_user_id,),
        ).rowcount
        deleted_user_settings = connection.execute(
            "DELETE FROM app_settings WHERE setting_key LIKE ? ESCAPE '\\'",
            (setting_key_pattern,),
        ).rowcount
        deleted_sessions = connection.execute(
            "DELETE FROM user_sessions WHERE user_id = ?",
            (target_user_id,),
        ).rowcount
        deleted_scan_sessions = connection.execute(
            "DELETE FROM dingtalk_scan_login_sessions WHERE auth_user_id = ?",
            (target_user_id,),
        ).rowcount
        deleted_identities = connection.execute(
            "DELETE FROM dingtalk_user_identities WHERE local_user_id = ?",
            (target_user_id,),
        ).rowcount
        deleted_accounts = connection.execute(
            "DELETE FROM local_accounts WHERE username = ?",
            (normalized_username,),
        ).rowcount
        deleted_users = connection.execute(
            "DELETE FROM users WHERE user_id = ?",
            (target_user_id,),
        ).rowcount

    logs_dir = LOG_DIR / owner_folder
    deleted_logs = False
    if logs_dir.exists():
        try:
            rmtree(logs_dir)
            deleted_logs = True
        except OSError as error:
            raise RuntimeError(f"账号已删除，但清理日志目录失败：{error}") from error

    return {
        "ok": True,
        "username": normalized_username,
        "user_id": target_user_id,
        "deleted_daily_entries": deleted_daily_entries,
        "deleted_weekly_plans": deleted_weekly_plans,
        "deleted_user_settings": deleted_user_settings,
        "deleted_sessions": deleted_sessions,
        "deleted_scan_sessions": deleted_scan_sessions,
        "deleted_identities": deleted_identities,
        "deleted_accounts": deleted_accounts,
        "deleted_users": deleted_users,
        "deleted_logs": deleted_logs,
    }


def guess_download_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def validate_version(value: str) -> str:
    matched = re.fullmatch(r"V(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not matched:
        raise ValueError("版本格式必须是 Vx.y.z。")
    major, minor, patch = (int(part) for part in matched.groups())
    return f"V{major}.{minor}.{patch}"


def parse_version_tuple(value: str) -> tuple[int, int, int]:
    normalized = validate_version(value)
    matched = re.fullmatch(r"V(\d+)\.(\d+)\.(\d+)", normalized)
    assert matched is not None
    return tuple(int(part) for part in matched.groups())


def build_version_string(major: int, minor: int, patch: int) -> str:
    return f"V{major}.{minor}.{patch}"


def get_next_patch_version(value: str) -> str:
    major, minor, patch = parse_version_tuple(value)
    return build_version_string(major, minor, patch + 1)


def get_version_snapshot_dir(version: str) -> Path:
    return VERSION_ARCHIVE_DIR / validate_version(version)


def build_version_snapshot_relative_paths() -> list[str]:
    relative_paths: list[str] = []
    seen: set[str] = set()
    for root_name in VERSION_SNAPSHOT_ROOTS:
        source_root = BASE_DIR / root_name
        if source_root.is_file():
            candidates = [source_root]
        elif source_root.is_dir():
            candidates = sorted(path for path in source_root.rglob("*") if path.is_file())
        else:
            continue
        for candidate in candidates:
            relative_path = candidate.relative_to(BASE_DIR).as_posix()
            if relative_path in seen:
                continue
            seen.add(relative_path)
            relative_paths.append(relative_path)
    return relative_paths


def normalize_version_snapshot_file_list(raw_files: object) -> list[str]:
    if isinstance(raw_files, (list, tuple)):
        candidates = list(raw_files)
    else:
        candidates = [VERSION_PRIMARY_SNAPSHOT_FILENAME]
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in candidates:
        relative_path = str(raw_value or "").strip().replace("\\", "/")
        if not relative_path:
            continue
        path = Path(relative_path)
        if path.is_absolute() or ".." in path.parts:
            continue
        safe_path = Path(*[part for part in path.parts if part not in ("", ".")]).as_posix()
        if not safe_path or safe_path in seen:
            continue
        seen.add(safe_path)
        normalized.append(safe_path)
    if normalized:
        return normalized
    return [VERSION_PRIMARY_SNAPSHOT_FILENAME]


def get_version_snapshot_file_list(snapshot_dir: Path) -> list[str]:
    meta_path = snapshot_dir / VERSION_META_FILENAME
    if meta_path.exists():
        try:
            meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta_payload = {}
        return normalize_version_snapshot_file_list(meta_payload.get("files"))
    return [VERSION_PRIMARY_SNAPSHOT_FILENAME]


def list_version_snapshot_dirs() -> list[tuple[str, Path]]:
    VERSION_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, Path]] = []
    for child in VERSION_ARCHIVE_DIR.iterdir():
        if not child.is_dir():
            continue
        try:
            version = validate_version(child.name)
        except ValueError:
            continue
        if not (child / VERSION_PRIMARY_SNAPSHOT_FILENAME).exists() and not (child / VERSION_META_FILENAME).exists():
            continue
        entries.append((version, child))
    entries.sort(key=lambda item: parse_version_tuple(item[0]), reverse=True)
    return entries


def prune_version_history(max_versions: int = VERSION_HISTORY_RETENTION) -> list[str]:
    keep_count = max(1, int(max_versions or 1))
    removed_versions: list[str] = []
    for version, snapshot_dir in list_version_snapshot_dirs()[keep_count:]:
        rmtree(snapshot_dir)
        removed_versions.append(version)
    return removed_versions


def write_version_snapshot(
    version: str,
    *,
    note: str = "",
    overwrite: bool = False,
) -> Path:
    normalized_version = validate_version(version)
    VERSION_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_dir = get_version_snapshot_dir(normalized_version)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_files = build_version_snapshot_relative_paths()
    files_changed = False
    for relative_path in snapshot_files:
        source_file = BASE_DIR / relative_path
        target_file = snapshot_dir / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if overwrite or not target_file.exists() or source_file.read_bytes() != target_file.read_bytes():
            copy2(source_file, target_file)
            files_changed = True

    meta_path = snapshot_dir / VERSION_META_FILENAME
    existing_files = get_version_snapshot_file_list(snapshot_dir)
    if overwrite or files_changed or not meta_path.exists() or existing_files != snapshot_files:
        meta_payload = {
            "version": normalized_version,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": note.strip(),
            "files": snapshot_files,
        }
        meta_path.write_text(json.dumps(meta_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    prune_version_history()
    return snapshot_dir


def load_current_snapshot_file_bytes(snapshot_files: list[str]) -> dict[str, bytes]:
    return {relative_path: (BASE_DIR / relative_path).read_bytes() for relative_path in snapshot_files}


def snapshot_dir_matches_current(
    snapshot_dir: Path,
    *,
    snapshot_files: list[str],
    current_file_bytes: dict[str, bytes],
) -> bool:
    if get_version_snapshot_file_list(snapshot_dir) != snapshot_files:
        return False
    for relative_path in snapshot_files:
        snapshot_file = snapshot_dir / relative_path
        if not snapshot_file.exists() or snapshot_file.read_bytes() != current_file_bytes[relative_path]:
            return False
    return True


def resolve_current_app_version() -> tuple[str, bool]:
    snapshot_files = build_version_snapshot_relative_paths()
    current_file_bytes = load_current_snapshot_file_bytes(snapshot_files)
    version_dirs = list_version_snapshot_dirs()
    for version, snapshot_dir in version_dirs:
        if snapshot_dir_matches_current(
            snapshot_dir,
            snapshot_files=snapshot_files,
            current_file_bytes=current_file_bytes,
        ):
            return version, False
    if not version_dirs:
        return APP_VERSION_BASELINE, False
    latest_known_version = max((APP_VERSION_BASELINE, version_dirs[0][0]), key=parse_version_tuple)
    return get_next_patch_version(latest_known_version), True


def ensure_current_version_snapshot() -> Path:
    global APP_VERSION
    APP_VERSION, auto_bumped = resolve_current_app_version()
    note = "检测到代码变更后自动生成的新版本快照" if auto_bumped else "当前业务版本快照"
    return write_version_snapshot(APP_VERSION, note=note)


def list_version_history() -> list[dict]:
    versions: list[dict] = []
    for version, child in list_version_snapshot_dirs():
        meta_path = child / VERSION_META_FILENAME
        meta_payload: dict = {}
        if meta_path.exists():
            try:
                meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta_payload = {}
        versions.append(
            {
                "version": version,
                "created_at": str(meta_payload.get("created_at", "")),
                "note": str(meta_payload.get("note", "")),
                "is_current": version == APP_VERSION,
                "files": get_version_snapshot_file_list(child),
            }
        )
    return versions


def rollback_to_version(version: str) -> dict:
    normalized_version = validate_version(version)
    snapshot_dir = get_version_snapshot_dir(normalized_version)
    snapshot_files = get_version_snapshot_file_list(snapshot_dir)
    missing_files = [relative_path for relative_path in snapshot_files if not (snapshot_dir / relative_path).exists()]
    if missing_files:
        raise ValueError(f"未找到 {normalized_version} 的版本快照文件：{', '.join(missing_files)}。")
    ensure_current_version_snapshot()
    for relative_path in snapshot_files:
        target_file = BASE_DIR / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        copy2(snapshot_dir / relative_path, target_file)
    return {
        "ok": True,
        "rolled_back_to": normalized_version,
        "restart_required": True,
        "message": f"代码已回退到 {normalized_version}，请重启本地服务后生效。",
    }


def render_index_html(current_user: dict | None = None) -> str:
    current_user_id = ""
    if isinstance(current_user, dict):
        current_user_id = str(current_user.get("user_id") or "").strip()
    target_user_id = current_user_id or None
    _, weekly_settings, _ = get_weekly_plan_settings(date.today().isoformat(), user_id=target_user_id)
    ui_settings, _ = get_ui_settings(user_id=target_user_id)
    field_options = get_business_field_options_for_user_id(target_user_id)
    html = INDEX_HTML.replace("__INITIAL_DATE__", date.today().isoformat())
    html = html.replace("__INITIAL_MONTH__", date.today().strftime("%Y-%m"))
    html = html.replace("__APP_VERSION__", APP_VERSION)
    html = html.replace(
        "__INITIAL_SETTINGS_PAYLOAD__",
        json.dumps(weekly_settings, ensure_ascii=False),
    )
    html = html.replace(
        "__INITIAL_UI_SETTINGS_PAYLOAD__",
        json.dumps(ui_settings, ensure_ascii=False),
    )
    html = html.replace(
        "__INITIAL_FIELD_OPTIONS_PAYLOAD__",
        json.dumps(field_options, ensure_ascii=False),
    )
    html = html.replace(
        "__PUBLIC_QR_SERVICE_TEMPLATE_JSON__",
        json.dumps(DINGTALK_PUBLIC_QR_SERVICE_TEMPLATE, ensure_ascii=False),
    )
    return html


def render_department_schedule_html(current_user: dict | None = None) -> str:
    current_user_id = ""
    if isinstance(current_user, dict):
        current_user_id = str(current_user.get("user_id") or "").strip()
    target_user_id = current_user_id or None
    ui_settings, _ = get_ui_settings(user_id=target_user_id)
    return render_department_schedule_page_html(
        app_version=APP_VERSION,
        initial_date=date.today().isoformat(),
        initial_ui_settings_json=json.dumps(ui_settings, ensure_ascii=False),
        public_qr_service_template_json=json.dumps(DINGTALK_PUBLIC_QR_SERVICE_TEMPLATE, ensure_ascii=False),
    )


def render_admin_html(current_user: dict | None = None) -> str:
    current_user_id = ""
    if isinstance(current_user, dict):
        current_user_id = str(current_user.get("user_id") or "").strip()
    target_user_id = current_user_id or None
    ui_settings, _ = get_ui_settings(user_id=target_user_id)
    initial_auth_payload = {
        "authenticated": bool(current_user),
        "user": current_user if isinstance(current_user, dict) else None,
    }
    initial_auth_payload_json = json.dumps(initial_auth_payload, ensure_ascii=False)
    initial_auth_payload_json = (
        initial_auth_payload_json.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    is_admin_user = bool(current_user and str(current_user.get("role") or "") == "admin")
    initial_auth_info_text = "当前登录：未登录"
    if current_user and isinstance(current_user, dict):
        display_name = str(current_user.get("display_name") or current_user.get("user_id") or "").strip()
        user_id = str(current_user.get("user_id") or "").strip()
        identity_text = escape(f"{display_name}（{user_id}）") if display_name or user_id else ""
        if is_admin_user:
            initial_auth_info_text = f"当前登录：{identity_text} · 已进入管理后台"
        else:
            initial_auth_info_text = f"当前登录：{identity_text} · 普通账号"
    return render_admin_page_html(
        initial_auth_payload_json=initial_auth_payload_json,
        initial_ui_settings_json=json.dumps(ui_settings, ensure_ascii=False),
        initial_body_attrs="" if is_admin_user else ' class="admin-auth-state"',
        initial_auth_info_text=initial_auth_info_text,
        initial_account_button_attrs="" if is_admin_user else " hidden",
        initial_logout_button_attrs="" if current_user else " hidden",
        initial_department_button_attrs="",
        initial_user_button_attrs="",
        initial_login_card_attrs=" hidden" if is_admin_user else "",
        initial_admin_content_attrs="" if is_admin_user else " hidden",
    )


class DailyPlannerHandler(BaseHTTPRequestHandler):
    def _get_session_token(self) -> str:
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return ""
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except Exception:
            return ""
        morsel = cookie.get(SESSION_COOKIE_NAME)
        if not morsel:
            return ""
        return str(morsel.value or "").strip()

    def _get_current_user(self) -> dict | None:
        return get_user_by_session(self._get_session_token())

    def _resolve_user_id(self, *, query: dict | None = None, payload: dict | None = None) -> str:
        query_map = query if isinstance(query, dict) else {}
        payload_map = payload if isinstance(payload, dict) else {}
        current_user = self._get_current_user()
        header_user_id = self.headers.get("X-User-Id", "")
        query_user_id = ""
        if "user_id" in query_map and query_map.get("user_id"):
            query_user_id = str(query_map.get("user_id", [""])[0]).strip()
        payload_user_id = str(payload_map.get("user_id", "")).strip()
        candidate = payload_user_id or query_user_id or header_user_id

        if current_user:
            target_user_id = candidate or current_user["user_id"]
            normalized_target = normalize_user_id(target_user_id)
            if normalized_target != current_user["user_id"] and current_user.get("role") != "admin":
                raise PermissionError("无权访问其他用户的数据。")
            return ensure_user(normalized_target)

        try:
            normalized = normalize_user_id(candidate)
        except ValueError:
            normalized = DEFAULT_LOCAL_USER_ID
        return ensure_user(normalized)

    def _set_session_cookie(self, session_token: str) -> str:
        max_age = SESSION_DURATION_DAYS * 24 * 60 * 60
        return (
            f"{SESSION_COOKIE_NAME}={quote(session_token)}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"
        )

    def _clear_session_cookie(self) -> str:
        return f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"

    def _is_admin(self, user: dict | None) -> bool:
        return bool(user and str(user.get("role") or "") == "admin")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        current_user = self._get_current_user()

        if parsed.path == "/":
            self._send_html(render_index_html(current_user))
            return

        if parsed.path == "/admin":
            self._send_html(render_admin_html(current_user))
            return

        if parsed.path == "/department-schedule":
            self._send_html(render_department_schedule_html(current_user))
            return

        if parsed.path == "/api/auth/me":
            if not current_user:
                self._send_json({"authenticated": False, "user": None})
                return
            self._send_json({"authenticated": True, "user": current_user})
            return

        if parsed.path == "/api/department-schedule":
            if not current_user:
                self._send_json({"error": "请先登录后再访问部门日程页面。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            requested_date = query.get("date", [""])[0] or date.today().isoformat()
            requested_department = query.get("department", [""])[0]
            requested_departments = query.get("departments", [])
            requested_positions = query.get("positions", [])
            try:
                payload = build_department_schedule_payload(
                    current_user,
                    requested_date,
                    requested_department,
                    requested_departments=requested_departments,
                    requested_positions=requested_positions,
                )
                self._send_json(payload)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/department-schedule/edit-logs":
            if not current_user:
                self._send_json({"error": "请先登录后再查看日程编辑日志。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            requested_department = query.get("department", [""])[0]
            requested_departments = query.get("departments", [])
            requested_positions = query.get("positions", [])
            try:
                payload = build_department_schedule_edit_logs_payload(
                    current_user,
                    requested_department,
                    requested_departments=requested_departments,
                    requested_positions=requested_positions,
                )
                self._send_json(payload)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/field-options":
            has_explicit_scope = bool(
                str(self.headers.get("X-User-Id", "")).strip()
                or str(query.get("user_id", [""])[0]).strip()
            )
            if not current_user and not has_explicit_scope:
                self._send_json(get_business_field_options())
                return
            try:
                user_id = self._resolve_user_id(query=query)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json(get_business_field_options_for_user_id(user_id))
            return

        if parsed.path == "/api/auth/dingtalk-config":
            requested_origin = query.get("origin", [""])[0] or build_request_origin_from_headers(self.headers)
            config = build_dingtalk_oauth_public_config(get_dingtalk_oauth_config(), requested_origin)
            self._send_json(config)
            return

        if parsed.path == "/api/auth/dingtalk/scan-entry":
            requested_login_id = query.get("login_id", [""])[0]
            try:
                session = get_dingtalk_scan_login_session(login_id=requested_login_id)
            except ValueError:
                session = None
            if not session:
                self._send_html(
                    build_dingtalk_callback_result_html("二维码已过期", "该扫码登录二维码已失效，请回到电脑页面重新生成。", is_error=True),
                    status=HTTPStatus.GONE,
                )
                return
            config = get_dingtalk_oauth_config()
            if not config.get("enabled") or not config.get("configured"):
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉登录未启用", "管理员尚未完成钉钉扫码登录配置。", is_error=True),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                auth_url = build_dingtalk_oauth_authorize_url(
                    config,
                    session["login_id"],
                    session["state_token"],
                    session["redirect_base_url"],
                )
            except (ValueError, RuntimeError) as error:
                self._send_html(
                    build_dingtalk_callback_result_html("生成授权地址失败", str(error), is_error=True),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            self._send_redirect(auth_url)
            return

        if parsed.path == "/api/auth/dingtalk/callback":
            config = get_dingtalk_oauth_config()
            if not config.get("enabled") or not config.get("configured"):
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉登录未启用", "管理员尚未完成钉钉扫码登录配置。", is_error=True),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            state_token = query.get("state", [""])[0]
            try:
                session = get_dingtalk_scan_login_session(state_token=state_token)
            except ValueError:
                session = None
            if not session:
                self._send_html(
                    build_dingtalk_callback_result_html("登录会话已失效", "当前扫码登录会话不存在或已过期，请重新从电脑页面生成二维码。", is_error=True),
                    status=HTTPStatus.GONE,
                )
                return
            denied_reason = str(
                query.get("error_description", [""])[0]
                or query.get("error", [""])[0]
                or query.get("message", [""])[0]
            ).strip()
            if denied_reason:
                update_dingtalk_scan_login_session(
                    session["login_id"],
                    status="denied",
                    error_message=denied_reason,
                )
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉授权未完成", denied_reason, is_error=True),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            auth_code = query.get("authCode", [""])[0] or query.get("code", [""])[0]
            if not auth_code:
                update_dingtalk_scan_login_session(
                    session["login_id"],
                    status="error",
                    error_message="钉钉回调未返回 authCode。",
                )
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉登录失败", "钉钉回调未返回 authCode。", is_error=True),
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            try:
                user, auth_payload = resolve_dingtalk_scan_login_user(config, auth_code)
                update_dingtalk_scan_login_session(
                    session["login_id"],
                    status="completed",
                    auth_user_id=user["user_id"],
                    auth_display_name=user["display_name"],
                    auth_payload=auth_payload,
                )
                token, expires_at = create_user_session(user["user_id"])
                self._send_html(
                    build_dingtalk_callback_result_html(
                        "钉钉登录成功",
                        f"已完成钉钉授权：{user['display_name']}（{user['user_id']}）。\n如果你是在电脑上扫码，网页会自动完成登录；也可以直接关闭当前窗口。",
                    ),
                    extra_headers={"Set-Cookie": self._set_session_cookie(token)},
                )
            except PermissionError as error:
                update_dingtalk_scan_login_session(
                    session["login_id"],
                    status="denied",
                    error_message=str(error),
                )
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉登录被拒绝", str(error), is_error=True),
                    status=HTTPStatus.FORBIDDEN,
                )
            except (RuntimeError, ValueError) as error:
                update_dingtalk_scan_login_session(
                    session["login_id"],
                    status="error",
                    error_message=str(error),
                )
                self._send_html(
                    build_dingtalk_callback_result_html("钉钉登录失败", str(error), is_error=True),
                    status=HTTPStatus.BAD_GATEWAY,
                )
            return

        if parsed.path == "/api/auth/dingtalk/scan-session":
            requested_login_id = query.get("login_id", [""])[0]
            try:
                session = get_dingtalk_scan_login_session(login_id=requested_login_id)
            except ValueError:
                session = None
            if not session:
                self._send_json(
                    {"status": "expired", "error_message": "二维码已过期，请重新生成。"},
                    status=HTTPStatus.OK,
                )
                return
            if session["status"] == "completed" and session["auth_user_id"]:
                user = get_user_by_id(session["auth_user_id"])
                token, expires_at = create_user_session(session["auth_user_id"])
                self._send_json(
                    {
                        "status": "completed",
                        "expires_at": session["expires_at"],
                        "user": user,
                        "session_expires_at": expires_at,
                    },
                    extra_headers={"Set-Cookie": self._set_session_cookie(token)},
                )
                return
            self._send_json(
                {
                    "status": session["status"],
                    "expires_at": session["expires_at"],
                    "error_message": session["error_message"],
                }
            )
            return

        if parsed.path == "/api/auth/dingtalk/scan-qr":
            requested_login_id = query.get("login_id", [""])[0]
            try:
                session = get_dingtalk_scan_login_session(login_id=requested_login_id)
            except ValueError:
                session = None
            if not session:
                self._send_json({"error": "二维码会话不存在或已过期。"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                content = build_qr_png_via_swift(
                    build_dingtalk_scan_entry_url(session["redirect_base_url"], session["login_id"])
                )
                self._send_bytes(content, "image/png")
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/admin/users":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json({"users": list_all_users()})
            return

        if parsed.path == "/api/admin/access-control":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json(get_access_control_settings())
            return

        if parsed.path == "/api/admin/account":
            if current_user and self._is_admin(current_user):
                self._send_json(get_admin_account_public_info())
                return
            self._send_json({"username": get_admin_account_public_info()["username"]})
            return

        if parsed.path == "/api/admin/local-accounts":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json(
                {
                    "accounts": list_local_accounts(),
                    "department_options": get_department_options()["options"],
                }
            )
            return

        if parsed.path == "/api/admin/department-options":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json(get_department_options())
            return

        if parsed.path == "/api/admin/position-field-scopes":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json(get_position_field_scopes())
            return

        if parsed.path == "/api/admin/dingtalk-oauth-config":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            config, updated_at = get_dingtalk_oauth_config_with_updated_at()
            self._send_json({**config, "updated_at": updated_at})
            return

        if parsed.path == "/api/admin/dingtalk-identities":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            self._send_json({"identities": list_dingtalk_user_identities()})
            return

        if parsed.path == "/api/admin/overview":
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            requested_date = query.get("date", [""])[0] or date.today().isoformat()
            requested_month = query.get("month", [""])[0] or requested_date[:7]
            try:
                self._send_json(build_admin_overview_payload(requested_date, requested_month))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            user_id = self._resolve_user_id(query=query)
        except PermissionError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            return

        if parsed.path == "/api/entry":
            requested_date = query.get("date", [""])[0]
            try:
                self._send_json({"entry": fetch_entry(validate_date(requested_date), user_id=user_id)})
            except ValueError:
                self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/entries":
            requested_date = query.get("date", [""])[0] or date.today().isoformat()
            try:
                self._send_json(
                    {"entries": fetch_recent_entries(anchor_date=requested_date, user_id=user_id)}
                )
            except ValueError:
                self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/customer-names":
            self._send_json(fetch_customer_directory(user_id=user_id))
            return

        if parsed.path == "/api/dingtalk-user-lookup":
            query = parse_qs(parsed.query)
            requested_name = query.get("name", [""])[0]
            try:
                self._send_json(resolve_dingtalk_user_by_name(requested_name, user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.NOT_FOUND)
            return

        if parsed.path == "/api/settings":
            week_start, settings, updated_at = get_weekly_plan_settings(date.today().isoformat(), user_id=user_id)
            self._send_json({"week_start": week_start, "settings": settings, "updated_at": updated_at})
            return

        if parsed.path == "/api/ui-settings":
            settings, updated_at = get_ui_settings(user_id=user_id)
            self._send_json({"settings": settings, "updated_at": updated_at})
            return

        if parsed.path == "/api/user-prompts":
            if not current_user:
                self._send_json({"error": "请先登录后再编辑提示词。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            self._send_json({"prompts": list_user_prompt_templates(user_id=user_id)})
            return

        if parsed.path == "/api/user-dingtalk-mcp":
            if not current_user:
                self._send_json({"error": "请先登录后再编辑钉钉 MCP 配置。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            self._send_json({"config": get_user_dingtalk_mcp_config_summary(current_user["user_id"])})
            return

        if parsed.path == "/api/user-dingtalk-report-templates":
            if not current_user:
                self._send_json({"error": "请先登录后再读取钉钉日志模板。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            try:
                self._send_json({"templates": list_user_available_dingtalk_report_templates(current_user["user_id"])})
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_GATEWAY)
            return

        if parsed.path == BING_DAILY_BACKGROUND_PROXY_PATH:
            try:
                requested_market = str(query.get("mkt", [BING_DAILY_IMAGE_MARKET])[0] or "").strip()
                self._send_redirect(
                    resolve_bing_daily_background_url(requested_market or BING_DAILY_IMAGE_MARKET),
                    allow_cache=True,
                    extra_headers={"Cache-Control": "public, max-age=86400, immutable"},
                )
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            return

        if parsed.path == "/api/version-history":
            self._send_json({"current_version": APP_VERSION, "versions": list_version_history()})
            return

        if parsed.path == "/api/weekly-plan":
            requested_date = query.get("date", [""])[0] or date.today().isoformat()
            try:
                week_start, settings, updated_at = get_weekly_plan_settings(requested_date, user_id=user_id)
                self._send_json({"week_start": week_start, "settings": settings, "updated_at": updated_at})
            except ValueError:
                self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/month":
            target_month = query.get("month", [""])[0]
            try:
                entries = fetch_month_entries(target_month, user_id=user_id)
                self._send_json(
                    {
                        "month": validate_month(target_month),
                        "entries": entries,
                        "stats": build_month_stats(entries),
                    }
                )
            except ValueError:
                self._send_json({"error": "月份格式必须是 YYYY-MM。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/export":
            target_month = query.get("month", [""])[0]
            try:
                month = validate_month(target_month)
                entries = fetch_month_entries(month, user_id=user_id)
                filename = build_month_export_xlsx_filename(month)
                content = build_excel_file(entries, month)
                save_generated_file_to_logs(
                    filename,
                    content,
                    user_id=user_id,
                    category="monthly_export",
                )
                self._send_file(
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename,
                )
            except ValueError:
                self._send_json({"error": "月份格式必须是 YYYY-MM。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/export-log":
            requested_date = query.get("date", [""])[0]
            try:
                work_date = validate_date(requested_date)
                content = generate_daily_log_via_codex(work_date, user_id=user_id)
                filename = build_daily_log_docx_filename(work_date)
                save_generated_file_to_logs(filename, content, user_id=user_id, category="daily_log")
                self._send_file(
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    filename,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/export-weekly-strength":
            requested_date = query.get("date", [""])[0]
            try:
                work_date = validate_date(requested_date)
                content = generate_weekly_strength_report_spreadsheet(work_date, user_id=user_id)
                filename = build_weekly_strength_xlsx_filename(work_date)
                save_generated_file_to_logs(filename, content, user_id=user_id, category="weekly_strength")
                self._send_file(
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/download-weekly-report-file":
            requested_filename = query.get("filename", [""])[0]
            try:
                target_path = resolve_generated_log_file_path(
                    requested_filename,
                    user_id=user_id,
                    category="weekly_report",
                )
                self._send_file(
                    target_path.read_bytes(),
                    guess_download_content_type(target_path),
                    target_path.name,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.NOT_FOUND)
            return

        if parsed.path == "/api/preview-log":
            requested_date = query.get("date", [""])[0]
            try:
                self._send_json(generate_daily_log_preview(validate_date(requested_date), user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/preview-weekly-report":
            requested_date = query.get("date", [""])[0]
            try:
                self._send_json(generate_weekly_report_preview(validate_date(requested_date), user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            except Exception as error:
                self._send_json({"error": f"生成周报时发生异常：{error}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/preview-weekly-strength":
            requested_date = query.get("date", [""])[0]
            try:
                self._send_json(generate_weekly_strength_preview(validate_date(requested_date), user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/delivery-progress":
            requested_date = query.get("date", [""])[0]
            force_refresh = query.get("force", ["0"])[0] in {"1", "true", "yes"}
            try:
                work_date = validate_date(requested_date)
                self._send_json(
                    generate_weekly_delivery_progress_reports(work_date, force_refresh=force_refresh, user_id=user_id)
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/delivery-progress-cache":
            requested_date = query.get("date", [""])[0]
            try:
                work_date = validate_date(requested_date)
                self._send_json(load_weekly_delivery_progress_cache_only(work_date, user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/department-schedule/weekly-plan":
            current_user = self._get_current_user()
            if not current_user:
                self._send_json({"error": "请先登录后再维护部门安排。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                target_user = resolve_department_schedule_target_user(
                    current_user,
                    str(payload.get("user_id", "")).strip(),
                )
                week_start = str(payload.get("week_start", date.today().isoformat())).strip() or date.today().isoformat()
                target_user_id = str(target_user.get("user_id", "")).strip()
                saved_week_start = get_week_start(week_start)
                _, current_settings, current_updated_at = get_weekly_plan_settings(
                    saved_week_start,
                    user_id=target_user_id,
                )
                settings = build_department_weekly_plan_settings_from_rows(
                    payload.get("weekly_plan_rows", []),
                    weekly_other_pending=payload.get("weekly_other_pending", ""),
                )
                if settings != current_settings:
                    change_details = build_weekly_plan_change_details(current_settings, settings)
                    saved_week_start, saved_settings, updated_at = save_weekly_plan_settings(
                        week_start,
                        settings,
                        user_id=target_user_id,
                    )
                    record_weekly_plan_edit_log(
                        saved_week_start,
                        target_user=target_user,
                        editor_user=current_user,
                        change_details=change_details,
                        edited_at=updated_at,
                    )
                else:
                    saved_settings = current_settings
                    updated_at = current_updated_at
                weekly_plan_edit_logs = list_weekly_plan_edit_logs(
                    saved_week_start,
                    target_user_id=target_user_id,
                    limit=3,
                )
                self._send_json(
                    {
                        "ok": True,
                        "user_id": target_user_id,
                        "week_start": saved_week_start,
                        "weekly_plan_rows": build_department_weekly_plan_rows(saved_settings),
                        "weekly_other_pending": str(saved_settings.get("weekly_other_pending", "") or "").strip(),
                        "updated_at": updated_at,
                        "weekly_plan_last_editor": weekly_plan_edit_logs[0] if weekly_plan_edit_logs else None,
                        "weekly_plan_edit_logs": weekly_plan_edit_logs,
                    },
                    status=HTTPStatus.OK,
                )
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/password-login":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                username = str(payload.get("username", "")).strip()
                password = str(payload.get("password", ""))
                user = verify_local_account_password(username, password, require_admin=True)
                token, expires_at = create_user_session(user["user_id"])
                self._send_json(
                    {"ok": True, "user": get_user_by_id(user["user_id"]), "expires_at": expires_at},
                    status=HTTPStatus.OK,
                    extra_headers={"Set-Cookie": self._set_session_cookie(token)},
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.UNAUTHORIZED)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/password-update":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                username = str(payload.get("username", "")).strip()
                current_password = str(payload.get("current_password", ""))
                new_password = str(payload.get("new_password", ""))
                current_credentials = ensure_default_admin_account_credentials()
                if not verify_admin_account_password(str(current_credentials.get("username", "")), current_password):
                    self._send_json({"error": "当前密码不正确。"}, status=HTTPStatus.BAD_REQUEST)
                    return
                public_payload, _ = save_admin_account_credentials(username or str(current_credentials.get("username", "")), new_password)
                self._send_json({"ok": True, **public_payload})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/local-accounts":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                account = save_local_account(
                    username=str(payload.get("username", "")).strip(),
                    display_name=str(payload.get("display_name", "")).strip(),
                    positions=payload.get("positions", []),
                    department=str(payload.get("department", "")).strip(),
                    password=str(payload.get("password", "")),
                    enabled=bool(payload.get("enabled", True)),
                    is_admin=bool(payload.get("is_admin", False)),
                    is_department_admin=bool(payload.get("is_department_admin", False)),
                    show_in_department_schedule=bool(payload.get("show_in_department_schedule", False)),
                )
                self._send_json({"ok": True, "account": account}, status=HTTPStatus.OK)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/department-options":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                data, _ = save_department_options(payload.get("departments", payload.get("options", [])))
                self._send_json(data, status=HTTPStatus.OK)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/position-field-scopes":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                data, _ = save_position_field_scopes(payload)
                self._send_json(data, status=HTTPStatus.OK)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/admin/dingtalk-oauth-config":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                config, updated_at = save_dingtalk_oauth_config(payload if isinstance(payload, dict) else {})
                self._send_json({**config, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/auth/dingtalk/scan-session":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                config = get_dingtalk_oauth_config()
                if not config.get("enabled") or not config.get("configured"):
                    raise ValueError("管理员尚未启用钉钉扫码登录。")
                requested_origin = str(payload.get("current_origin", "")).strip()
                try:
                    redirect_base_url = config.get("redirect_base_url") or normalize_external_base_url(requested_origin)
                except ValueError:
                    redirect_base_url = config.get("redirect_base_url") or build_request_origin_from_headers(self.headers)
                session = create_dingtalk_scan_login_session(str(redirect_base_url))
                auth_url = build_dingtalk_oauth_authorize_url(
                    config,
                    session["login_id"],
                    session["state_token"],
                    session["redirect_base_url"],
                )
                scan_entry_url = build_dingtalk_scan_entry_url(session["redirect_base_url"], session["login_id"])
                qr_image_url = ""
                if config.get("scan_qr_supported"):
                    qr_image_url = f"/api/auth/dingtalk/scan-qr?{urlencode({'login_id': session['login_id']}, quote_via=quote)}"
                self._send_json(
                    {
                        "ok": True,
                        "login_id": session["login_id"],
                        "expires_at": session["expires_at"],
                        "redirect_base_url": session["redirect_base_url"],
                        "auth_url": auth_url,
                        "scan_entry_url": scan_entry_url,
                        "qr_image_url": qr_image_url,
                    },
                    status=HTTPStatus.CREATED,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/auth/password-login":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                user = verify_local_account_password(
                    str(payload.get("username", "")).strip(),
                    str(payload.get("password", "")),
                )
                token, expires_at = create_user_session(user["user_id"])
                self._send_json(
                    {"ok": True, "user": get_user_by_id(user["user_id"]), "expires_at": expires_at},
                    status=HTTPStatus.OK,
                    extra_headers={"Set-Cookie": self._set_session_cookie(token)},
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.UNAUTHORIZED)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/auth/password-update":
            current_user = self._get_current_user()
            if not current_user:
                self._send_json({"error": "请先登录后再修改密码。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                account = update_local_account_password(
                    str(current_user.get("user_id", "")).strip(),
                    str(payload.get("current_password", "")),
                    str(payload.get("new_password", "")),
                )
                self._send_json({"ok": True, "account": account}, status=HTTPStatus.OK)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/auth/login":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                requested_user_id = str(payload.get("user_id", "")).strip()
                requested_name = str(payload.get("name", "")).strip()
                resolved_user_id = ""
                resolved_name = ""
                if requested_user_id:
                    resolved_user_id = normalize_user_id(requested_user_id)
                    resolved_name = requested_name or resolved_user_id
                elif requested_name:
                    resolved = resolve_dingtalk_user_by_name(requested_name)
                    resolved_user_id = normalize_user_id(str(resolved.get("user_id", "")).strip())
                    resolved_name = str(resolved.get("name") or requested_name).strip() or resolved_user_id
                else:
                    raise ValueError("登录需要提供 user_id 或 name。")
                if not is_user_allowed_to_login(resolved_user_id):
                    raise ValueError("该钉钉账号未开通登录权限，请联系管理员。")
                user_role = "admin" if has_admin_access(resolved_user_id) else "user"
                user_id = ensure_user(resolved_user_id, display_name=resolved_name, role=user_role)
                token, expires_at = create_user_session(user_id)
                user = get_user_by_id(user_id)
                if user:
                    user["role"] = "admin" if has_admin_access(user_id) else "user"
                self._send_json(
                    {"ok": True, "user": user, "expires_at": expires_at},
                    status=HTTPStatus.OK,
                    extra_headers={"Set-Cookie": self._set_session_cookie(token)},
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.NOT_FOUND)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/auth/logout":
            deleted = delete_user_session(self._get_session_token())
            self._send_json(
                {"ok": True, "logged_out": deleted},
                status=HTTPStatus.OK,
                extra_headers={"Set-Cookie": self._clear_session_cookie()},
            )
            return

        if self.path == "/api/admin/access-control":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                settings, _ = save_access_control_settings(
                    payload.get("login_allowed_users", []),
                    payload.get("admin_allowed_users", []),
                )
                self._send_json(settings)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/rollback-version":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                target_version = str(payload.get("version", "")).strip()
                result = rollback_to_version(target_version)
                self._send_json(result)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/send-daily-log":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                user_id = self._resolve_user_id(payload=payload)
                work_date = str(payload.get("work_date", "")).strip()
                sections = payload.get("sections", [])
                to_chat = payload.get("to_chat")
                recipients = payload.get("recipients", [])
                self._send_json(send_daily_log_to_dingtalk(work_date, sections, to_chat, recipients, user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/send-weekly-report":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                user_id = self._resolve_user_id(payload=payload)
                work_date = str(payload.get("work_date", "")).strip()
                sections = payload.get("sections", [])
                to_chat = payload.get("to_chat")
                recipients = payload.get("recipients", [])
                self._send_json(send_weekly_report_to_dingtalk(work_date, sections, to_chat, recipients, user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/settings":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                user_id = self._resolve_user_id(payload=payload)
                week_start = str(payload.get("week_start", date.today().isoformat())).strip() or date.today().isoformat()
                saved_week_start, settings, updated_at = save_weekly_plan_settings(week_start, payload, user_id=user_id)
                self._send_json({"week_start": saved_week_start, "settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/weekly-plan":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                user_id = self._resolve_user_id(payload=payload)
                week_start = str(payload.get("week_start", date.today().isoformat())).strip() or date.today().isoformat()
                settings_payload = payload.get("settings", payload)
                saved_week_start, settings, updated_at = save_weekly_plan_settings(
                    week_start, settings_payload, user_id=user_id
                )
                self._send_json({"week_start": saved_week_start, "settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/ui-settings":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                user_id = self._resolve_user_id(payload=payload)
                settings, updated_at = save_ui_settings(payload, user_id=user_id)
                self._send_json({"settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/user-prompts":
            current_user = self._get_current_user()
            if not current_user:
                self._send_json({"error": "请先登录后再编辑提示词。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                user_id = self._resolve_user_id(payload=payload)
                self._send_json(save_user_prompt_templates(payload, user_id=user_id))
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/user-dingtalk-mcp":
            current_user = self._get_current_user()
            if not current_user:
                self._send_json({"error": "请先登录后再编辑钉钉 MCP 配置。"}, status=HTTPStatus.UNAUTHORIZED)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8")) if raw_payload else {}
                if not isinstance(payload, dict):
                    payload = {}
                self._send_json({"config": save_user_dingtalk_mcp_config(current_user["user_id"], payload)})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path != "/api/entry":
            self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_payload = self.rfile.read(content_length)
            payload = json.loads(raw_payload.decode("utf-8"))
            user_id = self._resolve_user_id(payload=payload)
            self._send_json({"entry": upsert_entry(payload, user_id=user_id)}, status=HTTPStatus.CREATED)
        except json.JSONDecodeError:
            self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except PermissionError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/admin/local-accounts":
            current_user = self._get_current_user()
            if not self._is_admin(current_user):
                self._send_json({"error": "仅管理员可访问。"}, status=HTTPStatus.FORBIDDEN)
                return
            query = parse_qs(parsed.query)
            username = str(query.get("username", [""])[0]).strip()
            try:
                self._send_json(
                    delete_local_account_with_all_history(
                        username,
                        acting_user_id=str((current_user or {}).get("user_id") or "").strip(),
                    ),
                    status=HTTPStatus.OK,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path != "/api/entry":
            self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)
            return
        query = parse_qs(parsed.query)
        try:
            user_id = self._resolve_user_id(query=query)
        except PermissionError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.FORBIDDEN)
            return
        requested_date = query.get("date", [""])[0]
        try:
            removed = delete_entry(requested_date, user_id=user_id)
            if not removed:
                self._send_json({"error": "该日期没有可删除的记录。"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json({"ok": True, "date": requested_date})
        except ValueError:
            self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(
        self,
        html: str,
        status: HTTPStatus = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        for header_key, header_value in (extra_headers or {}).items():
            self.send_header(header_key, str(header_value))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(
        self,
        payload: dict,
        status: HTTPStatus = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        for header_key, header_value in (extra_headers or {}).items():
            self.send_header(header_key, str(header_value))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(
        self,
        content: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = content if isinstance(content, (bytes, bytearray)) else bytes(content)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        for header_key, header_value in (extra_headers or {}).items():
            self.send_header(header_key, str(header_value))
        self.end_headers()
        self.wfile.write(body)

    def _send_redirect(
        self,
        location: str,
        status: HTTPStatus = HTTPStatus.FOUND,
        extra_headers: dict[str, str] | None = None,
        allow_cache: bool = False,
    ) -> None:
        self.send_response(status)
        self.send_header("Location", str(location))
        if not allow_cache:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        for header_key, header_value in (extra_headers or {}).items():
            self.send_header(header_key, str(header_value))
        self.end_headers()

    def _send_file(self, content: bytes, content_type: str, filename: str) -> None:
        fallback_name = filename.encode("ascii", errors="ignore").decode("ascii") or "download.bin"
        encoded_name = quote(filename)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f"attachment; filename=\"{fallback_name}\"; filename*=UTF-8''{encoded_name}")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(content)


def run() -> None:
    init_db()
    ensure_current_version_snapshot()
    server = ThreadingHTTPServer((HOST, PORT), DailyPlannerHandler)
    print(f"Daily Planner running at http://{HOST}:{PORT}")
    print(f"Config file: {CONFIG_SOURCE_PATH}")
    print(f"Database file: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
