/* global agGrid */
'use strict';

/**
 * Populates the grid using JSON data contained within an element.
 * @param {string} dataElement - ID of script element containing JSON data.
 * @param {string} gridElement - ID of grid div element.
 */
function displayGrid(dataElement, gridElement) {
    const previewDataElement = document.getElementById(dataElement);
    const previewRowData = JSON.parse(previewDataElement.textContent);

    const firstPreviewRowData = typeof previewRowData.at(0) === 'undefined' ?
        {} : previewRowData[0];
    const previewColumnDefs = Object.keys(firstPreviewRowData)
        .map((key) => Object({field: key}));

    const previewGridOptions = {
        columnDefs: previewColumnDefs,
        rowData: previewRowData,
    };

    new agGrid.Grid(document.getElementById(gridElement), previewGridOptions);
    previewGridOptions.api.sizeColumnsToFit();
}

document.addEventListener('DOMContentLoaded', () => {
    displayGrid('concept-analysis-data', 'concept-analysis-grid');
    displayGrid('category-analysis-data', 'category-analysis-grid');
});
