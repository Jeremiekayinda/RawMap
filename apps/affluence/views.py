"""
Vues de l'application affluence.

Interface dashboard du simulateur temporaire d'affluence.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(staff_member_required, name='dispatch')
class SimulatorDashboardView(TemplateView):
    """
    Dashboard admin du simulateur d'affluence.

    Interface temporaire remplaçant les ESP32 pour tester les entrées
    et sorties clients par agence.
    """

    template_name = 'dashboard/simulator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Simulateur d\'affluence — RawMap'
        return context
