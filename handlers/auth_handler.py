import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services.database_service import DatabaseService
from services.redmine_service import RedmineService

logger = logging.getLogger(__name__)

class AuthHandler:
    
    EMPLOYEE_ID, REDMINE_URL, API_KEY, PROJECT_ID = range(4)
    
    def __init__(self):
        self.db = DatabaseService()
    
    async def start_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)
        
        existing_user = self.db.get_user_by_telegram_id(telegram_id)
        
        if existing_user:
            await update.message.reply_text(
                f"⚠️ You already have an account set up!\n\n"
                f"Employee ID: {existing_user['employee_id']}\n"
                f"Redmine URL: {existing_user['redmine_url']}\n\n"
                f"To update your settings, continue with the setup."
            )
        
        await update.message.reply_text(
            "**Terms and Conditions**\n\n"
            "By setting up your Redmine account, you allow me to help you manage your tasks and log time directly from Telegram.\n\n"
            "You agree to provide accurate information and it being stored for use by the bot.\n\n"
            "You agree to not misuse the chatbot in any way.\n\n",
            parse_mode='Markdown'
        )
        await update.message.reply_text(
            "🔧 **Setup Wizard**\n\n"
            "Let's configure your Redmine account.\n\n"
            "Step 1/4: Please enter your **Employee ID**:",
            parse_mode='Markdown'
        )
        
        return self.EMPLOYEE_ID
    
    async def get_employee_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        employee_id = update.message.text.strip()
        context.user_data['employee_id'] = employee_id
        
        await update.message.reply_text(
            f"Employee ID: {employee_id}\n\n"
            f"Step 2/4: Please enter your **Redmine URL**\n",
            parse_mode='Markdown'
        )
        
        return self.REDMINE_URL
    
    async def get_redmine_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        redmine_url = update.message.text.strip().rstrip('/')
        
        if not redmine_url.startswith('http'):
            await update.message.reply_text(
                "Invalid URL. Please enter a valid URL starting with http://"
            )
            return self.REDMINE_URL
        
        context.user_data['redmine_url'] = redmine_url
        
        await update.message.reply_text(
            f"Redmine URL: {redmine_url}\n\n"
            f"Step 3/4: Please enter your **Redmine API Key**\n"
            f"You can find it under API Key in your Redmine account settings.",
            parse_mode='Markdown'
        )
        
        return self.API_KEY
    
    async def get_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        api_key = update.message.text.strip()
        redmine_url = context.user_data['redmine_url']
        
        try:
            redmine = RedmineService(redmine_url, api_key)
            user_data = redmine.get_current_user()
            
            context.user_data['api_key'] = api_key
            context.user_data['redmine_user'] = user_data.get('user', {})
            
            await update.message.reply_text(
                f"API Key validated!\n"
                f"Redmine User: {user_data['user']['login']}\n\n"
                f"Step 4/4: Enter your **default Project ID** (optional, but recommended)\n"
                f"You can skip this by typing 'skip'",
                parse_mode='Markdown'
            )
            
            return self.PROJECT_ID
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            await update.message.reply_text(
                "Invalid API key or unable to connect to Redmine.\n"
                "Please check and try again:"
            )
            return self.API_KEY
    
    async def get_project_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        project_id = update.message.text.strip()
        
        if project_id.lower() == 'skip':
            project_id = None
        else:
            context.user_data['project_id'] = project_id
        
        user = update.effective_user
        telegram_id = str(user.id)
        name = user.full_name
        
        try:
            self.db.create_user(
                telegram_id=telegram_id,
                employee_id=context.user_data['employee_id'],
                name=name,
                redmine_url=context.user_data['redmine_url'],
                api_key=context.user_data['api_key'],
                project_id=project_id
            )
            
            await update.message.reply_text(
                "**Setup Complete!**\n\n"
                "Your account has been configured successfully.\n\n"
                "Use /menu to start using the bot!",
                parse_mode='Markdown'
            )
            
            context.user_data.clear()
            
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            await update.message.reply_text(
                "Failed to save your settings. Please try again with /setup"
            )
        
        return ConversationHandler.END
    
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = update.effective_user
        telegram_id = str(user.id)
        
        user_data = self.db.get_user_by_telegram_id(telegram_id)
        
        if not user_data:
            await query.message.reply_text(
                "No account found. Use /setup to configure your account."
            )
            return
        
        settings_msg = f"""
            **Your Settings**

            **Employee ID:** {user_data['employee_id']}
            **Name:** {user_data['name']}
            **Redmine URL:** {user_data['redmine_url']}
            **API Key:** {user_data['api_key'][:10]}...
            **Default Project:** {user_data.get('default_project_id', 'Not set')}

            To update settings, use /setup again.
            """
        await query.message.reply_text(settings_msg, parse_mode='Markdown')