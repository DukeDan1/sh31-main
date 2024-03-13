'use strict';
/* global Helpers */
/* exported processFileNLPWithProgress */

/**
 * File name that is displayed by the progress bar currently.
 */
let currentProgressFileName = '';

/**
 * Starts NLP processing task for a document, changing progress indicator periodically.
 * @param {string} fileName - File name for the document being processed.
 * @param {boolean} shouldRefresh - Whether the page should refresh if 100% is reached.
 */
function processFileNLPWithProgress(fileName, shouldRefresh) {
    const pollUpdate = async (fileName, initial) => {
        if (currentProgressFileName !== fileName) return;
        const data = await (await Helpers.apiCall('/api/nlp-process', 'POST', {
            file_name: fileName,
            initial: initial,
        })).json();
        document.getElementById('progress-nlp').value = data.progress;
        if (data.progress == 100 && shouldRefresh) location.reload();
        else if (data.progress != 100) setTimeout(pollUpdate, 1000, fileName, false);
    };
    currentProgressFileName = fileName;
    pollUpdate(fileName, true);
}
