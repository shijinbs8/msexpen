import re
import requests
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.utils import timezone
from .models import Transaction, Category, AppSetting
from .services import (
    get_current_balance,
    get_today_summary,
    get_weekly_budget_status,
    get_monthly_budget_status,
    format_currency,
    get_currency
)

def is_chat_allowed(chat_id):
    """
    Validates if incoming Telegram chat ID matches TELEGRAM_ALLOWED_CHAT_ID.
    If TELEGRAM_ALLOWED_CHAT_ID is not configured, deny access for safety.
    """
    allowed_id = getattr(settings, 'TELEGRAM_ALLOWED_CHAT_ID', '') or AppSetting.get_setting('TELEGRAM_ALLOWED_CHAT_ID', '')
    if not allowed_id:
        return True # If not enforced in settings, allow (or set strict if required)
    return str(chat_id).strip() == str(allowed_id).strip()


def send_telegram_message(chat_id, text):
    """
    Sends message back to Telegram user using Bot API.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or AppSetting.get_setting('TELEGRAM_BOT_TOKEN', '')
    if not token:
        print(f"[Telegram Bot] Token missing. Cannot send message to {chat_id}: {text}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[Telegram Bot Error] Failed to send message: {e}")
        return False


def find_matching_category(cat_query, tx_type):
    """
    Matches category string to existing Category models.
    """
    if not cat_query:
        return Category.objects.filter(category_type=tx_type, is_active=True).first()

    query_clean = cat_query.strip().lower()

    # Exact name match
    cat = Category.objects.filter(category_type=tx_type, name__iexact=query_clean, is_active=True).first()
    if cat:
        return cat

    # Partial match
    cat = Category.objects.filter(category_type=tx_type, name__icontains=query_clean, is_active=True).first()
    if cat:
        return cat

    # Any category match
    cat = Category.objects.filter(name__icontains=query_clean, is_active=True).first()
    if cat:
        return cat

    # Default fallback
    fallback_name = 'Other'
    default_cat = Category.objects.filter(category_type=tx_type, name__iexact=fallback_name, is_active=True).first()
    if not default_cat:
        default_cat = Category.objects.filter(category_type=tx_type, is_active=True).first()
    return default_cat


def add_transaction_from_telegram(tx_type, amount, cat_name, description):
    """
    Helper function to create transaction record from Telegram inputs.
    """
    category = find_matching_category(cat_name, tx_type)
    today = timezone.now().date()

    if not description:
        description = f"Telegram {tx_type.lower()}"

    tx = Transaction.objects.create(
        transaction_type=tx_type,
        amount=Decimal(str(amount)),
        category=category,
        description=description.strip(),
        transaction_date=today,
        payment_method='CASH',
        notes='Added via Telegram Bot'
    )
    return tx


def parse_and_process_message(chat_id, text):
    """
    Main entry point for parsing commands and messages from Telegram.
    """
    if not is_chat_allowed(chat_id):
        return "⛔ Unauthorized user. Access denied."

    raw_text = text.strip()
    text_lower = raw_text.lower()

    # --- 1. COMMANDS ---
    if text_lower in ('/start', '/help'):
        return (
            "<b>👋 Welcome to Personal Finance Bot!</b>\n\n"
            "<b>Commands:</b>\n"
            "• /balance - Current financial balance\n"
            "• /today - Summary of today\n"
            "• /week - Weekly budget remaining\n"
            "• /month - Monthly budget remaining\n"
            "• /budget - All budget status\n"
            "• /summary - Financial breakdown\n"
            "• /recent - Last 5 transactions\n"
            "• /categories - List available categories\n\n"
            "<b>Quick Add Formats:</b>\n"
            "• <code>expense 250 food lunch</code>\n"
            "• <code>income 5000 salary</code>\n"
            "• <i>spent 200 on food</i>\n"
            "• <i>spent 100 taxi</i>\n"
            "• <i>received 5000 salary</i>"
        )

    if text_lower == '/balance':
        bal = get_current_balance()
        return (
            "<b>💰 Current Balance Status</b>\n\n"
            f"Total Income: {bal['formatted_income']}\n"
            f"Total Expenses: {bal['formatted_expenses']}\n"
            "───────────────\n"
            f"<b>Net Balance: {bal['formatted_balance']}</b>"
        )

    if text_lower == '/today':
        tod = get_today_summary()
        return (
            "<b>📅 Today's Financial Summary</b>\n\n"
            f"Income Today: {tod['formatted_income']}\n"
            f"Expense Today: {tod['formatted_expense']}\n"
            "───────────────\n"
            f"<b>Net Today: {tod['formatted_net']}</b>"
        )

    if text_lower == '/week':
        w = get_weekly_budget_status()
        if w['budget_amount'] == 0:
            return "⚠️ No weekly budget set. Set a budget in web settings."
        return (
            "<b>📊 Weekly Budget Status</b>\n\n"
            f"Weekly Budget: {w['formatted_budget']}\n"
            f"Spent: {w['formatted_spent']}\n"
            f"Remaining: {w['formatted_remaining']}\n\n"
            f"<b>{w['percentage_used']}% used</b> ({w['warning_msg']})"
        )

    if text_lower == '/month':
        m = get_monthly_budget_status()
        if m['budget_amount'] == 0:
            return "⚠️ No monthly budget set. Set a budget in web settings."
        return (
            "<b>📊 Monthly Budget Status</b>\n\n"
            f"Monthly Budget: {m['formatted_budget']}\n"
            f"Spent: {m['formatted_spent']}\n"
            f"Remaining: {m['formatted_remaining']}\n\n"
            f"<b>{m['percentage_used']}% used</b> ({m['warning_msg']})"
        )

    if text_lower == '/budget':
        w = get_weekly_budget_status()
        m = get_monthly_budget_status()
        return (
            "<b>🎯 Budget Overview</b>\n\n"
            f"<b>Weekly:</b> {w['formatted_spent']} / {w['formatted_budget']} ({w['percentage_used']}% used)\n"
            f"<i>{w['warning_msg']}</i>\n\n"
            f"<b>Monthly:</b> {m['formatted_spent']} / {m['formatted_budget']} ({m['percentage_used']}% used)\n"
            f"<i>{m['warning_msg']}</i>"
        )

    if text_lower == '/summary':
        bal = get_current_balance()
        tod = get_today_summary()
        w = get_weekly_budget_status()
        m = get_monthly_budget_status()
        return (
            "<b>📊 Financial Summary Report</b>\n\n"
            f"💰 <b>Balance:</b> {bal['formatted_balance']}\n"
            f"📅 <b>Today Net:</b> {tod['formatted_net']}\n"
            f"🗓️ <b>Weekly Spent:</b> {w['formatted_spent']} ({w['percentage_used']}% budget used)\n"
            f"📆 <b>Monthly Spent:</b> {m['formatted_spent']} ({m['percentage_used']}% budget used)"
        )

    if text_lower == '/recent':
        recent_txs = Transaction.objects.select_related('category').order_by('-transaction_date', '-created_at')[:5]
        if not recent_txs:
            return "No transactions recorded yet."
        lines = ["<b>📜 Recent 5 Transactions:</b>\n"]
        for tx in recent_txs:
            icon = tx.category.icon if tx.category else '📦'
            prefix = "+" if tx.transaction_type == 'INCOME' else "-"
            lines.append(
                f"{icon} <b>{tx.description or tx.category.name if tx.category else 'Tx'}</b>\n"
                f"   <code>{prefix} {format_currency(tx.amount)}</code> | {tx.transaction_date.strftime('%d %b')}"
            )
        return "\n".join(lines)

    if text_lower == '/categories':
        cats = Category.objects.filter(is_active=True)
        exp_cats = [f"{c.icon} {c.name}" for c in cats if c.category_type == 'EXPENSE']
        inc_cats = [f"{c.icon} {c.name}" for c in cats if c.category_type == 'INCOME']
        return (
            "<b>📁 Available Categories:</b>\n\n"
            "<b>Expenses:</b>\n" + ", ".join(exp_cats) + "\n\n"
            "<b>Income:</b>\n" + ", ".join(inc_cats)
        )

    # --- 2. NATURAL BALANCE & BUDGET QUESTIONS ---
    if any(q in text_lower for q in ['how much money do i have', 'what is my balance', 'current balance', 'balance']):
        bal = get_current_balance()
        return (
            "<b>💰 Balance Query</b>\n\n"
            f"Income: {bal['formatted_income']}\n"
            f"Expenses: {bal['formatted_expenses']}\n"
            "───────────────\n"
            f"<b>Current Balance: {bal['formatted_balance']}</b>"
        )

    if any(q in text_lower for q in ['how much can i spend this week', 'weekly budget', 'weekly remaining', 'left this week']):
        w = get_weekly_budget_status()
        return (
            "<b>📊 Weekly Budget Status</b>\n\n"
            f"Weekly Budget: {w['formatted_budget']}\n"
            f"Spent: {w['formatted_spent']}\n"
            f"Remaining: {w['formatted_remaining']}\n\n"
            f"<b>{w['percentage_used']}% used</b>"
        )

    if any(q in text_lower for q in ['how much is left this month', 'monthly budget', 'monthly remaining', 'left this month']):
        m = get_monthly_budget_status()
        return (
            "<b>📊 Monthly Budget Status</b>\n\n"
            f"Monthly Budget: {m['formatted_budget']}\n"
            f"Spent: {m['formatted_spent']}\n"
            f"Remaining: {m['formatted_remaining']}\n\n"
            f"<b>{m['percentage_used']}% used</b>"
        )

    # --- 3. STRUCTURED PARSER: `expense 250 food lunch` or `income 5000 salary` ---
    parts = raw_text.split()
    if len(parts) >= 2:
        first_word = parts[0].lower()
        if first_word in ('expense', 'income', 'exp', 'inc'):
            tx_type = 'INCOME' if first_word in ('income', 'inc') else 'EXPENSE'
            try:
                amount = Decimal(parts[1])
                cat_name = parts[2] if len(parts) > 2 else ''
                desc = " ".join(parts[3:]) if len(parts) > 3 else (cat_name or tx_type.title())

                tx = add_transaction_from_telegram(tx_type, amount, cat_name, desc)
                cat_display = tx.category.name if tx.category else 'Uncategorized'
                cat_icon = tx.category.icon if tx.category else '📦'

                return (
                    f"✅ <b>{tx.get_transaction_type_display()} Added Successfully!</b>\n\n"
                    f"<b>Amount:</b> {format_currency(tx.amount)}\n"
                    f"<b>Category:</b> {cat_icon} {cat_display}\n"
                    f"<b>Description:</b> {tx.description}\n"
                    f"<b>Date:</b> {tx.transaction_date.strftime('%d %b %Y')}"
                )
            except InvalidOperation:
                pass # Fall back to regex/natural parser

    # --- 4. NATURAL LANGUAGE EXPENSE/INCOME REGEX PATTERNS ---
    # Pattern: spent 200 on food / spent 100 taxi / paid 500 electricity
    spent_match = re.search(r'(?:spent|paid|bought|cost|expense)\s+(\d+(?:\.\d+)?)\s*(?:on|for)?\s*(.*)', text_lower)
    if spent_match:
        amount = Decimal(spent_match.group(1))
        remainder = spent_match.group(2).strip()
        cat_name = remainder.split()[0] if remainder else 'Personal'
        desc = remainder if remainder else 'Telegram Expense'
        tx = add_transaction_from_telegram('EXPENSE', amount, cat_name, desc)
        cat_display = tx.category.name if tx.category else 'Uncategorized'
        cat_icon = tx.category.icon if tx.category else '📦'
        return (
            f"✅ <b>Expense Added Successfully!</b>\n\n"
            f"<b>Amount:</b> {format_currency(tx.amount)}\n"
            f"<b>Category:</b> {cat_icon} {cat_display}\n"
            f"<b>Description:</b> {tx.description}\n"
            f"<b>Date:</b> {tx.transaction_date.strftime('%d %b %Y')}"
        )

    # Pattern: received 5000 salary / got 2000 freelance / income 5000
    income_match = re.search(r'(?:received|got|earned|income|salary)\s+(\d+(?:\.\d+)?)\s*(?:from|for)?\s*(.*)', text_lower)
    if income_match:
        amount = Decimal(income_match.group(1))
        remainder = income_match.group(2).strip()
        cat_name = remainder.split()[0] if remainder else 'Salary'
        desc = remainder if remainder else 'Telegram Income'
        tx = add_transaction_from_telegram('INCOME', amount, cat_name, desc)
        cat_display = tx.category.name if tx.category else 'Uncategorized'
        cat_icon = tx.category.icon if tx.category else '📦'
        return (
            f"✅ <b>Income Added Successfully!</b>\n\n"
            f"<b>Amount:</b> {format_currency(tx.amount)}\n"
            f"<b>Category:</b> {cat_icon} {cat_display}\n"
            f"<b>Description:</b> {tx.description}\n"
            f"<b>Date:</b> {tx.transaction_date.strftime('%d %b %Y')}"
        )

    # --- 5. FALLBACK RESPONSE ---
    return (
        "❓ I couldn't understand this transaction.\n\n"
        "<b>Try standard formats:</b>\n"
        "<code>expense 250 food lunch</code>\n"
        "or\n"
        "<code>income 5000 salary</code>\n\n"
        "<b>Or natural formats:</b>\n"
        "<i>spent 200 on food</i>\n"
        "<i>paid 500 electricity</i>\n"
        "<i>received 5000 salary</i>"
    )
