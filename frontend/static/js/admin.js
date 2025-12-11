// Admin Dashboard JavaScript - WITH SUPABASE INTEGRATION

// Initialize Supabase client
// Admin Dashboard JS

const SUPABASE_URL = "https://tkyztssepvewbmgsaaeq.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRreXp0c3NlcHZld2JtZ3NhYWVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzODQ4NjMsImV4cCI6MjA3NDk2MDg2M30.uwxitzioVAWuNENFGnVwuXcQyvbXi6AdfjwYg-suoA8";

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Dashboard data cache
let dashboardData = {
    totalUsers: 0,
    totalPosts: 0,
    totalReports: 0,
    activeSubjects: 0,
    recentPosts: [],
    recentReports: []
};

// Fetch dashboard data from Supabase
async function fetchDashboardData() {
    try {
        // Show loading state
        document.querySelectorAll('.dashboard-box h3').forEach(el => {
            el.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        });

        // Fetch counts in parallel
        const [usersData, postsData, reportsData, subjectsData] = await Promise.all([
            supabase.from('users').select('*', { count: 'exact' }),
            supabase.from('posts').select('*', { count: 'exact' }),
            // Use the real reports table in Supabase for counting
            supabase.from('post_reports').select('*', { count: 'exact' }),
            supabase.from('subjects').select('*', { count: 'exact' })
        ]);

        // Fetch recent posts
        const recentPosts = [];

        // Update dashboard data
        dashboardData = {
            totalUsers: usersData.count || 0,
            totalPosts: postsData.count || 0,
            totalReports: reportsData.count || 0,
            activeSubjects: subjectsData.count || 0,
            recentPosts: recentPosts || []
        };

        // Update UI
        updateDashboardUI();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Show error state
        document.querySelectorAll('.dashboard-box h3').forEach(el => {
            el.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
        });
    }
}

// Update dashboard UI with fetched data
function updateDashboardUI() {
    // Update counters
    document.querySelector('.users-box h3').textContent = dashboardData.totalUsers.toLocaleString();
    document.querySelector('.posts-box h3').textContent = dashboardData.totalPosts.toLocaleString();
    document.querySelector('.reports-box h3').textContent = dashboardData.totalReports.toLocaleString();
    document.querySelector('.subjects-box h3').textContent = dashboardData.activeSubjects.toLocaleString();

    // Update recent posts
    const recentPostsContainer = document.getElementById('recent-posts');
    if (recentPostsContainer) {
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load dashboard data
    fetchDashboardData();
    
    // Set up auto-refresh every 5 minutes
    setInterval(fetchDashboardData, 5 * 60 * 1000);
});

// Tab Navigation - FIXED: Added event parameter
function showTab(tabName, event) {
    // Prevent default link behavior
    if (event) {
        event.preventDefault();
    }
    
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active class from all nav links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => link.classList.remove('active'));
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked nav link
    if (event) {
        event.target.closest('.nav-link').classList.add('active');
    }
}

// User Search
function searchUsers() {
    const searchTerm = document.getElementById('user-search').value.toLowerCase();
    const userCards = document.querySelectorAll('.user-card');
    
    userCards.forEach(card => {
        const username = card.dataset.username || '';
        const email = card.dataset.email || '';
        
        if (username.includes(searchTerm) || email.includes(searchTerm)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Get CSRF Token - FIXED: Better token retrieval
function getCSRFToken() {
    // Try meta tag first
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // Fallback to hidden input
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (inputToken) {
        return inputToken.value;
    }
    
    // Fallback to cookie
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    
    return cookieValue ? cookieValue.split('=')[1] : '';
}

// Subject Details Modal - FIXED: Better error handling
function showSubjectDetails(subject) {
    const modal = document.getElementById('subjectModal');
    const modalTitle = document.getElementById('subjectModalTitle');
    const modalBody = document.getElementById('subjectModalBody');

    if (!modal || !modalTitle || !modalBody) {
        console.error('Modal elements not found');
        return;
    }

    modalTitle.textContent = subject + ' Posts';
    modalBody.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading posts...</div>';

    // Fetch posts for this subject
    fetch(`/dashboard/api/subject-posts/?subject=${encodeURIComponent(subject)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            const posts = Array.isArray(data.posts) ? data.posts : [];

            if (posts.length > 0) {
                let postsHTML = '<div class="posts-list">';
                posts.forEach(post => {
                    const title = post.title || 'Untitled Post';
                    const author = post.author || 'Unknown';

                    let createdDisplay = 'Unknown date';
                    if (post.created_at) {
                        try {
                            createdDisplay = new Date(post.created_at).toLocaleString();
                        } catch (e) {
                            createdDisplay = String(post.created_at);
                        }
                    }

                    const description = post.description || '';
                    let descriptionHtml = '';
                    if (description) {
                        const snippet = description.length > 200 ? description.slice(0, 200) + '...' : description;
                        descriptionHtml = `<p class="post-content">${escapeHtml(snippet)}</p>`;
                    }

                    let mediaHtml = '';
                    const url = post.url || '';
                    if (url) {
                        const safeUrl = escapeHtml(url);
                        if (post.is_image) {
                            mediaHtml = `
                                <div class="report-media">
                                    <img src="${safeUrl}" alt="Post image">
                                </div>
                            `;
                        } else if (post.is_video) {
                            mediaHtml = `
                                <div class="report-media">
                                    <video src="${safeUrl}" controls muted></video>
                                </div>
                            `;
                        } else {
                            mediaHtml = `
                                <p class="post-content">
                                    <strong>Link:</strong>
                                    <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${safeUrl}</a>
                                </p>
                            `;
                        }
                    }

                    postsHTML += `
                        <div class="post-item">
                            <h4>${escapeHtml(title)}</h4>
                            <p>By: ${escapeHtml(author)} • ${escapeHtml(createdDisplay)}</p>
                            ${descriptionHtml}
                            ${mediaHtml}
                        </div>
                    `;
                });
                postsHTML += '</div>';
                modalBody.innerHTML = postsHTML;
            } else {
                modalBody.innerHTML = '<div class="no-data"><i class="fas fa-file-alt"></i><p>No posts found for this subject.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error fetching subject posts:', error);
            modalBody.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i><p>Error loading posts: ${escapeHtml(error.message)}</p></div>`;
        });

    modal.style.display = 'block';
}

function closeSubjectModal() {
    const modal = document.getElementById('subjectModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Toggle between Post Reports and Comment Reports
function showReportSection(sectionName) {
    const postSection = document.getElementById('post-reports-section');
    const commentSection = document.getElementById('comment-reports-section');

    if (!postSection || !commentSection) {
        return;
    }

    const postBtn = document.getElementById('toggle-post-reports');
    const commentBtn = document.getElementById('toggle-comment-reports');

    if (sectionName === 'posts') {
        postSection.classList.add('active');
        commentSection.classList.remove('active');
        if (postBtn) postBtn.classList.add('active');
        if (commentBtn) commentBtn.classList.remove('active');
    } else if (sectionName === 'comments') {
        commentSection.classList.add('active');
        postSection.classList.remove('active');
        if (commentBtn) commentBtn.classList.add('active');
        if (postBtn) postBtn.classList.remove('active');
    }

    const activeSection = sectionName === 'posts' ? postSection : commentSection;
    if (activeSection) {
        const list = activeSection.querySelector('.reports-list');
        if (list) {
            list.scrollTop = 0;
        }
    }
}

// Report Filters (Posts & Comments)
function filterReports() {
    // Convenience wrapper if we ever want to re-use a global filter
    filterPostReports();
    filterCommentReports();
}

function filterPostReports() {
    const section = document.getElementById('post-reports-section');
    if (!section) return;

    const searchInput = document.getElementById('post-report-search');
    const filterSelect = document.getElementById('post-report-filter');

    const term = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const statusFilter = filterSelect ? filterSelect.value : 'all';

    const cards = section.querySelectorAll('.report-card');
    cards.forEach(card => {
        const status = (card.dataset.status || '').toLowerCase();
        const matchesStatus = statusFilter === 'all' || status === statusFilter;

        const text = card.textContent ? card.textContent.toLowerCase() : '';
        const matchesSearch = !term || text.includes(term);

        card.style.display = matchesStatus && matchesSearch ? 'block' : 'none';
    });
}

function filterCommentReports() {
    const section = document.getElementById('comment-reports-section');
    if (!section) return;

    const searchInput = document.getElementById('comment-report-search');
    const filterSelect = document.getElementById('comment-report-filter');

    const term = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const statusFilter = filterSelect ? filterSelect.value : 'all';

    const cards = section.querySelectorAll('.report-card');
    cards.forEach(card => {
        const status = (card.dataset.status || '').toLowerCase();
        const matchesStatus = statusFilter === 'all' || status === statusFilter;

        const text = card.textContent ? card.textContent.toLowerCase() : '';
        const matchesSearch = !term || text.includes(term);

        card.style.display = matchesStatus && matchesSearch ? 'block' : 'none';
    });
}

// Update Report Status - FIXED: Better error handling and CSRF token
function updateReportStatus(reportId, newStatus) {
    if (!confirm(`Are you sure you want to mark this report as ${newStatus.replace('_', ' ')}?`)) {
        return;
    }
    
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }
    
    const formData = new FormData();
    formData.append('report_id', reportId);
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Show loading state
    const reportCard = document.querySelector(`[data-report-id="${reportId}"]`);
    if (reportCard) {
        reportCard.style.opacity = '0.5';
        reportCard.style.pointerEvents = 'none';
    }
    
    fetch('/dashboard/api/update-report/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin' // Important for CSRF
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload the page to show updated status
            location.reload();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error updating report status:', error);
        alert(`Error updating report status: ${error.message}`);
        
        // Restore card state
        if (reportCard) {
            reportCard.style.opacity = '1';
            reportCard.style.pointerEvents = 'auto';
        }
    });
}

// Update Comment Report Status
function updateCommentReportStatus(reportId, newStatus) {
    if (!confirm(`Are you sure you want to mark this comment report as ${newStatus.replace('_', ' ')}?`)) {
        return;
    }

    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }

    const formData = new FormData();
    formData.append('report_id', reportId);
    formData.append('status', newStatus);
    formData.append('csrfmiddlewaretoken', csrfToken);

    const reportCard = document.querySelector(`[data-comment-report-id="${reportId}"]`);
    if (reportCard) {
        reportCard.style.opacity = '0.5';
        reportCard.style.pointerEvents = 'none';
    }

    fetch('/dashboard/api/update-comment-report/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error updating comment report status:', error);
        alert(`Error updating comment report status: ${error.message}`);

        if (reportCard) {
            reportCard.style.opacity = '1';
            reportCard.style.pointerEvents = 'auto';
        }
    });
}

// Admin delete post (from Reports tab)
function adminDeletePost(postId) {
    if (!confirm('Are you sure you want to permanently delete this post? This action cannot be undone.')) {
        return;
    }

    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }

    const formData = new FormData();
    formData.append('post_id', postId);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/dashboard/api/admin-delete-post/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Reload to remove the deleted post's reports from the UI
            location.reload();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error deleting post:', error);
        alert(`Error deleting post: ${error.message}`);
    });
}

// Admin delete comment (from Comment Reports section)
function adminDeleteComment(commentId) {
    if (!confirm('Are you sure you want to permanently delete this comment? This action cannot be undone.')) {
        return;
    }

    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }

    const formData = new FormData();
    formData.append('comment_id', commentId);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/dashboard/api/admin-delete-comment/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error deleting comment:', error);
        alert(`Error deleting comment: ${error.message}`);
    });
}

// View User Details
function viewUserDetails(userId) {
    const modal = document.getElementById('userDetailModal');
    const titleEl = document.getElementById('userModalTitle');
    const bodyEl = document.getElementById('userModalBody');
    const footerEl = document.getElementById('userModalFooter');

    if (!modal || !titleEl || !bodyEl || !footerEl) {
        console.error('User detail modal elements not found');
        return;
    }

    titleEl.textContent = 'Loading user...';
    bodyEl.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading user details...</div>';
    footerEl.innerHTML = '';

    fetch(`/dashboard/api/user/${userId}/`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.error) {
                throw new Error(data && data.error ? data.error : 'Failed to load user');
            }

            const user = data.user || {};
            const stats = data.stats || {};
            const posts = Array.isArray(data.posts) ? data.posts : [];

            const role = (user.role || 'student').toLowerCase();
            const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
            const joined = user.date_joined || 'Unknown';
            const lastLogin = user.last_login || 'Never';
            const bio = user.bio || '';

            titleEl.textContent = user.username || user.email || 'User Details';

            let postsHtml = '';
            if (posts.length > 0) {
                const limited = posts.slice(0, 10);
                postsHtml = '<ul class="user-post-list">' +
                    limited.map(p => {
                        const subj = p.subject || 'Unknown';
                        const created = p.created_at || '';
                        return `
                            <li class="user-post-item">
                                <div class="user-post-title">${escapeHtml(p.title || '(No Title)')}</div>
                                <div class="user-post-meta">${escapeHtml(subj)} • ${escapeHtml(created)}</div>
                            </li>
                        `;
                    }).join('') +
                    '</ul>';
            } else {
                postsHtml = '<p class="no-data">No posts yet.</p>';
            }

            bodyEl.innerHTML = `
                <div class="user-modal-grid">
                    <div class="user-profile-summary">
                        <div class="user-modal-avatar"><i class="fas fa-user-circle"></i></div>
                        <h4>${escapeHtml(user.username || user.email || 'User')}</h4>
                        <p class="user-modal-email">${escapeHtml(user.email || '')}</p>
                        <span class="user-role-label user-role-${role}">Role: ${escapeHtml(roleLabel)}</span>
                        <div class="user-meta">
                            <p><strong>Joined:</strong> ${escapeHtml(joined)}</p>
                            <p><strong>Last login:</strong> ${escapeHtml(lastLogin)}</p>
                        </div>
                        ${bio ? `<p class="user-bio">${escapeHtml(bio)}</p>` : ''}
                        <div class="user-stats">
                            <div><strong>Posts:</strong> ${stats.post_count || 0}</div>
                            <div><strong>Comments:</strong> ${stats.comment_count || 0}</div>
                        </div>
                    </div>
                    <div class="user-post-history">
                        <h4>Recent Posts</h4>
                        ${postsHtml}
                    </div>
                </div>
            `;

            const isBanned = role === 'banned';
            const banAction = isBanned ? 'unban' : 'ban';
            const banLabel = isBanned ? 'Unban User' : 'Ban User';

            footerEl.innerHTML = `
                <button class="btn btn-secondary btn-sm" type="button" onclick="closeUserModal()">Close</button>
                <button class="btn btn-warning btn-sm" type="button" onclick="adminUpdateUser('${user.id}', '${banAction}')">${banLabel}</button>
                <button class="btn btn-danger btn-sm" type="button" onclick="adminUpdateUser('${user.id}', 'delete')">Delete User</button>
            `;
        })
        .catch(error => {
            console.error('Error loading user details:', error);
            titleEl.textContent = 'User Details';
            bodyEl.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i><p>${escapeHtml(error.message || 'Failed to load user details')}</p></div>`;
            footerEl.innerHTML = `
                <button class="btn btn-secondary btn-sm" type="button" onclick="closeUserModal()">Close</button>
            `;
        });

    modal.style.display = 'block';
}

function closeUserModal() {
    const modal = document.getElementById('userDetailModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function adminUpdateUser(userId, action) {
    let confirmText = '';
    if (action === 'ban') {
        confirmText = 'Are you sure you want to ban this user? They will no longer be able to log in.';
    } else if (action === 'unban') {
        confirmText = 'Are you sure you want to unban this user?';
    } else if (action === 'delete') {
        confirmText = 'Are you sure you want to permanently delete this user? This action cannot be undone.';
    } else {
        return;
    }

    if (!confirm(confirmText)) {
        return;
    }

    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        alert('CSRF token not found. Please refresh the page.');
        return;
    }

    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('action', action);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/dashboard/api/update-user/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.error) {
                throw new Error(data && data.error ? data.error : 'Failed to update user');
            }
            closeUserModal();
            location.reload();
        })
        .catch(error => {
            console.error('Error updating user:', error);
            alert(`Error updating user: ${error.message || error}`);
        });
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals when clicking outside
window.onclick = function(event) {
    const subjectModal = document.getElementById('subjectModal');
    if (event.target === subjectModal) {
        closeSubjectModal();
    }
    const userModal = document.getElementById('userDetailModal');
    if (event.target === userModal) {
        closeUserModal();
    }
}

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSubjectModal();
        closeUserModal();
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin page loaded');
    
    // Set initial active tab (dashboard by default)
    const urlHash = window.location.hash.substring(1) || 'dashboard';
    const tabToShow = document.getElementById(urlHash + '-tab');
    
    if (tabToShow) {
        // Hide all tabs first
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show the correct tab
        tabToShow.classList.add('active');
        
        // Update nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + urlHash) {
                link.classList.add('active');
            }
        });
    }
    
    // Log data availability for debugging
    console.log('Users found:', document.querySelectorAll('.user-card').length);
    console.log('Reports found:', document.querySelectorAll('.report-card').length);
    console.log('Subjects found:', document.querySelectorAll('.subject-box').length);
});