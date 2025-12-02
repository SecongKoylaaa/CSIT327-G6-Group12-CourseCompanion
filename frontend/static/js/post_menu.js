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