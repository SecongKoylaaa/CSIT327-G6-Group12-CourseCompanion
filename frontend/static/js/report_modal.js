// Report Modal JavaScript
function reportPost(postId) {
    // Set the post ID in the hidden field
    document.getElementById('report_post_id').value = postId;
    
    // Show the report modal
    const modal = document.getElementById('reportPostModal');
    modal.classList.add('active');
    
    // Close any open post menus
    document.querySelectorAll('.post-menu').forEach(menu => {
        menu.style.display = 'none';
    });
}

function closeReportModal() {
    const modal = document.getElementById('reportPostModal');
    modal.classList.remove('active');
    
    // Reset form
    document.getElementById('reportPostForm').reset();
    document.getElementById('report_post_id').value = '';
}

function submitReport() {
    const form = document.getElementById('reportPostForm');
    const formData = new FormData(form);
    
    // Validate form
    const violationType = formData.get('violation_type');
    if (!violationType) {
        alert('Please select a reason for reporting.');
        return false;
    }
    
    // Send report to backend
    fetch('/report_post/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Report submitted successfully. Thank you for helping keep our community safe.');
            closeReportModal();
        } else {
            alert(data.error || 'Failed to submit report. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error submitting report:', error);
        alert('An error occurred while submitting the report. Please try again.');
    });
    
    return false; // Prevent form submission
}

// Close modal when clicking outside
window.onclick = function(event) {
    const reportModal = document.getElementById('reportPostModal');
    if (event.target == reportModal) {
        closeReportModal();
    }
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeReportModal();
    }
});
