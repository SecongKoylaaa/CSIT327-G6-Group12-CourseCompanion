// Media Modal (Images & Videos)
(function() {
  const modal = document.getElementById('mediaModal');
  const modalImg = document.getElementById('modalImage');
  const modalVideo = document.getElementById('modalVideo');
  const closeModal = document.querySelector('.close-modal');

  // Open media modal when clicking on images/videos
  document.querySelectorAll('.clickable-media').forEach(el => {
    el.addEventListener('click', () => {
      modal.classList.add('show');
      
      if (el.tagName.toLowerCase() === 'img') {
        modalImg.src = el.src;
        modalImg.style.display = 'block';
        modalVideo.style.display = 'none';
      } else {
        modalVideo.src = el.src;
        modalVideo.style.display = 'block';
        modalImg.style.display = 'none';
        modalVideo.play();
      }
    });
  });

  // Close modal when clicking X
  closeModal.addEventListener('click', () => {
    modal.classList.remove('show');
    modalVideo.pause();
  });

  // Close modal when clicking outside
  modal.addEventListener('click', e => {
    if (e.target === modal) {
      modal.classList.remove('show');
      modalVideo.pause();
    }
  });
})();