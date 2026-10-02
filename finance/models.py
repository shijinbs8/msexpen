from django.db import models
from django.utils import timezone
from django.conf import settings

class Category(models.Model):
    TYPE_CHOICES = (
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
    )

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='EXPENSE')
    icon = models.CharField(max_length=50, default='📦', help_text="Emoji or icon identifier")
    color = models.CharField(max_length=20, default='#6C757D', help_text="Hex color code for badges & charts")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['category_type', 'name']

    def __str__(self):
        return f"{self.icon} {self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('EXPENSE', 'Expense'),
        ('INCOME', 'Income'),
    )

    PAYMENT_CHOICES = (
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('CARD', 'Card'),
        ('UPI', 'UPI / Online'),
        ('OTHER', 'Other'),
    )

    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='EXPENSE')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    description = models.CharField(max_length=255, blank=True, default='')
    transaction_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='CASH')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        cat_name = self.category.name if self.category else "Uncategorized"
        return f"{self.transaction_type}: {self.amount} - {cat_name} ({self.transaction_date})"


class Budget(models.Model):
    BUDGET_TYPE_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    )

    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_budget_type_display()} Budget: {self.amount}"


class AppSetting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_setting(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return getattr(settings, key, default)

    @classmethod
    def set_setting(cls, key, value, description=''):
        obj, _ = cls.objects.update_or_create(key=key, defaults={'value': str(value), 'description': description})
        return obj
