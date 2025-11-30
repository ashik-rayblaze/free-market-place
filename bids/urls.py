from django.urls import path
from . import views

app_name = 'bids'

urlpatterns = [
    path('', views.bid_list, name='list'),
    path('create/<int:project_id>/', views.bid_create, name='create'),
    path('<int:pk>/', views.bid_detail, name='detail'),
    path('<int:pk>/edit/', views.bid_edit, name='edit'),
    path('<int:pk>/delete/', views.bid_delete, name='delete'),
    path('<int:pk>/accept/', views.bid_accept, name='accept'),
    path('<int:pk>/reject/', views.bid_reject, name='reject'),
    path('<int:pk>/withdraw/', views.bid_withdraw, name='withdraw'),
]

