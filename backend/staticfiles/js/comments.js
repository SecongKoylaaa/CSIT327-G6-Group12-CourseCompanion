/* ========================================================================
   MANILA TIME CONVERSION
======================================================================== */
function toManilaTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
}

/* ========================================================================
   COMMENT SECTION TOGGLE
======================================================================== */
function toggleComments(el) {
  const post = el.closest(".post");
  if (!post) return;

  // Toggle expanded UI state
  post.classList.toggle("show-expanded");
  post.querySelectorAll(".comment-toggle").forEach(span => {
    if (span !== el) span.classList.remove("active");
  });
  el.classList.toggle("active");

  // Show/hide the expanded section
  const expanded = post.querySelector('.expanded-section');
  if (!expanded) return;
  const isVisible = expanded.style.display === 'block';
  if (isVisible) {
    expanded.style.display = 'none';
    return;
  }
  expanded.style.display = 'block';

  // Lazy-load comments only once per post
  const container = expanded.querySelector('.comments-section');
  if (!container) return;
  const loaded = container.getAttribute('data-loaded') === 'true';
  if (loaded) return;

  const postId = container.getAttribute('data-post-id');
  if (!postId) return;

  fetch(`/comments/${postId}/`, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' }})
    .then(res => {
      if (!res.ok) throw new Error('Failed to load comments');
      return res.text();
    })
    .then(html => {
      container.innerHTML = html;
      container.setAttribute('data-loaded', 'true');
      // Re-apply local time formatting for newly injected comments
      applyCommentTimes(container);
    })
    .catch(err => {
      container.innerHTML = `<div class="comments-error">Unable to load comments. Please try again.</div>`;
      console.error(err);
    });
}

/* ========================================================================
   COMMENT MENU TOGGLE
======================================================================== */
let openCommentMenu = null;

function toggleCommentMenu(commentId) {
  const menu = document.getElementById(`comment-menu-${commentId}`);
  if (!menu) return;

  // Close any other open menu
  if (openCommentMenu && openCommentMenu !== menu) {
    openCommentMenu.style.display = "none";
  }

  const isCurrentlyOpen = menu.style.display === "block";
  menu.style.display = isCurrentlyOpen ? "none" : "block";
  openCommentMenu = isCurrentlyOpen ? null : menu;
}

/* ========================================================================
   COMMENT VOTING
======================================================================== */
function voteComment(commentId, type, btn) {
  try {
    const container = btn.closest(".comment-votes");
    if (!container) return;

    const voteCountElem = container.querySelector(".comment-vote-count");
    const upBtn = container.querySelector(".comment-upvote");
    const downBtn = container.querySelector(".comment-downvote");

    if (btn.tagName === "BUTTON") btn.type = "button";

    const oldValue = voteCountElem?.textContent.trim() || "0";

    if (upBtn) upBtn.disabled = true;
    if (downBtn) downBtn.disabled = true;

    fetch(`/vote_comment/${commentId}/${type}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
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
          voteCountElem.animate(
            [
              { transform: "scale(1)" },
              { transform: "scale(1.2)" },
              { transform: "scale(1)" }
            ],
            { duration: 180 }
          );
        }

        upBtn?.classList.remove("active-upvote");
        downBtn?.classList.remove("active-downvote");

        if (data.user_vote === "upvote") upBtn?.classList.add("active-upvote");
        if (data.user_vote === "downvote") downBtn?.classList.add("active-downvote");
      })
      .catch(err => {
        console.error("Vote error:", err);
        if (voteCountElem) voteCountElem.textContent = oldValue;
      })
      .finally(() => {
        if (upBtn) upBtn.disabled = false;
        if (downBtn) downBtn.disabled = false;
      });

  } catch (ex) {
    console.error("voteComment exception:", ex);
  }
}

/* ========================================================================
   REPLY FORM TOGGLE
======================================================================== */
let openReplyForm = null;

function toggleReplyForm(commentId) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (!form) return;

  if (openReplyForm && openReplyForm !== form) {
    openReplyForm.style.display = "none";
  }

  const open = form.style.display === "none" || form.style.display === "";
  form.style.display = open ? "flex" : "none";

  if (open) {
    const t = form.querySelector("textarea");
    t?.focus();
  }

  openReplyForm = open ? form : null;
}

/* ========================================================================
   CLOSE MENUS ON OUTSIDE CLICK
======================================================================== */
document.addEventListener("click", e => {
  const isInsideCommentMenu = e.target.closest(".comment-menu-wrapper");
  if (!isInsideCommentMenu) {
    document.querySelectorAll(".comment-menu").forEach(m => m.style.display = "none");
    openCommentMenu = null;
  }

  document.querySelectorAll(".sort-menu").forEach(menu => {
    if (!menu.closest(".sort-dropdown").contains(e.target)) {
      menu.classList.remove("show");
    }
  });
});

/* ========================================================================
   EDIT FORM
======================================================================== */
function toggleEditForm(commentId) {
  const form = document.getElementById(`edit-form-${commentId}`);
  const text = document.getElementById(`comment-text-${commentId}`);
  if (!form || !text) return;

  const open = form.style.display === "none" || form.style.display === "";
  form.style.display = open ? "flex" : "none";
  text.style.display = open ? "none" : "block";
}

function cancelEdit(commentId) {
  const form = document.getElementById(`edit-form-${commentId}`);
  const text = document.getElementById(`comment-text-${commentId}`);
  if (!form || !text) return;

  form.style.display = "none";
  text.style.display = "block";
}

/* ========================================================================
   SORT SYSTEM
======================================================================== */
function toggleSortMenu(button) {
  const menu = button.closest(".sort-dropdown").querySelector(".sort-menu");
  menu.classList.toggle("show");
}

function selectSortOption(option, el, postId) {
  const dropdown = el.closest(".sort-dropdown");
  dropdown.querySelector(".selected-sort").textContent = option;
  dropdown.querySelector(".sort-menu").classList.remove("show");
  sortComments(postId, option.toLowerCase());
}

function sortComments(postId, sortType) {
  const container = document.getElementById(`comments-list-${postId}`);
  if (!container) return;

  const wrappers = Array.from(container.querySelectorAll(":scope > .comment-wrapper"));

  wrappers.sort((a, b) => {
    const ac = a.querySelector(".comment");
    const bc = b.querySelector(".comment");

    // FIXED HERE
    const av = parseInt(ac.dataset.votes) || 0;
    const bv = parseInt(bc.dataset.votes) || 0;

    const at = new Date(ac.dataset.created).getTime();
    const bt = new Date(bc.dataset.created).getTime();

    // Sort logic
    if (sortType === "top") return bv - av;
    if (sortType === "new") return bt - at;
    if (sortType === "oldest") return at - bt;

    return 0;
  });

  container.innerHTML = "";
  wrappers.forEach(w => container.appendChild(w));
}



/* ========================================================================
   CSRF HELPER
======================================================================== */
function getCookie(name) {
  const parts = `; ${document.cookie}`.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(";").shift() : null;
}

// Helper to apply Manila time formatting to any scope
function applyCommentTimes(root) {
  const scope = root || document;
  scope.querySelectorAll('.comment-time-local').forEach(el => {
    const iso = el.getAttribute('data-time');
    if (iso) {
      el.textContent = toManilaTime(iso);
    }
  });
}

/* ========================================================================
   APPLY MANILA TIME + COMMENT TEXTAREA VALIDATION + VOTE BUTTON FIXES
========================================================================= */
document.addEventListener("DOMContentLoaded", () => {
  // Manila time for any comments present on initial load
  applyCommentTimes(document);

  // Comment textarea min length (600) + autosize + counter
  const MIN_COMMENT_LENGTH = 600;

  document.querySelectorAll(".comment-textarea").forEach(t => {
    const counter = document.createElement("div");
    counter.className = "comment-error";
    t.after(counter);

    const form = t.closest("form");

    const update = () => {
      const len = t.value.length;
      counter.textContent = `${len} / ${MIN_COMMENT_LENGTH}` +
        (len < MIN_COMMENT_LENGTH ? " - Minimum 600 characters required" : "");

      counter.classList.toggle("too-short", len < MIN_COMMENT_LENGTH);

      t.style.height = "auto";
      t.style.height = t.scrollHeight + "px";
    };

    t.addEventListener("input", update);
    update();

    if (form) {
      form.addEventListener("submit", e => {
        const len = t.value.trim().length;
        if (len < MIN_COMMENT_LENGTH) {
          e.preventDefault();
          update();
          t.focus();
        }
      });
    }
  });

  // Prevent button-submit issues
  document.querySelectorAll(".comment-upvote, .comment-downvote").forEach(b => {
    if (b.tagName === "BUTTON") b.type = "button";
  });
});

/* ========================================================================
   POST VOTING
======================================================================== */
function votePost(postId, type, btn) {
  try {
    const container = btn.closest(".actions");
    if (!container) return;

    const voteCountElem = container.querySelector(".vote-count");
    const upBtn = container.querySelector(".upvote");
    const downBtn = container.querySelector(".downvote");

    if (btn.tagName === "BUTTON") btn.type = "button";

    const oldValue = voteCountElem?.textContent.trim() || "0";

    upBtn.disabled = true;
    downBtn.disabled = true;

    fetch(`/vote_post/${postId}/${type}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Accept": "application/json"
      },
      credentials: "same-origin"
    })
      .then(res => res.json())
      .then(data => {
        if (!data || data.error) return;

        const newVotes = parseInt(data.net_votes ?? oldValue, 10);
        voteCountElem.textContent = newVotes;

        voteCountElem.animate(
          [
            { transform: "scale(1)" },
            { transform: "scale(1.2)" },
            { transform: "scale(1)" }
          ],
          { duration: 180 }
        );

        upBtn.classList.remove("active-upvote");
        downBtn.classList.remove("active-downvote");

        if (data.user_vote === "upvote") upBtn.classList.add("active-upvote");
        if (data.user_vote === "downvote") downBtn.classList.add("active-downvote");
      })
      .catch(err => console.error("Vote error:", err))
      .finally(() => {
        upBtn.disabled = false;
        downBtn.disabled = false;
      });

  } catch (ex) {
    console.error("votePost exception:", ex);
  }
}
/* ========================================================================
   TOGGLE REPLIES (FINAL WORKING VERSION)
======================================================================== */
function toggleReplies(commentId) {
    const box = document.getElementById(`hidden-replies-${commentId}`);
    const btn = document.getElementById(`more-replies-${commentId}`);

    if (!box || !btn) return;

    const isHidden = box.style.display === "none" || box.style.display === "";

    if (isHidden) {
        box.style.display = "block";
        btn.textContent = "Hide Replies";
    } else {
        box.style.display = "none";
        btn.textContent = btn.dataset.originalText;
    }
}


// =========================
// SHOW/HIDE REPLY FORM
// =========================
function showReplyForm(commentId, userEmail) {
    const form = document.getElementById(`reply-form-${commentId}`);
    if (!form) return;

    const isHidden = form.style.display === "none" || form.style.display === "";
    if (isHidden) {
        form.style.display = "flex";
        const textarea = form.querySelector("textarea");
        if (textarea) {
            textarea.value = `@${userEmail} `;
            textarea.focus();
        }
    } else {
        form.style.display = "none";
    }
}

// =========================
// COMMENT MENU
// =========================
function toggleCommentMenuLegacy(commentId) {
    toggleCommentMenu(commentId);
}

// =========================
// EDIT COMMENT
// =========================
function toggleEditForm(commentId) {
    document.getElementById(`edit-form-${commentId}`).style.display = "block";
    document.getElementById(`comment-text-${commentId}`).style.display = "none";
}

function cancelEdit(commentId) {
    document.getElementById(`edit-form-${commentId}`).style.display = "none";
    document.getElementById(`comment-text-${commentId}`).style.display = "block";
}

// =========================
// MARK BEST ANSWER (FORUM Q&A)
// =========================
function markBestAnswer(postId, commentId) {
    if (!confirm("Mark this as the best answer? This will mark the question as solved.")) {
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(`/post/${postId}/mark-best-answer/${commentId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Reload to show best answer badge and update status
        } else {
            alert('Error: ' + (data.error || 'Could not mark best answer'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to mark best answer');
    });
}
// CHARACTER COUNTER
// =========================
function updateCharCount(textarea, counterId) {
    const counter = document.getElementById(counterId);
    if (!counter) return;
    
    const currentLength = textarea.value.length;
    const maxLength = 600;
    
    counter.textContent = `${currentLength}/${maxLength}`;
    
    // Add warning class when approaching limit
    if (currentLength > maxLength * 0.9) {
        counter.classList.add('warning');
    } else {
        counter.classList.remove('warning');
    }
    
    // Add danger class when at limit
    if (currentLength >= maxLength) {
        counter.classList.add('danger');
    } else {
        counter.classList.remove('danger');
    }
}