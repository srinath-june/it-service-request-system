// ==========================================================================
// IT Service Request Management System - Frontend SPA Controller
// ==========================================================================

let currentView = 'dashboard';
let users = [];
let itTeamUsers = [];
let categories = [];
let slaConfigs = [];
let currentTickets = [];
let currentTicketDetail = null;
let breachedFilterActive = false;

let priorityChart = null;
let categoryChart = null;
let statusChart = null;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', async () => {
  await loadMetadata();
  await loadDashboard();
});

// ==========================================================================
// Modal & Toast Helper (Works 100% reliably in all environments)
// ==========================================================================
function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.add('show');
  }
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.remove('show');
  }
}

// Close modal when clicking on backdrop
window.addEventListener('click', (e) => {
  if (e.target.classList.contains('custom-modal')) {
    e.target.classList.remove('show');
  }
});

function showToast(message, isError = false) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const item = document.createElement('div');
  item.className = `toast-item ${isError ? 'error' : 'success'}`;
  item.innerHTML = `
    <i class="fa-solid ${isError ? 'fa-circle-exclamation' : 'fa-circle-check'}"></i>
    <span>${message}</span>
  `;
  container.appendChild(item);
  setTimeout(() => {
    item.style.opacity = '0';
    item.style.transform = 'translateY(10px)';
    setTimeout(() => item.remove(), 300);
  }, 3500);
}

// ==========================================================================
// Metadata & Dropdown Initializer
// ==========================================================================
async function loadMetadata() {
  try {
    const [resUsers, resIT, resCats, resSLA] = await Promise.all([
      fetch('/api/v1/users').then(r => r.json()),
      fetch('/api/v1/users/it-team').then(r => r.json()),
      fetch('/api/v1/categories').then(r => r.json()),
      fetch('/api/v1/sla').then(r => r.json())
    ]);

    users = resUsers;
    itTeamUsers = resIT;
    categories = resCats;
    slaConfigs = resSLA;

    populateDropdowns();
  } catch (err) {
    console.error('Error loading metadata:', err);
    showToast('Failed to load system metadata', true);
  }
}

function populateDropdowns() {
  // Category dropdowns
  const catFilter = document.getElementById('filter-category');
  const createCat = document.getElementById('create-category');
  if (catFilter) catFilter.innerHTML = '<option value="">All Categories</option>';
  if (createCat) createCat.innerHTML = '';
  categories.forEach(c => {
    if (catFilter) catFilter.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    if (createCat) createCat.innerHTML += `<option value="${c.id}">${c.name}</option>`;
  });

  // Assignee dropdowns
  const assigneeFilter = document.getElementById('filter-assignee');
  const assignUser = document.getElementById('assign-user-id');
  const resolveUser = document.getElementById('resolve-user-id');
  if (assigneeFilter) assigneeFilter.innerHTML = '<option value="">All Assignees</option><option value="unassigned">Unassigned Only</option>';
  if (assignUser) assignUser.innerHTML = '';
  if (resolveUser) resolveUser.innerHTML = '';

  itTeamUsers.forEach(u => {
    if (assigneeFilter) assigneeFilter.innerHTML += `<option value="${u.id}">${u.full_name} (${u.role})</option>`;
    if (assignUser) assignUser.innerHTML += `<option value="${u.id}">${u.full_name} (${u.role} - ${u.department || 'IT'})</option>`;
    if (resolveUser) resolveUser.innerHTML += `<option value="${u.id}">${u.full_name} (${u.role})</option>`;
  });

  // Requester & Author dropdowns
  const createReq = document.getElementById('create-requester');
  const commentAuthor = document.getElementById('comment-author');
  const reopenActor = document.getElementById('reopen-actor-id');
  if (createReq) createReq.innerHTML = '';
  if (commentAuthor) commentAuthor.innerHTML = '';
  if (reopenActor) reopenActor.innerHTML = '';

  users.forEach(u => {
    if (createReq) createReq.innerHTML += `<option value="${u.id}">${u.full_name} (${u.department || u.role})</option>`;
    if (commentAuthor) commentAuthor.innerHTML += `<option value="${u.id}">${u.full_name}</option>`;
    if (reopenActor) reopenActor.innerHTML += `<option value="${u.id}">${u.full_name} (${u.role})</option>`;
  });
}

// ==========================================================================
// Navigation & View Controller
// ==========================================================================
function switchView(viewName) {
  currentView = viewName;
  document.getElementById('view-dashboard').style.display = viewName === 'dashboard' ? 'block' : 'none';
  document.getElementById('view-tickets').style.display = viewName === 'tickets' ? 'block' : 'none';
  document.getElementById('view-sla-config').style.display = viewName === 'sla-config' ? 'block' : 'none';

  document.querySelectorAll('.sidebar-nav .nav-link-item').forEach(el => el.classList.remove('active'));
  const activeNav = document.getElementById(`nav-${viewName}`);
  if (activeNav) activeNav.classList.add('active');

  const titles = {
    'dashboard': ['Management Dashboard', 'Real-time service desk metrics, SLA monitoring, and team workload.'],
    'tickets': ['Service Requests Queue', 'Filter, assign, update, resolve, and monitor IT service tickets.'],
    'sla-config': ['Runtime SLA Targets Configuration', 'Configure resolution hours per priority without modifying code.']
  };

  if (titles[viewName]) {
    document.getElementById('view-title').textContent = titles[viewName][0];
    document.getElementById('view-subtitle').textContent = titles[viewName][1];
  }

  refreshCurrentView();
}

function refreshCurrentView() {
  if (currentView === 'dashboard') loadDashboard();
  else if (currentView === 'tickets') loadTickets();
  else if (currentView === 'sla-config') loadSLAConfigView();
}

// ==========================================================================
// 1. Dashboard & Visualizations
// ==========================================================================
async function loadDashboard() {
  try {
    const res = await fetch('/api/v1/reports/dashboard');
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    const data = await res.json();

    document.getElementById('stat-total-open').textContent = data.total_open_requests;
    document.getElementById('stat-unassigned').textContent = data.unassigned_requests;
    document.getElementById('stat-sla-breached').textContent = data.sla_breached_open_requests;
    document.getElementById('stat-approaching').textContent = data.approaching_sla_breach_requests;
    document.getElementById('stat-critical-high').textContent = data.critical_open_requests + data.high_open_requests;
    document.getElementById('stat-critical').textContent = data.critical_open_requests;
    document.getElementById('stat-high').textContent = data.high_open_requests;
    document.getElementById('stat-compliance-rate').textContent = `${data.sla_compliance_rate_percent}%`;
    document.getElementById('stat-total-resolved').textContent = `${data.total_resolved_requests + data.total_closed_requests}`;

    // Render visual graphs or fallback HTML bars
    renderPriorityVisuals(data.by_priority);
    renderCategoryVisuals(data.by_category);
    renderStatusVisuals(data.by_status);

    // Render Workload table
    renderAssigneeWorkload(data.by_assignee);
  } catch (err) {
    console.error('Error loading dashboard:', err);
    showToast(err.message, true);
  }
}

function renderPriorityVisuals(items) {
  const labels = items.map(i => i.label);
  const counts = items.map(i => i.count);
  const colors = { 'CRITICAL': '#dc2626', 'HIGH': '#d97706', 'MEDIUM': '#2563eb', 'LOW': '#16a34a' };

  if (typeof Chart !== 'undefined') {
    try {
      const ctx = document.getElementById('chartPriority').getContext('2d');
      if (priorityChart) priorityChart.destroy();
      priorityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{ data: counts, backgroundColor: labels.map(l => colors[l] || '#64748b') }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } }
        }
      });
      return;
    } catch (e) {
      console.warn('ChartJS render failed, falling back to HTML bars:', e);
    }
  }

  // Pure HTML/CSS Fallback
  document.getElementById('chartPriority').style.display = 'none';
  const fallback = document.getElementById('fallbackPriorityList');
  fallback.style.display = 'flex';
  fallback.innerHTML = '';
  const total = counts.reduce((a, b) => a + b, 0) || 1;
  items.forEach(i => {
    const pct = Math.round((i.count / total) * 100);
    fallback.innerHTML += `
      <div class="stat-bar-row">
        <div class="stat-bar-label"><span>${i.label}</span><span>${i.count} (${pct}%)</span></div>
        <div class="stat-bar-track">
          <div class="stat-bar-fill" style="width: ${pct}%; background-color: ${colors[i.label] || '#64748b'};"></div>
        </div>
      </div>
    `;
  });
}

function renderCategoryVisuals(items) {
  const labels = items.map(i => i.label);
  const counts = items.map(i => i.count);

  if (typeof Chart !== 'undefined') {
    try {
      const ctx = document.getElementById('chartCategory').getContext('2d');
      if (categoryChart) categoryChart.destroy();
      categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{ label: 'Requests', data: counts, backgroundColor: '#3b82f6', borderRadius: 4 }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
          plugins: { legend: { display: false } }
        }
      });
      return;
    } catch (e) {
      console.warn('ChartJS render failed, falling back to HTML bars:', e);
    }
  }

  // Pure HTML/CSS Fallback
  document.getElementById('chartCategory').style.display = 'none';
  const fallback = document.getElementById('fallbackCategoryList');
  fallback.style.display = 'flex';
  fallback.innerHTML = '';
  const max = Math.max(...counts, 1);
  items.forEach(i => {
    const pct = Math.round((i.count / max) * 100);
    fallback.innerHTML += `
      <div class="stat-bar-row">
        <div class="stat-bar-label"><span>${i.label}</span><span>${i.count}</span></div>
        <div class="stat-bar-track">
          <div class="stat-bar-fill" style="width: ${pct}%; background-color: #3b82f6;"></div>
        </div>
      </div>
    `;
  });
}

function renderStatusVisuals(items) {
  const labels = items.map(i => i.label);
  const counts = items.map(i => i.count);
  const colors = {
    'NEW': '#2563eb', 'ASSIGNED': '#d97706', 'IN_PROGRESS': '#0d9488',
    'ON_HOLD': '#9333ea', 'RESOLVED': '#16a34a', 'CLOSED': '#64748b'
  };

  if (typeof Chart !== 'undefined') {
    try {
      const ctx = document.getElementById('chartStatus').getContext('2d');
      if (statusChart) statusChart.destroy();
      statusChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: labels,
          datasets: [{ data: counts, backgroundColor: labels.map(l => colors[l] || '#cbd5e1') }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } }
        }
      });
      return;
    } catch (e) {
      console.warn('ChartJS render failed, falling back to HTML bars:', e);
    }
  }

  // Pure HTML/CSS Fallback
  document.getElementById('chartStatus').style.display = 'none';
  const fallback = document.getElementById('fallbackStatusList');
  fallback.style.display = 'flex';
  fallback.innerHTML = '';
  const total = counts.reduce((a, b) => a + b, 0) || 1;
  items.forEach(i => {
    const pct = Math.round((i.count / total) * 100);
    fallback.innerHTML += `
      <div class="stat-bar-row">
        <div class="stat-bar-label"><span>${i.label}</span><span>${i.count} (${pct}%)</span></div>
        <div class="stat-bar-track">
          <div class="stat-bar-fill" style="width: ${pct}%; background-color: ${colors[i.label] || '#cbd5e1'};"></div>
        </div>
      </div>
    `;
  });
}

function renderAssigneeWorkload(items) {
  const tbody = document.getElementById('assignee-workload-tbody');
  tbody.innerHTML = '';
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No active team records.</td></tr>';
    return;
  }
  items.forEach(a => {
    tbody.innerHTML += `
      <tr>
        <td class="fw-semibold">
          <div class="d-flex align-items-center gap-2">
            <div class="bg-light text-primary rounded-circle d-flex align-items-center justify-content-center" style="width:28px; height:28px;">
              <i class="fa-solid fa-user small"></i>
            </div>
            <span>${a.name}</span>
          </div>
        </td>
        <td class="text-center"><span class="badge bg-primary rounded-pill px-3">${a.open_tickets}</span></td>
        <td class="text-center"><span class="badge bg-success rounded-pill px-3">${a.resolved_tickets}</span></td>
        <td class="text-center">
          ${a.sla_breached_tickets > 0
            ? `<span class="badge bg-danger rounded-pill px-3">${a.sla_breached_tickets}</span>`
            : `<span class="badge bg-light text-muted rounded-pill px-3">0</span>`
          }
        </td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary" onclick="filterByAssignee('${a.user_id === null ? 'unassigned' : a.user_id}')">
            View Tickets
          </button>
        </td>
      </tr>
    `;
  });
}

function filterByAssignee(assigneeId) {
  switchView('tickets');
  document.getElementById('filter-assignee').value = assigneeId;
  loadTickets();
}

// ==========================================================================
// 2. Service Requests Table & Queue
// ==========================================================================
async function loadTickets() {
  try {
    const search = document.getElementById('filter-search').value.trim();
    const status = document.getElementById('filter-status').value;
    const priority = document.getElementById('filter-priority').value;
    const categoryId = document.getElementById('filter-category').value;
    const assigneeVal = document.getElementById('filter-assignee').value;

    let url = '/api/v1/requests?';
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (status) url += `status=${encodeURIComponent(status)}&`;
    if (priority) url += `priority=${encodeURIComponent(priority)}&`;
    if (categoryId) url += `category_id=${encodeURIComponent(categoryId)}&`;
    if (assigneeVal === 'unassigned') url += `unassigned_only=true&`;
    else if (assigneeVal) url += `assigned_to_id=${encodeURIComponent(assigneeVal)}&`;
    if (breachedFilterActive) url += `sla_breached_only=true&`;

    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load tickets');
    currentTickets = await res.json();
    renderTicketsTable(currentTickets);
  } catch (err) {
    console.error('Error loading tickets:', err);
    showToast(err.message, true);
  }
}

function renderTicketsTable(tickets) {
  const tbody = document.getElementById('tickets-tbody');
  tbody.innerHTML = '';
  if (!tickets || tickets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-5">No service requests found matching your filters.</td></tr>';
    return;
  }

  tickets.forEach(t => {
    const slaBadge = formatSLABadge(t);
    const assigneeName = t.assigned_to ? t.assigned_to.full_name : '<span class="text-danger fw-semibold"><i class="fa-solid fa-circle-exclamation me-1"></i>Unassigned</span>';
    const requesterName = t.requester ? t.requester.full_name : 'Unknown';
    const categoryName = t.category ? t.category.name : 'General';

    tbody.innerHTML += `
      <tr>
        <td><strong class="text-primary font-monospace">${t.request_number}</strong></td>
        <td>
          <div class="fw-semibold text-truncate" style="max-width: 250px;" title="${t.subject}">${t.subject}</div>
          <small class="text-muted"><i class="fa-solid fa-tag me-1 text-muted"></i>${categoryName}</small>
        </td>
        <td><span class="badge badge-priority-${t.priority}">${t.priority}</span></td>
        <td><span class="badge badge-status-${t.status}">${t.status.replace('_', ' ')}</span></td>
        <td><small class="text-muted">${requesterName}</small></td>
        <td><small>${assigneeName}</small></td>
        <td>${slaBadge}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary" onclick="viewTicketDetails(${t.id})">
            <i class="fa-solid fa-eye me-1"></i> View
          </button>
        </td>
      </tr>
    `;
  });
}

function formatSLABadge(ticket) {
  const status = ticket.sla_status;
  const remainingSec = ticket.sla_remaining_seconds;
  const isBreached = ticket.is_sla_breached;
  const progress = Math.min(100, Math.round(ticket.sla_progress_percent));

  let timeText = '';
  if (['RESOLVED_WITHIN_SLA', 'RESOLVED_BREACHED'].includes(status)) {
    timeText = isBreached ? 'Breached on Resolution' : 'Resolved in SLA';
  } else if (isBreached) {
    timeText = 'Overdue / Breached';
  } else {
    const hrs = Math.floor(remainingSec / 3600);
    const mins = Math.floor((remainingSec % 3600) / 60);
    timeText = `${hrs}h ${mins}m left`;
  }

  let badgeClass = `sla-badge-${status}`;
  return `
    <div>
      <span class="${badgeClass}">
        <i class="fa-solid fa-clock"></i> ${timeText}
      </span>
      <div class="progress-sla">
        <div class="progress-sla-fill ${isBreached ? 'bg-danger' : (progress > 75 ? 'bg-warning' : 'bg-success')}" style="width: ${progress}%;"></div>
      </div>
    </div>
  `;
}

function handleFilterChange() {
  loadTickets();
}

function toggleBreachedFilter() {
  breachedFilterActive = !breachedFilterActive;
  const btn = document.getElementById('btn-breached-filter');
  if (breachedFilterActive) {
    btn.className = 'btn btn-danger btn-sm w-100';
  } else {
    btn.className = 'btn btn-outline-danger btn-sm w-100';
  }
  loadTickets();
}

function resetFilters() {
  document.getElementById('filter-search').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-priority').value = '';
  document.getElementById('filter-category').value = '';
  document.getElementById('filter-assignee').value = '';
  breachedFilterActive = false;
  document.getElementById('btn-breached-filter').className = 'btn btn-outline-danger btn-sm w-100';
  loadTickets();
}

// ==========================================================================
// 3. Ticket Detail Modal & Lifecycle Workflows
// ==========================================================================
async function viewTicketDetails(ticketId) {
  try {
    const res = await fetch(`/api/v1/requests/${ticketId}`);
    if (!res.ok) throw new Error('Failed to load ticket details');
    currentTicketDetail = await res.json();

    const t = currentTicketDetail;

    document.getElementById('detail-ticket-number').textContent = t.request_number;
    document.getElementById('detail-subject').textContent = t.subject;
    document.getElementById('detail-description').textContent = t.description;
    document.getElementById('detail-category').textContent = t.category ? t.category.name : 'Unknown';
    document.getElementById('detail-requester').textContent = t.requester ? `${t.requester.full_name} (${t.requester.department || 'Employee'})` : 'Unknown';
    document.getElementById('detail-created').textContent = new Date(t.created_at).toLocaleString();

    // Priority & Status Badges
    const pBadge = document.getElementById('detail-priority-badge');
    pBadge.className = `badge badge-priority-${t.priority}`;
    pBadge.textContent = t.priority;

    const sBadge = document.getElementById('detail-status-badge');
    sBadge.className = `badge badge-status-${t.status}`;
    sBadge.textContent = t.status.replace('_', ' ');

    const slaBadge = document.getElementById('detail-sla-badge');
    slaBadge.className = `sla-badge-${t.sla_status}`;
    slaBadge.textContent = t.sla_status.replace(/_/g, ' ');

    // SLA Countdown & Progress Bar
    const progress = Math.min(100, Math.round(t.sla_progress_percent));
    const pBar = document.getElementById('detail-sla-progress-bar');
    pBar.style.width = `${progress}%`;
    pBar.className = `progress-sla-fill ${t.is_sla_breached ? 'bg-danger' : (progress > 75 ? 'bg-warning' : 'bg-success')}`;

    const hrs = Math.floor(t.sla_remaining_seconds / 3600);
    const mins = Math.floor((t.sla_remaining_seconds % 3600) / 60);
    document.getElementById('detail-sla-countdown').textContent = t.is_sla_breached ? 'SLA Breached' : `Remaining: ${hrs}h ${mins}m`;
    document.getElementById('detail-sla-target').textContent = `${t.sla_target_hours} hours`;
    document.getElementById('detail-sla-due').textContent = new Date(t.sla_due_at).toLocaleString();
    document.getElementById('detail-on-hold-time').textContent = `${Math.round(t.total_on_hold_seconds / 60)} mins`;

    // Resolution Details Box
    const resBox = document.getElementById('detail-resolution-box');
    if (t.resolution_details) {
      resBox.style.display = 'block';
      document.getElementById('detail-resolution-text').textContent = t.resolution_details;
      const resolverName = t.resolved_by ? t.resolved_by.full_name : 'IT Staff';
      document.getElementById('detail-resolved-by').textContent = `Resolved by ${resolverName} on ${new Date(t.resolved_at || t.updated_at).toLocaleString()}`;
    } else {
      resBox.style.display = 'none';
    }

    // Dynamic Action Buttons
    renderActionButtons(t);

    // Comments & History
    renderComments(t.comments || []);
    renderHistory(t.history || []);

    openModal('modal-ticket-details');
  } catch (err) {
    console.error('Error fetching ticket details:', err);
    showToast(err.message, true);
  }
}

function renderActionButtons(t) {
  const container = document.getElementById('detail-action-buttons');
  container.innerHTML = '';

  // 1. Assign / Reassign Button
  if (t.status !== 'CLOSED') {
    container.innerHTML += `
      <button class="btn btn-outline-primary btn-sm" onclick="openAssignModal(${t.id})">
        <i class="fa-solid fa-user-plus me-1"></i> ${t.assigned_to_id ? 'Reassign' : 'Assign IT Staff'}
      </button>
    `;
  }

  // 2. Change Status Button
  if (t.status !== 'CLOSED' && t.status !== 'RESOLVED') {
    container.innerHTML += `
      <button class="btn btn-outline-secondary btn-sm" onclick="openStatusModal(${t.id}, '${t.status}')">
        <i class="fa-solid fa-arrows-spin me-1"></i> Change Status
      </button>
    `;
  }

  // 3. Resolve Button
  if (['ASSIGNED', 'IN_PROGRESS', 'ON_HOLD'].includes(t.status)) {
    container.innerHTML += `
      <button class="btn btn-success btn-sm" onclick="openResolveModal(${t.id})">
        <i class="fa-solid fa-check-circle me-1"></i> Resolve Request
      </button>
    `;
  }

  // 4. Close Button
  if (t.status === 'RESOLVED') {
    container.innerHTML += `
      <button class="btn btn-dark btn-sm" onclick="openCloseModal(${t.id})">
        <i class="fa-solid fa-lock me-1"></i> Close Request
      </button>
    `;
  }

  // 5. Reopen Button
  if (['RESOLVED', 'CLOSED'].includes(t.status)) {
    container.innerHTML += `
      <button class="btn btn-warning btn-sm" onclick="openReopenModal(${t.id})">
        <i class="fa-solid fa-rotate-left me-1"></i> Reopen Ticket
      </button>
    `;
  }
}

function switchDetailTab(tab) {
  const pComm = document.getElementById('panel-comments');
  const pHist = document.getElementById('panel-history');
  const bComm = document.getElementById('btn-tab-comments');
  const bHist = document.getElementById('btn-tab-history');

  if (tab === 'comments') {
    pComm.style.display = 'block';
    pHist.style.display = 'none';
    bComm.className = 'btn btn-sm btn-link text-decoration-none fw-bold text-dark border-bottom border-primary border-2 pb-2';
    bHist.className = 'btn btn-sm btn-link text-decoration-none text-muted pb-2';
  } else {
    pComm.style.display = 'none';
    pHist.style.display = 'block';
    bHist.className = 'btn btn-sm btn-link text-decoration-none fw-bold text-dark border-bottom border-primary border-2 pb-2';
    bComm.className = 'btn btn-sm btn-link text-decoration-none text-muted pb-2';
  }
}

function renderComments(comments) {
  const container = document.getElementById('comments-container');
  document.getElementById('comment-count').textContent = comments.length;
  container.innerHTML = '';
  if (!comments || comments.length === 0) {
    container.innerHTML = '<div class="text-center text-muted small py-4">No comments or work notes yet.</div>';
    return;
  }
  comments.forEach(c => {
    const authorName = c.author ? c.author.full_name : 'Staff';
    container.innerHTML += `
      <div class="p-2 mb-2 rounded border ${c.is_internal ? 'bg-warning-subtle border-warning' : 'bg-light'}">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <span class="fw-bold small">${authorName} ${c.is_internal ? '<span class="badge bg-warning text-dark ms-1" style="font-size:0.65rem;">Internal Note</span>' : ''}</span>
          <span class="text-muted" style="font-size:0.75rem;">${new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        <div class="small">${c.comment}</div>
      </div>
    `;
  });
}

function renderHistory(history) {
  const container = document.getElementById('history-container');
  container.innerHTML = '';
  if (!history || history.length === 0) {
    container.innerHTML = '<div class="text-muted small">No history logged.</div>';
    return;
  }
  history.forEach(h => {
    const actorName = h.actor ? h.actor.full_name : 'System';
    container.innerHTML += `
      <div class="audit-item">
        <div class="fw-bold small text-primary">${h.action_type.replace('_', ' ')}</div>
        <div class="small text-muted mb-1">${new Date(h.created_at).toLocaleString()} by <strong>${actorName}</strong></div>
        <div class="small text-dark">${h.remarks || (h.old_value ? `${h.old_value} → ${h.new_value}` : h.new_value)}</div>
      </div>
    `;
  });
}

// ==========================================================================
// 4. Modal Operations & Form Submissions
// ==========================================================================
function openCreateModal() {
  document.getElementById('form-create-request').reset();
  openModal('modal-create-request');
}

async function submitCreateRequest(e) {
  e.preventDefault();
  const payload = {
    requester_id: parseInt(document.getElementById('create-requester').value),
    category_id: parseInt(document.getElementById('create-category').value),
    priority: document.getElementById('create-priority').value,
    subject: document.getElementById('create-subject').value.trim(),
    description: document.getElementById('create-description').value.trim()
  };

  try {
    const res = await fetch('/api/v1/requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Failed to create request');
    }
    const created = await res.json();
    closeModal('modal-create-request');
    showToast(`Service Request ${created.request_number} created successfully!`);
    switchView('tickets');
  } catch (err) {
    showToast(err.message, true);
  }
}

function openAssignModal(ticketId) {
  document.getElementById('assign-request-id').value = ticketId;
  document.getElementById('assign-remarks').value = '';
  openModal('modal-assign');
}

async function submitAssign(e) {
  e.preventDefault();
  const ticketId = document.getElementById('assign-request-id').value;
  const payload = {
    assigned_to_id: parseInt(document.getElementById('assign-user-id').value),
    actor_id: 3, // Marcus Vance
    remarks: document.getElementById('assign-remarks').value.trim() || undefined
  };

  try {
    const res = await fetch(`/api/v1/requests/${ticketId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Assignment failed');
    }
    closeModal('modal-assign');
    showToast('Ticket assigned successfully!');
    if (document.getElementById('modal-ticket-details').classList.contains('show')) {
      viewTicketDetails(ticketId);
    } else {
      refreshCurrentView();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

function openStatusModal(ticketId, currentStatus) {
  document.getElementById('status-request-id').value = ticketId;
  document.getElementById('status-remarks').value = '';
  const select = document.getElementById('status-new-value');
  select.innerHTML = '';

  const validTransitions = {
    'NEW': ['ASSIGNED', 'IN_PROGRESS', 'ON_HOLD'],
    'ASSIGNED': ['IN_PROGRESS', 'ON_HOLD'],
    'IN_PROGRESS': ['ON_HOLD'],
    'ON_HOLD': ['IN_PROGRESS', 'ASSIGNED']
  };

  const allowed = validTransitions[currentStatus] || [];
  allowed.forEach(s => {
    select.innerHTML += `<option value="${s}">${s.replace('_', ' ')}</option>`;
  });

  document.getElementById('status-transition-hint').textContent = `Allowed transitions: ${allowed.join(', ')}`;
  openModal('modal-status');
}

async function submitStatusUpdate(e) {
  e.preventDefault();
  const ticketId = document.getElementById('status-request-id').value;
  const payload = {
    new_status: document.getElementById('status-new-value').value,
    actor_id: 3,
    remarks: document.getElementById('status-remarks').value.trim() || undefined
  };

  try {
    const res = await fetch(`/api/v1/requests/${ticketId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Status transition failed');
    }
    closeModal('modal-status');
    showToast('Status updated successfully!');
    if (document.getElementById('modal-ticket-details').classList.contains('show')) {
      viewTicketDetails(ticketId);
    } else {
      refreshCurrentView();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

function openResolveModal(ticketId) {
  document.getElementById('resolve-request-id').value = ticketId;
  document.getElementById('resolve-details').value = '';
  openModal('modal-resolve');
}

async function submitResolve(e) {
  e.preventDefault();
  const ticketId = document.getElementById('resolve-request-id').value;
  const payload = {
    resolved_by_id: parseInt(document.getElementById('resolve-user-id').value),
    resolution_details: document.getElementById('resolve-details').value.trim()
  };

  try {
    const res = await fetch(`/api/v1/requests/${ticketId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Resolution failed');
    }
    closeModal('modal-resolve');
    showToast('Service Request marked as RESOLVED!');
    if (document.getElementById('modal-ticket-details').classList.contains('show')) {
      viewTicketDetails(ticketId);
    } else {
      refreshCurrentView();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

function openCloseModal(ticketId) {
  document.getElementById('close-request-id').value = ticketId;
  document.getElementById('close-remarks').value = '';
  openModal('modal-close');
}

async function submitClose(e) {
  e.preventDefault();
  const ticketId = document.getElementById('close-request-id').value;
  const payload = {
    actor_id: 3,
    remarks: document.getElementById('close-remarks').value.trim() || undefined
  };

  try {
    const res = await fetch(`/api/v1/requests/${ticketId}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Closure failed');
    }
    closeModal('modal-close');
    showToast('Service Request closed.');
    if (document.getElementById('modal-ticket-details').classList.contains('show')) {
      viewTicketDetails(ticketId);
    } else {
      refreshCurrentView();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

function openReopenModal(ticketId) {
  document.getElementById('reopen-request-id').value = ticketId;
  document.getElementById('reopen-reason').value = '';
  openModal('modal-reopen');
}

async function submitReopen(e) {
  e.preventDefault();
  const ticketId = document.getElementById('reopen-request-id').value;
  const payload = {
    actor_id: parseInt(document.getElementById('reopen-actor-id').value),
    reason: document.getElementById('reopen-reason').value.trim()
  };

  try {
    const res = await fetch(`/api/v1/requests/${ticketId}/reopen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Reopen failed');
    }
    closeModal('modal-reopen');
    showToast('Service Request reopened!');
    if (document.getElementById('modal-ticket-details').classList.contains('show')) {
      viewTicketDetails(ticketId);
    } else {
      refreshCurrentView();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

async function submitComment(e) {
  e.preventDefault();
  if (!currentTicketDetail) return;
  const payload = {
    author_id: parseInt(document.getElementById('comment-author').value),
    comment: document.getElementById('comment-text').value.trim(),
    is_internal: document.getElementById('comment-internal').checked
  };

  try {
    const res = await fetch(`/api/v1/requests/${currentTicketDetail.id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to add comment');
    }
    document.getElementById('comment-text').value = '';
    viewTicketDetails(currentTicketDetail.id);
  } catch (err) {
    showToast(err.message, true);
  }
}

// ==========================================================================
// 5. SLA Configuration View
// ==========================================================================
async function loadSLAConfigView() {
  try {
    const res = await fetch('/api/v1/sla');
    if (!res.ok) throw new Error('Failed to load SLA configs');
    slaConfigs = await res.json();

    const tbody = document.getElementById('sla-config-tbody');
    tbody.innerHTML = '';
    slaConfigs.forEach(s => {
      tbody.innerHTML += `
        <tr>
          <td><span class="badge badge-priority-${s.priority} fs-6">${s.priority}</span></td>
          <td>
            <div class="input-group input-group-sm" style="max-width: 140px;">
              <input type="number" step="0.5" min="0.5" id="sla-val-${s.priority}" class="form-control" value="${s.resolution_sla_hours}">
              <span class="input-group-text">hrs</span>
            </div>
          </td>
          <td>
            <div class="input-group input-group-sm" style="max-width: 140px;">
              <input type="number" step="0.5" min="0.1" id="sla-resp-${s.priority}" class="form-control" value="${s.response_sla_hours}">
              <span class="input-group-text">hrs</span>
            </div>
          </td>
          <td><span class="badge bg-success">Active</span></td>
          <td class="text-end">
            <button class="btn btn-sm btn-primary" onclick="saveSLAConfig('${s.priority}')">
              <i class="fa-solid fa-floppy-disk me-1"></i> Save
            </button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    showToast(err.message, true);
  }
}

async function saveSLAConfig(priority) {
  const resHours = parseFloat(document.getElementById(`sla-val-${priority}`).value);
  const respHours = parseFloat(document.getElementById(`sla-resp-${priority}`).value);

  if (isNaN(resHours) || resHours <= 0) {
    showToast('Invalid resolution hours value', true);
    return;
  }

  try {
    const res = await fetch(`/api/v1/sla/${priority}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution_sla_hours: resHours, response_sla_hours: respHours })
    });
    if (!res.ok) throw new Error('Failed to save SLA configuration');
    showToast(`SLA for priority ${priority} updated to ${resHours} hours!`);
    loadMetadata();
  } catch (err) {
    showToast(err.message, true);
  }
}
