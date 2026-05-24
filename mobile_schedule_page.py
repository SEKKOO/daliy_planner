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
      resize: vertical;
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
      font-size: 12px;
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

    .member-list.two-column .member-meta {
      font-size: 10px;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
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
      grid-template-columns: 30px minmax(0, 1fr);
      gap: 6px;
      padding: 6px;
    }

    .member-list.two-column .week-label {
      font-size: 11px;
      padding-top: 16px;
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

    .member-meta {
      margin-top: 3px;
      font-size: 10px;
      color: var(--muted);
      line-height: 1.4;
      word-break: break-word;
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
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      padding: 6px;
      display: grid;
      grid-template-columns: 32px minmax(0, 1fr);
      gap: 6px;
      align-items: start;
    }

    .week-label {
      font-size: 11px;
      font-weight: 700;
      color: var(--text);
      padding-top: 16px;
      line-height: 1.2;
    }

    .week-fields {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 4px;
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
      <p class="section-text">登录后查看并维护当前可访问范围内的日程管理内容。</p>
      <div class="stack">
        <label class="field">
          <span class="field-label">用户名</span>
          <input id="mobile-login-username" type="text" autocomplete="username" placeholder="请输入用户名">
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input id="mobile-login-password" type="password" autocomplete="current-password" placeholder="请输入密码">
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

    let authState = normalizeAuthState(bootAuthState);
    let pagePayload = null;
    let isLoggingIn = false;
    let isLoading = false;
    let savingUserIds = new Set();
    let selectedMemberIds = [];
    let selectedPositions = [];
    let openDropdown = "";
    let compactModeEnabled = true;

    function normalizeAuthState(source) {
      const payload = source && typeof source === "object" ? source : {};
      const user = payload.user && typeof payload.user === "object" ? payload.user : null;
      return {
        authenticated: Boolean(payload.authenticated && user),
        user,
      };
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

    function getMemberMeta(member) {
      const user = member && typeof member === "object" ? member.user || {} : {};
      const positions = getMemberPositionLabels(member).join(" / ");
      const department = String(user.department || "").trim();
      return [positions, department].filter(Boolean).join(" · ") || "未配置岗位/部门";
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
      if (!hasActiveFilter()) {
        summaryLineEl.textContent = `${weekStart} 至 ${weekEnd} · 共 ${memberCount} 人 · ${totalItems} 条事项 · ${totalHours} 小时`;
        return;
      }
      summaryLineEl.textContent = `${weekStart} 至 ${weekEnd} · ${getFilterSummaryText()} · 展示 ${visibleMembers.length} 人`;
    }

    function syncControls() {
      const loggedIn = Boolean(authState.authenticated);
      loginCardEl.hidden = loggedIn;
      pageCardEl.hidden = !loggedIn;
      logoutButtonEl.hidden = !loggedIn;
      loginButtonEl.disabled = isLoggingIn;
      anchorDateEl.disabled = !loggedIn || isLoading;
      refreshButtonEl.disabled = !loggedIn || isLoading;
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
        const metaText = getMemberMeta(member);
        const weekStats = member && typeof member === "object" ? member.week_stats || {} : {};
        const statText = `${String(weekStats.total_items || 0)} 条 · ${String(weekStats.total_hours || 0)}h`;
        const rows = getVisibleWeeklyPlanRows(member);
        const rowMarkup = rows.map((row, rowIndex) => {
          const weekdayLabel = String(row && row.weekday_label || `第${rowIndex + 1}天`).trim();
          const am = String(row && row.am || "");
          const pm = String(row && row.pm || "");
          return `
            <div class="week-row">
              <div class="week-label">${escapeHtml(weekdayLabel)}</div>
              <div class="week-fields">
                <label class="field">
                  <span class="field-label">上午</span>
                  <textarea data-user-id="${escapeHtml(userId)}" data-row-index="${rowIndex}" data-field="am" ${canEdit ? "" : "disabled"} placeholder="上午安排">${escapeHtml(am)}</textarea>
                </label>
                <label class="field">
                  <span class="field-label">下午</span>
                  <textarea data-user-id="${escapeHtml(userId)}" data-row-index="${rowIndex}" data-field="pm" ${canEdit ? "" : "disabled"} placeholder="下午安排">${escapeHtml(pm)}</textarea>
                </label>
              </div>
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
                <div class="member-meta">${escapeHtml(metaText)}</div>
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
        throw new Error(payload.error || "请求失败");
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
        setStatus(pageStatusEl, "", false);
      } catch (error) {
        pagePayload = { members: [] };
        setStatus(pageStatusEl, error.message || "读取日程管理失败。", true);
      } finally {
        isLoading = false;
        renderLayout();
      }
    }

    async function saveMember(userId) {
      const member = findMember(userId);
      if (!member || savingUserIds.has(userId)) {
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
            weekly_plan_rows: Array.isArray(member.weekly_plan_rows) ? member.weekly_plan_rows : [],
            weekly_other_pending: String(member.weekly_other_pending || ""),
          }),
        });
        member.weekly_plan_rows = Array.isArray(payload.weekly_plan_rows) ? payload.weekly_plan_rows : member.weekly_plan_rows;
        member.weekly_other_pending = String(payload.weekly_other_pending || "");
        member.weekly_plan_updated_at = String(payload.updated_at || "");
        member.weekly_plan_last_editor = payload.weekly_plan_last_editor || member.weekly_plan_last_editor || null;
        setStatus(pageStatusEl, "安排已保存。", false);
      } catch (error) {
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
      setStatus(pageStatusEl, "", false);
      renderLayout();
    }

    memberListEl.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLTextAreaElement)) {
        return;
      }
      const userId = String(target.dataset.userId || "").trim();
      const field = String(target.dataset.field || "").trim();
      const member = findMember(userId);
      if (!member || !field) {
        return;
      }
      if (field === "weekly_other_pending") {
        member.weekly_other_pending = String(target.value || "");
        return;
      }
      const rowIndex = Number.parseInt(String(target.dataset.rowIndex || ""), 10);
      if (!Number.isInteger(rowIndex) || !Array.isArray(member.weekly_plan_rows) || !member.weekly_plan_rows[rowIndex]) {
        return;
      }
      member.weekly_plan_rows[rowIndex][field] = String(target.value || "");
    });

    memberListEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const saveButton = target.closest("[data-action='save-member']");
      if (!saveButton) {
        return;
      }
      const userId = String(saveButton.getAttribute("data-user-id") || "").trim();
      if (userId) {
        saveMember(userId);
      }
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
    anchorDateEl.addEventListener("change", () => loadDepartmentSchedule(false));
    clearFilterButtonEl.addEventListener("click", clearFilters);
    compactToggleEl.addEventListener("change", () => {
      compactModeEnabled = Boolean(compactToggleEl.checked);
      renderLayout();
    });

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
