from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/dashboard-data/', views.chart_data_api, name='chart_data_api'),
    
    path('transactions/', views.transaction_list_view, name='transaction_list'),
    path('transactions/add/', views.transaction_add_view, name='transaction_add'),
    path('transactions/<int:pk>/edit/', views.transaction_edit_view, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete_view, name='transaction_delete'),
    path('transactions/quick-add/', views.quick_add_ajax, name='quick_add_ajax'),
    
    path('reports/', views.reports_dashboard_view, name='reports'),
    path('reports/export/<str:export_format>/', views.export_report_view, name='export_report'),
    
    path('budgets/', views.budgets_view, name='budgets'),
    path('settings/', views.settings_view, name='settings'),
    
    path('telegram/webhook/', views.telegram_webhook_view, name='telegram_webhook'),
]
