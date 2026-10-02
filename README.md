# 💎 Mobile-First Income & Expense Manager

A complete, mobile-first personal finance application built with **Django**, **SQLite**, **Bootstrap 5**, **Chart.js**, and **Telegram Bot Integration**.

Designed to be used primarily from smartphones with a sleek glassmorphic UI, mobile bottom navigation, instant quick-add entry, dynamic budget warnings, downloadable financial reports (CSV & PDF), and full Telegram bot command/natural syntax support.

---

## 🚀 Features

- **Mobile-First Responsive Dashboard**:
  - Current Balance Hero Card (`Total Income - Total Expenses`)
  - Today's Summary (Income, Expenses, Net)
  - Interactive Weekly & Monthly Budget status cards with dynamic progress bars (Emerald <60%, Amber 60-80%, Orange 80-100%, Rose >100%) and automatic warning badges.
  - Category Doughnut Chart with interactive period toggle (Today, Week, Month).
  - Income vs Expense Timeline Bar Chart & Spending Trend Line Chart.
- **Transactions Management**:
  - Add/Edit/Delete transactions with custom dates, payment methods (Cash, Card, Bank, UPI, Other), and categories.
  - Numeric keyboard auto-trigger (`inputmode="decimal"`) for high-speed mobile logging.
  - Floating Quick Add button accessible from any page.
  - Search & filter by keyword, category, date range, or transaction type.
- **Financial Reports & Exports**:
  - Filterable statement dashboard (Today, Week, Month, Last Month, Custom Range).
  - Key Financial Metrics (Net Balance, Avg Daily Expense, Largest Expense, Top Category).
  - One-click **CSV Statement Export**.
  - Styled **PDF Statement Export** using ReportLab.
- **Telegram Bot Integration**:
  - Add expense: `expense 250 food lunch`
  - Add income: `income 5000 salary`
  - Natural text: `spent 200 on food`, `spent 100 taxi`, `paid 500 electricity`, `received 5000 salary`
  - Financial Commands: `/balance`, `/today`, `/week`, `/month`, `/budget`, `/summary`, `/recent`, `/categories`
  - Natural balance questions: `"what is my balance?"`, `"how much can I spend this week?"`, `"how much is left this month?"`
  - Strict security validation using `TELEGRAM_ALLOWED_CHAT_ID`.
- **Easy PythonAnywhere Deployment**:
  - Lightweight stack without Redis, Celery, React, or Docker.

---

## 📁 Project Structure

```text
expense_tracker/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── finance/
│   ├── models.py          # Category, Transaction, Budget, AppSetting
│   ├── views.py           # Dashboard, Transactions, Reports, Settings, Webhook
│   ├── services.py        # Reusable budget calculations & metrics logic
│   ├── telegram_bot.py    # Telegram Bot parser, security & commands router
│   ├── reports.py         # CSV & ReportLab PDF generator
│   ├── forms.py           # Django forms & validation
│   ├── urls.py
│   ├── admin.py
│   ├── management/
│   │   └── commands/
│   │       ├── seed_categories.py
│   │       └── run_telegram_bot.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── dashboard.js
│   │       └── transactions.js
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── transactions/
│       ├── reports/
│       ├── budgets/
│       └── settings/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Local Development Setup

### 1. Initialize Virtual Environment & Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file in the root folder:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DEFAULT_CURRENCY=AED
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_CHAT_ID=your_telegram_chat_id_here
```

### 3. Run Migrations & Seed Default Categories

```bash
python manage.py makemigrations finance
python manage.py migrate
python manage.py seed_categories
```

### 4. Create Superuser (For Django Admin access)

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your mobile browser or emulator!

---

## 🤖 Running Telegram Bot

To start the Telegram daemon in long-polling mode:

```bash
python manage.py run_telegram_bot
```

*Note: Make sure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_CHAT_ID` are configured in `.env` or in Web Settings.*

---

## 🌐 PythonAnywhere Deployment Guide

Deploying this app on **PythonAnywhere** takes only a few minutes.

### Step 1: Upload Code to PythonAnywhere

Log in to [PythonAnywhere](https://www.pythonanywhere.com/) and open a **Bash Console**.

Clone or upload your project directory to PythonAnywhere:

```bash
cd ~
git clone https://github.com/your-username/expense_tracker.git
cd expense_tracker
```

### Step 2: Create Virtual Environment & Install Requirements

In the PythonAnywhere Bash Console:

```bash
mkvirtualenv --python=/usr/bin/python3.10 finance-venv
pip install -r requirements.txt
```

### Step 3: Run Migrations & Seed Initial Categories

```bash
python manage.py makemigrations finance
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
```

### Step 4: Configure Web App in PythonAnywhere Web Tab

1. Go to the **Web** tab on PythonAnywhere dashboard.
2. Click **"Add a new web app"**.
3. Choose **Manual configuration** and select **Python 3.10**.
4. In the **Virtualenv** section, set the path:
   `/home/yourusername/.virtualenvs/finance-venv`
5. In the **Code** section, set:
   - **Source code**: `/home/yourusername/expense_tracker`
   - **Working directory**: `/home/yourusername/expense_tracker`

### Step 5: Configure WSGI Configuration File

Click on the **WSGI configuration file** link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`) and update its content to:

```python
import os
import sys

# Path to your project directory
path = '/home/yourusername/expense_tracker'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 6: Configure Static Files

Under the **Static files** section in the **Web** tab, add:
- **URL**: `/static/`
- **Directory**: `/home/yourusername/expense_tracker/staticfiles`

Then run collectstatic in Bash console:

```bash
python manage.py collectstatic --noinput
```

### Step 7: Environment Variables Setup

Create `.env` file in `/home/yourusername/expense_tracker/.env`:

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DEFAULT_CURRENCY=AED
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_CHAT_ID=your_chat_id_here
```

### Step 8: Reload Web App

Click the green **"Reload yourusername.pythonanywhere.com"** button at the top of the Web tab.

### Step 9: Run Telegram Bot on PythonAnywhere

On PythonAnywhere, you can run the Telegram Bot via **Always-On Tasks** (for Paid accounts) or **Scheduled Tasks** (for Free accounts running polling/webhook):

1. **Option A (Webhook mode)**: Set your Telegram webhook to point to:
   `https://yourusername.pythonanywhere.com/telegram/webhook/`
2. **Option B (Always-On task)**: Command:
   `/home/yourusername/.virtualenvs/finance-venv/bin/python /home/yourusername/expense_tracker/manage.py run_telegram_bot`

---

## 🔑 License
MIT License. Built for personal income & expense management.
