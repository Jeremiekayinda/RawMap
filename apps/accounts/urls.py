"""
URLs — application accounts.
"""

from django.urls import path
from django.views.generic.base import RedirectView

from apps.accounts.views import LoginView, LogoutView, ProfileView, RegisterView

app_name = 'accounts'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='entry'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
