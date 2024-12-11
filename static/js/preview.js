let currentPage = 1;
const rowsPerPage = 20;
let filteredData = [];
let originalData = [];

$(document).ready(function() {
    let datasetId = "{{ instance_id }}";
    let fileName = "{{ filename }}";

    console.log("Dataset ID:", datasetId);
    console.log("File Name:", fileName);

    $.ajax({
        url: `/api/preview/${datasetId}/${fileName}`,  // Ensure this is correctly formatted
        method: 'GET',
        beforeSend: function() {
            console.log("Starting AJAX request to fetch preview data.");
            $('#loading-spinner').show();
        },
        success: function(response) {
            console.log("AJAX request succeeded. Response received:", response);
            displayPreviewData(response);
            $('#loading-spinner').hide();
        },
        error: function(xhr, status, error) {
            console.error("AJAX request failed. Status:", status, "Error:", error);
            console.error("Response:", xhr.responseText);
            $('#status-message').text('An error occurred while fetching the preview.');
            $('#loading-spinner').hide();
        }
    });

    // Function to display the preview data
    function displayPreviewData(data) {
        console.log("Displaying preview data:", data);
        originalData = data;
        filteredData = data;
        renderTable(currentPage, data);
    }

    // Function to render the table with paginated data
    function renderTable(page, data) {
        console.log("Rendering table. Page:", page, "Data length:", data.length);
        const tableBody = $('#table-body');
        const tableHeader = $('#table-header');

        tableBody.empty();
        tableHeader.empty();

        if (data.length > 0) {
            // Populate table headers dynamically
            const headers = Object.keys(data[0]);
            const headerRow = $('<tr></tr>');
            headers.forEach(function(header) {
                headerRow.append(`<th>${header}</th>`);
            });
            tableHeader.append(headerRow);

            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            const paginatedData = data.slice(start, end);

            paginatedData.forEach(row => {
                const rowElement = $('<tr></tr>');
                headers.forEach(header => {
                    rowElement.append(`<td>${row[header] !== null ? row[header] : ''}</td>`);
                });
                tableBody.append(rowElement);
            });
        } else {
            console.log("No data available to display.");
            tableBody.append('<tr><td colspan="9">No data available</td></tr>');
        }

        // Update page number display
        $('#page-number').text(currentPage);
        $('#total-pages').text(Math.ceil(data.length / rowsPerPage));
    }

    // Function to filter data based on search term and date
    function filterData() {
        console.log("Filtering data.");
        const searchTerm = $('#search-bar').val().toLowerCase();
        const filterDate = $('#filter-date').val();

        console.log("Filter criteria - Search Term:", searchTerm, "Filter Date:", filterDate);

        filteredData = originalData.filter(row => {
            const matchesSearch = row.TPIN.toLowerCase().includes(searchTerm) ||
                row.LOCATION.toLowerCase().includes(searchTerm) ||
                row['TAX TYPE'].toLowerCase().includes(searchTerm) ||
                row['Transaction ID'].toLowerCase().includes(searchTerm);

            const matchesDate = !filterDate || row['Payment Date'] === filterDate;
            return matchesSearch && matchesDate;
        });

        console.log("Filtered data length:", filteredData.length);

        currentPage = 1;  // Reset to first page whenever filtering is applied
        renderTable(currentPage, filteredData);
    }

    // Pagination Controls
    $('#prev-page').on('click', function() {
        if (currentPage > 1) {
            console.log("Navigating to previous page.");
            currentPage--;
            renderTable(currentPage, filteredData);
        } else {
            console.log("Already on the first page. Cannot navigate further back.");
        }
    });

    $('#next-page').on('click', function() {
        if (currentPage * rowsPerPage < filteredData.length) {
            console.log("Navigating to next page.");
            currentPage++;
            renderTable(currentPage, filteredData);
        } else {
            console.log("Already on the last page. Cannot navigate further forward.");
        }
    });

    // Search and filter input listeners
    $('#search-bar').on('input', filterData);
    $('#filter-date').on('change', filterData);
});