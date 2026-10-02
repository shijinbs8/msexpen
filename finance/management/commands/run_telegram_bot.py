import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from finance.models import AppSetting
from finance.telegram_bot import parse_and_process_message, send_telegram_message

class Command(BaseCommand):
    help = 'Runs Telegram Bot daemon long-polling process for personal expense tracking.'

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or AppSetting.get_setting('TELEGRAM_BOT_TOKEN', '')

        if not token:
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_TOKEN environment variable or AppSetting is missing!"))
            self.stdout.write("Please configure TELEGRAM_BOT_TOKEN in .env or settings page.")
            return

        self.stdout.write(self.style.SUCCESS(f"Starting Telegram Bot long polling daemon..."))
        offset = 0

        while True:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {'offset': offset, 'timeout': 20}
                res = requests.get(url, params=params, timeout=25)

                if res.status_code == 200:
                    data = res.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        for update in updates:
                            update_id = update['update_id']
                            offset = update_id + 1

                            message = update.get('message', {})
                            text = message.get('text', '')
                            chat = message.get('chat', {})
                            chat_id = chat.get('id')

                            if chat_id and text:
                                self.stdout.write(f"Received message from chat_id {chat_id}: {text}")
                                reply_text = parse_and_process_message(chat_id, text)
                                send_telegram_message(chat_id, reply_text)

                time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("Telegram Bot daemon stopped by user."))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in polling loop: {e}"))
                time.sleep(5)
