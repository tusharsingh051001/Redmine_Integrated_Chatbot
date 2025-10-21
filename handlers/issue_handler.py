import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.database_service import DatabaseService
from services.redmine_service import RedmineService

logger = logging.getLogger(__name__)

class IssueHandler:
    
    def __init__(self):
        self.db = DatabaseService()
    
    def _get_redmine_service(self, telegram_id: str) -> RedmineService:
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found. Please run /setup first.")
        
        return RedmineService(user['redmine_url'], user['api_key'])
    
    async def show_my_issues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)
        
        try:
            redmine = self._get_redmine_service(telegram_id)
            result = redmine.get_issues(assigned_to_id='me', status_id='open', limit=10)
            
            issues = result.get('issues', [])
            
            if not issues:
                message = "You have no open issues!"
            else:
                message = f"**Your Open Issues** (showing {len(issues)}):\n\n"
                for issue in issues:
                    message += (
                        f"**#{issue['id']}** - {issue['subject']}\n"
                        f"Project: {issue['project']['name']}\n"
                        f"Status: {issue['status']['name']}\n"
                        f"Priority: {issue.get('priority', {}).get('name', 'N/A')}\n\n"
                    )
            
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    message, parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            error_msg = "Failed to fetch issues. Please check your setup with /setup"
            
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
    
    async def start_create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.message.reply_text(
            "🚧 **Create Issue feature coming soon!**\n\n"
            "For now, please create issues directly in Redmine.\n"
            "Use /menu to return to the main menu."
        )