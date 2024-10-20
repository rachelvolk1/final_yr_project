$(document).ready(function() {
  // Ensure the .section element is displayed as block on page load
  $('.section').css('display', 'block');

  $('#uploadForm').on('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission
    var formData = new FormData(this); // Get the form data

    uploadFile(formData);
  });

  function uploadFile(formData) {
    $.ajax({
      url: "/upload", // Use the direct URL
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: handleUploadSuccess,
      error: handleUploadError
    });
  }

  function handleUploadSuccess(response) {
    if (response.dataset_id) {
      $('#success-message').text('Upload successful. Please proceed to preview.');
      
      // Redirect to the preview page after a delay
      setTimeout(function() {
        window.location.href = '/preview?dataset_id=' + response.dataset_id;
      }, 2000); // Adjust delay as needed
    } else {
      $('#error-message').text('Upload failed. Please try again.');
    }
  }

  function handleUploadError(error) {
    console.error("Upload failed:", error);
    $('#error-message').text('An error occurred during upload.');
  }
});
