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
      --panel: rgba(255, 255, 255, 0.94);
      --panel-soft: #f8fbff;
      --line: #d8e2ef;
      --line-strong: #c8d6e7;
      --text: #17324d;
      --muted: #6c849c;
      --primary: #2764cb;
      --primary-soft: #e7f0ff;
      --primary-deep: #184b9c;
      --danger: #c23b4c;
      --danger-soft: #fff2f4;
      --success: #1d8a59;
      --shadow: 0 16px 34px rgba(31, 71, 128, 0.08);
      --radius: 18px;
      --radius-sm: 14px;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      min-height: 100%;
      background: linear-gradient(180deg, #edf4ff 0%, #f8fbff 36%, #f4f7fb 100%);
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
      border-radius: 14px;
      padding: 12px 14px;
    }

    textarea {
      min-height: 76px;
      resize: vertical;
      line-height: 1.55;
    }

    .shell {
      width: min(100%, 860px);
      margin: 0 auto;
      padding: 14px 14px 28px;
    }

    .card {
      background: var(--panel);
      border: 1px solid rgba(216, 226, 239, 0.9);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .header-card {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 18px;
      margin-bottom: 12px;
    }

    .eyebrow {
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.08em;
    }

    .title {
      margin: 6px 0 0;
      font-size: 24px;
      line-height: 1.15;
    }

    .subtitle {
      margin-top: 8px;
      font-size: 13px;
      color: var(--muted);
      line-height: 1.6;
    }

    .ghost-btn {
      background: transparent;
      border: 1px solid var(--line);
      color: var(--muted);
      padding: 10px 14px;
    }

    .ghost-btn[hidden] {
      display: none;
    }

    .login-card,
    .page-card {
      padding: 16px;
    }

    .section-title {
      margin: 0 0 10px;
      font-size: 18px;
    }

    .section-text {
      margin: 0 0 14px;
      font-size: 14px;
      color: var(--muted);
      line-height: 1.6;
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .field {
      display: grid;
      gap: 8px;
    }

    .field-label {
      font-size: 13px;
      color: var(--muted);
    }

    .status {
      min-height: 22px;
      margin: 8px 0 12px;
      font-size: 13px;
      color: var(--muted);
    }

    .status.is-error {
      color: var(--danger);
    }

    .primary-btn,
    .soft-btn,
    .danger-btn {
      width: 100%;
      padding: 12px 14px;
      font-weight: 700;
      border-radius: 15px;
    }

    .primary-btn {
      background: var(--primary);
      color: #fff;
    }

    .soft-btn {
      background: var(--primary-soft);
      color: var(--primary-deep);
    }

    .danger-btn {
      background: #fff;
      color: var(--danger);
      border: 1px solid rgba(194, 59, 76, 0.2);
    }

    .toolbar {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      margin-bottom: 12px;
    }

    .summary-line {
      font-size: 13px;
      color: var(--muted);
      line-height: 1.6;
      margin-bottom: 12px;
    }

    .member-list {
      display: grid;
      gap: 12px;
    }

    .member-card {
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: rgba(248, 251, 255, 0.96);
      padding: 14px;
    }

    .member-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }

    .member-name {
      font-size: 17px;
      font-weight: 700;
      line-height: 1.2;
    }

    .member-meta {
      margin-top: 4px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }

    .member-stats {
      font-size: 12px;
      color: var(--primary-deep);
      background: var(--primary-soft);
      border-radius: 999px;
      padding: 6px 10px;
      white-space: nowrap;
    }

    .week-grid {
      display: grid;
      gap: 10px;
    }

    .week-row {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px;
      display: grid;
      gap: 8px;
    }

    .week-label {
      font-size: 13px;
      font-weight: 700;
      color: var(--text);
    }

    .week-fields {
      display: grid;
      gap: 8px;
    }

    .week-fields textarea {
      min-height: 58px;
    }

    .helper-text {
      font-size: 12px;
      color: var(--muted);
    }

    .daily-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }

    .day-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
      padding: 10px;
    }

    .day-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 6px;
    }

    .day-meta {
      color: var(--muted);
      font-weight: 500;
      font-size: 12px;
    }

    .day-empty {
      font-size: 12px;
      color: var(--muted);
    }

    .day-items {
      display: grid;
      gap: 6px;
    }

    .day-item {
      font-size: 12px;
      line-height: 1.5;
      color: var(--text);
      padding-left: 10px;
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
      display: grid;
      gap: 8px;
      margin-top: 12px;
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

    @media (min-width: 740px) {
      .week-fields {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .member-actions {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 420px) {
      .shell {
        padding-left: 10px;
        padding-right: 10px;
      }

      .header-card,
      .login-card,
      .page-card {
        padding: 14px;
      }

      .toolbar {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card header-card">
      <div>
        <div class="eyebrow">DEPARTMENT SCHEDULE</div>
        <h1 class="title">日程管理</h1>
        <div class="subtitle" id="mobile-page-subtitle">手机端默认进入日程管理页面，仅保留简洁的成员日程展示与维护能力。</div>
      </div>
      <button type="button" class="ghost-btn" id="mobile-logout-button" hidden>退出</button>
    </section>

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
        <button type="button" class="soft-btn" id="mobile-refresh-button">刷新</button>
      </div>
      <div class="summary-line" id="mobile-summary-line"></div>
      <div class="status" id="mobile-page-status" aria-live="polite"></div>
      <div class="member-list" id="mobile-member-list"></div>
    </section>
  </main>

  <script>
    const bootAuthState = __INITIAL_AUTH_STATE_PAYLOAD__;

    const subtitleEl = document.getElementById("mobile-page-subtitle");
    const loginCardEl = document.getElementById("mobile-login-card");
    const loginUsernameEl = document.getElementById("mobile-login-username");
    const loginPasswordEl = document.getElementById("mobile-login-password");
    const loginStatusEl = document.getElementById("mobile-login-status");
    const loginButtonEl = document.getElementById("mobile-login-button");
    const logoutButtonEl = document.getElementById("mobile-logout-button");
    const pageCardEl = document.getElementById("mobile-page-card");
    const anchorDateEl = document.getElementById("mobile-anchor-date");
    const refreshButtonEl = document.getElementById("mobile-refresh-button");
    const summaryLineEl = document.getElementById("mobile-summary-line");
    const pageStatusEl = document.getElementById("mobile-page-status");
    const memberListEl = document.getElementById("mobile-member-list");

    let authState = normalizeAuthState(bootAuthState);
    let pagePayload = null;
    let isLoggingIn = false;
    let isLoading = false;
    let savingUserIds = new Set();

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
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function setStatus(target, message, isError = false) {
      target.textContent = message || "";
      target.classList.toggle("is-error", Boolean(isError && message));
    }

    function setSubtitle() {
      if (!(authState.authenticated && authState.user)) {
        subtitleEl.textContent = "手机端默认进入日程管理页面，仅保留简洁的成员日程展示与维护能力。";
        return;
      }
      const userName = String(authState.user.display_name || authState.user.user_id || "当前用户").trim();
      const department = String(authState.user.department || "").trim();
      subtitleEl.textContent = department ? `${userName} · ${department}` : `${userName} · 已进入日程管理`;
    }

    function renderSummaryLine() {
      if (!(pagePayload && typeof pagePayload === "object")) {
        summaryLineEl.textContent = "";
        return;
      }
      const summary = pagePayload.summary || {};
      const weekStart = String(pagePayload.week_start || "").trim();
      const weekEnd = String(pagePayload.week_end || "").trim();
      const departmentLabel = String(pagePayload.selected_department_label || pagePayload.selected_department || "全部成员").trim() || "全部成员";
      const memberCount = Number(summary.member_count || pagePayload.member_count || 0);
      const totalHours = String(summary.total_hours || "0").trim() || "0";
      const totalItems = Number(summary.total_items || 0);
      const filledDays = Number(summary.filled_days || 0);
      summaryLineEl.textContent = `${departmentLabel} · ${weekStart} 至 ${weekEnd} · ${memberCount} 人 · ${totalItems} 条事项 · ${totalHours} 小时 · ${filledDays} 人天`; 
    }

    function syncControls() {
      const loggedIn = Boolean(authState.authenticated);
      loginCardEl.hidden = loggedIn;
      pageCardEl.hidden = !loggedIn;
      logoutButtonEl.hidden = !loggedIn;
      loginButtonEl.disabled = isLoggingIn;
      anchorDateEl.disabled = !loggedIn || isLoading;
      refreshButtonEl.disabled = !loggedIn || isLoading;
    }

    function renderLayout() {
      setSubtitle();
      renderSummaryLine();
      syncControls();
      if (!(authState.authenticated && pagePayload && Array.isArray(pagePayload.members))) {
        memberListEl.innerHTML = "";
        return;
      }
      const canEdit = Boolean(pagePayload.can_edit_weekly_plan);
      const showDailySection = Boolean(pagePayload.show_daily_section);
      memberListEl.innerHTML = pagePayload.members.map((member, memberIndex) => {
        const user = member && typeof member === "object" ? member.user || {} : {};
        const userId = String(user.user_id || "").trim();
        const name = String(user.display_name || user.user_id || `成员 ${memberIndex + 1}`).trim();
        const metaParts = [String(user.position_labels || user.position || "").trim(), String(user.department || "").trim()].filter(Boolean);
        const weekStats = member && typeof member === "object" ? member.week_stats || {} : {};
        const statText = `${String(weekStats.total_items || 0)} 条 · ${String(weekStats.total_hours || 0)} 小时`;
        const rows = Array.isArray(member.weekly_plan_rows) ? member.weekly_plan_rows : [];
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
        const helperText = updatedAt ? `最近保存：${updatedAt}` : (canEdit ? "修改后点击保存即可更新该成员本周安排。" : "当前账号仅可查看安排。");
        return `
          <section class="member-card" data-user-id="${escapeHtml(userId)}">
            <div class="member-head">
              <div>
                <div class="member-name">${escapeHtml(name)}</div>
                <div class="member-meta">${escapeHtml(metaParts.join(" · ") || "未配置岗位/部门")}</div>
              </div>
              <div class="member-stats">${escapeHtml(statText)}</div>
            </div>
            <div class="week-grid">${rowMarkup}</div>
            <div class="stack" style="margin-top: 10px;">
              <label class="field">
                <span class="field-label">其他待办</span>
                <textarea data-user-id="${escapeHtml(userId)}" data-field="weekly_other_pending" ${canEdit ? "" : "disabled"} placeholder="补充跨天事项或其他待办">${escapeHtml(pendingValue)}</textarea>
              </label>
              <div class="helper-text">${escapeHtml(helperText)}</div>
            </div>
            ${dayMarkup}
            ${canEdit ? `
              <div class="member-actions">
                <button type="button" class="primary-btn" data-action="save-member" data-user-id="${escapeHtml(userId)}" ${savingUserIds.has(userId) ? "disabled" : ""}>${savingUserIds.has(userId) ? "保存中..." : "保存本周安排"}</button>
              </div>
            ` : ""}
          </section>
        `;
      }).join("");
    }

    function buildDayItemSummary(day) {
      const items = Array.isArray(day && day.items) ? day.items : [];
      return items.slice(0, 3).map((item) => {
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
      const days = Array.isArray(member && member.days) ? member.days : [];
      if (!days.length) {
        return "";
      }
      const dayCards = days.map((day) => {
        const label = `${String(day && day.weekday_label || "").trim()} ${String(day && day.work_date || "").trim()}`.trim();
        if (!day || day.has_entry !== true) {
          return `
            <div class="day-card">
              <div class="day-head"><span>${escapeHtml(label)}</span><span class="day-meta">未填写</span></div>
              <div class="day-empty">当天暂无日程明细。</div>
            </div>
          `;
        }
        const itemCount = Number(day.item_count || 0);
        const totalHours = String(day.total_hours || "").trim() || "0";
        const summaries = buildDayItemSummary(day);
        return `
          <div class="day-card">
            <div class="day-head"><span>${escapeHtml(label)}</span><span class="day-meta">${itemCount} 条 · ${escapeHtml(totalHours)} 小时</span></div>
            <div class="day-items">
              ${summaries.length ? summaries.map((summary) => `<div class="day-item">${escapeHtml(summary)}</div>`).join("") : '<div class="day-empty">已填写但无可展示摘要。</div>'}
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
      return pagePayload.members.find((member) => String(member && member.user && member.user.user_id || "").trim() === String(userId || "").trim()) || null;
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
      setStatus(pageStatusEl, `正在保存 ${String(member.user && member.user.display_name || member.user && member.user.user_id || "成员")} 的安排...`, false);
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
