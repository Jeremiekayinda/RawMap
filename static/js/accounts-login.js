/**
 * RawMap — Page de connexion premium
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    initPasswordToggle();
    initInputAnimations();
    initForgotPasswordHint();
});

function initPasswordToggle() {
    const toggleBtn = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('login-password');
    const toggleIcon = document.getElementById('toggle-password-icon');

    if (!toggleBtn || !passwordInput || !toggleIcon) {
        return;
    }

    toggleBtn.addEventListener('click', () => {
        const isHidden = passwordInput.type === 'password';
        passwordInput.type = isHidden ? 'text' : 'password';
        toggleIcon.classList.toggle('bi-eye', !isHidden);
        toggleIcon.classList.toggle('bi-eye-slash', isHidden);
    });
}

function initInputAnimations() {
    document.querySelectorAll('.rawmap-input-wrap .rawmap-input').forEach((input) => {
        input.addEventListener('focus', () => {
            input.closest('.rawmap-input-wrap')?.classList.add('is-focused');
        });
        input.addEventListener('blur', () => {
            input.closest('.rawmap-input-wrap')?.classList.remove('is-focused');
        });
    });
}

function initForgotPasswordHint() {
    const link = document.querySelector('.rawmap-link-forgot');
    if (!link) {
        return;
    }

    link.addEventListener('click', (event) => {
        event.preventDefault();
        link.setAttribute('title', 'Fonctionnalité bientôt disponible');
    });
}
