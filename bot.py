import os
import logging
from pyrogram.raw.all import layer
from pyrogram import Client, __version__
from flask import Flask
import threading

from config import Config

# Flask app
app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

@app.route("/")
def hello_world():
    return "Bot is running!"

@app.route("/health")
def health():
    return {"status": "ok"}

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    if not os.path.isdir(Config.DOWNLOAD_LOCATION):
        os.makedirs(Config.DOWNLOAD_LOCATION)

    if not Config.BOT_TOKEN:
        logger.error("Please set BOT_TOKEN in config.py or as env var")
        quit(1)

    if not Config.API_ID:
        logger.error("Please set API_ID in config.py or as env var")
        quit(1)

    if not Config.API_HASH:
        logger.error("Please set API_HASH in config.py or as env var")
        quit(1)

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

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
    
    # Keep the bot running
    bot.run()

if __name__ == "__main__":
    main()
