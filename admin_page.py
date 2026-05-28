from __future__ import annotations

from help_docs import HELP_DOCS_CSS, HELP_DOCS_OVERLAY_HTML


def render_admin_html(
    *,
    initial_auth_payload_json: str,
    initial_ui_settings_json: str,
    initial_body_attrs: str = ' class="admin-auth-state"',
    initial_auth_info_text: str = "登录后可统一维护管理员账号、本地账号、岗位字段和钉钉接入配置。",
    initial_account_button_attrs: str = " hidden",
    initial_logout_button_attrs: str = " hidden",
    initial_department_button_attrs: str = " hidden",
    initial_user_button_attrs: str = " hidden",
    initial_login_card_attrs: str = "",
    initial_admin_content_attrs: str = " hidden",
) -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>管理员控制台</title>
  <style>
    :root {
      color-scheme: light;
      --bg-page: #eef5ff;
      --bg-soft: #f8fbff;
      --bg-deep: #e2edfb;
      --panel: rgba(255, 255, 255, 0.46);
      --panel-strong: rgba(255, 255, 255, 0.3);
      --panel-soft: rgba(244, 249, 255, 0.2);
      --ink: #12304f;
      --muted: #405d7b;
      --line: rgba(49, 102, 173, 0.16);
      --line-strong: rgba(49, 102, 173, 0.24);
      --line-soft: rgba(49, 102, 173, 0.1);
      --accent: #2e77d0;
      --accent-strong: #1957ab;
      --accent-deep: #1e58a0;
      --accent-soft: #dfeeff;
      --accent-glow: rgba(46, 119, 208, 0.14);
      --primary: var(--accent);
      --primary-deep: var(--accent-deep);
      --primary-soft: var(--accent-soft);
      --primary-shadow: 0 14px 28px rgba(38, 86, 150, 0.12);
      --danger: #c03c47;
      --danger-soft: #fff0f2;
      --text: var(--ink);
      --text-soft: var(--muted);
      --surface-rgb: 255, 255, 255;
      --surface-soft-rgb: 244, 249, 255;
      --table-head-rgb: 239, 247, 255;
      --table-cell-rgb: 255, 255, 255;
      --table-cell-alt-rgb: 247, 250, 255;
      --shell-surface-alpha: 0.82;
      --shell-surface-strong-alpha: 0.9;
      --shell-surface-soft-alpha: 0.72;
      --shell-surface-subtle-alpha: 0.54;
      --surface: var(--boot-region-background, linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,249,255,0.86)));
      --surface-strong: rgba(var(--surface-rgb), var(--shell-surface-strong-alpha));
      --surface-soft: rgba(var(--surface-soft-rgb), var(--shell-surface-alpha));
      --card-shadow: 0 18px 42px rgba(38, 86, 150, 0.09);
      --radius: 28px;
    }
    body[data-theme="dark"] {
      color-scheme: dark;
      --bg-page: #172437;
      --bg-soft: #213149;
      --bg-deep: #101a29;
      --panel: rgba(34, 50, 76, 0.68);
      --panel-strong: rgba(48, 69, 101, 0.54);
      --panel-soft: rgba(65, 90, 128, 0.3);
      --ink: #edf5ff;
      --muted: #e1ebf8;
      --line: rgba(159, 191, 236, 0.22);
      --line-strong: rgba(159, 191, 236, 0.32);
      --line-soft: rgba(159, 191, 236, 0.14);
      --accent: #7db7ff;
      --accent-strong: #edf5ff;
      --accent-deep: #f8fbff;
      --accent-soft: rgba(92, 146, 224, 0.28);
      --accent-glow: rgba(125, 183, 255, 0.24);
      --danger: #ff9aa4;
      --danger-soft: rgba(123, 49, 60, 0.24);
      --surface-rgb: 38, 56, 84;
      --surface-soft-rgb: 25, 39, 60;
      --table-head-rgb: 41, 60, 91;
      --table-cell-rgb: 35, 52, 79;
      --table-cell-alt-rgb: 29, 43, 66;
      --card-shadow: 0 22px 52px rgba(4, 10, 22, 0.24);
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
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: transparent;
    }
    .page-background {
      position: fixed;
      inset: -22vh 0 -22vh 0;
      z-index: 0;
      pointer-events: none;
      background-color: var(--boot-page-background-color, var(--bg-deep));
      background-image: var(--boot-page-background-image, none);
      background-repeat: var(--boot-page-background-repeat, no-repeat, no-repeat, no-repeat);
      background-position: var(--boot-page-background-position, center, center, center, center);
      background-size: var(--boot-page-background-size, cover, cover, auto, auto);
      transform-origin: center center;
    }
    .wrap { position: relative; z-index: 1; max-width: 1240px; margin: 0 auto; padding: 22px 18px 36px; }
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
      min-width: 220px;
      max-width: min(460px, calc(100vw - 168px));
      padding: 12px 14px;
      border-radius: 20px;
      border: 1px solid rgba(49, 102, 173, 0.14);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,249,255,0.84)),
        linear-gradient(135deg, rgba(46,119,208,0.08), transparent 72%);
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
      color: var(--text-soft);
      word-break: break-word;
    }
    .login-status-chip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 108px;
      max-width: min(420px, calc(100vw - 24px));
      white-space: normal;
      word-break: break-word;
      line-height: 1.45;
      text-align: center;
      cursor: default;
      pointer-events: none;
    }
    .theme-toggle {
      min-width: 108px;
      min-height: auto;
      padding: 7px 12px;
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.88));
      color: var(--accent-deep);
      border: 1px solid rgba(49, 102, 173, 0.12);
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.01em;
      line-height: 1;
      white-space: nowrap;
      cursor: pointer;
      justify-content: center;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.48);
      backdrop-filter: blur(10px);
      transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
    }
    .theme-toggle:hover {
      opacity: 0.98;
      transform: translateY(-0.5px);
      box-shadow: 0 10px 20px rgba(46, 119, 208, 0.12);
    }
    .tiny-btn {
      padding: 7px 12px;
      font-size: 12px;
      line-height: 1;
    }
    .background-settings-button { min-width: 108px; }
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
    .background-settings-menu[hidden] { display: none; }
    .background-settings-head { display: grid; gap: 4px; }
    .background-settings-title { margin: 0; font-size: 15px; font-weight: 800; color: var(--text); }
    .background-settings-note { margin: 0; color: var(--text-soft); font-size: 12px; line-height: 1.6; }
    .background-settings-group {
      display: grid;
      gap: 10px;
      padding: 12px;
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.18);
      background: rgba(255,255,255,0.3);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.36);
    }
    .background-settings-group-title { font-size: 13px; font-weight: 700; color: var(--text); }
    .background-settings-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .visual-file-name {
      min-height: 40px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: rgba(246, 250, 255, 0.88);
      color: var(--text-soft);
      font-size: 12px;
      line-height: 1.5;
      overflow-wrap: anywhere;
    }
    .visual-slider-row { display: grid; gap: 10px; }
    .visual-slider-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 13px;
      color: var(--text);
      font-weight: 700;
    }
    .visual-slider-value { color: var(--text-soft); font-size: 12px; font-weight: 700; }
    .visual-slider { width: 100%; accent-color: var(--primary); }
    .soft {
      background: linear-gradient(180deg, rgba(235,245,255,0.28), rgba(229,240,255,0.14));
      color: var(--accent-deep);
      border: 1px solid rgba(255,255,255,0.2);
      backdrop-filter: blur(10px);
      box-shadow: none;
    }
    .card {
      position: relative;
      overflow: hidden;
      background: var(--boot-region-background, linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,249,255,0.86)));
      border: 1px solid rgba(255,255,255,0.28);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: var(--card-shadow);
      backdrop-filter: blur(20px) saturate(120%);
      margin-bottom: 16px;
    }
    .admin-hero-card {
      padding: 22px;
      background: var(--boot-panel-background, linear-gradient(180deg, rgba(255,255,255,0.9), rgba(244,249,255,0.82)));
    }
    .admin-hero-card::after {
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
    .admin-login-card { max-width: 760px; margin-left: auto; margin-right: auto; }
    body.admin-auth-state .wrap { max-width: 960px; }
    body.admin-auth-state .admin-hero-card,
    body.admin-auth-state .admin-login-card {
      max-width: 860px;
      margin-left: auto;
      margin-right: auto;
    }
    .admin-login-form {
      display: grid;
      gap: 14px;
      margin-top: 16px;
      padding: 16px;
      border: 1px solid rgba(255,255,255,0.22);
      border-radius: 18px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.42);
      backdrop-filter: blur(12px);
    }
    .admin-login-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: end;
    }
    .admin-login-actions {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }
    .admin-login-actions button { min-width: 144px; }
    #admin-content { display: grid; gap: 16px; }
    #admin-content > .card { margin-bottom: 0; }
    h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: -0.02em; }
    h2 { margin: 0 0 6px; font-size: 18px; letter-spacing: -0.01em; }
    h3 { margin: 0; }
    .muted { color: var(--text-soft); font-size: 13px; line-height: 1.7; font-weight: 500; }
    label { display: grid; gap: 6px; color: var(--text); font-size: 13px; font-weight: 600; }
    textarea, input, select, button { font: inherit; }
    textarea, input, select {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line-strong);
      border-radius: 12px;
      padding: 10px 12px;
      box-sizing: border-box;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      color: var(--text);
      -webkit-text-fill-color: currentColor;
      box-shadow: inset 0 1px 2px rgba(21,61,110,0.06);
      transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
      backdrop-filter: blur(10px);
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
      border: 1px solid rgba(42,111,214,0.16);
      background: rgba(var(--surface-rgb), 0.88);
      color: var(--text);
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
      border-color: rgba(42,111,214,0.34);
      background: rgba(var(--surface-soft-rgb), 0.96);
    }
    .password-toggle-btn:focus-visible {
      outline: none;
      border-color: rgba(42,111,214,0.48);
      box-shadow: 0 0 0 4px rgba(42,111,214,0.12);
    }
    .password-toggle-btn.is-visible {
      border-color: rgba(42,111,214,0.34);
      background: rgba(214, 231, 255, 0.96);
      color: var(--primary);
    }
    .password-toggle-btn span {
      font-size: 16px;
      line-height: 1;
      pointer-events: none;
    }
    textarea { min-height: 124px; resize: vertical; }
    textarea:disabled,
    input:disabled,
    select:disabled {
      opacity: 1;
      -webkit-text-fill-color: currentColor;
    }
    textarea:focus, input:focus, select:focus {
      outline: none;
      border-color: rgba(42,111,214,0.62);
      box-shadow: 0 0 0 4px rgba(42,111,214,0.12);
    }
    input[type="checkbox"] {
      width: auto;
      min-height: auto;
      margin: 0;
      padding: 0;
      accent-color: var(--primary);
      box-shadow: none;
    }
    button {
      border: 1px solid var(--primary);
      border-radius: 12px;
      background: linear-gradient(135deg, var(--primary), #58a8ff);
      color: #fff;
      padding: 10px 14px;
      min-height: 40px;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      box-shadow: var(--primary-shadow);
      transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease, background-color 0.15s ease;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 14px 26px rgba(42,111,214,0.22); }
    button.secondary {
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      color: var(--text);
      border-color: var(--line);
      box-shadow: none;
    }
    button.secondary:hover { box-shadow: 0 10px 18px rgba(21,68,128,0.08); }
    button.danger {
      background: linear-gradient(180deg, #ef7777 0%, #d95b5b 100%);
      border-color: #d95b5b;
      box-shadow: 0 12px 24px rgba(217,91,91,0.18);
    }
    button.danger.secondary {
      background: var(--danger-soft);
      color: var(--danger);
      border-color: rgba(217,91,91,0.28);
      box-shadow: none;
    }
    button:disabled {
      opacity: 0.52;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }
    [hidden] { display: none !important; }
    .row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
    .col { flex: 1; min-width: 260px; }
    .top-actions { display: flex; gap: 10px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
    .checkline { display: flex; align-items: center; gap: 8px; color: var(--text); font-size: 13px; }
    .code {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--primary-soft);
      color: var(--primary-deep);
      border: 1px solid rgba(42,111,214,0.14);
      font-family: Menlo, Monaco, monospace;
      font-size: 12px;
    }
    .tag-list { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
    .tag-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--primary-soft);
      color: var(--primary-deep);
      border: 1px solid rgba(42,111,214,0.14);
    }
    .tag-pill button { border: none; background: transparent; color: var(--danger); padding: 0; cursor: pointer; min-height: auto; box-shadow: none; }
    .option-checklist {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      min-height: 48px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha));
    }
    .option-checkitem {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 11px;
      border-radius: 999px;
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
      color: var(--text);
      border: 1px solid rgba(42,111,214,0.12);
    }
    .option-empty { color: var(--text-soft); font-size: 13px; }
    .local-account-select-shell { display: grid; gap: 10px; margin-top: 10px; }
    .local-account-position-multiselect {
      position: relative;
      display: grid;
      gap: 8px;
    }
    .local-account-position-trigger {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      min-height: 44px;
      border-radius: 12px;
      border: 1px solid var(--line-strong);
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      color: var(--text);
      box-shadow: inset 0 1px 2px rgba(21,61,110,0.03);
    }
    .local-account-position-trigger:hover {
      box-shadow: 0 10px 18px rgba(21,68,128,0.08);
    }
    .local-account-position-trigger:disabled {
      background: rgba(245,248,252,0.88);
      color: var(--text-soft);
      border-color: var(--line);
    }
    .local-account-position-summary {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      text-align: left;
    }
    .local-account-position-arrow {
      flex: 0 0 auto;
      color: var(--text);
      font-size: 12px;
      transition: transform 0.18s ease;
    }
    .local-account-position-multiselect.open .local-account-position-arrow {
      transform: rotate(180deg);
    }
    .local-account-position-menu {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      right: 0;
      z-index: 30;
      display: grid;
      gap: 10px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      box-shadow: 0 18px 32px rgba(18,53,96,0.14);
      backdrop-filter: blur(16px);
    }
    .local-account-position-menu-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .local-account-position-menu-note {
      color: var(--text-soft);
      font-size: 12px;
      line-height: 1.6;
    }
    .local-account-position-options {
      display: grid;
      gap: 8px;
      max-height: 220px;
      overflow: auto;
      padding-right: 2px;
    }
    .local-account-position-options .option-checkitem {
      width: 100%;
      justify-content: flex-start;
      padding: 9px 12px;
      border-radius: 12px;
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    .local-account-position-empty {
      padding: 12px;
      border-radius: 12px;
      border: 1px dashed var(--line);
      background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha));
      color: var(--text-soft);
      font-size: 13px;
    }
    .local-account-department-controls { display: grid; gap: 8px; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; align-items: center; }
    .local-account-department-controls button { min-height: 42px; white-space: nowrap; }
    .local-account-select-note { color: var(--text-soft); font-size: 12px; line-height: 1.7; }
    .local-account-actions { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .mcp-config-cell { min-width: 280px; display: grid; gap: 8px; }
    .mcp-config-item { display: grid; gap: 3px; }
    .mcp-config-label { color: var(--text-soft); font-size: 11px; font-weight: 700; letter-spacing: 0.02em; }
    .mcp-config-value { font-size: 12px; line-height: 1.5; word-break: break-all; }
    .mcp-config-value.is-code { font-family: Menlo, Monaco, monospace; font-size: 11px; }
    .mcp-config-value.is-empty,
    .mcp-config-meta { color: var(--text-soft); }
    .mcp-config-meta { font-size: 11px; line-height: 1.4; }
    .department-directory-overview {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }
    .department-directory-card {
      display: grid;
      gap: 6px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      cursor: pointer;
      transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
    }
    .department-directory-card:hover {
      transform: translateY(-1px);
      border-color: rgba(42,111,214,0.18);
      box-shadow: 0 10px 24px rgba(46,119,208,0.1);
    }
    .department-directory-card.is-active {
      border-color: rgba(42,111,214,0.26);
      box-shadow: 0 12px 28px rgba(46,119,208,0.12);
      background: linear-gradient(
        180deg,
        rgba(255,255,255,0.78),
        rgba(233,242,255,0.72)
      );
    }
    .department-directory-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
    .department-directory-card-title { color: var(--text); font-size: 14px; font-weight: 700; }
    .department-directory-meta { color: var(--text-soft); font-size: 12px; line-height: 1.6; word-break: break-word; }
    .department-directory-empty {
      padding: 14px;
      border: 1px dashed var(--line);
      border-radius: 14px;
      color: var(--text-soft);
      font-size: 12px;
      background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha));
    }
    .field-manager-shell { margin-top: 14px; }
    .field-manager-select-row { display: grid; gap: 10px; margin-bottom: 12px; }
    .field-manager-block {
      display: grid;
      gap: 14px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      box-shadow: 0 8px 22px rgba(27,64,109,0.06);
      backdrop-filter: blur(14px);
    }
    .field-manager-block-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
    .field-manager-block-head h3 { margin: 0 0 6px; font-size: 16px; }
    .field-manager-toolbar { display: grid; gap: 10px; }
    .field-manager-input { display: grid; gap: 6px; color: var(--text); font-size: 13px; }
    .field-manager-buttonbar { display: flex; gap: 10px; flex-wrap: wrap; }
    .field-manager-status { min-height: 24px; }
    .field-summary-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 62px; padding: 5px 10px; border-radius: 999px; background: var(--primary-soft); color: var(--primary-deep); border: 1px solid rgba(42,111,214,0.14); font-size: 12px; font-weight: 700; white-space: nowrap; }
    .field-option-list { min-height: 150px; max-height: 230px; overflow: auto; display: grid; gap: 8px; padding: 8px; border: 1px solid var(--line); border-radius: 14px; background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha)); }
    .field-option-row { display: flex; align-items: center; gap: 12px; padding: 9px 10px; border-radius: 12px; border: 1px solid rgba(42,111,214,0.08); background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha)); }
    .field-option-row-main { display: flex; align-items: center; gap: 10px; min-width: 0; }
    .field-option-index { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px; background: var(--primary-soft); color: var(--primary-deep); font-size: 12px; font-weight: 700; flex: 0 0 28px; }
    .field-option-label { color: var(--text); font-size: 13px; word-break: break-word; }
    .field-config-note { color: var(--text-soft); font-size: 12px; line-height: 1.7; }
    .position-scope-shell { margin-top: 14px; }
    .position-scope-layout { display: grid; gap: 14px; grid-template-columns: 280px minmax(0, 1fr); align-items: stretch; }
    .position-scope-sidebar { display: grid; gap: 12px; align-content: stretch; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: linear-gradient(180deg, rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)), rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))); box-shadow: 0 8px 22px rgba(27,64,109,0.05); height: 100%; backdrop-filter: blur(14px); }
    .position-scope-sidebar > .position-scope-panel { height: 100%; align-content: start; }
    .position-scope-sidebar .position-scope-action-buttons { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .position-scope-sidebar .position-scope-action-buttons button {
      width: 100%;
      min-height: 34px;
      padding: 6px 10px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.3;
      box-shadow: 0 4px 10px rgba(46,119,208,0.08);
    }
    .position-scope-sidebar .position-scope-action-buttons button.secondary {
      border-color: var(--line-strong);
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
      color: var(--text);
      box-shadow: none;
    }
    .position-scope-sidebar .position-scope-action-buttons button.danger.secondary {
      border-color: rgba(217,91,91,0.24);
      color: var(--danger);
      background: var(--danger-soft);
    }
    .position-scope-sidebar #save-position-field-scope { grid-column: 1 / -1; }
    .position-scope-editor { display: grid; gap: 12px; height: 100%; }
    .position-scope-panel { display: grid; gap: 12px; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: linear-gradient(180deg, rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)), rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))); backdrop-filter: blur(14px); }
    .position-scope-panel[hidden] { display: none !important; }
    .position-scope-panel-head { display: grid; gap: 6px; }
    .position-scope-panel-label, .position-scope-inline { display: inline-flex; align-items: center; gap: 8px; width: fit-content; padding: 6px 10px; border-radius: 999px; background: var(--primary-soft); color: var(--primary-deep); border: 1px solid rgba(42,111,214,0.14); font-size: 12px; font-weight: 700; white-space: nowrap; }
    .position-scope-current-panel { background: linear-gradient(180deg, rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)), rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))); }
    .position-scope-current { display: inline-flex; align-items: center; gap: 8px; color: var(--text); font-size: 18px; font-weight: 700; }
    .position-scope-current-note { color: var(--text-soft); font-size: 13px; line-height: 1.7; }
    .position-scope-action-buttons { align-items: stretch; }
    .position-scope-action-buttons button { flex: 1 1 180px; }
    .position-scope-grid { display: grid; gap: 12px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .position-scope-summary-panel { margin-top: 14px; }
    .position-scope-summary { overflow: auto; border: 1px solid var(--line); border-radius: 14px; background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha)); }
    .position-scope-summary table { margin-top: 0; background: transparent; min-width: 640px; }
    .position-scope-summary td { line-height: 1.7; }
    .table-shell {
      margin-top: 16px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha));
    }
    .admin-account-overlay[hidden] { display: none !important; }
    .admin-account-overlay {
      position: fixed;
      inset: 0;
      z-index: 80;
      display: grid;
      place-items: center;
      padding: 22px;
      background: rgba(15, 34, 58, 0.34);
      backdrop-filter: blur(10px);
    }
    .admin-account-dialog {
      width: min(560px, 100%);
      display: grid;
      gap: 14px;
      padding: 18px;
      border-radius: 22px;
      border: 1px solid rgba(255,255,255,0.45);
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      box-shadow: 0 24px 60px rgba(16, 39, 66, 0.24);
      backdrop-filter: blur(18px);
    }
    .admin-account-dialog-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }
    .admin-account-dialog-title {
      margin: 0;
      font-size: 20px;
      letter-spacing: -0.02em;
      color: var(--text);
    }
    .admin-account-dialog-body {
      display: grid;
      gap: 12px;
    }
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; }
    .table-shell table { margin-top: 0; min-width: 720px; background: transparent; }
    th, td { border: none; border-bottom: 1px solid var(--line); padding: 10px 12px; font-size: 13px; text-align: left; vertical-align: top; background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha)); }
    tbody tr:nth-child(even) td { background: rgba(var(--table-cell-alt-rgb), var(--shell-surface-alpha)); }
    tbody tr:last-child td { border-bottom: none; }
    th { background: rgba(var(--table-head-rgb), var(--shell-surface-strong-alpha)); color: var(--text); font-weight: 700; }
    pre { margin: 0; white-space: pre-wrap; }
    [id$="-status"]:not(:empty) {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 11px;
      border-radius: 999px;
      border: 1px solid rgba(42,111,214,0.12);
      background: rgba(var(--surface-soft-rgb), var(--shell-surface-soft-alpha));
    }
    [id$="-status"]:empty { display: none; }
    body[data-theme="dark"] .muted,
    body[data-theme="dark"] .option-empty,
    body[data-theme="dark"] .local-account-select-note,
    body[data-theme="dark"] .field-config-note,
    body[data-theme="dark"] .position-scope-current-note,
    body[data-theme="dark"] pre {
      color: var(--muted);
    }
    body[data-theme="dark"] .card,
    body[data-theme="dark"] .admin-login-form,
    body[data-theme="dark"] .field-manager-block,
    body[data-theme="dark"] .position-scope-sidebar,
    body[data-theme="dark"] .position-scope-panel,
    body[data-theme="dark"] .position-scope-summary,
    body[data-theme="dark"] .table-shell,
    body[data-theme="dark"] .option-checklist,
    body[data-theme="dark"] .field-option-list,
    body[data-theme="dark"] .local-account-position-menu,
    body[data-theme="dark"] .local-account-position-empty,
    body[data-theme="dark"] .admin-account-dialog {
      border-color: rgba(255,255,255,0.08);
      background:
        linear-gradient(180deg, rgba(48, 69, 101, 0.54), rgba(30, 46, 71, 0.3)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.05), transparent 74%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 14px 28px rgba(4, 10, 22, 0.12);
    }
    body[data-theme="dark"] button.secondary {
      background: linear-gradient(180deg, rgba(55, 80, 118, 0.62), rgba(36, 54, 82, 0.44));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
    }
    body[data-theme="dark"] button.danger.secondary {
      background: linear-gradient(180deg, rgba(123, 49, 60, 0.9), rgba(86, 35, 43, 0.84));
      border-color: rgba(255, 154, 164, 0.22);
      color: #ffe6e8;
    }
    body[data-theme="dark"] .option-checkitem,
    body[data-theme="dark"] .field-option-row,
    body[data-theme="dark"] .local-account-position-trigger,
    body[data-theme="dark"] .local-account-position-options .option-checkitem,
    body[data-theme="dark"] .position-scope-sidebar .position-scope-action-buttons button.secondary {
      background: linear-gradient(180deg, rgba(36, 53, 82, 0.76), rgba(25, 39, 61, 0.62));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }
    body[data-theme="dark"] .local-account-position-trigger:disabled {
      background: linear-gradient(180deg, rgba(31, 46, 71, 0.72), rgba(23, 35, 55, 0.6));
      border-color: rgba(255,255,255,0.08);
      color: var(--muted);
      box-shadow: none;
    }
    body[data-theme="dark"] .local-account-position-arrow,
    body[data-theme="dark"] .page-user-badge-label {
      color: var(--accent-strong);
    }
    body[data-theme="dark"] .code,
    body[data-theme="dark"] .tag-pill,
    body[data-theme="dark"] .field-summary-badge,
    body[data-theme="dark"] .position-scope-panel-label,
    body[data-theme="dark"] .position-scope-inline,
    body[data-theme="dark"] .field-option-index {
      color: #f8fbff;
      background: rgba(54, 77, 112, 0.88);
      border-color: rgba(255,255,255,0.12);
    }
    body[data-theme="dark"] h1,
    body[data-theme="dark"] h2,
    body[data-theme="dark"] h3,
    body[data-theme="dark"] .field-manager-status:not(:empty) {
      color: #f8fbff;
    }
    body[data-theme="dark"] .field-option-label,
    body[data-theme="dark"] .position-scope-current,
    body[data-theme="dark"] label,
    body[data-theme="dark"] .checkline,
    body[data-theme="dark"] input,
    body[data-theme="dark"] select,
    body[data-theme="dark"] textarea,
    body[data-theme="dark"] th,
    body[data-theme="dark"] td {
      color: var(--ink);
    }
    body[data-theme="dark"] input,
    body[data-theme="dark"] select,
    body[data-theme="dark"] textarea {
      background: linear-gradient(180deg, rgba(36, 53, 82, 0.76), rgba(25, 39, 61, 0.62));
      border-color: rgba(255,255,255,0.1);
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
      color: rgba(199, 215, 236, 0.74);
    }
    body[data-theme="dark"] .page-user-badge {
      border-color: rgba(255,255,255,0.12);
      background:
        linear-gradient(180deg, rgba(36, 54, 82, 0.88), rgba(24, 38, 61, 0.78)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.12), transparent 72%);
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
    body[data-theme="dark"] .theme-toggle {
      background: linear-gradient(180deg, rgba(52, 76, 112, 0.62), rgba(35, 53, 81, 0.42));
      border-color: rgba(255,255,255,0.1);
      color: var(--ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
    }
    body[data-theme="dark"] .theme-toggle:hover {
      box-shadow: 0 12px 24px rgba(7, 15, 30, 0.18);
    }
    body[data-theme="dark"] .soft {
      background: linear-gradient(180deg, rgba(77, 114, 165, 0.58), rgba(51, 77, 114, 0.38));
      border-color: rgba(255,255,255,0.1);
      color: #eff6ff;
    }
    body[data-theme="dark"] .visual-file-name {
      background: rgba(25, 38, 59, 0.78);
      border-color: rgba(159, 191, 236, 0.18);
      color: var(--muted);
    }
    body[data-theme="dark"] [id$="-status"]:not(:empty) {
      color: #f8fbff;
      border-color: rgba(159, 191, 236, 0.28);
      background: rgba(54, 77, 112, 0.88);
    }
    body[data-theme="dark"] th {
      color: #f8fbff;
      background: rgba(54, 77, 112, 0.92);
    }
    @media (max-width: 768px) {
      .field-manager-block-head,
      .field-option-row { flex-direction: column; align-items: flex-start; }
      .field-manager-buttonbar { width: 100%; }
      .field-manager-buttonbar button { width: 100%; }
      .field-summary-badge { align-self: flex-start; }
      .wrap { padding-top: 18px; }
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
      .page-theme-toggle button,
      .page-theme-toggle .login-status-chip { width: 100%; }
      .admin-login-grid { grid-template-columns: 1fr; }
      .admin-login-actions { width: 100%; }
      .admin-login-actions button { width: 100%; }
      .local-account-position-menu { position: static; }
      .local-account-department-controls { grid-template-columns: 1fr; }
      .local-account-department-controls button { width: 100%; }
      .position-scope-layout { grid-template-columns: 1fr; }
      .position-scope-grid { grid-template-columns: 1fr; }
      .table-shell table { min-width: 640px; }
    }
__HELP_DOCS_CSS__
  </style>
</head>
<body__INITIAL_BODY_ATTRS__>
  <script>
    window.__bootUiSettings = __INITIAL_UI_SETTINGS_PAYLOAD__;
    window.__applyShellVisualSettings = (() => {
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
      const normalizeUiSettings = (source) => {
        const settings = source && typeof source === "object" ? source : {};
        return {
          background_image: typeof settings.background_image === "string" ? settings.background_image : "",
          background_mode: ["cover", "contain", "repeat"].includes(settings.background_mode) ? settings.background_mode : "cover",
          region_opacity: normalizeOpacity(
            firstDefinedValue(
              settings.region_opacity,
              settings.weekly_region_opacity,
              settings.editor_region_opacity,
              settings.month_region_opacity
            ),
            0.94
          ),
        };
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
      const buildBodyBackgroundImage = (theme, backgroundImage) => {
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
      };
      const buildViewportFallback = (theme) => {
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
      };
      const buildRegionSurface = (theme, opacity) => {
        const start = opacity;
        const end = Math.max(0.16, opacity - 0.08);
        if (theme === "dark") {
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
      return function applyShellVisualSettings(settings) {
        const normalized = normalizeUiSettings(settings);
        const theme = readStoredThemePreference() || getAutoTheme();
        document.body.dataset.theme = theme;
        const root = document.documentElement;
        const backgroundLayerStyle = buildBackgroundLayerStyle(normalized.background_image, normalized.background_mode);
        root.style.setProperty("--boot-page-background-color", theme === "dark" ? "#101a29" : "#e2edfb");
        root.style.setProperty("--boot-viewport-background", buildViewportFallback(theme));
        root.style.setProperty("--boot-page-background-image", buildBodyBackgroundImage(theme, normalized.background_image));
        root.style.setProperty("--boot-page-background-size", backgroundLayerStyle.size);
        root.style.setProperty("--boot-page-background-position", backgroundLayerStyle.position);
        root.style.setProperty("--boot-page-background-repeat", backgroundLayerStyle.repeat);
        root.style.setProperty("--boot-panel-background", buildRegionSurface(theme, Math.max(0.18, normalized.region_opacity - 0.04)));
        root.style.setProperty("--boot-region-background", buildRegionSurface(theme, normalized.region_opacity));
        root.style.setProperty(
          "--shell-surface-strong-alpha",
          String(Math.max(0.28, Math.min(0.98, normalized.region_opacity)))
        );
        root.style.setProperty(
          "--shell-surface-alpha",
          String(Math.max(0.22, Math.min(0.94, normalized.region_opacity - 0.04)))
        );
        root.style.setProperty(
          "--shell-surface-soft-alpha",
          String(Math.max(0.16, Math.min(0.9, normalized.region_opacity - 0.12)))
        );
        root.style.setProperty(
          "--shell-surface-subtle-alpha",
          String(Math.max(0.12, Math.min(0.86, normalized.region_opacity - 0.2)))
        );
        return normalized;
      };
    })();
    window.__bootUiSettings = window.__applyShellVisualSettings(window.__bootUiSettings);
  </script>
  <div class="page-background" aria-hidden="true"></div>
  <div class="wrap">
    <div class="page-theme-toggle">
      <button class="theme-toggle tiny-btn" id="admin-logout"__INITIAL_LOGOUT_BUTTON_ATTRS__>退出</button>
      <button class="theme-toggle tiny-btn" id="admin-account-button"__INITIAL_ACCOUNT_BUTTON_ATTRS__>修改密码</button>
      <button class="theme-toggle tiny-btn" id="admin-user-page"__INITIAL_USER_BUTTON_ATTRS__>用户页面</button>
      <button class="theme-toggle tiny-btn" id="admin-department-page"__INITIAL_DEPARTMENT_BUTTON_ATTRS__>日程管理</button>
      <button type="button" class="theme-toggle tiny-btn" id="theme-toggle">黑夜模式</button>
      <button type="button" class="theme-toggle tiny-btn background-settings-button" id="background-settings-button" aria-expanded="false" aria-controls="background-settings-menu">背景设置</button>
      <button type="button" class="theme-toggle tiny-btn" id="help-docs-button">帮助文档</button>
      <div class="background-settings-menu" id="background-settings-menu" hidden>
        <div class="background-settings-head">
          <h2 class="background-settings-title">背景与透明度</h2>
          <p class="background-settings-note">这里的背景图、展示模式和透明度会与填写页保持同一套个人设置，也支持切换到 Bing 每日图片。</p>
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
          <label>
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
    </div>
    <div class="card admin-login-card" id="admin-login-card"__INITIAL_LOGIN_CARD_ATTRS__>
      <h2>管理员登录</h2>
      <div class="muted">使用管理员账号进入后台，统一处理账号、权限和钉钉对接配置。</div>
      <div class="admin-login-form">
        <div class="admin-login-grid">
          <label>账号 <input id="login-username" type="text" value="admin"></label>
          <label>密码 <input id="login-password" type="password" placeholder="请输入管理员密码" data-password-toggle></label>
        </div>
        <div class="admin-login-actions">
          <button id="admin-login">登录后台</button>
          <span class="muted" id="admin-login-status"></span>
        </div>
      </div>
    </div>
    <div id="admin-content"__INITIAL_ADMIN_CONTENT_ATTRS__>
      <div class="card">
        <h2>字段管理</h2>
        <div class="muted">按岗位进行字段配置</div>
        <div class="position-scope-shell">
          <div class="position-scope-layout">
            <aside class="position-scope-sidebar">
              <section class="position-scope-panel">
                <div class="position-scope-panel-head">
                  <div class="position-scope-panel-label">岗位操作与选择</div>
                  <div class="field-config-note">先选择要编辑的岗位，再新增、复制或删除岗位；复制当前配置会把当前已填写字段复制到新岗位。</div>
                </div>
                <label class="field-manager-input">
                  <span>新岗位名称</span>
                  <input id="position-field-scope-new-position" type="text" placeholder="例如 售前经理">
                </label>
                <label class="field-manager-input">
                  <span>选择岗位</span>
                  <select id="position-field-scope-select">
                    <option value="">请先新增岗位</option>
                  </select>
                </label>
                <div class="field-manager-buttonbar position-scope-action-buttons">
                  <button id="create-position-field-scope">新增空岗位</button>
                  <button class="secondary" id="copy-position-field-scope">复制当前配置</button>
                  <button id="save-position-field-scope">保存当前岗位配置</button>
                  <button class="secondary danger" id="delete-position-field-scope">删除当前岗位</button>
                  <button class="secondary" id="reload-position-field-scope">重新加载</button>
                </div>
              </section>
            </aside>
            <div class="field-manager-block position-scope-editor">
              <div class="field-manager-block-head">
                <div>
                  <h3 id="position-field-scope-title">按岗位限制可选字段</h3>
                  <div class="muted" id="position-field-scope-subtitle">为不同岗位单独设置可用的销售、项目类型、服务方式、服务类型；一个用户勾选多个岗位时，可选项按已配置岗位取并集。</div>
                </div>
                <span class="position-scope-inline" id="position-field-scope-count">0 个岗位</span>
              </div>
              <section class="position-scope-panel position-scope-current-panel" hidden>
                <div class="position-scope-panel-label">当前岗位</div>
                <div class="position-scope-current" id="position-field-scope-current">当前岗位：未选择</div>
                <div class="position-scope-current-note" id="position-field-scope-current-note">请先选择岗位，再到下方维护该岗位可用的字段。</div>
              </section>
              <section class="position-scope-panel">
                <div class="position-scope-panel-head">
                  <div class="position-scope-panel-label">字段配置</div>
                  <div class="field-config-note">下面 4 个输入框均按逗号分隔，留空表示该岗位对该字段不单独限制。</div>
                </div>
                <div class="position-scope-grid">
                  <label class="field-manager-input">
                    <span>销售字段</span>
                    <input id="position-field-scope-sales" type="text" placeholder="例如 张三,李四">
                  </label>
                  <label class="field-manager-input">
                    <span>项目类型字段</span>
                    <input id="position-field-scope-project-types" type="text" placeholder="例如 A,B+,B">
                  </label>
                  <label class="field-manager-input">
                    <span>服务方式字段</span>
                    <input id="position-field-scope-service-modes" type="text" placeholder="例如 客户现场,远程支持">
                  </label>
                  <label class="field-manager-input">
                    <span>服务类型字段</span>
                    <input id="position-field-scope-item-types" type="text" placeholder="例如 方案交流,POC1,交付">
                  </label>
                </div>
                <div class="field-config-note">删除岗位前会提示受影响用户，并同步从这些用户身上移除该岗位。</div>
                <div class="field-manager-status muted" id="position-field-scope-status"></div>
              </section>
            </div>
          </div>
          <section class="position-scope-panel position-scope-summary-panel">
            <div class="position-scope-panel-head">
              <div class="position-scope-panel-label">岗位限制总览</div>
              <div class="field-config-note">用于快速对比不同岗位当前可选的销售、项目类型、服务方式、服务类型。</div>
            </div>
            <div class="position-scope-summary" id="position-field-scope-summary"></div>
          </section>
        </div>
      </div>
      <div class="card">
        <h2>本地账号管理</h2>
        <div class="muted">本地账号可直接用于网页登录；账号启停、管理员权限、部门管理员权限、日程展示权限、岗位和所属部门都在这里统一维护。</div>
        <div class="row" style="margin-top:10px;">
          <div class="col"><label>账号 <input id="local-account-username" type="text" placeholder="例如 zhangsan"></label></div>
          <div class="col"><label>显示名称 <input id="local-account-display-name" type="text" placeholder="例如 张三"></label></div>
        </div>
        <div class="local-account-select-shell">
          <div class="row">
            <div class="col">
              <div class="field-manager-input">
                <span>岗位</span>
                <div class="local-account-position-multiselect" id="local-account-position-multiselect">
                  <button
                    id="local-account-position-trigger"
                    class="local-account-position-trigger"
                    type="button"
                    aria-haspopup="listbox"
                    aria-expanded="false"
                  >
                    <span class="local-account-position-summary" id="local-account-position-summary">请选择岗位</span>
                    <span class="local-account-position-arrow">▼</span>
                  </button>
                  <div class="local-account-position-menu" id="local-account-position-menu" hidden>
                    <div class="local-account-position-menu-head">
                      <div class="position-scope-panel-label">岗位多选</div>
                      <div class="local-account-position-menu-note">点击即可勾选多个岗位</div>
                    </div>
                    <div class="local-account-position-options" id="local-account-position-options"></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col">
              <div class="field-manager-input">
                <span>所属部门</span>
                <div class="local-account-department-controls">
                  <select id="local-account-department-select"></select>
                  <input id="local-account-new-department" type="text" placeholder="输入新部门名称">
                  <button class="secondary" id="add-local-account-department" type="button">添加并选择</button>
                </div>
              </div>
            </div>
          </div>
          <div class="local-account-select-note">岗位支持多选；如果当前没有可选部门，可在右侧直接新增并立即选中。</div>
        </div>
        <div class="row" style="margin-top:10px;">
          <div class="col"><label>密码 <input id="local-account-password" type="password" placeholder="新建必填；留空表示不修改" data-password-toggle></label></div>
          <div class="col" style="display:flex; align-items:flex-end; gap:18px; flex-wrap:wrap;">
            <label class="checkline"><input id="local-account-enabled" type="checkbox" checked>启用账号</label>
            <label class="checkline"><input id="local-account-is-admin" type="checkbox">管理员</label>
            <label class="checkline"><input id="local-account-is-department-admin" type="checkbox">部门管理员</label>
            <label class="checkline"><input id="local-account-show-in-department-schedule" type="checkbox">在日程管理页展示</label>
          </div>
        </div>
        <div class="muted" style="margin-top:10px;">账号仅支持 3-64 位字母、数字、._@-；默认 <span class="code">admin</span> 账号始终保留管理员权限。未勾选“在日程管理页展示”的用户不会出现在日程管理页面。</div>
        <div class="row" style="margin-top:10px;">
          <button id="save-local-account">保存本地账号</button>
          <button class="secondary" id="reset-local-account-form">清空表单</button>
          <button class="secondary" id="reload-local-accounts">刷新账号列表</button>
          <span class="muted" id="local-account-status"></span>
        </div>
        <div class="table-shell">
          <table>
            <thead>
              <tr><th>账号</th><th>显示名</th><th>岗位</th><th>所属部门</th><th>本地 userId</th><th>状态</th><th>角色</th><th>日程展示</th><th>最近更新时间</th><th>操作</th></tr>
            </thead>
            <tbody id="local-accounts-body"></tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <h2>用户钉钉 MCP 总览</h2>
        <div class="muted">这里会展示每个用户当前保存的钉钉 MCP 地址与模板选择，方便管理员直接排查具体配置。</div>
        <div class="row" style="margin-top:10px;">
          <button class="secondary" id="reload-admin-users">刷新用户 MCP</button>
          <span class="muted" id="admin-users-status"></span>
        </div>
        <div class="table-shell">
          <table>
            <thead>
              <tr><th>显示名</th><th>本地 userId</th><th>钉钉 MCP</th></tr>
            </thead>
            <tbody id="admin-users-body"></tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <h2>部门共享钉钉通讯录</h2>
        <div class="muted">同部门用户共享一份钉钉姓名 / userId 数据库。员工在用户页通过钉钉通讯录查到的人员会自动写入本部门；这里也可以直接用当前管理员账号补充查询并加入共享人员。</div>
        <div class="row" style="margin-top:10px;">
          <div class="col">
            <label>所属部门
              <select id="department-directory-department"></select>
            </label>
          </div>
          <div class="col">
            <label>补充人员姓名
              <input id="department-directory-lookup-name" type="text" placeholder="输入姓名后查询并加入当前部门">
            </label>
          </div>
          <div class="col" style="display:flex; align-items:flex-end; gap:10px; flex-wrap:wrap;">
            <button id="add-department-directory-entry">查询并加入当前部门</button>
            <button class="secondary" id="reload-department-directory">刷新共享人员</button>
          </div>
        </div>
        <span class="muted" id="department-directory-status"></span>
        <div class="department-directory-overview" id="department-directory-overview"></div>
        <div class="table-shell" style="margin-top:12px;">
          <table>
            <thead>
              <tr><th>姓名</th><th>钉钉 userId</th><th>最近同步人</th><th>最近同步时间</th></tr>
            </thead>
            <tbody id="department-directory-body"></tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <h2>钉钉用户权限控制</h2>
        <div class="muted">填写钉钉 userId，本地账号能否登录以上方配置为主</div>
        <div class="row">
          <div class="col">
            <div class="muted">登录用户 userId</div>
            <textarea id="login-users" rows="6" placeholder="例如：&#10;282860371726230453&#10;manager_demo_userid"></textarea>
          </div>
          <div class="col">
            <div class="muted">管理后台 userId</div>
            <textarea id="admin-users" rows="6" placeholder="例如：&#10;282860371726230453"></textarea>
          </div>
        </div>
        <div class="row" style="margin-top:10px;">
          <button id="save-access">保存权限配置</button>
          <button class="secondary" id="reload-access">刷新权限配置</button>
          <span class="muted" id="access-status"></span>
        </div>
      </div>
      <div class="card">
        <h2>钉钉组织接入与扫码登录</h2>
        <div class="muted">配置钉钉开放平台应用后，首页可展示扫码登录；建议使用可被手机访问的局域网或公网地址作为回调基地址。</div>
        <div class="row" style="margin-top:10px;">
          <label class="checkline"><input id="dingtalk-enabled" type="checkbox">启用钉钉扫码登录</label>
          <label class="checkline"><input id="dingtalk-auto-login" type="checkbox">允许当前组织成员直接登录</label>
        </div>
        <div class="row" style="margin-top:10px;">
          <div class="col"><label>ClientId <input id="dingtalk-client-id" type="text" placeholder="dingxxxxxxxxxxxxxxxx"></label></div>
          <div class="col"><label>ClientSecret <input id="dingtalk-client-secret" type="password" placeholder="请输入应用密钥" data-password-toggle></label></div>
        </div>
        <div class="row" style="margin-top:10px;">
          <div class="col"><label>CorpId <input id="dingtalk-corp-id" type="text" placeholder="dingxxxxxxxxxxxxxxxx"></label></div>
          <div class="col"><label>回调基地址 <input id="dingtalk-redirect-base-url" type="url" placeholder="例如 http://192.168.1.23:8000"></label></div>
        </div>
        <div class="muted" style="margin-top:10px;">
          需要在钉钉开放平台把回调地址配置为 <span class="code" id="dingtalk-callback-url">未配置</span>，并确保应用授权范围包含 <span class="code">openid</span>、<span class="code">corpid</span>、<span class="code">Contact.User.Read</span>。
        </div>
        <div class="row" style="margin-top:10px;">
          <button id="save-dingtalk-config">保存钉钉配置</button>
          <button class="secondary" id="reload-dingtalk-config">刷新钉钉配置</button>
          <span class="muted" id="dingtalk-config-status"></span>
        </div>
      </div>
      <div class="card">
        <h2>最近识别到的钉钉用户</h2>
        <div class="muted">扫码登录成功后，系统会缓存钉钉身份信息，方便查看本地 userId、权限和最近更新时间。</div>
        <div class="row" style="margin-top:10px;">
          <button class="secondary" id="reload-dingtalk-identities">刷新用户列表</button>
          <span class="muted" id="dingtalk-identities-status"></span>
        </div>
        <div class="table-shell">
          <table>
            <thead>
              <tr><th>姓名</th><th>本地 userId</th><th>CorpId</th><th>手机号</th><th>角色</th><th>最近更新时间</th></tr>
            </thead>
            <tbody id="dingtalk-identities-body"></tbody>
          </table>
        </div>
      </div>
    </div>
    <div class="admin-account-overlay" id="admin-account-overlay" hidden>
      <section class="admin-account-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-account-dialog-title">
        <div class="admin-account-dialog-head">
          <div>
            <h2 class="admin-account-dialog-title" id="admin-account-dialog-title">修改管理员帐密</h2>
            <div class="muted">修改后将用于下次进入管理员后台时登录，系统仅保存加密后的密码结果。</div>
          </div>
          <button class="secondary" type="button" id="admin-account-overlay-close">关闭</button>
        </div>
        <div class="admin-account-dialog-body">
          <label>账号 <input id="admin-username" type="text"></label>
          <label>当前密码 <input id="admin-current-password" type="password" autocomplete="current-password" data-password-toggle></label>
          <label>新密码 <input id="admin-new-password" type="password" autocomplete="new-password" placeholder="至少 8 位" data-password-toggle></label>
          <label>确认新密码 <input id="admin-confirm-password" type="password" autocomplete="new-password" data-password-toggle></label>
          <div class="row" style="margin-top:4px;">
            <button id="admin-account-save" type="button">保存管理员帐密</button>
            <span class="muted" id="admin-account-status"></span>
          </div>
        </div>
      </section>
    </div>
__HELP_DOCS_OVERLAY__
  </div>
  <script>
    let initialAdminAuthState = __INITIAL_ADMIN_AUTH_PAYLOAD__;
    const authInfo = document.getElementById("auth-info");
    const adminContent = document.getElementById("admin-content");
    const loginCard = document.getElementById("admin-login-card");
    const adminAccountButton = document.getElementById("admin-account-button");
    const adminLogoutButton = document.getElementById("admin-logout");
    const adminDepartmentPageButton = document.getElementById("admin-department-page");
    const adminUserPageButton = document.getElementById("admin-user-page");
    const helpDocsButton = document.getElementById("help-docs-button");
    const themeToggleButton = document.getElementById("theme-toggle");
    const backgroundSettingsButton = document.getElementById("background-settings-button");
    const backgroundSettingsMenu = document.getElementById("background-settings-menu");
    const backgroundImageInput = document.getElementById("background-image-input");
    const selectBackgroundImageButton = document.getElementById("select-background-image");
    const useBingBackgroundButton = document.getElementById("use-bing-background");
    const clearBackgroundImageButton = document.getElementById("clear-background-image");
    const backgroundImageName = document.getElementById("background-image-name");
    const backgroundModeSelect = document.getElementById("background-mode-select");
    const regionOpacityInput = document.getElementById("region-opacity-input");
    const regionOpacityValue = document.getElementById("region-opacity-value");
    const adminLoginStatus = document.getElementById("admin-login-status");
    const loginUsersEl = document.getElementById("login-users");
    const adminUsersEl = document.getElementById("admin-users");
    const accessStatus = document.getElementById("access-status");
    const adminAccountOverlay = document.getElementById("admin-account-overlay");
    const adminAccountOverlayCloseButton = document.getElementById("admin-account-overlay-close");
    const adminUsernameEl = document.getElementById("admin-username");
    const adminCurrentPasswordEl = document.getElementById("admin-current-password");
    const adminNewPasswordEl = document.getElementById("admin-new-password");
    const adminConfirmPasswordEl = document.getElementById("admin-confirm-password");
    const adminAccountStatus = document.getElementById("admin-account-status");
    const helpOverlay = document.getElementById("help-overlay");
    const helpOverlayCloseButton = document.getElementById("help-overlay-close");
    const helpTabList = document.getElementById("help-tab-list");
    const helpRolePill = document.getElementById("help-role-pill");
    const helpPagePill = document.getElementById("help-page-pill");
    const helpSectionArticles = Array.from(document.querySelectorAll("#help-sections [data-help-section]"));
    const positionFieldScopeCountEl = document.getElementById("position-field-scope-count");
    const positionFieldScopeTitleEl = document.getElementById("position-field-scope-title");
    const positionFieldScopeSubtitleEl = document.getElementById("position-field-scope-subtitle");
    const positionFieldScopeCurrentEl = document.getElementById("position-field-scope-current");
    const positionFieldScopeCurrentNoteEl = document.getElementById("position-field-scope-current-note");
    const positionFieldScopeSelectEl = document.getElementById("position-field-scope-select");
    const positionFieldScopeNewPositionEl = document.getElementById("position-field-scope-new-position");
    const positionFieldScopeSalesEl = document.getElementById("position-field-scope-sales");
    const positionFieldScopeProjectTypesEl = document.getElementById("position-field-scope-project-types");
    const positionFieldScopeServiceModesEl = document.getElementById("position-field-scope-service-modes");
    const positionFieldScopeItemTypesEl = document.getElementById("position-field-scope-item-types");
    const positionFieldScopeStatusEl = document.getElementById("position-field-scope-status");
    const positionFieldScopeSummaryEl = document.getElementById("position-field-scope-summary");
    const createPositionFieldScopeButton = document.getElementById("create-position-field-scope");
    const copyPositionFieldScopeButton = document.getElementById("copy-position-field-scope");
    const savePositionFieldScopeButton = document.getElementById("save-position-field-scope");
    const deletePositionFieldScopeButton = document.getElementById("delete-position-field-scope");
    const reloadPositionFieldScopeButton = document.getElementById("reload-position-field-scope");
    const localAccountUsernameEl = document.getElementById("local-account-username");
    const localAccountDisplayNameEl = document.getElementById("local-account-display-name");
    const localAccountPositionMultiselectEl = document.getElementById("local-account-position-multiselect");
    const localAccountPositionTriggerEl = document.getElementById("local-account-position-trigger");
    const localAccountPositionSummaryEl = document.getElementById("local-account-position-summary");
    const localAccountPositionMenuEl = document.getElementById("local-account-position-menu");
    const localAccountPositionOptionsBox = document.getElementById("local-account-position-options");
    const localAccountDepartmentSelectEl = document.getElementById("local-account-department-select");
    const localAccountNewDepartmentEl = document.getElementById("local-account-new-department");
    const addLocalAccountDepartmentButton = document.getElementById("add-local-account-department");
    const localAccountPasswordEl = document.getElementById("local-account-password");
    const localAccountEnabledEl = document.getElementById("local-account-enabled");
    const localAccountIsAdminEl = document.getElementById("local-account-is-admin");
    const localAccountIsDepartmentAdminEl = document.getElementById("local-account-is-department-admin");
    const localAccountShowInDepartmentScheduleEl = document.getElementById("local-account-show-in-department-schedule");
    const localAccountsBody = document.getElementById("local-accounts-body");
    const localAccountStatus = document.getElementById("local-account-status");
    const adminUsersBody = document.getElementById("admin-users-body");
    const adminUsersStatus = document.getElementById("admin-users-status");
    const departmentDirectoryDepartmentEl = document.getElementById("department-directory-department");
    const departmentDirectoryLookupNameEl = document.getElementById("department-directory-lookup-name");
    const addDepartmentDirectoryEntryButton = document.getElementById("add-department-directory-entry");
    const reloadDepartmentDirectoryButton = document.getElementById("reload-department-directory");
    const departmentDirectoryOverviewEl = document.getElementById("department-directory-overview");
    const departmentDirectoryBody = document.getElementById("department-directory-body");
    const departmentDirectoryStatus = document.getElementById("department-directory-status");
    const dingtalkEnabledEl = document.getElementById("dingtalk-enabled");
    const dingtalkAutoLoginEl = document.getElementById("dingtalk-auto-login");
    const dingtalkClientIdEl = document.getElementById("dingtalk-client-id");
    const dingtalkClientSecretEl = document.getElementById("dingtalk-client-secret");
    const dingtalkCorpIdEl = document.getElementById("dingtalk-corp-id");
    const dingtalkRedirectBaseUrlEl = document.getElementById("dingtalk-redirect-base-url");
    const dingtalkCallbackUrlEl = document.getElementById("dingtalk-callback-url");
    const dingtalkConfigStatus = document.getElementById("dingtalk-config-status");
    const dingtalkIdentitiesBody = document.getElementById("dingtalk-identities-body");
    const dingtalkIdentitiesStatus = document.getElementById("dingtalk-identities-status");
    let adminUsers = [];
    let localAccounts = [];
    let localAccountPositionOptions = [];
    let localAccountDepartmentOptions = [];
    let isDepartmentDirectoryBusy = false;
    let positionFieldScopes = {};
    let currentPositionFieldScopePosition = "";
    let adminPageVerified = false;
    let currentUiSettings = window.__bootUiSettings || {};
    let visualSettingsAutosaveTimer = null;
    let isBackgroundSettingsOpen = false;
    let isHelpOverlayOpen = false;
    let activeHelpSectionKey = "";
    const VISUAL_SETTINGS_AUTOSAVE_DELAY_MS = 260;
    const MAX_BACKGROUND_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
    const THEME_PREFERENCE_STORAGE_KEY = "daily_planner_theme_preference";
    const BING_DAILY_BACKGROUND_PATH = "/api/backgrounds/bing-daily";
    const AUTO_THEME_DAY_START_HOUR = 6;
    const AUTO_THEME_NIGHT_START_HOUR = 19;
    const CURRENT_HELP_PAGE_KEY = "admin";
    const HELP_SECTION_META = {
      user: { label: "用户页面" },
      department: { label: "日程管理" },
      admin: { label: "管理员后台" },
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

    function normalizeLines(text) {
      return String(text || "").split(/\\r?\\n/).map((v) => v.trim()).filter(Boolean);
    }
    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }
    function setMessage(target, text, isError) {
      target.textContent = text || "";
      target.style.color = isError ? "var(--danger)" : "var(--ink)";
    }
    function setAuthInfoText(text) {
      if (authInfo) {
        authInfo.textContent = text || "";
      }
    }
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
        applyVisualSettings(currentUiSettings);
        scheduleAutoThemeRefresh();
      }, getNextAutoThemeSwitchDelay());
    }
    function setBackgroundSettingsOpen(isOpen) {
      isBackgroundSettingsOpen = Boolean(isOpen);
      backgroundSettingsMenu.hidden = !isBackgroundSettingsOpen;
      backgroundSettingsButton.setAttribute("aria-expanded", isBackgroundSettingsOpen ? "true" : "false");
    }
    function normalizeUiSettings(settings) {
      const source = settings && typeof settings === "object" ? settings : {};
      const numeric = Number(source.region_opacity);
      return {
        background_image: typeof source.background_image === "string" ? source.background_image : "",
        background_mode: ["cover", "contain", "repeat"].includes(source.background_mode) ? source.background_mode : "cover",
        region_opacity: Number.isFinite(numeric) ? Math.min(1, Math.max(0.25, Math.round(numeric * 100) / 100)) : 0.94,
      };
    }
    function formatOpacityPercent(value) {
      return `${Math.round(Number(value || 0) * 100)}%`;
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
    function applyVisualSettings(settings) {
      currentUiSettings = normalizeUiSettings(settings);
      if (typeof window.__applyShellVisualSettings === "function") {
        window.__bootUiSettings = window.__applyShellVisualSettings(currentUiSettings);
        currentUiSettings = normalizeUiSettings(window.__bootUiSettings);
      }
      const theme = document.body.dataset.theme === "dark" ? "dark" : "light";
      themeToggleButton.textContent = theme === "dark" ? "白天模式" : "黑夜模式";
      themeToggleButton.setAttribute("aria-label", theme === "dark" ? "切换到白天模式" : "切换到黑夜模式");
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
    async function saveVisualSettings() {
      try {
        const response = await fetch("/api/ui-settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(currentUiSettings),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存界面设置失败");
        }
        applyVisualSettings(data.settings || currentUiSettings);
      } catch (error) {
        // Keep the last-applied visual settings if the save fails.
      }
    }
    function scheduleVisualSettingsSave() {
      window.clearTimeout(visualSettingsAutosaveTimer);
      visualSettingsAutosaveTimer = window.setTimeout(() => {
        visualSettingsAutosaveTimer = null;
        saveVisualSettings();
      }, VISUAL_SETTINGS_AUTOSAVE_DELAY_MS);
    }
    function handleBackgroundImageSelection(file) {
      if (!file || !file.type.startsWith("image/") || file.size > MAX_BACKGROUND_IMAGE_SIZE_BYTES) {
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: String(reader.result || "") });
        applyVisualSettings(currentUiSettings);
        scheduleVisualSettingsSave();
      };
      reader.readAsDataURL(file);
    }
    function getInitialAuthenticatedUser() {
      if (!initialAdminAuthState || !initialAdminAuthState.authenticated || !initialAdminAuthState.user) {
        return null;
      }
      return initialAdminAuthState.user;
    }
    function getInitialAdminUser() {
      const user = getInitialAuthenticatedUser();
      if (!user || String(user.role || "") !== "admin") {
        return null;
      }
      return user;
    }
    function formatAdminIdentity(user) {
      if (!user) {
        return "";
      }
      return `${user.display_name || user.user_id}（${user.user_id}）`;
    }
    function setAdminIdentityText(user) {
      setAuthInfoText(`当前登录：${formatAdminIdentity(user)} · 已进入管理后台`);
    }
    function getAdminLoginPromptText() {
      const user = getInitialAuthenticatedUser();
      if (!user) {
        return "当前登录：未登录";
      }
      const roleText = String(user.role || "") === "admin" ? "管理员" : "普通账号";
      return `当前登录：${formatAdminIdentity(user)} · ${roleText}`;
    }
    function isAdminPageVerified() {
      return adminPageVerified;
    }
    function setAdminPageVerified(verified) {
      adminPageVerified = Boolean(verified);
      renderHelpDocs(activeHelpSectionKey);
    }
    function getHelpRoleLabel() {
      const user = getInitialAuthenticatedUser();
      if (!user) {
        return "未登录";
      }
      if (String(user.role || "") === "admin") {
        return "系统管理员";
      }
      if (Boolean(user.is_department_admin)) {
        return "部门管理员";
      }
      return "普通用户";
    }
    function getAllowedHelpSectionKeys() {
      const user = getInitialAuthenticatedUser();
      const sections = ["user"];
      if (user) {
        sections.push("department");
      }
      if (isAdminPageVerified()) {
        sections.push("admin");
      }
      return sections.filter((sectionKey, index, list) => list.indexOf(sectionKey) === index);
    }
    function getDefaultHelpSectionKey(allowedKeys) {
      if (allowedKeys.includes(CURRENT_HELP_PAGE_KEY)) {
        return CURRENT_HELP_PAGE_KEY;
      }
      return allowedKeys[0] || "user";
    }
    function renderHelpDocs(preferredKey = "") {
      const allowedKeys = getAllowedHelpSectionKeys();
      const nextSectionKey = allowedKeys.includes(preferredKey)
        ? preferredKey
        : (allowedKeys.includes(activeHelpSectionKey) ? activeHelpSectionKey : getDefaultHelpSectionKey(allowedKeys));
      activeHelpSectionKey = nextSectionKey;
      if (helpRolePill) {
        helpRolePill.textContent = `当前身份：${getHelpRoleLabel()}`;
      }
      if (helpPagePill) {
        const currentPageMeta = HELP_SECTION_META[CURRENT_HELP_PAGE_KEY] || HELP_SECTION_META.admin;
        helpPagePill.textContent = `当前页面：${currentPageMeta.label}`;
      }
      if (helpTabList) {
        helpTabList.textContent = "";
        allowedKeys.forEach((sectionKey) => {
          const sectionEl = helpSectionArticles.find((item) => item.dataset.helpSection === sectionKey);
          const label = String(
            sectionEl && sectionEl.dataset.helpTabLabel
            || HELP_SECTION_META[sectionKey] && HELP_SECTION_META[sectionKey].label
            || sectionKey
          ).trim();
          const button = document.createElement("button");
          button.type = "button";
          button.className = `help-tab${sectionKey === activeHelpSectionKey ? " is-active" : ""}`;
          button.textContent = label;
          button.setAttribute("role", "tab");
          button.setAttribute("aria-selected", sectionKey === activeHelpSectionKey ? "true" : "false");
          button.addEventListener("click", () => {
            renderHelpDocs(sectionKey);
          });
          helpTabList.appendChild(button);
        });
      }
      helpSectionArticles.forEach((sectionEl) => {
        const sectionKey = String(sectionEl.dataset.helpSection || "").trim();
        const visible = allowedKeys.includes(sectionKey) && sectionKey === activeHelpSectionKey;
        sectionEl.hidden = !visible;
        sectionEl.setAttribute("aria-hidden", visible ? "false" : "true");
      });
    }
    function openHelpOverlay(preferredKey = "") {
      isHelpOverlayOpen = true;
      helpOverlay.hidden = false;
      renderHelpDocs(preferredKey);
      window.setTimeout(() => {
        const activeButton = helpTabList.querySelector(".help-tab.is-active") || helpOverlayCloseButton;
        if (activeButton && typeof activeButton.focus === "function") {
          activeButton.focus();
        }
      }, 0);
    }
    function closeHelpOverlay() {
      isHelpOverlayOpen = false;
      helpOverlay.hidden = true;
    }
    function showAdminCheckingView() {
      document.body.classList.add("admin-auth-state");
      adminContent.hidden = true;
      loginCard.hidden = true;
      adminAccountButton.hidden = true;
      adminLogoutButton.hidden = true;
      adminDepartmentPageButton.hidden = false;
      adminUserPageButton.hidden = false;
      closeAdminAccountOverlay();
      setAuthInfoText("正在校验当前登录状态...");
    }
    function showAdminLoginView() {
      document.body.classList.add("admin-auth-state");
      adminContent.hidden = true;
      loginCard.hidden = false;
      adminAccountButton.hidden = true;
      adminLogoutButton.hidden = !getInitialAuthenticatedUser();
      adminDepartmentPageButton.hidden = false;
      adminUserPageButton.hidden = false;
      closeAdminAccountOverlay();
      setAuthInfoText(getAdminLoginPromptText());
      resetLocalAccountForm();
    }
    function normalizeOptionListForUi(options) {
      const list = Array.isArray(options) ? options : [];
      const seen = new Set();
      return list
        .map((item) => String(item || "").trim())
        .filter((item) => item)
        .filter((item) => {
          const key = item.toLowerCase();
          if (seen.has(key)) {
            return false;
          }
          seen.add(key);
          return true;
        });
    }
    function parseOptionConfigText(text) {
      return normalizeOptionListForUi(
        String(text || "")
          .split(/[,\\n，]/)
          .map((item) => String(item || "").trim())
          .filter(Boolean)
      );
    }
    function formatOptionConfigText(options) {
      return normalizeOptionListForUi(options).join(",");
    }
    function getPositionFieldScopeInputValueMap() {
      return {
        sales: parseOptionConfigText(positionFieldScopeSalesEl.value),
        project_types: parseOptionConfigText(positionFieldScopeProjectTypesEl.value),
        service_modes: parseOptionConfigText(positionFieldScopeServiceModesEl.value),
        item_types: parseOptionConfigText(positionFieldScopeItemTypesEl.value),
      };
    }
    function normalizePositionFieldScopeMapForUi(scopes) {
      const source = scopes && typeof scopes === "object" ? scopes : {};
      const normalized = {};
      localAccountPositionOptions.forEach((position) => {
        const rawScope = source[position];
        if (!rawScope || typeof rawScope !== "object") {
          return;
        }
        const scope = {
          sales: normalizeOptionListForUi(rawScope.sales || []),
          project_types: normalizeOptionListForUi(rawScope.project_types || []),
          service_modes: normalizeOptionListForUi(rawScope.service_modes || []),
          item_types: normalizeOptionListForUi(rawScope.item_types || []),
        };
        if (scope.sales.length || scope.project_types.length || scope.service_modes.length || scope.item_types.length) {
          normalized[position] = scope;
        }
      });
      return normalized;
    }
    function getCurrentPositionFieldScopePosition() {
      return String(currentPositionFieldScopePosition || "").trim();
    }
    function fillPositionFieldScopeForm(position) {
      const scope = position && positionFieldScopes[position] ? positionFieldScopes[position] : {};
      positionFieldScopeSalesEl.value = formatOptionConfigText(scope.sales || []);
      positionFieldScopeProjectTypesEl.value = formatOptionConfigText(scope.project_types || []);
      positionFieldScopeServiceModesEl.value = formatOptionConfigText(scope.service_modes || []);
      positionFieldScopeItemTypesEl.value = formatOptionConfigText(scope.item_types || []);
    }
    function getPositionFieldScopeCountText() {
      if (!localAccountPositionOptions.length) {
        return "暂无岗位";
      }
      return `${localAccountPositionOptions.length} 个岗位`;
    }
    function renderPositionFieldScopeSelect() {
      const currentPosition = getCurrentPositionFieldScopePosition();
      if (!localAccountPositionOptions.length) {
        positionFieldScopeSelectEl.innerHTML = '<option value="">请先新增岗位</option>';
        positionFieldScopeSelectEl.value = "";
        return;
      }
      positionFieldScopeSelectEl.innerHTML = localAccountPositionOptions.map((position) => {
        return `<option value="${escapeHtml(position)}">${escapeHtml(position)}</option>`;
      }).join("");
      positionFieldScopeSelectEl.value = localAccountPositionOptions.includes(currentPosition)
        ? currentPosition
        : (localAccountPositionOptions[0] || "");
    }
    function updatePositionFieldScopeEditorState() {
      const currentPosition = getCurrentPositionFieldScopePosition();
      const hasSelection = Boolean(currentPosition && localAccountPositionOptions.includes(currentPosition));
      positionFieldScopeCurrentEl.textContent = hasSelection ? `当前岗位：${currentPosition}` : "当前岗位：未选择";
      positionFieldScopeCurrentNoteEl.textContent = hasSelection
        ? "修改完成后点击“保存当前岗位配置”即可生效。"
        : "请先选择岗位，再到下方维护该岗位可用的字段。";
      positionFieldScopeCountEl.textContent = getPositionFieldScopeCountText();
      positionFieldScopeTitleEl.textContent = hasSelection ? `岗位字段限制：${currentPosition}` : "按岗位限制可选字段";
      positionFieldScopeSubtitleEl.textContent = hasSelection
        ? "修改后点击“保存当前岗位配置”即可生效；一个用户勾选多个岗位时，可选项按岗位取并集。"
        : "请先选择岗位，再配置该岗位可用的销售、项目类型、服务方式、服务类型。";
      positionFieldScopeSelectEl.disabled = !localAccountPositionOptions.length;
      [
        positionFieldScopeSalesEl,
        positionFieldScopeProjectTypesEl,
        positionFieldScopeServiceModesEl,
        positionFieldScopeItemTypesEl,
        copyPositionFieldScopeButton,
        savePositionFieldScopeButton,
        deletePositionFieldScopeButton,
      ].forEach((element) => {
        element.disabled = !hasSelection;
      });
    }
    function setCurrentPositionFieldScopePosition(position, options = {}) {
      const normalizedPosition = String(position || "").trim();
      const nextPosition = localAccountPositionOptions.includes(normalizedPosition)
        ? normalizedPosition
        : (localAccountPositionOptions[0] || "");
      currentPositionFieldScopePosition = nextPosition;
      if (nextPosition) {
        fillPositionFieldScopeForm(nextPosition);
      } else {
        positionFieldScopeSalesEl.value = "";
        positionFieldScopeProjectTypesEl.value = "";
        positionFieldScopeServiceModesEl.value = "";
        positionFieldScopeItemTypesEl.value = "";
      }
      renderPositionFieldScopeSelect();
      renderPositionFieldScopeSummary();
      updatePositionFieldScopeEditorState();
      if (options.clearStatus !== false) {
        setMessage(positionFieldScopeStatusEl, "", false);
      }
    }
    function syncPositionFieldScopePayload(data, preferredPosition = "") {
      const selectedLocalPositions = getSelectedLocalAccountPositions();
      localAccountPositionOptions = normalizeOptionListForUi(data.positions || localAccountPositionOptions);
      positionFieldScopes = normalizePositionFieldScopeMapForUi(data.scopes || {});
      renderLocalAccountPositionOptions(selectedLocalPositions.filter((item) => localAccountPositionOptions.includes(item)));
      const currentPosition = preferredPosition || getCurrentPositionFieldScopePosition();
      setCurrentPositionFieldScopePosition(currentPosition, { clearStatus: false });
      positionFieldScopeNewPositionEl.value = "";
    }
    function renderPositionFieldScopeSummary() {
      if (!localAccountPositionOptions.length) {
        positionFieldScopeSummaryEl.innerHTML = '<div class="option-empty" style="padding:12px;">请先新增岗位，再维护岗位关联规则。</div>';
        return;
      }
      positionFieldScopeSummaryEl.innerHTML = `
        <table>
          <thead>
            <tr><th>岗位</th><th>销售字段</th><th>项目类型字段</th><th>服务方式字段</th><th>服务类型字段</th></tr>
          </thead>
          <tbody>
            ${localAccountPositionOptions.map((position) => {
              const scope = positionFieldScopes[position] || {};
              const renderValues = (values) => {
                const list = normalizeOptionListForUi(values || []);
                return list.length ? escapeHtml(list.join("、")) : '<span class="muted">未单独配置</span>';
              };
              return `<tr>
                <td>${escapeHtml(position)}</td>
                <td>${renderValues(scope.sales)}</td>
                <td>${renderValues(scope.project_types)}</td>
                <td>${renderValues(scope.service_modes)}</td>
                <td>${renderValues(scope.item_types)}</td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      `;
    }
    function getSelectedLocalAccountPositions() {
      return Array.from(localAccountPositionOptionsBox.querySelectorAll('input[type="checkbox"]:checked'))
        .map((input) => String(input.value || "").trim())
        .filter(Boolean);
    }
    function formatLocalAccountPositionSummary(selectedPositions = []) {
      const normalized = normalizeOptionListForUi(selectedPositions);
      if (!localAccountPositionOptions.length) {
        return "请先新增岗位";
      }
      if (!normalized.length) {
        return "请选择岗位";
      }
      if (normalized.length <= 2) {
        return normalized.join("、");
      }
      return `${normalized.slice(0, 2).join("、")} 等 ${normalized.length} 个岗位`;
    }
    function updateLocalAccountPositionSummary(selectedPositions = getSelectedLocalAccountPositions()) {
      localAccountPositionSummaryEl.textContent = formatLocalAccountPositionSummary(selectedPositions);
    }
    function setLocalAccountPositionMenuOpen(isOpen) {
      const canOpen = !localAccountPositionTriggerEl.disabled && localAccountPositionOptions.length > 0;
      const shouldOpen = Boolean(isOpen && canOpen);
      localAccountPositionMenuEl.hidden = !shouldOpen;
      localAccountPositionTriggerEl.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
      localAccountPositionMultiselectEl.classList.toggle("open", shouldOpen);
    }
    function getSelectedLocalAccountDepartment() {
      return String(localAccountDepartmentSelectEl.value || "").trim();
    }
    function renderLocalAccountPositionOptions(selectedPositions = []) {
      const selectedPositionSet = new Set(
        (Array.isArray(selectedPositions) ? selectedPositions : [selectedPositions])
          .map((item) => String(item || "").trim())
          .filter(Boolean)
      );
      if (!localAccountPositionOptions.length) {
        localAccountPositionOptionsBox.innerHTML = '<div class="local-account-position-empty">请先在上方字段管理中新增岗位。</div>';
        localAccountPositionTriggerEl.disabled = true;
        updateLocalAccountPositionSummary([]);
        setLocalAccountPositionMenuOpen(false);
        return;
      }
      localAccountPositionTriggerEl.disabled = false;
      localAccountPositionOptionsBox.innerHTML = localAccountPositionOptions.map((option) => {
        return `
          <label class="option-checkitem">
            <input type="checkbox" value="${escapeHtml(option)}"${selectedPositionSet.has(option) ? " checked" : ""}>
            <span>${escapeHtml(option)}</span>
          </label>
        `;
      }).join("");
      updateLocalAccountPositionSummary(Array.from(selectedPositionSet));
    }
    function renderLocalAccountDepartmentOptions(selectedDepartment = "") {
      const selectedValue = String(selectedDepartment || "").trim();
      const availableOptions = normalizeOptionListForUi(localAccountDepartmentOptions);
      if (!availableOptions.length) {
        localAccountDepartmentSelectEl.innerHTML = '<option value="">请先添加部门</option>';
        localAccountDepartmentSelectEl.value = "";
        return;
      }
      localAccountDepartmentSelectEl.innerHTML = [
        '<option value="">请选择所属部门</option>',
        ...availableOptions.map((option) => {
          return `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`;
        }),
      ].join("");
      localAccountDepartmentSelectEl.value = availableOptions.includes(selectedValue) ? selectedValue : "";
    }
    async function addLocalAccountDepartment() {
      const departmentName = String(localAccountNewDepartmentEl.value || "").trim();
      if (!departmentName) {
        setMessage(localAccountStatus, "请先填写要新增的所属部门。", true);
        return;
      }
      const existingDepartment = localAccountDepartmentOptions.find((item) => item.toLowerCase() === departmentName.toLowerCase());
      if (existingDepartment) {
        renderLocalAccountDepartmentOptions(existingDepartment);
        localAccountNewDepartmentEl.value = "";
        setMessage(localAccountStatus, `所属部门 ${existingDepartment} 已存在，已直接选中。`, false);
        return;
      }
      try {
        const response = await fetch("/api/admin/department-options", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ departments: [...localAccountDepartmentOptions, departmentName] }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "新增所属部门失败");
        }
        localAccountDepartmentOptions = normalizeOptionListForUi(data.options || []);
        renderLocalAccountDepartmentOptions(departmentName);
        localAccountNewDepartmentEl.value = "";
        await loadDepartmentDirectory(departmentName).catch(() => {});
        setMessage(localAccountStatus, `所属部门 ${departmentName} 已添加并选中。`, false);
      } catch (error) {
        setMessage(localAccountStatus, error.message || "新增所属部门失败", true);
      }
    }
    async function loadPositionFieldScopes() {
      const response = await fetch("/api/admin/position-field-scopes");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取岗位关联规则失败");
      }
      syncPositionFieldScopePayload(data);
      setMessage(positionFieldScopeStatusEl, `最近更新：${data.updated_at || "未记录"}`, false);
    }
    async function savePositionFieldScopes() {
      const selectedPosition = getCurrentPositionFieldScopePosition();
      if (!selectedPosition) {
        setMessage(positionFieldScopeStatusEl, "请先选择岗位。", true);
        return;
      }
      const nextScope = getPositionFieldScopeInputValueMap();
      const nextScopes = {
        ...(positionFieldScopes && typeof positionFieldScopes === "object" ? positionFieldScopes : {}),
      };
      if (nextScope.sales.length || nextScope.project_types.length || nextScope.service_modes.length || nextScope.item_types.length) {
        nextScopes[selectedPosition] = nextScope;
      } else {
        delete nextScopes[selectedPosition];
      }
      try {
        const response = await fetch("/api/admin/position-field-scopes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ positions: localAccountPositionOptions, scopes: nextScopes }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存岗位关联规则失败");
        }
        syncPositionFieldScopePayload(data, selectedPosition);
        await loadLocalAccounts().catch(() => {});
        setMessage(positionFieldScopeStatusEl, `岗位 ${selectedPosition} 的关联规则保存成功。`, false);
      } catch (error) {
        setMessage(positionFieldScopeStatusEl, error.message || "保存岗位关联规则失败", true);
      }
    }
    async function createPositionFieldScopePosition(copyCurrent = false) {
      const positionName = String(positionFieldScopeNewPositionEl.value || "").trim();
      if (!positionName) {
        setMessage(positionFieldScopeStatusEl, "请先填写要新增的岗位名称。", true);
        return;
      }
      if (localAccountPositionOptions.some((item) => item.toLowerCase() === positionName.toLowerCase())) {
        const existing = localAccountPositionOptions.find((item) => item.toLowerCase() === positionName.toLowerCase()) || positionName;
        setCurrentPositionFieldScopePosition(existing);
        setMessage(positionFieldScopeStatusEl, `岗位 ${existing} 已存在，已切换到该岗位。`, false);
        return;
      }
      const nextPositions = [...localAccountPositionOptions, positionName];
      const nextScopes = {
        ...(positionFieldScopes && typeof positionFieldScopes === "object" ? positionFieldScopes : {}),
      };
      if (copyCurrent) {
        const currentPosition = getCurrentPositionFieldScopePosition();
        if (!currentPosition) {
          setMessage(positionFieldScopeStatusEl, "请先选择一个已有岗位，再复制配置。", true);
          return;
        }
        const sourceScope = getPositionFieldScopeInputValueMap();
        if (sourceScope.sales.length || sourceScope.project_types.length || sourceScope.service_modes.length || sourceScope.item_types.length) {
          nextScopes[positionName] = sourceScope;
        }
      }
      try {
        const response = await fetch("/api/admin/position-field-scopes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ positions: nextPositions, scopes: nextScopes }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || (copyCurrent ? "复制岗位配置失败" : "新增岗位失败"));
        }
        syncPositionFieldScopePayload(data, positionName);
        await loadLocalAccounts().catch(() => {});
        setMessage(
          positionFieldScopeStatusEl,
          copyCurrent
            ? `已复制当前岗位配置到新岗位 ${positionName}。`
            : `岗位 ${positionName} 已新增，请继续填写该岗位的可选字段。`,
          false
        );
      } catch (error) {
        setMessage(positionFieldScopeStatusEl, error.message || (copyCurrent ? "复制岗位配置失败" : "新增岗位失败"), true);
      }
    }
    async function fetchAffectedUsersForPosition(position) {
      try {
        const response = await fetch("/api/admin/users");
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取受影响用户失败");
        }
        return (Array.isArray(data.users) ? data.users : []).filter((user) => {
          return Array.isArray(user.positions) && user.positions.includes(position);
        });
      } catch (error) {
        return localAccounts.filter((account) => Array.isArray(account.positions) && account.positions.includes(position));
      }
    }
    function buildDeletePositionConfirmText(position, affectedUsers) {
      const users = Array.isArray(affectedUsers) ? affectedUsers : [];
      const previewLines = users.slice(0, 8).map((user) => {
        const displayName = String(user.display_name || user.username || user.user_id || "未命名用户").trim();
        const userId = String(user.user_id || user.username || "").trim();
        return `- ${displayName}${userId ? `（${userId}）` : ""}`;
      });
      if (!previewLines.length) {
        previewLines.push("- 当前没有已关联该岗位的用户");
      }
      if (users.length > 8) {
        previewLines.push(`- 其余 ${users.length - 8} 个用户也会同步受影响`);
      }
      return [
        `确认删除岗位“${position}”吗？`,
        "",
        "删除后会同时处理：",
        "1. 删除该岗位的字段限制配置",
        "2. 从已关联用户身上移除这个岗位",
        "",
        `受影响用户：${users.length} 个`,
        ...previewLines,
        "",
        "确认继续删除吗？",
      ].join("\\n");
    }
    async function deletePositionFieldScopePosition() {
      const selectedPosition = getCurrentPositionFieldScopePosition();
      if (!selectedPosition) {
        setMessage(positionFieldScopeStatusEl, "请先选择要删除的岗位。", true);
        return;
      }
      if (localAccountPositionOptions.length <= 1) {
        setMessage(positionFieldScopeStatusEl, "至少保留一个岗位，无法删除最后一个岗位。", true);
        return;
      }
      const affectedUsers = await fetchAffectedUsersForPosition(selectedPosition);
      if (!window.confirm(buildDeletePositionConfirmText(selectedPosition, affectedUsers))) {
        return;
      }
      const nextPositions = localAccountPositionOptions.filter((item) => item !== selectedPosition);
      const nextScopes = { ...(positionFieldScopes || {}) };
      delete nextScopes[selectedPosition];
      try {
        const response = await fetch("/api/admin/position-field-scopes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ positions: nextPositions, scopes: nextScopes }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "删除岗位失败");
        }
        const preferredPosition = nextPositions[0] || "";
        syncPositionFieldScopePayload(data, preferredPosition);
        await loadLocalAccounts().catch(() => {});
        setMessage(positionFieldScopeStatusEl, `岗位 ${selectedPosition} 已删除。`, false);
      } catch (error) {
        setMessage(positionFieldScopeStatusEl, error.message || "删除岗位失败", true);
      }
    }
    function resetLocalAccountForm() {
      localAccountUsernameEl.value = "";
      localAccountDisplayNameEl.value = "";
      localAccountNewDepartmentEl.value = "";
      localAccountPasswordEl.value = "";
      localAccountEnabledEl.checked = true;
      localAccountIsAdminEl.checked = false;
      localAccountIsDepartmentAdminEl.checked = false;
      localAccountShowInDepartmentScheduleEl.checked = false;
      renderLocalAccountPositionOptions("");
      renderLocalAccountDepartmentOptions("");
      setMessage(localAccountStatus, "", false);
    }
    function fillLocalAccountForm(account) {
      const row = account || {};
      localAccountUsernameEl.value = row.username || "";
      localAccountDisplayNameEl.value = row.display_name || "";
      localAccountNewDepartmentEl.value = "";
      localAccountPasswordEl.value = "";
      localAccountEnabledEl.checked = row.enabled !== false;
      localAccountIsAdminEl.checked = Boolean(row.is_admin);
      localAccountIsDepartmentAdminEl.checked = Boolean(row.is_department_admin);
      localAccountShowInDepartmentScheduleEl.checked = Boolean(row.show_in_department_schedule);
      renderLocalAccountPositionOptions(row.positions || row.position || []);
      renderLocalAccountDepartmentOptions(row.department || "");
    }
    function buildDeleteLocalAccountConfirmText(account) {
      const row = account || {};
      const displayName = String(row.display_name || row.username || "").trim();
      const username = String(row.username || "").trim();
      const userId = String(row.user_id || "").trim();
      return [
        `确认彻底删除用户“${displayName || username || userId}”吗？`,
        "",
        "删除后会同时清空：",
        "1. 本地账号本身",
        "2. 历史填写记录与周计划",
        "3. 提示词、背景设置、钉钉 MCP 与发送配置",
        "4. 该用户导出的日志文件",
        "5. 登录会话与钉钉身份缓存",
        "",
        `账号：${username || "未设置"}`,
        `本地 userId：${userId || "未设置"}`,
        "",
        "此操作不可恢复，确认继续删除吗？",
      ].join("\\n");
    }
    function describeLocalAccountTemplate(label, templateName, source) {
      const resolvedName = String(templateName || "").trim();
      if (!resolvedName) {
        return `${label}：未选择`;
      }
      return source === "invalid"
        ? `${label}：${resolvedName}（不兼容）`
        : `${label}：${resolvedName}`;
    }
    function renderLocalAccountMcpSummary(row) {
      const summary = row && typeof row === "object" && row.dingtalk_mcp && typeof row.dingtalk_mcp === "object"
        ? row.dingtalk_mcp
        : {};
      const logMcpUrl = String(summary.log_mcp_url || "").trim();
      const directoryMcpUrl = String(summary.directory_mcp_url || "").trim();
      const dailyTemplateText = describeLocalAccountTemplate(
        "日报",
        summary.daily_template_name,
        String(summary.daily_template_source || "missing").trim() || "missing"
      );
      const weeklyTemplateText = describeLocalAccountTemplate(
        "周报",
        summary.weekly_template_name,
        String(summary.weekly_template_source || "missing").trim() || "missing"
      );
      const updatedAt = String(summary.updated_at || "").trim();
      return `
        <div class="mcp-config-cell">
          <div class="mcp-config-item">
            <div class="mcp-config-label">日志发送 MCP</div>
            <div class="mcp-config-value${logMcpUrl ? " is-code" : " is-empty"}">${escapeHtml(logMcpUrl || "未配置")}</div>
          </div>
          <div class="mcp-config-item">
            <div class="mcp-config-label">通讯录查询 MCP</div>
            <div class="mcp-config-value${directoryMcpUrl ? " is-code" : " is-empty"}">${escapeHtml(directoryMcpUrl || "未配置")}</div>
          </div>
          <div class="mcp-config-item">
            <div class="mcp-config-label">模板选择</div>
            <div class="mcp-config-value">${escapeHtml(`${dailyTemplateText} · ${weeklyTemplateText}`)}</div>
          </div>
          <div class="mcp-config-meta">MCP 配置时间：${escapeHtml(updatedAt || "未记录")}</div>
        </div>
      `;
    }
    async function deleteLocalAccount(account) {
      const row = account || {};
      const username = String(row.username || "").trim();
      if (!username) {
        setMessage(localAccountStatus, "未找到要删除的账号。", true);
        return;
      }
      if (!window.confirm(`确认删除账号“${username}”吗？`)) {
        return;
      }
      if (!window.confirm(buildDeleteLocalAccountConfirmText(row))) {
        return;
      }
      try {
        const response = await fetch(`/api/admin/local-accounts?username=${encodeURIComponent(username)}`, {
          method: "DELETE",
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "删除本地账号失败");
        }
        resetLocalAccountForm();
        await loadLocalAccounts();
        await loadAdminUsers().catch(() => {});
        await loadDepartmentDirectory().catch(() => {});
        setMessage(localAccountStatus, `账号 ${username} 已删除，对应历史数据和配置也已清理。`, false);
      } catch (error) {
        setMessage(localAccountStatus, error.message || "删除本地账号失败", true);
      }
    }
    function renderLocalAccounts(rows) {
      localAccounts = Array.isArray(rows) ? rows.slice() : [];
      if (!localAccounts.length) {
        localAccountsBody.innerHTML = '<tr><td colspan="10">暂无本地账号</td></tr>';
        return;
      }
      localAccountsBody.innerHTML = localAccounts.map((row) => {
        const status = row.enabled ? "启用" : "停用";
        const scheduleVisibility = row.show_in_department_schedule ? "展示" : "不展示";
        const roleList = [];
        if (row.is_admin) {
          roleList.push("管理员");
        }
        if (row.is_department_admin) {
          roleList.push("部门管理员");
        }
        if (!roleList.length) {
          roleList.push("普通用户");
        }
        const role = roleList.join(" / ");
        const position = Array.isArray(row.positions) && row.positions.length
          ? row.positions.join("、")
          : (String(row.position || "").trim() || "未设置");
        const department = String(row.department || "").trim() || "未设置";
        return `<tr>
          <td>${escapeHtml(row.username || "")}</td>
          <td>${escapeHtml(row.display_name || row.username || "")}</td>
          <td>${escapeHtml(position)}</td>
          <td>${escapeHtml(department)}</td>
          <td><span class="code">${escapeHtml(row.user_id || "")}</span></td>
          <td>${status}</td>
          <td>${role}</td>
          <td>${scheduleVisibility}</td>
          <td>${escapeHtml(row.updated_at || "") || "未记录"}</td>
          <td>
            <div class="local-account-actions">
              <button type="button" class="secondary local-account-edit" data-username="${escapeHtml(row.username || "")}">载入</button>
              <button type="button" class="secondary danger local-account-delete" data-username="${escapeHtml(row.username || "")}">删除</button>
            </div>
          </td>
        </tr>`;
      }).join("");
    }
    function renderAdminUsers(rows) {
      adminUsers = Array.isArray(rows) ? rows.slice() : [];
      if (!adminUsers.length) {
        adminUsersBody.innerHTML = '<tr><td colspan="3">暂无用户</td></tr>';
        return;
      }
      adminUsersBody.innerHTML = adminUsers.map((row) => {
        return `<tr>
          <td>${escapeHtml(row.display_name || row.user_id || "")}</td>
          <td><span class="code">${escapeHtml(row.user_id || "")}</span></td>
          <td>${renderLocalAccountMcpSummary(row)}</td>
        </tr>`;
      }).join("");
    }
    async function loadLocalAccounts() {
      const response = await fetch("/api/admin/local-accounts");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取本地账号失败");
      }
      const selectedDepartment = getSelectedLocalAccountDepartment();
      localAccountDepartmentOptions = normalizeOptionListForUi(data.department_options || []);
      renderLocalAccountDepartmentOptions(selectedDepartment);
      renderLocalAccounts(data.accounts || []);
      setMessage(localAccountStatus, `已加载 ${Array.isArray(data.accounts) ? data.accounts.length : 0} 个本地账号。`, false);
    }
    async function loadAdminUsers() {
      const response = await fetch("/api/admin/users");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取用户 MCP 失败");
      }
      renderAdminUsers(data.users || []);
      setMessage(adminUsersStatus, `已加载 ${Array.isArray(data.users) ? data.users.length : 0} 个用户。`, false);
    }
    function setDepartmentDirectoryBusy(isBusy, buttonText) {
      isDepartmentDirectoryBusy = Boolean(isBusy);
      departmentDirectoryDepartmentEl.disabled = isDepartmentDirectoryBusy;
      departmentDirectoryLookupNameEl.disabled = isDepartmentDirectoryBusy;
      addDepartmentDirectoryEntryButton.disabled = isDepartmentDirectoryBusy;
      reloadDepartmentDirectoryButton.disabled = isDepartmentDirectoryBusy;
      addDepartmentDirectoryEntryButton.textContent = buttonText || "查询并加入当前部门";
    }
    function renderDepartmentDirectoryDepartmentOptions(options, selectedDepartment) {
      const availableOptions = normalizeOptionListForUi(options);
      const selectedValue = String(selectedDepartment || "").trim();
      departmentDirectoryDepartmentEl.innerHTML = [
        '<option value="">请选择所属部门</option>',
        ...availableOptions.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`),
      ].join("");
      departmentDirectoryDepartmentEl.value = availableOptions.includes(selectedValue) ? selectedValue : "";
    }
    function buildDepartmentDirectorySyncedByText(row) {
      const displayName = String(row && row.synced_by_display_name || "").trim();
      const userId = String(row && row.synced_by_user_id || "").trim();
      if (!displayName && !userId) {
        return "未记录";
      }
      return displayName && userId && displayName !== userId
        ? `${displayName}（${userId}）`
        : (displayName || userId);
    }
    function renderDepartmentDirectoryOverview(rows, selectedDepartment) {
      const items = Array.isArray(rows) ? rows : [];
      const currentDepartment = String(selectedDepartment || "").trim();
      if (!items.length) {
        departmentDirectoryOverviewEl.innerHTML = '<div class="department-directory-empty">暂无可用部门，请先在“本地账号管理”里维护所属部门。</div>';
        return;
      }
      departmentDirectoryOverviewEl.innerHTML = items.map((row) => {
        const department = String(row && row.department || "").trim() || "未设置部门";
        const isActive = currentDepartment && department === currentDepartment;
        return `
          <article class="department-directory-card${isActive ? " is-active" : ""}" data-department="${escapeHtml(department)}">
            <div class="department-directory-card-top">
              <div class="department-directory-card-title">${escapeHtml(department)}</div>
              <span class="tag-pill">${escapeHtml(String(row && row.record_count || 0))} 条</span>
            </div>
            <div class="department-directory-meta">唯一姓名：${escapeHtml(String(row && row.unique_name_count || 0))} · 同名组数：${escapeHtml(String(row && row.duplicate_name_count || 0))}</div>
            <div class="department-directory-meta">最近更新：${escapeHtml(String(row && row.updated_at || "").trim() || "未同步")}</div>
            <div class="department-directory-meta">最近同步人：${escapeHtml(buildDepartmentDirectorySyncedByText(row))}</div>
          </article>
        `;
      }).join("");
    }
    function renderDepartmentDirectoryEntries(rows, selectedDepartment) {
      const items = Array.isArray(rows) ? rows : [];
      const currentDepartment = String(selectedDepartment || "").trim();
      if (!currentDepartment) {
        departmentDirectoryBody.innerHTML = '<tr><td colspan="4">暂无可用部门，请先在“本地账号管理”里维护所属部门。</td></tr>';
        return;
      }
      if (!items.length) {
        departmentDirectoryBody.innerHTML = `<tr><td colspan="4">${escapeHtml(currentDepartment)} 暂无已同步人员。</td></tr>`;
        return;
      }
      departmentDirectoryBody.innerHTML = items.map((row) => `
        <tr>
          <td>${escapeHtml(String(row && row.name || "").trim())}</td>
          <td><span class="code">${escapeHtml(String(row && row.user_id || "").trim())}</span></td>
          <td>${escapeHtml(buildDepartmentDirectorySyncedByText(row))}</td>
          <td>${escapeHtml(String(row && row.updated_at || "").trim() || "未记录")}</td>
        </tr>
      `).join("");
    }
    async function loadDepartmentDirectory(requestedDepartment = "") {
      const currentDepartment = String(requestedDepartment || departmentDirectoryDepartmentEl.value || "").trim();
      setDepartmentDirectoryBusy(true, "查询并加入当前部门");
      try {
        const query = currentDepartment ? `?department=${encodeURIComponent(currentDepartment)}` : "";
        const response = await fetch(`/api/admin/department-directory-cache${query}`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取部门共享通讯录失败");
        }
        renderDepartmentDirectoryDepartmentOptions(data.departments || [], data.selected_department || "");
        renderDepartmentDirectoryOverview(data.overview || [], data.selected_department || "");
        renderDepartmentDirectoryEntries(data.entries || [], data.selected_department || "");
        if (String(data.selected_department || "").trim()) {
          setMessage(
            departmentDirectoryStatus,
            `已加载 ${String(data.selected_department || "").trim()} 部门共享通讯录，共 ${Array.isArray(data.entries) ? data.entries.length : 0} 条记录。`,
            false
          );
        } else {
          setMessage(departmentDirectoryStatus, "暂无可用部门，请先在本地账号中配置所属部门。", false);
        }
      } catch (error) {
        renderDepartmentDirectoryOverview([], "");
        renderDepartmentDirectoryEntries([], "");
        setMessage(departmentDirectoryStatus, error.message || "读取部门共享通讯录失败", true);
      } finally {
        setDepartmentDirectoryBusy(false, "查询并加入当前部门");
      }
    }
    async function addDepartmentDirectoryEntry() {
      const selectedDepartment = String(departmentDirectoryDepartmentEl.value || "").trim();
      const targetName = String(departmentDirectoryLookupNameEl.value || "").trim();
      if (!selectedDepartment) {
        setMessage(departmentDirectoryStatus, "请先选择要维护的所属部门。", true);
        return;
      }
      if (!targetName) {
        setMessage(departmentDirectoryStatus, "请先输入要查询的姓名。", true);
        return;
      }
      setDepartmentDirectoryBusy(true, "查询中...");
      setMessage(departmentDirectoryStatus, `正在使用当前管理员账号查询 ${targetName} 并写入 ${selectedDepartment} 部门共享通讯录，请稍候...`, false);
      try {
        const response = await fetch("/api/admin/department-directory-cache", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ department: selectedDepartment, name: targetName }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "补充共享通讯录失败");
        }
        renderDepartmentDirectoryDepartmentOptions(data.departments || [], data.selected_department || "");
        renderDepartmentDirectoryOverview(data.overview || [], data.selected_department || "");
        renderDepartmentDirectoryEntries(data.entries || [], data.selected_department || "");
        const addedEntry = data.added_entry || {};
        departmentDirectoryLookupNameEl.value = "";
        setMessage(
          departmentDirectoryStatus,
          `已将 ${String(addedEntry.name || targetName).trim() || targetName}（${String(addedEntry.user_id || "").trim() || "未返回 userId"}）加入 ${String(data.selected_department || selectedDepartment).trim()} 部门共享通讯录。`,
          false
        );
      } catch (error) {
        setMessage(departmentDirectoryStatus, error.message || "补充共享通讯录失败", true);
      } finally {
        setDepartmentDirectoryBusy(false, "查询并加入当前部门");
      }
    }
    async function saveLocalAccount() {
      const username = String(localAccountUsernameEl.value || "").trim();
      if (!username) {
        setMessage(localAccountStatus, "请先填写账号。", true);
        return;
      }
      const payload = {
        username,
        display_name: String(localAccountDisplayNameEl.value || "").trim(),
        positions: getSelectedLocalAccountPositions(),
        department: getSelectedLocalAccountDepartment(),
        password: String(localAccountPasswordEl.value || ""),
        enabled: localAccountEnabledEl.checked,
        is_admin: localAccountIsAdminEl.checked,
        is_department_admin: localAccountIsDepartmentAdminEl.checked,
        show_in_department_schedule: localAccountShowInDepartmentScheduleEl.checked,
      };
      if (!payload.positions.length) {
        setMessage(localAccountStatus, "请至少选择一个岗位。", true);
        return;
      }
      if (!payload.department) {
        setMessage(localAccountStatus, "请先选择所属部门。", true);
        return;
      }
      try {
        const response = await fetch("/api/admin/local-accounts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存本地账号失败");
        }
        fillLocalAccountForm(data.account || payload);
        localAccountPasswordEl.value = "";
        localAccountNewDepartmentEl.value = "";
        await loadLocalAccounts();
        await loadAdminUsers().catch(() => {});
        await loadDepartmentDirectory(payload.department).catch(() => {});
        await loadAccessControl().catch(() => {});
        await loadAdminAccountInfo().catch(() => {});
        setMessage(localAccountStatus, `本地账号 ${username} 保存成功。`, false);
      } catch (error) {
        setMessage(localAccountStatus, error.message || "保存本地账号失败", true);
      }
    }
    function getCallbackBaseUrlPreview() {
      const configuredBaseUrl = String(dingtalkRedirectBaseUrlEl.value || "").trim();
      return configuredBaseUrl || window.location.origin;
    }
    function updateDingtalkCallbackPreview() {
      const baseUrl = getCallbackBaseUrlPreview();
      dingtalkCallbackUrlEl.textContent = `${baseUrl.replace(/\/$/, "")}/api/auth/dingtalk/callback`;
    }
    function renderDingtalkIdentities(rows) {
      if (!Array.isArray(rows) || !rows.length) {
        dingtalkIdentitiesBody.innerHTML = '<tr><td colspan="6">暂无钉钉扫码用户</td></tr>';
        return;
      }
      dingtalkIdentitiesBody.innerHTML = rows.map((row) => {
        const displayName = row.display_name || row.nick || row.local_user_id || "";
        return `<tr>
          <td>${escapeHtml(displayName)}</td>
          <td><span class="code">${escapeHtml(row.local_user_id || "")}</span></td>
          <td>${escapeHtml(row.corp_id || "") || "未回传"}</td>
          <td>${escapeHtml(row.mobile || "") || "未回传"}</td>
          <td>${escapeHtml(row.role || "user")}</td>
          <td>${escapeHtml(row.updated_at || "") || "未记录"}</td>
        </tr>`;
      }).join("");
    }
    async function loadAccessControl() {
      const response = await fetch("/api/admin/access-control");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取权限配置失败");
      }
      loginUsersEl.value = (data.login_allowed_users || []).join("\\n");
      adminUsersEl.value = (data.admin_allowed_users || []).join("\\n");
      setMessage(accessStatus, `最近更新：${data.updated_at || "未记录"}`, false);
    }
    async function loadAdminAccountInfo() {
      const response = await fetch("/api/admin/account");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取管理员账号失败");
      }
      adminUsernameEl.value = data.username || "admin";
      document.getElementById("login-username").value = data.username || "admin";
    }
    async function loadDingtalkConfig() {
      const response = await fetch("/api/admin/dingtalk-oauth-config");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取钉钉配置失败");
      }
      dingtalkEnabledEl.checked = Boolean(data.enabled);
      dingtalkAutoLoginEl.checked = Boolean(data.allow_org_auto_login);
      dingtalkClientIdEl.value = data.client_id || "";
      dingtalkClientSecretEl.value = data.client_secret || "";
      dingtalkCorpIdEl.value = data.corp_id || "";
      dingtalkRedirectBaseUrlEl.value = data.redirect_base_url || "";
      updateDingtalkCallbackPreview();
      setMessage(dingtalkConfigStatus, `最近更新：${data.updated_at || "未记录"}`, false);
    }
    async function loadDingtalkIdentities() {
      const response = await fetch("/api/admin/dingtalk-identities");
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "读取钉钉用户失败");
      }
      renderDingtalkIdentities(data.identities || []);
      setMessage(dingtalkIdentitiesStatus, `已加载 ${Array.isArray(data.identities) ? data.identities.length : 0} 条用户`, false);
    }
    async function reloadShellVisualSettings() {
      try {
        const response = await fetch("/api/ui-settings");
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取界面设置失败");
        }
        applyVisualSettings(data.settings || currentUiSettings || window.__bootUiSettings || {});
      } catch (error) {
        // Keep the last-applied visual settings if the refresh fails.
      }
    }
    async function ensureAdmin(options = {}) {
      const preferInitialState = options.preferInitialState !== false;
      const initialAdminUser = preferInitialState ? getInitialAdminUser() : null;
      if (initialAdminUser) {
        setAdminIdentityText(initialAdminUser);
        return initialAdminUser;
      }
      const response = await fetch("/api/auth/me");
      const data = await response.json();
      if (!response.ok || !data || !data.authenticated || !data.user || data.user.role !== "admin") {
        initialAdminAuthState = {
          authenticated: Boolean(data && data.authenticated && data.user),
          user: data && data.user ? data.user : null,
        };
        throw new Error("not_admin");
      }
      initialAdminAuthState = {
        authenticated: true,
        user: data.user,
      };
      setAdminIdentityText(data.user);
      return data.user;
    }
    async function handleAdminLogin() {
      const username = String(document.getElementById("login-username").value || "").trim();
      const password = String(document.getElementById("login-password").value || "");
      if (!username || !password) {
        setMessage(adminLoginStatus, "请输入账号和密码。", true);
        return;
      }
      try {
        const response = await fetch("/api/admin/password-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "登录失败");
        }
        initialAdminAuthState = {
          authenticated: Boolean(data && data.user),
          user: data && data.user ? data.user : null,
        };
        setAdminPageVerified(true);
        setMessage(adminLoginStatus, "登录成功。", false);
        await reloadShellVisualSettings();
        await bootstrap();
      } catch (error) {
        setMessage(adminLoginStatus, error.message || "登录失败", true);
      }
    }
    async function handleAdminLogout() {
      try {
        const response = await fetch("/api/auth/logout", { method: "POST" });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.error || "退出失败");
        }
        document.getElementById("login-password").value = "";
        initialAdminAuthState = { authenticated: false, user: null };
        setAdminPageVerified(false);
        setMessage(adminLoginStatus, "已退出登录。", false);
        await reloadShellVisualSettings();
      } catch (error) {
        setMessage(adminLoginStatus, error.message || "退出失败", true);
      }
      await bootstrap();
    }
    function openAdminAccountOverlay() {
      adminAccountOverlay.hidden = false;
      adminCurrentPasswordEl.value = "";
      adminNewPasswordEl.value = "";
      adminConfirmPasswordEl.value = "";
      setMessage(adminAccountStatus, "", false);
      if (!String(adminUsernameEl.value || "").trim()) {
        loadAdminAccountInfo().catch(() => {});
      }
      window.setTimeout(() => adminCurrentPasswordEl.focus(), 0);
    }
    function closeAdminAccountOverlay() {
      adminAccountOverlay.hidden = true;
      adminCurrentPasswordEl.value = "";
      adminNewPasswordEl.value = "";
      adminConfirmPasswordEl.value = "";
      setMessage(adminAccountStatus, "", false);
    }
    async function saveAdminAccount() {
      const username = String(adminUsernameEl.value || "").trim();
      const current_password = String(adminCurrentPasswordEl.value || "");
      const new_password = String(adminNewPasswordEl.value || "");
      const confirm_password = String(adminConfirmPasswordEl.value || "");
      if (!username || !current_password || !new_password) {
        setMessage(adminAccountStatus, "请填写账号、当前密码和新密码。", true);
        return;
      }
      if (new_password !== confirm_password) {
        setMessage(adminAccountStatus, "两次输入的新密码不一致。", true);
        return;
      }
      try {
        const response = await fetch("/api/admin/password-update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, current_password, new_password }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存失败");
        }
        adminUsernameEl.value = data.username || username;
        document.getElementById("login-username").value = data.username || username;
        adminCurrentPasswordEl.value = "";
        adminNewPasswordEl.value = "";
        adminConfirmPasswordEl.value = "";
        setMessage(adminAccountStatus, "管理员账号/密码更新成功。", false);
        window.setTimeout(() => closeAdminAccountOverlay(), 600);
      } catch (error) {
        setMessage(adminAccountStatus, error.message || "保存失败", true);
      }
    }
    async function saveDingtalkConfig() {
      const payload = {
        enabled: dingtalkEnabledEl.checked,
        allow_org_auto_login: dingtalkAutoLoginEl.checked,
        client_id: String(dingtalkClientIdEl.value || "").trim(),
        client_secret: String(dingtalkClientSecretEl.value || "").trim(),
        corp_id: String(dingtalkCorpIdEl.value || "").trim(),
        redirect_base_url: String(dingtalkRedirectBaseUrlEl.value || "").trim(),
      };
      try {
        const response = await fetch("/api/admin/dingtalk-oauth-config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存钉钉配置失败");
        }
        dingtalkEnabledEl.checked = Boolean(data.enabled);
        dingtalkAutoLoginEl.checked = Boolean(data.allow_org_auto_login);
        dingtalkClientIdEl.value = data.client_id || "";
        dingtalkClientSecretEl.value = data.client_secret || "";
        dingtalkCorpIdEl.value = data.corp_id || "";
        dingtalkRedirectBaseUrlEl.value = data.redirect_base_url || "";
        updateDingtalkCallbackPreview();
        setMessage(dingtalkConfigStatus, "钉钉配置保存成功。", false);
      } catch (error) {
        setMessage(dingtalkConfigStatus, error.message || "保存钉钉配置失败", true);
      }
    }
    function showAdminContentView() {
      document.body.classList.remove("admin-auth-state");
      loginCard.hidden = true;
      adminContent.hidden = false;
      adminAccountButton.hidden = false;
      adminLogoutButton.hidden = false;
      adminDepartmentPageButton.hidden = false;
      adminUserPageButton.hidden = false;
    }
    function summarizeBootstrapFailures(failures) {
      if (!Array.isArray(failures) || !failures.length) {
        return "";
      }
      return failures.map((item) => item.label).join("、");
    }
    async function bootstrap() {
      showAdminCheckingView();
      try {
        await ensureAdmin({ preferInitialState: true });
        setAdminPageVerified(true);
        showAdminContentView();
        await loadAdminAccountInfo().catch((error) => {
          setMessage(adminLoginStatus, error.message || "读取管理员账号失败", true);
        });
        resetLocalAccountForm();
        const failures = [];
        const tasks = [
          ["岗位字段配置", loadPositionFieldScopes, positionFieldScopeStatusEl],
          ["本地账号", loadLocalAccounts, localAccountStatus],
          ["用户 MCP", loadAdminUsers, adminUsersStatus],
          ["部门共享通讯录", loadDepartmentDirectory, departmentDirectoryStatus],
          ["登录权限", loadAccessControl, accessStatus],
          ["钉钉配置", loadDingtalkConfig, dingtalkConfigStatus],
          ["钉钉身份缓存", loadDingtalkIdentities, dingtalkIdentitiesStatus],
        ];
        for (const [label, loader, statusEl] of tasks) {
          try {
            await loader();
          } catch (error) {
            failures.push({ label, message: error.message || `${label}加载失败` });
            setMessage(statusEl, error.message || `${label}加载失败`, true);
          }
        }
        if (failures.length) {
          const adminUser = getInitialAdminUser();
          setAuthInfoText(`当前登录：${formatAdminIdentity(adminUser)} · 后台已打开，部分模块加载失败`);
          setMessage(adminLoginStatus, `已进入后台，部分模块加载失败：${summarizeBootstrapFailures(failures)}`, true);
        } else {
          setMessage(adminLoginStatus, "", false);
        }
      } catch (error) {
        setAdminPageVerified(false);
        showAdminLoginView();
        await loadAdminAccountInfo().catch(() => {});
      }
    }
    function bindFieldSaveShortcut(inputEl, buttonEl) {
      inputEl.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
          return;
        }
        event.preventDefault();
        buttonEl.click();
      });
    }
    [
      positionFieldScopeSalesEl,
      positionFieldScopeProjectTypesEl,
      positionFieldScopeServiceModesEl,
        positionFieldScopeItemTypesEl,
      ].forEach((inputEl) => bindFieldSaveShortcut(inputEl, savePositionFieldScopeButton));
    bindFieldSaveShortcut(positionFieldScopeNewPositionEl, createPositionFieldScopeButton);
    bindFieldSaveShortcut(localAccountNewDepartmentEl, addLocalAccountDepartmentButton);
    bindFieldSaveShortcut(departmentDirectoryLookupNameEl, addDepartmentDirectoryEntryButton);
    document.getElementById("admin-login").addEventListener("click", handleAdminLogin);
    adminAccountButton.addEventListener("click", openAdminAccountOverlay);
    adminLogoutButton.addEventListener("click", handleAdminLogout);
    adminDepartmentPageButton.addEventListener("click", () => {
      window.location.href = "/department-schedule";
    });
    adminUserPageButton.addEventListener("click", () => {
      window.location.href = "/daily-planner";
    });
    helpDocsButton.addEventListener("click", () => {
      openHelpOverlay(CURRENT_HELP_PAGE_KEY);
    });
    helpOverlayCloseButton.addEventListener("click", closeHelpOverlay);
    helpOverlay.addEventListener("click", (event) => {
      if (event.target === helpOverlay) {
        closeHelpOverlay();
      }
    });
    adminAccountOverlayCloseButton.addEventListener("click", closeAdminAccountOverlay);
    adminAccountOverlay.addEventListener("click", (event) => {
      if (event.target === adminAccountOverlay) {
        closeAdminAccountOverlay();
      }
    });
    positionFieldScopeSelectEl.addEventListener("change", (event) => {
      const nextPosition = String(event.target.value || "").trim();
      if (!nextPosition) {
        return;
      }
      setCurrentPositionFieldScopePosition(nextPosition);
    });
    localAccountPositionTriggerEl.addEventListener("click", () => {
      setLocalAccountPositionMenuOpen(localAccountPositionMenuEl.hidden);
    });
    localAccountPositionOptionsBox.addEventListener("change", (event) => {
      const input = event.target.closest('input[type="checkbox"]');
      if (!input) {
        return;
      }
      updateLocalAccountPositionSummary();
    });
    document.addEventListener("click", (event) => {
      if (!localAccountPositionMultiselectEl.contains(event.target)) {
        setLocalAccountPositionMenuOpen(false);
      }
      if (
        isBackgroundSettingsOpen
        && !backgroundSettingsMenu.contains(event.target)
        && !backgroundSettingsButton.contains(event.target)
      ) {
        setBackgroundSettingsOpen(false);
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        setLocalAccountPositionMenuOpen(false);
        setBackgroundSettingsOpen(false);
        if (isHelpOverlayOpen) {
          closeHelpOverlay();
        }
      }
    });
    savePositionFieldScopeButton.addEventListener("click", savePositionFieldScopes);
    createPositionFieldScopeButton.addEventListener("click", () => createPositionFieldScopePosition(false));
    copyPositionFieldScopeButton.addEventListener("click", () => createPositionFieldScopePosition(true));
    deletePositionFieldScopeButton.addEventListener("click", deletePositionFieldScopePosition);
    reloadPositionFieldScopeButton.addEventListener("click", () => {
      loadPositionFieldScopes().catch((error) => setMessage(positionFieldScopeStatusEl, error.message || "加载岗位关联规则失败", true));
    });
    document.getElementById("reload-access").addEventListener("click", () => {
      loadAccessControl().catch((error) => setMessage(accessStatus, error.message || "加载失败", true));
    });
    document.getElementById("reload-local-accounts").addEventListener("click", async () => {
      try {
        await loadLocalAccounts();
        await loadDepartmentDirectory().catch(() => {});
      } catch (error) {
        setMessage(localAccountStatus, error.message || "加载失败", true);
      }
    });
    document.getElementById("reload-admin-users").addEventListener("click", () => {
      loadAdminUsers().catch((error) => setMessage(adminUsersStatus, error.message || "加载失败", true));
    });
    reloadDepartmentDirectoryButton.addEventListener("click", () => {
      loadDepartmentDirectory().catch((error) => setMessage(departmentDirectoryStatus, error.message || "加载失败", true));
    });
    addDepartmentDirectoryEntryButton.addEventListener("click", addDepartmentDirectoryEntry);
    departmentDirectoryDepartmentEl.addEventListener("change", () => {
      loadDepartmentDirectory(departmentDirectoryDepartmentEl.value).catch((error) => {
        setMessage(departmentDirectoryStatus, error.message || "加载失败", true);
      });
    });
    departmentDirectoryOverviewEl.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null;
      if (!target) {
        return;
      }
      const card = target.closest("[data-department]");
      if (!card) {
        return;
      }
      const department = String(card.getAttribute("data-department") || "").trim();
      if (!department) {
        return;
      }
      departmentDirectoryDepartmentEl.value = department;
      loadDepartmentDirectory(department).catch((error) => {
        setMessage(departmentDirectoryStatus, error.message || "加载失败", true);
      });
    });
    document.getElementById("save-local-account").addEventListener("click", saveLocalAccount);
    addLocalAccountDepartmentButton.addEventListener("click", addLocalAccountDepartment);
    document.getElementById("reset-local-account-form").addEventListener("click", resetLocalAccountForm);
    localAccountsBody.addEventListener("click", async (event) => {
      const deleteButton = event.target.closest(".local-account-delete");
      if (deleteButton) {
        const username = String(deleteButton.getAttribute("data-username") || "").trim();
        const account = localAccounts.find((item) => String(item.username || "") === username);
        if (!account) {
          setMessage(localAccountStatus, "未找到要删除的账号。", true);
          return;
        }
        await deleteLocalAccount(account);
        return;
      }
      const editButton = event.target.closest(".local-account-edit");
      if (!editButton) {
        return;
      }
      const username = String(editButton.getAttribute("data-username") || "").trim();
      const account = localAccounts.find((item) => String(item.username || "") === username);
      if (!account) {
        return;
      }
      fillLocalAccountForm(account);
      setMessage(localAccountStatus, `已载入账号 ${username}，留空密码可保持原密码不变。`, false);
    });
    document.getElementById("save-access").addEventListener("click", async () => {
      try {
        const payload = {
          login_allowed_users: normalizeLines(loginUsersEl.value),
          admin_allowed_users: normalizeLines(adminUsersEl.value),
        };
        const response = await fetch("/api/admin/access-control", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存失败");
        }
        loginUsersEl.value = (data.login_allowed_users || []).join("\\n");
        adminUsersEl.value = (data.admin_allowed_users || []).join("\\n");
        await loadAdminUsers().catch(() => {});
        setMessage(accessStatus, "权限配置保存成功。", false);
      } catch (error) {
        setMessage(accessStatus, error.message || "保存失败", true);
      }
    });
    dingtalkRedirectBaseUrlEl.addEventListener("input", updateDingtalkCallbackPreview);
    document.getElementById("reload-dingtalk-config").addEventListener("click", () => {
      loadDingtalkConfig().catch((error) => setMessage(dingtalkConfigStatus, error.message || "加载失败", true));
    });
    document.getElementById("save-dingtalk-config").addEventListener("click", saveDingtalkConfig);
    document.getElementById("reload-dingtalk-identities").addEventListener("click", () => {
      loadDingtalkIdentities().catch((error) => setMessage(dingtalkIdentitiesStatus, error.message || "加载失败", true));
    });
    document.getElementById("admin-account-save").addEventListener("click", saveAdminAccount);
    themeToggleButton.addEventListener("click", () => {
      const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
      writeStoredThemePreference(nextTheme);
      applyVisualSettings(currentUiSettings);
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
      scheduleVisualSettingsSave();
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
      scheduleVisualSettingsSave();
    });
    backgroundModeSelect.addEventListener("change", (event) => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_mode: event.target.value });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    regionOpacityInput.addEventListener("input", (event) => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, region_opacity: Number(event.target.value) / 100 });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    initializePasswordToggleFields();
    updateDingtalkCallbackPreview();
    applyVisualSettings(currentUiSettings);
    scheduleAutoThemeRefresh();
    bootstrap();
  </script>
</body>
</html>
""".replace("__INITIAL_ADMIN_AUTH_PAYLOAD__", initial_auth_payload_json).replace(
        "__INITIAL_UI_SETTINGS_PAYLOAD__", initial_ui_settings_json
    ).replace(
        "__HELP_DOCS_CSS__", HELP_DOCS_CSS
    ).replace(
        "__HELP_DOCS_OVERLAY__", HELP_DOCS_OVERLAY_HTML
    ).replace(
        "__INITIAL_BODY_ATTRS__", initial_body_attrs
    ).replace(
        "__INITIAL_AUTH_INFO_TEXT__", initial_auth_info_text
    ).replace(
        "__INITIAL_ACCOUNT_BUTTON_ATTRS__", initial_account_button_attrs
    ).replace(
        "__INITIAL_LOGOUT_BUTTON_ATTRS__", initial_logout_button_attrs
    ).replace(
        "__INITIAL_DEPARTMENT_BUTTON_ATTRS__", initial_department_button_attrs
    ).replace(
        "__INITIAL_USER_BUTTON_ATTRS__", initial_user_button_attrs
    ).replace(
        "__INITIAL_LOGIN_CARD_ATTRS__", initial_login_card_attrs
    ).replace(
        "__INITIAL_ADMIN_CONTENT_ATTRS__", initial_admin_content_attrs
    )
