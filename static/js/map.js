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
        vert: 'Vert',
        orange: 'Orange',
        rouge: 'Rouge',
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

    function buildPopupContent(agency) {
        const affluence = getAffluenceForAgency(agency.id);
        const isOpen = isAgencyOpen(agency);
        const openLabel = isOpen === null ? 'Non renseigné' : isOpen ? 'Ouverte' : 'Fermée';
        const openClass = isOpen ? 'open' : 'closed';
        const level = affluence?.niveau || 'default';
        const levelLabel = affluence?.niveau_display || NIVEAU_LABELS[level] || 'N/A';
        const personnes = affluence?.personnes_presentes ?? '—';
        const taux = affluence?.taux_occupation ?? '—';

        return `
            <div class="agency-popup">
                <div class="agency-popup-title">${escapeHtml(agency.nom)}</div>
                <ul class="agency-popup-list">
                    <li>
                        <span>Adresse</span>
                        <span>${escapeHtml(formatAddress(agency))}</span>
                    </li>
                    <li>
                        <span>Statut</span>
                        <span class="agency-popup-badge ${openClass}">${openLabel}</span>
                    </li>
                    <li>
                        <span>Personnes</span>
                        <span>${personnes}</span>
                    </li>
                    <li>
                        <span>Occupation</span>
                        <span>${taux}${taux !== '—' ? ' %' : ''}</span>
                    </li>
                    <li>
                        <span>Niveau</span>
                        <span class="agency-popup-badge level-${level}">${escapeHtml(levelLabel)}</span>
                    </li>
                </ul>
                <a
                    href="/agencies/${agency.id}/"
                    class="btn btn-sm btn-primary w-100"
                >
                    Voir les détails
                </a>
            </div>
        `;
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
            });

            marker.bindPopup(buildPopupContent(agency), {
                maxWidth: 300,
                minWidth: 220,
            });

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
        const marker = agencyMarkers.get(agencyId);
        if (!marker) {
            return;
        }

        map.flyTo(marker.getLatLng(), 16, { duration: 1 });
        marker.openPopup();
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
        marker.setPopupContent(buildPopupContent(agency));
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
            if (!event.target.closest('.map-controls')) {
                hideSearchResults();
            }
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
