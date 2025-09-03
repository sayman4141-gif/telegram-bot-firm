#!/usr/bin/env python3
"""
Telegram Bot with Google Gemini AI Integration
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)
    
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    exit(1)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Telegram Bot is running!')
    
    def log_message(self, format, *args):
        pass  # تجاهل HTTP logs

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health server running on port {port}")
    server.serve_forever()

class TelegramBot:
    def __init__(self):
        """Initialize the bot with Gemini AI model"""
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Bot initialized with Gemini AI")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🤖 Hello! I'm your AI assistant powered by The Firm Team.\n\n"
            "I can help you with:\n"
            "• Answering questions\n"
            "• Creative writing\n"
            "• Problem solving\n"
            "• General conversation\n\n"
            "Just send me any message and I'll respond using AI!"
        )
        await update.message.reply_text(welcome_message)
        logger.info(f"Started conversation with user {update.effective_user.first_name}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🆘 **How to use this bot:**\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            "Simply send me any text message and I'll respond using AI!\n\n"
            "Examples:\n"
            "• Ask me questions: 'What is quantum physics?'\n"
            "• Creative tasks: 'Write a short story about space'\n"
            "• Problem solving: 'Help me debug this code'\n"
            "• General chat: 'How are you today?'"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages using Gemini AI"""
        user_message = update.message.text
        user_name = update.effective_user.first_name
        
        logger.info(f"Received message from {user_name}: {user_message[:50]}...")
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Generate response using Gemini AI
            response = self.model.generate_content(user_message)
            ai_response = response.text
            
            # Send response back to user
            await update.message.reply_text(ai_response)
            logger.info(f"Sent AI response to {user_name}")
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            error_message = (
                "🚫 Sorry, I encountered an error while processing your message. "
                "Please try again in a moment."
            )
            await update.message.reply_text(error_message)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function to run the bot"""
    logger.info("Starting Telegram Bot with Gemini AI...")
    
    # Start health server in background thread
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Create bot instance
    bot = TelegramBot()
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", bot.start_command))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_error_handler(bot.error_handler)
    
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
