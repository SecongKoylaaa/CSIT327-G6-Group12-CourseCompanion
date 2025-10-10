from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('home/', views.home_page, name='home'),
    path('logout/', views.logout_page, name='logout'),
    path('create-post-link/', views.create_post_link, name='create-post-link'),
    path('create-post-image/', views.create_post_image, name='create-post-image'),
]
