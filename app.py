from flask import Flask
import threading
import os
import asyncio
import logging
from pyrogram import Client
from config import Config

app = Flask(__name__)

# Global bot instance
bot_instance = None
bot_running = False

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.route("/")
def hello_world():
    return f"Telegram Bot is Running! Status: {'Active' if bot_running else 'Starting...'}"

@app.route("/health")
def health_check():
    return {"status": "healthy", "bot_running": bot_running}

@app.route("/restart")
def restart_bot():
    """Emergency restart endpoint"""
    global bot_running
    if bot_instance:
        try:
            asyncio.create_task(restart_bot_async())
            return {"status": "restarting"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "no_bot_instance"}

async def restart_bot_async():
    global bot_instance, bot_running
    if bot_instance:
        await bot_instance.stop()
        bot_running = False
        await asyncio.sleep(2)
        await bot_instance.start()
        bot_running = True

def run_bot_sync():
    """Run the bot synchronously in a separate thread"""
    global bot_instance, bot_running
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
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
        loop.run_until_complete(bot_instance.start())
        bot_running = True
        logger.info("Bot started successfully!")
        
        # Keep the bot running
        loop.run_forever()
        
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")
        bot_running = False

if __name__ == "__main__":
    # Validate required environment variables
    if not all([Config.BOT_TOKEN, Config.API_ID, Config.API_HASH]):
        logger.error("Missing required environment variables!")
        exit(1)
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    import time
    time.sleep(3)
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
