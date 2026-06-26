/**
 * RawMap — Simulateur d'affluence (dashboard admin)
 *
 * Appelle l'API REST du simulateur et met à jour l'interface
 * sans rechargement de page. Notifie la carte Leaflet via BroadcastChannel.
 */

'use strict';

const AffluenceSimulator = (() => {
    const API = {
        agencies: '/api/v1/agencies/',
        affluence: '/api/v1/affluence/',
        entry: (id) => `/api/v1/simulator/entry/${id}/`,
        exit: (id) => `/api/v1/simulator/exit/${id}/`,
        reset: (id) => `/api/v1/simulator/reset/${id}/`,
    };

    const NIVEAU_LABELS = {
        vert: 'Faible',
        orange: 'Moyenne',
        rouge: 'Forte',
    };

    const NIVEAU_EMOJI = {
        vert: '🟢',
        orange: '🟠',
        rouge: '🔴',
    };

    const BROADCAST_CHANNEL = 'rawmap-affluence';

    let agencies = [];
    let affluenceMap = new Map();
    let affluenceChart = null;

    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => document.querySelectorAll(selector);

    function getCsrfToken() {
        return (
            document.querySelector('meta[name="csrf-token"]')?.content
            || document.cookie
                .split('; ')
                .find((row) => row.startsWith('csrftoken='))
                ?.split('=')[1]
            || ''
        );
    }

    function showAlert(message, type = 'danger') {
        const el = $('#simulator-alert');
        if (!el) {
            return;
        }
        el.textContent = message;
        el.className = `alert alert-${type}`;
        el.classList.remove('d-none');
        setTimeout(() => el.classList.add('d-none'), 5000);
    }

    async function fetchAllPages(url) {
        const results = [];
        let nextUrl = url;

        while (nextUrl) {
            const response = await fetch(nextUrl, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`Erreur API (${response.status})`);
            }

            const data = await response.json();
            if (Array.isArray(data)) {
                return data;
            }
            if (Array.isArray(data.results)) {
                results.push(...data.results);
            }
            nextUrl = data.next;
        }
        return results;
    }

    async function loadData() {
        const [agenciesData, affluenceData] = await Promise.all([
            fetchAllPages(API.agencies),
            fetchAllPages(API.affluence),
        ]);

        agencies = agenciesData;
        affluenceMap = new Map(
            affluenceData.map((item) => [item.agence, item]),
        );
    }

    function getAffluence(agencyId) {
        return affluenceMap.get(agencyId) || {
            personnes_presentes: 0,
            taux_occupation: '0.00',
            niveau: 'vert',
            niveau_display: 'Faible',
        };
    }

    function broadcastAffluenceUpdate(agencyId, affluence) {
        if (typeof BroadcastChannel === 'undefined') {
            return;
        }
        const channel = new BroadcastChannel(BROADCAST_CHANNEL);
        channel.postMessage({
            type: 'affluence-updated',
            agency_id: agencyId,
            affluence,
        });
        channel.close();
    }

    function updateCardUI(agencyId, affluence) {
        const card = document.querySelector(`[data-agency-id="${agencyId}"]`);
        if (!card) {
            return;
        }

        card.querySelector('[data-field="personnes"]').textContent =
            affluence.personnes_presentes;
        card.querySelector('[data-field="taux"]').textContent =
            `${affluence.taux_occupation} %`;

        const badge = card.querySelector('[data-field="niveau"]');
        const levelLabel = affluence.niveau_display || NIVEAU_LABELS[affluence.niveau] || '—';
        const levelEmoji = NIVEAU_EMOJI[affluence.niveau] || '';
        badge.textContent = levelEmoji ? `${levelEmoji} ${levelLabel}` : levelLabel;
        badge.className = `niveau-badge ${affluence.niveau || 'default'}`;

        card.classList.remove('updating');
    }

    async function callSimulatorAction(action, agencyId) {
        const urls = {
            entry: API.entry(agencyId),
            exit: API.exit(agencyId),
            reset: API.reset(agencyId),
        };

        const card = document.querySelector(`[data-agency-id="${agencyId}"]`);
        card?.classList.add('updating');

        const response = await fetch(urls[action], {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
        });

        const data = await response.json();

        if (!response.ok || data.status === 'error') {
            card?.classList.remove('updating');
            showAlert(data.message || 'Erreur lors de la mise à jour.');
            return;
        }

        affluenceMap.set(agencyId, data.affluence);
        updateCardUI(agencyId, data.affluence);
        updateStats();
        broadcastAffluenceUpdate(agencyId, data.affluence);
    }

    function formatNiveauLabel(affluence) {
        const level = affluence.niveau || 'vert';
        const label = affluence.niveau_display || NIVEAU_LABELS[level] || '—';
        const emoji = NIVEAU_EMOJI[level] || '';
        return emoji ? `${emoji} ${label}` : label;
    }

    function buildAgencyCard(agency) {
        const affluence = getAffluence(agency.id);
        const niveau = affluence.niveau || 'default';

        return `
            <div class="col-12 col-md-6 col-xl-4">
                <article class="rm-card agency-card" data-agency-id="${agency.id}">
                    <div class="rm-card-body">
                        <div class="agency-card-header">
                            <h2 class="agency-card-title">${escapeHtml(agency.nom)}</h2>
                            <div class="agency-card-code">${escapeHtml(agency.code)}</div>
                        </div>
                        <div class="affluence-stats">
                            <div class="affluence-stat">
                                <span class="affluence-stat-label">Personnes</span>
                                <span class="affluence-stat-value" data-field="personnes">${affluence.personnes_presentes}</span>
                            </div>
                            <div class="affluence-stat">
                                <span class="affluence-stat-label">Occupation</span>
                                <span class="affluence-stat-value" data-field="taux">${affluence.taux_occupation} %</span>
                            </div>
                            <div class="affluence-stat">
                                <span class="affluence-stat-label">Niveau</span>
                                <span class="niveau-badge ${niveau}" data-field="niveau">${escapeHtml(formatNiveauLabel(affluence))}</span>
                            </div>
                            <div class="affluence-stat">
                                <span class="affluence-stat-label">Capacité max.</span>
                                <span class="affluence-stat-value">${agency.capacite_max}</span>
                            </div>
                        </div>
                        <div class="simulator-actions">
                            <button type="button" class="rm-btn rm-btn-primary rm-btn-sm" data-action="entry" data-agency-id="${agency.id}">
                                <i class="bi bi-plus-lg"></i> Entrée
                            </button>
                            <button type="button" class="rm-btn rm-btn-secondary rm-btn-sm" data-action="exit" data-agency-id="${agency.id}">
                                <i class="bi bi-dash-lg"></i> Sortie
                            </button>
                            <button type="button" class="rm-btn rm-btn-dark rm-btn-sm" data-action="reset" data-agency-id="${agency.id}">
                                <i class="bi bi-arrow-counterclockwise"></i> Reset
                            </button>
                        </div>
                    </div>
                </article>
            </div>
        `;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function updateStats() {
        const stats = { vert: 0, orange: 0, rouge: 0 };
        affluenceMap.forEach((item) => {
            if (item.niveau in stats) stats[item.niveau] += 1;
        });
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('stat-agencies', agencies.length);
        set('stat-faible', stats.vert);
        set('stat-moyenne', stats.orange);
        set('stat-forte', stats.rouge);
        updateChart(stats);
    }

    function updateChart(stats) {
        const canvas = document.getElementById('affluence-chart');
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const data = {
            labels: ['Faible', 'Moyenne', 'Forte'],
            datasets: [{
                data: [stats.vert, stats.orange, stats.rouge],
                backgroundColor: ['#28a745', '#fd7e14', '#dc3545'],
                borderWidth: 0,
                hoverOffset: 6,
            }],
        };

        if (affluenceChart) {
            affluenceChart.data.datasets[0].data = data.datasets[0].data;
            affluenceChart.update();
            return;
        }

        affluenceChart = new Chart(canvas, {
            type: 'doughnut',
            data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '62%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 16,
                            usePointStyle: true,
                            font: { family: 'Poppins, sans-serif', size: 12 },
                        },
                    },
                },
            },
        });
    }

    function renderGrid() {
        const grid = $('#simulator-grid');
        if (!grid) {
            return;
        }

        grid.innerHTML = agencies.map(buildAgencyCard).join('');
        grid.classList.remove('d-none');
        $('#simulator-loading')?.classList.add('d-none');
        updateStats();
    }

    function bindEvents() {
        document.addEventListener('click', (event) => {
            const btn = event.target.closest('[data-action][data-agency-id]');
            if (!btn) {
                return;
            }
            const action = btn.dataset.action;
            const agencyId = Number(btn.dataset.agencyId);
            callSimulatorAction(action, agencyId);
        });
    }

    async function init() {
        const grid = $('#simulator-grid');
        if (!grid) {
            return;
        }

        bindEvents();

        try {
            await loadData();
            renderGrid();
        } catch (error) {
            console.error('Simulateur — erreur :', error);
            showAlert('Impossible de charger les agences. Vérifiez votre connexion et vos droits admin.');
            $('#simulator-loading')?.classList.add('d-none');
        }
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', () => {
    AffluenceSimulator.init();
});
