"""
Tests unitaires — application accounts.
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.forms import LoginForm, RegisterForm
from apps.accounts.models import Profile


class RegisterFormTests(TestCase):
    def test_register_creates_user_and_profile(self):
        form = RegisterForm(data={
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'username': 'jeandupont',
            'email': 'jean@example.cd',
            'telephone': '+243812345678',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        profile = Profile.objects.get(user=user)
        self.assertEqual(user.email, 'jean@example.cd')
        self.assertEqual(profile.telephone, '+243812345678')

    def test_register_password_mismatch(self):
        form = RegisterForm(data={
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'username': 'jean2',
            'email': 'jean2@example.cd',
            'telephone': '+243812345678',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.cd',
            password='TestPass123!',
        )

    def test_login_with_username(self):
        form = LoginForm(data={
            'identifier': 'loginuser',
            'password': 'TestPass123!',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_login_with_email(self):
        form = LoginForm(data={
            'identifier': 'login@example.cd',
            'password': 'TestPass123!',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_login_invalid_credentials(self):
        form = LoginForm(data={
            'identifier': 'loginuser',
            'password': 'wrongpassword',
        })
        self.assertFalse(form.is_valid())


class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser',
            email='view@example.cd',
            password='TestPass123!',
            first_name='View',
            last_name='User',
        )
        Profile.objects.get_or_create(user=self.user, defaults={'telephone': '+243812345678'})

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_register_and_auto_login(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Marie',
            'last_name': 'Kabila',
            'username': 'mariek',
            'email': 'marie@example.cd',
            'telephone': '+243812345679',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:home'))
        self.assertTrue(User.objects.filter(username='mariek').exists())
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'identifier': 'view@example.cd',
            'password': 'TestPass123!',
            'remember_me': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:home'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_success_with_csrf_enforcement(self):
        client = Client(enforce_csrf_checks=True)
        login_page = client.get(reverse('accounts:login'))
        self.assertEqual(login_page.status_code, 200)
        csrf_token = login_page.context['csrf_token']
        response = client.post(
            reverse('accounts:login'),
            {
                'identifier': 'view@example.cd',
                'password': 'TestPass123!',
                'remember_me': True,
                'csrfmiddlewaretoken': csrf_token,
            },
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[:500])
        self.assertEqual(response.url, reverse('core:home'))

    def test_root_redirects_to_login(self):
        response = self.client.get(reverse('accounts:entry'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_update(self):
        self.client.login(username='viewuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.cd',
            'telephone': '+243812345680',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'updated@example.cd')

    def test_logout(self):
        self.client.login(username='viewuser', password='TestPass123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_redirected_from_login(self):
        self.client.login(username='viewuser', password='TestPass123!')
        response = self.client.get(reverse('accounts:login'))
        self.assertRedirects(response, reverse('core:home'))
