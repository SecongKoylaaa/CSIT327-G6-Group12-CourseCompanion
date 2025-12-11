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

// Make votePost available on Profile too (shared helper)
function votePost(postId, type, btn) {
  try {
    const container = btn.closest(".actions");
    if (!container) return;

    const voteCountElem = container.querySelector(".vote-count");
    const upBtn = container.querySelector(".upvote");
    const downBtn = container.querySelector(".downvote");

    if (btn && btn.tagName === "BUTTON") btn.type = "button";

    const oldValue = voteCountElem?.textContent.trim() || "0";
    if (upBtn) upBtn.disabled = true;
    if (downBtn) downBtn.disabled = true;

    fetch(`/vote_post/${postId}/${type}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": (function getCookie(name){const v=`; ${document.cookie}`;const p=v.split(`; ${name}=`);return p.length===2?p.pop().split(";").shift():null;})("csrftoken"),
        "Accept": "application/json"
      },
      credentials: "same-origin"
    })
      .then(res => res.json())
      .then(data => {
        if (!data || data.error) return;
        const newVotes = parseInt(data.net_votes ?? oldValue, 10);
        if (voteCountElem) {
          voteCountElem.textContent = newVotes;
          voteCountElem.animate([
            { transform: "scale(1)" },
            { transform: "scale(1.2)" },
            { transform: "scale(1)" }
          ], { duration: 180 });
        }
        upBtn?.classList.remove("active-upvote");
        downBtn?.classList.remove("active-downvote");
        if (data.user_vote === "upvote") upBtn?.classList.add("active-upvote");
        if (data.user_vote === "downvote") downBtn?.classList.add("active-downvote");
      })
      .catch(() => { if (voteCountElem) voteCountElem.textContent = oldValue; })
      .finally(() => { if (upBtn) upBtn.disabled = false; if (downBtn) downBtn.disabled = false; });

  } catch (ex) { /* swallow */ }
}