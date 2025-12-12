/* ========== MODAL OPEN/CLOSE ========== */
document.getElementById("editBtn").addEventListener("click", () => {
  document.getElementById("editPopup").style.display = "flex";
});

function closeEditPopup() {
  document.getElementById("editPopup").style.display = "none";
}

/* ========== UPLOAD SCRIPT ========== */
const box = document.getElementById("profileUploadBox");
const fileInput = document.getElementById("profilePicInput");
const previewImg = document.getElementById("previewProfileImg");
const text = document.getElementById("profileUploadText");
const removeBtn = document.getElementById("removeProfileBtn");
const placeholder = document.getElementById("previewPlaceholder");

/* click → open file chooser */
box.addEventListener("click", () => fileInput.click());

/* file selected */
fileInput.addEventListener("change", function () {
  const file = this.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = e => {
    previewImg.src = e.target.result;
    previewImg.style.display = "block";
    if (placeholder) placeholder.style.display = "none";
    text.style.display = "none";
    removeBtn.style.display = "flex";
    document.getElementById("removePictureFlag").value = "0"; // prevent delete flag
  };
  reader.readAsDataURL(file);
});

/* Drag highlight */
box.addEventListener("dragover", e => {
  e.preventDefault();
  box.style.borderColor = "#4a90e2";
});

box.addEventListener("dragleave", () => box.style.borderColor = "#888");

/* Drop upload */
box.addEventListener("drop", e => {
  e.preventDefault();
  box.style.borderColor = "#888";

  const file = e.dataTransfer.files[0];
  if (!file) return;

  fileInput.files = e.dataTransfer.files;

  const reader = new FileReader();
  reader.onload = e2 => {
    previewImg.src = e2.target.result;
    previewImg.style.display = "block";
    if (placeholder) placeholder.style.display = "none";
    text.style.display = "none";
    removeBtn.style.display = "flex";
    document.getElementById("removePictureFlag").value = "0"; // prevent delete flag
  };
  reader.readAsDataURL(file);
});

/* Remove image */
removeBtn.addEventListener("click", e => {
  e.stopPropagation();
  previewImg.src = "";
  previewImg.style.display = "none";
  if (placeholder) placeholder.style.display = "flex";
  text.style.display = "block";
  removeBtn.style.display = "none";
  fileInput.value = "";

  // mark deletion for Django view
  document.getElementById("removePictureFlag").value = "1";
});

/* ========== PROFILE TABS: POSTS / COMMENTS ========== */
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".profile-tabs .tab-btn");
  const sections = {
    profilePostsSection: document.getElementById("profilePostsSection"),
    profileCommentsSection: document.getElementById("profileCommentsSection"),
  };

  function showSection(target) {
    Object.entries(sections).forEach(([key, el]) => {
      if (!el) return;
      const show = key === target;
      el.style.display = show ? "block" : "none";
    });
    tabs.forEach(b => {
      const isActive = b.getAttribute("data-target") === target;
      b.classList.toggle("active", isActive);
      b.setAttribute("aria-selected", isActive ? "true" : "false");
    });
  }

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-target");
      showSection(target);
    });
  });

  // Initialize with Posts visible
  showSection("profilePostsSection");
});

// ==================== CAROUSEL & MEDIA MODAL (from template) ====================
function sharePost(postId){
  try {
    const url = `${window.location.origin}/home/#post-${postId}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(() => {
        alert('Post link copied to clipboard');
      });
      return;
    }
    const tmp = document.createElement('input');
    tmp.value = url;
    document.body.appendChild(tmp);
    tmp.select();
    document.execCommand('copy');
    document.body.removeChild(tmp);
    alert('Post link copied to clipboard');
  } catch(e){
    console.error('Share failed', e);
  }
}

const carouselStates = {};

function changeSlide(postId, direction) {
  if (!carouselStates[postId]) {
    carouselStates[postId] = { currentIndex: 0 };
  }
  const carousel = document.getElementById('carousel-' + postId);
  const images = carousel.querySelectorAll('.carousel-image');
  const indicators = carousel.querySelectorAll('.indicator');
  const counter = carousel.querySelector('.current-slide');
  images[carouselStates[postId].currentIndex].classList.remove('active');
  indicators[carouselStates[postId].currentIndex].classList.remove('active');
  carouselStates[postId].currentIndex += direction;
  if (carouselStates[postId].currentIndex >= images.length) {
    carouselStates[postId].currentIndex = 0;
  } else if (carouselStates[postId].currentIndex < 0) {
    carouselStates[postId].currentIndex = images.length - 1;
  }
  images[carouselStates[postId].currentIndex].classList.add('active');
  indicators[carouselStates[postId].currentIndex].classList.add('active');
  counter.textContent = carouselStates[postId].currentIndex + 1;
}

function goToSlide(postId, index) {
  if (!carouselStates[postId]) {
    carouselStates[postId] = { currentIndex: 0 };
  }
  const carousel = document.getElementById('carousel-' + postId);
  const images = carousel.querySelectorAll('.carousel-image');
  const indicators = carousel.querySelectorAll('.indicator');
  const counter = carousel.querySelector('.current-slide');
  images[carouselStates[postId].currentIndex].classList.remove('active');
  indicators[carouselStates[postId].currentIndex].classList.remove('active');
  carouselStates[postId].currentIndex = index;
  images[carouselStates[postId].currentIndex].classList.add('active');
  indicators[carouselStates[postId].currentIndex].classList.add('active');
  counter.textContent = carouselStates[postId].currentIndex + 1;
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.image-carousel').forEach(carousel => {
    const postId = carousel.id.replace('carousel-', '');
    carouselStates[postId] = { currentIndex: 0 };
  });
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('carousel-btn')) {
      const postId = e.target.dataset.postId;
      const direction = parseInt(e.target.dataset.direction);
      changeSlide(postId, direction);
    }
    if (e.target.classList.contains('indicator')) {
      const postId = e.target.dataset.postId;
      const index = parseInt(e.target.dataset.index);
      goToSlide(postId, index);
    }
  });
});

// MEDIA MODAL (from template)
const modal = document.getElementById('mediaModal');
const modalImg = document.getElementById('modalImage');
const modalVideo = document.getElementById('modalVideo');
const closeModal = document.querySelector('.close-modal');
document.addEventListener('click', function(e) {
  const clickableMedia = e.target.closest('.clickable-media');
  if (clickableMedia) {
    modal.classList.add('show');
    if (clickableMedia.tagName.toLowerCase() === 'img') {
      modalImg.src = clickableMedia.src;
      modalImg.style.display = 'block';
      modalVideo.style.display = 'none';
    } else if (clickableMedia.tagName.toLowerCase() === 'video') {
      modalVideo.src = clickableMedia.src;
      modalVideo.style.display = 'block';
      modalImg.style.display = 'none';
      modalVideo.play();
    }
  }
});
closeModal.addEventListener('click', () => {
  modal.classList.remove('show');
  modalVideo.pause();
});
modal.addEventListener('click', e => {
  if (e.target === modal) {
    modal.classList.remove('show');
    modalVideo.pause();
  }
});

