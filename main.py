# main.py
import os
import logging
from dotenv import load_dotenv
from adapters.telegram_adapter import TelegramBotAdapter

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    try:
        bot = TelegramBotAdapter(telegram_token)
        logger.info("Starting Redmine Telegram Bot...")
        # Blocking run
        bot.app.run_polling()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.exception(f"Bot failed to start: {e}")

if __name__ == "__main__":
    main()
