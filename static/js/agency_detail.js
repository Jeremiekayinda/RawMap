/**
 * RawMap — Page détail agence
 *
 * Initialise la carte Leaflet centrée sur l'agence
 * et le graphique d'évolution de l'affluence.
 */

'use strict';

const AgencyDetailPage = (() => {
    let affluenceChart = null;

    function initMap() {
        const mapEl = document.getElementById('agency-detail-map');
        if (!mapEl || typeof L === 'undefined') {
            return;
        }

        const latitude = parseFloat(mapEl.dataset.latitude);
        const longitude = parseFloat(mapEl.dataset.longitude);
        const agencyName = mapEl.dataset.agencyName || 'Agence';

        if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
            return;
        }

        const map = L.map(mapEl, {
            zoomControl: true,
            scrollWheelZoom: false,
        }).setView([latitude, longitude], 16);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(map);

        const affluenceLevel = document.querySelector('.niveau-badge')?.classList
            .item(1)
            ?.replace('niveau-', '') || 'default';

        const colors = {
            vert: '#28a745',
            orange: '#fd7e14',
            rouge: '#dc3545',
            default: '#0d6efd',
        };

        const markerIcon = L.divIcon({
            className: 'rawmap-marker rawmap-marker-agency',
            html: `<div class="rawmap-marker-dot" style="background-color:${colors[affluenceLevel] || colors.default};width:22px;height:22px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.35);"></div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14],
        });

        L.marker([latitude, longitude], { icon: markerIcon })
            .addTo(map)
            .bindPopup(`<strong>${escapeHtml(agencyName)}</strong>`)
            .openPopup();

        setTimeout(() => map.invalidateSize(), 200);
    }

    function initChart() {
        const canvas = document.getElementById('affluence-chart');
        const dataEl = document.getElementById('affluence-chart-data');

        if (!canvas || !dataEl || typeof Chart === 'undefined') {
            return;
        }

        let chartData;
        try {
            chartData = JSON.parse(dataEl.textContent);
        } catch (error) {
            console.error('Erreur parsing données graphique :', error);
            return;
        }

        if (!chartData.labels?.length) {
            return;
        }

        affluenceChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Personnes présentes',
                        data: chartData.personnes,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Taux d\'occupation (%)',
                        data: chartData.taux,
                        borderColor: '#fd7e14',
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        tension: 0.3,
                        pointRadius: 3,
                        yAxisID: 'y1',
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Personnes' },
                        beginAtZero: true,
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Occupation (%)' },
                        beginAtZero: true,
                        grid: { drawOnChartArea: false },
                    },
                },
            },
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initAffluenceSync() {
        if (typeof BroadcastChannel === 'undefined') {
            return;
        }

        const channel = new BroadcastChannel('rawmap-affluence');
        channel.onmessage = (event) => {
            if (event.data?.type !== 'affluence-updated' || !affluenceChart) {
                return;
            }
            location.reload();
        };
    }

    function init() {
        initMap();
        initChart();
        initAffluenceSync();
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', () => {
    AgencyDetailPage.init();
});
