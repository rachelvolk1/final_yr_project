let currentPage = 1;
const rowsPerPage = 20;  // Default rows per page
let filteredData = [];
let originalData = [];

window.onload = function() {
    const section = document.querySelector('.section');
    if (section) {
        section.style.display = 'block';  // Ensure the section is displayed
    }

    // Automatically load dataset when the page is loaded
    const filename = "{{ filename|tojson }}";  // Safely pass Flask variable into JS
    if (filename) {
        $('#status-message').text("Loading dataset...");

        // Fetch dataset using AJAX
        $.ajax({
            url: `/api/preview/${filename}`,
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                originalData = response;
                filteredData = [...originalData];  // Copy original data for filtering
                renderTable(currentPage, filteredData);
                $('#status-message').text("Dataset loaded successfully.");
            },
            error: function(xhr, status, error) {
                $('#status-message').text('Error loading dataset: ' + error);
            }
        });
    } else {
        $('#status-message').text("No dataset to load.");
    }
};

function renderTable(page, data) {
    const tableBody = document.getElementById('table-body');
    tableBody.innerHTML = '';  // Clear the table

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(row => {
        const rowElement = `
            <tr>
                <td>${row.TPIN}</td>
                <td>${row.LOCATION}</td>
                <td>${row['TAX TYPE']}</td>
                <td>${row['Transaction ID']}</td>
                <td>${row['Period From']}</td>
                <td>${row['Period To']}</td>
                <td>${row['Payment Method']}</td>
                <td>${row['Payment Amount']}</td>
                <td>${row['Payment Date']}</td>
            </tr>`;
        tableBody.innerHTML += rowElement;
    });
}

function filterData() {
    const searchTerm = document.getElementById('search-bar').value.toLowerCase();
    const filterDate = document.getElementById('filter-date').value;

    filteredData = originalData.filter(row => {
        const matchesSearch = row.TPIN.toLowerCase().includes(searchTerm) ||
            row.LOCATION.toLowerCase().includes(searchTerm) ||
            row['TAX TYPE'].toLowerCase().includes(searchTerm) ||
            row['Transaction ID'].toLowerCase().includes(searchTerm);
        
        const matchesDate = !filterDate || row['Payment Date'] === filterDate;
        return matchesSearch && matchesDate;
    });

    renderTable(currentPage, filteredData);
}

// Pagination Controls
$('#prev-page').on('click', function() {
    if (currentPage > 1) {
        currentPage--;
        renderTable(currentPage, filteredData);
        document.getElementById('page-number').textContent = currentPage;
    }
});

$('#next-page').on('click', function() {
    if (currentPage * rowsPerPage < filteredData.length) {
        currentPage++;
        renderTable(currentPage, filteredData);
        document.getElementById('page-number').textContent = currentPage;
    }
});

// Search and filter
$('#search-bar').on('input', filterData);
$('#filter-date').on('change', filterData);
