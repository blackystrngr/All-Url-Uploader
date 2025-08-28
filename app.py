from flask import Flask
import threading
import os
from bot import start_bot

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Telegram Bot is Running!"

@app.route("/health")
def health_check():
    return {"status": "healthy", "bot": "running"}

def run_bot():
    """Run the Telegram bot in a separate thread"""
    start_bot()

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
