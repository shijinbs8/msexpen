from decimal import Decimal
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Max, Q
from .models import Transaction, Category, Budget, AppSetting

def get_currency():
    """Returns the default currency configured in settings (default AED)."""
    return AppSetting.get_setting('DEFAULT_CURRENCY', 'AED')

def format_currency(amount):
    """Formats numeric amount as string with currency, e.g. AED 1,250.00"""
    currency = get_currency()
    if amount is None:
        amount = Decimal('0.00')
    return f"{currency} {float(amount):,.2f}"

def get_current_balance():
    """
    Calculates total balance: Total Income - Total Expenses.
    Returns Decimal value and formatted string.
    """
    income_total = Transaction.objects.filter(transaction_type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_total = Transaction.objects.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    balance = income_total - expense_total
    return {
        'income': income_total,
        'expenses': expense_total,
        'balance': balance,
        'formatted_balance': format_currency(balance),
        'formatted_income': format_currency(income_total),
        'formatted_expenses': format_currency(expense_total),
    }

def get_today_summary():
    """
    Calculates today's income, expenses, and net value.
    """
    today = timezone.now().date()
    today_txs = Transaction.objects.filter(transaction_date=today)
    income_today = today_txs.filter(transaction_type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_today = today_txs.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_today = income_today - expense_today

    return {
        'income': income_today,
        'expense': expense_today,
        'net': net_today,
        'formatted_income': format_currency(income_today),
        'formatted_expense': format_currency(expense_today),
        'formatted_net': format_currency(net_today),
    }

def get_weekly_budget_status():
    """
    Calculates current week's spending against weekly budget.
    Current week = Monday to Sunday of the active week.
    Returns status level: normal (0-60%), warning (60-80%), high (80-100%), exceeded (>100%).
    """
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday()) # Monday
    end_of_week = start_of_week + timedelta(days=6) # Sunday

    # Get budget amount
    budget_obj = Budget.objects.filter(budget_type='WEEKLY', is_active=True).first()
    budget_amount = budget_obj.amount if budget_obj else Decimal('0.00')

    # Weekly expenses
    weekly_spent = Transaction.objects.filter(
        transaction_type='EXPENSE',
        transaction_date__gte=start_of_week,
        transaction_date__lte=end_of_week
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    remaining = budget_amount - weekly_spent
    percentage_used = (weekly_spent / budget_amount * 100) if budget_amount > 0 else Decimal('0.0')
    percentage_used = float(round(percentage_used, 1))

    # Warning logic
    if budget_amount == 0:
        status_level = 'none'
        warning_msg = "No weekly budget set."
    elif percentage_used > 100:
        status_level = 'exceeded'
        over_by = weekly_spent - budget_amount
        warning_msg = f"Weekly budget exceeded by {format_currency(over_by)}"
    elif percentage_used >= 80:
        status_level = 'high'
        warning_msg = f"High spending! You have used {percentage_used}% of your weekly budget."
    elif percentage_used >= 60:
        status_level = 'warning'
        warning_msg = f"Warning: {percentage_used}% of weekly budget used."
    else:
        status_level = 'normal'
        warning_msg = f"{format_currency(remaining)} remaining this week"

    return {
        'budget_type': 'WEEKLY',
        'budget_amount': budget_amount,
        'spent': weekly_spent,
        'remaining': remaining,
        'percentage_used': percentage_used,
        'percentage_remaining': max(0.0, round(100.0 - percentage_used, 1)),
        'status_level': status_level,
        'warning_msg': warning_msg,
        'start_date': start_of_week,
        'end_date': end_of_week,
        'formatted_budget': format_currency(budget_amount),
        'formatted_spent': format_currency(weekly_spent),
        'formatted_remaining': format_currency(remaining),
    }

def get_monthly_budget_status():
    """
    Calculates current month's spending against monthly budget.
    """
    today = timezone.now().date()
    start_of_month = date(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

    budget_obj = Budget.objects.filter(budget_type='MONTHLY', is_active=True).first()
    budget_amount = budget_obj.amount if budget_obj else Decimal('0.00')

    month_txs = Transaction.objects.filter(
        transaction_date__gte=start_of_month,
        transaction_date__lte=end_of_month
    )
    monthly_income = month_txs.filter(transaction_type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_spent = month_txs.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    remaining = budget_amount - monthly_spent
    percentage_used = (monthly_spent / budget_amount * 100) if budget_amount > 0 else Decimal('0.0')
    percentage_used = float(round(percentage_used, 1))

    if budget_amount == 0:
        status_level = 'none'
        warning_msg = "No monthly budget set."
    elif percentage_used > 100:
        status_level = 'exceeded'
        over_by = monthly_spent - budget_amount
        warning_msg = f"Monthly budget exceeded by {format_currency(over_by)}"
    elif percentage_used >= 80:
        status_level = 'high'
        warning_msg = f"High spending! You have used {percentage_used}% of your monthly budget."
    elif percentage_used >= 60:
        status_level = 'warning'
        warning_msg = f"Warning: {percentage_used}% of monthly budget used."
    else:
        status_level = 'normal'
        warning_msg = f"{format_currency(remaining)} remaining this month"

    return {
        'budget_type': 'MONTHLY',
        'budget_amount': budget_amount,
        'income': monthly_income,
        'spent': monthly_spent,
        'remaining': remaining,
        'percentage_used': percentage_used,
        'percentage_remaining': max(0.0, round(100.0 - percentage_used, 1)),
        'status_level': status_level,
        'warning_msg': warning_msg,
        'start_date': start_of_month,
        'end_date': end_of_month,
        'formatted_budget': format_currency(budget_amount),
        'formatted_income': format_currency(monthly_income),
        'formatted_spent': format_currency(monthly_spent),
        'formatted_remaining': format_currency(remaining),
    }

def get_category_spending(period='month', start_date=None, end_date=None):
    """
    Returns breakdown of expenses by category for Chart.js doughnut chart.
    """
    qs = Transaction.objects.filter(transaction_type='EXPENSE')
    today = timezone.now().date()

    if start_date and end_date:
        qs = qs.filter(transaction_date__range=[start_date, end_date])
    elif period == 'today':
        qs = qs.filter(transaction_date=today)
    elif period == 'week':
        start_week = today - timedelta(days=today.weekday())
        qs = qs.filter(transaction_date__gte=start_week)
    elif period == 'month':
        start_month = date(today.year, today.month, 1)
        qs = qs.filter(transaction_date__gte=start_month)

    categories_data = qs.values(
        'category__id', 'category__name', 'category__icon', 'category__color'
    ).annotate(total=Sum('amount')).order_by('-total')

    labels = []
    data = []
    colors = []
    items = []

    palette = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#64748B']
    idx = 0

    for cat in categories_data:
        name = cat['category__name'] or 'Uncategorized'
        icon = cat['category__icon'] or '📦'
        color = cat['category__color'] or palette[idx % len(palette)]
        amount = float(cat['total'] or 0)
        
        labels.append(f"{icon} {name}")
        data.append(amount)
        colors.append(color)
        items.append({
            'name': name,
            'icon': icon,
            'color': color,
            'amount': Decimal(str(amount)),
            'formatted_amount': format_currency(Decimal(str(amount)))
        })
        idx += 1

    return {
        'labels': labels,
        'data': data,
        'colors': colors,
        'items': items,
    }

def get_income_vs_expense_data(days=30):
    """
    Returns daily timeline data of income vs expense for Chart.js bar/line chart.
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    # Initialize dates map
    dates_map = {}
    curr = start_date
    while curr <= today:
        dates_map[curr.strftime('%b %d')] = {'date_obj': curr, 'income': 0.0, 'expense': 0.0}
        curr += timedelta(days=1)

    txs = Transaction.objects.filter(transaction_date__gte=start_date, transaction_date__lte=today)
    for tx in txs:
        key = tx.transaction_date.strftime('%b %d')
        if key in dates_map:
            if tx.transaction_type == 'INCOME':
                dates_map[key]['income'] += float(tx.amount)
            else:
                dates_map[key]['expense'] += float(tx.amount)

    labels = list(dates_map.keys())
    income_data = [dates_map[k]['income'] for k in labels]
    expense_data = [dates_map[k]['expense'] for k in labels]

    return {
        'labels': labels,
        'income': income_data,
        'expense': expense_data,
    }

def get_spending_trend(days=7):
    """
    Returns spending trend over past N days.
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=days - 1)

    dates_map = {}
    curr = start_date
    while curr <= today:
        dates_map[curr.strftime('%a, %b %d')] = 0.0
        curr += timedelta(days=1)

    txs = Transaction.objects.filter(
        transaction_type='EXPENSE',
        transaction_date__gte=start_date,
        transaction_date__lte=today
    )
    for tx in txs:
        key = tx.transaction_date.strftime('%a, %b %d')
        if key in dates_map:
            dates_map[key] += float(tx.amount)

    return {
        'labels': list(dates_map.keys()),
        'data': list(dates_map.values()),
    }

def get_report_data(period='month', custom_start=None, custom_end=None):
    """
    Generates summary metrics and grouped transactions for reports.
    """
    today = timezone.now().date()
    start_date = None
    end_date = today

    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_date = date(today.year, today.month, 1)
    elif period == 'last_month':
        first_of_this_month = date(today.year, today.month, 1)
        end_date = first_of_this_month - timedelta(days=1)
        start_date = date(end_date.year, end_date.month, 1)
    elif period == 'custom' and custom_start and custom_end:
        start_date = custom_start
        end_date = custom_end
    else: # Default month
        start_date = date(today.year, today.month, 1)

    tx_qs = Transaction.objects.select_related('category').filter(
        transaction_date__gte=start_date,
        transaction_date__lte=end_date
    ).order_by('-transaction_date', '-created_at')

    income_total = tx_qs.filter(transaction_type='INCOME').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    expense_total = tx_qs.filter(transaction_type='EXPENSE').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_balance = income_total - expense_total
    total_count = tx_qs.count()

    largest_expense_tx = tx_qs.filter(transaction_type='EXPENSE').order_by('-amount').first()
    largest_expense = largest_expense_tx.amount if largest_expense_tx else Decimal('0.00')

    # Top expense category
    top_cat = tx_qs.filter(transaction_type='EXPENSE').values(
        'category__name', 'category__icon'
    ).annotate(cat_sum=Sum('amount')).order_by('-cat_sum').first()
    top_category_name = f"{top_cat['category__icon']} {top_cat['category__name']}" if top_cat and top_cat['category__name'] else "None"

    # Average daily expense
    num_days = max(1, (end_date - start_date).days + 1)
    avg_daily_expense = expense_total / Decimal(str(num_days))

    # Category breakdown
    cat_breakdown = get_category_spending(start_date=start_date, end_date=end_date)

    return {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_balance': net_balance,
        'total_count': total_count,
        'largest_expense': largest_expense,
        'top_category_name': top_category_name,
        'avg_daily_expense': avg_daily_expense,
        'formatted_income': format_currency(income_total),
        'formatted_expense': format_currency(expense_total),
        'formatted_net': format_currency(net_balance),
        'formatted_largest': format_currency(largest_expense),
        'formatted_avg_daily': format_currency(avg_daily_expense),
        'cat_breakdown': cat_breakdown,
        'transactions': tx_qs,
    }
