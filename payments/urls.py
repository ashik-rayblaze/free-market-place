from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_dashboard, name='dashboard'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/add-funds/', views.add_funds, name='add_funds'),
    path('wallet/withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('methods/', views.payment_methods, name='methods'),
    path('methods/add/', views.add_payment_method, name='add_method'),
    path('methods/<int:pk>/set-default/', views.set_default_payment_method, name='set_default'),
    path('methods/<int:pk>/delete/', views.delete_payment_method, name='delete_method'),
    path('transactions/', views.transaction_list, name='transactions'),
    path('escrow/<int:project_id>/', views.escrow_detail, name='escrow_detail'),
    path('escrow/<int:project_id>/release/', views.release_escrow, name='release_escrow'),
    path('escrow/<int:project_id>/refund/', views.refund_escrow, name='refund_escrow'),
]

