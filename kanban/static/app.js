/* Kanban Dashboard — client-side logic */
(function () {
  const API = "/api/stories";
  let stories = [];
  let autoTrigger = localStorage.getItem("kanban-auto-trigger") !== "false";

  // ── Toast ────────────────────────────────────────────────────────
  function showToast(message, variant = "success") {
    const c = document.getElementById("kb-toasts");
    if (!c) return;
    const t = document.createElement("div");
    t.className = `toast toast-${variant}`;
    t.textContent = message;
    c.appendChild(t);
    setTimeout(() => t.remove(), 5000);
  }

  // ── OpenCode health check ────────────────────────────────────────
  let ocConnected = false;

  async function checkOpenCode() {
    try {
      const r = await fetch("http://localhost:4096/global/health", { signal: AbortSignal.timeout(2000) });
      ocConnected = r.ok;
    } catch {
      ocConnected = false;
    }
    const dot = document.getElementById("kb-oc-status");
    if (dot) {
      dot.className = `indicator ${ocConnected ? "on" : "off"}`;
      dot.title = ocConnected ? "OpenCode connecté (port 4096)" : "OpenCode injoignable — lance 'opencode --port 4096'";
    }
  }

  // ── Fetch ────────────────────────────────────────────────────────
  async function loadStories() {
    const r = await fetch(API);
    stories = await r.json();
    render();
  }

  async function updateStory(id, data) {
    const url = new URL(`${API}/${encodeURIComponent(id)}`, location.origin);
    if (!autoTrigger) url.searchParams.set("no_trigger", "1");
    const r = await fetch(url.toString(), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await r.json();
    if (result && result._trigger) {
      const tr = result._trigger;
      if (tr.triggered) {
        showToast(`OpenCode ← ${tr.command}`);
      } else if (tr.disabled) {
      } else if (tr.error) {
        showToast(`⚠ OpenCode injoignable — ${tr.error}. Lance 'opencode --port 4096'`, "warning");
      }
    } else if (data.status === "refining" && !autoTrigger) {
      showToast(`⏸ Auto-trigger désactivé — active le bouton "Auto" pour lancer OpenCode`, "warning");
    }
    await loadStories();
  }

  async function deleteStory(id) {
    await fetch(`${API}/${encodeURIComponent(id)}`, { method: "DELETE" });
    await loadStories();
  }

  async function createStory(data) {
    await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    await loadStories();
  }

  // ── Render ───────────────────────────────────────────────────────
  function render() {
    renderKanban();
    renderStats();
    renderList();
    updateCounts();
    updateView();
  }

  function filterText() {
    const q = document.getElementById("kb-search").value.toLowerCase();
    return q;
  }

  function matches(s, q) {
    if (!q) return true;
    return (
      s.id.toLowerCase().includes(q) ||
      s.title.toLowerCase().includes(q) ||
      (s.description || "").toLowerCase().includes(q) ||
      (s.phase_name || "").toLowerCase().includes(q)
    );
  }

  function colStatus(s) {
    return s.status || "pending";
  }

  const STACK_OPTIONS = ["backend", "frontend", "database", "devops", "infrastructure", "architecture", "security", "docs", "bugfix"];
  const STACK_COLORS = {
    backend: "#3b82f6", frontend: "#f59e0b", database: "#10b981", devops: "#8b5cf6",
    infrastructure: "#6b7280", architecture: "#06b6d4", security: "#ef4444",
    docs: "#94a3b8", bugfix: "#f97316",
  };

  function tddBadge(s) {
    const st = (s.tdd && s.tdd.status) || "pending";
    return `<span class="c-badge ${st}">TDD ${badgeIcon(st)}</span>`;
  }

  function qaBadge(s) {
    const st = (s.qa && s.qa.status) || "pending";
    return `<span class="c-badge ${st}">QA ${badgeIcon(st)}</span>`;
  }

  function stackBadges(s) {
    const stack = s.stack || [];
    if (!stack.length) return "";
    return stack.map((t) => {
      const c = STACK_COLORS[t] || "#64748b";
      return `<span class="c-badge" style="background:${c}18;color:${c};border:1px solid ${c}44">${t}</span>`;
    }).join("");
  }

  function badgeIcon(st) {
    return st === "passed" ? "✓" : st === "failed" ? "✗" : st === "in_progress" ? "◌" : "○";
  }

  function cardHtml(s) {
    const q = filterText();
    if (!matches(s, q)) return "";
    return `<div class="card" data-id="${s.id}">
      <div class="c-top">
        <span class="c-id">${s.id}</span>
        <span class="c-prio ${s.priority}">${s.priority}</span>
      </div>
      <div class="c-title">${escHtml(s.title || "")}</div>
      <div class="c-badges">${tddBadge(s)}${qaBadge(s)}${stackBadges(s)}</div>
    </div>`;
  }

  function renderKanban() {
    document.querySelectorAll(".kcol-list").forEach((el) => {
      const status = el.dataset.list;
      const items = stories
        .filter((s) => colStatus(s) === status)
        .sort((a, b) => (a.order ?? 9999) - (b.order ?? 9999) || a.id.localeCompare(b.id));
      el.innerHTML = items.map(cardHtml).join("");
    });
  }

  function renderStats() {
    const totals = { pending: 0, refining: 0, secops_tm: 0, tdd: 0, secops_cr: 0, qa: 0, simplify: 0, commit_ready: 0, completed: 0, blocked: 0 };
    stories.forEach((s) => {
      const st = colStatus(s);
      if (st in totals) totals[st]++;
    });
    const total = stories.length;
    const done = totals.completed;
    const pct = total ? Math.round((done / total) * 100) : 0;
    document.getElementById("kb-stats").innerHTML = `
      <span class="s-item"><span class="s-dot" style="background:#6b7280"></span>En attente <span class="s-num">${totals.pending}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#f59e0b"></span>Raffinement <span class="s-num">${totals.refining}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#7c3aed"></span>SecOps <span class="s-num">${totals.secops_tm}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#3b82f6"></span>TDD <span class="s-num">${totals.tdd}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#a78bfa"></span>SecOps Rev <span class="s-num">${totals.secops_cr}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#ec4899"></span>QA <span class="s-num">${totals.qa}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#14b8a6"></span>Simplify <span class="s-num">${totals.simplify}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#10b981"></span>Prêt commit <span class="s-num">${totals.commit_ready}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#065f46"></span>Terminé <span class="s-num">${totals.completed}</span></span>
      <span class="s-sep"></span>
      <span class="s-item"><span class="s-dot" style="background:#ef4444"></span>Bloqué <span class="s-num">${totals.blocked}</span></span>
      <span style="flex:1"></span>
      <span style="color:#64748b">${done}/${total} · ${pct}% complet</span>`;
  }

  function renderList() {
    const tbody = document.getElementById("kb-list-body");
    const q = filterText();
    const items = stories.filter((s) => matches(s, q));
    const labels = {
      pending: "En attente", refining: "Raffinement", secops_tm: "SecOps",
      tdd: "TDD", secops_cr: "SecOps Rev", qa: "QA", simplify: "Simplify",
      commit_ready: "Prêt commit", completed: "Terminé", blocked: "Bloqué",
    };
    const colors = {
      pending: "#6b7280", refining: "#f59e0b", secops_tm: "#7c3aed",
      tdd: "#3b82f6", secops_cr: "#a78bfa", qa: "#ec4899", simplify: "#14b8a6",
      commit_ready: "#10b981", completed: "#065f46", blocked: "#ef4444",
    };
    tbody.innerHTML = items
      .map(
        (s) => `<tr data-id="${s.id}">
          <td style="font-family:monospace;color:#64748b">${s.id}</td>
          <td>${escHtml(s.title)}</td>
          <td class="lv-phase">${s.phase}: ${escHtml(s.phase_name)}</td>
          <td><span class="c-prio ${s.priority}">${s.priority}</span></td>
          <td><span class="lv-status" style="color:${colors[colStatus(s)]};background:${colors[colStatus(s)]}11">● ${labels[colStatus(s)] || colStatus(s)}</span></td>
          <td>${badgeIcon((s.tdd && s.tdd.status) || "pending")}</td>
          <td>${badgeIcon((s.qa && s.qa.status) || "pending")}</td>
        </tr>`
      )
      .join("");
  }

  function updateCounts() {
    ["pending", "refining", "secops_tm", "tdd", "secops_cr", "qa", "simplify", "commit_ready", "completed", "blocked"].forEach((st) => {
      const el = document.querySelector(`[data-count="${st}"]`);
      if (el) el.textContent = stories.filter((s) => colStatus(s) === st).length;
    });
  }

  function updateView() {
    const mode = document.querySelector(".toggle-group .active");
    if (!mode) return;
    const view = mode.dataset.view;
    const kanban = document.getElementById("kb-kanban");
    const list = document.getElementById("kb-list");
    kanban.classList.toggle("hidden", view !== "kanban");
    list.classList.toggle("visible", view === "list");
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  // ── SortableJS ───────────────────────────────────────────────────
  function initSortable() {
    document.querySelectorAll(".kcol-list").forEach((el) => {
      Sortable.create(el, {
        group: "kanban",
        animation: 200,
        ghostClass: "sortable-ghost",
        chosenClass: "sortable-chosen",
        onEnd: async function (evt) {
          const storyId = evt.item.dataset.id;
          const newCol = evt.to.closest(".kcol");
          if (!newCol) return;
          const newStatus = newCol.dataset.status;
          const oldStatus = evt.from.closest(".kcol").dataset.status;
          if (newStatus === oldStatus) {
            // Reorder within same column — persist new order
            const cards = evt.to.querySelectorAll(".card");
            const order = Array.from(cards).map((c) => c.dataset.id);
            await fetch("/api/reorder", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ status: newStatus, order }),
            });
            // Sync local stories order so list view stays consistent
            order.forEach((id, idx) => {
              const s = stories.find((x) => x.id === id);
              if (s) s.order = idx;
            });
          } else {
            await updateStory(storyId, { status: newStatus });
          }
        },
        });
    });
  }

  // ── Modal ────────────────────────────────────────────────────────
  function openModal(storyId) {
    const s = stories.find((x) => x.id === storyId);
    if (!s) return;
    const overlay = document.getElementById("kb-modal");
    document.getElementById("modal-title").textContent = `✏️ ${s.id}`;
    document.getElementById("modal-body").innerHTML = modalContent(s);

    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        document.querySelector(`.tab-panel[data-panel="${btn.dataset.tab}"]`).classList.add("active");
      });
    });

    overlay.classList.add("open");
  }

  function closeModal() {
    document.getElementById("kb-modal").classList.remove("open");
  }

  function historySection(s) {
    const entries = (s.history || []).slice().reverse().slice(0, 15);
    if (!entries.length) {
      return `<div class="m-section"><h3>Historique</h3><p style="color:#475569;font-size:0.75rem">Aucune modification enregistrée.</p></div>`;
    }
    const rows = entries.map((e) => {
      const actor = (e.by || "?").replace(/[^a-z0-9-]/gi, "");
      return `<div class="h-entry">
        <span class="h-ts">${e.ts || ""}</span>
        <span class="h-by by-${actor}">${e.by || "?"}</span>
        <span class="h-changes">${escHtml((e.changes || []).join(" · "))}</span>
      </div>`;
    }).join("");
    return `<div class="m-section"><h3>Historique</h3><div class="h-list">${rows}</div></div>`;
  }

  function implementationGuideSection(s) {
    const ig = s.implementation_guide;
    if (!ig || typeof ig !== "object" || !Object.keys(ig).length) return "";

    const scopeBadges = (ig.scope || [])
      .map((sc) => `<span class="ig-scope-badge">${escHtml(sc)}</span>`)
      .join("");

    const typeHtml = ig.type
      ? `<div class="ig-meta-row"><span class="ig-label">Type</span><span class="ig-type-badge">${escHtml(ig.type)}</span>${scopeBadges}</div>`
      : "";

    const approachHtml = ig.approach
      ? `<div class="ig-approach">${escHtml(ig.approach)}</div>`
      : "";

    function fileList(files, colorClass) {
      if (!files || !files.length) return "";
      return files.map((f) => {
        const detail = f.role || f.change || f.reason || "";
        return `<div class="ig-file ${colorClass}"><code>${escHtml(f.path)}</code>${detail ? `<span class="ig-file-detail">${escHtml(detail)}</span>` : ""}</div>`;
      }).join("");
    }

    const filesCreate = fileList(ig.files_create, "ig-create");
    const filesModify = fileList(ig.files_modify, "ig-modify");
    const filesDelete = fileList(ig.files_delete, "ig-delete");
    const filesHtml = (filesCreate || filesModify || filesDelete)
      ? `<div class="ig-files-section">
          <div class="ig-sub-label">Fichiers</div>
          <div class="ig-files">${filesCreate}${filesModify}${filesDelete}</div>
        </div>`
      : "";

    const stepsHtml = ig.steps && ig.steps.length
      ? `<div class="ig-steps-section">
          <div class="ig-sub-label">Séquence d'implémentation</div>
          <div class="ig-steps">${ig.steps.map((st, i) =>
            `<div class="ig-step"><span class="ig-step-num">${i + 1}</span><span class="ig-step-text">${escHtml(st.replace(/^\d+\.\s*/, ""))}</span></div>`
          ).join("")}</div>
        </div>`
      : "";

    const bottomMeta = [
      ig.test_strategy ? `<div class="ig-bottom-row"><span class="ig-label">Tests</span><span>${escHtml(ig.test_strategy)}</span></div>` : "",
      ig.constraints ? `<div class="ig-bottom-row"><span class="ig-label">Contraintes</span><span>${escHtml(ig.constraints)}</span></div>` : "",
      ig.data_model ? `<div class="ig-bottom-row"><span class="ig-label">Modèle</span><span>${escHtml(ig.data_model)}</span></div>` : "",
    ].filter(Boolean).join("");

    const body = [typeHtml, approachHtml, filesHtml, stepsHtml, bottomMeta].filter(Boolean).join("");
    if (!body) return "";

    return `<div class="m-section"><h3>Plan d'implémentation</h3><div class="ig-body">${body}</div></div>`;
  }

  function simplifyReportSection(s) {
    const r = s.simplify_report;
    if (!r || !r.status) return "";
    const statusColor = { passed: "#22c55e", fixed: "#fb923c", skipped: "#64748b" }[r.status] || "#64748b";
    const statusLabel = { passed: "Aucun problème", fixed: "Problèmes corrigés", skipped: "Ignoré" }[r.status] || r.status;
    const agentRows = r.agents
      ? Object.entries(r.agents).map(([agent, summary]) =>
          `<div class="sr-agent"><span class="sr-agent-name">${escHtml(agent)}</span><span class="sr-agent-summary">${escHtml(summary)}</span></div>`
        ).join("")
      : "";
    const counters = (r.issues_found != null)
      ? `<div class="sr-counters">
          <span class="sr-counter"><span class="sr-num">${r.issues_found}</span> trouvés</span>
          <span class="sr-counter sr-fixed"><span class="sr-num">${r.issues_fixed ?? 0}</span> corrigés</span>
        </div>`
      : "";
    const notes = r.notes ? `<div class="sr-notes">${escHtml(r.notes)}</div>` : "";
    return `<div class="m-section sr-section">
      <h3>Simplify <span class="sr-status" style="background:${statusColor}20;color:${statusColor};border-color:${statusColor}40">${statusLabel}</span></h3>
      ${counters}
      ${agentRows}
      ${notes}
    </div>`;
  }

  function refinementSection(s) {
    const decisions = s.refine_decisions || [];
    if (!decisions.length) return "";
    const items = decisions.map((d) => {
      if (typeof d === "string") {
        return `<div class="rd-item"><span class="rd-decision">${escHtml(d)}</span></div>`;
      }
      const role = d.role ? `<span class="rd-role">${escHtml(d.role)}</span>` : "";
      const q = d.question ? `<span class="rd-q">${escHtml(d.question)}</span>` : "";
      const dec = escHtml(d.decision || d.text || "");
      return `<div class="rd-item">${role}${q}<span class="rd-decision">→ ${dec}</span></div>`;
    }).join("");
    return `<div class="m-section"><h3>Décisions de raffinement</h3><div class="rd-list">${items}</div></div>`;
  }

  function modalContent(s) {
    const acs = (s.acceptance_criteria || [])
      .map(
        (ac, i) => `<div class="ac-item">
          <input type="checkbox" class="ac-check" data-acidx="${i}" ${ac.checked ? "checked" : ""}>
          <input type="text" class="ac-text" value="${escHtml(ac.text)}" data-acidx="${i}">
        </div>`
      )
      .join("");

    const statuses = ["pending", "refining", "secops_tm", "tdd", "secops_cr", "qa", "simplify", "commit_ready", "completed", "blocked"];
    const statusLabels = {
      pending: "En attente", refining: "Raffinement", secops_tm: "SecOps",
      tdd: "TDD", secops_cr: "SecOps Rev", qa: "QA", simplify: "Simplify",
      commit_ready: "Prêt commit", completed: "Terminé", blocked: "Bloqué",
    };

    const currentStack = s.stack || [];
    const stackHtml = STACK_OPTIONS.map((t) => {
      const c = STACK_COLORS[t] || "#64748b";
      const active = currentStack.includes(t) ? "active" : "";
      return `<span class="stack-tag ${active}" style="--stk-color:${c}" data-stk="${t}">${t}</span>`;
    }).join("");

    const tddStatuses = ["pending", "in_progress", "passed", "failed"];
    const qaStatuses = ["pending", "in_progress", "passed", "failed"];

    const hasRefine = (s.refine_decisions || []).length > 0 ||
      (s.implementation_guide && Object.keys(s.implementation_guide).length > 0);

    return `
    <div class="m-inline">
      <div class="m-row"><label>ID</label><input type="text" id="me-id" value="${s.id}" readonly style="color:#64748b"></div>
      <div class="m-row"><label>Phase</label><input type="text" value="Phase ${s.phase} — ${escHtml(s.phase_name)}" readonly style="color:#64748b"></div>
    </div>
    <div class="m-row"><label>Titre</label><input type="text" id="me-title" value="${escHtml(s.title || "")}"></div>
    <div class="m-inline">
      <div class="m-row"><label>Priorité</label><select id="me-prio">
        ${["P0", "P1", "P2", "Future"].map((p) => `<option ${s.priority === p ? "selected" : ""} value="${p}">${p}</option>`).join("")}
      </select></div>
      <div class="m-row"><label>Statut</label><select id="me-status">
        ${statuses.map((st) => `<option ${colStatus(s) === st ? "selected" : ""} value="${st}">${statusLabels[st] || st}</option>`).join("")}
      </select></div>
    </div>
    <div class="m-section">
      <h3>Stack / Catégories</h3>
      <div class="stack-tags" id="me-stack">${stackHtml}</div>
    </div>

    <div class="modal-tabs">
      <button class="tab-btn active" data-tab="spec">Spécification</button>
      <button class="tab-btn" data-tab="refine">Raffinement${hasRefine ? '<span class="tab-dot"></span>' : ''}</button>
      <button class="tab-btn" data-tab="progress">Avancement</button>
      <button class="tab-btn" data-tab="history">Historique</button>
    </div>

    <div class="tab-panel active" data-panel="spec">
      <div class="m-row"><label>Description</label><textarea id="me-desc" rows="3">${escHtml(s.description || "")}</textarea></div>
      <div class="m-section">
        <h3>Critères d'acceptation</h3>
        <div id="me-acs">${acs}</div>
      </div>
    </div>

    <div class="tab-panel" data-panel="refine">
      ${refinementSection(s)}
      ${implementationGuideSection(s)}
      ${!hasRefine ? '<p class="tab-empty">Aucun raffinement effectué sur cette story.</p>' : ''}
    </div>

    <div class="tab-panel" data-panel="progress">
      <div class="m-row"><label>Notes</label><textarea id="me-notes" rows="2">${escHtml(s.notes || "")}</textarea></div>
      <div class="m-section">
        <h3>TDD</h3>
        <div class="m-row">
          <div class="m-inline-3 m-label-row">
            <label>Statut</label><label>Tests</label><label>Coverage</label>
          </div>
          <div class="m-inline-3">
            <select id="me-tdd-status">
              ${tddStatuses.map((st) => `<option ${(s.tdd && s.tdd.status) === st ? "selected" : ""} value="${st}">${st}</option>`).join("")}
            </select>
            <input type="number" id="me-tdd-tests" value="${(s.tdd && s.tdd.tests) || 0}">
            <input type="text" id="me-tdd-cov" value="${(s.tdd && s.tdd.coverage) || "0%"}">
          </div>
        </div>
        <div class="m-row"><label>Notes TDD</label><textarea id="me-tdd-notes" rows="1">${escHtml((s.tdd && s.tdd.notes) || "")}</textarea></div>
      </div>
      <div class="m-section">
        <h3>QA</h3>
        <div class="m-row">
          <div class="m-inline m-label-row">
            <label>Statut</label><label>AC couverts</label>
          </div>
          <div class="m-inline">
            <select id="me-qa-status">
              ${qaStatuses.map((st) => `<option ${(s.qa && s.qa.status) === st ? "selected" : ""} value="${st}">${st}</option>`).join("")}
            </select>
            <input type="text" id="me-qa-acs" value="${(s.qa && s.qa.ac_covered) || "0/0"}">
          </div>
        </div>
        <div class="m-row"><label>Notes QA</label><textarea id="me-qa-notes" rows="1">${escHtml((s.qa && s.qa.notes) || "")}</textarea></div>
      </div>
      <div class="m-section">
        <h3>SecOps CR — Commentaires</h3>
        <div class="m-row"><textarea id="me-secops-comments" rows="2" placeholder="Observations, risques, recommandations...">${escHtml((s.secops_report && s.secops_report.comments) || "")}</textarea></div>
      </div>
      ${simplifyReportSection(s)}
      <div class="m-section">
        <h3>Simplify — Notes manuelles</h3>
        <div class="m-row"><textarea id="me-simplify-comments" rows="2" placeholder="Simplifications appliquées, refactoring noté...">${escHtml(s.simplify_comments || "")}</textarea></div>
      </div>
    </div>

    <div class="tab-panel" data-panel="history">
      ${historySection(s)}
    </div>

    <div class="m-actions">
      <button class="btn-danger" id="me-delete"><i class="ti ti-trash"></i> Supprimer</button>
      <div style="flex:1"></div>
      <button class="btn-secondary" onclick="closeModal()">Annuler</button>
      <button class="btn-primary" id="me-save"><i class="ti ti-device-floppy"></i> Sauvegarder</button>
    </div>`;
  }

  function saveModal() {
    const storyId = document.getElementById("me-id").value;
    const acInputs = document.querySelectorAll("#me-acs .ac-item");
    const acs = Array.from(acInputs).map((item) => {
      const cb = item.querySelector(".ac-check");
      const txt = item.querySelector(".ac-text");
      return { id: parseInt(cb.dataset.acidx) + 1, text: txt.value, checked: cb.checked };
    });

    const stack = Array.from(document.querySelectorAll("#me-stack .stack-tag.active")).map((el) => el.dataset.stk);

    const data = {
      title: document.getElementById("me-title").value,
      priority: document.getElementById("me-prio").value,
      status: document.getElementById("me-status").value,
      stack,
      description: document.getElementById("me-desc").value,
      acceptance_criteria: acs,
      notes: document.getElementById("me-notes").value,
      tdd: {
        status: document.getElementById("me-tdd-status").value,
        tests: parseInt(document.getElementById("me-tdd-tests").value) || 0,
        coverage: document.getElementById("me-tdd-cov").value,
        notes: document.getElementById("me-tdd-notes").value,
      },
      qa: {
        status: document.getElementById("me-qa-status").value,
        ac_covered: document.getElementById("me-qa-acs").value,
        notes: document.getElementById("me-qa-notes").value,
      },
      secops_report: {
        comments: document.getElementById("me-secops-comments").value,
      },
      simplify_comments: document.getElementById("me-simplify-comments").value,
    };
    updateStory(storyId, data);
    closeModal();
  }

  // ── Auto-trigger toggle ──────────────────────────────────────────
  function initTriggerToggle() {
    const btn = document.getElementById("kb-trigger-toggle");
    if (!btn) return;
    const dot = document.getElementById("kb-trigger-dot");
    const update = () => {
      dot.className = `indicator ${autoTrigger ? "on" : "off"}`;
      btn.title = autoTrigger
        ? "Le glissement vers Raffinement déclenche /next-story dans OpenCode"
        : "Auto-trigger désactivé — OpenCode ne sera pas notifié";
    };
    update();
    btn.addEventListener("click", () => {
      autoTrigger = !autoTrigger;
      localStorage.setItem("kanban-auto-trigger", autoTrigger.toString());
      update();
      showToast(autoTrigger ? "Auto-trigger OpenCode activé" : "Auto-trigger OpenCode désactivé", "success");
    });
  }

  // ── Events ───────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    loadStories();
    initSortable();
    initTriggerToggle();
    checkOpenCode();
    setInterval(checkOpenCode, 30000);

    // SSE — live refresh when any story changes (drag, MCP, another tab)
    const sse = new EventSource("/api/events");
    sse.onmessage = (e) => {
      if (e.data === "refresh") loadStories();
    };
    sse.onerror = () => {
      // EventSource auto-reconnects on error
    };

    // Toggle view
    document.querySelector(".toggle-group").addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      document.querySelectorAll(".toggle-group button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      updateView();
    });

    // Search
    document.getElementById("kb-search").addEventListener("input", () => {
      renderKanban();
      renderList();
    });

    // Card click → modal (event delegation on kanban)
    document.getElementById("kb-kanban").addEventListener("click", (e) => {
      const card = e.target.closest(".card");
      if (card) openModal(card.dataset.id);
    });

    // List row click → modal
    document.getElementById("kb-list-body").addEventListener("click", (e) => {
      const row = e.target.closest("tr");
      if (row) openModal(row.dataset.id);
    });

    // Modal close
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("kb-modal").addEventListener("click", (e) => {
      if (e.target.classList.contains("modal-overlay")) closeModal();
    });

    // Modal save (event delegation because modal content is dynamic)
    document.getElementById("modal-body").addEventListener("click", (e) => {
      const btn = e.target.closest("#me-save");
      if (btn) saveModal();
    });

    // Modal delete
    document.getElementById("modal-body").addEventListener("click", (e) => {
      const btn = e.target.closest("#me-delete");
      if (btn) {
        const storyId = document.getElementById("me-id").value;
        if (confirm(`Supprimer ${storyId} ?`)) {
          deleteStory(storyId);
          closeModal();
        }
      }
    });

    // Stack tag toggle
    document.getElementById("modal-body").addEventListener("click", (e) => {
      const tag = e.target.closest(".stack-tag");
      if (tag) tag.classList.toggle("active");
    });

    // New story
    document.getElementById("kb-new").addEventListener("click", () => {
      const title = prompt("Titre de la nouvelle US :");
      if (title && title.trim()) {
        createStory({ title: title.trim(), priority: "P2", phase: 7 });
      }
    });

    // List sort
    document.querySelector(".list-view table thead").addEventListener("click", (e) => {
      const th = e.target.closest("th");
      if (!th || !th.dataset.sort) return;
      const key = th.dataset.sort;
      const asc = th.dataset.dir !== "asc";
      document.querySelectorAll(".list-view th").forEach((t) => delete t.dataset.dir);
      th.dataset.dir = asc ? "asc" : "desc";
      stories.sort((a, b) => {
        let va = a[key] || "";
        let vb = b[key] || "";
        if (key === "phase") { va = a.phase || 99; vb = b.phase || 99; }
        if (key === "tdd_status") { va = (a.tdd && a.tdd.status) || ""; vb = (b.tdd && b.tdd.status) || ""; }
        if (key === "qa_status") { va = (a.qa && a.qa.status) || ""; vb = (b.qa && b.qa.status) || ""; }
        if (typeof va === "string") {
          return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        }
        return asc ? va - vb : vb - va;
      });
      renderList();
    });
  });

  // ── Expose for inline handlers ───────────────────────────────────
  window.closeModal = closeModal;
})();
