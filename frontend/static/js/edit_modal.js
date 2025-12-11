// Edit Post Modal Logic (robust to script/markup order)
(function() {
  function getRefs() {
    return {
      editModal: document.getElementById('editPostModal'),
      editForm: document.getElementById('editPostForm'),
      editFormFields: document.getElementById('edit-form-fields')
    };
  }

  // Open edit modal
  window.openEditModal = function(postId) {
    const { editModal, editForm, editFormFields } = getRefs();
    // Show loading state
    if (editFormFields) {
      editFormFields.innerHTML = '<p style="text-align: center; padding: 40px; color: #888;">Loading...</p>';
    }
    if (editModal) {
      editModal.classList.add('active');
    }
    
    // Fetch edit form
    fetch(`/post/${postId}/edit/`)
      .then(response => {
        if (!response.ok) throw new Error('Failed to load edit form');
        return response.text();
      })
      .then(html => {
        // Insert form HTML into modal
        const refs = getRefs();
        if (refs.editFormFields) refs.editFormFields.innerHTML = html;
        if (refs.editForm) refs.editForm.action = `/post/${postId}/edit/`;
        
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
    const { editModal, editForm, editFormFields } = getRefs();
    if (editModal) editModal.classList.remove('active');
    setTimeout(() => {
      if (editFormFields) editFormFields.innerHTML = '';
      if (editForm) editForm.action = '';
    }, 300);
  };

  // Close modal on Escape key
  document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('editPostModal');
    if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
      closeEditModal();
    }
  });

  // Close modal when clicking overlay
  // Use delegated listener to handle overlay clicks regardless of load order
  document.addEventListener('click', function(e) {
    const modal = document.getElementById('editPostModal');
    if (modal && e.target === modal) {
      closeEditModal();
    }
  });

  // Wrap form fields in proper structure
  function wrapFormFields() {
    const { editFormFields } = getRefs();
    if (!editFormFields) return;
    const fields = editFormFields.querySelectorAll('input, textarea, select');

    fields.forEach(field => {
      if (!field) return;
      // Skip if already wrapped
      if (field.closest('.form-group')) return;

      const label = editFormFields.querySelector(`label[for="${field.id}"]`);
      const wrapper = document.createElement('div');
      wrapper.className = 'form-group';

      if (label && field.parentNode) {
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(label);
        wrapper.appendChild(field);

        if (field.hasAttribute('required')) {
          label.classList.add('required');
        }
      }
    });
  }

  // Character counter for title and description fields
  function setupCharCounter() {
    const { editFormFields } = getRefs();
    if (!editFormFields) return;
    const titleField = editFormFields.querySelector('input[name="title"], #edit-title');
    const descField = editFormFields.querySelector('textarea[name="description"], #edit-description');

    const MAX_TITLE = 300;
    const MAX_DESC = 1000;

    const ensureCounter = (field) => {
      if (!field) return null;
      let counter = field.closest('.form-group')?.querySelector('.char-count');
      if (!counter) {
        counter = document.createElement('div');
        counter.className = 'char-count';
        field.parentNode.appendChild(counter);
      }
      return counter;
    };

    const titleCounter = ensureCounter(titleField);
    const descCounter = ensureCounter(descField);

    const updateTitle = () => {
      if (!titleField || !titleCounter) return;
      let val = titleField.value || '';
      if (val.length > MAX_TITLE) {
        val = val.slice(0, MAX_TITLE);
        titleField.value = val;
      }
      titleCounter.textContent = `${val.length}/${MAX_TITLE} characters`;
      titleCounter.classList.toggle('char-limit-reached', val.length >= MAX_TITLE);
    };

    const updateDesc = () => {
      if (!descField || !descCounter) return;
      let val = descField.value || '';
      if (val.length > MAX_DESC) {
        val = val.slice(0, MAX_DESC);
        descField.value = val;
      }
      descCounter.textContent = `${val.length}/${MAX_DESC} characters`;
      descCounter.classList.toggle('char-limit-reached', val.length >= MAX_DESC);
    };

    if (titleField) {
      titleField.addEventListener('input', updateTitle);
      updateTitle();
    }

    if (descField) {
      descField.addEventListener('input', updateDesc);
      updateDesc();
    }
  }

  // Add file input change listener to show selected filename
  function addFileInputListener() {
    const { editFormFields } = getRefs();
    if (!editFormFields) return;
    const fileInputs = editFormFields.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
      input.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name;
        if (fileName) {
          const label = this.closest('.form-group')?.querySelector('label');
          if (label) {
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
  // Delegated submit handler to avoid null refs when form markup loads later
  document.addEventListener('submit', function(e) {
    const form = document.getElementById('editPostForm');
    if (e.target === form) {
      const modal = document.getElementById('editPostModal');
      const submitBtn = modal ? modal.querySelector('.btn-primary') : null;
      if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
      }
    }
  });
})();