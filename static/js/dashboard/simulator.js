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
        vert: 'Vert',
        orange: 'Orange',
        rouge: 'Rouge',
    };

    const BROADCAST_CHANNEL = 'rawmap-affluence';

    let agencies = [];
    let affluenceMap = new Map();

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
            niveau_display: 'Vert',
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
        badge.textContent = affluence.niveau_display || NIVEAU_LABELS[affluence.niveau] || '—';
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
        broadcastAffluenceUpdate(agencyId, data.affluence);
    }

    function buildAgencyCard(agency) {
        const affluence = getAffluence(agency.id);
        const niveau = affluence.niveau || 'default';

        return `
            <div class="col-12 col-md-6 col-xl-4">
                <article class="card agency-card" data-agency-id="${agency.id}">
                    <div class="card-body">
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
                                <span class="niveau-badge ${niveau}" data-field="niveau">${escapeHtml(affluence.niveau_display || NIVEAU_LABELS[niveau] || '—')}</span>
                            </div>
                            <div class="affluence-stat">
                                <span class="affluence-stat-label">Capacité max.</span>
                                <span class="affluence-stat-value">${agency.capacite_max}</span>
                            </div>
                        </div>
                        <div class="simulator-actions">
                            <button type="button" class="btn btn-success btn-sm" data-action="entry" data-agency-id="${agency.id}">
                                ➕ Entrée
                            </button>
                            <button type="button" class="btn btn-warning btn-sm" data-action="exit" data-agency-id="${agency.id}">
                                ➖ Sortie
                            </button>
                            <button type="button" class="btn btn-outline-secondary btn-sm" data-action="reset" data-agency-id="${agency.id}">
                                🔄 Reset
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

    function renderGrid() {
        const grid = $('#simulator-grid');
        if (!grid) {
            return;
        }

        grid.innerHTML = agencies.map(buildAgencyCard).join('');
        grid.classList.remove('d-none');
        $('#simulator-loading')?.classList.add('d-none');
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
