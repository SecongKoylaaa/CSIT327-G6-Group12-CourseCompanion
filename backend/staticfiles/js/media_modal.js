// Media Modal (Images & Videos)
(function() {
  const modal = document.getElementById('mediaModal');
  const modalImg = document.getElementById('modalImage');
  const modalVideo = document.getElementById('modalVideo');
  const closeModal = document.querySelector('.close-modal');

  // Guard: only bind if modal elements exist on this page
  if (modal && modalImg && modalVideo && closeModal) {
    // Use event delegation to handle dynamically loaded media
    document.addEventListener('click', (e) => {
      const clickedMedia = e.target.closest('.clickable-media');
      if (clickedMedia) {
        e.preventDefault();
        e.stopPropagation();
        
        modal.classList.add('show');
        if (clickedMedia.tagName.toLowerCase() === 'img') {
          modalImg.src = clickedMedia.src;
          modalImg.style.display = 'block';
          modalVideo.style.display = 'none';
        } else if (clickedMedia.tagName.toLowerCase() === 'video') {
          modalVideo.src = clickedMedia.src;
          modalVideo.style.display = 'block';
          modalImg.style.display = 'none';
          try { modalVideo.play(); } catch (_) {}
        }
      }
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