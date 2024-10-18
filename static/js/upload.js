window.onload = function() {
    const section = document.querySelector('.section');
    section.style.display = 'block';
};
$(document).ready(function() {
    // Handle form submission for file upload
    $('#uploadForm').on('submit', function(event) {
        event.preventDefault(); // Prevent default form submission

        var formData = new FormData(this); // Create FormData object from form

        $.ajax({
            url: $(this).attr('action'), // URL for the file upload (Flask route)
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                // Check if the response contains a filename
                if (response.filename) {
                    // Redirect to the preview page with the uploaded filename
                    window.location.href = '/preview/' + response.filename;
                } else {
                    $('#error-message').text('Unexpected response received.');
                }
            },
            error: function(err) {
                console.error('Error uploading file:', err);
                $('#error-message').text('Error uploading file. Please try again.');
            }
        });
    });
});
