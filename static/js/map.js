/**
 * RawMap — Application cartographique Leaflet
 *
 * Charge les agences depuis l'API v1 et affiche leur affluence
 * en temps réel via des marqueurs colorés.
 */

'use strict';

const RawMapApp = (() => {
    /* ------------------------------------------------------------------ */
    /* Configuration                                                       */
    /* ------------------------------------------------------------------ */
    const API = {
        agencies: '/api/v1/agencies/',
        affluence: '/api/v1/affluence/',
    };

    const DEFAULT_CENTER = [-4.3217, 15.3222]; // Kinshasa [lat, lng]
    const DEFAULT_ZOOM = 13;

    const AFFLUENCE_COLORS = {
        vert: '#28a745',
        orange: '#fd7e14',
        rouge: '#dc3545',
        default: '#6c757d',
    };

    const JOURS_SEMAINE = [
        'dimanche',
        'lundi',
        'mardi',
        'mercredi',
        'jeudi',
        'vendredi',
        'samedi',
    ];

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

    /* ------------------------------------------------------------------ */
    /* État interne                                                        */
    /* ------------------------------------------------------------------ */
    let map = null;
    let userMarker = null;
    let userPosition = null;
    let agencies = [];
    let affluenceByAgency = new Map();
    let agencyMarkers = new Map();
    let agencyLayerGroup = null;
    let selectedAgencyId = null;
    let activeFilter = 'all';

    /* ------------------------------------------------------------------ */
    /* Utilitaires DOM                                                     */
    /* ------------------------------------------------------------------ */
    const $ = (selector) => document.querySelector(selector);

    function showLoading(visible) {
        const el = $('#map-loading');
        if (el) {
            el.classList.toggle('hidden', !visible);
        }
    }

    function showError(message) {
        const el = $('#map-error');
        if (!el) {
            return;
        }
        if (message) {
            el.textContent = message;
            el.classList.remove('d-none');
        } else {
            el.classList.add('d-none');
        }
    }

    /* ------------------------------------------------------------------ */
    /* API                                                                 */
    /* ------------------------------------------------------------------ */
    async function fetchAllPages(url) {
        const results = [];
        let nextUrl = url;

        while (nextUrl) {
            const response = await fetch(nextUrl, {
                headers: { Accept: 'application/json' },
            });

            if (!response.ok) {
                throw new Error(`Erreur API (${response.status}) : ${nextUrl}`);
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

    async function loadAgencies() {
        agencies = await fetchAllPages(API.agencies);
    }

    async function loadAffluence() {
        const affluenceList = await fetchAllPages(API.affluence);
        affluenceByAgency = new Map(
            affluenceList.map((item) => [item.agence, item]),
        );
    }

    /* ------------------------------------------------------------------ */
    /* Carte Leaflet                                                       */
    /* ------------------------------------------------------------------ */
    function initMap() {
        map = L.map('rawmap-map', {
            zoomControl: true,
            attributionControl: true,
        }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);

        agencyLayerGroup = L.layerGroup().addTo(map);

        map.on('click', () => hideSearchResults());
    }

    function createMarkerIcon(type, level) {
        const levelAttr = level ? ` data-level="${level}"` : '';
        return L.divIcon({
            className: `rawmap-marker rawmap-marker-${type}${level ? ' rawmap-marker-agency' : ' rawmap-marker-user'}`,
            html: `<div class="rawmap-marker-dot"${levelAttr}></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
            popupAnchor: [0, -14],
        });
    }

    function renderUserMarker(lat, lng) {
        userPosition = { lat, lng };

        if (userMarker) {
            userMarker.setLatLng([lat, lng]);
        } else {
            userMarker = L.marker([lat, lng], {
                icon: createMarkerIcon('user'),
                zIndexOffset: 1000,
            })
                .addTo(map)
                .bindPopup('<strong>Votre position</strong>');
        }
    }

    function getAffluenceForAgency(agencyId) {
        return affluenceByAgency.get(agencyId) || null;
    }

    function getAffluenceLevel(agencyId) {
        const affluence = getAffluenceForAgency(agencyId);
        return affluence?.niveau || 'default';
    }

    function isAgencyOpen(agency) {
        if (!Array.isArray(agency.horaires) || agency.horaires.length === 0) {
            return null;
        }

        const today = JOURS_SEMAINE[new Date().getDay()];
        const horaire = agency.horaires.find((h) => h.jour === today);

        if (!horaire) {
            return false;
        }

        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();
        const [openH, openM] = horaire.heure_ouverture.split(':').map(Number);
        const [closeH, closeM] = horaire.heure_fermeture.split(':').map(Number);
        const openMinutes = openH * 60 + openM;
        const closeMinutes = closeH * 60 + closeM;

        return currentMinutes >= openMinutes && currentMinutes < closeMinutes;
    }

    function formatAddress(agency) {
        return [agency.adresse, agency.commune, agency.ville]
            .filter(Boolean)
            .join(', ');
    }

    function getTodayHoraire(agency) {
        if (!Array.isArray(agency.horaires) || agency.horaires.length === 0) {
            return null;
        }
        const today = JOURS_SEMAINE[new Date().getDay()];
        return agency.horaires.find((h) => h.jour === today) || null;
    }

    function formatTodayHours(agency) {
        const horaire = getTodayHoraire(agency);
        if (!horaire) {
            return 'Non renseigné';
        }
        const open = horaire.heure_ouverture.slice(0, 5);
        const close = horaire.heure_fermeture.slice(0, 5);
        return `${open} – ${close}`;
    }

    function getDirectionsUrl(agency) {
        return (
            `https://www.google.com/maps/dir/?api=1`
            + `&destination=${agency.latitude},${agency.longitude}`
        );
    }

    function getLevelLabel(level, affluence) {
        return affluence?.niveau_display || NIVEAU_LABELS[level] || 'N/A';
    }

    function buildAgencyPanelHtml(agency, compact = false) {
        const affluence = getAffluenceForAgency(agency.id);
        const isOpen = isAgencyOpen(agency);
        const openLabel = isOpen === null ? 'Non renseigné' : isOpen ? 'Ouverte' : 'Fermée';
        const openBadge = isOpen ? 'rm-badge-open' : 'rm-badge-closed';
        const level = affluence?.niveau || 'default';
        const levelLabel = getLevelLabel(level, affluence);
        const personnes = affluence?.personnes_presentes ?? '—';
        const taux = affluence?.taux_occupation ?? '—';
        const atmCount = agency.atm_disponibles_count ?? 0;
        const todayHours = formatTodayHours(agency);
        const directionsUrl = getDirectionsUrl(agency);
        const levelClass = {
            vert: 'rm-badge-faible',
            orange: 'rm-badge-moyenne',
            rouge: 'rm-badge-forte',
        }[level] || 'rm-badge-closed';

        const actions = `
            <div class="agency-panel-actions">
                <a href="/agencies/${agency.id}/" class="rm-btn rm-btn-primary rm-btn-sm">
                    <i class="bi bi-file-text"></i> Détails
                </a>
                <a href="${directionsUrl}" target="_blank" rel="noopener" class="rm-btn rm-btn-secondary rm-btn-sm">
                    <i class="bi bi-signpost-split"></i> Me guider
                </a>
            </div>`;

        const rows = `
            <div class="agency-panel-row"><i class="bi bi-geo-alt"></i><span>${escapeHtml(formatAddress(agency))}</span></div>
            <div class="agency-panel-row"><i class="bi bi-door-open"></i><span class="rm-badge ${openBadge}">${openLabel}</span></div>
            <div class="agency-panel-row"><i class="bi bi-people"></i><span>${personnes} personnes</span></div>
            <div class="agency-panel-row"><i class="bi bi-graph-up"></i><span>${taux}${taux !== '—' ? ' %' : ''} occupation</span></div>
            <div class="agency-panel-row"><i class="bi bi-traffic-light"></i><span class="rm-badge ${levelClass}">${escapeHtml(levelLabel)}</span></div>
            <div class="agency-panel-row"><i class="bi bi-credit-card-2-front"></i><span>${atmCount} ATM disponibles</span></div>
            <div class="agency-panel-row"><i class="bi bi-clock"></i><span>${escapeHtml(todayHours)}</span></div>`;

        if (compact) {
            return `<div class="agency-popup-premium">
                <h3 class="agency-popup-name">${escapeHtml(agency.nom)}</h3>
                <div class="agency-panel-rows">${rows}</div>${actions}
            </div>`;
        }

        return `<div class="agency-sidebar-content-inner">
            <div class="agency-sidebar-hero">
                <div class="agency-sidebar-icon"><i class="bi bi-building"></i></div>
                <h3>${escapeHtml(agency.nom)}</h3>
                <p class="rm-text-muted small mb-0">${escapeHtml(agency.code)}</p>
            </div>
            <div class="agency-panel-rows">${rows}</div>${actions}
        </div>`;
    }

    function buildPopupContent(agency) {
        return buildAgencyPanelHtml(agency, true);
    }

    function showAgencySidebar(agency) {
        selectedAgencyId = agency.id;
        const sidebar = $('#agency-sidebar');
        const content = $('#agency-sidebar-content');
        if (!sidebar || !content) return;
        content.innerHTML = buildAgencyPanelHtml(agency, false);
        sidebar.classList.add('is-open');
        sidebar.setAttribute('aria-hidden', 'false');
    }

    function hideAgencySidebar() {
        selectedAgencyId = null;
        const sidebar = $('#agency-sidebar');
        if (!sidebar) return;
        sidebar.classList.remove('is-open');
        sidebar.setAttribute('aria-hidden', 'true');
    }

    function refreshAgencyViews(agency) {
        const marker = agencyMarkers.get(agency.id);
        if (marker) {
            marker.setPopupContent(buildPopupContent(agency));
        }
        if (selectedAgencyId === agency.id) {
            const content = $('#agency-sidebar-content');
            if (content) content.innerHTML = buildAgencyPanelHtml(agency, false);
        }
    }

    function selectAgency(agencyId) {
        const agency = agencies.find((a) => a.id === agencyId);
        if (!agency) return;
        const marker = agencyMarkers.get(agencyId);
        if (marker) {
            map.flyTo(marker.getLatLng(), 16, { duration: 0.8 });
        }
        showAgencySidebar(agency);
        if (window.innerWidth < 992 && marker) {
            marker.openPopup();
        }
    }

    function passesFilter(agencyId) {
        if (activeFilter === 'all') return true;
        return getAffluenceLevel(agencyId) === activeFilter;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function renderAgencyMarkers() {
        agencyLayerGroup.clearLayers();
        agencyMarkers.clear();

        agencies.forEach((agency) => {
            if (agency.latitude == null || agency.longitude == null) {
                return;
            }

            const level = getAffluenceLevel(agency.id);
            const marker = L.marker([agency.latitude, agency.longitude], {
                icon: createMarkerIcon('agency', level),
                opacity: passesFilter(agency.id) ? 1 : 0.25,
            });

            marker.bindPopup(buildPopupContent(agency), {
                maxWidth: 360,
                minWidth: 280,
                className: 'agency-popup-wrapper',
            });

            marker.on('click', () => selectAgency(agency.id));

            marker.addTo(agencyLayerGroup);
            agencyMarkers.set(agency.id, marker);
        });
    }

    /* ------------------------------------------------------------------ */
    /* Géolocalisation                                                     */
    /* ------------------------------------------------------------------ */
    function locateUser(flyTo = true) {
        if (!navigator.geolocation) {
            showError('La géolocalisation n\'est pas supportée par votre navigateur.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                renderUserMarker(latitude, longitude);
                showError(null);

                if (flyTo) {
                    map.flyTo([latitude, longitude], 15, { duration: 1.2 });
                }
            },
            (error) => {
                const messages = {
                    1: 'Autorisation de géolocalisation refusée.',
                    2: 'Position indisponible.',
                    3: 'Délai de géolocalisation dépassé.',
                };
                showError(messages[error.code] || 'Impossible d\'obtenir votre position.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000,
            },
        );
    }

    /* ------------------------------------------------------------------ */
    /* Recherche                                                           */
    /* ------------------------------------------------------------------ */
    function hideSearchResults() {
        const container = $('#search-results');
        if (container) {
            container.classList.add('d-none');
            container.innerHTML = '';
        }
    }

    function showSearchResults(matches) {
        const container = $('#search-results');
        if (!container) {
            return;
        }

        if (matches.length === 0) {
            container.innerHTML = `
                <div class="search-result-item text-muted">
                    Aucune agence trouvée.
                </div>
            `;
        } else {
            container.innerHTML = matches
                .slice(0, 8)
                .map(
                    (agency) => `
                    <button
                        type="button"
                        class="search-result-item"
                        data-agency-id="${agency.id}"
                        role="option"
                    >
                        <div class="search-result-name">${escapeHtml(agency.nom)}</div>
                        <div class="search-result-meta">${escapeHtml(formatAddress(agency))}</div>
                    </button>
                `,
                )
                .join('');
        }

        container.classList.remove('d-none');

        container.querySelectorAll('.search-result-item[data-agency-id]').forEach((btn) => {
            btn.addEventListener('click', () => {
                focusAgency(Number(btn.dataset.agencyId));
                hideSearchResults();
                $('#agency-search').value = btn.querySelector('.search-result-name').textContent;
            });
        });
    }

    function searchAgencies(query) {
        const normalized = query.trim().toLowerCase();
        if (!normalized) {
            hideSearchResults();
            return;
        }

        const matches = agencies.filter((agency) =>
            agency.nom.toLowerCase().includes(normalized),
        );

        showSearchResults(matches);
    }

    function focusAgency(agencyId) {
        selectAgency(agencyId);
    }

    /* ------------------------------------------------------------------ */
    /* Synchronisation affluence (simulateur / IoT)                        */
    /* ------------------------------------------------------------------ */
    function updateAgencyAffluence(agencyId, affluenceData) {
        affluenceByAgency.set(agencyId, affluenceData);

        const marker = agencyMarkers.get(agencyId);
        const agency = agencies.find((item) => item.id === agencyId);

        if (!marker || !agency) {
            return;
        }

        const level = affluenceData?.niveau || 'default';
        marker.setIcon(createMarkerIcon('agency', level));
        marker.setOpacity(passesFilter(agencyId) ? 1 : 0.25);
        refreshAgencyViews(agency);
    }

    function initAffluenceSync() {
        if (typeof BroadcastChannel === 'undefined') {
            return;
        }

        const channel = new BroadcastChannel('rawmap-affluence');
        channel.onmessage = (event) => {
            if (event.data?.type === 'affluence-updated') {
                updateAgencyAffluence(event.data.agency_id, event.data.affluence);
            }
        };
    }

    /* ------------------------------------------------------------------ */
    /* Événements                                                          */
    /* ------------------------------------------------------------------ */
    function bindEvents() {
        $('#btn-locate')?.addEventListener('click', () => locateUser(true));

        const searchInput = $('#agency-search');
        searchInput?.addEventListener('input', (event) => {
            searchAgencies(event.target.value);
        });

        searchInput?.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                hideSearchResults();
            }
        });

        document.addEventListener('click', (event) => {
            if (!event.target.closest('.map-header')) {
                hideSearchResults();
            }
        });

        $('#sidebar-close')?.addEventListener('click', hideAgencySidebar);

        document.querySelectorAll('#affluence-filters .rm-chip').forEach((chip) => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('#affluence-filters .rm-chip').forEach((c) => c.classList.remove('active'));
                chip.classList.add('active');
                activeFilter = chip.dataset.filter || 'all';
                renderAgencyMarkers();
            });
        });
    }

    /* ------------------------------------------------------------------ */
    /* Initialisation                                                      */
    /* ------------------------------------------------------------------ */
    async function init() {
        const mapElement = $('#rawmap-map');
        if (!mapElement) {
            return;
        }

        initMap();
        bindEvents();
        showLoading(true);
        showError(null);

        try {
            await Promise.all([loadAgencies(), loadAffluence()]);
            renderAgencyMarkers();
            initAffluenceSync();
            locateUser(false);
        } catch (error) {
            console.error('RawMap — Erreur de chargement :', error);
            showError(
                'Impossible de charger les agences. Vérifiez que l\'API est accessible.',
            );
        } finally {
            showLoading(false);
        }

        console.info('RawMap — Carte initialisée.');
    }

    return { init, updateAgencyAffluence };
})();

document.addEventListener('DOMContentLoaded', () => {
    RawMapApp.init();
});
