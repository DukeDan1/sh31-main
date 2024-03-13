'use strict';
/* global Helpers */
/* global agGrid */
/* exported displayAnalysis */
/* exported scrollToMessage */

/**
 * Represents the message analysis.
 * @class
 */
class MessageAnalysis {
    /**
     * Represents the message analysis.
     * @constructor
     * @param {string} messageID - The ID of the message to analyse.
     */
    constructor(messageID) {
        this.messageID = messageID;
        this.display_element = 'md-'+messageID;
        this.fetchMessage();
    }

    /**
     * Show loading wheel.
     */
    showLoadingWheel() {
        Helpers.changeInnerHTML(
            this.display_element,
            '<div class="spinner-border text-info mb-3" role="status"></div>',
        );
        Helpers.removeClass(this.display_element, 'd-none');
    }

    /**
     * Fetches the message from the API.
     */
    fetchMessage() {
        this.showLoadingWheel();
        Helpers.apiCall(`/api/message/${this.messageID}`, 'GET')
            .then((response) => response.json())
            .then((message) => {
                if (message.pending) {
                    setTimeout(this.fetchMessage.bind(this), 1000);
                } else {
                    this.message_analysis = message;
                    this.displayMessageAnalysis();
                }
            })
            .catch((error) => {
                this.message_analysis = {
                    error: true,
                    message: 'An error has occurred while fetching this message. Please try again.',
                };
                this.displayMessageAnalysis();
            });
    }

    /**
     * Displays the message analysis.
     */
    displayMessageAnalysis() {
        Helpers.removeClass(this.display_element, 'd-none');
        if (this.message_analysis && !this.message_analysis.error) {
            Helpers.changeInnerHTML(this.display_element, this.formatMessageAnalysis());
            this.createAgGrid(
                this.message_analysis.concept_analysis_data,
                `${this.messageID}-concept-analysis-grid`,
            );
        } else {
            Helpers.changeInnerHTML(
                this.display_element,
                Helpers.generateAlert(this.message_analysis.message, 'danger'),
            );
        }
    }

    /**
     * Format message analysis.
     * @return {string} - The formatted message analysis.
     */
    formatMessageAnalysis() {
        return `
        <hr class="mb-1"/>
        <p><b>Risk Level:</b> ${this.message_analysis.message_risk_score}</p>
        <p><b>Sentiment:</b> ${this.message_analysis.message_sentiment}</p>
        <div id="${this.messageID}-concept-analysis">
            <b>Concept Analysis:</b>
            <div id="${this.messageID}-concept-analysis-grid" 
            class="ag-theme-alpine analysis-grid"></div>
        </div>
        `;
    }

    /**
     * Creates an ag-Grid with the provided data and attaches it to the specified grid element.
     * @param {Array} data - The data to be displayed in the ag-Grid.
     * @param {string} gridElementId - The ID of the HTML element where the ag-Grid will be attached
     */
    createAgGrid(data, gridElementId) {
        if (!data) {
            Helpers.addClass(
                gridElementId.slice(0, gridElementId.length-5), 'd-none',
            );
        } else {
            const rowData = typeof data.at(0) === 'undefined' ?
                {} : data[0];
            const columnDefs = Object.keys(rowData)
                .filter((key) => key !== 'profile_id')
                .map((key) => {
                    return {
                        field: key,
                        sortable: true,
                        filter: true,
                        resizable: true,
                        cellRenderer: (params) => {
                            if (params.data.profile_id) {
                                return `<a href="/profile/${params.data.profile_id}/"
                                class="text-decoration-underline link-primary" 
                                onclick="event.stopPropagation();">
                                ${params.value}
                                </a>`;
                            } else {
                                return params.value;
                            }
                        },
                    };
                });

            const gridOptions = {
                columnDefs,
                rowData: data,
                rowHeight: 30,
                headerHeight: 30,
            };

            new agGrid.Grid(document.getElementById(gridElementId), gridOptions);
            gridOptions.api.sizeColumnsToFit();
        }
    }
}

window.message_dict = {};


/**
 * Handler for when the user clicks on a message.
 * Displays the message analysis and stores it.
 * @param {string} messageID - The ID of the message.
 * @param {Event} event - The event object.
 */
function displayAnalysis(messageID, event) {
    event.preventDefault();

    if (window.message_dict[messageID]) {
        const element = document.getElementById('md-'+messageID);
        if (element.classList.contains('d-none')) {
            window.message_dict[messageID].displayMessageAnalysis();
        } else {
            Helpers.addClass('md-'+messageID, 'd-none');
        }
    } else {
        window.message_dict[messageID] = new MessageAnalysis(messageID);
    }
}

/**
 * Scrolls to the message with the specified ID.
 * @param {string} messageID - The ID of the message to scroll to.
 */
function scrollToMessage(messageID) {
    const element = document.getElementById('md-'+messageID);
    element.scrollIntoView();
}

/**
 * Checks if the content is overflowing horizontally.
 * Display the modal button instead of the right menu if it is.
 */
function checkOverflow() {
    const documentWidth = document.documentElement.scrollWidth;
    const viewportWidth = window.innerWidth;
    const documentListOpenSm = document.getElementById('document-list-open-sm');
    const documentListLg = document.getElementById('document-list-lg');

    if (documentWidth > viewportWidth) {
        // content is overflowing horizontally
        documentListOpenSm.classList.add('d-block');
        documentListOpenSm.classList.remove('d-none');
        documentListLg.classList.add('d-none');
        documentListLg.classList.remove('d-block');
    } else {
        // content is not overflowing horizontally
        documentListOpenSm.classList.add('d-none');
        documentListOpenSm.classList.remove('d-block');
        documentListLg.classList.add('d-block');
        documentListLg.classList.remove('d-none');
    }
}

/**
 * Jumps to the specified message index in the document view.
 * @param {number} messageIndex - The index of the message to jump to.
 * @param {Event} event - The event object (created when an element is clicked).
 */
function jumpToMessage(messageIndex, event=null) {
    if (event) {
        event.preventDefault();
    }

    const element = document.querySelector(`[data-index="${messageIndex}"]`);
    element.click();
    element.scrollIntoView();
}

window.onload = () => {
    checkOverflow();
    try {
        const myPlot = document.querySelector('.plotly-graph-div.js-plotly-plot');

        myPlot.on('plotly_click', function(plot) {
            jumpToMessage(plot.points[0].x);
        });
    } catch (error) {
        // If the plotly graph has not loaded, do nothing.
    }
};

window.onresize = checkOverflow;
