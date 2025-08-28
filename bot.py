import os
import logging
from pyrogram.raw.all import layer
from pyrogram import Client, idle, __version__

from config import Config

# ... (keep your existing logging setup)

def start_bot():
    """Start the Telegram bot"""
    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)

    if not Config.BOT_TOKEN:
        logger.error("Please set BOT_TOKEN in config.py or as env var")
        return

    if not Config.API_ID:
        logger.error("Please set API_ID in config.py or as env var")
        return

    if not Config.API_HASH:
        logger.error("Please set API_HASH in config.py or as env var")
        return

    bot = Client(
        "All-Url-Uploader",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        workers=50,
        plugins=dict(root="plugins"),
    )

    bot.start()
    logger.info("Bot has started.")
    logger.info("**Bot Started**\n\n**Pyrogram Version:** %s \n**Layer:** %s", __version__, layer)
    logger.info("Developed by github.com/kalanakt Sponsored by www.netronk.com")
    idle()
    bot.stop()
    logger.info("Bot Stopped ;)")

if __name__ == "__main__":
    start_bot()
