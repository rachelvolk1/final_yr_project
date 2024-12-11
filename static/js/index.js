
document.addEventListener('DOMContentLoaded', () => {

    const fetchAndUpdate = (url, elementId, defaultMessage) => {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const element = document.getElementById(elementId);
                const key = Object.keys(data)[0];
                if (data[key]) {
                    element.textContent = data[key];
                } else {
                    element.textContent = defaultMessage;
                }
            })
            .catch(error => {
                console.error(`Error fetching data from ${url}:`, error);
                const element = document.getElementById(elementId);
                element.textContent = "Error";
            });
    };

    fetchAndUpdate('/api/get_last_cleaned_dataset', 'last-dataset-cleaned', 'No datasets found');
    fetchAndUpdate('/api/get_last_model_trained', 'last-model-trained', 'No models found');
    fetchAndUpdate('/api/users', 'total-users-count', 'Error loading total users');
    fetchAndUpdate('/api/current_users', 'current-users-count', 'Error loading current users');
    fetchAndUpdate('/api/get_trained_model_count', 'datasets-trained-count', '0');

    fetch('/api/get_folder_counts')
        .then(response => response.json())
        .then(data => {
            if (data.uploads !== undefined) {
                document.getElementById('uploads-count').textContent = data.uploads;
            }
            if (data.preprocessed_data !== undefined) {
                document.getElementById('preprocessed-data-count').textContent = data.preprocessed_data;
            }
        })
        .catch(error => {
            console.error("Error fetching folder counts:", error);
            document.getElementById('uploads-count').textContent = "Error";
            document.getElementById('preprocessed-data-count').textContent = "Error";
        });
});