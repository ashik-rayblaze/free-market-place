from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:pk>/send/', views.send_message, name='send_message'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('start/project/<int:project_id>/', views.start_project_conversation, name='start_project_conversation'),
]

