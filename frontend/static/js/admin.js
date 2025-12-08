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
            supabase.from('reports').select('*', { count: 'exact' }),
            supabase.from('subjects').select('*', { count: 'exact' })
        ]);

        // Fetch recent posts
        const { data: recentPosts } = await supabase
            .from('posts')
            .select('*, author:users(*)')
            .order('created_at', { ascending: false })
            .limit(5);

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
        if (dashboardData.recentPosts.length > 0) {
            recentPostsContainer.innerHTML = dashboardData.recentPosts.map(post => `
                <div class="recent-post">
                    <div class="post-header">
                        <span class="post-author">${escapeHtml(post.author?.username || 'Unknown')}</span>
                        <span class="post-date">${new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                    <p class="post-preview">${escapeHtml(post.content?.substring(0, 100) || '')}${post.content?.length > 100 ? '...' : ''}</p>
                </div>
            `).join('');
        } else {
            recentPostsContainer.innerHTML = '<p class="no-data">No recent posts found</p>';
        }
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
            
            if (data.posts && data.posts.length > 0) {
                let postsHTML = '<div class="posts-list">';
                data.posts.forEach(post => {
                    const postDate = post.created_at ? new Date(post.created_at).toLocaleDateString() : 'Unknown date';
                    const postContent = post.content ? post.content.substring(0, 200) : '';
                    const contentEllipsis = post.content && post.content.length > 200 ? '...' : '';
                    
                    postsHTML += `
                        <div class="post-item">
                            <h4>${escapeHtml(post.title || 'Untitled Post')}</h4>
                            <p>By: ${escapeHtml(post.username || 'Unknown')} • ${postDate}</p>
                            ${postContent ? `<p class="post-content">${escapeHtml(postContent)}${contentEllipsis}</p>` : ''}
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

// Report Filter
function filterReports() {
    const filterValue = document.getElementById('report-filter').value;
    const reportCards = document.querySelectorAll('.report-card');
    
    reportCards.forEach(card => {
        const status = card.dataset.status;
        
        if (filterValue === 'all' || status === filterValue) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
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

// View User Details
function viewUserDetails(userId) {
    // This could open a modal with more user details
    alert(`User details view for user ID: ${userId}\n\nThis feature could be expanded to show:\n- User profile\n- Post history\n- Activity log\n- Ban/unban options`);
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('subjectModal');
    if (event.target === modal) {
        closeSubjectModal();
    }
}

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSubjectModal();
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