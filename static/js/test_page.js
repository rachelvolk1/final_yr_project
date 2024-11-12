$(document).ready(function() {
    $('.section').css('display', 'block');
    // Apply Filters button functionality
    $('#apply-filters').on('click', function() {
        const selectedFeatures = [];
        $('.form-check-input:checked').each(function() {
            selectedFeatures.push($(this).val());
        });
        alert('Selected Features: ' + selectedFeatures.join(', '));
    });

    // Tab functionality
    $('.nav-link').on('click', function(event) {
        event.preventDefault();
        var tab = new bootstrap.Tab(this);
        tab.show();
    });
});