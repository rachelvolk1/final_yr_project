console.log("train.js is loaded");

window.onload = function() {
  const section = document.querySelector('#train-section');
  if (section) {
    section.style.display = 'block';
  } else {
    console.error("Cannot find element with id 'train-section'");
  }

  const submitButton = document.getElementById('submit-data-button');
  if (submitButton) {
    submitButton.style.display = 'none';
  }
};

document.addEventListener("DOMContentLoaded", function() {
  populateDatasetSelect();

  const datasetSelect = document.getElementById("dataset-select");
  datasetSelect.addEventListener("change", function() {
    const selectedDataset = this.value;
    if (selectedDataset) {
      console.log(`Selected dataset: ${selectedDataset}`);
      fetchPreviewData(selectedDataset);
    } else {
      updatePreviewTable([], []);
    }
    toggleStartTrainingButton();
  });

  const modelTypeSelect = document.getElementById("model-type");
  modelTypeSelect.addEventListener("change", function() {
    const selectedModelType = this.value;
    console.log(`Selected model type: ${selectedModelType}`);
    updateParametersForm(selectedModelType);
    toggleStartTrainingButton();
  });

  const startTrainingButton = document.getElementById("start-training");
  startTrainingButton.addEventListener("click", function() {
    const modelType = document.getElementById("model-type").value;
    const datasetName = document.getElementById("dataset-select").value;

    if (!modelType || !datasetName) {
      alert("Please select both a dataset and a model type first.");
      return;
    }

    document.getElementById("training-message").textContent = "Training in progress...";
    document.querySelector(".progress-bar").style.width = "0%";

    const formData = new FormData();
    formData.append("model-type", modelType);
    formData.append("dataset-name", datasetName);
    formData.append("hyperparameters", JSON.stringify(getHyperparameters(modelType)));

    console.log("Submitting training request:", {
      "model-type": modelType,
      "dataset-name": datasetName,
      "hyperparameters": getHyperparameters(modelType)
    });

    fetch("/train", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(`Error: ${data.error}`);
        document.getElementById("training-message").textContent = "Training failed.";
      } else {
        document.getElementById("training-message").textContent = "Training complete!";
        document.querySelector(".progress-bar").style.width = "100%";
        updateMetricsTable(data.metrics);
        toggleSaveDeployButton(true);
      }
    })
    .catch(error => {
      console.error('Error during training:', error);
      document.getElementById("training-message").textContent = "Training failed.";
    });
  });

  const saveDeployButton = document.getElementById("save-deploy");
  saveDeployButton.addEventListener("click", function() {
    const modelSelect = document.getElementById("saved-model-select");
    if (!modelSelect) {
      console.error('Error: Model select element not found.');
      alert('No model select element found.');
      return;
    }

    const modelName = modelSelect.value;

    if (!modelName) {
      alert("No model selected.");
      return;
    }

    fetch('/api/save-deploy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ model_name: modelName })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert("Model saved and deployed successfully!");
        saveDeployButton.textContent = "Model has been saved and deployed";
        toggleSaveDeployButton(false);
      } else {
        alert("Failed to save and deploy the model.");
      }
    })
    .catch(error => {
      console.error('Error saving and deploying model:', error);
      alert('An error occurred while saving and deploying the model.');
    });
  });
});

function toggleStartTrainingButton() {
  const datasetSelect = document.getElementById("dataset-select").value;
  const modelTypeSelect = document.getElementById("model-type").value;
  const startTrainingButton = document.getElementById("start-training");

  startTrainingButton.disabled = !(datasetSelect && modelTypeSelect);
}

function populateDatasetSelect() {
  fetch("/list-preprocessed-datasets")
    .then(response => response.json())
    .then(data => {
      if (data.datasets) {
        const datasetSelect = document.getElementById("dataset-select");
        datasetSelect.innerHTML = '<option value="">Select a Dataset</option>';
        data.datasets.forEach(dataset => {
          const option = document.createElement("option");
          option.value = dataset;
          option.textContent = dataset;
          datasetSelect.appendChild(option);
        });
        console.log("Datasets populated:", data.datasets);
      } else if (data.error) {
        console.error("Error fetching dataset names:", data.error);
      }
    })
    .catch(error => {
      console.error("Error fetching datasets:", error);
    });
}

function fetchPreviewData(dataset) {
  fetch(`/preview-preprocessed-dataset?dataset=${encodeURIComponent(dataset)}`)
    .then(response => response.json())
    .then(data => {
      if (data.columns && data.preview_data) {
        updatePreviewTable(data.columns, data.preview_data);
      } else if (data.error) {
        console.error("Error fetching preview data:", data.error);
        updatePreviewTable([], []);
      } else {
        console.error("Unexpected response format:", data);
        updatePreviewTable([], []);
      }
    })
    .catch(error => {
      console.error("Error fetching preview data:", error);
      updatePreviewTable([], []);
    });
}

function updatePreviewTable(columns, data) {
  const tableHeader = document.getElementById('table-header');
  const tableBody = document.getElementById('table-body');

  if (!tableHeader || !tableBody) {
    console.error("Table header or body element not found.");
    return;
  }

  tableHeader.innerHTML = '';
  tableBody.innerHTML = '';

  if (columns.length > 0) {
    columns.forEach(column => {
      const th = document.createElement('th');
      th.textContent = column;
      tableHeader.appendChild(th);
    });

    if (data.length > 0) {
      data.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(cell => {
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

function updateParametersForm(modelType) {
  if (!modelType) return;

  const modelParameters = {
    "Isolation Forest": {
      "n_estimators": 100,
      "max_samples": "auto",
      "contamination": "auto",
      "max_features": 1.0,
      "bootstrap": false,
      "random_state": null
    },
    "One-Class SVM": {
      "kernel": "rbf",
      "nu": 0.5,
      "gamma": "scale",
      "degree": 3,
      "coef0": 0.0,
      "tol": 1e-3,
      "cache_size": 200,
      "shrinking": true,
      "verbose": false
    },
    "Random Forest": {
      "n_estimators": 100,
      "max_depth": 10,
      "min_samples_split": 2,
      "min_samples_leaf": 1,
      "max_features": 'sqrt',
      "random_state": 1,
      "bootstrap": true
    }
  };

  const parametersConfig = modelParameters[modelType];
  if (!parametersConfig) return;

  const parametersDiv = document.getElementById('model-parameters');
  parametersDiv.innerHTML = '';

  Object.entries(parametersConfig).forEach(([parameter, defaultValue]) => {
    const parameterDiv = document.createElement('div');
    parameterDiv.className = 'form-group';

    const label = document.createElement('label');
    label.htmlFor = parameter;
    label.textContent = `${parameter}:`;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = parameter;
    input.id = parameter;
    input.value = defaultValue;

    parameterDiv.appendChild(label);
    parameterDiv.appendChild(input);

    parametersDiv.appendChild(parameterDiv);
  });
}

function toggleSaveDeployButton(enabled) {
  const saveDeployButton = document.getElementById('save-deploy');
  saveDeployButton.disabled = !enabled;
}

function updateMetricsTable(metrics) {
  const metricsBody = document.getElementById('metrics-body');

  if (!metricsBody) {
    console.error("Metrics body element not found.");
    return;
  }

  metricsBody.innerHTML = '';

  if (metrics && typeof metrics === 'object' && Object.keys(metrics).length > 0) {
    for (const [metric, value] of Object.entries(metrics)) {
      const tr = document.createElement('tr');
      const tdMetric = document.createElement('td');
      tdMetric.textContent = metric;
      const tdValue = document.createElement('td');
      tdValue.textContent = value.toFixed ? value.toFixed(2) : value;
      tr.appendChild(tdMetric);
      tr.appendChild(tdValue);
      metricsBody.appendChild(tr);
    }
  } else {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 2;
    td.className = 'text-center';
    td.textContent = 'No metrics available.';
    tr.appendChild(td);
    metricsBody.appendChild(tr);
  }
}

function getHyperparameters(modelType) {
  const parametersDiv = document.getElementById('model-parameters');
  const inputs = parametersDiv.querySelectorAll('input');
  let hyperparameters = {};

  inputs.forEach(input => {
    hyperparameters[input.name] = input.value;
  });

  return hyperparameters;
}console.log("train.js is loaded");

window.onload = function() {
  const section = document.querySelector('#train-section');
  if (section) {
    section.style.display = 'block';
  } else {
    console.error("Cannot find element with id 'train-section'");
  }

  const submitButton = document.getElementById('submit-data-button');
  if (submitButton) {
    submitButton.style.display = 'none';
  }
};

document.addEventListener("DOMContentLoaded", function() {
  populateDatasetSelect();

  const datasetSelect = document.getElementById("dataset-select");
  datasetSelect.addEventListener("change", function() {
    const selectedDataset = this.value;
    if (selectedDataset) {
      console.log(`Selected dataset: ${selectedDataset}`);
      fetchPreviewData(selectedDataset);
    } else {
      updatePreviewTable([], []);
    }
    toggleStartTrainingButton();
  });

  const modelTypeSelect = document.getElementById("model-type");
  modelTypeSelect.addEventListener("change", function() {
    const selectedModelType = this.value;
    console.log(`Selected model type: ${selectedModelType}`);
    updateParametersForm(selectedModelType);
    toggleStartTrainingButton();
  });

  const startTrainingButton = document.getElementById("start-training");
  startTrainingButton.addEventListener("click", function() {
    const modelType = document.getElementById("model-type").value;
    const datasetName = document.getElementById("dataset-select").value;

    if (!modelType || !datasetName) {
      alert("Please select both a dataset and a model type first.");
      return;
    }

    document.getElementById("training-message").textContent = "Training in progress...";
    document.querySelector(".progress-bar").style.width = "0%";

    const formData = new FormData();
    formData.append("model-type", modelType);
    formData.append("dataset-name", datasetName);
    formData.append("hyperparameters", JSON.stringify(getHyperparameters(modelType)));

    console.log("Submitting training request:", {
      "model-type": modelType,
      "dataset-name": datasetName,
      "hyperparameters": getHyperparameters(modelType)
    });

    fetch("/train", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(`Error: ${data.error}`);
        document.getElementById("training-message").textContent = "Training failed.";
      } else {
        document.getElementById("training-message").textContent = "Training complete!";
        document.querySelector(".progress-bar").style.width = "100%";
        updateMetricsTable(data.metrics);
        toggleSaveDeployButton(true);
      }
    })
    .catch(error => {
      console.error('Error during training:', error);
      document.getElementById("training-message").textContent = "Training failed.";
    });
  });

  const saveDeployButton = document.getElementById("save-deploy");
  saveDeployButton.addEventListener("click", function() {
    const modelSelect = document.getElementById("saved-model-select");
    if (!modelSelect) {
      console.error('Error: Model select element not found.');
      alert('No model select element found.');
      return;
    }

    const modelName = modelSelect.value;

    if (!modelName) {
      alert("No model selected.");
      return;
    }

    fetch('/api/save-deploy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ model_name: modelName })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert("Model saved and deployed successfully!");
        saveDeployButton.textContent = "Model has been saved and deployed";
        toggleSaveDeployButton(false);
      } else {
        alert("Failed to save and deploy the model.");
      }
    })
    .catch(error => {
      console.error('Error saving and deploying model:', error);
      alert('An error occurred while saving and deploying the model.');
    });
  });
});

function toggleStartTrainingButton() {
  const datasetSelect = document.getElementById("dataset-select").value;
  const modelTypeSelect = document.getElementById("model-type").value;
  const startTrainingButton = document.getElementById("start-training");

  startTrainingButton.disabled = !(datasetSelect && modelTypeSelect);
}

function populateDatasetSelect() {
  fetch("/list-preprocessed-datasets")
    .then(response => response.json())
    .then(data => {
      if (data.datasets) {
        const datasetSelect = document.getElementById("dataset-select");
        datasetSelect.innerHTML = '<option value="">Select a Dataset</option>';
        data.datasets.forEach(dataset => {
          const option = document.createElement("option");
          option.value = dataset;
          option.textContent = dataset;
          datasetSelect.appendChild(option);
        });
        console.log("Datasets populated:", data.datasets);
      } else if (data.error) {
        console.error("Error fetching dataset names:", data.error);
      }
    })
    .catch(error => {
      console.error("Error fetching datasets:", error);
    });
}

function fetchPreviewData(dataset) {
  fetch(`/preview-preprocessed-dataset?dataset=${encodeURIComponent(dataset)}`)
    .then(response => response.json())
    .then(data => {
      if (data.columns && data.preview_data) {
        updatePreviewTable(data.columns, data.preview_data);
      } else if (data.error) {
        console.error("Error fetching preview data:", data.error);
        updatePreviewTable([], []);
      } else {
        console.error("Unexpected response format:", data);
        updatePreviewTable([], []);
      }
    })
    .catch(error => {
      console.error("Error fetching preview data:", error);
      updatePreviewTable([], []);
    });
}

function updatePreviewTable(columns, data) {
  const tableHeader = document.getElementById('table-header');
  const tableBody = document.getElementById('table-body');

  if (!tableHeader || !tableBody) {
    console.error("Table header or body element not found.");
    return;
  }

  tableHeader.innerHTML = '';
  tableBody.innerHTML = '';

  if (columns.length > 0) {
    columns.forEach(column => {
      const th = document.createElement('th');
      th.textContent = column;
      tableHeader.appendChild(th);
    });

    if (data.length > 0) {
      data.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(cell => {
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

function updateParametersForm(modelType) {
  if (!modelType) return;

  const modelParameters = {
    "Isolation Forest": {
      "n_estimators": 100,
      "max_samples": "auto",
      "contamination": "auto",
      "max_features": 1.0,
      "bootstrap": false,
      "random_state": null
    },
    "One-Class SVM": {
      "kernel": "rbf",
      "nu": 0.5,
      "gamma": "scale",
      "degree": 3,
      "coef0": 0.0,
      "tol": 1e-3,
      "cache_size": 200,
      "shrinking": true,
      "verbose": false
    },
    "Random Forest": {
      "n_estimators": 100,
      "max_depth": 10,
      "min_samples_split": 2,
      "min_samples_leaf": 1,
      "max_features": 'sqrt',
      "random_state": 1,
      "bootstrap": true
    }
  };

  const parametersConfig = modelParameters[modelType];
  if (!parametersConfig) return;

  const parametersDiv = document.getElementById('model-parameters');
  parametersDiv.innerHTML = '';

  Object.entries(parametersConfig).forEach(([parameter, defaultValue]) => {
    const parameterDiv = document.createElement('div');
    parameterDiv.className = 'form-group';

    const label = document.createElement('label');
    label.htmlFor = parameter;
    label.textContent = `${parameter}:`;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = parameter;
    input.id = parameter;
    input.value = defaultValue;

    parameterDiv.appendChild(label);
    parameterDiv.appendChild(input);

    parametersDiv.appendChild(parameterDiv);
  });
}

function toggleSaveDeployButton(enabled) {
  const saveDeployButton = document.getElementById('save-deploy');
  saveDeployButton.disabled = !enabled;
}

function updateMetricsTable(metrics) {
  const metricsBody = document.getElementById('metrics-body');

  if (!metricsBody) {
    console.error("Metrics body element not found.");
    return;
  }

  metricsBody.innerHTML = '';

  if (metrics && typeof metrics === 'object' && Object.keys(metrics).length > 0) {
    for (const [metric, value] of Object.entries(metrics)) {
      const tr = document.createElement('tr');
      const tdMetric = document.createElement('td');
      tdMetric.textContent = metric;
      const tdValue = document.createElement('td');
      tdValue.textContent = value.toFixed ? value.toFixed(2) : value;
      tr.appendChild(tdMetric);
      tr.appendChild(tdValue);
      metricsBody.appendChild(tr);
    }
  } else {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 2;
    td.className = 'text-center';
    td.textContent = 'No metrics available.';
    tr.appendChild(td);
    metricsBody.appendChild(tr);
  }
}

function getHyperparameters(modelType) {
  const parametersDiv = document.getElementById('model-parameters');
  const inputs = parametersDiv.querySelectorAll('input');
  let hyperparameters = {};

  inputs.forEach(input => {
    hyperparameters[input.name] = input.value;
  });

  return hyperparameters;
}