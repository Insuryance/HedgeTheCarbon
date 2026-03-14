/* ═══════════════════════════════════════════════════════════════
   CarbonIQ — Frontend Application Logic
   API client + dynamic rendering for all dashboard sections
   ═══════════════════════════════════════════════════════════════ */

const API = '';
let chartInstances = {};

// ─── Navigation ─────────────────────────────────────────────
function navigateTo(section) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    document.getElementById(`section-${section}`).classList.add('active');
    document.querySelector(`.nav-item[data-section="${section}"]`).classList.add('active');

    // Load section data
    const loaders = {
        dashboard: loadDashboard,
        projects: loadProjects,
        risk: loadRiskExplorer,
        quant: loadQuantEngine,
        arbitrage: loadArbitrage,
        crawler: loadCrawlerHistory,
        cdc: loadCDCLog,
        docs: () => {},
    };
    if (loaders[section]) loaders[section]();
}

// ─── Utility ────────────────────────────────────────────────
function fmt(n) {
    if (n === null || n === undefined) return '—';
    if (typeof n === 'number') {
        if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(1) + 'B';
        if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
        if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
        return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return n;
}

function $(n) { return (typeof n === 'number') ? `$${fmt(n)}` : n; }

function riskBadge(rating) {
    const cl = { LOW: 'badge-low', MEDIUM: 'badge-medium', HIGH: 'badge-high', CRITICAL: 'badge-critical' };
    return `<span class="badge ${cl[rating] || 'badge-medium'}">${rating}</span>`;
}

function signalBadge(signal) {
    if (signal.includes('BUY')) return `<span class="badge badge-buy">${signal}</span>`;
    if (signal.includes('SELL')) return `<span class="badge badge-sell">${signal}</span>`;
    return `<span class="badge badge-hold">${signal}</span>`;
}

function registryBadge(reg) {
    const map = { 'Verra': 'badge-verra', 'Gold Standard': 'badge-gs', 'ACR': 'badge-acr', 'CAR': 'badge-car' };
    return `<span class="badge ${map[reg] || 'badge-verra'}">${reg}</span>`;
}

function alphaSpan(val) {
    const cls = val >= 0 ? 'alpha-positive' : 'alpha-negative';
    const sign = val >= 0 ? '+' : '';
    return `<span class="${cls}">${sign}${val.toFixed(2)}%</span>`;
}

function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }
}

async function api(path) {
    try {
        const res = await fetch(API + path);
        if (!res.ok) throw new Error(`API ${res.status}`);
        return await res.json();
    } catch (e) {
        console.error('API error:', path, e);
        return null;
    }
}

async function apiPost(path, body = {}) {
    try {
        const res = await fetch(API + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        return await res.json();
    } catch (e) {
        console.error('API error:', path, e);
        return null;
    }
}

// ─── Dashboard ──────────────────────────────────────────────
async function loadDashboard() {
    const data = await api('/api/analytics/summary');
    if (!data) return;

    document.getElementById('dashboard-stats').innerHTML = `
        <div class="stat-card green">
            <div class="stat-label">Total Projects</div>
            <div class="stat-value">${data.total_projects}</div>
            <div class="stat-sub">Across ${Object.keys(data.registry_breakdown).length} registries</div>
        </div>
        <div class="stat-card blue">
            <div class="stat-label">Credits Issued</div>
            <div class="stat-value">${fmt(data.total_credits_issued)}</div>
            <div class="stat-sub">tCO₂e total issuance</div>
        </div>
        <div class="stat-card amber">
            <div class="stat-label">Credits Retired</div>
            <div class="stat-value">${fmt(data.total_credits_retired)}</div>
            <div class="stat-sub">${((data.total_credits_retired / Math.max(1, data.total_credits_issued)) * 100).toFixed(1)}% retirement rate</div>
        </div>
        <div class="stat-card purple">
            <div class="stat-label">Market Value</div>
            <div class="stat-value">${$(data.total_market_value)}</div>
            <div class="stat-sub">Avg ${$(data.avg_price_per_tonne)}/tonne</div>
        </div>
    `;

    // Registry chart
    destroyChart('chart-registry');
    const regCtx = document.getElementById('chart-registry').getContext('2d');
    chartInstances['chart-registry'] = new Chart(regCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.registry_breakdown),
            datasets: [{
                data: Object.values(data.registry_breakdown),
                backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } }
            }
        }
    });

    // Risk chart
    destroyChart('chart-risk');
    const riskCtx = document.getElementById('chart-risk').getContext('2d');
    chartInstances['chart-risk'] = new Chart(riskCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.risk_distribution),
            datasets: [{
                data: Object.values(data.risk_distribution),
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#dc2626'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Inter' } } }
            }
        }
    });

    // Project types chart
    destroyChart('chart-types');
    const typesCtx = document.getElementById('chart-types').getContext('2d');
    chartInstances['chart-types'] = new Chart(typesCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(data.project_type_breakdown),
            datasets: [{
                label: 'Projects',
                data: Object.values(data.project_type_breakdown),
                backgroundColor: '#3b82f6',
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { family: 'Inter' } } },
                y: { grid: { display: false }, ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } }
            }
        }
    });
}

// ─── Projects ───────────────────────────────────────────────
async function loadProjects() {
    const registry = document.getElementById('filter-registry').value;
    const type = document.getElementById('filter-type').value;
    let url = '/api/projects/?limit=100';
    if (registry) url += `&registry=${encodeURIComponent(registry)}`;
    if (type) url += `&project_type=${encodeURIComponent(type)}`;

    const data = await api(url);
    if (!data) return;

    document.getElementById('projects-table').innerHTML = `
        <table>
            <thead><tr>
                <th>Name</th><th>Registry</th><th>Type</th><th>Country</th>
                <th>Methodology</th><th>Buffer Pool</th><th>Status</th><th>Actions</th>
            </tr></thead>
            <tbody>
                ${data.map(p => `<tr>
                    <td style="max-width:200px;" title="${p.name}">${p.name}</td>
                    <td>${registryBadge(p.registry)}</td>
                    <td>${p.project_type}</td>
                    <td>${p.country}</td>
                    <td><code>${p.methodology || '—'}</code></td>
                    <td>${p.buffer_pool_percent}%</td>
                    <td><span class="badge badge-low">${p.status}</span></td>
                    <td><button class="btn-sm" onclick="showProject('${p.id}')">Details</button></td>
                </tr>`).join('')}
            </tbody>
        </table>
    `;
}

async function showProject(id) {
    const p = await api(`/api/projects/${id}`);
    if (!p) return;

    document.getElementById('modal-project-name').textContent = p.name;
    document.getElementById('project-modal').style.display = 'flex';

    let html = `
        <div class="detail-grid">
            <div class="detail-item"><div class="detail-label">Registry</div><div class="detail-value">${p.registry}</div></div>
            <div class="detail-item"><div class="detail-label">Registry ID</div><div class="detail-value">${p.registry_id || '—'}</div></div>
            <div class="detail-item"><div class="detail-label">Type</div><div class="detail-value">${p.project_type}</div></div>
            <div class="detail-item"><div class="detail-label">Country</div><div class="detail-value">${p.country}</div></div>
            <div class="detail-item"><div class="detail-label">Methodology</div><div class="detail-value">${p.methodology || '—'}</div></div>
            <div class="detail-item"><div class="detail-label">Buffer Pool</div><div class="detail-value">${p.buffer_pool_percent}%</div></div>
            <div class="detail-item"><div class="detail-label">Developer</div><div class="detail-value">${p.developer || '—'}</div></div>
            <div class="detail-item"><div class="detail-label">Coordinates</div><div class="detail-value">${p.latitude?.toFixed(2) || '—'}, ${p.longitude?.toFixed(2) || '—'}</div></div>
        </div>
        <p style="color:var(--text-secondary);font-size:13px;margin-bottom:20px;">${p.description || ''}</p>
    `;

    // Vintages
    if (p.vintages && p.vintages.length > 0) {
        html += `<div class="modal-section"><h3>Vintages (${p.vintages.length})</h3>
        <div class="data-table-wrapper"><table>
            <thead><tr><th>Year</th><th>Volume</th><th>Retired</th><th>Available</th><th>Velocity</th><th>Price/t</th></tr></thead>
            <tbody>${p.vintages.map(v => `<tr>
                <td>${v.issuance_year}</td>
                <td>${fmt(v.total_volume)}</td>
                <td>${fmt(v.retired_volume)}</td>
                <td>${fmt(v.available_volume)}</td>
                <td>${v.retirement_velocity}%/yr</td>
                <td>${$(v.price_per_tonne)}</td>
            </tr>`).join('')}</tbody>
        </table></div></div>`;
    }

    // Risk Signals
    if (p.risk_signals && p.risk_signals.length > 0) {
        const r = p.risk_signals[0];
        html += `<div class="modal-section"><h3>Latest Risk Signal</h3>
        <div class="detail-grid">
            <div class="detail-item"><div class="detail-label">Overall Rating</div><div class="detail-value">${riskBadge(r.overall_risk_rating)}</div></div>
            <div class="detail-item"><div class="detail-label">Composite Score</div><div class="detail-value">${r.composite_score}</div></div>
            <div class="detail-item"><div class="detail-label">Wildfire</div><div class="detail-value">${r.wildfire_proximity}</div></div>
            <div class="detail-item"><div class="detail-label">Deforestation</div><div class="detail-value">${r.deforestation_rate}</div></div>
            <div class="detail-item"><div class="detail-label">Political Risk</div><div class="detail-value">${r.political_risk_score}</div></div>
            <div class="detail-item"><div class="detail-label">Additionality</div><div class="detail-value">${r.additionality_score}</div></div>
            <div class="detail-item"><div class="detail-label">Reversal Risk</div><div class="detail-value">${r.reversal_risk}</div></div>
            <div class="detail-item"><div class="detail-label">Buffer Health</div><div class="detail-value">${r.buffer_pool_health}</div></div>
        </div></div>`;
    }

    // Audits
    if (p.audits && p.audits.length > 0) {
        html += `<div class="modal-section"><h3>Audits (${p.audits.length})</h3>
        <div class="data-table-wrapper"><table>
            <thead><tr><th>Date</th><th>VVB</th><th>Type</th><th>Quality</th><th>Reversal</th><th>Findings</th></tr></thead>
            <tbody>${p.audits.map(a => `<tr>
                <td>${new Date(a.audit_date).toLocaleDateString()}</td>
                <td>${a.vvb_name}</td>
                <td>${a.audit_type}</td>
                <td>${a.audit_quality_score}</td>
                <td>${a.reversal_event ? '<span class="badge badge-critical">YES</span>' : '<span class="badge badge-low">NO</span>'}</td>
                <td style="max-width:250px;" title="${a.findings_summary || ''}">${a.findings_summary || '—'}</td>
            </tr>`).join('')}</tbody>
        </table></div></div>`;
    }

    // Fair Value
    const fv = await api(`/api/quant/fair-value/${id}`);
    if (fv) {
        html += `<div class="modal-section"><h3>Fair Value Analysis</h3>
        <div class="detail-grid">
            <div class="detail-item"><div class="detail-label">Market Price</div><div class="detail-value">${$(fv.market_price)}</div></div>
            <div class="detail-item"><div class="detail-label">Fair Value</div><div class="detail-value" style="color:var(--accent-green);">${$(fv.fair_value)}</div></div>
            <div class="detail-item"><div class="detail-label">Alpha</div><div class="detail-value">${alphaSpan(fv.alpha_percent)}</div></div>
            <div class="detail-item"><div class="detail-label">Signal</div><div class="detail-value">${signalBadge(fv.signal)}</div></div>
            <div class="detail-item"><div class="detail-label">Reliability</div><div class="detail-value">${fv.reliability_score.toFixed(3)}</div></div>
            <div class="detail-item"><div class="detail-label">Liquidity Discount</div><div class="detail-value">${$(fv.liquidity_discount)}</div></div>
            <div class="detail-item"><div class="detail-label">Reversal Premium</div><div class="detail-value">${$(fv.reversal_risk_premium)}</div></div>
            <div class="detail-item"><div class="detail-label">Confidence</div><div class="detail-value">${fv.confidence}%</div></div>
        </div></div>`;
    }

    document.getElementById('modal-body').innerHTML = html;
}

function closeModal() {
    document.getElementById('project-modal').style.display = 'none';
}

// Close modal on backdrop click
document.getElementById('project-modal').addEventListener('click', (e) => {
    if (e.target.id === 'project-modal') closeModal();
});

// ─── Risk Explorer ──────────────────────────────────────────
async function loadRiskExplorer() {
    const dist = await api('/api/analytics/risk-distribution');
    const projects = await api('/api/projects/?limit=100');
    if (!dist || !projects) return;

    const o = dist.overall;
    const total = Object.values(o).reduce((a, b) => a + b, 0);

    document.getElementById('risk-overview').innerHTML = `
        <div class="stat-card green"><div class="stat-label">Low Risk</div><div class="stat-value">${o.LOW || 0}</div><div class="stat-sub">${total ? ((o.LOW / total) * 100).toFixed(0) : 0}% of projects</div></div>
        <div class="stat-card amber"><div class="stat-label">Medium Risk</div><div class="stat-value">${o.MEDIUM || 0}</div><div class="stat-sub">${total ? ((o.MEDIUM / total) * 100).toFixed(0) : 0}% of projects</div></div>
        <div class="stat-card red"><div class="stat-label">High Risk</div><div class="stat-value">${o.HIGH || 0}</div><div class="stat-sub">${total ? ((o.HIGH / total) * 100).toFixed(0) : 0}% of projects</div></div>
        <div class="stat-card purple"><div class="stat-label">Critical</div><div class="stat-value">${o.CRITICAL || 0}</div><div class="stat-sub">${total ? ((o.CRITICAL / total) * 100).toFixed(0) : 0}% of projects</div></div>
    `;

    // Histogram
    if (dist.composite_histogram && dist.composite_histogram.length > 0) {
        destroyChart('chart-risk-histogram');
        const ctx = document.getElementById('chart-risk-histogram').getContext('2d');
        chartInstances['chart-risk-histogram'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dist.composite_histogram.map(b => b.range),
                datasets: [{
                    label: 'Projects',
                    data: dist.composite_histogram.map(b => b.count),
                    backgroundColor: dist.composite_histogram.map(b => {
                        const start = parseInt(b.range);
                        if (start < 30) return '#10b981';
                        if (start < 50) return '#f59e0b';
                        if (start < 70) return '#ef4444';
                        return '#dc2626';
                    }),
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { family: 'Inter' } } },
                    y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { family: 'Inter' }, stepSize: 1 } }
                }
            }
        });
    }

    // Risk factors radar
    if (dist.by_factor) {
        destroyChart('chart-risk-factors');
        const ctx2 = document.getElementById('chart-risk-factors').getContext('2d');
        const factors = Object.keys(dist.by_factor);
        chartInstances['chart-risk-factors'] = new Chart(ctx2, {
            type: 'radar',
            data: {
                labels: factors.map(f => f.charAt(0).toUpperCase() + f.slice(1)),
                datasets: [
                    { label: 'High', data: factors.map(f => dist.by_factor[f].high), backgroundColor: 'rgba(239,68,68,0.2)', borderColor: '#ef4444', pointBackgroundColor: '#ef4444' },
                    { label: 'Medium', data: factors.map(f => dist.by_factor[f].medium), backgroundColor: 'rgba(245,158,11,0.2)', borderColor: '#f59e0b', pointBackgroundColor: '#f59e0b' },
                    { label: 'Low', data: factors.map(f => dist.by_factor[f].low), backgroundColor: 'rgba(16,185,129,0.2)', borderColor: '#10b981', pointBackgroundColor: '#10b981' },
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } } },
                scales: { r: { grid: { color: '#1e293b' }, ticks: { display: false }, pointLabels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } } }
            }
        });
    }

    // Risk table with all projects
    const riskRows = [];
    for (const p of projects) {
        const signals = await api(`/api/risk-signals/${p.id}`);
        if (signals && signals.length > 0) {
            const s = signals[0];
            riskRows.push({ ...p, risk: s });
        }
    }

    document.getElementById('risk-projects-table').innerHTML = `
        <table>
            <thead><tr>
                <th>Project</th><th>Registry</th><th>Type</th><th>Country</th>
                <th>Composite</th><th>Rating</th><th>Wildfire</th><th>Reversal</th>
            </tr></thead>
            <tbody>${riskRows.map(r => `<tr>
                <td style="max-width:180px;" title="${r.name}">${r.name}</td>
                <td>${registryBadge(r.registry)}</td>
                <td>${r.project_type}</td>
                <td>${r.country}</td>
                <td>${r.risk.composite_score}</td>
                <td>${riskBadge(r.risk.overall_risk_rating)}</td>
                <td>${r.risk.wildfire_proximity}</td>
                <td>${r.risk.reversal_risk}</td>
            </tr>`).join('')}</tbody>
        </table>
    `;
}

// ─── Quant Engine ───────────────────────────────────────────
async function loadQuantEngine() {
    const portfolio = await api('/api/quant/portfolio');
    if (!portfolio) return;

    document.getElementById('portfolio-summary').innerHTML = `
        <div class="stat-card green">
            <div class="stat-label">Portfolio Fair Value</div>
            <div class="stat-value">${$(portfolio.total_fair_value)}</div>
            <div class="stat-sub">${portfolio.total_projects} projects</div>
        </div>
        <div class="stat-card blue">
            <div class="stat-label">Market Value</div>
            <div class="stat-value">${$(portfolio.total_market_value)}</div>
            <div class="stat-sub">${fmt(portfolio.total_volume)} tCO₂e</div>
        </div>
        <div class="stat-card ${portfolio.portfolio_alpha >= 0 ? 'green' : 'red'}">
            <div class="stat-label">Portfolio Alpha</div>
            <div class="stat-value">${$(portfolio.portfolio_alpha)}</div>
            <div class="stat-sub">${((portfolio.portfolio_alpha / Math.max(1, portfolio.total_market_value)) * 100).toFixed(2)}% spread</div>
        </div>
        <div class="stat-card amber">
            <div class="stat-label">Avg Risk Score</div>
            <div class="stat-value">${portfolio.avg_risk_score}</div>
            <div class="stat-sub">Composite weighted</div>
        </div>
    `;

    document.getElementById('quant-positions').innerHTML = `
        <table>
            <thead><tr>
                <th>Project</th><th>Registry</th><th>Mkt Price</th><th>Fair Value</th>
                <th>Alpha</th><th>Signal</th><th>Confidence</th><th>Reliability</th>
            </tr></thead>
            <tbody>${portfolio.positions.map(p => `<tr>
                <td style="max-width:200px;" title="${p.project_name}">${p.project_name}</td>
                <td>${registryBadge(p.registry)}</td>
                <td>${$(p.market_price)}</td>
                <td>${$(p.fair_value)}</td>
                <td>${alphaSpan(p.alpha_percent)}</td>
                <td>${signalBadge(p.signal)}</td>
                <td>${p.confidence}%</td>
                <td>${p.reliability_score.toFixed(3)}</td>
            </tr>`).join('')}</tbody>
        </table>
    `;
}

// ─── Arbitrage ──────────────────────────────────────────────
async function loadArbitrage() {
    const data = await api('/api/quant/arbitrage?min_alpha=5');
    if (!data) return;

    if (data.length === 0) {
        document.getElementById('arbitrage-table').innerHTML = '<div class="loading" style="color:var(--text-muted)">No arbitrage opportunities found above threshold.</div>';
        return;
    }

    document.getElementById('arbitrage-table').innerHTML = `
        <table>
            <thead><tr>
                <th>Project</th><th>Registry</th><th>Type</th><th>Country</th>
                <th>Mkt Price</th><th>Fair Value</th><th>Alpha</th><th>Risk</th><th>Signal</th>
            </tr></thead>
            <tbody>${data.map(a => `<tr>
                <td style="max-width:200px;" title="${a.project_name}">${a.project_name}</td>
                <td>${registryBadge(a.registry)}</td>
                <td>${a.project_type}</td>
                <td>${a.country}</td>
                <td>${$(a.market_price)}</td>
                <td>${$(a.fair_value)}</td>
                <td>${alphaSpan(a.alpha_percent)}</td>
                <td>${riskBadge(a.risk_rating)}</td>
                <td>${signalBadge(a.signal)}</td>
            </tr>`).join('')}</tbody>
        </table>
    `;
}

// ─── Crawler ────────────────────────────────────────────────
async function triggerCrawl() {
    const btn = document.getElementById('btn-crawl');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⟳</span> Crawling...';

    const result = await apiPost('/api/crawler/run', { registries: ["Verra", "Gold Standard", "ACR", "CAR"] });

    const box = document.getElementById('crawl-result');
    if (result) {
        box.className = 'alert-box';
        box.innerHTML = `✓ Crawl completed: ${result.total_new} new projects, ${result.total_updated} updated across ${result.registries_crawled} registries.`;
    } else {
        box.className = 'alert-box error';
        box.innerHTML = '✗ Crawl failed. Check server logs.';
    }
    box.style.display = 'block';

    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">⟳</span> Run Registry Crawl';
    loadCrawlerHistory();
}

async function loadCrawlerHistory() {
    const data = await api('/api/crawler/status?limit=10');
    if (!data || data.length === 0) {
        document.getElementById('crawl-history').innerHTML = '<div class="loading" style="color:var(--text-muted)">No crawl history yet.</div>';
        return;
    }

    document.getElementById('crawl-history').innerHTML = `
        <table>
            <thead><tr><th>Registry</th><th>Status</th><th>Found</th><th>New</th><th>Updated</th><th>Started</th><th>Completed</th></tr></thead>
            <tbody>${data.map(r => `<tr>
                <td>${registryBadge(r.registry)}</td>
                <td><span class="badge ${r.status === 'completed' ? 'badge-low' : 'badge-medium'}">${r.status}</span></td>
                <td>${r.projects_found}</td>
                <td>${r.projects_new}</td>
                <td>${r.projects_updated}</td>
                <td>${r.started_at ? new Date(r.started_at).toLocaleString() : '—'}</td>
                <td>${r.completed_at ? new Date(r.completed_at).toLocaleString() : '—'}</td>
            </tr>`).join('')}</tbody>
        </table>
    `;
}

// ─── CDC Log ────────────────────────────────────────────────
async function loadCDCLog() {
    const data = await api('/api/analytics/cdc-log?limit=50');
    if (!data || data.length === 0) {
        document.getElementById('cdc-table').innerHTML = '<div class="loading" style="color:var(--text-muted)">No change history recorded yet.</div>';
        return;
    }

    document.getElementById('cdc-table').innerHTML = `
        <table>
            <thead><tr><th>Timestamp</th><th>Entity Type</th><th>Action</th><th>Entity ID</th><th>Changed Fields</th></tr></thead>
            <tbody>${data.map(c => `<tr>
                <td>${c.timestamp ? new Date(c.timestamp).toLocaleString() : '—'}</td>
                <td><span class="badge badge-verra">${c.entity_type}</span></td>
                <td><span class="badge ${c.action === 'create' ? 'badge-low' : c.action === 'delete' ? 'badge-high' : 'badge-medium'}">${c.action}</span></td>
                <td style="font-family:monospace;font-size:11px;">${c.entity_id ? c.entity_id.substring(0, 8) + '...' : '—'}</td>
                <td>${c.changed_fields ? JSON.stringify(c.changed_fields).substring(0, 60) : '—'}</td>
            </tr>`).join('')}</tbody>
        </table>
    `;
}

// ─── Document Search ────────────────────────────────────────
async function searchDocs() {
    const query = document.getElementById('doc-search-input').value.trim();
    if (!query) return;

    const results = await api(`/api/analytics/document-search?query=${encodeURIComponent(query)}&top_k=10`);
    if (!results || results.length === 0) {
        document.getElementById('doc-results').innerHTML = '<div class="loading" style="color:var(--text-muted)">No matching documents. Try indexing first.</div>';
        return;
    }

    document.getElementById('doc-results').innerHTML = results.map(r => `
        <div class="doc-result-card">
            <div class="doc-title">${r.title}</div>
            <div class="doc-similarity">Similarity: ${(r.similarity * 100).toFixed(1)}%</div>
            <div class="doc-summary">${r.content_summary || ''}</div>
        </div>
    `).join('');
}

async function indexDocs() {
    const result = await apiPost('/api/analytics/index-documents');
    if (result) {
        alert(`Indexed ${result.documents_indexed} documents. Vocabulary: ${result.index_stats.vocabulary_size || 0} terms.`);
    }
}

// ─── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
