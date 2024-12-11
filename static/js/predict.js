$(function () {
    console.log('Initializing date pickers and populating dataset select dropdown on page load');

    // Initialize date pickers
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
    });

    // Populate dataset select dropdown on page load
    populateDatasetSelect();

    // Handle dataset selection change
    $('#dataset-select').change(function () {
        const selectedDataset = $(this).val();
        console.log('Dataset selected:', selectedDataset);
        if (selectedDataset) {
            fetchPreviewData(selectedDataset);
        } else {
            updatePreviewTable([], []);
        }
    });

    // Bind event handlers to prediction buttons
    $('#batch-predict-button').click(makeBatchPrediction);
    $('#individual-predict-button').click(makeIndividualPrediction);

    // Event handler for TPIN field to load dynamic fields
    $('#TPIN').blur(loadDynamicFields);

    // Handle transaction ID selection change to load specific date fields
    $('#Transaction_ID').change(loadDateFields);
});

function populateDatasetSelect() {
    console.log('Fetching list of preprocessed datasets');
    fetch('/list-preprocessed-datasets')
        .then(response => response.json())
        .then(data => {
            console.log('Received dataset list:', data.datasets);
            if (data.datasets) {
                const datasetSelect = $('#dataset-select');
                datasetSelect.empty().append('<option value="">Select a Dataset</option>');
                data.datasets.forEach(dataset => {
                    datasetSelect.append(new Option(dataset, dataset));
                });
            } else {
                console.error('Error fetching dataset names:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching datasets:', error);
        });
}

function fetchPreviewData(dataset) {
    console.log(`Fetching preview data for dataset: ${dataset}`);

    fetch(`/preview-preprocessed-dataset?dataset=${encodeURIComponent(dataset)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Received preview data:', data);
            if (data.columns && data.preview_data) {
                updatePreviewTable(data.columns, data.preview_data);
            } else {
                console.error('Error fetching preview data:', data.error);
                updatePreviewTable([], []);
            }
        })
        .catch(error => {
            console.error('Error fetching preview data:', error);
            updatePreviewTable([], []);
        });
}

function updatePreviewTable(columns, data) {
    console.log('Updating preview table with columns:', columns);
    console.log('And data:', data);

    const tableHeader = $('#table-header');
    const tableBody = $('#table-body');

    tableHeader.empty();
    tableBody.empty();

    if (columns.length > 0) {
        columns.forEach(column => {
            $('<th>').text(column).appendTo(tableHeader);
        });

        if (data.length > 0) {
            data.forEach(row => {
                const tr = $('<tr>');
                row.forEach(cell => {
                    $('<td>').text(cell).appendTo(tr);
                });
                tr.appendTo(tableBody);
            });
        } else {
            $('<tr>').append($('<td>').attr('colspan', columns.length).text('No data available.')).appendTo(tableBody);
        }
    } else {
        $('<tr>').append($('<td>').attr('colspan', 9).text('No data available.')).appendTo(tableBody);
    }
}

function makeBatchPrediction() {
    const selectedDataset = $('#dataset-select').val();
    if (!selectedDataset) {
        alert('Please select a dataset for batch prediction.');
        return;
    }

    const spinner = $('#loading-spinner');
    const resultElement = $('#prediction-result');
    const analyzeButton = $('#analyze-results-button');
    const noResultsMessage = $('#no-results-message');

    spinner.show();
    resultElement.html('<p>Loading prediction, please wait...</p>');
    analyzeButton.hide();
    noResultsMessage.hide();

    console.log('Making batch prediction with dataset:', selectedDataset);

    const batchData = {
        filename: selectedDataset  // Assuming you're sending a filename for batch prediction
    };

    fetch('/predict-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(batchData)
    })
    .then(response => {
        console.log('Batch prediction response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Error: ${response.statusText} - ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Received batch prediction data:', data);
        if (data.predictions) {
            const fraudulentCount = data.predictions.filter(prediction => prediction === 1).length;
            resultElement.html(`<p class="text-success"><strong>Batch Prediction Result:</strong> ${fraudulentCount} transactions were predicted as potentially fraudulent</p>`);

            if (fraudulentCount > 0) {
                analyzeButton.show();
            } else {
                noResultsMessage.show();
            }
        } else {
            resultElement.html('<p>No predictions returned.</p>');
            noResultsMessage.show();
        }
    })
    .catch(error => {
        console.error('Error making batch prediction:', error);
        resultElement.html(`<p class="text-danger">Error making batch prediction: ${error.message}.</p>`);
        noResultsMessage.show();
    })
    .finally(() => spinner.hide());
}

function makeIndividualPrediction() {
    const inputData = {
        TPIN: $('#TPIN').val(),
        LOCATION: $('#LOCATION').val(),
        TAX_TYPE: $('#TAX_TYPE').val(),
        Transaction_ID: $('#Transaction_ID').val(),
        Period_From_year: $('#Period_From_year').val(),
        Period_From_month: $('#Period_From_month').val(),
        Period_From_day: $('#Period_From_day').val(),
        Period_To_year: $('#Period_To_year').val(),
        Period_To_month: $('#Period_To_month').val(),
        Period_To_day: $('#Period_To_day').val(),
        Payment_Method: $('#Payment_Method').val(),
        Payment_Amount: $('#Payment_Amount').val(),
        Payment_Date_year: $('#Payment_Date_year').val(),
        Payment_Date_month: $('#Payment_Date_month').val(),
        Payment_Date_day: $('#Payment_Date_day').val(),
    };

    console.log('Making individual prediction with input data:', inputData);

    const spinner = $('#loading-spinner');
    const resultElement = $('#prediction-result');
    const analyzeButton = $('#analyze-results-button');
    const noResultsMessage = $('#no-results-message');

    spinner.show();
    resultElement.html('<p>Loading prediction, please wait...</p>');
    analyzeButton.hide();
    noResultsMessage.hide();

    fetch('/predict-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_data: inputData })
    })
    .then(response => {
        console.log('Individual prediction response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Error: ${response.statusText} - ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Received individual prediction data:', data);

        const prediction = data.predictions;
        if (prediction === 1) {
            analyzeButton.show();
        } else {
            noResultsMessage.show();
        }
        resultElement.html(`<p><strong>Prediction Result:</strong> ${JSON.stringify(prediction)}</p>`);
    })
    .catch(error => {
        console.error('Error making individual prediction:', error);
        resultElement.html(`<p class="text-danger">Error making prediction: ${error.message}</p>`);
        noResultsMessage.show();
    })
    .finally(() => spinner.hide());
}

function loadDynamicFields() {
    const tpin = $('#TPIN').val();
    const selectedDataset = $('#dataset-select').val();
    if (!tpin || !selectedDataset) return;

    console.log(`Fetching dynamic fields for TPIN: ${tpin} from dataset: ${selectedDataset}`);

    fetch(`/get-dynamic-fields?tpin=${tpin}&dataset=${encodeURIComponent(selectedDataset)}`)
        .then(response => {
            console.log('Dynamic fields fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Received dynamic fields data:', data);
            if (data.error) {
                alert(data.error);
                return;
            }
            populateSelect('LOCATION', data.locations);
            populateSelect('TAX_TYPE', data.tax_types);
            populateSelect('Transaction_ID', data.transaction_ids);
            populatePaymentDate(data.payment_dates);
            populatePeriodFromDate(data.period_from_dates);
            populatePeriodToDate(data.period_to_dates);
        })
        .catch(error => {
            console.error('Error fetching dynamic fields:', error);
        });
}

function loadDateFields() {
    const transactionId = $('#Transaction_ID').val();
    if (!transactionId) return;

    console.log(`Fetching transaction dates for Transaction ID: ${transactionId}`);

    fetch(`/get-transaction-dates?transaction_id=${transactionId}`)
        .then(response => {
            console.log('Transaction dates fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Received transaction dates data:', data);
            if (data.error) {
                alert(data.error);
                return;
            }
            populatePeriodFromDate(data.period_from);
            populatePeriodToDate(data.period_to);
            populatePaymentDate(data.payment_date);
        })
        .catch(error => {
            console.error('Error fetching transaction dates:', error);
        });
}

function populateSelect(elementId, options) {
    console.log(`Populating select element: ${elementId} with options:`, options);

    const selectElement = $(`#${elementId}`);
    selectElement.empty().append('<option value="">Select</option>');
    options.forEach(option => {
        selectElement.append(new Option(option, option));
    });
}

function populateField(elementId, value) {
    console.log(`Populating field: ${elementId} with value: ${value}`);

    if (value !== null && value !== undefined) {
        $(`#${elementId}`).val(value);
    }
}

function populatePaymentDate(paymentDates) {
    console.log('Populating payment dates:', paymentDates);

    if (paymentDates) {
        $('#Payment_Date_year').val(paymentDates.year);
        $('#Payment_Date_month').val(paymentDates.month);
        $('#Payment_Date_day').val(paymentDates.day);
    }
}

function populatePeriodFromDate(periodFromDates) {
    console.log('Populating period from dates:', periodFromDates);

    if (periodFromDates) {
        $('#Period_From_year').val(periodFromDates.year);
        $('#Period_From_month').val(periodFromDates.month);
        $('#Period_From_day').val(periodFromDates.day);
    }
}

function populatePeriodToDate(periodToDates) {
    console.log('Populating period to dates:', periodToDates);

    if (periodToDates) {
        $('#Period_To_year').val(periodToDates.year);
        $('#Period_To_month').val(periodToDates.month);
        $('#Period_To_day').val(periodToDates.day);
    }
}