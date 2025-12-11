// Media Modal (Images & Videos)
(function() {
  const modal = document.getElementById('mediaModal');
  const modalImg = document.getElementById('modalImage');
  const modalVideo = document.getElementById('modalVideo');
  const closeModal = document.querySelector('.close-modal');

  // Guard: only bind if modal elements exist on this page
  if (modal && modalImg && modalVideo && closeModal) {
    document.querySelectorAll('.clickable-media').forEach(el => {
      el.addEventListener('click', () => {
        modal.classList.add('show');
        if (el.tagName.toLowerCase() === 'img') {
          modalImg.src = el.src;
          modalImg.style.display = 'block';
          modalVideo.style.display = 'none';
        } else if (el.tagName.toLowerCase() === 'video') {
          modalVideo.src = el.src;
          modalVideo.style.display = 'block';
          modalImg.style.display = 'none';
          try { modalVideo.play(); } catch (_) {}
        }
      });
    });

    closeModal.addEventListener('click', () => {
      modal.classList.remove('show');
      try { modalVideo.pause(); } catch (_) {}
    });

    modal.addEventListener('click', e => {
      if (e.target === modal) {
        modal.classList.remove('show');
        try { modalVideo.pause(); } catch (_) {}
      }
    });
  }
})();