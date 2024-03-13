'use strict';
/* global Helpers */
/* exported deleteDocument */

/**
 * Retrieves search results based on the provided query.
 * If wildcard is set to true, it retrieves all files owned by the user.
 * If wildcard is set to false, it retrieves results based on
 * the query entered in the search input field.
 * @param {boolean} [wildcard=false] - Indicates whether to retrieve all results or not.
 */
function getSearchResults(wildcard = false) {
    let query = '%';
    if (!wildcard) {
        query = document.getElementById('search-input').value;
    }

    document.getElementById('search-results').innerHTML = `
    <div class="text-center">
        <div class="spinner-border text-primary mb-3" role="status"></div>
    </div>`;

    Helpers.apiCall(
        '/api/document-search',
        'POST',
        {
            query: query,
            show_all: wildcard,
        },
    ).then((response) => response.json())
        .then((results) => {
            const searchResults = document.getElementById('search-results');
            searchResults.innerHTML = '';
            if (results.success) {
                results = results.result;
                if (results.length === 0) {
                    searchResults.innerHTML = '<p>No results found</p>';
                } else {
                    results.forEach((result) => {
                        searchResults.innerHTML += `
                        <li class="list-group-item">
                            <a href="${result.url}" class="document-link">
                            <span class="icon">&#xe873;</span>
                                ${result.display_name}
                            </a>
                            <hr>
                            <button 
                            class="btn btn-danger" 
                            onclick="deleteDocument('${result.file_name}', event);">Delete</button>
                        </li>
                        `;
                    });
                }
            } else {
                searchResults.innerHTML = Helpers.generateAlert(results.message, 'danger');
            }
        })
        .catch((error) => {
            console.error(error);
            document.getElementById('search-results').innerHTML = Helpers.generateAlert(
                'An error has occurred while fetching the search results. Please try again.',
                'danger',
            );
        });
}

/**
 * Deletes a document.
 * @param {string} filename - The name of the file to be deleted.
 * @param {Event} event - The event object triggered by the delete button.
 */
function deleteDocument(filename, event) {
    event.preventDefault();
    const button = event.target;
    const parent = button.parentElement;

    button.classList.add('disabled');
    button.innerHTML = `
    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    `;

    Helpers.apiCall(
        '/api/upload-file/reject',
        'POST',
        {
            file_name: filename,
        },
    ).then((response) => response.json())
        .then((response) => {
            if (response.success) {
                parent.outerHTML = Helpers.generateAlert(
                    'Document successfully deleted',
                    'success',
                );
            } else {
                button.innerHTML = 'Delete';
                button.classList.remove('disabled');
                parent.innerHTML += Helpers.generateAlert(response.error, 'danger');
            }
        })
        .catch((error) => {
            button.innerHTML = 'Delete';
            button.classList.remove('disabled');
            parent.innerHTML += Helpers.generateAlert(
                'An error has occurred while deleting the document. Please try again.',
                'danger',
            );
        });
}

document.addEventListener('DOMContentLoaded', () => {
    getSearchResults(true);

    document.getElementById('search-input').addEventListener('input', () =>{
        if (document.getElementById('search-input').value === '') {
            getSearchResults(true);
        } else {
            getSearchResults();
        }
    });

    document.getElementById('search').addEventListener('submit', (event) => {
        event.preventDefault();
        getSearchResults();
    });
});
