console.log("preprocessing.js is loaded");

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded and parsed");
    fetchDatasets();

    // Refetch datasets when the dropdown is focused
    document.getElementById("dataset-select").addEventListener("focus", fetchDatasets);

    // Handle dataset selection change
    document.getElementById("dataset-select").addEventListener("change", function() {
        const datasetSelected = this.value;
        if (datasetSelected) {
            fetchDatasetPreview(datasetSelected);
        }
    });

    // Handle the preprocessing button click
    document.getElementById("start-preprocessing").addEventListener("click", function() {
        const datasetSelected = document.getElementById("dataset-select").value;
        if (!datasetSelected) {
            document.getElementById("status-message").textContent = "Please select a dataset to preprocess.";
            document.getElementById("status-message").classList.add("text-danger");
            console.warn("No dataset selected for preprocessing.");
            return;
        }

        // Log the selected dataset
        console.log(`Selected dataset for preprocessing: ${datasetSelected}`);

        document.getElementById("status-message").textContent = "Starting preprocessing...";
        document.getElementById("status-message").classList.remove("text-danger");
        document.getElementById("status-message").classList.add("text-info");
        document.getElementById("loading-spinner").style.display = "block";

        fetch("/preprocessing", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                "dataset": datasetSelected
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok: " + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            document.getElementById("status-message").textContent = "Preprocessing completed successfully!";
            document.getElementById("status-message").classList.remove("text-info");
            document.getElementById("status-message").classList.add("text-success");
            document.getElementById("loading-spinner").style.display = "none";
            console.log("Preprocessing result:", data.result);
        })
        .catch(error => {
            document.getElementById("status-message").textContent = "An error occurred during preprocessing: " + error.message;
            document.getElementById("status-message").classList.remove("text-info");
            document.getElementById("status-message").classList.add("text-danger");
            document.getElementById("loading-spinner").style.display = "none";
            console.error("Error:", error);
        });
    });
});

function fetchDatasets() {
    console.log("Fetching datasets");
    fetch("/list-datasets")
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok: " + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("Data received: ", data);
            if (data && data.datasets) {
                const datasetSelect = document.getElementById("dataset-select");
                datasetSelect.innerHTML = '<option value="">Select a Dataset</option>';
                data.datasets.forEach(dataset => {
                    console.log("Adding dataset:", dataset);
                    const option = document.createElement("option");
                    option.value = dataset;
                    option.textContent = dataset;
                    datasetSelect.appendChild(option);
                });
            } else {
                console.warn("No datasets found in the response");
            }
        })
        .catch(error => {
            console.error("Error fetching datasets:", error);
            alert("Error fetching datasets: " + error.message);
        });
}

function fetchDatasetPreview(dataset) {
    fetch(`/preview-clean-dataset?dataset=${dataset}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.preview_data && data.columns) {
                updatePreviewTable(data.columns, data.preview_data);
            } else {
                console.warn("No preview data found in the response");
                updatePreviewTable([], []);
            }
        })
        .catch(error => {
            console.error("Error fetching dataset preview:", error);
            alert("Error fetching dataset preview: " + error.message);
        });
}

function updatePreviewTable(columns, data) {
    const tableHeader = document.getElementById('table-header');
    const tableBody = document.getElementById('table-body');

    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';

    if (columns.length > 0) {
        columns.forEach((column) => {
            const th = document.createElement('th');
            th.textContent = column;
            tableHeader.appendChild(th);
        });

        if (data.length > 0) {
            data.forEach((row) => {
                const tr = document.createElement('tr');
                row.forEach((cell) => {
                    const td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        } else {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = columns.length;
            td.className = 'text-center';
            td.textContent = 'No data available.';
            tr.appendChild(td);
            tableBody.appendChild(tr);
        }
    } else {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 9;
        td.className = 'text-center';
        td.textContent = 'No data available.';
        tr.appendChild(td);
        tableBody.appendChild(tr);
    }
}