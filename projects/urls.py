from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='home'),
    path('create/', views.project_create, name='create'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_edit, name='edit'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
    path('search/', views.project_search, name='search'),
    path('category/<int:category_id>/', views.project_list_by_category, name='by_category'),
    # Also handle singular 'project' URLs
    path('project/create/', views.project_create, name='create_singular'),
]

