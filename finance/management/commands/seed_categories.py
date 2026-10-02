from django.core.management.base import BaseCommand
from finance.models import Category

class Command(BaseCommand):
    help = 'Seeds initial expense and income categories with icons and colors.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")

        expense_categories = [
            {'name': 'Food', 'icon': '🍔', 'color': '#EF4444'},
            {'name': 'Groceries', 'icon': '🛒', 'color': '#F59E0B'},
            {'name': 'Transport', 'icon': '🚌', 'color': '#3B82F6'},
            {'name': 'Fuel', 'icon': '⛽', 'color': '#6366F1'},
            {'name': 'Shopping', 'icon': '🛍️', 'color': '#EC4899'},
            {'name': 'Bills', 'icon': '🧾', 'color': '#8B5CF6'},
            {'name': 'Electricity', 'icon': '⚡', 'color': '#EAB308'},
            {'name': 'Internet', 'icon': '🌐', 'color': '#06B6D4'},
            {'name': 'Phone', 'icon': '📱', 'color': '#10B981'},
            {'name': 'Rent', 'icon': '🏠', 'color': '#64748B'},
            {'name': 'Medical', 'icon': '🏥', 'color': '#14B8A6'},
            {'name': 'Entertainment', 'icon': '🎬', 'color': '#D946EF'},
            {'name': 'Education', 'icon': '🎓', 'color': '#3949AB'},
            {'name': 'Travel', 'icon': '✈️', 'color': '#0284C7'},
            {'name': 'Family', 'icon': '👨‍👩‍👧', 'color': '#F43F5E'},
            {'name': 'Personal', 'icon': '👤', 'color': '#84CC16'},
            {'name': 'Other', 'icon': '📦', 'color': '#94A3B8'},
        ]

        income_categories = [
            {'name': 'Salary', 'icon': '💼', 'color': '#10B981'},
            {'name': 'Freelance', 'icon': '💻', 'color': '#3B82F6'},
            {'name': 'Business', 'icon': '🏢', 'color': '#8B5CF6'},
            {'name': 'Bonus', 'icon': '🎁', 'color': '#F59E0B'},
            {'name': 'Investment', 'icon': '📈', 'color': '#06B6D4'},
            {'name': 'Other', 'icon': '💵', 'color': '#64748B'},
        ]

        created_count = 0
        for item in expense_categories:
            obj, created = Category.objects.get_or_create(
                name=item['name'],
                category_type='EXPENSE',
                defaults={'icon': item['icon'], 'color': item['color']}
            )
            if created:
                created_count += 1

        for item in income_categories:
            obj, created = Category.objects.get_or_create(
                name=item['name'],
                category_type='INCOME',
                defaults={'icon': item['icon'], 'color': item['color']}
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded categories. Created {created_count} new categories."))
