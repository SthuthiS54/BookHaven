$(document).ready(function() {
    $('#addReviewForm').submit(function(event) {
        event.preventDefault();  // Prevent default form submission

        // Serialize form data
        var formData = $(this).serialize();

        // Submit data using Ajax
        $.ajax({
            type: 'POST',
            url: '{{ url_for("add_review", book_id=book.book_id) }}',  // Adjust as per your Flask route
            data: formData,
            success: function(response) {
                // Assuming your Flask route returns JSON with success message
                alert(response.message);  // Display success message or handle as needed
                // Optionally update reviews list on the page
            },
            error: function(error) {
                alert('Error adding review: ' + error.responseJSON.message);  // Display error message
            }
        });
    });
});
