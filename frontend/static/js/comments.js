// -------------------- MANILA TIME CONVERSION --------------------
function toManilaTime(isoString) {
  const date = new Date(isoString);
  const options = {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  };
  return date.toLocaleString("en-PH", options);
}

// -------------------- COMMENTS TOGGLE --------------------
function toggleComments(el) {
  const post = el.closest(".post");
  if (!post) return;
  post.classList.toggle("show-expanded");
}

// -------------------- COMMENT MENU TOGGLE --------------------
let openCommentMenu = null;
function toggleCommentMenu(commentId) {
  const menu = document.getElementById(`comment-menu-${commentId}`);
  if (!menu) return;

  if (openCommentMenu && openCommentMenu !== menu) {
    openCommentMenu.style.display = "none";
  }

  if (menu.style.display === "none" || menu.style.display === "") {
    menu.style.display = "block";
    openCommentMenu = menu;
  } else {
    menu.style.display = "none";
    openCommentMenu = null;
  }
}


// -------------------- COMMENT VOTING SYSTEM --------------------
function voteComment(commentId, type, btn) {
  try {
    const container = btn.closest(".comment-votes");
    if (!container) return;

    const voteCountElem = container.querySelector(".comment-vote-count");
    const upBtn = container.querySelector(".comment-upvote");
    const downBtn = container.querySelector(".comment-downvote");

    if (btn && btn.tagName === "BUTTON") btn.type = "button";

    const oldValue = voteCountElem?.textContent.trim() || "0";
    if (voteCountElem) voteCountElem.textContent = oldValue;

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
        if (!data || data.error) {
          console.error(data?.error || "Vote error");
          return;
        }

        const newVotes = (data.net_votes !== undefined && data.net_votes !== null) 
                          ? data.net_votes 
                          : oldValue;

        if (voteCountElem) {
          voteCountElem.textContent = newVotes;
          voteCountElem.style.opacity = "1"; // force visible
          voteCountElem.animate(
            [
              { transform: "scale(1)", opacity: 1 },
              { transform: "scale(1.2)", opacity: 1 },
              { transform: "scale(1)", opacity: 1 }
            ],
            { duration: 180 }
          );
        }

        if (upBtn) upBtn.classList.remove("active-upvote");
        if (downBtn) downBtn.classList.remove("active-downvote");

        if (data.user_vote === "upvote") upBtn?.classList.add("active-upvote");
        else if (data.user_vote === "downvote") downBtn?.classList.add("active-downvote");
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



// -------------------- REPLY FORM TOGGLE --------------------
let openReplyForm = null;
function toggleReplyForm(commentId) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (!form) return;

  if (openReplyForm && openReplyForm !== form) openReplyForm.style.display = "none";

  if (form.style.display === "none" || form.style.display === "") {
    form.style.display = "flex";
    const t = form.querySelector('textarea, input[type="text"]');
    if (t) t.focus();
    openReplyForm = form;
  } else {
    form.style.display = "none";
    openReplyForm = null;
  }
}



// -------------------- CLOSE MENUS ON OUTSIDE CLICK --------------------
document.addEventListener("click", function(e) {
  if (!e.target.classList.contains("comment-menu-btn")) {
    document.querySelectorAll(".comment-menu").forEach(menu => menu.style.display = "none");
    openCommentMenu = null;
  }

  document.querySelectorAll(".sort-menu").forEach(menu => {
    if (!menu.closest(".sort-dropdown").contains(e.target)) menu.classList.remove("show");
  });
});

// -------------------- EDIT FORM TOGGLE --------------------
function toggleEditForm(commentId) {
  const form = document.getElementById(`edit-form-${commentId}`);
  const text = document.getElementById(`comment-text-${commentId}`);
  if (!form || !text) return;

  if (form.style.display === "none" || form.style.display === "") {
    form.style.display = "flex";
    text.style.display = "none";
  } else {
    form.style.display = "none";
    text.style.display = "block";
  }
}

function cancelEdit(commentId) {
  const form = document.getElementById(`edit-form-${commentId}`);
  const text = document.getElementById(`comment-text-${commentId}`);
  if (!form || !text) return;
  form.style.display = "none";
  text.style.display = "block";
}

// -------------------- SORT DROPDOWN --------------------
function toggleSortMenu(button) {
  const sortDropdown = button.closest(".sort-dropdown");
  const sortMenu = sortDropdown.querySelector(".sort-menu");
  sortMenu.classList.toggle("show");
}

function selectSortOption(option, el, postId) {
  const dropdown = el.closest(".sort-dropdown");
  const selectedSort = dropdown.querySelector(".selected-sort");
  const sortMenu = dropdown.querySelector(".sort-menu");
  selectedSort.textContent = option;
  sortMenu.classList.remove("show");
  sortComments(postId, option.toLowerCase());
}

function sortComments(postId, sortType) {
  const commentList = document.getElementById(`comments-list-${postId}`);
  if (!commentList) return;

  const topLevelComments = Array.from(commentList.children)
    .filter(el => el.classList.contains("comment") && !el.closest(".replies"));

  topLevelComments.sort((a, b) => {
    const aVotes = parseInt(a.dataset.votes) || 0;
    const bVotes = parseInt(b.dataset.votes) || 0;
    const aTime = new Date(a.dataset.created).getTime();
    const bTime = new Date(b.dataset.created).getTime();

    if (sortType === "top") return bVotes - aVotes;
    if (sortType === "new") return bTime - aTime;
    if (sortType === "oldest") return aTime - bTime;
    return 0;
  });

  commentList.innerHTML = "";
  topLevelComments.forEach(c => commentList.appendChild(c));
}

// -------------------- CSRF HELPER --------------------
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

// -------------------- APPLY MANILA TIME --------------------
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".comment-time-local").forEach(el => {
    const iso = el.getAttribute("data-time");
    if (iso) el.textContent = toManilaTime(iso);
  });
});

// -------------------- TOGGLE MORE REPLIES --------------------
function toggleMoreComments(commentId) {
  const hiddenReplies = document.getElementById(`hidden-replies-${commentId}`);
  const moreRepliesBtn = document.querySelector(`.more-replies[data-comment-id='${commentId}']`);

  if (hiddenReplies.style.display === "none" || hiddenReplies.style.display === "") {
    hiddenReplies.style.display = "block";
    moreRepliesBtn.textContent = "Show Less Comments";
  } else {
    hiddenReplies.style.display = "none";
    moreRepliesBtn.textContent = "Show More Comments";
  }
}

// -------------------- LIVE COMMENT CHARACTER VALIDATION & AUTO-RESIZE --------------------
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll(".comment-form, .reply-form, .edit-form");

  forms.forEach(form => {
    const textarea = form.querySelector("textarea[name='comment']");
    if (!textarea) return;

    // Create counter/error display element (only once)
    let counter = textarea.nextElementSibling;
    if (!counter || !counter.classList || !counter.classList.contains("comment-error")) {
      counter = document.createElement("div");
      counter.className = "comment-error";
      textarea.after(counter);
    }
    counter.textContent = "0 / 300";

    // Auto-resize function
    function resizeTextarea() {
      textarea.style.height = "auto";
      textarea.style.height = textarea.scrollHeight + "px";
    }

    textarea.addEventListener("input", () => {
      let value = textarea.value;

      // Hard limit
      if (value.length > 300) value = value.slice(0, 300);
      textarea.value = value;

      // Update counter/error text
      counter.textContent = `${value.length} / 300${value.length === 300 ? " - Maximum reached" : ""}`;
      if (value.length === 300) counter.classList.add("maxed");
      else counter.classList.remove("maxed");

      // Resize textarea
      resizeTextarea();
    });

    // Initialize height
    resizeTextarea();
  });

  // ----- CHANGED ----- Ensure all vote buttons are type="button" to prevent accidental submits
  document.querySelectorAll(".comment-upvote, .comment-downvote").forEach(b => {
    if (b.tagName === "BUTTON") b.type = "button";
  });
});

// -------------------- Small helper used for dynamic textareas --------------------
function resizeInput(input) {
  input.style.height = "auto"; // reset first
  input.style.height = input.scrollHeight + "px"; // grow only textarea
}

// Initialize existing textareas if any were added outside DOMContentLoaded
document.querySelectorAll(".comment-form textarea, .reply-form textarea").forEach(input => {
  input.addEventListener("input", () => {
    if (input.value.length > 300) input.value = input.value.slice(0, 300); // hard limit
    resizeInput(input);
  });

  // initialize height
  resizeInput(input);
});
