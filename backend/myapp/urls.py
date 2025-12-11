from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),

    # AUTH
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('recover/', views.recover_password_page, name='recover-password'),
    path('reset-password/<str:reset_token>/', views.reset_password_page, name='reset-password'),

    # HOME
    path('home/', views.home_page, name='home'),

    # ADMIN
    path('dashboard/', views.admin_page, name='admin'),
    path('dashboard/api/subject-posts/', views.admin_subject_posts, name='admin_subject_posts'),
    path('dashboard/api/update-report/', views.admin_update_report, name='admin_update_report'),
    path('dashboard/api/update-comment-report/', views.admin_update_comment_report, name='admin_update_comment_report'),
    path('dashboard/api/all-posts/', views.admin_all_posts, name='admin_all_posts'),
    path('dashboard/api/admin-delete-post/', views.admin_delete_post, name='admin_delete_post'),
    path('dashboard/api/admin-delete-comment/', views.admin_delete_comment, name='admin_delete_comment'),

    # POSTS
    path('create-post-text/', views.create_post_text, name='create-post-text'),
    path('create-post-image-video/', views.create_post_image, name='create-post-image-video'),
    path('create-post-link/', views.create_post_link, name='create-post-link'),

    # 🔥 ADD THESE (Fix Reverse URL Errors)
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),

    # REPORTING
    path('report_post/', views.report_post, name='report_post'),
    path('report_comment/', views.report_comment, name='report_comment'),

    # Diagnostics
    path('diagnostics/', views.diagnostics, name='diagnostics'),

    # POST VOTING
    path("vote_post/<int:post_id>/<str:vote_type>/", views.vote_post, name="vote_post"),

    # COMMENTS
    path('edit_comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('vote_comment/<int:comment_id>/<str:vote_type>/', views.vote_comment, name='vote_comment'),
    
]
