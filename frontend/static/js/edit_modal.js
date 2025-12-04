// Edit Post Modal Logic
(function() {
  const editModal = document.getElementById('editPostModal');
  const editForm = document.getElementById('editPostForm');
  const editFormFields = document.getElementById('edit-form-fields');

  // Open edit modal
  window.openEditModal = function(postId) {
    // Show loading state
    editFormFields.innerHTML = '<p style="text-align: center; padding: 40px; color: #888;">Loading...</p>';
    editModal.classList.add('active');
    
    // Fetch edit form
    fetch(`/post/${postId}/edit/`)
      .then(response => {
        if (!response.ok) throw new Error('Failed to load edit form');
        return response.text();
      })
      .then(html => {
        // Insert form HTML into modal
        editFormFields.innerHTML = html;
        editForm.action = `/post/${postId}/edit/`;
        
        // Wrap form fields in proper structure
        wrapFormFields();
        
        // Add file input change listener
        addFileInputListener();

        // Initialize character counter for description field (300 chars)
        setupCharCounter();
      })

      .catch(error => {
        console.error('Error loading edit form:', error);
        editFormFields.innerHTML = '<p style="text-align: center; padding: 40px; color: #e74c3c;">Failed to load form. Please try again.</p>';
      });
  };

  // Close edit modal
  window.closeEditModal = function() {
    editModal.classList.remove('active');
    setTimeout(() => {
      editFormFields.innerHTML = '';
      editForm.action = '';
    }, 300);
  };

  // Close modal on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && editModal.classList.contains('active')) {
      closeEditModal();
    }
  });

  // Close modal when clicking overlay
  editModal.addEventListener('click', function(e) {
    if (e.target === editModal) {
      closeEditModal();
    }
  });

  // Wrap form fields in proper structure
  function wrapFormFields() {
    const fields = editFormFields.querySelectorAll('input, textarea, select');
    
    fields.forEach(field => {
      // Skip if already wrapped
      if (field.closest('.form-group')) return;
      
      const label = editFormFields.querySelector(`label[for="${field.id}"]`);
      const wrapper = document.createElement('div');
      wrapper.className = 'form-group';
      
      if (label) {
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(label);
        wrapper.appendChild(field);
        
        // Add required indicator if needed
        if (field.hasAttribute('required')) {
          label.classList.add('required');
        }
      }
    });
  }

  // Character counter for description textarea (300 characters)
  function setupCharCounter() {
    const descriptionField = editFormFields.querySelector('textarea[name="description"], textarea#description');
    if (!descriptionField) return;

    const MAX_LENGTH = 300;

    let counter = descriptionField.closest('.form-group')?.querySelector('.char-count');
    if (!counter) {
      counter = document.createElement('div');
      counter.className = 'char-count';
      descriptionField.parentNode.appendChild(counter);
    }

    const updateCounter = () => {
      let value = descriptionField.value || '';
      if (value.length > MAX_LENGTH) {
        value = value.slice(0, MAX_LENGTH);
        descriptionField.value = value;
      }

      const used = value.length;
      counter.textContent = `${used}/${MAX_LENGTH} characters`;
      if (used >= MAX_LENGTH) {
        counter.classList.add('char-limit-reached');
      } else {
        counter.classList.remove('char-limit-reached');
      }
    };

    descriptionField.addEventListener('input', updateCounter);
    // Initialize on open with existing content
    updateCounter();
  }

  // Add file input change listener to show selected filename
  function addFileInputListener() {
    const fileInputs = editFormFields.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
      input.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name;
        if (fileName) {
          const label = this.closest('.form-group')?.querySelector('label');
          if (label) {
            // Store original label text if not already stored
            if (!label.dataset.originalText) {
              label.dataset.originalText = label.textContent;
            }
            label.textContent = `${label.dataset.originalText} - ${fileName}`;
          }
        }
      });
    });
  }

  // Form submission with loading state
  editForm.addEventListener('submit', function(e) {
    const submitBtn = editModal.querySelector('.btn-primary');
    if (submitBtn) {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
    }
  });
})();