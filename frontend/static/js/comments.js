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
  post.classList.toggle("show-expanded");
}

// -------------------- COMMENT VOTING SYSTEM --------------------
function voteComment(commentId, type, btn) {
  const container = btn.closest(".comment-votes");
  const voteCountElem = container.querySelector(".comment-vote-count");
  const upBtn = container.querySelector(".comment-upvote");
  const downBtn = container.querySelector(".comment-downvote");

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
      if (data.error) {
        console.error(data.error);
        return;
      }

      voteCountElem.textContent = data.net_votes;

      upBtn.classList.remove("active-upvote");
      downBtn.classList.remove("active-downvote");

      if (data.user_vote === "upvote") {
        upBtn.classList.add("active-upvote");
        upBtn.animate([{ transform: "scale(1)" }, { transform: "scale(1.2)" }, { transform: "scale(1)" }], { duration: 200 });
      } else if (data.user_vote === "downvote") {
        downBtn.classList.add("active-downvote");
        downBtn.animate([{ transform: "scale(1)" }, { transform: "scale(1.2)" }, { transform: "scale(1)" }], { duration: 200 });
      }
    })
    .catch(err => console.error("Comment vote error:", err));
}

// -------------------- REPLY FORM TOGGLE --------------------
let openReplyForm = null;
function toggleReplyForm(commentId) {
  const form = document.getElementById(`reply-form-${commentId}`);
  if (!form) return;

  if (openReplyForm && openReplyForm !== form) openReplyForm.style.display = "none";

  if (form.style.display === "none" || form.style.display === "") {
    form.style.display = "flex";
    form.querySelector('input[type="text"]').focus();
    openReplyForm = form;
  } else {
    form.style.display = "none";
    openReplyForm = null;
  }
}

// -------------------- COMMENT MENU TOGGLE --------------------
let openCommentMenu = null;
function toggleCommentMenu(commentId) {
  const menu = document.getElementById(`comment-menu-${commentId}`);
  if (!menu) return;

  if (openCommentMenu && openCommentMenu !== menu) openCommentMenu.style.display = "none";

  if (menu.style.display === "none" || menu.style.display === "") {
    menu.style.display = "block";
    openCommentMenu = menu;
  } else {
    menu.style.display = "none";
    openCommentMenu = null;
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

// -------------------- REDDIT-STYLE PERSISTENT VOTING --------------------
document.addEventListener("DOMContentLoaded", () => {
  const savedVotes = JSON.parse(localStorage.getItem("userVotes")) || {};

  // Restore votes for posts and comments
  Object.entries(savedVotes).forEach(([id, type]) => {
    const container = document.querySelector(`[data-vote-id="${id}"]`);
    if (!container) return;
    const upBtn = container.querySelector(".vote-btn.upvote, .comment-upvote");
    const downBtn = container.querySelector(".vote-btn.downvote, .comment-downvote");
    if (type === "up") upBtn?.classList.add("active-upvote");
    if (type === "down") downBtn?.classList.add("active-downvote");
  });

  // Handle click events for all vote buttons
  document.querySelectorAll(".vote-btn, .comment-upvote, .comment-downvote").forEach(btn => {
    btn.addEventListener("click", () => {
      const container = btn.closest("[data-vote-id]");
      if (!container) return;

      const id = container.dataset.voteId;
      const voteCountEl = container.querySelector(".vote-count, .comment-vote-count");
      const upBtn = container.querySelector(".vote-btn.upvote, .comment-upvote");
      const downBtn = container.querySelector(".vote-btn.downvote, .comment-downvote");

      let count = parseInt(voteCountEl?.textContent || "0");
      const currentVote = savedVotes[id];
      const isUp = btn.classList.contains("upvote") || btn.classList.contains("comment-upvote");
      const newVote = isUp ? "up" : "down";

      if (currentVote === newVote) {
        // Remove vote
        delete savedVotes[id];
        btn.classList.remove("active-upvote", "active-downvote");
        count += isUp ? -1 : 1;
      } else {
        // Apply new vote
        if (newVote === "up") {
          upBtn.classList.add("active-upvote");
          downBtn.classList.remove("active-downvote");
          count += currentVote === "down" ? 2 : 1;
        } else {
          downBtn.classList.add("active-downvote");
          upBtn.classList.remove("active-upvote");
          count -= currentVote === "up" ? 2 : 1;
        }
        savedVotes[id] = newVote;
      }

      // Animate the clicked button
      btn.animate([{ transform: "scale(1)" }, { transform: "scale(1.2)" }, { transform: "scale(1)" }], { duration: 180 });

      // Update count and save
      if (voteCountEl) voteCountEl.textContent = count;
      localStorage.setItem("userVotes", JSON.stringify(savedVotes));
    });
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
