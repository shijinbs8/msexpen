from django.contrib import admin
from .models import Category, Transaction, Budget, AppSetting

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'category_type', 'color', 'is_active', 'created_at')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name',)
    ordering = ('category_type', 'name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'transaction_type', 'amount', 'category', 'description', 'payment_method')
    list_filter = ('transaction_type', 'payment_method', 'transaction_date', 'category')
    search_fields = ('description', 'notes')
    date_hierarchy = 'transaction_date'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('budget_type', 'amount', 'is_active', 'created_at')
    list_filter = ('budget_type', 'is_active')

@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'value')
