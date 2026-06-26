"""
Formulaires d'authentification et de profil — application accounts.
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Profile
from apps.accounts.validators.validators import validate_telephone


class LoginForm(forms.Form):
    """Connexion par email ou nom d'utilisateur."""

    identifier = forms.CharField(
        label=_('Email ou nom d\'utilisateur'),
        max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'rawmap-input',
                'id': 'login-identifier',
                'placeholder': 'Entrez votre email ou nom d\'utilisateur',
                'autocomplete': 'username',
                'autofocus': True,
            },
        ),
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'rawmap-input rawmap-input-password',
                'id': 'login-password',
                'placeholder': 'Entrez votre mot de passe',
                'autocomplete': 'current-password',
            },
        ),
    )
    remember_me = forms.BooleanField(
        label=_('Se souvenir de moi'),
        required=False,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input rawmap-check'},
        ),
    )

    error_messages = {
        'invalid_login': _(
            'Identifiants incorrects. Vérifiez votre email ou nom d\'utilisateur '
            'et votre mot de passe.',
        ),
        'inactive': _('Ce compte est désactivé.'),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('identifier', '').strip()
        password = cleaned_data.get('password')

        if not identifier or not password:
            return cleaned_data

        user = self._resolve_user(identifier)
        if user is None:
            raise ValidationError(self.error_messages['invalid_login'])

        authenticated = authenticate(
            self.request,
            username=user.get_username(),
            password=password,
        )
        if authenticated is None:
            raise ValidationError(self.error_messages['invalid_login'])

        if not authenticated.is_active:
            raise ValidationError(self.error_messages['inactive'])

        self.user_cache = authenticated
        return cleaned_data

    def get_user(self):
        return self.user_cache

    @staticmethod
    def _resolve_user(identifier: str) -> User | None:
        if '@' in identifier:
            return User.objects.filter(email__iexact=identifier).first()
        return User.objects.filter(username__iexact=identifier).first()


class RegisterForm(forms.Form):
    """Inscription d'un nouvel utilisateur RawMap."""

    first_name = forms.CharField(
        label=_('Prénom'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'rawmap-input', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label=_('Nom'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'rawmap-input', 'autocomplete': 'family-name'}),
    )
    username = forms.CharField(
        label=_('Nom d\'utilisateur'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'rawmap-input', 'autocomplete': 'username'}),
    )
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'class': 'rawmap-input', 'autocomplete': 'email'}),
    )
    telephone = forms.CharField(
        label=_('Téléphone'),
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'class': 'rawmap-input',
                'placeholder': '+243812345678',
                'autocomplete': 'tel',
            },
        ),
    )
    password1 = forms.CharField(
        label=_('Mot de passe'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'rawmap-input rawmap-input-password',
                'id': 'register-password1',
                'autocomplete': 'new-password',
            },
        ),
    )
    password2 = forms.CharField(
        label=_('Confirmation du mot de passe'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'rawmap-input rawmap-input-password',
                'id': 'register-password2',
                'autocomplete': 'new-password',
            },
        ),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_('Ce nom d\'utilisateur est déjà pris.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_('Cet email est déjà utilisé.'))
        return email

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone'].strip()
        validate_telephone(telephone)
        return telephone

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', _('Les mots de passe ne correspondent pas.'))

        if password1:
            validate_password(password1)

        return cleaned_data

    def save(self) -> User:
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.telephone = self.cleaned_data['telephone']
        profile.save(update_fields=['telephone', 'updated_at'])
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Mise à jour du profil utilisateur."""

    first_name = forms.CharField(
        label=_('Prénom'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'rawmap-input', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label=_('Nom'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'rawmap-input', 'autocomplete': 'family-name'}),
    )
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'class': 'rawmap-input', 'autocomplete': 'email'}),
    )

    class Meta:
        model = Profile
        fields = ['photo', 'telephone']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'rawmap-input', 'accept': 'image/*'}),
            'telephone': forms.TextInput(
                attrs={'class': 'rawmap-input', 'placeholder': '+243812345678', 'autocomplete': 'tel'},
            ),
        }
        labels = {
            'photo': _('Photo'),
            'telephone': _('Téléphone'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.user.first_name
        self.fields['last_name'].initial = self.user.last_name
        self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
        if exists:
            raise ValidationError(_('Cet email est déjà utilisé par un autre compte.'))
        return email

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').strip()
        if telephone:
            validate_telephone(telephone)
        return telephone

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save(update_fields=['first_name', 'last_name', 'email'])
        if commit:
            profile.save()
        return profile
