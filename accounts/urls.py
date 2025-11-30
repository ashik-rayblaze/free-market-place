from django.urls import path
from . import views
from . import admin_views
from pages import views as pages_views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Admin URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', admin_views.admin_user_list, name='admin_users'),
    path('admin/users/<int:pk>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('admin/projects/', admin_views.admin_project_list, name='admin_projects'),
    path('admin/bids/', admin_views.admin_bid_list, name='admin_bids'),
    path('admin/transactions/', admin_views.admin_transaction_list, name='admin_transactions'),
    path('admin/reports/', admin_views.admin_report_list, name='admin_reports'),
    path('admin/wallets/', admin_views.admin_wallet_list, name='admin_wallets'),
    path('admin/categories/', admin_views.admin_category_list, name='admin_categories'),
    # Static Pages Admin
    path('admin/pages/', pages_views.admin_page_list, name='admin_pages'),
    path('admin/pages/create/', pages_views.admin_page_create, name='admin_page_create'),
    path('admin/pages/<int:pk>/edit/', pages_views.admin_page_edit, name='admin_page_edit'),
    path('admin/pages/<int:pk>/delete/', pages_views.admin_page_delete, name='admin_page_delete'),
]

