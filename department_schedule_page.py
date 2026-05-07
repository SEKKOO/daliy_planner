from __future__ import annotations

DEPARTMENT_SCHEDULE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>部门日程管理</title>
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
      --danger: #c03c47;
      --danger-soft: #fff0f2;
      --success: #279e66;
      --text: var(--ink);
      --text-soft: var(--muted);
      --primary: var(--accent);
      --primary-deep: var(--accent-deep);
      --primary-soft: var(--accent-soft);
      --surface-rgb: 255, 255, 255;
      --surface-soft-rgb: 244, 249, 255;
      --table-head-rgb: 239, 247, 255;
      --table-cell-rgb: 255, 255, 255;
      --table-cell-alt-rgb: 247, 250, 255;
      --shell-surface-alpha: 0.82;
      --shell-surface-strong-alpha: 0.9;
      --shell-surface-soft-alpha: 0.72;
      --shell-surface-subtle-alpha: 0.54;
      --card-shadow: 0 18px 42px rgba(38, 86, 150, 0.09);
      --button-shadow: 0 14px 28px rgba(38, 86, 150, 0.12);
      --inner-shadow: inset 0 1px 0 rgba(255,255,255,0.42);
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
      --success: #61ddb1;
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
    .wrap { position: relative; z-index: 1; max-width: 1520px; margin: 0 auto; padding: 22px 18px 40px; }
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
      box-shadow: var(--card-shadow);
      backdrop-filter: blur(20px) saturate(120%);
    }
    .card::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 1px;
      background: linear-gradient(90deg, rgba(46, 119, 208, 0.2), rgba(46, 119, 208, 0.02));
      pointer-events: none;
    }
    .hero {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      padding: 22px;
      background: var(--boot-panel-background, linear-gradient(180deg, rgba(255,255,255,0.9), rgba(244,249,255,0.82)));
    }
    .hero::after {
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
      background: var(--primary-soft);
      color: var(--primary-deep);
      border: 1px solid rgba(42,111,214,0.14);
      font-size: 12px;
      font-weight: 700;
    }
    h1 { margin: 14px 0 8px; font-size: 30px; letter-spacing: -0.03em; }
    h2 { margin: 0; font-size: 20px; }
    .muted { color: var(--text-soft); font-size: 13px; line-height: 1.7; font-weight: 500; }
    .top-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
    }
    button, input, select, textarea { font: inherit; }
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
      box-shadow: var(--button-shadow);
      transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
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
    button.danger.secondary {
      background: var(--danger-soft);
      color: var(--danger);
      border-color: rgba(217,91,91,0.28);
    }
    button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; box-shadow: none; }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: 12px;
      padding: 10px 12px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      color: var(--text);
      -webkit-text-fill-color: currentColor;
      box-shadow: inset 0 1px 2px rgba(21,61,110,0.06);
      transition: border-color 0.18s ease, box-shadow 0.18s ease;
      backdrop-filter: blur(10px);
    }
    input, select { min-height: 42px; }
    textarea { min-height: 64px; resize: vertical; }
    input:disabled,
    select:disabled,
    textarea:disabled {
      opacity: 1;
      -webkit-text-fill-color: currentColor;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: rgba(42,111,214,0.62);
      box-shadow: 0 0 0 4px rgba(42,111,214,0.12);
    }
    label { display: grid; gap: 6px; font-size: 13px; font-weight: 600; color: var(--text); }
    .toolbar-card,
    .section-card,
    .state-card {
      margin-top: 16px;
      padding: 18px;
    }
    .toolbar-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: 220px 240px minmax(260px, 1fr);
      align-items: end;
    }
    .toolbar-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-start;
    }
    .toolbar-meta {
      margin-top: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .status-text { min-height: 22px; }
    .chip-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    .plan-week-meta {
      display: grid;
      gap: 6px;
      justify-items: end;
    }
    .plan-week-meta-chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .plan-week-meta-updated {
      font-size: 12px;
      line-height: 1.5;
      color: var(--text-soft);
      text-align: right;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--primary-soft);
      color: var(--primary-deep);
      border: 1px solid rgba(42,111,214,0.14);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .section-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .section-head-main { display: grid; gap: 6px; }
    .plan-table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
    }
    .plan-layout {
      display: grid;
      grid-template-columns: 128px minmax(0, 1fr);
      gap: 8px;
      align-items: start;
    }
    .plan-member-list {
      display: grid;
      gap: 0;
      align-self: start;
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: hidden;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
    }
    .plan-member-spacer {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 6px;
      border-bottom: 1px solid var(--line);
      background: rgba(var(--table-head-rgb), var(--shell-surface-strong-alpha));
    }
    .plan-member-row {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 6px;
      border-bottom: 1px solid var(--line);
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    .plan-member-row:last-child { border-bottom: none; }
    .plan-table {
      width: max(1480px, 100%);
      border-collapse: separate;
      border-spacing: 0;
    }
    .plan-table th,
    .plan-table td {
      padding: 12px;
      font-size: 13px;
      vertical-align: top;
      border-bottom: 1px solid var(--line);
      border-right: 1px solid rgba(215,227,239,0.72);
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    .plan-table th:last-child,
    .plan-table td:last-child { border-right: none; }
    .plan-table tr:last-child td { border-bottom: none; }
    .plan-table th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(var(--table-head-rgb), var(--shell-surface-strong-alpha));
      color: var(--text);
      font-weight: 700;
      white-space: nowrap;
    }
    .member-text-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      min-height: 100%;
    }
    .member-text {
      display: block;
      max-width: 100%;
      color: var(--text);
      font-size: 13px;
      font-weight: 600;
      line-height: 1.5;
      text-align: center;
      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .member-subtext {
      display: block;
      max-width: 100%;
      color: var(--text-soft);
      font-size: 12px;
      font-weight: 500;
      line-height: 1.45;
      text-align: center;
      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .plan-day-cell { min-width: 188px; }
    .plan-day-editor { display: grid; gap: 8px; }
    .plan-day-field {
      display: grid;
      gap: 4px;
      padding: 8px;
      border-radius: 14px;
      border: 1px solid rgba(42,111,214,0.12);
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
      box-shadow: var(--inner-shadow);
    }
    .plan-day-label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: var(--primary-deep);
      text-transform: uppercase;
    }
    .plan-day-input {
      min-height: 60px;
      padding: 8px 10px;
      border-radius: 10px;
      font-size: 12px;
      line-height: 1.5;
    }
    .pending-cell { min-width: 220px; }
    .pending-input { min-height: 132px; font-size: 12px; line-height: 1.6; }
    .action-cell {
      min-width: 170px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
    }
    .row-actions { display: grid; gap: 10px; }
    .row-actions button { width: 100%; }
    .row-status {
      min-height: 40px;
      display: flex;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 8px;
    }
    .row-status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 32px;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid rgba(42,111,214,0.14);
      background: linear-gradient(180deg, rgba(238,245,255,0.98) 0%, rgba(225,238,255,0.96) 100%);
      color: var(--primary-deep);
      box-shadow: 0 8px 18px rgba(42,111,214,0.12);
      font-size: 12px;
      font-weight: 700;
      line-height: 1.5;
    }
    .row-status-badge::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: currentColor;
      opacity: 0.78;
      flex: 0 0 auto;
    }
    .row-status-badge.pending {
      border-color: rgba(177,118,16,0.24);
      background: linear-gradient(180deg, rgba(255,247,226,0.98) 0%, rgba(255,241,208,0.96) 100%);
      color: #9f6809;
      box-shadow: 0 8px 18px rgba(177,118,16,0.12);
    }
    .row-status-badge.success {
      border-color: rgba(31,122,79,0.22);
      background: linear-gradient(180deg, rgba(232,249,239,0.98) 0%, rgba(218,244,229,0.96) 100%);
      color: #1f7a4f;
      box-shadow: 0 8px 18px rgba(31,122,79,0.12);
    }
    .row-status-badge.error {
      border-color: rgba(210,85,85,0.24);
      background: linear-gradient(180deg, rgba(255,242,242,0.98) 0%, rgba(255,231,231,0.96) 100%);
      color: #c33636;
      box-shadow: 0 8px 18px rgba(210,85,85,0.12);
    }
    .row-status-badge.readonly {
      border-color: rgba(91,115,141,0.16);
      background: linear-gradient(180deg, rgba(245,248,252,0.98) 0%, rgba(236,241,247,0.96) 100%);
      font-size: 12px;
      color: var(--text-soft);
      box-shadow: none;
    }
    .row-status-badge.readonly::before {
      opacity: 0.52;
    }
    .row-status-badge.time {
      line-height: 1.6;
    }
    .daily-select-row {
      display: grid;
      gap: 12px;
      grid-template-columns: 320px minmax(240px, 1fr);
      align-items: end;
      margin-bottom: 14px;
    }
    .member-week-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    .member-week-note {
      margin-top: 6px;
      color: var(--text-soft);
      font-size: 13px;
      line-height: 1.7;
    }
    .daily-table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
    }
    .daily-week-table {
      width: max(1400px, 100%);
      border-collapse: separate;
      border-spacing: 0;
    }
    .daily-week-table th,
    .daily-week-table td {
      padding: 12px;
      font-size: 13px;
      vertical-align: top;
      border-bottom: 1px solid var(--line);
      border-right: 1px solid rgba(215,227,239,0.72);
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    .daily-week-table th:last-child,
    .daily-week-table td:last-child { border-right: none; }
    .daily-week-table tr:last-child td { border-bottom: none; }
    .daily-week-table th {
      background: rgba(var(--table-head-rgb), var(--shell-surface-strong-alpha));
      color: var(--text);
      font-weight: 700;
      white-space: nowrap;
      min-width: 200px;
    }
    .daily-day-cell {
      min-width: 200px;
      background: linear-gradient(
        180deg,
        rgba(var(--surface-rgb), var(--shell-surface-strong-alpha)),
        rgba(var(--surface-soft-rgb), var(--shell-surface-alpha))
      );
    }
    .daily-day-head {
      display: grid;
      gap: 5px;
      margin-bottom: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(42,111,214,0.1);
    }
    .daily-day-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .daily-day-name { font-size: 15px; font-weight: 700; color: var(--text); }
    .daily-day-stat { font-size: 12px; font-weight: 700; color: var(--primary-deep); }
    .daily-day-date { font-size: 12px; color: var(--text-soft); }
    .daily-day-updated { font-size: 11px; color: var(--text-soft); }
    .empty-card {
      display: grid;
      place-items: center;
      min-height: 138px;
      padding: 14px;
      border-radius: 14px;
      border: 1px dashed var(--line);
      color: var(--text-soft);
      font-size: 13px;
      background: rgba(var(--surface-rgb), var(--shell-surface-alpha));
      text-align: center;
    }
    .log-list { display: grid; gap: 10px; }
    .log-item {
      display: grid;
      gap: 8px;
      padding: 11px 12px;
      border-radius: 14px;
      border: 1px solid rgba(42,111,214,0.1);
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    .log-item-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    .log-item-title { font-size: 13px; font-weight: 700; color: var(--text); }
    .tag-row { display: flex; gap: 6px; flex-wrap: wrap; }
    .tiny-tag {
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--primary-soft);
      color: var(--primary-deep);
      border: 1px solid rgba(42,111,214,0.12);
      font-size: 11px;
      font-weight: 700;
    }
    .log-text {
      white-space: pre-wrap;
      line-height: 1.6;
      color: var(--text);
      font-size: 13px;
    }
    .log-extra { display: grid; gap: 5px; color: var(--text-soft); font-size: 12px; line-height: 1.6; }
    .state-card {
      text-align: center;
      display: grid;
      gap: 12px;
    }
    .state-title { font-size: 20px; font-weight: 800; color: var(--text); }
    .state-actions { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
    .full-width-note { width: 100%; }
    .password-overlay[hidden] { display: none; }
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
    .password-dialog-body { display: grid; gap: 12px; }
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
    .auth-status-text {
      min-height: 22px;
      font-size: 12px;
      line-height: 1.6;
      color: var(--text-soft);
      white-space: pre-wrap;
    }
    [hidden] { display: none !important; }
    body[data-theme="dark"] .eyebrow,
    body[data-theme="dark"] .chip,
    body[data-theme="dark"] .tiny-tag {
      color: var(--ink);
      background: rgba(41, 60, 91, 0.8);
      border-color: rgba(255,255,255,0.08);
    }
    body[data-theme="dark"] .toolbar-card,
    body[data-theme="dark"] .section-card,
    body[data-theme="dark"] .state-card,
    body[data-theme="dark"] .plan-table-wrap,
    body[data-theme="dark"] .daily-table-wrap,
    body[data-theme="dark"] .empty-card,
    body[data-theme="dark"] .log-item,
    body[data-theme="dark"] .plan-day-field {
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
    body[data-theme="dark"] .daily-day-stat,
    body[data-theme="dark"] .plan-day-label,
    body[data-theme="dark"] .page-user-badge-label {
      color: var(--ink);
    }
    body[data-theme="dark"] .muted,
    body[data-theme="dark"] .member-meta,
    body[data-theme="dark"] .member-week-note,
    body[data-theme="dark"] .daily-day-date,
    body[data-theme="dark"] .daily-day-updated,
    body[data-theme="dark"] .log-extra,
    body[data-theme="dark"] .row-status-badge.readonly {
      color: var(--muted);
    }
    body[data-theme="dark"] .empty-card,
    body[data-theme="dark"] .log-text,
    body[data-theme="dark"] .member-name,
    body[data-theme="dark"] .daily-day-name,
    body[data-theme="dark"] .log-item-title,
    body[data-theme="dark"] .state-title,
    body[data-theme="dark"] label,
    body[data-theme="dark"] input,
    body[data-theme="dark"] select,
    body[data-theme="dark"] textarea {
      color: var(--ink);
    }
    body[data-theme="dark"] h2,
    body[data-theme="dark"] h3,
    body[data-theme="dark"] .status-text,
    body[data-theme="dark"] .chip,
    body[data-theme="dark"] .plan-table th,
    body[data-theme="dark"] .daily-week-table th,
    body[data-theme="dark"] .plan-table thead .member-cell {
      color: #f8fbff;
    }
    body[data-theme="dark"] .member-text {
      color: #f8fbff;
    }
    body[data-theme="dark"] .member-subtext {
      color: var(--muted);
    }
    body[data-theme="dark"] .plan-member-list {
      border-color: rgba(255,255,255,0.08);
      background:
        linear-gradient(180deg, rgba(48, 69, 101, 0.54), rgba(30, 46, 71, 0.3)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.05), transparent 74%);
    }
    body[data-theme="dark"] .plan-member-spacer,
    body[data-theme="dark"] .plan-member-row {
      border-color: rgba(255,255,255,0.08);
    }
    body[data-theme="dark"] .plan-member-spacer {
      background: rgba(54, 77, 112, 0.92);
    }
    body[data-theme="dark"] .plan-member-row {
      background: rgba(var(--table-cell-rgb), var(--shell-surface-strong-alpha));
    }
    body[data-theme="dark"] .plan-table th,
    body[data-theme="dark"] .daily-week-table th,
    body[data-theme="dark"] .plan-table thead .member-cell {
      background: rgba(54, 77, 112, 0.92);
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
    body[data-theme="dark"] .row-status-badge,
    body[data-theme="dark"] .row-status-badge.time {
      color: var(--ink);
      border-color: rgba(255,255,255,0.08);
      background: rgba(41, 60, 91, 0.8);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 10px 20px rgba(4, 10, 22, 0.12);
    }
    body[data-theme="dark"] .row-status-badge.readonly {
      border-color: rgba(255,255,255,0.08);
      background: rgba(32, 46, 70, 0.76);
    }
    body[data-theme="dark"] .row-status-badge.pending {
      color: #ffd27a;
      border-color: rgba(255, 210, 122, 0.34);
      background: linear-gradient(180deg, rgba(110, 82, 44, 0.78) 0%, rgba(77, 58, 32, 0.68) 100%);
    }
    body[data-theme="dark"] .row-status-badge.success {
      color: #9ef0cb;
      border-color: rgba(97, 221, 177, 0.34);
      background: linear-gradient(180deg, rgba(31, 82, 67, 0.78) 0%, rgba(22, 57, 47, 0.68) 100%);
    }
    body[data-theme="dark"] .row-status-badge.error {
      color: #ffb8c0;
      border-color: rgba(255, 154, 164, 0.34);
      background: linear-gradient(180deg, rgba(99, 42, 51, 0.82) 0%, rgba(69, 29, 36, 0.72) 100%);
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
    body[data-theme="dark"] .password-dialog {
      background:
        linear-gradient(180deg, rgba(46, 67, 101, 0.94), rgba(28, 43, 66, 0.9)),
        linear-gradient(135deg, rgba(125, 183, 255, 0.08), transparent 72%);
      border-color: rgba(255,255,255,0.1);
      box-shadow: 0 26px 70px rgba(4, 10, 22, 0.3);
    }
    @media (max-width: 980px) {
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
      .hero { flex-direction: column; }
      .toolbar-grid,
      .daily-select-row { grid-template-columns: 1fr; }
      .plan-week-meta { justify-items: start; }
      .plan-week-meta-chips { justify-content: flex-start; }
      .plan-week-meta-updated { text-align: left; }
    }
    @media (max-width: 720px) {
      .top-actions button,
      .toolbar-actions button,
      .state-actions button { width: 100%; }
    }
  </style>
</head>
<body>
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
      <button type="button" class="theme-toggle tiny-btn" id="logout-page">退出</button>
      <button type="button" class="theme-toggle tiny-btn" id="password-button" hidden>修改密码</button>
      <button type="button" class="theme-toggle tiny-btn" id="back-user-page">用户页面</button>
      <button type="button" class="theme-toggle tiny-btn" id="back-admin-page" hidden>管理后台</button>
      <button type="button" class="theme-toggle tiny-btn" id="theme-toggle">黑夜模式</button>
      <button type="button" class="theme-toggle tiny-btn background-settings-button" id="background-settings-button" aria-expanded="false" aria-controls="background-settings-menu">背景设置</button>
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

    <section class="card toolbar-card" id="toolbar-card">
      <div class="toolbar-grid">
        <label>
          <span>基准日期</span>
          <input id="schedule-date" type="date" value="__INITIAL_DATE__">
        </label>
        <label>
          <span>查看部门</span>
          <select id="schedule-department"></select>
        </label>
        <div class="toolbar-actions">
          <button type="button" class="secondary" id="prev-week-button">上周</button>
          <button type="button" class="secondary" id="next-week-button">下周</button>
          <button type="button" id="reload-schedule-button">刷新</button>
        </div>
      </div>
      <div class="toolbar-meta">
        <div class="status-text muted" id="page-status">正在加载...</div>
        <div class="chip-row" id="toolbar-summary"></div>
      </div>
    </section>

    <section class="card section-card" id="plan-section">
      <div class="section-head">
        <div class="section-head-main">
          <h2>部门本周安排</h2>
          <div class="muted">按用户横向查看周一到周日安排，编辑后会自动保存。</div>
        </div>
        <div class="plan-week-meta" id="plan-week-meta"></div>
      </div>
      <div class="plan-layout">
        <div class="plan-member-list" id="department-plan-members"></div>
        <div class="plan-table-wrap">
          <table class="plan-table">
            <thead>
              <tr>
                <th>周一</th>
                <th>周二</th>
                <th>周三</th>
                <th>周四</th>
                <th>周五</th>
                <th>周六</th>
                <th>周日</th>
                <th>其他待办</th>
              </tr>
            </thead>
            <tbody id="department-plan-body"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="card section-card" id="daily-section" hidden>
      <div class="section-head">
        <div class="section-head-main">
          <h2>用户每日事项展示</h2>
          <div class="muted">选择部门内任意一位用户后，按周一到周日查看其每天填写的事项内容。</div>
        </div>
      </div>
      <div class="daily-select-row">
        <label>
          <span>用户选择</span>
          <select id="member-user-select"></select>
        </label>
        <div>
          <div class="member-week-meta chip-row" id="selected-member-meta"></div>
          <div class="member-week-note" id="selected-member-note">请选择一位用户后查看其本周事项。</div>
        </div>
      </div>
      <div class="daily-table-wrap">
        <table class="daily-week-table">
          <thead>
            <tr>
              <th>周一</th>
              <th>周二</th>
              <th>周三</th>
              <th>周四</th>
              <th>周五</th>
              <th>周六</th>
              <th>周日</th>
            </tr>
          </thead>
          <tbody id="member-daily-body"></tbody>
        </table>
      </div>
    </section>

    <section class="card state-card" id="state-card" hidden>
      <div class="state-title" id="state-title">暂时无法查看</div>
      <div class="muted" id="state-message"></div>
      <div class="state-actions">
        <button type="button" class="secondary" id="state-go-user">用户页面</button>
        <button type="button" class="secondary" id="state-go-admin">管理后台</button>
      </div>
    </section>
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
          <label>当前密码 <input id="password-current-input" type="password" autocomplete="current-password" data-password-toggle></label>
          <label>新密码 <input id="password-new-input" type="password" autocomplete="new-password" data-password-toggle></label>
          <label>确认新密码 <input id="password-confirm-input" type="password" autocomplete="new-password" data-password-toggle></label>
          <div class="row">
            <button type="button" id="password-submit-button">保存新密码</button>
          </div>
          <div class="auth-status-text" id="password-status"></div>
        </div>
      </section>
    </div>
  </div>

  <script>
    const dateInput = document.getElementById("schedule-date");
    const departmentSelect = document.getElementById("schedule-department");
    const memberUserSelect = document.getElementById("member-user-select");
    const viewerMetaEl = document.getElementById("viewer-meta");
    const pageStatusEl = document.getElementById("page-status");
    const toolbarSummaryEl = document.getElementById("toolbar-summary");
    const planWeekMetaEl = document.getElementById("plan-week-meta");
    const departmentPlanMembersEl = document.getElementById("department-plan-members");
    const departmentPlanBody = document.getElementById("department-plan-body");
    const selectedMemberMetaEl = document.getElementById("selected-member-meta");
    const selectedMemberNoteEl = document.getElementById("selected-member-note");
    const memberDailyBodyEl = document.getElementById("member-daily-body");
    const stateCardEl = document.getElementById("state-card");
    const stateTitleEl = document.getElementById("state-title");
    const stateMessageEl = document.getElementById("state-message");
    const toolbarCardEl = document.getElementById("toolbar-card");
    const planSectionEl = document.getElementById("plan-section");
    const dailySectionEl = document.getElementById("daily-section");
    const backAdminPageButton = document.getElementById("back-admin-page");
    const logoutPageButton = document.getElementById("logout-page");
    const passwordButton = document.getElementById("password-button");
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
    const passwordOverlay = document.getElementById("password-overlay");
    const passwordOverlayCloseButton = document.getElementById("password-overlay-close");
    const passwordDialogAccount = document.getElementById("password-dialog-account");
    const passwordCurrentInput = document.getElementById("password-current-input");
    const passwordNewInput = document.getElementById("password-new-input");
    const passwordConfirmInput = document.getElementById("password-confirm-input");
    const passwordSubmitButton = document.getElementById("password-submit-button");
    const passwordStatus = document.getElementById("password-status");
    const PLAN_AUTO_SAVE_DELAY_MS = 1000;
    const VISUAL_SETTINGS_AUTOSAVE_DELAY_MS = 260;
    const MAX_BACKGROUND_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
    const THEME_PREFERENCE_STORAGE_KEY = "daily_planner_theme_preference";
    const BING_DAILY_BACKGROUND_PATH = "/api/backgrounds/bing-daily";
    const AUTO_THEME_DAY_START_HOUR = 6;
    const AUTO_THEME_NIGHT_START_HOUR = 19;
    let latestPayload = null;
    let currentUiSettings = window.__bootUiSettings || {};
    let selectedMemberUserId = "";
    let visualSettingsAutosaveTimer = null;
    let isBackgroundSettingsOpen = false;
    let isPasswordOverlayOpen = false;
    const planAutoSaveTimers = new Map();
    const planSaveInFlightUsers = new Set();

    function initializePasswordToggleFields() {
      document.querySelectorAll('input[type="password"][data-password-toggle]').forEach((input) => {
        if (!(input instanceof HTMLInputElement) || input.dataset.passwordToggleReady === 'true') {
          return;
        }
        const parent = input.parentNode;
        if (!parent) {
          return;
        }
        input.dataset.passwordToggleReady = 'true';
        const wrapper = document.createElement('span');
        wrapper.className = 'password-input-wrap';
        parent.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle-btn';
        toggleButton.innerHTML = '<span aria-hidden="true">&#128065;</span>';
        if (input.id) {
          toggleButton.setAttribute('aria-controls', input.id);
        }
        const syncToggleState = () => {
          const isVisible = input.type === 'text';
          toggleButton.classList.toggle('is-visible', isVisible);
          toggleButton.setAttribute('aria-pressed', isVisible ? 'true' : 'false');
          const label = isVisible ? '隐藏密码' : '显示密码';
          toggleButton.setAttribute('aria-label', label);
          toggleButton.title = label;
        };
        toggleButton.addEventListener('mousedown', (event) => {
          event.preventDefault();
        });
        toggleButton.addEventListener('click', () => {
          const selectionStart = typeof input.selectionStart === 'number' ? input.selectionStart : null;
          const selectionEnd = typeof input.selectionEnd === 'number' ? input.selectionEnd : null;
          input.type = input.type === 'password' ? 'text' : 'password';
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

    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function setStatus(text, isError = false) {
      pageStatusEl.textContent = text || "";
      pageStatusEl.style.color = isError ? "var(--danger)" : "var(--ink)";
    }
    function setInlineStatus(target, text, isError = false) {
      target.textContent = text || "";
      target.style.color = isError ? "var(--danger)" : "var(--ink)";
    }
    function setViewerMetaText(text) {
      if (viewerMetaEl) {
        viewerMetaEl.textContent = text || "";
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
    function canCurrentUserChangePassword(user) {
      return Boolean(user && String(user.user_id || "").trim().startsWith("local"));
    }
    function openPasswordOverlay() {
      const viewer = latestPayload && latestPayload.viewer ? latestPayload.viewer : null;
      if (!canCurrentUserChangePassword(viewer)) {
        return;
      }
      isPasswordOverlayOpen = true;
      passwordOverlay.hidden = false;
      passwordDialogAccount.textContent = `当前账号：${viewer.display_name || viewer.user_id || "未登录"}`;
      passwordCurrentInput.value = "";
      passwordNewInput.value = "";
      passwordConfirmInput.value = "";
      setInlineStatus(passwordStatus, "", false);
      window.setTimeout(() => passwordCurrentInput.focus(), 0);
    }
    function closePasswordOverlay() {
      isPasswordOverlayOpen = false;
      passwordOverlay.hidden = true;
      passwordCurrentInput.value = "";
      passwordNewInput.value = "";
      passwordConfirmInput.value = "";
      setInlineStatus(passwordStatus, "", false);
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
        const response = await fetch("/api/auth/password-update", {
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
        setStatus("密码修改成功。");
      } catch (error) {
        setInlineStatus(passwordStatus, error.message || "密码修改失败。", true);
      }
    }

    function formatRole(user) {
      const parts = [];
      if (String(user && user.role || "") === "admin") {
        parts.push("管理员");
      } else if (user && user.is_department_admin) {
        parts.push("部门管理员");
      } else {
        parts.push("普通用户");
      }
      const positions = Array.isArray(user && user.positions) ? user.positions.filter(Boolean) : [];
      if (positions.length) {
        parts.push(positions.join("、"));
      }
      const department = String(user && user.department || "").trim();
      if (department) {
        parts.push(department);
      }
      return parts.join(" · ");
    }

    function formatDateLabel(value) {
      const text = String(value || "").trim();
      if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
        return text || "-";
      }
      return text.slice(5).replace("-", "/");
    }

    function shiftDateByDays(value, days) {
      const source = String(value || "").trim();
      if (!/^\d{4}-\d{2}-\d{2}$/.test(source)) {
        return source;
      }
      const current = new Date(`${source}T00:00:00`);
      current.setDate(current.getDate() + days);
      const year = current.getFullYear();
      const month = `${current.getMonth() + 1}`.padStart(2, "0");
      const day = `${current.getDate()}`.padStart(2, "0");
      return `${year}-${month}-${day}`;
    }

    function renderChip(text) {
      return `<span class="chip">${escapeHtml(text)}</span>`;
    }

    function showStateCard(title, message, showAdminButton = true) {
      stateTitleEl.textContent = title || "暂时无法查看";
      stateMessageEl.textContent = message || "";
      stateCardEl.hidden = false;
      toolbarCardEl.hidden = false;
      planSectionEl.hidden = true;
      dailySectionEl.hidden = true;
      document.getElementById("state-go-admin").hidden = !showAdminButton;
    }

    function hideStateCard() {
      stateCardEl.hidden = true;
      planSectionEl.hidden = false;
    }

    function getMembers() {
      return Array.isArray(latestPayload && latestPayload.members) ? latestPayload.members : [];
    }

    function getMemberByUserId(userId) {
      const normalized = String(userId || "").trim();
      return getMembers().find((member) => String(member && member.user && member.user.user_id || "").trim() === normalized) || null;
    }

    function canEditDepartmentWeeklyPlan() {
      return Boolean(latestPayload && latestPayload.can_edit_weekly_plan !== false);
    }

    function canViewDailySection() {
      return Boolean(latestPayload && latestPayload.show_daily_section);
    }

    function applyPayloadViewVisibility(payload) {
      const viewer = payload && payload.viewer ? payload.viewer : {};
      const canShowDailySection = Boolean(payload && payload.show_daily_section);
      const canShowAdminButton = Boolean(payload && payload.show_admin_button);
      dailySectionEl.hidden = !canShowDailySection;
      backAdminPageButton.hidden = !canShowAdminButton;
      document.getElementById("state-go-admin").hidden = !canShowAdminButton;
      setViewerMetaText(`当前登录：${viewer.display_name || viewer.user_id || '当前用户'} · ${formatRole(viewer)}`);
    }

    function findDepartmentPlanRow(userId) {
      const normalized = String(userId || "").trim();
      return Array.from(departmentPlanBody.querySelectorAll('tr[data-user-id]')).find((row) => {
        return String(row.getAttribute('data-user-id') || '').trim() === normalized;
      }) || null;
    }

    function getPlanRowStatusEl(userId) {
      const row = findDepartmentPlanRow(userId);
      return row ? row.querySelector('.row-status') : null;
    }

    function renderPlanRowStatusMarkup(text, tone = 'time') {
      const normalizedText = String(text || '').trim();
      if (!normalizedText) {
        return '';
      }
      const allowedTones = new Set(['time', 'pending', 'success', 'error', 'readonly']);
      const normalizedTone = allowedTones.has(String(tone || '').trim()) ? String(tone || '').trim() : 'time';
      return `<span class="row-status-badge ${normalizedTone}">${escapeHtml(normalizedText)}</span>`;
    }

    function setPlanRowStatus(userId, text, isError = false) {
      const statusEl = getPlanRowStatusEl(userId);
      if (!statusEl) {
        return;
      }
      const statusText = String(text || '').trim();
      let tone = 'time';
      if (isError) {
        tone = 'error';
      } else if (!statusText) {
        tone = 'time';
      } else if (statusText.includes('最近保存')) {
        tone = 'time';
      } else if (statusText.includes('自动保存中') || statusText.includes('正在保存') || statusText.includes('已修改')) {
        tone = 'pending';
      } else if (statusText.includes('没有编辑权限') || statusText.includes('仅管理员')) {
        tone = 'readonly';
      } else if (statusText.includes('已保存')) {
        tone = 'success';
      }
      statusEl.innerHTML = renderPlanRowStatusMarkup(statusText, tone);
    }

    function clearAllPlanAutoSaveTimers() {
      planAutoSaveTimers.forEach((timerId) => window.clearTimeout(timerId));
      planAutoSaveTimers.clear();
    }

    function syncDepartmentPlanMemberHeights() {
      const spacerEl = departmentPlanMembersEl.querySelector('.plan-member-spacer');
      const headerRow = departmentPlanBody.closest('table') && departmentPlanBody.closest('table').querySelector('thead tr');
      if (spacerEl && headerRow) {
        spacerEl.style.height = `${Math.ceil(headerRow.getBoundingClientRect().height)}px`;
      }
      const memberRows = Array.from(departmentPlanMembersEl.querySelectorAll('.plan-member-row[data-user-id]'));
      const tableRows = Array.from(departmentPlanBody.querySelectorAll('tr[data-user-id]'));
      memberRows.forEach((row) => {
        row.style.height = 'auto';
      });
      memberRows.forEach((row, index) => {
        const tableRow = tableRows[index];
        if (!tableRow) {
          return;
        }
        row.style.height = `${Math.ceil(tableRow.getBoundingClientRect().height)}px`;
      });
    }

    function renderDepartmentSelect(payload) {
      const departments = Array.isArray(payload && payload.departments) ? payload.departments : [];
      const options = [];
      if (payload && payload.allow_all_departments) {
        options.push('<option value="__all__">全部部门</option>');
      }
      departments.forEach((department) => {
        options.push(`<option value="${escapeHtml(department)}">${escapeHtml(department)}</option>`);
      });
      if (!options.length) {
        options.push('<option value="">暂无可查看部门</option>');
      }
      departmentSelect.innerHTML = options.join("");
      const selectedValue = payload && payload.selected_department ? payload.selected_department : "__all__";
      departmentSelect.value = selectedValue;
      if (!departmentSelect.value && payload && payload.allow_all_departments) {
        departmentSelect.value = "__all__";
      }
      departmentSelect.disabled = !(payload && payload.can_switch_department);
    }

    function renderToolbarSummary(payload) {
      const summary = payload && payload.summary || {};
      const chips = [
        `周范围 ${payload && payload.week_start || "-"} ~ ${payload && payload.week_end || "-"}`,
        `成员 ${summary.member_count || 0} 人`,
      ];
      if (payload && payload.show_daily_section) {
        chips.push(`本周工时 ${summary.total_hours || "0"}h`);
        chips.push(`事项 ${summary.total_items || 0} 条`);
      }
      toolbarSummaryEl.innerHTML = chips.map(renderChip).join("");
      const planMetaChips = [`当前部门 ${payload && payload.selected_department_label || "全部部门"}`];
      const latestUpdatedAt = getLatestDepartmentWeeklyPlanUpdatedAt(payload);
      planWeekMetaEl.innerHTML = `
        <div class="plan-week-meta-chips">${planMetaChips.map(renderChip).join("")}</div>
        <div class="plan-week-meta-updated">最近保存：${escapeHtml(latestUpdatedAt || "未记录")}</div>
      `;
    }

    function getLatestDepartmentWeeklyPlanUpdatedAt(payload) {
      const members = Array.isArray(payload && payload.members) ? payload.members : [];
      let latestUpdatedAt = "";
      members.forEach((member) => {
        const updatedAt = String(member && member.weekly_plan_updated_at || "").trim();
        if (updatedAt && (!latestUpdatedAt || updatedAt > latestUpdatedAt)) {
          latestUpdatedAt = updatedAt;
        }
      });
      return latestUpdatedAt;
    }

    function renderPlanDayEditor(userId, dayRow, index) {
      const row = dayRow && typeof dayRow === "object" ? dayRow : {};
      const disabledAttr = canEditDepartmentWeeklyPlan() ? '' : ' disabled';
      return `
        <div class="plan-day-editor">
          <div class="plan-day-field">
            <div class="plan-day-label">上午</div>
            <textarea class="plan-day-input" data-user-id="${escapeHtml(userId)}" data-day-index="${index}" data-part="am" placeholder="上午安排"${disabledAttr}>${escapeHtml(row.am || "")}</textarea>
          </div>
          <div class="plan-day-field">
            <div class="plan-day-label">下午</div>
            <textarea class="plan-day-input" data-user-id="${escapeHtml(userId)}" data-day-index="${index}" data-part="pm" placeholder="下午安排"${disabledAttr}>${escapeHtml(row.pm || "")}</textarea>
          </div>
        </div>
      `;
    }

    function renderDepartmentPlanTable(payload) {
      const members = Array.isArray(payload && payload.members) ? payload.members : [];
      const canEdit = Boolean(payload && payload.can_edit_weekly_plan !== false);
      departmentPlanMembersEl.innerHTML = `
        <div class="plan-member-spacer">
          <div class="member-text">用户</div>
        </div>
      `;
      if (!members.length) {
        departmentPlanBody.innerHTML = '<tr><td colspan="8"><div class="empty-card">当前部门暂无成员，请先补充成员所属部门后再查看。</div></td></tr>';
        return;
      }
      departmentPlanMembersEl.innerHTML += members.map((member) => {
        const user = member.user || {};
        const userId = String(user.user_id || "").trim();
        const userDisplayName = String(user.display_name || userId || "未命名用户").trim();
        const userPositions = String(
          user.position_labels
          || (Array.isArray(user.positions) ? user.positions.filter(Boolean).join("、") : "")
          || user.position
          || ""
        ).trim();
        const userMetaTitle = [userDisplayName, formatRole(user)].filter(Boolean).join(" · ");
        return `
          <div class="plan-member-row" data-user-id="${escapeHtml(userId)}">
            <div class="member-text-wrap">
              <div class="member-text" title="${escapeHtml(userMetaTitle)}">${escapeHtml(userDisplayName)}</div>
              ${userPositions ? `<div class="member-subtext">${escapeHtml(userPositions)}</div>` : ''}
            </div>
          </div>
        `;
      }).join("");
      departmentPlanBody.innerHTML = members.map((member) => {
        const user = member.user || {};
        const userId = String(user.user_id || "").trim();
        const weeklyRows = Array.isArray(member.weekly_plan_rows) ? member.weekly_plan_rows : [];
        return `
          <tr data-user-id="${escapeHtml(userId)}">
            ${weeklyRows.map((row, index) => `<td class="plan-day-cell">${renderPlanDayEditor(userId, row, index)}</td>`).join("")}
            <td class="pending-cell">
              <textarea class="pending-input" data-user-id="${escapeHtml(userId)}" data-field="weekly_other_pending" placeholder="补充本周其他待办或跨天事项"${canEdit ? "" : " disabled"}>${escapeHtml(member.weekly_other_pending || "")}</textarea>
            </td>
          </tr>
        `;
      }).join("");
      departmentPlanBody.querySelectorAll('.plan-day-input').forEach((element) => {
        element.disabled = !canEdit;
      });
      window.requestAnimationFrame(syncDepartmentPlanMemberHeights);
    }

    function renderMemberSelect(payload) {
      if (!payload || !payload.show_daily_section) {
        memberUserSelect.innerHTML = '<option value="">当前账号不展示每日事项</option>';
        memberUserSelect.disabled = true;
        selectedMemberUserId = "";
        return;
      }
      const members = Array.isArray(payload && payload.members) ? payload.members : [];
      if (!members.length) {
        memberUserSelect.innerHTML = '<option value="">当前部门暂无成员</option>';
        memberUserSelect.disabled = true;
        selectedMemberUserId = "";
        return;
      }
      const availableIds = members.map((member) => String(member && member.user && member.user.user_id || "").trim()).filter(Boolean);
      if (!availableIds.includes(selectedMemberUserId)) {
        selectedMemberUserId = availableIds[0] || "";
      }
      memberUserSelect.disabled = false;
      memberUserSelect.innerHTML = members.map((member) => {
        const user = member.user || {};
        const userId = String(user.user_id || "").trim();
        const selectedAttr = userId === selectedMemberUserId ? ' selected' : '';
        return `<option value="${escapeHtml(userId)}"${selectedAttr}>${escapeHtml(user.display_name || userId || "未命名用户")}</option>`;
      }).join("");
      memberUserSelect.value = selectedMemberUserId;
    }

    function renderLogItems(items) {
      const list = Array.isArray(items) ? items : [];
      if (!list.length) {
        return '<div class="empty-card">当天还没有填写事项</div>';
      }
      return `<div class="log-list">${list.map((item) => {
        const tags = [
          item.item_type ? `<span class="tiny-tag">${escapeHtml(item.item_type)}</span>` : '',
          item.service_mode ? `<span class="tiny-tag">${escapeHtml(item.service_mode)}</span>` : '',
          item.project_type ? `<span class="tiny-tag">${escapeHtml(item.project_type)}</span>` : '',
          item.sales ? `<span class="tiny-tag">${escapeHtml(item.sales)}</span>` : '',
          item.work_hours ? `<span class="tiny-tag">${escapeHtml(String(item.work_hours))}h</span>` : '',
        ].filter(Boolean).join('');
        const extraBlocks = [
          item.pending_issues ? `<div>遗留事项：${escapeHtml(item.pending_issues)}</div>` : '',
          item.risk ? `<div>风险：${escapeHtml(item.risk)}</div>` : '',
        ].filter(Boolean).join('');
        return `
          <div class="log-item">
            <div class="log-item-head">
              <div class="log-item-title">${escapeHtml(item.customer_name || '未填写客户')}</div>
              <div class="tag-row">${tags}</div>
            </div>
            <div class="log-text">${escapeHtml(item.work_content || '未填写工作内容')}</div>
            ${extraBlocks ? `<div class="log-extra">${extraBlocks}</div>` : ''}
          </div>
        `;
      }).join('')}</div>`;
    }

    function renderDailyDayCell(day) {
      const dayLabel = String(day && day.weekday_label || '').trim();
      const workDate = String(day && day.work_date || '').trim();
      const hasEntry = Boolean(day && day.has_entry);
      const totalHours = String(day && day.total_hours || '0').trim() || '0';
      const itemCount = Number(day && day.item_count || 0);
      const updatedAt = String(day && day.updated_at || '').trim() || '未更新';
      return `
        <td class="daily-day-cell">
          <div class="daily-day-head">
            <div class="daily-day-title">
              <div class="daily-day-name">${escapeHtml(dayLabel)}</div>
              <div class="daily-day-stat">${hasEntry ? `${escapeHtml(totalHours)}h / ${escapeHtml(String(itemCount))} 项` : '未填写'}</div>
            </div>
            <div class="daily-day-date">${escapeHtml(formatDateLabel(workDate))}</div>
            <div class="daily-day-updated">${escapeHtml(updatedAt)}</div>
          </div>
          ${renderLogItems(day && day.items)}
        </td>
      `;
    }

    function renderSelectedMemberDailyItems() {
      if (!canViewDailySection()) {
        selectedMemberMetaEl.innerHTML = '';
        selectedMemberNoteEl.textContent = '';
        memberDailyBodyEl.innerHTML = '';
        return;
      }
      const member = getMemberByUserId(selectedMemberUserId);
      if (!member) {
        selectedMemberMetaEl.innerHTML = '';
        selectedMemberNoteEl.textContent = '当前没有可查看的用户。';
        memberDailyBodyEl.innerHTML = '<tr><td colspan="7"><div class="empty-card full-width-note">请选择有效用户后查看其本周事项。</div></td></tr>';
        return;
      }
      const user = member.user || {};
      const weekStats = member.week_stats || {};
      selectedMemberMetaEl.innerHTML = [
        user.display_name || user.user_id || '未命名用户',
        `本周工时 ${weekStats.total_hours || '0'}h`,
        `填写天数 ${weekStats.filled_days || 0}`,
        `事项 ${weekStats.total_items || 0}`,
      ].map(renderChip).join('');
      selectedMemberNoteEl.textContent = `${formatRole(user)} · 当前查看 ${latestPayload && latestPayload.week_start || '-'} 至 ${latestPayload && latestPayload.week_end || '-'} 这一周。`;
      const days = Array.isArray(member.days) ? member.days : [];
      memberDailyBodyEl.innerHTML = `<tr>${days.map((day) => renderDailyDayCell(day)).join('')}</tr>`;
    }

    function getWeeklyPlanRowPayload(userId) {
      const normalizedUserId = String(userId || '').trim();
      const row = findDepartmentPlanRow(normalizedUserId);
      if (!row) {
        return null;
      }
      const weekly_plan_rows = Array.from({ length: 7 }, (_, index) => {
        const amEl = row.querySelector(`[data-day-index="${index}"][data-part="am"]`);
        const pmEl = row.querySelector(`[data-day-index="${index}"][data-part="pm"]`);
        return {
          am: String(amEl && amEl.value || '').trim(),
          pm: String(pmEl && pmEl.value || '').trim(),
        };
      });
      const pendingEl = row.querySelector('[data-field="weekly_other_pending"]');
      return {
        weekly_plan_rows,
        weekly_other_pending: String(pendingEl && pendingEl.value || '').trim(),
      };
    }

    function resetMemberWeeklyPlanRow(userId) {
      const member = getMemberByUserId(userId);
      const row = findDepartmentPlanRow(userId);
      if (!member || !row) {
        return;
      }
      const timerId = planAutoSaveTimers.get(String(userId || '').trim());
      if (timerId) {
        window.clearTimeout(timerId);
        planAutoSaveTimers.delete(String(userId || '').trim());
      }
      const weeklyRows = Array.isArray(member.weekly_plan_rows) ? member.weekly_plan_rows : [];
      weeklyRows.forEach((dayRow, index) => {
        const amEl = row.querySelector(`[data-day-index="${index}"][data-part="am"]`);
        const pmEl = row.querySelector(`[data-day-index="${index}"][data-part="pm"]`);
        if (amEl) {
          amEl.value = String(dayRow && dayRow.am || '');
        }
        if (pmEl) {
          pmEl.value = String(dayRow && dayRow.pm || '');
        }
      });
      const pendingEl = row.querySelector('[data-field="weekly_other_pending"]');
      if (pendingEl) {
        pendingEl.value = String(member.weekly_other_pending || '');
      }
      window.requestAnimationFrame(syncDepartmentPlanMemberHeights);
      setStatus(`已恢复 ${member.user && member.user.display_name || userId} 的当前周安排。`);
      setPlanRowStatus(userId, '已恢复为最近一次保存内容。');
    }

    function scheduleMemberWeeklyPlanAutosave(userId) {
      const normalizedUserId = String(userId || '').trim();
      if (!normalizedUserId || !canEditDepartmentWeeklyPlan()) {
        return;
      }
      const existingTimer = planAutoSaveTimers.get(normalizedUserId);
      if (existingTimer) {
        window.clearTimeout(existingTimer);
      }
      setPlanRowStatus(normalizedUserId, '已修改，1 秒后自动保存...');
      const timerId = window.setTimeout(() => {
        planAutoSaveTimers.delete(normalizedUserId);
        if (planSaveInFlightUsers.has(normalizedUserId)) {
          scheduleMemberWeeklyPlanAutosave(normalizedUserId);
          return;
        }
        saveMemberWeeklyPlan(normalizedUserId, { source: 'auto' });
      }, PLAN_AUTO_SAVE_DELAY_MS);
      planAutoSaveTimers.set(normalizedUserId, timerId);
    }

    async function flushPendingPlanAutoSaves() {
      if (!planAutoSaveTimers.size) {
        return;
      }
      const pendingUserIds = Array.from(planAutoSaveTimers.keys());
      pendingUserIds.forEach((userId) => {
        const timerId = planAutoSaveTimers.get(userId);
        if (timerId) {
          window.clearTimeout(timerId);
        }
        planAutoSaveTimers.delete(userId);
      });
      for (const userId of pendingUserIds) {
        await saveMemberWeeklyPlan(userId, { source: 'auto' });
      }
    }

    async function saveMemberWeeklyPlan(userId, options = {}) {
      const normalizedUserId = String(userId || '').trim();
      const member = getMemberByUserId(normalizedUserId);
      const rowPayload = getWeeklyPlanRowPayload(normalizedUserId);
      const source = String(options && options.source || 'manual');
      if (!member || !rowPayload || !latestPayload) {
        setStatus('未找到要保存的用户安排。', true);
        return;
      }
      if (!canEditDepartmentWeeklyPlan()) {
        setStatus('当前账号没有编辑部门本周安排的权限。', true);
        setPlanRowStatus(normalizedUserId, '没有编辑权限。', true);
        return;
      }
      if (planSaveInFlightUsers.has(normalizedUserId)) {
        if (source === 'auto') {
          scheduleMemberWeeklyPlanAutosave(normalizedUserId);
        }
        return;
      }
      const pendingTimer = planAutoSaveTimers.get(normalizedUserId);
      if (pendingTimer) {
        window.clearTimeout(pendingTimer);
        planAutoSaveTimers.delete(normalizedUserId);
      }
      planSaveInFlightUsers.add(normalizedUserId);
      setPlanRowStatus(normalizedUserId, source === 'auto' ? '自动保存中...' : '正在保存...');
      try {
        const response = await fetch('/api/department-schedule/weekly-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: normalizedUserId,
            week_start: latestPayload.week_start,
            weekly_plan_rows: rowPayload.weekly_plan_rows,
            weekly_other_pending: rowPayload.weekly_other_pending,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || '保存失败');
        }
        member.weekly_plan_rows = Array.isArray(payload.weekly_plan_rows) ? payload.weekly_plan_rows : [];
        member.weekly_other_pending = String(payload.weekly_other_pending || '');
        member.weekly_plan_updated_at = String(payload.updated_at || '');
        renderToolbarSummary(latestPayload);
        window.requestAnimationFrame(syncDepartmentPlanMemberHeights);
        setStatus(`${member.user && member.user.display_name || normalizedUserId} 的本周安排已保存。`);
        setPlanRowStatus(normalizedUserId, `最近保存：${member.weekly_plan_updated_at || '刚刚'}`);
      } catch (error) {
        setStatus(error.message || '保存失败，请稍后重试。', true);
        setPlanRowStatus(normalizedUserId, error.message || '保存失败，请稍后重试。', true);
      } finally {
        planSaveInFlightUsers.delete(normalizedUserId);
      }
    }

    function applyPayload(payload) {
      latestPayload = payload;
      clearAllPlanAutoSaveTimers();
      hideStateCard();
      applyPayloadViewVisibility(payload);
      renderDepartmentSelect(payload);
      renderToolbarSummary(payload);
      renderDepartmentPlanTable(payload);
      renderMemberSelect(payload);
      renderSelectedMemberDailyItems();
      const viewer = payload.viewer || {};
      passwordButton.hidden = !canCurrentUserChangePassword(viewer);
      setStatus(`已加载 ${payload.selected_department_label || '全部部门'} 在 ${payload.week_start || '-'} 当周的安排。`);
    }

    async function loadDepartmentSchedule(options = {}) {
      if (options.flushPending !== false) {
        await flushPendingPlanAutoSaves();
      }
      if (!options.silent) {
        setStatus('正在加载部门周安排...');
      }
      const currentSelectedMember = String(memberUserSelect.value || selectedMemberUserId || '').trim();
      if (currentSelectedMember) {
        selectedMemberUserId = currentSelectedMember;
      }
      const params = new URLSearchParams();
      params.set('date', String(dateInput.value || '__INITIAL_DATE__').trim() || '__INITIAL_DATE__');
      const selectedDepartment = String(departmentSelect.value || '').trim();
      if (selectedDepartment) {
        params.set('department', selectedDepartment);
      }
      try {
        const response = await fetch(`/api/department-schedule?${params.toString()}`);
        const payload = await response.json();
        if (!response.ok) {
          throw { status: response.status, message: payload.error || '加载失败' };
        }
        applyPayload(payload);
      } catch (error) {
        const statusCode = Number(error && error.status || 0);
        const message = String(error && error.message || '加载失败，请稍后重试。');
        if (statusCode === 401) {
          setViewerMetaText('当前登录：未登录');
          passwordButton.hidden = true;
          showStateCard('请先登录', message, false);
        } else if (statusCode === 403) {
          setViewerMetaText('当前登录：无权访问当前页面');
          passwordButton.hidden = true;
          showStateCard('没有访问权限', message, !backAdminPageButton.hidden);
        } else {
          passwordButton.hidden = true;
          showStateCard('读取失败', message, !backAdminPageButton.hidden);
        }
        setStatus(message, true);
      }
    }

    document.getElementById('back-user-page').addEventListener('click', () => {
      window.location.href = '/';
    });
    backAdminPageButton.addEventListener('click', () => {
      window.location.href = '/admin';
    });
    logoutPageButton.addEventListener('click', async () => {
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } finally {
        window.location.href = '/';
      }
    });
    document.getElementById('state-go-user').addEventListener('click', () => {
      window.location.href = '/';
    });
    document.getElementById('state-go-admin').addEventListener('click', () => {
      window.location.href = '/admin';
    });
    passwordButton.addEventListener('click', openPasswordOverlay);
    passwordOverlayCloseButton.addEventListener('click', closePasswordOverlay);
    passwordOverlay.addEventListener('click', (event) => {
      if (event.target === passwordOverlay) {
        closePasswordOverlay();
      }
    });
    [passwordCurrentInput, passwordNewInput, passwordConfirmInput].forEach((input) => {
      input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          submitPasswordUpdate();
        }
      });
    });
    passwordSubmitButton.addEventListener('click', submitPasswordUpdate);
    themeToggleButton.addEventListener('click', () => {
      const nextTheme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
      writeStoredThemePreference(nextTheme);
      applyVisualSettings(currentUiSettings);
      scheduleAutoThemeRefresh();
    });
    backgroundSettingsButton.addEventListener('click', (event) => {
      event.stopPropagation();
      setBackgroundSettingsOpen(!isBackgroundSettingsOpen);
    });
    backgroundSettingsMenu.addEventListener('click', (event) => {
      event.stopPropagation();
    });
    selectBackgroundImageButton.addEventListener('click', () => backgroundImageInput.click());
    useBingBackgroundButton.addEventListener('click', () => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: BING_DAILY_BACKGROUND_PATH });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    backgroundImageInput.addEventListener('change', (event) => {
      const [file] = event.target.files || [];
      handleBackgroundImageSelection(file);
      backgroundImageInput.value = '';
    });
    clearBackgroundImageButton.addEventListener('click', () => {
      if (!currentUiSettings.background_image) {
        return;
      }
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: '' });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    backgroundModeSelect.addEventListener('change', (event) => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_mode: event.target.value });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    regionOpacityInput.addEventListener('input', (event) => {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, region_opacity: Number(event.target.value) / 100 });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    });
    document.addEventListener('click', (event) => {
      if (
        isBackgroundSettingsOpen
        && !backgroundSettingsMenu.contains(event.target)
        && !backgroundSettingsButton.contains(event.target)
      ) {
        setBackgroundSettingsOpen(false);
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        setBackgroundSettingsOpen(false);
        if (isPasswordOverlayOpen) {
          closePasswordOverlay();
        }
      }
    });
    window.addEventListener('resize', () => {
      window.requestAnimationFrame(syncDepartmentPlanMemberHeights);
    });
    document.getElementById('reload-schedule-button').addEventListener('click', () => {
      loadDepartmentSchedule();
    });
    document.getElementById('prev-week-button').addEventListener('click', () => {
      dateInput.value = shiftDateByDays(dateInput.value, -7);
      loadDepartmentSchedule();
    });
    document.getElementById('next-week-button').addEventListener('click', () => {
      dateInput.value = shiftDateByDays(dateInput.value, 7);
      loadDepartmentSchedule();
    });
    dateInput.addEventListener('change', () => {
      loadDepartmentSchedule();
    });
    departmentSelect.addEventListener('change', () => {
      loadDepartmentSchedule();
    });
    memberUserSelect.addEventListener('change', () => {
      selectedMemberUserId = String(memberUserSelect.value || '').trim();
      renderSelectedMemberDailyItems();
    });
    departmentPlanBody.addEventListener('input', (event) => {
      const input = event.target.closest('.plan-day-input, .pending-input');
      if (!input || !canEditDepartmentWeeklyPlan()) {
        return;
      }
      window.requestAnimationFrame(syncDepartmentPlanMemberHeights);
      scheduleMemberWeeklyPlanAutosave(input.getAttribute('data-user-id') || '');
    });

    initializePasswordToggleFields();
    applyVisualSettings(currentUiSettings);
    scheduleAutoThemeRefresh();
    loadDepartmentSchedule();
  </script>
</body>
</html>
"""


def render_department_schedule_html(*, app_version: str, initial_date: str, initial_ui_settings_json: str) -> str:
    html = DEPARTMENT_SCHEDULE_HTML.replace("__INITIAL_DATE__", initial_date)
    html = html.replace("__APP_VERSION__", app_version)
    html = html.replace("__INITIAL_UI_SETTINGS_PAYLOAD__", initial_ui_settings_json)
    return html
