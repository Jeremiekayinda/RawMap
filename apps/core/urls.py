"""
URLs de l'application core (pages publiques de base).
"""

from django.urls import path

from apps.core import views

app_name = 'core'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('agencies/<int:pk>/', views.agency_detail, name='agency-detail'),
]
