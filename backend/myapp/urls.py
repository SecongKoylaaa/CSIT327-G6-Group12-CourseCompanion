from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('home/', views.home_page, name='home'),
    path('logout/', views.logout_page, name='logout'),
    path('create-post-text/', views.create_post_text, name='create-post-text'),
    path('create-post-image-video/', views.create_post_image, name='create-post-image-video'),
    path('create-post-image-link/', views.create_post_link, name='create-post-link'),
    path('recover/', views.recover_password_page, name='recover-password'),
    path('reset-password/<str:reset_token>/', views.reset_password_page, name='reset-password'),
]