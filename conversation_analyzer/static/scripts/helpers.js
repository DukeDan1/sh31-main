'use strict';
/* exported Helpers */

/**
 * A collection of helper functions for the application.
 */
class Helpers {
    /**
     * Represents a generic API call.
     * Requires the csrfmiddlewaretoken to be present in the DOM.
     * @param {string} endpoint - The endpoint to call.
     * @param {string} method - The HTTP method to use.
     * @param {string} body - An object containing the body of the request.
     * @return {Promise} - A promise object representing the response.
     */
    static apiCall(endpoint, method, body) {
        return fetch(endpoint, {
            method,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
    }

    /**
     * Adds a class to an element.
     * @param {string} elementId - The ID of the element to add the class to.
     * @param {string} className - The name of the class to add.
     */
    static addClass(elementId, className) {
        document.getElementById(elementId).classList.add(className);
    }

    /**
     * Removes a class from an element.
     * @param {string} elementId - The ID of the element to remove the class from.
     * @param {string} className - The name of the class to remove.
     */
    static removeClass(elementId, className) {
        document.getElementById(elementId).classList.remove(className);
    }

    /**
     * Replaces a class on an element.
     * @param {string} elementId - The ID of the element to toggle the class on.
     * @param {string} replaceClass - The name of the class to replace.
     * @param {string} newClass - The name of the new class.
     */
    static replaceClass(elementId, replaceClass, newClass) {
        Helpers.addClass(elementId, newClass);
        Helpers.removeClass(elementId, replaceClass);
    }

    /**
     * Changes the inner HTML of an element.
     * @param {string} elementId - The ID of the element to change the inner HTML of.
     * @param {string} content - The new inner HTML content.
     */
    static changeInnerHTML(elementId, content) {
        document.getElementById(elementId).innerHTML = content;
    }

    /**
     * Generates an alert message.
     * @param {string} msg - The message to display in the alert.
     * @param {string} type - The type of alert to generate (default: 'danger').
     * @return {string} - The HTML code for the alert.
     */
    static generateAlert(msg, type = 'danger') {
        return `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <strong> ${msg} </strong>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close">
            </button>
        </div>
        `;
    }

    /**
     * Shows a loading message, used in the upload page.
     * @param {string} uploadElementId - The ID of the upload element.
     */
    static showLoading(uploadElementId) {
        Helpers.addClass('upload-label', 'disabled');
        Helpers.addClass(uploadElementId, 'disabled');
        Helpers.replaceClass('preview-wrapper', 'd-block', 'd-none');
        Helpers.replaceClass('info', 'd-none', 'd-block');
        Helpers.changeInnerHTML('info', `
        <div class="d-flex justify-content-center align-items-center mt-5">
        <div class="text-center">
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <div>We're processing your conversation, please wait...</div>
        </div>
        </div>`);
    }

    /**
     * Recursively gets all the children of an element.
     * @param {HTMLElement} element - The element to get the children of.
     * @return {Array<HTMLElement>} An array of all the children of the element.
     */
    static recursiveChildren(element) {
        const children = Array.from(element.children);
        return children.concat(children.map((e) => this.recursiveChildren(e)).flat());
    }

    /**
     * Function which finds duplicate values in a form.
     * @param {Array} choices - An array of objects representing the form choices.
     * @return {boolean} - True if all elements unique, false if not.
     */
    static areChoicesValid(choices) {
        let choice;
        for (choice of choices) {
            if (choices.filter((x) => x.value == choice.value).length > 1) {
                return false;
            }
            if (choice.value == '') {
                return false;
            }
        }
        return true;
    }
}
