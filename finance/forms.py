from django import forms
from django.utils import timezone
from .models import Transaction, Category, Budget

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'category', 'description', 'transaction_date', 'payment_method', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_transaction_type'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input-lg form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'inputmode': 'decimal',
                'required': 'required'
            }),
            'category': forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_category'}),
            'description': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. Lunch at Cafe, Salary, Taxi'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes or receipt references'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('transaction_date') and not self.instance.pk:
            self.initial['transaction_date'] = timezone.now().strftime('%Y-%m-%d')
        
        # Populate categories nicely with icons
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('category_type', 'name')
        self.fields['category'].empty_label = "-- Select Category --"

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['budget_type', 'amount']
        widgets = {
            'budget_type': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'inputmode': 'decimal'
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount < 0:
            raise forms.ValidationError("Budget amount cannot be negative.")
        return amount


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emoji like 🍕, 🚗'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
