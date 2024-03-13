'use strict';
/* global Helpers */

/**
 * Displays a loading wheel and disables form elements.
 */
function showLoadingWheel() {
    Helpers.changeInnerHTML(
        'submit',
        '<div class="spinner-border text-primary mb-3" role="status"></div>',
    );
    Helpers.addClass('submit', 'disabled');
    Helpers.addClass('username', 'disabled');
    Helpers.addClass('password', 'disabled');
    Helpers.replaceClass('submit', 'btn-primary', 'btn-info');
}

/**
 * Hides the loading wheel and restores the login form to its original state.
 */
function hideLoadingWheel() {
    Helpers.changeInnerHTML(
        'submit',
        'Log In',
    );
    Helpers.removeClass('submit', 'disabled');
    Helpers.removeClass('username', 'disabled');
    Helpers.removeClass('password', 'disabled');
    Helpers.replaceClass('submit', 'btn-info', 'btn-primary');
}

window.onload = () => {
    document.getElementById('login').addEventListener('submit', (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        if (!username || !password) {
            Helpers.changeInnerHTML(
                'response',
                Helpers.generateAlert('Please enter a username and password.', 'danger'),
            );
            return;
        }

        showLoadingWheel();

        /**
         * Represents the data object for login.
         * @typedef {Object} LoginData
         * @property {string} username - The username.
         * @property {string} password - The password.
         */

        const data = /** @type {LoginData} */ {
            username: username,
            password: password,
        };

        Helpers.apiCall('/api/login', 'POST', data)
            .then((response) => response.json())
            .then((response) => {
                if (response.success) {
                    Helpers.changeInnerHTML(
                        'response',
                        Helpers.generateAlert(response.message, 'success'),
                    );
                    Helpers.addClass('submit', 'd-none');
                    setTimeout(() => window.location.href = '/dashboard', 500);
                } else {
                    Helpers.changeInnerHTML(
                        'response',
                        Helpers.generateAlert(response.message, 'danger'),
                    );
                    hideLoadingWheel();
                }
            })
            .catch((error) => {
                Helpers.changeInnerHTML(
                    'response',
                    Helpers.generateAlert('Unable to log in. Please try again.', 'danger'),
                );
                hideLoadingWheel();
                console.log(error);
            });
    });
};
