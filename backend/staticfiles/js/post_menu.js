// Post Menu Toggle (Edit/Delete dropdown)
function togglePostMenu(postId) {
  const menu = document.getElementById(`post-menu-${postId}`);
  
  // Close all other menus first
  document.querySelectorAll('.post-menu').forEach(m => {
    if (m.id !== `post-menu-${postId}`) {
      m.style.display = 'none';
    }
  });
  
  // Toggle current menu
  menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
  document.querySelectorAll('.post-menu').forEach(menu => {
    const btn = menu.previousElementSibling;
    if (!menu.contains(event.target) && (!btn || !btn.contains(event.target))) {
      menu.style.display = 'none';
    }
  });
});

// Share helper available on Home and Profile
function sharePost(postId) {
  try {
    const anchorUrl = `${window.location.origin}/home/#post-${postId}`;
    // Always copy to clipboard to avoid Edge's share popup
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(anchorUrl).then(() => {
        alert('Post link copied to clipboard');
      });
      return;
    }
    // Fallback for older browsers
    const tmp = document.createElement('input');
    tmp.value = anchorUrl;
    document.body.appendChild(tmp);
    tmp.select();
    document.execCommand('copy');
    document.body.removeChild(tmp);
    alert('Post link copied to clipboard');
  } catch (e) {
    console.error('Share failed:', e);
  }
}