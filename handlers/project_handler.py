import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import DatabaseService
from services.redmine_service import RedmineService

logger = logging.getLogger(__name__)

class ProjectHandler:
    
    def __init__(self):
        self.db = DatabaseService()
    
    def _get_redmine_service(self, telegram_id: str) -> RedmineService:
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found. Please run /setup first.")
        
        return RedmineService(user['redmine_url'], user['api_key'])
    
    async def show_projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)
        
        try:
            redmine = self._get_redmine_service(telegram_id)
            result = redmine.get_projects(limit=20)
            
            projects = result.get('projects', [])
            
            if not projects:
                message = "No projects found."
            else:
                message = f"📁 **Your Projects** (showing {len(projects)}):\n\n"
                for project in projects:
                    message += (
                        f"**{project['name']}**\n"
                        f"ID: {project['id']} | Identifier: {project['identifier']}\n"
                        f"{project.get('description', 'No description')[:100]}\n\n"
                    )
            
            await update.callback_query.message.reply_text(
                message, parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            await update.callback_query.message.reply_text(
                "Failed to fetch projects. Please check your setup with /setup"
            )