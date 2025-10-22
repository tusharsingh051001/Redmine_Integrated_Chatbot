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
        return RedmineService(user["redmine_url"], user["api_key"])

    async def show_my_issues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show issues as an inline keyboard with one button per-issue.
        Callback data will be: logtime_<issue_id>
        """
        user = update.effective_user
        telegram_id = str(user.id)
        logger.debug("show_my_issues called for telegram_id=%s", telegram_id)

        try:
            redmine = self._get_redmine_service(telegram_id)
            result = redmine.get_issues(assigned_to_id="me", status_id="open", limit=10)
            issues = result.get("issues", [])

            if not issues:
                logger.debug("No issues found for user %s", telegram_id)
                msg = "You have no open issues!"
                if update.callback_query:
                    await update.callback_query.message.reply_text(msg)
                else:
                    await update.message.reply_text(msg)
                return

            # Build message and keyboard
            buttons = []
            message = f"**Your Open Issues (showing {len(issues)})**\n\n"
            for issue in issues:
                issue_id = issue.get("id")
                subject = issue.get("subject", "No subject")
                project_name = issue.get("project", {}).get("name", "Unknown Project")
                status_name = issue.get("status", {}).get("name", "Unknown Status")
                priority = issue.get("priority", {}).get("name", "N/A")

                issue_text = f"#{issue_id} - {subject}"
                message = (
                    f"**{issue_text}**\n"
                    f"Project: {project_name}\n"
                    f"Status: {status_name}\n"
                    f"Priority: {priority}\n\n"
                )

                # Inline button to log time to this specific issue
                buttons = [[InlineKeyboardButton(f"Log Time to Issue#{issue_id}", callback_data=f"logtime_{issue_id}")]]  # ✅ Notice double brackets

                reply_markup = InlineKeyboardMarkup(buttons)

                # Send message with inline buttons
                if update.callback_query:
                    logger.debug("Replying to callback_query with issues list for %s", telegram_id)
                    await update.callback_query.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    logger.debug("Replying to message with issues list for %s", telegram_id)
                    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)


        except Exception as e:
            logger.exception("Error fetching issues for user %s: %s", telegram_id, e)
            error_msg = "Failed to fetch issues. Please check your setup with /setup"
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg)
            else:
                await update.message.reply_text(error_msg)

    async def start_create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug("start_create_issue called (stub).")
        await update.callback_query.message.reply_text(
            "🚧 **Create Issue feature coming soon!**\n\n"
            "For now, please create issues directly in Redmine.\n"
            "Use /menu to return to the main menu."
        )
