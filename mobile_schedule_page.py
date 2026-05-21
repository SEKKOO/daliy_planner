from __future__ import annotations


MOBILE_SCHEDULE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>手机日程管理</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --panel-soft: #f8fbff;
      --line: #d8e3f0;
      --text: #16324d;
      --muted: #67809a;
      --primary: #2563c9;
      --primary-strong: #174b9d;
      --primary-soft: #e7f0ff;
      --danger: #c0394b;
      --danger-soft: #fff2f4;
      --success: #1d8a59;
      --shadow: 0 12px 28px rgba(28, 66, 120, 0.08);
      --radius: 18px;
      --radius-sm: 12px;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      min-height: 100%;
      background: linear-gradient(180deg, #eef5ff 0%, #f8fbff 36%, #f4f7fb 100%);
      color: var(--text);
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }

    body {
      padding: env(safe-area-inset-top, 0) 0 env(safe-area-inset-bottom, 0);
    }

    button,
    input,
    select,
    textarea {
      font: inherit;
    }

    button {
      border: none;
      border-radius: 999px;
      cursor: pointer;
    }

    input,
    select,
    textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      color: var(--text);
      padding: 12px 14px;
    }

    textarea {
      min-height: 92px;
      resize: vertical;
    }

    .shell {
      width: min(100%, 760px);
      margin: 0 auto;
      padding: 14px 14px 110px;
    }

    .card {
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid rgba(216, 227, 240, 0.9);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 18px 18px 14px;
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
      line-height: 1.1;
    }

    .user-line {
      margin-top: 8px;
      font-size: 13px;
      color: var(--muted);
    }

    .ghost-btn,
    .text-btn {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--line);
      padding: 10px 14px;
    }

    .ghost-btn[hidden],
    .text-btn[hidden] {
      display: none;
    }

    .login-card,
    .editor-card {
      padding: 16px;
    }

    .section-title {
      margin: 0 0 10px;
      font-size: 18px;
    }

    .section-text {
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 14px;
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

    .date-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
    }

    .today-btn {
      background: var(--primary-soft);
      color: var(--primary);
      padding: 12px 16px;
      font-weight: 700;
    }

    .status {
      min-height: 22px;
      margin: 8px 0 14px;
      font-size: 13px;
      color: var(--muted);
    }

    .status.is-error {
      color: var(--danger);
    }

    .item-list {
      display: grid;
      gap: 12px;
    }

    .item-card {
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
      padding: 14px;
    }

    .item-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }

    .item-title {
      font-size: 15px;
      font-weight: 700;
    }

    .item-remove {
      padding: 8px 12px;
      background: var(--danger-soft);
      color: var(--danger);
      border: 1px solid rgba(192, 57, 75, 0.16);
    }

    .grid-two {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .actions {
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 20;
      padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0));
      background: rgba(244, 247, 251, 0.94);
      backdrop-filter: blur(16px);
      border-top: 1px solid rgba(216, 227, 240, 0.92);
    }

    .actions-inner {
      width: min(100%, 760px);
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .action-btn {
      padding: 13px 12px;
      font-weight: 700;
      border-radius: 16px;
    }

    .action-btn.primary {
      background: var(--primary);
      color: #fff;
    }

    .action-btn.soft {
      background: var(--primary-soft);
      color: var(--primary);
    }

    .action-btn.danger {
      background: #fff;
      color: var(--danger);
      border: 1px solid rgba(192, 57, 75, 0.2);
    }

    .action-btn:disabled,
    .ghost-btn:disabled,
    .today-btn:disabled,
    .item-remove:disabled {
      opacity: 0.56;
      cursor: not-allowed;
    }

    @media (max-width: 420px) {
      .shell {
        padding-left: 10px;
        padding-right: 10px;
      }

      .head {
        padding: 16px 14px 12px;
      }

      .login-card,
      .editor-card {
        padding: 14px;
      }

      .grid-two,
      .actions-inner {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="card head">
      <div>
        <div class="eyebrow">MOBILE SCHEDULE</div>
        <h1 class="title">我的日程</h1>
        <div class="user-line" id="mobile-user-line">请先登录后查看并编辑自己的日程。</div>
      </div>
      <button type="button" class="ghost-btn" id="mobile-logout-button" hidden>退出</button>
    </section>

    <section class="card login-card" id="mobile-login-card">
      <h2 class="section-title">登录</h2>
      <p class="section-text">使用本地账号登录后，即可在手机端直接查看、编辑和保存自己的日程。</p>
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
      <button type="button" class="action-btn primary" id="mobile-login-button" style="width:100%;">登录并进入日程</button>
    </section>

    <section class="card editor-card" id="mobile-editor-card" hidden>
      <div class="date-row">
        <input id="mobile-work-date" type="date" value="__INITIAL_DATE__">
        <button type="button" class="today-btn" id="mobile-today-button">今天</button>
      </div>
      <div class="status" id="mobile-editor-status" aria-live="polite"></div>
      <datalist id="mobile-customer-options"></datalist>
      <div class="item-list" id="mobile-item-list"></div>
    </section>
  </main>

  <div class="actions" id="mobile-actions" hidden>
    <div class="actions-inner">
      <button type="button" class="action-btn soft" id="mobile-add-button">新增事项</button>
      <button type="button" class="action-btn danger" id="mobile-delete-button">清空当天</button>
      <button type="button" class="action-btn primary" id="mobile-save-button">保存日程</button>
    </div>
  </div>

  <script>
    const bootAuthState = __INITIAL_AUTH_STATE_PAYLOAD__;
    const DEFAULT_FIELD_OPTIONS = {
      item_types: ["方案交流", "方案汇报", "POC1", "POC2", "交付", "服务", "基建"],
      project_types: ["A", "B+", "B", "C"],
      sales: [],
      service_modes: ["客户现场", "远程支持"]
    };

    const userLineEl = document.getElementById("mobile-user-line");
    const loginCardEl = document.getElementById("mobile-login-card");
    const loginUsernameEl = document.getElementById("mobile-login-username");
    const loginPasswordEl = document.getElementById("mobile-login-password");
    const loginStatusEl = document.getElementById("mobile-login-status");
    const loginButtonEl = document.getElementById("mobile-login-button");
    const logoutButtonEl = document.getElementById("mobile-logout-button");
    const editorCardEl = document.getElementById("mobile-editor-card");
    const actionsEl = document.getElementById("mobile-actions");
    const dateInputEl = document.getElementById("mobile-work-date");
    const todayButtonEl = document.getElementById("mobile-today-button");
    const editorStatusEl = document.getElementById("mobile-editor-status");
    const itemListEl = document.getElementById("mobile-item-list");
    const customerOptionsEl = document.getElementById("mobile-customer-options");
    const addButtonEl = document.getElementById("mobile-add-button");
    const deleteButtonEl = document.getElementById("mobile-delete-button");
    const saveButtonEl = document.getElementById("mobile-save-button");

    let authState = normalizeAuthState(bootAuthState);
    let fieldOptions = { ...DEFAULT_FIELD_OPTIONS };
    let customerNames = [];
    let itemState = [];
    let hasLoadedEntry = false;
    let hasExistingEntry = false;
    let isSubmittingLogin = false;
    let isLoadingEntry = false;
    let isSavingEntry = false;
    let isDeletingEntry = false;

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

    function normalizeFieldOptionList(values) {
      if (!Array.isArray(values)) {
        return [];
      }
      const seen = new Set();
      return values
        .map((value) => String(value || "").trim())
        .filter((value) => {
          if (!value || seen.has(value)) {
            return false;
          }
          seen.add(value);
          return true;
        });
    }

    function createEmptyItem() {
      return {
        customer_name: "",
        project_type: "",
        sales: "",
        item_type: "",
        service_mode: "",
        work_hours: "",
        work_content: "",
        pending_issues: "",
        risk: "",
      };
    }

    function normalizeItem(source) {
      const payload = source && typeof source === "object" ? source : {};
      return {
        customer_name: String(payload.customer_name || "").trim(),
        project_type: String(payload.project_type || "").trim(),
        sales: String(payload.sales || "").trim(),
        item_type: String(payload.item_type || "").trim(),
        service_mode: String(payload.service_mode || "").trim(),
        work_hours: String(payload.work_hours == null ? "" : payload.work_hours).trim(),
        work_content: String(payload.work_content || "").trim(),
        pending_issues: String(payload.pending_issues || payload.notes || "").trim(),
        risk: String(payload.risk || "").trim(),
      };
    }

    function hasMeaningfulItem(item) {
      return Object.values(normalizeItem(item)).some((value) => String(value || "").trim());
    }

    function getCurrentUserLabel() {
      if (!(authState.authenticated && authState.user)) {
        return "请先登录后查看并编辑自己的日程。";
      }
      const displayName = String(authState.user.display_name || authState.user.user_id || "当前用户").trim();
      return `${displayName} · 仅展示并编辑自己的日程`;
    }

    function buildSelectOptions(options, value, placeholder) {
      const normalizedValue = String(value || "").trim();
      const optionList = normalizeFieldOptionList(options);
      const markup = [`<option value="">${escapeHtml(placeholder)}</option>`];
      optionList.forEach((option) => {
        const selected = option === normalizedValue ? ' selected' : '';
        markup.push(`<option value="${escapeHtml(option)}"${selected}>${escapeHtml(option)}</option>`);
      });
      if (normalizedValue && !optionList.includes(normalizedValue)) {
        markup.push(`<option value="${escapeHtml(normalizedValue)}" selected>${escapeHtml(normalizedValue)}</option>`);
      }
      return markup.join("");
    }

    function renderCustomerOptions() {
      customerOptionsEl.innerHTML = customerNames
        .map((name) => `<option value="${escapeHtml(name)}"></option>`)
        .join("");
    }

    function renderItems() {
      if (!itemState.length) {
        itemState = [createEmptyItem()];
      }
      itemListEl.innerHTML = itemState.map((item, index) => `
        <section class="item-card" data-index="${index}">
          <div class="item-head">
            <div class="item-title">事项 ${index + 1}</div>
            <button type="button" class="item-remove" data-action="remove-item" data-index="${index}">删除</button>
          </div>
          <div class="stack">
            <label class="field">
              <span class="field-label">客户名称</span>
              <input data-field="customer_name" data-index="${index}" list="mobile-customer-options" value="${escapeHtml(item.customer_name || "")}" placeholder="请输入客户名称">
            </label>
            <div class="grid-two">
              <label class="field">
                <span class="field-label">项目类型</span>
                <select data-field="project_type" data-index="${index}">
                  ${buildSelectOptions(fieldOptions.project_types, item.project_type, "请选择")}
                </select>
              </label>
              <label class="field">
                <span class="field-label">销售</span>
                <select data-field="sales" data-index="${index}">
                  ${buildSelectOptions(fieldOptions.sales, item.sales, "请选择")}
                </select>
              </label>
            </div>
            <div class="grid-two">
              <label class="field">
                <span class="field-label">事项类型</span>
                <select data-field="item_type" data-index="${index}">
                  ${buildSelectOptions(fieldOptions.item_types, item.item_type, "请选择")}
                </select>
              </label>
              <label class="field">
                <span class="field-label">服务方式</span>
                <select data-field="service_mode" data-index="${index}">
                  ${buildSelectOptions(fieldOptions.service_modes, item.service_mode, "请选择")}
                </select>
              </label>
            </div>
            <label class="field">
              <span class="field-label">工时</span>
              <input data-field="work_hours" data-index="${index}" type="number" min="0" step="0.5" value="${escapeHtml(item.work_hours || "")}" placeholder="请输入工时">
            </label>
            <label class="field">
              <span class="field-label">工作内容</span>
              <textarea data-field="work_content" data-index="${index}" placeholder="请输入工作内容">${escapeHtml(item.work_content || "")}</textarea>
            </label>
            <label class="field">
              <span class="field-label">遗留事项</span>
              <textarea data-field="pending_issues" data-index="${index}" placeholder="请输入遗留事项">${escapeHtml(item.pending_issues || "")}</textarea>
            </label>
            <label class="field">
              <span class="field-label">存在风险</span>
              <textarea data-field="risk" data-index="${index}" placeholder="请输入存在风险">${escapeHtml(item.risk || "")}</textarea>
            </label>
          </div>
        </section>
      `).join("");

      Array.from(itemListEl.querySelectorAll(".item-remove")).forEach((button) => {
        button.disabled = itemState.length <= 1 || isSavingEntry || isDeletingEntry || isLoadingEntry;
      });
    }

    function syncActionState() {
      const disabled = !authState.authenticated || isSavingEntry || isDeletingEntry || isLoadingEntry;
      saveButtonEl.disabled = disabled;
      addButtonEl.disabled = disabled;
      todayButtonEl.disabled = disabled;
      deleteButtonEl.disabled = disabled || !hasExistingEntry;
      dateInputEl.disabled = disabled;
      loginButtonEl.disabled = isSubmittingLogin;
    }

    function renderLayout() {
      userLineEl.textContent = getCurrentUserLabel();
      loginCardEl.hidden = authState.authenticated;
      editorCardEl.hidden = !authState.authenticated;
      actionsEl.hidden = !authState.authenticated;
      logoutButtonEl.hidden = !authState.authenticated;
      if (authState.authenticated) {
        renderCustomerOptions();
        renderItems();
      }
      syncActionState();
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
      renderLayout();
    }

    async function loadFieldOptions() {
      const payload = await requestJson("/api/field-options");
      const source = payload && typeof payload === "object" ? payload : {};
      fieldOptions = {
        item_types: normalizeFieldOptionList(source.item_types || DEFAULT_FIELD_OPTIONS.item_types),
        project_types: normalizeFieldOptionList(source.project_types || DEFAULT_FIELD_OPTIONS.project_types),
        sales: normalizeFieldOptionList(source.sales || DEFAULT_FIELD_OPTIONS.sales),
        service_modes: normalizeFieldOptionList(source.service_modes || DEFAULT_FIELD_OPTIONS.service_modes),
      };
    }

    async function loadCustomerNames() {
      const payload = await requestJson("/api/customer-names");
      customerNames = Array.isArray(payload.customer_names)
        ? payload.customer_names.map((name) => String(name || "").trim()).filter(Boolean)
        : [];
    }

    async function loadEntry() {
      if (!authState.authenticated) {
        return;
      }
      isLoadingEntry = true;
      syncActionState();
      setStatus(editorStatusEl, "正在加载日程...", false);
      try {
        const payload = await requestJson(`/api/entry?date=${encodeURIComponent(dateInputEl.value)}`);
        const entry = payload.entry && typeof payload.entry === "object" ? payload.entry : null;
        hasExistingEntry = Boolean(entry);
        hasLoadedEntry = true;
        itemState = entry && Array.isArray(entry.items) && entry.items.length
          ? entry.items.map((item) => normalizeItem(item))
          : [createEmptyItem()];
        setStatus(editorStatusEl, entry ? `已加载 ${dateInputEl.value} 的日程。` : "当天暂无日程，可直接填写后保存。", false);
      } catch (error) {
        itemState = [createEmptyItem()];
        hasExistingEntry = false;
        setStatus(editorStatusEl, error.message || "读取日程失败。", true);
      } finally {
        isLoadingEntry = false;
        renderLayout();
      }
    }

    function collectSubmitItems() {
      return itemState
        .map((item) => normalizeItem(item))
        .filter((item) => hasMeaningfulItem(item));
    }

    async function saveEntry() {
      if (!authState.authenticated || isSavingEntry || isDeletingEntry) {
        return;
      }
      const items = collectSubmitItems();
      if (!items.length) {
        setStatus(editorStatusEl, "请至少填写一条有效事项。", true);
        return;
      }
      isSavingEntry = true;
      syncActionState();
      setStatus(editorStatusEl, "正在保存日程...", false);
      try {
        const payload = await requestJson("/api/entry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            work_date: dateInputEl.value,
            items,
          }),
        });
        const entry = payload.entry && typeof payload.entry === "object" ? payload.entry : null;
        hasExistingEntry = Boolean(entry);
        itemState = entry && Array.isArray(entry.items) && entry.items.length
          ? entry.items.map((item) => normalizeItem(item))
          : [createEmptyItem()];
        setStatus(editorStatusEl, "日程已保存。", false);
      } catch (error) {
        setStatus(editorStatusEl, error.message || "保存日程失败。", true);
      } finally {
        isSavingEntry = false;
        renderLayout();
      }
    }

    async function deleteEntry() {
      if (!authState.authenticated || isDeletingEntry || !hasExistingEntry) {
        return;
      }
      isDeletingEntry = true;
      syncActionState();
      setStatus(editorStatusEl, "正在清空当天日程...", false);
      try {
        await requestJson(`/api/entry?date=${encodeURIComponent(dateInputEl.value)}`, { method: "DELETE" });
        hasExistingEntry = false;
        itemState = [createEmptyItem()];
        setStatus(editorStatusEl, "当天日程已清空。", false);
      } catch (error) {
        setStatus(editorStatusEl, error.message || "清空失败。", true);
      } finally {
        isDeletingEntry = false;
        renderLayout();
      }
    }

    async function login() {
      if (isSubmittingLogin) {
        return;
      }
      const username = String(loginUsernameEl.value || "").trim();
      const password = String(loginPasswordEl.value || "");
      if (!username || !password) {
        setStatus(loginStatusEl, "请输入用户名和密码。", true);
        return;
      }
      isSubmittingLogin = true;
      syncActionState();
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
        await bootstrapEditor();
      } catch (error) {
        setStatus(loginStatusEl, error.message || "登录失败。", true);
      } finally {
        isSubmittingLogin = false;
        syncActionState();
      }
    }

    async function logout() {
      try {
        await requestJson("/api/auth/logout", { method: "POST" });
      } catch (error) {
        // Ignore logout response errors and clear local state anyway.
      }
      authState = normalizeAuthState({ authenticated: false, user: null });
      itemState = [createEmptyItem()];
      hasExistingEntry = false;
      hasLoadedEntry = false;
      setStatus(editorStatusEl, "", false);
      renderLayout();
    }

    async function bootstrapEditor() {
      if (!authState.authenticated) {
        return;
      }
      try {
        await Promise.all([loadFieldOptions(), loadCustomerNames()]);
      } catch (error) {
        setStatus(editorStatusEl, error.message || "初始化失败。", true);
      }
      await loadEntry();
    }

    function setToday() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, "0");
      const day = String(today.getDate()).padStart(2, "0");
      dateInputEl.value = `${year}-${month}-${day}`;
    }

    itemListEl.addEventListener("input", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement)) {
        return;
      }
      const index = Number.parseInt(target.dataset.index || "", 10);
      const field = String(target.dataset.field || "").trim();
      if (!Number.isInteger(index) || !itemState[index] || !field) {
        return;
      }
      itemState[index][field] = String(target.value || "");
    });

    itemListEl.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const removeButton = target.closest("[data-action='remove-item']");
      if (!removeButton) {
        return;
      }
      const index = Number.parseInt(String(removeButton.getAttribute("data-index") || ""), 10);
      if (!Number.isInteger(index) || itemState.length <= 1) {
        return;
      }
      itemState.splice(index, 1);
      renderLayout();
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
    todayButtonEl.addEventListener("click", async () => {
      setToday();
      await loadEntry();
    });
    dateInputEl.addEventListener("change", () => {
      loadEntry();
    });
    addButtonEl.addEventListener("click", () => {
      itemState.push(createEmptyItem());
      renderLayout();
    });
    saveButtonEl.addEventListener("click", saveEntry);
    deleteButtonEl.addEventListener("click", deleteEntry);

    renderLayout();
    if (authState.authenticated) {
      bootstrapEditor();
    }
  </script>
</body>
</html>
"""


def render_mobile_schedule_html(*, initial_date: str, initial_auth_payload_json: str) -> str:
    html = MOBILE_SCHEDULE_HTML.replace("__INITIAL_DATE__", initial_date)
    html = html.replace("__INITIAL_AUTH_STATE_PAYLOAD__", initial_auth_payload_json)
    return html
