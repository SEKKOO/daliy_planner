from __future__ import annotations


MOBILE_SCHEDULE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>日程管理</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: rgba(255, 255, 255, 0.95);
      --panel-soft: rgba(247, 250, 255, 0.98);
      --line: #d7e2ef;
      --text: #17324d;
      --muted: #6c849c;
      --primary: #2a63c5;
      --primary-soft: #e6efff;
      --primary-deep: #18478d;
      --danger: #c53f51;
      --shadow: 0 14px 28px rgba(31, 71, 128, 0.08);
      --radius: 16px;
      --radius-sm: 12px;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      min-height: 100%;
      background: linear-gradient(180deg, #edf4ff 0%, #f8fbff 38%, #f4f7fb 100%);
      color: var(--text);
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }

    body {
      padding: env(safe-area-inset-top, 0) 0 env(safe-area-inset-bottom, 0);
    }

    button,
    input,
    textarea {
      font: inherit;
    }

    button {
      border: none;
      cursor: pointer;
      border-radius: 999px;
    }

    input,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 12px;
      padding: 9px 11px;
    }

    textarea {
      min-height: 50px;
      resize: none;
      overflow-y: hidden;
      line-height: 1.45;
      font-size: 12px;
    }

    .shell {
      width: min(100%, 760px);
      margin: 0 auto;
      padding: 8px 8px 16px;
    }

    .card {
      background: var(--panel);
      border: 1px solid rgba(215, 226, 239, 0.9);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .login-card,
    .page-card {
      padding: 10px;
    }

    .section-title {
      margin: 0 0 8px;
      font-size: 16px;
    }

    .section-text {
      margin: 0 0 12px;
      font-size: 11px;
      color: var(--muted);
      line-height: 1.55;
    }

    .stack {
      display: grid;
      gap: 10px;
    }

    .field {
      display: grid;
      gap: 6px;
    }

    .field-label {
      font-size: 12px;
      color: var(--muted);
    }

    .status {
      min-height: 18px;
      margin: 8px 0 10px;
      font-size: 12px;
      color: var(--muted);
    }

    .status.is-error {
      color: var(--danger);
    }

    .primary-btn {
      width: 100%;
      padding: 11px 14px;
      font-weight: 700;
      border-radius: 13px;
      background: var(--primary);
      color: #fff;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 8px;
    }

    .toolbar input[type="date"] {
      width: clamp(126px, 38vw, 148px);
      min-width: 126px;
      flex: 0 0 clamp(126px, 38vw, 148px);
      padding: 7px 9px;
      font-size: 11px;
      min-height: 31px;
    }

    .toolbar-actions {
      display: flex;
      align-items: center;
      gap: 5px;
      margin-left: auto;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .toolbar-btn {
      min-height: 30px;
      padding: 0 9px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }

    .compact-toggle {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: rgba(255, 255, 255, 0.9);
      color: var(--muted);
      font-size: 11px;
      line-height: 1.2;
      user-select: none;
      white-space: nowrap;
    }

    .compact-toggle input {
      width: 14px;
      height: 14px;
      margin: 0;
      accent-color: var(--primary);
      flex: 0 0 auto;
    }

    .toolbar-btn.soft {
      background: var(--primary-soft);
      color: var(--primary-deep);
    }

    .toolbar-btn.ghost {
      background: transparent;
      border: 1px solid var(--line);
      color: var(--muted);
    }

    .picker-block {
      border: 1px solid var(--line);
      border-radius: 13px;
      background: var(--panel-soft);
      padding: 8px;
      margin-bottom: 8px;
    }

    .picker-group {
      display: grid;
      gap: 6px;
      min-width: 0;
    }

    .picker-group + .picker-group {
      margin-top: 8px;
    }

    .picker-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      align-items: start;
    }

    .picker-grid .picker-group + .picker-group {
      margin-top: 0;
    }

    .picker-select {
      position: relative;
    }

    .picker-select-trigger {
      width: 100%;
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #fff;
      color: var(--text);
      font-size: 11px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      text-align: left;
    }

    .picker-select-trigger::after {
      content: "";
      flex: 0 0 auto;
      width: 0;
      height: 0;
      border-left: 4px solid transparent;
      border-right: 4px solid transparent;
      border-top: 5px solid var(--muted);
      transition: transform 0.16s ease;
    }

    .picker-select-trigger[aria-expanded="true"]::after {
      transform: rotate(180deg);
    }

    .picker-select-trigger:disabled {
      opacity: 0.58;
      cursor: not-allowed;
    }

    .picker-select-menu {
      position: absolute;
      left: 0;
      right: 0;
      top: calc(100% + 6px);
      z-index: 30;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.98);
      box-shadow: 0 12px 24px rgba(28, 60, 110, 0.12);
      padding: 6px;
      max-height: 220px;
      overflow: auto;
    }

    .picker-option {
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 7px 7px;
      border-radius: 9px;
      font-size: 11px;
      color: var(--text);
    }

    .picker-option + .picker-option {
      margin-top: 2px;
    }

    .picker-option input {
      width: 14px;
      height: 14px;
      margin: 0;
      accent-color: var(--primary);
      flex: 0 0 auto;
    }

    .picker-option:active,
    .picker-option.is-selected {
      background: var(--primary-soft);
    }

    .picker-empty {
      padding: 8px;
      font-size: 11px;
      color: var(--muted);
    }

    .summary-line,
    .empty-copy,
    .helper-text,
    .day-empty {
      font-size: 11px;
      color: var(--muted);
      line-height: 1.55;
    }

    .summary-line {
      margin-bottom: 6px;
      font-size: 10px;
      line-height: 1.4;
    }

    .member-list {
      display: grid;
      gap: 6px;
    }

    .member-list.two-column {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 5px;
    }

    .member-list.two-column .member-card {
      padding: 7px;
      border-radius: 11px;
    }

    .member-list.two-column .member-head {
      display: grid;
      gap: 4px;
      margin-bottom: 6px;
    }

    .member-list.two-column .member-name {
      font-size: 12px;
    }

    .member-list.two-column .member-stats {
      width: fit-content;
      max-width: 100%;
      white-space: normal;
      font-size: 10px;
      padding: 3px 6px;
    }

    .member-list.two-column .week-grid {
      gap: 5px;
    }

    .member-list.two-column .week-row {
      padding: 6px;
    }

    .member-list.two-column .week-fields {
      gap: 4px;
    }

    .member-list.two-column .field-label {
      font-size: 10px;
    }

    .member-list.two-column .week-fields textarea,
    .member-list.two-column .pending-block textarea {
      min-height: 38px;
      padding: 6px 6px;
      font-size: 11px;
    }

    .member-list.two-column .pending-block {
      margin-top: 6px;
      gap: 4px;
    }

    .member-list.two-column .helper-text {
      font-size: 10px;
      line-height: 1.35;
    }

    .member-list.two-column .day-card {
      padding: 6px;
    }

    .member-list.two-column .day-head,
    .member-list.two-column .day-meta,
    .member-list.two-column .day-item,
    .member-list.two-column .day-empty {
      font-size: 10px;
    }

    .member-list.two-column .member-actions {
      margin-top: 6px;
    }

    .member-list.two-column .save-btn {
      width: 100%;
      min-height: 28px;
      padding: 0 8px;
      font-size: 10px;
    }

    .empty-state {
      border: 1px dashed var(--line);
      border-radius: 13px;
      background: rgba(255, 255, 255, 0.72);
      padding: 14px 12px;
      text-align: center;
    }

    .empty-title {
      margin: 0 0 4px;
      font-size: 13px;
      font-weight: 700;
      color: var(--text);
    }

    .member-card {
      border: 1px solid var(--line);
      border-radius: 13px;
      background: rgba(248, 251, 255, 0.98);
      padding: 8px;
    }

    .member-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 6px;
    }

    .member-head > div {
      min-width: 0;
    }

    .member-name {
      font-size: 13px;
      font-weight: 700;
      line-height: 1.2;
    }

    .member-stats {
      flex: 0 0 auto;
      font-size: 10px;
      color: var(--primary-deep);
      background: var(--primary-soft);
      border-radius: 999px;
      padding: 3px 7px;
      white-space: nowrap;
    }

    .week-grid {
      display: grid;
      gap: 5px;
    }

    .week-row {
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 10px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.70), rgba(247,250,255,0.42)),
        linear-gradient(135deg, rgba(42,99,197,0.08), rgba(42,99,197,0.02));
      padding: 6px;
      box-shadow: 0 10px 20px rgba(31, 71, 128, 0.07), inset 0 1px 0 rgba(255,255,255,0.46);
      backdrop-filter: blur(12px) saturate(130%);
      -webkit-backdrop-filter: blur(12px) saturate(130%);
    }

    .week-day-group {
      display: grid;
      gap: 5px;
      padding: 7px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: var(--panel-soft);
    }

    .week-day-group-head {
      display: flex;
      justify-content: space-between;
      gap: 6px;
      color: var(--primary-deep);
      font-size: 11px;
      font-weight: 700;
    }

    .week-day-group-head span:last-child {
      color: var(--muted);
      font-weight: 500;
    }

    .schedule-item-time-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 26px;
      align-items: stretch;
      gap: 2px;
      color: var(--muted);
      font-size: 10px;
    }

    .schedule-item-time-stack {
      min-width: 0;
      display: grid;
      gap: 1px;
    }

    .schedule-item-time-row input[type="time"] {
      min-width: 0;
      height: 20px;
      min-height: 20px;
      padding: 0 5px;
      border-radius: 7px;
      background: rgba(255,255,255,0.40);
      border-color: rgba(255,255,255,0.58);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.24);
      font-size: 10px;
      line-height: 1;
    }

    .schedule-item-time-row input[type="text"] {
      min-width: 0;
      height: 20px;
      min-height: 20px;
      padding: 0 5px;
      border-radius: 7px;
      background: rgba(255,255,255,0.40);
      border-color: rgba(255,255,255,0.58);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.24);
      font-size: 10px;
      line-height: 1;
    }

    .schedule-item-time-row button,
    .schedule-item-add {
      min-height: 27px;
      padding: 5px 7px;
      font-size: 10px;
      white-space: nowrap;
    }

    .schedule-item-delete {
      min-width: 26px;
      min-height: 41px;
      align-self: stretch;
      display: grid;
      grid-template-rows: 1fr 1fr;
      place-items: center;
      padding: 0 4px;
      line-height: 1;
      white-space: normal;
    }

    .schedule-item-delete span {
      display: block;
    }

    .calendar-sync-badge {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      min-height: 15px;
      padding: 1px 5px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--muted);
      font-size: 9px;
      line-height: 1.2;
      white-space: nowrap;
    }

    .calendar-sync-caption {
      color: var(--muted);
      font-size: 9px;
      font-weight: 600;
      line-height: 1.35;
      white-space: normal;
    }

    .calendar-sync-inline {
      display: block;
      min-width: 0;
      overflow: hidden;
      color: var(--muted);
      font-size: 9px;
      font-weight: 700;
      line-height: 1.2;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .calendar-sync-state.success { color: #1e8a64; }
    .calendar-sync-state.pending { color: var(--primary-deep); }
    .calendar-sync-state.warning { color: #9a6412; }
    .calendar-sync-state.danger { color: var(--danger); }
    .calendar-sync-state.muted,
    .calendar-sync-state.neutral { color: var(--muted); }

    .schedule-item-sync-row {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
      min-height: 11px;
      margin-bottom: 2px;
    }

    .schedule-item-editor textarea {
      min-height: 42px;
      background: rgba(255,255,255,0.38);
      border-color: rgba(255,255,255,0.58);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.24);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }

    .schedule-item-location {
      min-height: 30px;
      padding: 6px 7px;
      background: rgba(255,255,255,0.34);
      border-color: rgba(255,255,255,0.54);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.20);
      font-size: 11px;
    }

    .schedule-item-add {
      width: 100%;
      border: 1px dashed var(--line);
      background: transparent;
      color: var(--primary-deep);
    }

    .schedule-item-create-form {
      display: grid;
      gap: 6px;
      padding: 7px;
      border: 1px solid rgba(33, 114, 207, 0.24);
      border-radius: 10px;
      background: rgba(238, 247, 255, 0.78);
    }

    .schedule-item-create-form label {
      display: grid;
      gap: 3px;
      color: var(--muted);
      font-size: 10px;
      font-weight: 700;
    }

    .schedule-item-create-input {
      width: 100%;
      min-width: 0;
      padding: 6px 7px;
      font-size: 11px;
    }
    .schedule-item-create-time-row .schedule-item-create-input {
      height: 22px;
      min-height: 22px;
      padding: 1px 6px;
      border-radius: 7px;
      font-size: 10px;
      line-height: 1;
    }

    .schedule-item-create-title {
      min-height: 42px;
      resize: vertical;
    }

    .schedule-item-create-time-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 5px;
    }

    .schedule-item-create-error {
      min-height: 15px;
      color: var(--danger);
      font-size: 10px;
      line-height: 1.4;
    }

    .schedule-item-create-actions {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 5px;
    }

    .schedule-item-create-actions button {
      min-height: 27px;
      padding: 5px 7px;
      font-size: 10px;
    }

    .week-fields {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 4px;
    }

    .week-prefix {
      color: var(--primary);
      font-weight: 700;
    }

    .week-fields .field {
      gap: 3px;
    }

    .week-fields textarea {
      min-height: 40px;
      padding: 6px 7px;
      font-size: 11px;
    }

    .pending-block {
      margin-top: 6px;
      display: grid;
      gap: 4px;
    }

    .pending-block textarea {
      min-height: 38px;
      padding: 6px 7px;
      font-size: 11px;
    }

    .compact-helper {
      margin-top: 4px;
    }

    .daily-list {
      display: grid;
      gap: 5px;
      margin-top: 6px;
    }

    .day-card {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      padding: 6px;
    }

    .day-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 3px;
      font-size: 10px;
      font-weight: 700;
    }

    .day-meta {
      color: var(--muted);
      font-weight: 500;
      font-size: 10px;
    }

    .day-items {
      display: grid;
      gap: 3px;
    }

    .day-item {
      font-size: 10px;
      line-height: 1.35;
      color: var(--text);
      padding-left: 9px;
      position: relative;
    }

    .day-item::before {
      content: "";
      position: absolute;
      left: 0;
      top: 7px;
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: var(--primary);
    }

    .member-actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 6px;
    }

    .save-btn {
      min-height: 28px;
      padding: 0 10px;
      border-radius: 11px;
      background: var(--primary);
      color: #fff;
      font-size: 10px;
      font-weight: 700;
    }

    button:disabled,
    input:disabled,
    textarea:disabled {
      opacity: 0.58;
      cursor: not-allowed;
    }

    [hidden] {
      display: none !important;
    }

    @media (max-width: 380px) {
      .shell {
        padding-left: 8px;
        padding-right: 8px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card login-card" id="mobile-login-card">
      <h2 class="section-title">登录</h2>
      <p class="section-text">登录后查看并维护当前可访问范围内的日程管理内容。账号为拼音全拼，密码默认为拼音全拼@123。</p>
      <div class="stack">
        <label class="field">
          <span class="field-label">用户名</span>
          <input id="mobile-login-username" type="text" autocomplete="username" placeholder="zhangsan">
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input id="mobile-login-password" type="password" autocomplete="current-password" placeholder="zhangsan@123">
        </label>
      </div>
      <div class="status" id="mobile-login-status" aria-live="polite"></div>
      <button type="button" class="primary-btn" id="mobile-login-button">登录并进入日程管理</button>
    </section>

    <section class="card page-card" id="mobile-page-card" hidden>
      <div class="toolbar">
        <input id="mobile-anchor-date" type="date" value="__INITIAL_DATE__">
        <div class="toolbar-actions">
          <button type="button" class="toolbar-btn soft" id="mobile-refresh-button">刷新</button>
          <button type="button" class="toolbar-btn soft" id="mobile-sync-dingtalk-calendar-button">同步钉钉</button>
          <label class="compact-toggle">
            <input id="mobile-compact-toggle" type="checkbox" checked>
            <span>精简显示</span>
          </label>
          <button type="button" class="toolbar-btn ghost" id="mobile-clear-filter-button" hidden>清空选择</button>
          <button type="button" class="toolbar-btn ghost" id="mobile-logout-button" hidden>退出</button>
        </div>
      </div>

      <div class="picker-block">
        <div class="picker-grid">
          <div class="picker-group">
            <div class="picker-select">
              <button type="button" class="picker-select-trigger" id="mobile-position-trigger" aria-expanded="false">选择岗位</button>
              <div class="picker-select-menu" id="mobile-position-menu" hidden></div>
            </div>
          </div>
          <div class="picker-group">
            <div class="picker-select">
              <button type="button" class="picker-select-trigger" id="mobile-member-trigger" aria-expanded="false">选择人员</button>
              <div class="picker-select-menu" id="mobile-member-menu" hidden></div>
            </div>
          </div>
        </div>
      </div>

      <div class="summary-line" id="mobile-summary-line"></div>
      <div class="status" id="mobile-page-status" aria-live="polite"></div>
      <div class="member-list" id="mobile-member-list"></div>
    </section>
  </main>

  <script>
    const bootAuthState = __INITIAL_AUTH_STATE_PAYLOAD__;

    const loginCardEl = document.getElementById("mobile-login-card");
    const loginUsernameEl = document.getElementById("mobile-login-username");
    const loginPasswordEl = document.getElementById("mobile-login-password");
    const loginStatusEl = document.getElementById("mobile-login-status");
    const loginButtonEl = document.getElementById("mobile-login-button");
    const pageCardEl = document.getElementById("mobile-page-card");
    const anchorDateEl = document.getElementById("mobile-anchor-date");
    const refreshButtonEl = document.getElementById("mobile-refresh-button");
    const syncDingtalkCalendarButton = document.getElementById("mobile-sync-dingtalk-calendar-button");
    const logoutButtonEl = document.getElementById("mobile-logout-button");
    const clearFilterButtonEl = document.getElementById("mobile-clear-filter-button");
    const compactToggleEl = document.getElementById("mobile-compact-toggle");
    const positionTriggerEl = document.getElementById("mobile-position-trigger");
    const positionMenuEl = document.getElementById("mobile-position-menu");
    const memberTriggerEl = document.getElementById("mobile-member-trigger");
    const memberMenuEl = document.getElementById("mobile-member-menu");
    const summaryLineEl = document.getElementById("mobile-summary-line");
    const pageStatusEl = document.getElementById("mobile-page-status");
    const memberListEl = document.getElementById("mobile-member-list");
    const WEEKLY_PLAN_TIME_PATTERN = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

    let authState = normalizeAuthState(bootAuthState);
    let pagePayload = null;
    let isLoggingIn = false;
    let isLoading = false;
    let isCalendarSyncing = false;
    let savingUserIds = new Set();
    let selectedMemberIds = [];
    let selectedPositions = [];
    let openDropdown = "";
    let compactModeEnabled = true;
    let scheduleCreateFormKeys = new Set();

    function normalizeAuthState(source) {
      const payload = source && typeof source === "object" ? source : {};
      const user = payload.user && typeof payload.user === "object" ? payload.user : null;
      return {
        authenticated: Boolean(payload.authenticated && user),
        user,
      };
    }

    function getCurrentViewerUserId() {
      return String(
        authState && authState.user && authState.user.user_id
        || pagePayload && pagePayload.viewer && pagePayload.viewer.user_id
        || ""
      ).trim();
    }

    function isDingtalkImportedScheduleItem(item) {
      return String(item && item.source || "").trim() === "dingtalk_calendar";
    }

    function isEditingAnotherUserSchedule(userId) {
      const viewerUserId = getCurrentViewerUserId();
      const targetUserId = String(userId || "").trim();
      return Boolean(viewerUserId && targetUserId && viewerUserId !== targetUserId);
    }

    function isProtectedCrossUserDingtalkItem(userId, item) {
      return isEditingAnotherUserSchedule(userId) && isDingtalkImportedScheduleItem(item);
    }

    function escapeHtml(value) {
      return String(value == null ? "" : value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function setStatus(target, message, isError = false) {
      target.textContent = message || "";
      target.classList.toggle("is-error", Boolean(isError && message));
    }

    function normalizeCalendarSyncState(sync) {
      const source = sync && typeof sync === "object" ? sync : {};
      return {
        status: String(source.status || "local_only").trim() || "local_only",
        label: String(source.label || "本地").trim() || "本地",
        tone: String(source.tone || "neutral").trim() || "neutral",
        hint: String(source.hint || "").trim(),
        calendar_name: String(source.calendar_name || "").trim(),
        event_id: String(source.event_id || "").trim(),
        enabled: Boolean(source.enabled),
      };
    }

    function getCalendarSyncToneClass(state) {
      const tone = String((state && state.tone) || "").trim();
      if (["success", "pending", "warning", "danger", "muted", "neutral"].includes(tone)) {
        return tone;
      }
      const status = String((state && state.status) || "").trim();
      if (status === "synced") {
        return "success";
      }
      if (status === "pending" || status === "syncing") {
        return "pending";
      }
      if (["remote_changed", "remote_deleted", "remote_cancelled"].includes(status)) {
        return "warning";
      }
      if (status === "failed" || status === "conflict") {
        return "danger";
      }
      if (status === "missing" || status === "idle" || status === "deleted") {
        return "muted";
      }
      return "neutral";
    }

    function renderCalendarSyncBadge(sync) {
      const state = normalizeCalendarSyncState(sync);
      const title = [state.hint, state.calendar_name ? `日历：${state.calendar_name}` : "", state.event_id ? `eventId：${state.event_id}` : ""]
        .filter(Boolean)
        .join(" · ");
      return `<span class="calendar-sync-inline" title="${escapeHtml(title)}">钉钉 · 同步状态：<span class="calendar-sync-state ${getCalendarSyncToneClass(state)}">${escapeHtml(state.label)}</span></span>`;
    }

    function renderScheduleItemSyncMeta(item) {
      return `<div class="schedule-item-sync-row">${renderCalendarSyncBadge(item && item.calendar_sync)}</div>`;
    }

    function getVisibleCalendarSyncText() {
      const visibleMembers = getVisibleMembers();
      if (!visibleMembers.length) {
        return "";
      }
      let configured = 0;
      let pending = 0;
      let failed = 0;
      visibleMembers.forEach((member) => {
        const sync = normalizeCalendarSyncState(member && member.calendar_sync);
        if (sync.enabled) {
          configured += 1;
        }
        if (sync.status === "pending" || sync.status === "syncing") {
          pending += 1;
        }
        if (sync.status === "failed" || sync.status === "conflict") {
          failed += 1;
        }
      });
      const parts = [`钉钉 ${configured}/${visibleMembers.length} 人已配置`];
      if (pending) {
        parts.push(`待处理 ${pending}`);
      }
      if (failed) {
        parts.push(`异常 ${failed}`);
      }
      return parts.join(" · ");
    }

    function normalizeKey(value) {
      return String(value || "").trim().toLowerCase();
    }

    function isWeekendLabel(label) {
      const normalized = String(label || "").trim();
      return normalized.includes("周六") || normalized.includes("周日");
    }

    function dedupeValues(values) {
      const seen = new Set();
      const result = [];
      (Array.isArray(values) ? values : []).forEach((value) => {
        const label = String(value || "").trim();
        const key = normalizeKey(label);
        if (!label || seen.has(key)) {
          return;
        }
        seen.add(key);
        result.push(label);
      });
      return result;
    }

    function getMemberName(member, fallbackIndex = 0) {
      const user = member && typeof member === "object" ? member.user || {} : {};
      return String(user.display_name || user.user_id || `成员 ${fallbackIndex + 1}`).trim();
    }

    function getMemberUserId(member) {
      const user = member && typeof member === "object" ? member.user || {} : {};
      return String(user.user_id || "").trim();
    }

    function getMemberPositionLabels(member) {
      const user = member && typeof member === "object" ? member.user || {} : {};
      const values = [];
      if (Array.isArray(user.position_labels)) {
        values.push(...user.position_labels);
      } else if (typeof user.position_labels === "string") {
        values.push(...String(user.position_labels || "").split(/[、,，/]/));
      }
      if (Array.isArray(user.positions)) {
        values.push(...user.positions);
      }
      values.push(user.position || "");
      return dedupeValues(values);
    }

    function getMemberOptions() {
      if (!(pagePayload && Array.isArray(pagePayload.members))) {
        return [];
      }
      return pagePayload.members
        .map((member, index) => ({
          userId: getMemberUserId(member),
          name: getMemberName(member, index),
        }))
        .filter((item) => item.userId);
    }

    function getPositionOptions() {
      const payloadOptions = pagePayload && Array.isArray(pagePayload.available_positions)
        ? dedupeValues(pagePayload.available_positions)
        : [];
      if (payloadOptions.length) {
        return payloadOptions;
      }
      if (!(pagePayload && Array.isArray(pagePayload.members))) {
        return [];
      }
      const labels = [];
      pagePayload.members.forEach((member) => {
        labels.push(...getMemberPositionLabels(member));
      });
      return dedupeValues(labels);
    }

    function getSelectedMemberNames() {
      const optionMap = new Map(getMemberOptions().map((item) => [normalizeKey(item.userId), item.name]));
      return selectedMemberIds
        .map((userId) => optionMap.get(normalizeKey(userId)) || "")
        .filter(Boolean);
    }

    function hasActiveFilter() {
      return Boolean(selectedMemberIds.length || selectedPositions.length);
    }

    function getFilterSummaryText() {
      const parts = [];
      if (selectedPositions.length) {
        parts.push(selectedPositions.length === 1 ? `岗位：${selectedPositions[0]}` : `岗位：已选 ${selectedPositions.length} 项`);
      }
      const memberNames = getSelectedMemberNames();
      if (memberNames.length) {
        parts.push(memberNames.length === 1 ? `人员：${memberNames[0]}` : `人员：已选 ${memberNames.length} 人`);
      }
      return parts.join(" · ");
    }

    function getVisibleMembers() {
      if (!(pagePayload && Array.isArray(pagePayload.members))) {
        return [];
      }
      if (!hasActiveFilter()) {
        return [];
      }
      const selectedMemberKeys = new Set(selectedMemberIds.map((item) => normalizeKey(item)));
      const selectedPositionKeys = new Set(selectedPositions.map((item) => normalizeKey(item)));
      return pagePayload.members.filter((member) => {
        const memberMatched = selectedMemberKeys.has(normalizeKey(getMemberUserId(member)));
        const positionMatched = getMemberPositionLabels(member).some((label) => selectedPositionKeys.has(normalizeKey(label)));
        return memberMatched || positionMatched;
      });
    }

    function getVisibleWeeklyPlanRows(member) {
      const rows = Array.isArray(member && member.weekly_plan_rows) ? member.weekly_plan_rows : [];
      if (!compactModeEnabled) {
        return rows;
      }
      return rows.filter((row) => !isWeekendLabel(row && row.weekday_label));
    }

    function addDaysToDateString(value, offset) {
      const source = String(value || "").trim();
      if (!source) {
        return "";
      }
      const dateValue = new Date(`${source}T00:00:00`);
      if (Number.isNaN(dateValue.getTime())) {
        return "";
      }
      dateValue.setDate(dateValue.getDate() + Number(offset || 0));
      return dateValue.toISOString().slice(0, 10);
    }

    function buildScheduleCreateFormKey(userId, dayIndex) {
      return `${String(userId || "").trim()}::${Number(dayIndex || 0)}`;
    }

    function sanitizeScheduleTimeInput(value) {
      return String(value || "")
        .trim()
        .replace(/[０-９]/g, (character) => String(character.charCodeAt(0) - 0xfee0))
        .replace(/[：；;]/g, ":")
        .replace(/\s+/g, "");
    }

    function normalizeScheduleTimeInput(value) {
      const source = sanitizeScheduleTimeInput(value);
      if (!source) {
        return "";
      }
      const hourOnlyMatch = source.match(/^(\d{1,2})$/);
      if (hourOnlyMatch) {
        const hour = Number(hourOnlyMatch[1]);
        return hour >= 0 && hour <= 23 ? `${String(hour).padStart(2, "0")}:00` : source;
      }
      const timeMatch = source.match(/^(\d{1,2}):(\d{1,2})$/);
      if (!timeMatch) {
        return source;
      }
      const hour = Number(timeMatch[1]);
      const minute = Number(timeMatch[2]);
      if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
        return source;
      }
      return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
    }

    function isScheduleTimeFieldName(fieldName) {
      return fieldName === "start_time" || fieldName === "end_time";
    }

    function sanitizeScheduleTimeField(input) {
      if (!(input instanceof HTMLInputElement)) {
        return "";
      }
      const sanitized = sanitizeScheduleTimeInput(input.value);
      if (sanitized !== String(input.value || "")) {
        input.value = sanitized;
      }
      return sanitized;
    }

    function normalizeScheduleTimeField(input) {
      if (!(input instanceof HTMLInputElement)) {
        return "";
      }
      const normalized = normalizeScheduleTimeInput(input.value);
      if (normalized !== String(input.value || "")) {
        input.value = normalized;
      }
      return normalized;
    }

    function normalizeScheduleItemsForSave(items) {
      return (Array.isArray(items) ? items : []).map((item) => {
        const source = item && typeof item === "object" ? item : {};
        return {
          ...source,
          start_time: normalizeScheduleTimeInput(source.start_time),
          end_time: normalizeScheduleTimeInput(source.end_time),
        };
      });
    }

    function validateScheduleTimeRange(startTime, endTime, title = "", options = {}) {
      const normalizedTitle = String(title || "").trim();
      const normalizedStart = normalizeScheduleTimeInput(startTime);
      const normalizedEnd = normalizeScheduleTimeInput(endTime);
      const requireTitle = !options || options.requireTitle !== false;
      if (requireTitle && !normalizedTitle) {
        return "请填写日程安排。";
      }
      if (!WEEKLY_PLAN_TIME_PATTERN.test(normalizedStart)) {
        return "开始时间必须是 HH:MM 格式，例如 09:00。";
      }
      if (!WEEKLY_PLAN_TIME_PATTERN.test(normalizedEnd)) {
        return "结束时间必须是 HH:MM 格式，例如 18:00。";
      }
      if (normalizedStart >= normalizedEnd) {
        return "结束时间必须晚于开始时间。";
      }
      return "";
    }

    function validateMemberScheduleItems(member) {
      const items = getMemberWeeklyPlanItems(member);
      for (const item of items) {
        const title = String(item && item.title || "").trim();
        const legacy = Boolean(item && (item.legacy_slot_key || item.source === "legacy"));
        if (!title && !legacy) {
          continue;
        }
        const message = validateScheduleTimeRange(
          item && item.start_time,
          item && item.end_time,
          title || "日程",
          { requireTitle: false }
        );
        if (message) {
          return title ? `日程“${title}”：${message}` : message;
        }
      }
      return "";
    }

    function setScheduleCreateFormError(form, message) {
      const errorEl = form && form.querySelector("[data-schedule-create-error]");
      if (errorEl) {
        errorEl.textContent = String(message || "").trim();
      }
    }

    function readScheduleCreateField(form, fieldName) {
      const input = form ? form.querySelector(`[data-schedule-create-field="${fieldName}"]`) : null;
      if (isScheduleTimeFieldName(fieldName)) {
        return normalizeScheduleTimeField(input);
      }
      return String(input && input.value || "").trim();
    }

    function renderScheduleItemCreateForm(userId, dayIndex) {
      return `
        <form class="schedule-item-create-form" data-schedule-create-form data-user-id="${escapeHtml(userId)}" data-day-index="${dayIndex}">
          <label>
            <span>安排</span>
            <textarea class="schedule-item-create-input schedule-item-create-title" data-schedule-create-field="title" placeholder="填写日程安排" required></textarea>
          </label>
          <div class="schedule-item-create-time-row">
            <label>
              <span>开始时间</span>
              <input class="schedule-item-create-input" type="text" data-schedule-create-field="start_time" inputmode="numeric" maxlength="5" placeholder="09:00" required>
            </label>
            <label>
              <span>结束时间</span>
              <input class="schedule-item-create-input" type="text" data-schedule-create-field="end_time" inputmode="numeric" maxlength="5" placeholder="10:00" required>
            </label>
          </div>
          <label>
            <span>地点（可选）</span>
            <input class="schedule-item-create-input" type="text" data-schedule-create-field="location" placeholder="填写地点">
          </label>
          <div class="schedule-item-create-error" data-schedule-create-error aria-live="polite"></div>
          <div class="schedule-item-create-actions">
            <button type="button" class="secondary" data-action="cancel-plan-item" data-user-id="${escapeHtml(userId)}" data-day-index="${dayIndex}">取消</button>
            <button type="submit" class="primary">新建</button>
          </div>
        </form>
      `;
    }

    function getMemberWeeklyPlanItems(member) {
      if (Array.isArray(member && member.weekly_plan_items)) {
        return member.weekly_plan_items;
      }
      const rows = Array.isArray(member && member.weekly_plan_rows) ? member.weekly_plan_rows : [];
      const weekStart = String(pagePayload && pagePayload.week_start || "").trim();
      const dayKeys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
      const items = [];
      rows.forEach((row, dayIndex) => {
        const source = row && typeof row === "object" ? row : {};
        if (String(source.am || "").trim()) {
          items.push({
            id: `legacy_am_${dayIndex}`,
            work_date: addDaysToDateString(weekStart, dayIndex),
            start_time: "09:00",
            end_time: "12:00",
            title: String(source.am || "").trim(),
            location: "",
            description: "",
            legacy_slot_key: `weekly_${dayKeys[dayIndex]}_am`,
            source: "legacy"
          });
        }
        if (String(source.pm || "").trim()) {
          items.push({
            id: `legacy_pm_${dayIndex}`,
            work_date: addDaysToDateString(weekStart, dayIndex),
            start_time: "13:30",
            end_time: "18:00",
            title: String(source.pm || "").trim(),
            location: "",
            description: "",
            legacy_slot_key: `weekly_${dayKeys[dayIndex]}_pm`,
            source: "legacy"
          });
        }
      });
      return items;
    }

    function getVisibleWeeklyPlanItems(member) {
      const items = getMemberWeeklyPlanItems(member);
      if (!compactModeEnabled) {
        return items;
      }
      const weekStart = String(pagePayload && pagePayload.week_start || "").trim();
      return items.filter((item) => {
        const workDate = String(item && item.work_date || "").trim();
        const dayIndex = Math.round((new Date(`${workDate}T00:00:00`) - new Date(`${weekStart}T00:00:00`)) / 86400000);
        return dayIndex < 5;
      });
    }

    function getVisibleMemberDays(member) {
      const days = Array.isArray(member && member.days) ? member.days : [];
      if (!compactModeEnabled) {
        return days;
      }
      return days.filter((day) => !isWeekendLabel(day && day.weekday_label));
    }

    function reconcileActiveFilters() {
      const memberOptions = getMemberOptions();
      const positionOptions = getPositionOptions();
      const memberKeySet = new Set(memberOptions.map((item) => normalizeKey(item.userId)));
      const positionMap = new Map(positionOptions.map((item) => [normalizeKey(item), item]));
      selectedMemberIds = dedupeValues(selectedMemberIds).filter((item) => memberKeySet.has(normalizeKey(item)));
      selectedPositions = dedupeValues(
        selectedPositions
          .map((item) => positionMap.get(normalizeKey(item)) || "")
          .filter(Boolean)
      );
      if (openDropdown === "position" && !positionOptions.length) {
        openDropdown = "";
      }
      if (openDropdown === "member" && !memberOptions.length) {
        openDropdown = "";
      }
    }

    function buildDropdownTriggerLabel(kind) {
      if (kind === "position") {
        if (!selectedPositions.length) {
          return "选择岗位";
        }
        return selectedPositions.length === 1 ? selectedPositions[0] : `已选 ${selectedPositions.length} 个岗位`;
      }
      const memberNames = getSelectedMemberNames();
      if (!memberNames.length) {
        return "选择人员";
      }
      return memberNames.length === 1 ? memberNames[0] : `已选 ${memberNames.length} 人`;
    }

    function renderDropdownMenu(target, items, selectedValues, type) {
      if (!items.length) {
        target.innerHTML = '<div class="picker-empty">暂无可选项</div>';
        return;
      }
      const selectedKeys = new Set((Array.isArray(selectedValues) ? selectedValues : []).map((item) => normalizeKey(item)));
      target.innerHTML = items.map((item) => {
        const value = typeof item === "string" ? item : item.userId;
        const label = typeof item === "string" ? item : item.name;
        const selected = selectedKeys.has(normalizeKey(value));
        return `
          <label class="picker-option${selected ? " is-selected" : ""}">
            <input type="checkbox" data-action="${type}" data-value="${escapeHtml(value)}"${selected ? " checked" : ""}>
            <span>${escapeHtml(label)}</span>
          </label>
        `;
      }).join("");
    }

    function syncDropdownState() {
      const isPositionOpen = openDropdown === "position";
      const isMemberOpen = openDropdown === "member";
      positionTriggerEl.setAttribute("aria-expanded", isPositionOpen ? "true" : "false");
      memberTriggerEl.setAttribute("aria-expanded", isMemberOpen ? "true" : "false");
      positionMenuEl.hidden = !isPositionOpen;
      memberMenuEl.hidden = !isMemberOpen;
    }

    function renderFilterControls() {
      if (!(authState.authenticated && pagePayload && Array.isArray(pagePayload.members))) {
        positionTriggerEl.textContent = "选择岗位";
        memberTriggerEl.textContent = "选择人员";
        positionMenuEl.innerHTML = "";
        memberMenuEl.innerHTML = "";
        openDropdown = "";
        syncDropdownState();
        clearFilterButtonEl.hidden = true;
        return;
      }
      const memberOptions = getMemberOptions();
      const positionOptions = getPositionOptions();
      positionTriggerEl.textContent = buildDropdownTriggerLabel("position");
      memberTriggerEl.textContent = buildDropdownTriggerLabel("member");
      renderDropdownMenu(positionMenuEl, positionOptions, selectedPositions, "toggle-position");
      renderDropdownMenu(memberMenuEl, memberOptions, selectedMemberIds, "toggle-member");
      syncDropdownState();
      clearFilterButtonEl.hidden = !hasActiveFilter();
    }

    function renderSummaryLine() {
      if (!(pagePayload && typeof pagePayload === "object")) {
        summaryLineEl.textContent = "";
        return;
      }
      const summary = pagePayload.summary || {};
      const weekStart = String(pagePayload.week_start || "").trim();
      const weekEnd = String(pagePayload.week_end || "").trim();
      if (!weekStart || !weekEnd) {
        summaryLineEl.textContent = "";
        return;
      }
      const memberCount = Number(summary.member_count || pagePayload.member_count || 0);
      const totalHours = String(summary.total_hours || "0").trim() || "0";
      const totalItems = Number(summary.total_items || 0);
      const visibleMembers = getVisibleMembers();
      const syncText = getVisibleCalendarSyncText();
      if (!hasActiveFilter()) {
        summaryLineEl.textContent = `${weekStart} 至 ${weekEnd} · 共 ${memberCount} 人 · ${totalItems} 条事项 · ${totalHours} 小时`;
        return;
      }
      summaryLineEl.textContent = `${weekStart} 至 ${weekEnd} · ${getFilterSummaryText()} · 展示 ${visibleMembers.length} 人${syncText ? ` · ${syncText}` : ""}`;
    }

    function syncControls() {
      const loggedIn = Boolean(authState.authenticated);
      loginCardEl.hidden = loggedIn;
      pageCardEl.hidden = !loggedIn;
      logoutButtonEl.hidden = !loggedIn;
      loginButtonEl.disabled = isLoggingIn;
      anchorDateEl.disabled = !loggedIn || isLoading;
      refreshButtonEl.disabled = !loggedIn || isLoading;
      syncDingtalkCalendarButton.disabled = !loggedIn || isLoading || isCalendarSyncing || savingUserIds.size > 0 || !getVisibleMembers().length;
      syncDingtalkCalendarButton.textContent = isCalendarSyncing ? "同步中..." : "同步钉钉";
      logoutButtonEl.disabled = !loggedIn || isLoading;
      clearFilterButtonEl.disabled = !loggedIn || isLoading;
      compactToggleEl.disabled = !loggedIn || isLoading;
      positionTriggerEl.disabled = !loggedIn || isLoading;
      memberTriggerEl.disabled = !loggedIn || isLoading;
      compactToggleEl.checked = compactModeEnabled;
      if (!loggedIn || isLoading) {
        openDropdown = "";
      }
      syncDropdownState();
    }

    function renderEmptyState(title, copy) {
      return `
        <section class="empty-state">
          <div class="empty-title">${escapeHtml(title)}</div>
          <div class="empty-copy">${escapeHtml(copy)}</div>
        </section>
      `;
    }

    function resizeTextarea(target) {
      if (!(target instanceof HTMLTextAreaElement)) {
        return;
      }
      target.style.height = "auto";
      target.style.height = `${target.scrollHeight}px`;
    }

    function syncTextareaHeights() {
      memberListEl.querySelectorAll("textarea").forEach((textarea) => {
        resizeTextarea(textarea);
      });
    }

    function renderLayout() {
      reconcileActiveFilters();
      syncControls();
      renderFilterControls();
      renderSummaryLine();

      if (!(authState.authenticated && pagePayload && Array.isArray(pagePayload.members))) {
        memberListEl.classList.remove("two-column");
        memberListEl.innerHTML = "";
        return;
      }

      if (!hasActiveFilter()) {
        memberListEl.classList.remove("two-column");
        memberListEl.innerHTML = renderEmptyState("未选择展示对象", "请在上方点击岗位或人员按钮后再查看对应日程。");
        return;
      }

      const visibleMembers = getVisibleMembers();
      if (!visibleMembers.length) {
        memberListEl.classList.remove("two-column");
        memberListEl.innerHTML = renderEmptyState("当前筛选下无内容", "可以重新选择其他岗位或人员。");
        return;
      }

      memberListEl.classList.toggle("two-column", visibleMembers.length > 1);
      const canEdit = Boolean(pagePayload.can_edit_weekly_plan);
      const showDailySection = Boolean(pagePayload.show_daily_section);
      memberListEl.innerHTML = visibleMembers.map((member, memberIndex) => {
        const userId = getMemberUserId(member);
        const name = getMemberName(member, memberIndex);
        const weekStats = member && typeof member === "object" ? member.week_stats || {} : {};
        const statText = `${String(weekStats.total_items || 0)} 条 · ${String(weekStats.total_hours || 0)}h`;
        const visibleItems = getVisibleWeeklyPlanItems(member);
        const dayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
        const weekStart = String(pagePayload && pagePayload.week_start || "").trim();
        const dayCount = compactModeEnabled ? 5 : 7;
        const rowMarkup = Array.from({ length: dayCount }, (_, dayIndex) => {
          const workDate = addDaysToDateString(weekStart, dayIndex);
          const dayItems = visibleItems
            .filter((item) => String(item && item.work_date || "").trim() === workDate)
            .sort((left, right) => String(left.start_time || "").localeCompare(String(right.start_time || "")));
          const itemMarkup = dayItems.length
            ? dayItems.map((item) => {
                const itemId = String(item && item.id || "").trim();
                const legacy = Boolean(item && (item.legacy_slot_key || item.source === "legacy"));
                const protectedDingtalkItem = isProtectedCrossUserDingtalkItem(userId, item);
                const disabledAttr = canEdit ? "" : " disabled";
                const itemDisabledAttr = protectedDingtalkItem ? " disabled" : disabledAttr;
                const timeDisabledAttr = (legacy || protectedDingtalkItem) ? " disabled" : disabledAttr;
                const deleteDisabledAttr = (disabledAttr || protectedDingtalkItem) ? " disabled" : "";
                const deleteLabel = protectedDingtalkItem ? "他人的钉钉同步日程仅本人可删除" : "删除日程";
                return `
                  <div class="week-row schedule-item-editor${protectedDingtalkItem ? " is-protected" : ""}" data-user-id="${escapeHtml(userId)}" data-item-id="${escapeHtml(itemId)}" data-day-index="${dayIndex}">
                    ${renderScheduleItemSyncMeta(item)}
                    <div class="schedule-item-time-row">
                      <div class="schedule-item-time-stack">
                        <input type="text" data-plan-field="start_time"${timeDisabledAttr} inputmode="numeric" maxlength="5" placeholder="09:00" value="${escapeHtml(item.start_time || "")}" aria-label="开始时间">
                        <input type="text" data-plan-field="end_time"${timeDisabledAttr} inputmode="numeric" maxlength="5" placeholder="10:00" value="${escapeHtml(item.end_time || "")}" aria-label="结束时间">
                      </div>
                      <button type="button" class="danger schedule-item-delete" data-action="delete-plan-item"${deleteDisabledAttr} title="${escapeHtml(deleteLabel)}" aria-label="${escapeHtml(deleteLabel)}"><span>删</span><span>除</span></button>
                    </div>
                    ${legacy ? `<div class="field-label">${String(item.legacy_slot_key || "").endsWith("_pm") ? "下午" : "上午"} · 旧数据</div>` : ""}
                    ${protectedDingtalkItem ? '<div class="field-label">钉钉同步 · 仅本人可改</div>' : ""}
                    <textarea data-plan-field="title" ${itemDisabledAttr} placeholder="内容">${escapeHtml(item.title || "")}</textarea>
                    <input class="schedule-item-location" data-plan-field="location" ${itemDisabledAttr} placeholder="地点" value="${escapeHtml(item.location || "")}">
                  </div>
                `;
              }).join("")
            : '<div class="day-empty">暂无安排</div>';
          const createKey = buildScheduleCreateFormKey(userId, dayIndex);
          const createMarkup = scheduleCreateFormKeys.has(createKey)
            ? renderScheduleItemCreateForm(userId, dayIndex)
            : `<button type="button" class="secondary schedule-item-add" data-action="add-plan-item" data-user-id="${escapeHtml(userId)}" data-day-index="${dayIndex}">+ 新建日程</button>`;
          return `
            <div class="week-day-group" data-day-index="${dayIndex}">
              <div class="week-day-group-head">
                <span>${dayLabels[dayIndex]}</span>
                <span>${escapeHtml(workDate)}</span>
              </div>
              ${itemMarkup}
              ${canEdit ? createMarkup : ""}
            </div>
          `;
        }).join("");
        const pendingValue = String(member && member.weekly_other_pending || "");
        const dayMarkup = showDailySection ? renderMemberDays(member) : "";
        const updatedAt = String(member && member.weekly_plan_updated_at || "").trim();
        const helperText = updatedAt ? `最近保存：${updatedAt}` : (canEdit ? "修改后点击保存。" : "当前账号仅可查看。");
        const helperMarkup = `<div class="helper-text${compactModeEnabled ? " compact-helper" : ""}">${escapeHtml(helperText)}</div>`;
        const pendingMarkup = compactModeEnabled ? helperMarkup : `
            <div class="pending-block">
              <label class="field">
                <span class="field-label">其他待办</span>
                <textarea data-user-id="${escapeHtml(userId)}" data-field="weekly_other_pending" ${canEdit ? "" : "disabled"} placeholder="补充待办">${escapeHtml(pendingValue)}</textarea>
              </label>
              ${helperMarkup}
            </div>
        `;
        return `
          <section class="member-card" data-user-id="${escapeHtml(userId)}">
            <div class="member-head">
              <div>
                <div class="member-name">${escapeHtml(name)}</div>
              </div>
              <div class="member-stats">${escapeHtml(statText)}</div>
            </div>
            <div class="week-grid">${rowMarkup}</div>
            ${pendingMarkup}
            ${dayMarkup}
            ${canEdit ? `
              <div class="member-actions">
                <button type="button" class="save-btn" data-action="save-member" data-user-id="${escapeHtml(userId)}" ${savingUserIds.has(userId) ? "disabled" : ""}>${savingUserIds.has(userId) ? "保存中..." : "保存安排"}</button>
              </div>
            ` : ""}
          </section>
        `;
      }).join("");
      syncTextareaHeights();
    }

    function buildDayItemSummary(day) {
      const items = Array.isArray(day && day.items) ? day.items : [];
      return items.slice(0, 2).map((item) => {
        const customerName = String(item && item.customer_name || "").trim();
        const workContent = String(item && item.work_content || "").trim();
        const hours = String(item && item.work_hours || "").trim();
        const parts = [];
        if (customerName) {
          parts.push(customerName);
        }
        if (workContent) {
          parts.push(workContent);
        }
        if (hours) {
          parts.push(`${hours}h`);
        }
        return parts.join(" · ") || "已填写日程";
      });
    }

    function renderMemberDays(member) {
      const days = getVisibleMemberDays(member);
      if (!days.length) {
        return "";
      }
      const dayCards = days.map((day) => {
        const label = `${String(day && day.weekday_label || "").trim()} ${String(day && day.work_date || "").trim()}`.trim();
        if (!day || day.has_entry !== true) {
          return `
            <div class="day-card">
              <div class="day-head"><span>${escapeHtml(label)}</span><span class="day-meta">未填写</span></div>
              <div class="day-empty">当天暂无明细。</div>
            </div>
          `;
        }
        const itemCount = Number(day.item_count || 0);
        const totalHours = String(day.total_hours || "").trim() || "0";
        const summaries = buildDayItemSummary(day);
        return `
          <div class="day-card">
            <div class="day-head"><span>${escapeHtml(label)}</span><span class="day-meta">${itemCount} 条 · ${escapeHtml(totalHours)}h</span></div>
            <div class="day-items">
              ${summaries.length ? summaries.map((summary) => `<div class="day-item">${escapeHtml(summary)}</div>`).join("") : '<div class="day-empty">已填写但暂无可展示摘要。</div>'}
            </div>
          </div>
        `;
      }).join("");
      return `
        <div class="daily-list">
          ${dayCards}
        </div>
      `;
    }

    function findMember(userId) {
      if (!(pagePayload && Array.isArray(pagePayload.members))) {
        return null;
      }
      return pagePayload.members.find((member) => getMemberUserId(member) === String(userId || "").trim()) || null;
    }

    async function requestJson(url, options) {
      const response = await fetch(url, options);
      let payload = {};
      try {
        payload = await response.json();
      } catch (error) {
        payload = {};
      }
      if (!response.ok) {
        const requestError = new Error(payload.error || "请求失败");
        requestError.status = response.status;
        requestError.payload = payload;
        throw requestError;
      }
      return payload;
    }

    async function refreshAuthState() {
      const payload = await requestJson("/api/auth/me");
      authState = normalizeAuthState(payload);
    }

    async function loadDepartmentSchedule(showLoadingMessage = true) {
      if (!authState.authenticated) {
        return;
      }
      isLoading = true;
      syncControls();
      if (showLoadingMessage) {
        setStatus(pageStatusEl, "正在加载日程管理...", false);
      }
      try {
        const payload = await requestJson(`/api/department-schedule?date=${encodeURIComponent(anchorDateEl.value)}&mobile=1`);
        pagePayload = payload && typeof payload === "object" ? payload : {};
        scheduleCreateFormKeys = new Set();
        setStatus(pageStatusEl, "", false);
      } catch (error) {
        pagePayload = { members: [] };
        setStatus(pageStatusEl, error.message || "读取日程管理失败。", true);
      } finally {
        isLoading = false;
        renderLayout();
      }
    }

    function buildMobileScheduleSyncPayload() {
      const visibleUserIds = getVisibleMembers().map(getMemberUserId).filter(Boolean);
      return {
        date: String(anchorDateEl.value || "__INITIAL_DATE__").trim() || "__INITIAL_DATE__",
        users: visibleUserIds.length ? visibleUserIds : ["__none__"],
      };
    }

    async function syncDingtalkCalendarForVisibleMembers() {
      if (isCalendarSyncing) {
        return;
      }
      const visibleUserIds = getVisibleMembers().map(getMemberUserId).filter(Boolean);
      if (!visibleUserIds.length) {
        setStatus(pageStatusEl, "请先选择要展示的岗位或人员。", true);
        return;
      }
      isCalendarSyncing = true;
      renderLayout();
      setStatus(pageStatusEl, "正在同步当前可见成员的钉钉日程...", false);
      try {
        for (const userId of visibleUserIds) {
          const member = findMember(userId);
          if (member) {
            await saveMember(userId);
          }
        }
        const payload = await requestJson("/api/department-schedule/calendar-sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildMobileScheduleSyncPayload()),
        });
        if (payload && payload.payload) {
          pagePayload = payload.payload;
          scheduleCreateFormKeys = new Set();
        }
        const summary = payload && payload.summary || {};
        const importedCount = Number(summary.imported_count || 0);
        const queuedCount = Number(summary.queued_count || 0);
        const extraParts = [];
        if (importedCount) {
          extraParts.push(`导入 ${importedCount} 条`);
        }
        if (queuedCount) {
          extraParts.push(`推送 ${queuedCount} 条`);
        }
        const extraText = extraParts.length ? `，${extraParts.join("，")}` : "";
        setStatus(
          pageStatusEl,
          `钉钉同步完成：已处理 ${summary.synced_count || 0} 人，未配置 ${summary.skipped_count || 0} 人，失败 ${summary.failed_count || 0} 人${extraText}。`,
          Number(summary.failed_count || 0) > 0
        );
      } catch (error) {
        setStatus(pageStatusEl, error.message || "同步钉钉失败，请稍后重试。", true);
      } finally {
        isCalendarSyncing = false;
        renderLayout();
      }
    }

    async function saveMember(userId) {
      const member = findMember(userId);
      if (!member || savingUserIds.has(userId)) {
        return;
      }
      member.weekly_plan_items = normalizeScheduleItemsForSave(getMemberWeeklyPlanItems(member));
      const validationMessage = validateMemberScheduleItems(member);
      if (validationMessage) {
        setStatus(pageStatusEl, validationMessage, true);
        return;
      }
      savingUserIds.add(userId);
      renderLayout();
      setStatus(pageStatusEl, `正在保存 ${getMemberName(member)} 的安排...`, false);
      try {
        const payload = await requestJson("/api/department-schedule/weekly-plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: String(userId || "").trim(),
            week_start: String(pagePayload && pagePayload.week_start || anchorDateEl.value || "").trim(),
            base_updated_at: String(member.weekly_plan_updated_at || ""),
            weekly_plan_items: member.weekly_plan_items,
            weekly_other_pending: String(member.weekly_other_pending || ""),
          }),
        });
        member.weekly_plan_items = Array.isArray(payload.weekly_plan_items)
          ? payload.weekly_plan_items
          : member.weekly_plan_items || [];
        member.weekly_plan_rows = Array.isArray(payload.weekly_plan_rows) ? payload.weekly_plan_rows : member.weekly_plan_rows;
        member.weekly_other_pending = String(payload.weekly_other_pending || "");
        member.weekly_plan_updated_at = String(payload.updated_at || "");
        member.weekly_plan_last_editor = payload.weekly_plan_last_editor || member.weekly_plan_last_editor || null;
        setStatus(pageStatusEl, "安排已保存。", false);
      } catch (error) {
        if (Number(error && error.status || 0) === 409) {
          const displayName = getMemberName(member);
          const payload = error && error.payload && typeof error.payload === "object" ? error.payload : {};
          const message = payload.error || `${displayName} 的本周安排已被其他人更新，请刷新后再保存。`;
          member.weekly_plan_last_editor = payload.weekly_plan_last_editor || member.weekly_plan_last_editor || null;
          setStatus(pageStatusEl, message, true);
          window.alert(`${displayName} 的本周安排已被其他人更新。\n\n点击确定后将刷新页面，请重新确认后再编辑保存。`);
          window.location.reload();
          return;
        }
        setStatus(pageStatusEl, error.message || "保存安排失败。", true);
      } finally {
        savingUserIds.delete(userId);
        renderLayout();
      }
    }

    function clearFilters() {
      selectedMemberIds = [];
      selectedPositions = [];
      openDropdown = "";
      renderLayout();
    }

    async function login() {
      if (isLoggingIn) {
        return;
      }
      const username = String(loginUsernameEl.value || "").trim();
      const password = String(loginPasswordEl.value || "");
      if (!username || !password) {
        setStatus(loginStatusEl, "请输入用户名和密码。", true);
        return;
      }
      isLoggingIn = true;
      syncControls();
      setStatus(loginStatusEl, "正在登录...", false);
      try {
        await requestJson("/api/auth/password-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        loginPasswordEl.value = "";
        setStatus(loginStatusEl, "", false);
        await refreshAuthState();
        await loadDepartmentSchedule();
      } catch (error) {
        setStatus(loginStatusEl, error.message || "登录失败。", true);
      } finally {
        isLoggingIn = false;
        renderLayout();
      }
    }

    async function logout() {
      try {
        await requestJson("/api/auth/logout", { method: "POST" });
      } catch (error) {
        // Ignore logout errors and clear local state anyway.
      }
      authState = normalizeAuthState({ authenticated: false, user: null });
      pagePayload = null;
      savingUserIds = new Set();
      selectedMemberIds = [];
      selectedPositions = [];
      openDropdown = "";
      scheduleCreateFormKeys = new Set();
      setStatus(pageStatusEl, "", false);
      renderLayout();
    }

    memberListEl.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLTextAreaElement) && !(target instanceof HTMLInputElement)) {
        return;
      }
      const createForm = target.closest("[data-schedule-create-form]");
      if (createForm) {
        setScheduleCreateFormError(createForm, "");
        if (isScheduleTimeFieldName(target.dataset.scheduleCreateField)) {
          sanitizeScheduleTimeField(target);
        }
        if (target instanceof HTMLTextAreaElement) {
          resizeTextarea(target);
        }
        return;
      }
      const editor = target.closest(".schedule-item-editor");
      const userId = String(
        target.dataset.userId
        || (editor && editor.dataset.userId)
        || ""
      ).trim();
      const field = String(target.dataset.field || target.dataset.planField || "").trim();
      const member = findMember(userId);
      if (!member || !field) {
        return;
      }
      if (field === "weekly_other_pending") {
        member.weekly_other_pending = String(target.value || "");
        return;
      }
      const itemId = String(editor && editor.dataset.itemId || "").trim();
      const item = getMemberWeeklyPlanItems(member).find((candidate) => String(candidate.id || "") === itemId);
      if (!item || !field) {
        return;
      }
      if (isScheduleTimeFieldName(field)) {
        sanitizeScheduleTimeField(target);
      }
      item[field] = String(target.value || "");
      if (target instanceof HTMLTextAreaElement) {
        resizeTextarea(target);
      }
    });

    memberListEl.addEventListener("focusout", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const createField = target.closest("[data-schedule-create-field]");
      if (createField && isScheduleTimeFieldName(createField.dataset.scheduleCreateField)) {
        normalizeScheduleTimeField(createField);
        return;
      }
      const field = String(target.dataset.planField || "").trim();
      if (!isScheduleTimeFieldName(field)) {
        return;
      }
      const editor = target.closest(".schedule-item-editor");
      const userId = String(editor && editor.dataset.userId || "").trim();
      const member = findMember(userId);
      const itemId = String(editor && editor.dataset.itemId || "").trim();
      const item = getMemberWeeklyPlanItems(member).find((candidate) => String(candidate.id || "") === itemId);
      if (!item) {
        return;
      }
      item[field] = normalizeScheduleTimeField(target);
    });

    memberListEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const action = target.closest("[data-action]");
      if (!action) {
        return;
      }
      const actionName = String(action.getAttribute("data-action") || "").trim();
      const userId = String(
        action.getAttribute("data-user-id")
        || (action.closest("[data-user-id]") && action.closest("[data-user-id]").getAttribute("data-user-id"))
        || ""
      ).trim();
      const member = findMember(userId);
      if (!member) {
        return;
      }
      if (actionName === "add-plan-item") {
        const dayIndex = Number(action.getAttribute("data-day-index") || 0);
        scheduleCreateFormKeys.add(buildScheduleCreateFormKey(userId, dayIndex));
        renderLayout();
        const createForm = Array.from(memberListEl.querySelectorAll("[data-schedule-create-form]")).find((candidate) => {
          return String(candidate.getAttribute("data-user-id") || "").trim() === userId
            && Number(candidate.getAttribute("data-day-index") || -1) === dayIndex;
        });
        const titleInput = createForm && createForm.querySelector('[data-schedule-create-field="title"]');
        if (titleInput && typeof titleInput.focus === "function") {
          titleInput.focus();
        }
        return;
      }
      if (actionName === "cancel-plan-item") {
        const dayIndex = Number(action.getAttribute("data-day-index") || 0);
        scheduleCreateFormKeys.delete(buildScheduleCreateFormKey(userId, dayIndex));
        renderLayout();
        return;
      }
      if (actionName === "delete-plan-item") {
        const editor = action.closest(".schedule-item-editor");
        const itemId = String(editor && editor.dataset.itemId || "").trim();
        const targetItem = getMemberWeeklyPlanItems(member).find(
          (item) => String(item && item.id || "").trim() === itemId
        );
        if (isProtectedCrossUserDingtalkItem(userId, targetItem)) {
          setStatus(pageStatusEl, "他人从钉钉同步的日程仅本人可删除。", true);
          return;
        }
        member.weekly_plan_items = getMemberWeeklyPlanItems(member).filter(
          (item) => String(item && item.id || "") !== itemId
        );
        renderLayout();
        return;
      }
      if (actionName === "save-member" && userId) {
        saveMember(userId);
      }
    });

    memberListEl.addEventListener("submit", (event) => {
      const form = event.target.closest("[data-schedule-create-form]");
      if (!form) {
        return;
      }
      event.preventDefault();
      const userId = String(form.getAttribute("data-user-id") || "").trim();
      const member = findMember(userId);
      if (!member) {
        return;
      }
      const dayIndex = Number(form.getAttribute("data-day-index") || -1);
      if (!Number.isInteger(dayIndex) || dayIndex < 0 || dayIndex >= 7) {
        return;
      }
      const title = readScheduleCreateField(form, "title");
      const startTime = readScheduleCreateField(form, "start_time");
      const endTime = readScheduleCreateField(form, "end_time");
      const location = readScheduleCreateField(form, "location");
      const validationMessage = validateScheduleTimeRange(startTime, endTime, title);
      if (validationMessage) {
        setScheduleCreateFormError(form, validationMessage);
        return;
      }
      const weekStart = String(pagePayload && pagePayload.week_start || "").trim();
      const items = getMemberWeeklyPlanItems(member).map((item) => ({ ...item }));
      items.push({
        id: `weekly_item_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`,
        work_date: addDaysToDateString(weekStart, dayIndex),
        start_time: startTime,
        end_time: endTime,
        title,
        description: "",
        location,
        sort_order: items.length,
        legacy_slot_key: "",
        source: "new",
      });
      member.weekly_plan_items = items;
      scheduleCreateFormKeys.delete(buildScheduleCreateFormKey(userId, dayIndex));
      renderLayout();
    });

    function toggleDropdown(name) {
      openDropdown = openDropdown === name ? "" : name;
      syncDropdownState();
    }

    function toggleValueInList(values, nextValue) {
      const normalizedNext = normalizeKey(nextValue);
      if (!normalizedNext) {
        return Array.isArray(values) ? values.slice() : [];
      }
      const source = Array.isArray(values) ? values.slice() : [];
      const index = source.findIndex((item) => normalizeKey(item) === normalizedNext);
      if (index >= 0) {
        source.splice(index, 1);
        return source;
      }
      source.push(String(nextValue || "").trim());
      return source;
    }

    positionTriggerEl.addEventListener("click", () => {
      if (positionTriggerEl.disabled) {
        return;
      }
      toggleDropdown("position");
    });

    memberTriggerEl.addEventListener("click", () => {
      if (memberTriggerEl.disabled) {
        return;
      }
      toggleDropdown("member");
    });

    positionMenuEl.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) {
        return;
      }
      if (target.dataset.action !== "toggle-position") {
        return;
      }
      const nextValue = String(target.dataset.value || "").trim();
      selectedPositions = toggleValueInList(selectedPositions, nextValue);
      renderLayout();
    });

    memberMenuEl.addEventListener("change", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) {
        return;
      }
      if (target.dataset.action !== "toggle-member") {
        return;
      }
      const nextValue = String(target.dataset.value || "").trim();
      selectedMemberIds = toggleValueInList(selectedMemberIds, nextValue);
      renderLayout();
    });

    document.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      if (target.closest(".picker-select")) {
        return;
      }
      if (openDropdown) {
        openDropdown = "";
        syncDropdownState();
      }
    });

    loginButtonEl.addEventListener("click", login);
    loginUsernameEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        login();
      }
    });
    loginPasswordEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        login();
      }
    });
    logoutButtonEl.addEventListener("click", logout);
    refreshButtonEl.addEventListener("click", () => loadDepartmentSchedule());
    syncDingtalkCalendarButton.addEventListener("click", syncDingtalkCalendarForVisibleMembers);
    anchorDateEl.addEventListener("change", () => loadDepartmentSchedule(false));
    clearFilterButtonEl.addEventListener("click", clearFilters);
    compactToggleEl.addEventListener("change", () => {
      compactModeEnabled = Boolean(compactToggleEl.checked);
      renderLayout();
    });
    window.addEventListener("resize", syncTextareaHeights);

    renderLayout();
    if (authState.authenticated) {
      loadDepartmentSchedule();
    }
  </script>
</body>
</html>
"""


def render_mobile_schedule_html(*, initial_date: str, initial_auth_payload_json: str) -> str:
    html = MOBILE_SCHEDULE_HTML.replace("__INITIAL_DATE__", initial_date)
    html = html.replace("__INITIAL_AUTH_STATE_PAYLOAD__", initial_auth_payload_json)
    return html
