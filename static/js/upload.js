$(document).ready(function() {
  // Ensure the .section element is displayed as block on page load
  $('.section').css('display', 'block');

  // Handle form submission for upload
  $('#uploadForm').on('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission
    var formData = new FormData(this); // Get the form data

    uploadFile(formData);
  });

  // Handle Preview button click
  $('#preview').on('click', function(e) {
    e.preventDefault(); // Prevent the default form submission
    // Retrieve the instance ID and filename from the button's data attributes
    var datasetId = $(this).data('dataset-id');
    var filename = $(this).data('filename');
    if (datasetId && filename) {
      // Redirect to the preview page with the instance ID and filename
      window.location.href = `/preview/${datasetId}/${filename}`;
    } else {
      $('#error-message').text('Please upload a file before previewing.');
    }
  });

  function uploadFile(formData) {
    $.ajax({
      url: "/upload", // Use the correct URL
      method: 'POST', // Use POST method
      data: formData,
      processData: false,
      contentType: false,
      success: handleUploadSuccess,
      error: handleUploadError
    });
  }

  function handleUploadSuccess(response) {
    if (response.dataset_id && response.filename) {
      $('#success-message').text('Upload successful. Please proceed to preview.');

      // Set instance_id and filename data attributes on the preview button
      $('#preview').data('instance-id', response.dataset_id);
      $('#preview').data('filename', response.filename);
    } else {
      $('#error-message').text('Upload failed. Please try again.');
    }
  }

  function handleUploadError(error) {
    console.error("Upload failed:", error);
    $('#error-message').text('An error occurred during upload.');
  }
});
