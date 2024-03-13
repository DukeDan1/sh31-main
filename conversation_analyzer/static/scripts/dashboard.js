'use strict';
/* exported selectDocument */
/**
 * Sets the selected document value and submits the form.
 * @param {string} selectedDocument - The selected document value.
 */
function selectDocument(selectedDocument) {
    document.getElementById('selectDocument').value = selectedDocument;
    document.getElementById('dropdown_form').submit();
}
