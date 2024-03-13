'use strict';
/* global Helpers, processFileNLPWithProgress */

/**
 * Represents a file upload object.
 * @class
 */
class FileUpload {
    /**
     * Creates a new instance of FileUpload.
     */
    constructor() {
        /**
         * The name of the file being uploaded.
         * @type {string}
         */
        this.fileName = null;
        /**
         * The base URL for the API endpoint.
         * @type {string}
         */
        this.apiBase = '/api/upload-file';
        /**
         * The ID of the upload element.
         * @type {string}
         */
        this.uploadElementId = 'upload-label';
        const uploadInputElement = document.getElementById(this.uploadElementId).control;
        uploadInputElement.style.display = 'none';
        const previewGridOptions = {
            columnDefs: [],
            rowData: [],
        };

        // eslint-disable-next-line no-undef
        new agGrid.Grid(document.getElementById('preview-grid'), previewGridOptions);
        previewGridOptions.api.sizeColumnsToFit();
        /**
         * The options for the preview grid.
         * @type {Object}
         */
        this.previewGridOptions = previewGridOptions;
        /**
         * The data in the preview, initially null.
         * @type {Array}
         */
        this.previewData = null;
    }

    /**
     * Uploads the selected file.
     */
    upload() {
        const formData = new FormData();
        formData.append('file', document.getElementById(this.uploadElementId).control.files[0]);
        Helpers.showLoading(this.uploadElementId);
        fetch(this.apiBase, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector(['[name=csrfmiddlewaretoken]']).value,
            },
        })
            .then((response) => response.json())
            .catch((err) => {
                this.displayError('An unexpected error has occurred. Please try again.');
                console.log(err);
            })
            .then((data) => {
                if (data.success) {
                    this.previewData = data.preview;
                    this.format();
                    this.messages();
                    this.populateFields(Object.keys(this.previewData[0]));
                    Helpers.changeInnerHTML('info', '');
                    this.setFileName(data.file_name);
                    this.showFieldMapping(true);
                } else {
                    this.displayError(data.error);
                }
            }).catch((err) => {
                this.displayError(`An unexpected error has occurred. 
                Please try again with a different file.`);
                console.log(err);
            });
    }

    /**
     * Formats the preview data and displays it in the grid.
     */
    format() {
        const firstPreviewRowData = typeof this.previewData.at(0) === 'undefined' ?
            {} : this.previewData[0];
        const previewColumnDefs = Object.keys(firstPreviewRowData)
            .map((key) => Object({field: key}));

        // extract message.raw_content if present
        for (let x = 0; x < this.previewData.length; x++) {
            if (this.previewData[x].body && this.previewData[x].body.raw_content) {
                this.previewData[x].body = this.previewData[x].body.raw_content;
            }
        }

        this.previewGridOptions.api.setColumnDefs(previewColumnDefs);
        this.previewGridOptions.api.setRowData(this.previewData);
        this.previewGridOptions.api.sizeColumnsToFit();
        Helpers.replaceClass('preview-wrapper', 'd-none', 'd-block');
        Helpers.removeClass('accept-btn', 'disabled');
        Helpers.removeClass('reject-btn', 'disabled');
    }

    /**
     * Shows or hides the field mapping section based on the given parameter.
     * @param {boolean} show - Indicates whether to show or hide the field mapping
     * and message preview section.
     */
    showFieldMapping(show) {
        if (show) {
            Helpers.replaceClass('field-mapping', 'd-none', 'd-block');
            Helpers.replaceClass('field-map-heading', 'd-none', 'd-block');
            Helpers.replaceClass('messages-heading', 'd-none', 'd-block');
            Helpers.replaceClass('show-messages', 'd-none', 'd-block');
        } else {
            Helpers.replaceClass('field-mapping', 'd-block', 'd-none');
            Helpers.replaceClass('field-map-heading', 'd-block', 'd-none');
            Helpers.replaceClass('messages-heading', 'd-block', 'd-none');
            Helpers.replaceClass('show-messages', 'd-block', 'd-none');
        }
    }

    /**
     * Handles the response from the server after accepting or rejecting the file.
     * @param {string} response - The response type (accept or reject).
     */
    handleResponse(response) {
        const buttonId = `${response}-btn`;
        const endpoint = `${this.apiBase}/${response}`;
        const body = {
            file_name: this.getFileName(),
        };

        Helpers.changeInnerHTML('info', '');
        Helpers.changeInnerHTML('error', '');

        if (response == 'accept') {
            body.field_mapping = Helpers.recursiveChildren(
                document.getElementById('field-mapping'),
            )
                .filter((e) => e.tagName.toLowerCase() == 'select')
                .map((selectField) => {
                    return {
                        'field': selectField.id.replace('message-', ''),
                        'value': selectField.value,
                    };
                });

            if (!document.getElementById('separate-dt-fields').checked) {
                body.field_mapping = body.field_mapping.filter((e) =>
                    e.field != 'date' && e.field != 'time',
                );
            } else {
                body.field_mapping = body.field_mapping.filter((e) =>
                    e.field != 'timestamp',
                );
            }

            if (!Helpers.areChoicesValid(body.field_mapping)) {
                this.displayError(`You have selected duplicate columns, or
                you have not mapped a column. 
                Please ensure that each field is mapped to a unique column.`);
                return;
            }
        }

        Helpers.addClass('accept-btn', 'disabled');
        Helpers.addClass('reject-btn', 'disabled');
        Helpers.changeInnerHTML(buttonId, `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 
        ${response.charAt(0).toUpperCase() + response.slice(1)}ing...
        `);
        Helpers.apiCall(endpoint, 'POST', body)
            .then((response) => response.json())
            .catch((err) => {
                this.displayError('An unexpected error has occurred. Please try again.');
                Helpers.removeClass('accept-btn', 'disabled');
                Helpers.removeClass('reject-btn', 'disabled');
                Helpers.changeInnerHTML(
                    buttonId,
                    `${response.charAt(0).toUpperCase() + response.slice(1)}`,
                );
                console.log(err);
            }).then((data) => {
                Helpers.addClass('accept-btn', 'disabled');
                Helpers.addClass('reject-btn', 'disabled');
                Helpers.removeClass(this.uploadElementId, 'disabled');
                Helpers.changeInnerHTML(
                    buttonId,
                    `${response.charAt(0).toUpperCase() + response.slice(1)}`,
                );
                if (data.success) {
                    Helpers.changeInnerHTML('info', Helpers.generateAlert(data.message, 'success'));
                    Helpers.removeClass('info', 'd-none');
                    this.previewGridOptions.api.setColumnDefs([]);
                    this.previewGridOptions.api.setRowData([]);
                    this.previewGridOptions.api.sizeColumnsToFit();
                    Helpers.changeInnerHTML('messages', '');
                    this.showFieldMapping(false);
                    this.unpopulateFields();
                    processFileNLPWithProgress(this.getFileName(), false);
                } else {
                    this.displayError(data.error);
                    Helpers.removeClass('accept-btn', 'disabled');
                    Helpers.removeClass('reject-btn', 'disabled');
                }
            }).catch((err) => {
                console.log(err);
                Helpers.removeClass('accept-btn', 'disabled');
                Helpers.removeClass('reject-btn', 'disabled');
            });
    }

    /**
     * Accepts the uploaded file.
     */
    accept() {
        this.handleResponse('accept');
    }

    /**
     * Rejects the uploaded file.
     */
    reject() {
        this.handleResponse('reject');
    }

    /**
     * Returns the name of the uploaded file.
     * @return {string} The name of the uploaded file.
     */
    getFileName() {
        return this.fileName;
    }

    /**
     * Sets the name of the uploaded file.
     * @param {string} fileName - The name of the uploaded file.
     */
    setFileName(fileName) {
        this.fileName = fileName;
    }

    /**
     * Displays an error message.
     * @param {string} errors - The error message to display.
     */
    displayError(errors) {
        Helpers.changeInnerHTML('error', Helpers.generateAlert(errors));
        Helpers.removeClass(this.uploadElementId, 'disabled');
        Helpers.replaceClass('info', 'd-block', 'd-none');
        Helpers.replaceClass('preview-wrapper', 'd-none', 'd-block');
    }

    /**
    * Populates the field mapping dropdowns with the column names of the data file uploaded.
    * @param {Array} columnNames - The column names.
    */
    populateFields(columnNames) {
        const children = Helpers.recursiveChildren(document.getElementById('field-mapping'));
        children.filter((e) => e.tagName.toLowerCase() == 'select')
            .forEach((selectField) => {
                selectField.innerHTML += columnNames.map((columnName) => {
                    const acceptedValues = [columnName.toLowerCase()];

                    if (columnName == 'name') {
                        acceptedValues.push('sender');
                    } else if (columnName == 'username') {
                        acceptedValues.push('sender');
                    }

                    return `<option value="${columnName}" ${
                        acceptedValues
                            .indexOf(selectField.id.replace('message-', '')) > -1 ? ' selected' : ''
                    }
                    >${columnName}</option>`.replace('\n', '');
                });
            });

        if (columnNames.filter((e) => e.toLowerCase() == 'timestamp').length > 0) {
            this.showSeparateDateTimeFields(false);
        } else if (columnNames.filter((e) =>
            e.toLowerCase() == 'date' || e.toLowerCase() == 'time').length >= 2) {
            this.showSeparateDateTimeFields(true);
        } else if (columnNames.filter((e) => e.toLowerCase() == 'date').length > 0) {
            // this means that there is a date column but no time column
            this.showSeparateDateTimeFields(false);
            let x;
            const timestampField = document.getElementById('message-timestamp');
            for (x = 0; x < timestampField.options.length; x++) {
                if (timestampField[x].value == 'date') {
                    timestampField[x].selected = true;
                    break;
                }
            }
        } else {
            // no date, time or timestamp detected. Set timestamp as default
            // user will need to manually map their columns.
            this.showSeparateDateTimeFields(false);
        }
    }

    /**
     * Deletes the options in the field mapping dropdowns.
     * Should be called when a file is accepted/rejected.
    */
    unpopulateFields() {
        const children = Helpers.recursiveChildren(document.getElementById('field-mapping'));

        children.filter((e) => e.tagName.toLowerCase() == 'select')
            .forEach((selectField) => {
                selectField.innerHTML = '<option value="">Select a field...</option>';
            });
    }

    /**
     * Renders the messages in the chat container based on the preview data.
     */
    messages() {
        const chatContainer = document.getElementById('messages');
        let previousAuthor = null;
        let firstMessage = true;
        let messageElement;

        this.previewData.forEach((msg) => {
            if (msg.name != previousAuthor) {
                messageElement = document.createElement('div');
                messageElement.className = 'message';
                if (!firstMessage) messageElement.classList.add('d-none');

                const dateTime = document.createElement('div');
                dateTime.className = 'date-time';
                dateTime.textContent = `${msg.date ? msg.date : ''} ${msg.time ? msg.time : ''}`;

                const username = document.createElement('div');
                username.className = 'username';
                username.textContent = msg.name;
                messageElement.appendChild(dateTime);
                messageElement.appendChild(username);
            }

            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';

            if (msg.body && msg.body.raw_content) {
                messageContent.textContent = msg.body.raw_content;
            } else if (msg.message) {
                messageContent.textContent = msg.message;
            } else if (msg.content) {
                messageContent.textContent = msg.content;
            } else if (msg.comment) {
                messageContent.textContent = msg.comment;
            } else if (msg.body) {
                messageContent.textContent = msg.body;
            } else {
                console.log('Error: no message content found');
                console.log(msg);
            }

            messageElement.appendChild(messageContent);
            if (msg.name == previousAuthor) {
                messageContent.insertAdjacentHTML('beforebegin', '<br>');
                messageContent.classList.add('mt-1');
            }

            chatContainer.appendChild(messageElement);
            previousAuthor = msg.name;
            firstMessage = false;
        });
    }

    /**
     * Returns the preview data.
     * @return {Array} The preview data.
    */
    getPreviewData() {
        return this.previewData;
    }

    /**
     * Sets whether to show separate date and time fields.
     * @param {boolean} show - Indicates whether to show separate date and time fields.
     */
    showSeparateDateTimeFields(show) {
        if (show) {
            Helpers.replaceClass('message-1f', 'd-block', 'd-none');
            Helpers.replaceClass('message-2f-1', 'd-none', 'd-block');
            Helpers.replaceClass('message-2f-2', 'd-none', 'd-block');
        } else {
            Helpers.replaceClass('message-2f-1', 'd-block', 'd-none');
            Helpers.replaceClass('message-1f', 'd-none', 'd-block');
            Helpers.replaceClass('message-2f-2', 'd-block', 'd-none');
        }
        document.getElementById('separate-dt-fields').checked = show;
    }
}

window.onload = () => {
    /**
     * Creates a new instance of FileUpload and assigns it to the variable 'file'.
     * @type {FileUpload}
     */
    const file = new FileUpload();

    document.getElementById('upload-label').control.addEventListener('input', () => {
        file.upload();
    });

    document.getElementById('accept-btn').addEventListener('click', (e) => {
        e.preventDefault();
        file.accept();
    });

    document.getElementById('reject-btn').addEventListener('click', (e) => {
        e.preventDefault();
        file.reject();
    });

    document.getElementById('separate-dt-fields').addEventListener('change', (e) => {
        file.showSeparateDateTimeFields(e.currentTarget.checked);
    });

    document.getElementById('message-sender').addEventListener('change', (e) => {
        for (let x = 0; x < document.getElementsByClassName('username').length; x++) {
            document.getElementsByClassName('username')[x].textContent =
                file.getPreviewData()[x][e.currentTarget.value];
        }
    });

    document.getElementById('message-body').addEventListener('change', (e) => {
        for (let x = 0; x < document.getElementsByClassName('message-content').length; x++) {
            document.getElementsByClassName('message-content')[x].textContent =
                file.getPreviewData()[x][e.currentTarget.value];
        }
    });

    document.getElementById('message-date').addEventListener('change', (e) => {
        for (let x = 0; x < document.getElementsByClassName('date-time').length; x++) {
            /* eslint-disable */
            document.getElementsByClassName('date-time')[x].textContent =
                `${file.getPreviewData()[x][e.currentTarget.value]}
            ${file.getPreviewData()[x][
                document.getElementById('message-time').value ?
                    document.getElementById('message-time').value : 'time'
                ]}`;
            /* eslint-enable */
        }
    });

    document.getElementById('message-time').addEventListener('change', (e) => {
        for (let x = 0; x < document.getElementsByClassName('date-time').length; x++) {
            /* eslint-disable */
            document.getElementsByClassName('date-time')[x].textContent =
                `${file.getPreviewData()[x][
                document.getElementById('message-date').value ?
                    document.getElementById('message-date').value : 'date'
                ]}
            ${file.getPreviewData()[x][e.currentTarget.value]} `;
            /* eslint-enable */
        }
    });

    document.getElementById('message-timestamp').addEventListener('change', (e) => {
        for (let x = 0; x < document.getElementsByClassName('date-time').length; x++) {
            document.getElementsByClassName('date-time')[x].textContent =
                file.getPreviewData()[x][e.currentTarget.value];
        }
    });

    document.getElementById('show-messages').addEventListener('click', (e) => {
        e.preventDefault();
        for (const message of document.getElementsByClassName('message')) {
            message.classList.remove('d-none');
        }
        e.currentTarget.classList.add('d-none');
    });
};


