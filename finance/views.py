import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone

from .models import Transaction, Category, Budget, AppSetting
from .forms import TransactionForm, BudgetForm, CategoryForm
from .services import (
    get_currency,
    format_currency,
    get_current_balance,
    get_today_summary,
    get_weekly_budget_status,
    get_monthly_budget_status,
    get_category_spending,
    get_income_vs_expense_data,
    get_spending_trend,
    get_report_data,
)
from .reports import export_transactions_csv, export_transactions_pdf
from .telegram_bot import parse_and_process_message, send_telegram_message, is_chat_allowed

def global_settings_context(request):
    """Context processor available in all templates."""
    return {
        'CURRENCY': get_currency(),
    }

# --- DASHBOARD ---
def dashboard_view(request):
    balance_info = get_current_balance()
    today_info = get_today_summary()
    weekly_budget = get_weekly_budget_status()
    monthly_budget = get_monthly_budget_status()

    recent_transactions = Transaction.objects.select_related('category').order_by('-transaction_date', '-created_at')[:6]

    context = {
        'active_page': 'dashboard',
        'balance': balance_info,
        'today': today_info,
        'weekly_budget': weekly_budget,
        'monthly_budget': monthly_budget,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)


# --- CHART DATA API ---
def chart_data_api(request):
    """
    Returns JSON formatted data for Chart.js interactive charts.
    """
    cat_period = request.GET.get('cat_period', 'month')
    trend_days = int(request.GET.get('trend_days', 7))

    category_chart = get_category_spending(period=cat_period)
    income_vs_expense = get_income_vs_expense_data(days=30)
    spending_trend = get_spending_trend(days=trend_days)

    return JsonResponse({
        'category_chart': category_chart,
        'income_vs_expense': income_vs_expense,
        'spending_trend': spending_trend,
    })


# --- TRANSACTIONS ---
def transaction_list_view(request):
    type_filter = request.GET.get('type', 'all')
    period = request.GET.get('period', 'all')
    category_id = request.GET.get('category', '')
    search_query = request.GET.get('q', '').strip()
    custom_start = request.GET.get('start_date', '')
    custom_end = request.GET.get('end_date', '')

    qs = Transaction.objects.select_related('category').all()

    # Type filter
    if type_filter in ('INCOME', 'EXPENSE'):
        qs = qs.filter(transaction_type=type_filter)

    # Category filter
    if category_id:
        qs = qs.filter(category_id=category_id)

    # Search filter
    if search_query:
        qs = qs.filter(description__icontains=search_query)

    # Period filter
    today = timezone.now().date()
    if period == 'today':
        qs = qs.filter(transaction_date=today)
    elif period == 'week':
        start_week = today - timezone.timedelta(days=today.weekday())
        qs = qs.filter(transaction_date__gte=start_week)
    elif period == 'month':
        start_month = today.replace(day=1)
        qs = qs.filter(transaction_date__gte=start_month)
    elif period == 'custom' and custom_start and custom_end:
        try:
            s_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            e_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            qs = qs.filter(transaction_date__range=[s_date, e_date])
        except ValueError:
            pass

    qs = qs.order_by('-transaction_date', '-created_at')
    categories = Category.objects.filter(is_active=True)

    context = {
        'active_page': 'transactions',
        'transactions': qs,
        'categories': categories,
        'selected_type': type_filter,
        'selected_period': period,
        'selected_category': category_id,
        'search_query': search_query,
        'custom_start': custom_start,
        'custom_end': custom_end,
    }
    return render(request, 'transactions/list.html', context)


def transaction_add_view(request):
    initial_type = request.GET.get('type', 'EXPENSE').upper()
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save()
            messages.success(request, f"{tx.get_transaction_type_display()} of {format_currency(tx.amount)} saved successfully!")
            return redirect('transaction_list')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = TransactionForm(initial={'transaction_type': initial_type, 'transaction_date': timezone.now().strftime('%Y-%m-%d')})

    context = {
        'active_page': 'add',
        'form': form,
        'initial_type': initial_type,
    }
    return render(request, 'transactions/add.html', context)


def transaction_edit_view(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=tx)
        if form.is_valid():
            tx = form.save()
            messages.success(request, "Transaction updated successfully!")
            return redirect('transaction_list')
        else:
            messages.error(request, "Please check form errors.")
    else:
        form = TransactionForm(instance=tx)

    context = {
        'active_page': 'transactions',
        'form': form,
        'transaction': tx,
    }
    return render(request, 'transactions/edit.html', context)


def transaction_delete_view(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        tx.delete()
        messages.success(request, "Transaction deleted successfully.")
        return redirect('transaction_list')
    
    return render(request, 'transactions/delete_confirm.html', {'transaction': tx})


@csrf_exempt
def quick_add_ajax(request):
    """AJAX endpoint for floating quick-add modal."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save()
            return JsonResponse({
                'success': True,
                'message': f"Added {tx.get_transaction_type_display()} of {format_currency(tx.amount)}!"
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)


# --- REPORTS ---
def reports_dashboard_view(request):
    period = request.GET.get('period', 'month')
    custom_start_str = request.GET.get('start_date', '')
    custom_end_str = request.GET.get('end_date', '')

    custom_start = None
    custom_end = None
    if custom_start_str and custom_end_str:
        try:
            custom_start = datetime.strptime(custom_start_str, '%Y-%m-%d').date()
            custom_end = datetime.strptime(custom_end_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    report = get_report_data(period=period, custom_start=custom_start, custom_end=custom_end)

    context = {
        'active_page': 'reports',
        'report': report,
        'period': period,
        'custom_start': custom_start_str,
        'custom_end': custom_end_str,
    }
    return render(request, 'reports/dashboard.html', context)


def export_report_view(request, export_format):
    period = request.GET.get('period', 'month')
    custom_start_str = request.GET.get('start_date', '')
    custom_end_str = request.GET.get('end_date', '')

    custom_start = None
    custom_end = None
    if custom_start_str and custom_end_str:
        try:
            custom_start = datetime.strptime(custom_start_str, '%Y-%m-%d').date()
            custom_end = datetime.strptime(custom_end_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    report_data = get_report_data(period=period, custom_start=custom_start, custom_end=custom_end)

    if export_format == 'csv':
        return export_transactions_csv(report_data)
    elif export_format == 'pdf':
        return export_transactions_pdf(report_data)
    else:
        return HttpResponse("Invalid format", status=400)


# --- BUDGETS ---
def budgets_view(request):
    weekly_budget_obj = Budget.objects.filter(budget_type='WEEKLY').first()
    monthly_budget_obj = Budget.objects.filter(budget_type='MONTHLY').first()

    if request.method == 'POST':
        b_type = request.POST.get('budget_type')
        amount = request.POST.get('amount')
        try:
            amt_val = float(amount)
            if amt_val < 0:
                messages.error(request, "Budget amount cannot be negative.")
            else:
                Budget.objects.update_or_create(
                    budget_type=b_type,
                    defaults={'amount': amt_val, 'is_active': True}
                )
                messages.success(request, f"{b_type.title()} budget updated to {format_currency(amt_val)}")
                return redirect('budgets')
        except ValueError:
            messages.error(request, "Invalid budget amount entered.")

    weekly_status = get_weekly_budget_status()
    monthly_status = get_monthly_budget_status()

    context = {
        'active_page': 'settings',
        'weekly_budget_obj': weekly_budget_obj,
        'monthly_budget_obj': monthly_budget_obj,
        'weekly_status': weekly_status,
        'monthly_status': monthly_status,
    }
    return render(request, 'budgets/list.html', context)


# --- SETTINGS ---
def settings_view(request):
    categories = Category.objects.filter(is_active=True).order_by('category_type', 'name')
    bot_token = AppSetting.get_setting('TELEGRAM_BOT_TOKEN', '')
    allowed_chat_id = AppSetting.get_setting('TELEGRAM_ALLOWED_CHAT_ID', '')
    current_currency = get_currency()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_currency':
            new_curr = request.POST.get('currency', 'AED').strip().upper()
            AppSetting.set_setting('DEFAULT_CURRENCY', new_curr, 'Application default currency')
            messages.success(request, f"Currency updated to {new_curr}")
            return redirect('settings')

        elif action == 'save_telegram':
            token = request.POST.get('telegram_bot_token', '').strip()
            chat_id = request.POST.get('telegram_allowed_chat_id', '').strip()
            AppSetting.set_setting('TELEGRAM_BOT_TOKEN', token, 'Telegram Bot Token')
            AppSetting.set_setting('TELEGRAM_ALLOWED_CHAT_ID', chat_id, 'Allowed Telegram Chat ID')
            messages.success(request, "Telegram settings updated successfully.")
            return redirect('settings')

        elif action == 'add_category':
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "New category added!")
                return redirect('settings')
            else:
                messages.error(request, "Error adding category.")

    context = {
        'active_page': 'settings',
        'categories': categories,
        'bot_token': bot_token,
        'allowed_chat_id': allowed_chat_id,
        'currency': current_currency,
        'category_form': CategoryForm(),
    }
    return render(request, 'settings/settings.html', context)


# --- TELEGRAM WEBHOOK ---
@csrf_exempt
def telegram_webhook_view(request):
    """Webhook endpoint for receiving updates directly from Telegram."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            message = body.get('message', {})
            text = message.get('text', '')
            chat = message.get('chat', {})
            chat_id = chat.get('id')

            if chat_id and text:
                reply_text = parse_and_process_message(chat_id, text)
                send_telegram_message(chat_id, reply_text)

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return HttpResponse("Telegram Webhook Endpoint active.")


# --- ERROR HANDLERS ---
def handler404(request, exception=None):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)
