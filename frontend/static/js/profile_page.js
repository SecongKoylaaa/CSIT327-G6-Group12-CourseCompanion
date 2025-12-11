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

