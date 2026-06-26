"""
Vues d'authentification et de profil — application accounts.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import FormView, TemplateView

from apps.accounts.forms import LoginForm, ProfileUpdateForm, RegisterForm
from apps.accounts.models import Profile


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(FormView):
    """Page de connexion — /login/"""

    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        remember_me = form.cleaned_data.get('remember_me')
        if remember_me:
            self.request.session.set_expiry(60 * 60 * 24 * 14)  # 14 jours
        else:
            self.request.session.set_expiry(0)  # fin de session navigateur

        messages.success(self.request, f'Bienvenue, {user.get_short_name() or user.username} !')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Connexion impossible. Vérifiez vos identifiants.')
        return super().form_invalid(form)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RegisterView(FormView):
    """Page d'inscription — /register/"""

    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            'Votre compte a été créé avec succès. Bienvenue sur RawMap !',
        )
        return super().form_valid(form)


class LogoutView(AuthLogoutView):
    """Déconnexion — /logout/"""

    next_page = reverse_lazy('accounts:login')
    http_method_names = ['get', 'post', 'head', 'options']

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Vous avez été déconnecté.')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ProfileView(TemplateView):
    """Page de profil utilisateur — /profile/"""

    template_name = 'accounts/profile.html'

    def get(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileUpdateForm(instance=profile, user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour.')
            return redirect('accounts:profile')

        messages.error(request, 'Corrigez les erreurs ci-dessous.')
        return render(request, self.template_name, {'form': form})
