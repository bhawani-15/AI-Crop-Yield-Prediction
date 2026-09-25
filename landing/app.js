/* ═══════════════════════════════════════════════════════════
   KrishiDrishti Landing Page — Complete JavaScript
   ═══════════════════════════════════════════════════════════
   Sections:
   1. Page animations (navbar, parallax, scroll-reveal, counters)
   2. Mobile hamburger
   3. Modal system (open/close)
   4. Metadata loader (single shared fetch, cached)
   5. Modal 1 — AI Yield Prediction (conversational wizard)
   6. Modal 2 — Agro-Weather Insights
   7. Modal 3 — Historical Yield Analytics (SVG chart)
   8. Modal 4 — SHAP Explainability
   ═══════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    const API = 'http://localhost:8000';

    /* ─────────────────────────────────────────
       § 1. PAGE ANIMATIONS
       ───────────────────────────────────────── */

    // Navbar scroll
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });

    // Hero parallax
    const heroBg = document.getElementById('hero-parallax');
    window.addEventListener('scroll', () => {
        if (heroBg) heroBg.style.transform = `scale(1.1) translateY(${window.scrollY * 0.25}px)`;
    }, { passive: true });

    // Scroll reveal
    const revealObs = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

    // Animated counters
    function easeOut(t) { return 1 - Math.pow(1 - t, 4); }
    function animCount(el, target, ms) {
        const t0 = performance.now();
        (function tick(now) {
            const p = Math.min((now - t0) / ms, 1);
            el.textContent = Math.floor(easeOut(p) * target).toLocaleString();
            if (p < 1) requestAnimationFrame(tick); else el.textContent = target.toLocaleString();
        })(t0);
    }
    let counted = false;
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length) {
        new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !counted) {
                counted = true;
                const targets = [77000, 30, 865, 491], durs = [1800, 1200, 1500, 1500];
                document.querySelectorAll('.stat-number').forEach((el, i) => animCount(el, targets[i], durs[i]));
            }
        }, { threshold: 0.3 }).observe(statCards[0]);
    }

    // Active nav highlight
    const navLinks = document.querySelectorAll('.nav-link');
    new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) navLinks.forEach(l => {
                l.classList.toggle('active', l.getAttribute('href') === `#${e.target.id}`);
            });
        });
    }, { threshold: 0.4 }).observe(document.querySelector('section[id]'));
    const activeStyle = document.createElement('style');
    activeStyle.textContent = `.nav-link.active{color:#fff!important;background:rgba(52,211,153,.14)!important}`;
    document.head.appendChild(activeStyle);

    /* ─────────────────────────────────────────
       § 2. MOBILE HAMBURGER
       ───────────────────────────────────────── */
    const ham = document.getElementById('hamburger');
    const nl = document.getElementById('nav-links');
    const nc = document.querySelector('.nav-cta');
    if (ham) {
        ham.addEventListener('click', () => {
            const open = nl.classList.toggle('open');
            if (nc) nc.classList.toggle('open', open);
            const [s0, s1, s2] = ham.querySelectorAll('span');
            if (open) {
                s0.style.transform = 'rotate(45deg) translate(5px,5px)';
                s1.style.opacity = '0';
                s2.style.transform = 'rotate(-45deg) translate(5px,-5px)';
            } else { s0.style.transform = s2.style.transform = ''; s1.style.opacity = ''; }
        });
        document.querySelectorAll('.nav-link').forEach(l => l.addEventListener('click', () => {
            nl.classList.remove('open'); if (nc) nc.classList.remove('open');
            ham.querySelectorAll('span').forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
        }));
    }

    /* ─────────────────────────────────────────
       § 3. MODAL SYSTEM
       ───────────────────────────────────────── */
    const overlay = document.getElementById('modal-overlay');
    const closeBtn = document.getElementById('modal-close-btn');
    let activePanel = null;

    function openModal(panelId) {
        document.querySelectorAll('.modal-panel').forEach(p => p.hidden = true);
        const panel = document.getElementById(panelId);
        if (!panel) return;
        panel.hidden = false;
        activePanel = panelId;
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        // Trigger data loading for this modal
        onModalOpen(panelId);
    }

    function closeModal() {
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        activePanel = null;
    }

    // Close on button, backdrop, Escape
    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && activePanel) closeModal(); });

    // Wire cards — both the card and its inner try-button
    document.querySelectorAll('[data-modal]').forEach(el => {
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            openModal(el.dataset.modal);
        });
        el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(el.dataset.modal); } });
    });

    /* ─────────────────────────────────────────
       § 4. SHARED METADATA CACHE
       ───────────────────────────────────────── */
    let metaCache = null;

    async function getMetadata() {
        if (metaCache) return metaCache;
        try {
            const r = await fetch(`${API}/api/metadata`, { signal: AbortSignal.timeout(6000) });
            metaCache = await r.json();
            return metaCache;
        } catch { return null; }
    }

    function fillSelect(sel, options, placeholder = '— Select —') {
        sel.innerHTML = `<option value="">${placeholder}</option>` +
            options.map(o => `<option value="${o}">${o}</option>`).join('');
    }

    function cascadeDistricts(stateSel, districtSel, meta) {
        stateSel.addEventListener('change', () => {
            const districts = (meta.state_to_districts || {})[stateSel.value] || [];
            fillSelect(districtSel, districts, '— Select District —');
        });
    }

    /* ─────────────────────────────────────────
       § 5. MODAL DISPATCH
       ───────────────────────────────────────── */
    function onModalOpen(id) {
        if (id === 'modal-yield') initYield();
        if (id === 'modal-weather') initWeather();
        if (id === 'modal-history') initHistory();
        if (id === 'modal-shap') initShap();
    }

    /* ─────────────────────────────────────────
       § 6. MODAL 1 — AI YIELD PREDICTION WIZARD
       ───────────────────────────────────────── */
    let yieldMeta = null;
    let wizState = {};

    async function initYield() {
        // Reset wizard
        resetYield();
        yieldMeta = await getMetadata();
        if (!yieldMeta) { addAiMsg('⚠️ Could not connect to the AI backend. Please ensure FastAPI is running on port 8000.'); return; }
        fillSelect(document.getElementById('wiz-state'), yieldMeta.states);
        fillSelect(document.getElementById('wiz-crop'), yieldMeta.crops);
        fillSelect(document.getElementById('wiz-season'), yieldMeta.seasons);
    }

    function resetYield() {
        wizState = {};
        const chatArea = document.getElementById('chat-area');
        chatArea.innerHTML = `
      <div class="chat-msg ai-msg">
        <span class="chat-avatar">🌾</span>
        <div class="chat-bubble"><strong>KrishiDrishti AI</strong><br/>
        Namaste! 🙏 I'll help you forecast crop yield. Let's begin — which <strong>State</strong> are you farming in?</div>
      </div>`;
        // Show only first step
        showWizStep('wiz-step-state');
        document.getElementById('yield-result').hidden = true;
        document.getElementById('wizard-steps').hidden = false;
    }

    function showWizStep(id) {
        document.querySelectorAll('.wiz-step').forEach(s => s.hidden = true);
        const el = document.getElementById(id);
        if (el) { el.hidden = false; el.querySelector('select,input')?.focus(); }
    }

    function addAiMsg(text) {
        const chat = document.getElementById('chat-area');
        const div = document.createElement('div');
        div.className = 'chat-msg ai-msg';
        div.innerHTML = `<span class="chat-avatar">🌾</span><div class="chat-bubble"><strong>KrishiDrishti AI</strong><br/>${text}</div>`;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    }

    function addUserMsg(text) {
        const chat = document.getElementById('chat-area');
        const div = document.createElement('div');
        div.className = 'chat-msg user-msg';
        div.innerHTML = `<div class="chat-bubble user-bubble">${text}</div><span class="chat-avatar">👨‍🌾</span>`;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    }

    // Step: State → District
    document.getElementById('wiz-next-state')?.addEventListener('click', () => {
        const sel = document.getElementById('wiz-state');
        if (!sel.value) { sel.style.borderColor = '#ef4444'; return; }
        sel.style.borderColor = '';
        wizState.state = sel.value;
        addUserMsg(sel.value);
        if (yieldMeta) fillSelect(document.getElementById('wiz-district'), (yieldMeta.state_to_districts || {})[sel.value] || []);
        addAiMsg(`Great choice! 🌏 <strong>${sel.value}</strong> is a major agricultural state. Now, which <strong>District</strong> are you in?`);
        showWizStep('wiz-step-district');
    });

    // Step: District → Crop
    document.getElementById('wiz-next-district')?.addEventListener('click', () => {
        const sel = document.getElementById('wiz-district');
        if (!sel.value) { sel.style.borderColor = '#ef4444'; return; }
        sel.style.borderColor = '';
        wizState.district = sel.value;
        addUserMsg(sel.value);
        addAiMsg(`📍 <strong>${sel.value}</strong> noted! Which <strong>Crop</strong> are you planning to grow?`);
        showWizStep('wiz-step-crop');
    });

    // Step: Crop → Season
    document.getElementById('wiz-next-crop')?.addEventListener('click', () => {
        const sel = document.getElementById('wiz-crop');
        if (!sel.value) { sel.style.borderColor = '#ef4444'; return; }
        sel.style.borderColor = '';
        wizState.crop = sel.value;
        addUserMsg(sel.value);
        addAiMsg(`🌾 <strong>${sel.value}</strong> is a popular crop in this region. Which <strong>Season</strong> are you targeting?`);
        showWizStep('wiz-step-season');
    });

    // Step: Season → Year
    document.getElementById('wiz-next-season')?.addEventListener('click', () => {
        const sel = document.getElementById('wiz-season');
        if (!sel.value) { sel.style.borderColor = '#ef4444'; return; }
        sel.style.borderColor = '';
        wizState.season = sel.value;
        addUserMsg(sel.value);
        addAiMsg(`📅 <strong>${sel.value}</strong> season selected. Finally, which <strong>Year</strong> do you want to forecast?`);
        showWizStep('wiz-step-year');
    });

    // Step: Year → Predict
    document.getElementById('wiz-predict-btn')?.addEventListener('click', async () => {
        const yearEl = document.getElementById('wiz-year');
        wizState.year = parseInt(yearEl.value, 10);
        addUserMsg(`Year ${wizState.year}`);
        addAiMsg(`🤖 Excellent! Let me run the XGBoost model now for <strong>${wizState.crop}</strong> in <strong>${wizState.district}, ${wizState.state}</strong> (${wizState.season} ${wizState.year})...<br/><em>Analysing 77K+ historical records…</em>`);
        document.getElementById('wizard-steps').hidden = true;

        try {
            const r = await fetch(`${API}/api/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    state: wizState.state,
                    district: wizState.district,
                    crop: wizState.crop,
                    season: wizState.season,
                    year: wizState.year,
                    custom_lag_yield: null
                }),
                signal: AbortSignal.timeout(10000)
            });

            if (!r.ok) throw new Error(`API ${r.status}`);
            const d = await r.json();
            renderYieldResult(d);
        } catch (err) {
            addAiMsg(`❌ Prediction failed: ${err.message}. Please check the FastAPI backend is running.`);
            document.getElementById('wizard-steps').hidden = false;
        }
    });

    function renderYieldResult(d) {
        const distDelta = d.delta_vs_district_pct;
        const stateDelta = d.delta_vs_state_pct;
        const distColor = distDelta >= 0 ? '#34d399' : '#f87171';
        const stateColor = stateDelta >= 0 ? '#34d399' : '#f87171';
        const distSign = distDelta >= 0 ? '+' : '';
        const stateSign = stateDelta >= 0 ? '+' : '';

        // AI congratulates with context
        const tone = d.predicted_yield_kg_ha > (d.district_avg_yield || 0)
            ? '✅ Excellent news! The forecast is <strong>above the district average</strong>.'
            : '📊 The forecast is slightly below the district average — consider optimizing inputs.';
        addAiMsg(`${tone} Here are your complete results 👇`);

        // Shap bars
        let shapHtml = '';
        if (d.shap_feature_importance?.length) {
            const maxAbs = Math.max(...d.shap_feature_importance.map(s => Math.abs(s.impact)));
            shapHtml = `<div class="shap-bars">
        <h4 class="shap-bars-title">🔍 Why this prediction? (SHAP drivers)</h4>
        ${d.shap_feature_importance.map(s => {
                const pct = Math.round((Math.abs(s.impact) / maxAbs) * 100);
                const col = s.impact >= 0 ? '#34d399' : '#f87171';
                const sign = s.impact >= 0 ? '+' : '';
                return `<div class="shap-row">
            <span class="shap-fname">${s.feature_name_clean}</span>
            <div class="shap-bar-wrap">
              <div class="shap-bar" style="width:${pct}%;background:${col}"></div>
            </div>
            <span class="shap-val" style="color:${col}">${sign}${s.impact.toFixed(1)}</span>
          </div>`;
            }).join('')}
      </div>`;
        }

        const el = document.getElementById('yield-result');
        el.innerHTML = `
      <div class="result-grid">
        <div class="result-kpi primary">
          <div class="kpi-label">Forecasted Yield</div>
          <div class="kpi-value">${d.predicted_yield_kg_ha.toLocaleString()}<span class="kpi-unit">kg/ha</span></div>
          <div class="kpi-sub">${d.predicted_yield_quintal_acre} Quintals/Acre</div>
        </div>
        <div class="result-kpi">
          <div class="kpi-label">Confidence</div>
          <div class="kpi-value conf">${d.confidence_level}</div>
          <div class="kpi-sub">Prior yield: ${d.lag_yield_used.toLocaleString()} kg/ha</div>
        </div>
        <div class="result-kpi">
          <div class="kpi-label">vs District Avg</div>
          <div class="kpi-value" style="color:${distColor}">${distSign}${distDelta ?? '—'}%</div>
          <div class="kpi-sub">District avg: ${d.district_avg_yield?.toLocaleString() ?? 'N/A'} kg/ha</div>
        </div>
        <div class="result-kpi">
          <div class="kpi-label">vs State Avg</div>
          <div class="kpi-value" style="color:${stateColor}">${stateSign}${stateDelta ?? '—'}%</div>
          <div class="kpi-sub">State avg: ${d.state_avg_yield?.toLocaleString() ?? 'N/A'} kg/ha</div>
        </div>
      </div>
      ${shapHtml}
      <a href="http://localhost:8501" class="result-dashboard-btn" target="_blank">Open Full Dashboard for complete analysis →</a>`;
        el.hidden = false;
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /* ─────────────────────────────────────────
       § 7. MODAL 2 — AGRO-WEATHER INSIGHTS
       ───────────────────────────────────────── */
    async function initWeather() {
        const meta = await getMetadata();
        if (!meta) return;
        const stateSel = document.getElementById('weather-state-sel');
        const districtSel = document.getElementById('weather-district-sel');
        fillSelect(stateSel, meta.states);
        cascadeDistricts(stateSel, districtSel, meta);
        document.getElementById('weather-result').hidden = true;
    }

    document.getElementById('weather-fetch-btn')?.addEventListener('click', async () => {
        const state = document.getElementById('weather-state-sel').value;
        const district = document.getElementById('weather-district-sel').value;
        if (!state || !district) {
            alert('Please select both State and District.'); return;
        }
        const btn = document.getElementById('weather-fetch-btn');
        btn.textContent = '⏳ Fetching…'; btn.disabled = true;

        try {
            const r = await fetch(`${API}/api/weather?district=${encodeURIComponent(district)}&state=${encodeURIComponent(state)}`,
                { signal: AbortSignal.timeout(8000) });
            if (!r.ok) throw new Error(`API ${r.status}`);
            const d = await r.json();
            renderWeatherResult(d);
        } catch (e) {
            document.getElementById('weather-result').innerHTML = `<div class="err-box">❌ Weather fetch failed: ${e.message}</div>`;
            document.getElementById('weather-result').hidden = false;
        } finally { btn.textContent = '🌤️ Get Live Weather'; btn.disabled = false; }
    });

    function renderWeatherResult(d) {
        const forecast = d.daily_forecast || [];
        const forecastHtml = forecast.map(f => `
      <div class="fc-day">
        <div class="fc-date">${f.date}</div>
        <div class="fc-temp">↑${f.temp_max}° ↓${f.temp_min}°</div>
        <div class="fc-rain">🌧 ${f.precipitation_sum}mm</div>
        ${f.rain_probability != null ? `<div class="fc-prob">${f.rain_probability}% rain</div>` : ''}
      </div>`).join('');

        const res = document.getElementById('weather-result');
        res.innerHTML = `
      <div class="weather-now-card">
        <div class="weather-loc">📍 ${d.district}, ${d.state}</div>
        <div class="weather-condition">🌤 ${d.weather_condition}</div>
        <div class="weather-metrics-grid">
          <div class="wm"><span>🌡️</span><strong>${d.current_temperature}°C</strong><small>Temperature</small></div>
          <div class="wm"><span>💧</span><strong>${d.current_humidity}%</strong><small>Humidity</small></div>
          <div class="wm"><span>🌧️</span><strong>${d.current_precipitation} mm</strong><small>Precipitation</small></div>
          <div class="wm"><span>💨</span><strong>${d.current_wind_speed} km/h</strong><small>Wind Speed</small></div>
        </div>
        <div class="advisory-box">
          🌱 <strong>Advisory:</strong> ${d.agricultural_advisory}
        </div>
      </div>
      <div class="forecast-label">7-Day Outlook</div>
      <div class="forecast-row">${forecastHtml}</div>`;
        res.hidden = false;
        res.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /* ─────────────────────────────────────────
       § 8. MODAL 3 — HISTORICAL TRENDS
       ───────────────────────────────────────── */
    async function initHistory() {
        const meta = await getMetadata();
        if (!meta) return;
        const stateSel = document.getElementById('hist-state-sel');
        const districtSel = document.getElementById('hist-district-sel');
        fillSelect(stateSel, meta.states);
        fillSelect(document.getElementById('hist-crop-sel'), meta.crops);
        cascadeDistricts(stateSel, districtSel, meta);
        document.getElementById('hist-result').hidden = true;
    }

    document.getElementById('hist-fetch-btn')?.addEventListener('click', async () => {
        const state = document.getElementById('hist-state-sel').value;
        const district = document.getElementById('hist-district-sel').value;
        const crop = document.getElementById('hist-crop-sel').value;
        if (!state || !district || !crop) { alert('Please select State, District, and Crop.'); return; }
        const btn = document.getElementById('hist-fetch-btn');
        btn.textContent = '⏳ Loading…'; btn.disabled = true;
        try {
            const r = await fetch(
                `${API}/api/historical-trends?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&crop=${encodeURIComponent(crop)}`,
                { signal: AbortSignal.timeout(8000) }
            );
            if (!r.ok) throw new Error(`API ${r.status}`);
            const d = await r.json();
            renderHistResult(d);
        } catch (e) {
            document.getElementById('hist-result').innerHTML = `<div class="err-box">❌ ${e.message}</div>`;
            document.getElementById('hist-result').hidden = false;
        } finally { btn.textContent = '📊 Show Historical Trends'; btn.disabled = false; }
    });

    function renderHistResult(d) {
        const trends = d.trends || [];
        const res = document.getElementById('hist-result');
        if (!trends.length) {
            res.innerHTML = `<div class="err-box">ℹ️ No historical data found for <strong>${d.crop}</strong> in <strong>${d.district}</strong>.</div>`;
            res.hidden = false; return;
        }

        const yields = trends.map(t => t.yield_kg_ha);
        const labels = trends.map(t => t.year);
        const maxY = Math.max(...yields) * 1.1;
        const minY = Math.max(0, Math.min(...yields) * 0.88);
        const W = 620, H = 200, padL = 60, padR = 20, padT = 20, padB = 40;
        const xStep = (W - padL - padR) / (yields.length - 1 || 1);

        function px(i) { return padL + i * xStep; }
        function py(v) { return padT + (H - padT - padB) * (1 - (v - minY) / (maxY - minY || 1)); }

        const pts = yields.map((v, i) => `${px(i)},${py(v)}`).join(' ');
        const areaD = `M${padL},${H - padB} ` + yields.map((v, i) => `L${px(i)},${py(v)}`).join(' ') + ` L${W - padR},${H - padB} Z`;

        const circles = yields.map((v, i) =>
            `<circle cx="${px(i)}" cy="${py(v)}" r="4" fill="#34d399" stroke="#042f2e" stroke-width="2">
         <title>${labels[i]}: ${v.toLocaleString()} kg/ha</title></circle>`
        ).join('');

        const xLabels = labels.map((l, i) =>
            `<text x="${px(i)}" y="${H - padB + 16}" text-anchor="middle" font-size="9" fill="#94a3b8">${l.split('-')[0]}</text>`
        ).join('');

        const yTick = [minY, (minY + maxY) / 2, maxY].map(v =>
            `<text x="${padL - 6}" y="${py(v) + 4}" text-anchor="end" font-size="9" fill="#94a3b8">${Math.round(v).toLocaleString()}</text>
       <line x1="${padL}" y1="${py(v)}" x2="${W - padR}" y2="${py(v)}" stroke="rgba(148,163,184,0.15)" stroke-width="1"/>`
        ).join('');

        res.innerHTML = `
      <div class="hist-header">
        <h4>${d.crop} — ${d.district}, ${d.state}</h4>
        <div class="hist-kpis">
          <span class="h-kpi">📈 Peak: <strong>${(d.max_yield || 0).toLocaleString()} kg/ha</strong></span>
          <span class="h-kpi">📉 Low: <strong>${(d.min_yield || 0).toLocaleString()} kg/ha</strong></span>
          <span class="h-kpi">📊 Avg: <strong>${(d.avg_yield || 0).toLocaleString()} kg/ha</strong></span>
        </div>
      </div>
      <div class="chart-wrap">
        <svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" class="trend-svg">
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#34d399" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="#34d399" stop-opacity="0.02"/>
            </linearGradient>
          </defs>
          ${yTick}
          <path d="${areaD}" fill="url(#areaGrad)"/>
          <polyline points="${pts}" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linejoin="round"/>
          ${circles}
          ${xLabels}
          <text x="${padL - 6}" y="${padT}" text-anchor="end" font-size="9" fill="#64748b">kg/ha</text>
        </svg>
      </div>
      <div class="hist-seasons">
        ${[...new Set(trends.map(t => t.season))].map(s => `<span class="f-tag">${s}</span>`).join('')}
      </div>`;
        res.hidden = false;
        res.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /* ─────────────────────────────────────────
       § 9. MODAL 4 — SHAP EXPLAINABILITY
       ───────────────────────────────────────── */
    async function initShap() {
        const meta = await getMetadata();
        if (!meta) return;
        const stateSel = document.getElementById('shap-state-sel');
        const districtSel = document.getElementById('shap-district-sel');
        fillSelect(stateSel, meta.states);
        fillSelect(document.getElementById('shap-crop-sel'), meta.crops);
        fillSelect(document.getElementById('shap-season-sel'), meta.seasons);
        cascadeDistricts(stateSel, districtSel, meta);
        document.getElementById('shap-result').hidden = true;
    }

    document.getElementById('shap-run-btn')?.addEventListener('click', async () => {
        const state = document.getElementById('shap-state-sel').value;
        const district = document.getElementById('shap-district-sel').value;
        const crop = document.getElementById('shap-crop-sel').value;
        const season = document.getElementById('shap-season-sel').value;
        if (!state || !district || !crop || !season) { alert('Please fill all fields.'); return; }
        const btn = document.getElementById('shap-run-btn');
        btn.textContent = '⏳ Computing SHAP…'; btn.disabled = true;

        try {
            const r = await fetch(`${API}/api/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state, district, crop, season, year: 2025, custom_lag_yield: null }),
                signal: AbortSignal.timeout(12000)
            });
            if (!r.ok) throw new Error(`API ${r.status}`);
            const d = await r.json();
            renderShapResult(d, district, state, crop, season);
        } catch (e) {
            document.getElementById('shap-result').innerHTML = `<div class="err-box">❌ ${e.message}</div>`;
            document.getElementById('shap-result').hidden = false;
        } finally { btn.textContent = '🔍 Explain This Prediction'; btn.disabled = false; }
    });

    function renderShapResult(d, district, state, crop, season) {
        const shap = d.shap_feature_importance || [];
        const maxAbs = Math.max(...shap.map(s => Math.abs(s.impact)), 1);
        const shapRows = shap.length
            ? shap.map(s => {
                const pct = Math.round((Math.abs(s.impact) / maxAbs) * 100);
                const col = s.impact >= 0 ? '#34d399' : '#f87171';
                const sign = s.impact >= 0 ? '+' : '';
                return `<div class="shap-row">
            <span class="shap-fname">${s.feature_name_clean}</span>
            <div class="shap-bar-wrap">
              <div class="shap-bar" style="width:${pct}%;background:${col}"></div>
            </div>
            <span class="shap-val" style="color:${col}">${sign}${s.impact.toFixed(1)} kg/ha</span>
          </div>`;
            }).join('')
            : '<p class="dim">No SHAP data returned.</p>';

        const res = document.getElementById('shap-result');
        res.innerHTML = `
      <div class="shap-header">
        <div class="result-kpi primary" style="margin-bottom:16px">
          <div class="kpi-label">Predicted Yield (2025)</div>
          <div class="kpi-value">${d.predicted_yield_kg_ha.toLocaleString()}<span class="kpi-unit">kg/ha</span></div>
          <div class="kpi-sub">${crop} · ${season} · ${district}, ${state}</div>
        </div>
        <h4 class="shap-bars-title">Feature Contributions (SHAP Values)</h4>
        <p class="dim" style="margin-bottom:12px">Each bar shows how much a feature <em>pushed</em> the prediction above (+) or below (−) the baseline.</p>
        <div class="shap-bars">${shapRows}</div>
        <div class="shap-legend">
          <span style="color:#34d399">■ Increases yield</span>
          <span style="color:#f87171">■ Decreases yield</span>
        </div>
      </div>`;
        res.hidden = false;
        res.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

})();
