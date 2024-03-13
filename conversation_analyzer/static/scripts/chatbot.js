'use strict';
/* global Helpers */
// Always load this script last.

/**
 * Represents the chatbot interface.
 */
class Chatbot {
    /**
     * Represents the chatbot interface.
     * The interface is used to communicate with the chatbot API endpoint.
     * @constructor
     * @param {string} elementID - The ID of the element to display the chatbot in.
     * @param {string} documentID - The document ID of the conversation to analyse.}
     */
    constructor(elementID, documentID) {
        this.display_element = elementID;
        this.messages = [];
        this.documentID = documentID;

        this.createEventListeners();
    }

    /**
     * Initializes the chatbot event listeners.
    */
    createEventListeners() {
        document.getElementById(this.display_element + '-form')
            .addEventListener('submit', (event) => {
                event.preventDefault();
                this.fetchResponse();
            });

        document.getElementById(this.display_element + '-input')
            .addEventListener('input', (event) => {
                // disable / enable submit button
                if (document.getElementById(this.display_element + '-input').value === '') {
                    Helpers.addClass(this.display_element + '-submit', 'disabled');
                } else {
                    Helpers.removeClass(this.display_element + '-submit', 'disabled');
                }

                const txHeight = 38;
                const tx = event.target;

                if (tx.value == '') {
                    tx.setAttribute('style', 'height:' + txHeight + 'px;overflow-y:hidden;');
                } else {
                    tx.setAttribute('style', 'height:'+(tx.scrollHeight)+'px;overflow-y:hidden;');
                }

                tx.height = 'auto';
                tx.height = (this.scrollHeight) + 'px';
            });

        document.getElementById(this.display_element + '-input')
            .addEventListener('keydown', (event) => {
                // submit form if enter is pressed. Do not submit if shift+enter is pressed.
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    document.getElementById(this.display_element + '-submit').click();
                }
            });

        document.getElementById(this.display_element + '-button')
            .addEventListener('click', (event) => {
                event.preventDefault();
                const chatbotElement = document.getElementById(this.display_element);
                const chatbotButton = document.getElementById(this.display_element + '-button');
                if (chatbotElement.classList.contains('d-none')) {
                    chatbotElement.classList.remove('d-none');
                    chatbotButton.classList.add('d-none');
                } else {
                    chatbotElement.classList.add('d-none');
                    chatbotButton.classList.remove('d-none');
                }
            });

        document.getElementById(this.display_element + '-close')
            .addEventListener('click', () => {
                const chatbotElement = document.getElementById(this.display_element);
                const chatbotButton = document.getElementById(this.display_element + '-button');
                chatbotElement.classList.add('d-none');
                chatbotButton.classList.remove('d-none');
            });
    }

    /**
     * Fetch a response from OpenAI.
     */
    fetchResponse() {
        const message = document.getElementById(this.display_element + '-input').value;

        this.messages.push({
            role: 'user',
            content: message,
        });
        this.messages.push({
            role: 'assistant',
            content: `<div class='spinner-grow' style='width: 28px; height: 30px;' role='status'>
                <span class='visually-hidden'>Loading...</span>
            </div>`,
        });

        document.getElementById(this.display_element + '-input')
            .setAttribute('style', 'height:38px;overflow-y:hidden;');

        // display the user's message
        this.displayMessages();
        document.getElementById(this.display_element + '-input').value = '';
        Helpers.addClass(this.display_element + '-submit', 'disabled');
        this.messages.pop();

        const body = {
            user_messages: this.messages,
            document_id: this.documentID,
        };

        Helpers.apiCall('/api/chatbot', 'POST', body)
            .then((response) => response.json())
            .then((response) => {
                if (response.success) {
                    this.messages = response.messages;
                    this.displayMessages();
                } else {
                    this.messages.push({
                        role: 'assistant',
                        content: Helpers.generateAlert(response.error),
                    });
                    this.displayMessages();

                    document.getElementById(this.display_element + '-input').value = message;
                    Helpers.removeClass(this.display_element + '-submit', 'disabled');
                }
            })
            .catch((error) => {
                this.messages.push({
                    role: 'assistant',
                    content: Helpers.generateAlert(
                        'An error has occurred while fetching the response. Please try again.',
                    ),
                });
                this.displayMessages();

                document.getElementById(this.display_element + '-input').value = message;
                Helpers.removeClass(this.display_element + '-submit', 'disabled');
            });
    }

    /**
     * Displays the messages in the chatbot.
     */
    displayMessages() {
        // the this.messages variable contains an array of messages.
        // each message has a role (either assistant or user) and a content (the message itself)
        Helpers.changeInnerHTML(this.display_element + '-body', '');
        for (const message of this.messages) {
            const messageElement = document.createElement('div');
            messageElement.classList.add(this.display_element + '-message', message.role);
            messageElement.innerHTML = message.content;
            document.getElementById(this.display_element + '-body').appendChild(messageElement);
        }
        // scroll to the bottom of the chat
        const parent = document.getElementById(this.display_element + '-body');
        parent.scrollTop = parent.scrollHeight;
    }

    /**
     * Resets the chatbot and sets a new document ID.
     * @param {string} documentID - The document ID of the conversation to analyse.
    */
    changeDocument(documentID) {
        this.messages = [];
        this.documentID = documentID;
        this.displayMessages();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const documentID = document.getElementById('document-id').value;
    const chatbot = new Chatbot('chatbot', documentID);

    document.getElementById('document-id')
        .addEventListener('change', (event) => {
            chatbot.changeDocument(event.target.value);
        });
});
