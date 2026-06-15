// ── STATE ──────────────────────────────────────────────
const state = { invoices: [], auditRecords: [], stageChart: null, gaugeChart: null, trendChart: null, amountChart: null, successChart: null };

// ── SPLASH ─────────────────────────────────────────────
window.addEventListener('load', () => {
  setTimeout(() => {
    document.getElementById('splash').classList.add('hidden');
    init();
  }, 2000);
});

// ── INIT ───────────────────────────────────────────────
function init() {
  setupNav();
  setupRunAgent();
  setupFileUpload();
  setupFilters();
  loadDashboard();
  loadInvoices();
  loadAudit();
}

// ── NAVIGATION ─────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      const page = item.dataset.page;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      item.classList.add('active');
      document.getElementById(`page-${page}`).classList.add('active');

      const titles = {
        home:        ['Home',           'Welcome to Knot AI Platform'],
        dashboard:   ['Dashboard',      'Real-time enterprise recovery intelligence'],
        collections: ['Collections',    'Manage and action overdue invoices'],
        emaillab:    ['Email Lab',      'Preview and review AI-generated communications'],
        analytics:   ['Analytics',      'Collection velocity and recovery metrics'],
        audit:       ['Audit Trail',    'Complete immutable event log'],
        settings:    ['Settings',       'Configure models, rules and infrastructure']
      };
      const [title, sub] = titles[page] || ['—','—'];
      document.getElementById('page-title').textContent = title;
      document.getElementById('page-subtitle').textContent = sub;
      
      const topbarActions = document.getElementById('topbar-actions');
      if(topbarActions) {
        topbarActions.style.display = page === 'home' ? 'none' : 'flex';
      }

      if (page === 'analytics') buildAnalyticsCharts();
      if (page === 'emaillab')  buildEmailLab();
      if (page === 'audit')     loadAudit();
    });
  });
}

// ── DASHBOARD ──────────────────────────────────────────
async function loadDashboard() {
  const res = await fetch('/api/stats').then(r => r.json()).catch(() => ({}));
  document.getElementById('kpi-total').textContent  = res.total_invoices ?? '—';
  document.getElementById('kpi-sent').textContent   = res.emails_sent ?? '—';
  document.getElementById('kpi-legal').textContent  = res.legal_flags ?? '—';
  document.getElementById('kpi-value').textContent  = res.total_value_at_risk
    ? '₹' + res.total_value_at_risk.toLocaleString('en-IN', {maximumFractionDigits:0}) : '—';
  document.getElementById('gauge-label').textContent = (res.recovery_rate ?? 0) + '%';
  document.getElementById('queue-count').textContent = res.total_invoices ?? '—';

  buildStageChart(res.stage_distribution || {});
  buildGaugeChart(res.recovery_rate || 0);
  buildStageBars(res.stage_distribution || {}, res.total_invoices || 1);
  buildAlerts();
}

function buildStageChart(dist) {
  const ctx = document.getElementById('stageChart').getContext('2d');
  const labels = ['Stage 1\nFriendly','Stage 2\nFirm','Stage 3\nSerious','Stage 4\nFinal','Legal'];
  const values = [dist['1']||0, dist['2']||0, dist['3']||0, dist['4']||0, dist['5']||0];
  const colors = ['#2D6A4F','#C8922A','#C0392B','#922B21','#1A1814'];

  if (state.stageChart) state.stageChart.destroy();
  state.stageChart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 2, borderColor: '#111827' }] },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '72%',
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, color: '#5C5750', font: { family:'DM Sans',size:12 }, padding: 32 } } }
    }
  });
}

function buildGaugeChart(rate) {
  const ctx = document.getElementById('gaugeChart').getContext('2d');
  if (state.gaugeChart) state.gaugeChart.destroy();
  state.gaugeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [rate, 100 - rate],
        backgroundColor: ['#2D6A4F','#F4F1EB'],
        borderWidth: 0, circumference: 180, rotation: 270
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '78%', plugins: { legend: { display: false }, tooltip: { enabled: false } } }
  });
}

function buildStageBars(dist, total) {
  [1,2,3,4,5].forEach(s => {
    const v = dist[String(s)] || 0;
    const pct = total ? Math.round(v / total * 100) : 0;
    const fill = document.getElementById(`bar-s${s}`);
    const val  = document.getElementById(`bar-s${s}-val`);
    if (fill) { fill.style.width = '0%'; setTimeout(() => fill.style.width = pct + '%', 300); }
    if (val) val.textContent = v;
  });
}

async function buildAlerts() {
  const data = await fetch('/api/invoices').then(r=>r.json()).catch(()=>[]);
  const alerts = data.filter(r => r.stage >= 4 || r.send_status === 'GENERATION_FAILED').slice(0,5);
  const list = document.getElementById('alert-list');
  if (!alerts.length) { list.innerHTML = '<div class="alert-item" style="color:var(--muted)">No critical alerts.</div>'; return; }
  list.innerHTML = alerts.map(a => {
    const badgeClass = a.stage === 5 ? 'badge-legal' : a.stage === 4 ? 'badge-s4' : 'badge-s3';
    const label = a.stage === 5 ? 'LEGAL' : `STAGE ${a.stage}`;
    return `<div class="alert-item">
      <span class="alert-badge ${badgeClass}">${label}</span>
      <span class="alert-name">${a.client_name}</span>
      <span class="alert-amt">${a.days_overdue}d | ₹${Number(a.amount_due).toLocaleString('en-IN')}</span>
    </div>`;
  }).join('');
}

// ── INVOICE TABLE ──────────────────────────────────────
async function loadInvoices() {
  state.invoices = await fetch('/api/invoices').then(r=>r.json()).catch(()=>[]);
  renderInvoiceTable(state.invoices);
}

function renderInvoiceTable(rows) {
  const tbody = document.getElementById('invoice-tbody');
  if (!rows.length) { tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No invoices found. Run the agent first.</td></tr>'; return; }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><b>${r.invoice_no}</b></td>
      <td>${r.client_name}</td>
      <td>₹${Number(r.amount_due).toLocaleString('en-IN')}</td>
      <td><span style="color:${r.days_overdue>30?'#1A1814':r.days_overdue>21?'#922B21':r.days_overdue>14?'#C0392B':'#C8922A'}">${r.days_overdue}d</span></td>
      <td>${stageBadge(r.stage)}</td>
      <td>${statusPill(r.send_status)}</td>
      <td style="display:flex;gap:6px;">
        <button class="btn-ghost btn-sm" onclick="openEmailModal('${r.invoice_no}')" title="Preview"><i class="fa-solid fa-eye"></i></button>
        <button class="btn-ghost btn-sm" style="color:var(--green);border-color:rgba(16,185,129,0.3);" onclick="resolveInvoice('${r.invoice_no}')" title="Mark Resolved"><i class="fa-solid fa-check"></i></button>
      </td>
    </tr>`).join('');
}

async function resolveInvoice(invNo) {
  if(!confirm("Mark invoice " + invNo + " as resolved? This will clear it from the active queue.")) return;
  await fetch('/api/resolve/' + invNo, { method: 'POST' });
  await Promise.all([loadDashboard(), loadInvoices(), loadAudit()]);
}

function stageBadge(s) {
  const labels = {1:'Stage 1 · Friendly',2:'Stage 2 · Firm',3:'Stage 3 · Serious',4:'Stage 4 · Final',5:'⚖ Legal'};
  return `<span class="stage-badge s${s}">${labels[s]||'—'}</span>`;
}

function statusPill(st) {
  const map = {SENT:{cls:'sent',t:'Sent'},DRY_RUN_LOGGED:{cls:'dry',t:'Dry Run'},LEGAL_ESCALATION:{cls:'legal',t:'Legal'},GENERATION_FAILED:{cls:'failed',t:'Failed'}};
  const m = map[st] || {cls:'pending',t:st||'—'};
  return `<span class="status-pill ${m.cls}">${m.t}</span>`;
}

function setupFilters() {
  document.getElementById('filter-stage').addEventListener('change', applyFilters);
  document.getElementById('sort-by').addEventListener('change', applyFilters);
  document.getElementById('audit-filter').addEventListener('change', renderAuditTable);
  
  const resetBtn = document.getElementById('reset-filters-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      document.getElementById('filter-stage').value = '';
      document.getElementById('sort-by').value = 'days_overdue';
      applyFilters();
    });
  }
}

function applyFilters() {
  let rows = [...state.invoices];
  const stage = document.getElementById('filter-stage').value;
  const sort  = document.getElementById('sort-by').value;
  if (stage) rows = rows.filter(r => String(r.stage) === stage);
  rows.sort((a,b) => b[sort] - a[sort]);
  renderInvoiceTable(rows);
}

// ── AUDIT TRAIL ────────────────────────────────────────
async function loadAudit() {
  state.auditRecords = await fetch('/api/audit').then(r=>r.json()).catch(()=>[]);
  renderAuditTable();
}

function renderAuditTable() {
  const tbody  = document.getElementById('audit-tbody');
  const filter = document.getElementById('audit-filter')?.value || '';
  let rows = state.auditRecords;
  if (filter) rows = rows.filter(r => r.send_status === filter);
  if (!rows.length) { tbody.innerHTML = '<tr><td colspan="8" class="table-empty">No audit records.</td></tr>'; return; }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td style="color:var(--muted);font-size:.75rem">${r.timestamp?.slice(0,16).replace('T',' ')||'—'}</td>
      <td><b>${r.invoice_no}</b></td>
      <td>${r.client_name}</td>
      <td>₹${Number(r.amount_due).toLocaleString('en-IN')}</td>
      <td style="color:var(--muted)">${r.days_overdue}d</td>
      <td>${stageBadge(r.stage)}</td>
      <td>${statusPill(r.send_status)}</td>
      <td>${r.subject ? `<button class="btn-ghost btn-sm" onclick="openEmailModal('${r.invoice_no}')"><i class="fa-solid fa-eye"></i></button>` : '—'}</td>
    </tr>`).join('');
}

// ── EMAIL LAB ──────────────────────────────────────────
function buildEmailLab() {
  const list = document.getElementById('email-list');
  const emails = state.auditRecords.filter(r => r.subject);
  if (!emails.length) { list.innerHTML = '<div class="email-empty">Run the agent to generate communications.</div>'; return; }

  // Dedupe by invoice_no (latest entry)
  const seen = new Set();
  const unique = emails.filter(r => { if(seen.has(r.invoice_no)) return false; seen.add(r.invoice_no); return true; });

  list.innerHTML = unique.map(r => `
    <div class="email-list-item" onclick="selectEmailPreview('${r.invoice_no}')" data-inv="${r.invoice_no}">
      <div class="eli-top">
        <span class="eli-client">${r.client_name}</span>
        ${stageBadge(r.stage)}
      </div>
      <div class="eli-subject">${r.subject}</div>
    </div>`).join('');
}

async function selectEmailPreview(invNo) {
  document.querySelectorAll('.email-list-item').forEach(i => i.classList.toggle('active', i.dataset.inv === invNo));
  const r = state.auditRecords.find(x => x.invoice_no === invNo && x.subject);
  if (!r) return;

  const panel = document.getElementById('email-preview-panel');
  const chk = r.personalization_check || {};
  const checks = ['client_name_present','invoice_no_present','amount_present','due_date_present','days_overdue_present','payment_link_present'];
  const checkLabels = ['Client Name','Invoice No','Amount','Due Date','Days Overdue','Payment Link'];

  panel.innerHTML = `
    <div class="ep-header">
      <div class="ep-meta">
        <span>To: <b>${r.client_email||'—'}</b></span>
        <span>Stage: <b>${r.stage}</b></span>
        <span>Tone: <b>${r.tone_used||'—'}</b></span>
        <span>Days Overdue: <b style="color:var(--red)">${r.days_overdue}d</b></span>
        <span>Amount: <b>₹${Number(r.amount_due).toLocaleString('en-IN')}</b></span>
      </div>
      <div class="ep-subject">${r.subject}</div>
    </div>
    <div class="ep-body">${r.body||'No body content.'}</div>
    <div class="ep-check">
      ${checks.map((c,i) => {
        const pass = chk[c] !== false;
        return `<span class="check-item ${pass?'pass':'fail'}"><i class="fa-solid fa-${pass?'circle-check':'circle-xmark'}"></i>${checkLabels[i]}</span>`;
      }).join('')}
    </div>`;
}

// ── EMAIL MODAL ────────────────────────────────────────
async function openEmailModal(invNo) {
  const r = state.auditRecords.find(x => x.invoice_no === invNo);
  if (!r) { alert("No audit record found. Run the agent first to generate logs."); return; }
  document.getElementById('email-modal-invoice').textContent = r.invoice_no;
  document.getElementById('email-modal-meta').innerHTML = `
    <span>Client: <b>${r.client_name}</b></span>
    <span>Email: <b>${r.client_email}</b></span>
    <span>Stage: <b>${r.stage}</b></span>
    <span>Days Overdue: <b>${r.days_overdue}</b></span>
    <span>Amount: <b>₹${Number(r.amount_due).toLocaleString('en-IN')}</b></span>
    <span>Status: ${statusPill(r.send_status)}</span>`;
  document.getElementById('email-modal-subject').textContent = r.subject || 'No Subject';
  document.getElementById('email-modal-body').textContent = r.body || 'No email generated for this status.';
  document.getElementById('email-modal').classList.add('open');
}
document.getElementById('email-modal-close').addEventListener('click', () => document.getElementById('email-modal').classList.remove('open'));
document.getElementById('email-modal').addEventListener('click', e => { if(e.target===e.currentTarget) e.currentTarget.classList.remove('open'); });

// ── ANALYTICS CHARTS ───────────────────────────────────
function buildAnalyticsCharts() {
  const records = state.auditRecords;
  if (!records.length) return;

  // KPIs
  const total = records.length;
  const legal = records.filter(r => r.stage === 5).length;
  const avgDays = total ? Math.round(records.reduce((acc, r) => acc + (r.days_overdue || 0), 0) / total) : 0;
  
  const elTotal = document.getElementById('analytics-total');
  if (elTotal) elTotal.textContent = total;
  const elLegal = document.getElementById('analytics-legal');
  if (elLegal) elLegal.textContent = legal;
  const elAvg = document.getElementById('analytics-avg-days');
  if (elAvg) elAvg.textContent = avgDays + 'd';

  // Trend Chart
  const byDate = {};
  records.forEach(r => { const d = (r.timestamp||'').slice(0,10); byDate[d]=(byDate[d]||0)+1; });
  const dates  = Object.keys(byDate).sort();
  const counts = dates.map(d => byDate[d]);
  const ctx1 = document.getElementById('trendChart')?.getContext('2d');
  if (ctx1) {
    if (state.trendChart) state.trendChart.destroy();
    state.trendChart = new Chart(ctx1, {
      type:'line',
      data:{ labels:dates, datasets:[{label:'Events',data:counts,borderColor:'#C8922A',backgroundColor:'rgba(200,146,42,.10)',tension:.4,fill:true,pointRadius:4,pointBackgroundColor:'#C8922A'}]},
      options:{ responsive:true, maintainAspectRatio: false, plugins:{legend:{display:false}}, scales:{ x:{grid:{color:'rgba(26,24,20,.05)'},ticks:{color:'#5C5750',font:{family:'DM Sans'}}}, y:{grid:{color:'rgba(26,24,20,.05)'},ticks:{color:'#5C5750',font:{family:'DM Sans'}}} } }
    });
  }

  // Amount by Stage
  const stageAmts = {};
  records.forEach(r => { const s = r.stage; stageAmts[s] = (stageAmts[s]||0) + r.amount_due; });
  const ctx2 = document.getElementById('amountChart')?.getContext('2d');
  if (ctx2) {
    if (state.amountChart) state.amountChart.destroy();
    state.amountChart = new Chart(ctx2, {
      type:'bar',
      data:{ labels:['S1','S2','S3','S4','Legal'], datasets:[{data:[stageAmts[1]||0,stageAmts[2]||0,stageAmts[3]||0,stageAmts[4]||0,stageAmts[5]||0],backgroundColor:['#2D6A4F','#C8922A','#C0392B','#922B21','#1A1814'],borderRadius:6}]},
      options:{ responsive:true, maintainAspectRatio: false, plugins:{legend:{display:false}}, scales:{ x:{grid:{display:false},ticks:{color:'#5C5750',font:{family:'DM Sans'}}}, y:{grid:{color:'rgba(26,24,20,.05)'},ticks:{color:'#5C5750',font:{family:'DM Sans'}}} } }
    });
  }

  // Success Rate
  const statusCounts = {};
  records.forEach(r => { statusCounts[r.send_status]=(statusCounts[r.send_status]||0)+1; });
  const ctx3 = document.getElementById('successChart')?.getContext('2d');
  if (ctx3) {
    if (state.successChart) state.successChart.destroy();
    const labels = Object.keys(statusCounts).map(k => k.replace(/_/g,' '));
    const values = Object.values(statusCounts);
    const colors = Object.keys(statusCounts).map(k => {
      if(k === 'SENT') return '#2D6A4F';
      if(k === 'DRY_RUN_LOGGED') return '#C8922A';
      if(k === 'LEGAL_ESCALATION') return '#1A1814';
      if(k === 'RESOLVED') return '#9B9590';
      if(k === 'GENERATION_FAILED') return '#922B21';
      return '#5C5750';
    });
    state.successChart = new Chart(ctx3, {
      type:'pie',
      data:{ labels, datasets:[{data:values,backgroundColor:colors,borderWidth:2,borderColor:'#111827'}]},
      options:{ responsive:true, maintainAspectRatio: false, layout:{padding:{bottom:16}}, plugins:{legend:{position:'bottom',labels:{usePointStyle: true, color:'#5C5750',font:{family:'DM Sans',size:11},padding:32}}} }
    });
  }
}

// ── FILE UPLOAD & PREVIEW ──────────────────────────────
function setupFileUpload() {
  const zone  = document.getElementById('upload-zone');
  const input = document.getElementById('file-input');
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) {
      input.files = e.dataTransfer.files;
      handleFile(e.dataTransfer.files[0]);
    }
  });
  input.addEventListener('change', () => { if(input.files[0]) handleFile(input.files[0]); });

  document.getElementById('preview-btn').addEventListener('click', () => {
    if (input.files[0]) previewFile(input.files[0]);
  });
}

function handleFile(file) {
  document.querySelector('.upload-zone span').textContent = `📄 ${file.name} (${(file.size/1024).toFixed(1)} KB) — ready`;
}

async function previewFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/api/preview', { method: 'POST', body: fd }).then(r=>r.json()).catch(e=>({error:e}));
  if (res.error) { alert('Preview error: ' + res.error); return; }
  state.invoices = res;
  renderInvoiceTable(res);
}

// ── RUN AGENT ──────────────────────────────────────────
function setupRunAgent() {
  const handler = async () => {
    const modal    = document.getElementById('run-modal');
    const progress = document.getElementById('modal-progress');
    const status   = document.getElementById('modal-status');
    const result   = document.getElementById('modal-result');
    const closeBtn = document.getElementById('modal-close');
    const indicator = document.getElementById('agent-status-indicator');

    modal.classList.add('open');
    result.style.display = 'none';
    closeBtn.style.display = 'none';
    progress.style.width = '0%';
    status.textContent = 'Initializing agent…';
    indicator.innerHTML = '<span class="status-dot running"></span><span>Agent Running…</span>';
    const spinner = document.querySelector('#run-modal .spinner');
    if(spinner) spinner.style.display = 'block';

    // Animate progress
    let pct = 0;
    const steps = ['Loading invoices…','Calculating overdue stages…','Generating AI communications…','Logging to audit trail…','Finalizing results…'];
    let si = 0;
    const interval = setInterval(() => {
      pct = Math.min(pct + (100/(steps.length * 8)), 92);
      progress.style.width = pct + '%';
      if (pct > (si+1)*18 && si < steps.length-1) { si++; status.textContent = steps[si]; }
    }, 400);

    const fd = new FormData();
    const fileInput = document.getElementById('file-input');
    if (fileInput.files[0]) fd.append('file', fileInput.files[0]);
    fd.append('dry_run', document.getElementById('dry-run-toggle').checked ? 'true' : 'false');

    try {
      const res = await fetch('/api/run', { method: 'POST', body: fd }).then(r=>r.json());
      clearInterval(interval);
      progress.style.width = '100%';
      status.textContent = 'Complete!';
      if(spinner) spinner.style.display = 'none';

      if (res.success) {
        document.getElementById('res-total').textContent  = res.total || 0;
        document.getElementById('res-sent').textContent   = (res.sent||0) + (res.dry_run||0);
        document.getElementById('res-legal').textContent  = res.legal || 0;
        document.getElementById('res-failed').textContent = res.failed || 0;
        result.style.display = 'block';
      } else {
        status.textContent = 'Error: ' + (res.error || 'Unknown error');
      }
      
      // Auto-close after 4 seconds
      setTimeout(() => {
        if(document.getElementById('run-modal').classList.contains('open')) {
           document.getElementById('modal-close').click();
        }
      }, 4000);
      
    } catch(e) {
      clearInterval(interval);
      status.textContent = 'Connection error — is the server running?';
    }

    closeBtn.style.display = 'flex';
    indicator.innerHTML = '<span class="status-dot done"></span><span>Agent Done</span>';
    await Promise.all([loadDashboard(), loadInvoices(), loadAudit()]);
  };

  document.getElementById('run-agent-btn').addEventListener('click', handler);
  document.getElementById('run-agent-btn-collection').addEventListener('click', handler);

  document.getElementById('modal-close').addEventListener('click', () => {
    document.getElementById('run-modal').classList.remove('open');
    document.getElementById('agent-status-indicator').innerHTML = '<span class="status-dot idle"></span><span>Agent Idle</span>';
  });

  document.getElementById('run-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
  });
}

// ── SETTINGS ───────────────────────────────────────────
const tempRange = document.getElementById('temp-range');
const tempVal   = document.getElementById('temp-val');
if (tempRange) tempRange.addEventListener('input', () => { tempVal.textContent = tempRange.value; });

document.getElementById('clear-db-btn')?.addEventListener('click', async () => {
  if(!confirm("Are you sure you want to completely wipe the database? This cannot be undone.")) return;
  await fetch('/api/data/clear', { method: 'POST' });
  await Promise.all([loadDashboard(), loadInvoices(), loadAudit()]);
});

document.getElementById('clear-audit-btn')?.addEventListener('click', async () => {
  if(!confirm("Are you sure you want to clear the entire audit log? This will remove all records.")) return;
  await fetch('/api/data/clear', { method: 'POST' });
  await Promise.all([loadDashboard(), loadInvoices(), loadAudit()]);
});
