from flask import Flask, request
import threading
import os
import asyncio
import logging
import signal
import sys
from pyrogram import Client
from config import Config

app = Flask(__name__)

# Global bot instance
bot_instance = None
bot_running = False
stop_event = threading.Event()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.route("/", methods=['GET', 'HEAD', 'POST'])
def hello_world():
    """Handle all HTTP methods for health checks"""
    return f"Telegram Bot is Running! Status: {'Active' if bot_running else 'Starting...'}"

@app.route("/health", methods=['GET', 'HEAD', 'POST'])
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "bot_running": bot_running}

@app.route("/webhook", methods=['POST'])
def webhook():
    """Webhook endpoint for future use"""
    return {"status": "webhook_received"}

async def start_bot():
    """Start the bot asynchronously"""
    global bot_instance, bot_running
    
    try:
        # Initialize bot
        if not os.path.isdir(Config.DOWNLOAD_LOCATION):
            os.makedirs(Config.DOWNLOAD_LOCATION)

        bot_instance = Client(
            "All-Url-Uploader",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=50,
            plugins=dict(root="plugins"),
        )
        
        logger.info("Starting Telegram bot...")
        
        # Start bot
        await bot_instance.start()
        bot_running = True
        logger.info("Bot started successfully!")
        
        # Keep the bot running until stop_event is set
        while not stop_event.is_set():
            await asyncio.sleep(1)
        
        logger.info("Stopping bot...")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        bot_running = False
    finally:
        if bot_instance:
            try:
                await bot_instance.stop()
                logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
            bot_running = False

def run_bot_sync():
    """Run the bot synchronously in a separate thread"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(start_bot())
        
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")
        global bot_running
        bot_running = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    stop_event.set()
    sys.exit(0)

# Validate required environment variables
def validate_config():
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        return False
    if not Config.API_ID:
        logger.error("API_ID is not set!")
        return False
    if not Config.API_HASH:
        logger.error("API_HASH is not set!")
        return False
    return True

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Validate configuration
    if not validate_config():
        exit(1)
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    import time
    time.sleep(5)
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
