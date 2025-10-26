import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from services.database_service import DatabaseService
from services.redmine_service import RedmineService

logger = logging.getLogger(__name__)


class IssueHandler:
    def __init__(self):
        self.db = DatabaseService()


    ASK_PROJECT, ASK_SUBJECT, ASK_DESCRIPTION, ASK_PRIORITY, ASK_TRACKER, CONFIRM_CREATE = range(6)

    # Helpers------------------------------------------------------
    async def _reply(self, update: Update, text: str, reply_markup=None, parse_mode="Markdown"):
        """Safe reply for callback_query or message."""
        if update.callback_query:
            return await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        elif update.message:
            return await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

    def _get_redmine_service(self, telegram_id: str) -> RedmineService:
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found. Please run /setup first.")
        return RedmineService(user["redmine_url"], user["api_key"])

    def _get_current_user_id(self, telegram_id: str) -> int:
        """Fetch the current user ID from Redmine to assign issues to self."""
        redmine = self._get_redmine_service(telegram_id)
        user_info = redmine.get_current_user()
        return user_info["user"]["id"]

    # Show My Issues----------------------------------------------------------------------
    async def show_my_issues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = str(update.effective_user.id)
        try:
            redmine = self._get_redmine_service(telegram_id)
            issues = redmine.get_issues(assigned_to_id="me", status_id="open", limit=10).get("issues", [])

            if not issues:
                await self._reply(update, "You have no open issues!")
                return

            for issue in issues:
                issue_id = issue.get("id")
                subject = issue.get("subject", "No subject")
                project_name = issue.get("project", {}).get("name", "Unknown Project")
                status_name = issue.get("status", {}).get("name", "Unknown Status")
                priority = issue.get("priority", {}).get("name", "N/A")

                message = (
                    f"**#{issue_id} - {subject}**\n"
                    f"Project: {project_name}\n"
                    f"Status: {status_name}\n"
                    f"Priority: {priority}\n\n"
                )
                buttons = [
                    [InlineKeyboardButton(f"Log Time to Issue#{issue_id}", callback_data=f"logtime_{issue_id}")]
                ]
                await self._reply(update, message, reply_markup=InlineKeyboardMarkup(buttons))

        except Exception as e:
            logger.exception("Error fetching issues: %s", e)
            await self._reply(update, "Failed to fetch issues. Please check your setup with /setup")

    # Create Issue Flow----------------------------------------------------------------------
    async def start_create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = str(update.effective_user.id)
        try:
            redmine = self._get_redmine_service(telegram_id)
            projects = redmine.get_projects().get("projects", [])
            if not projects:
                await self._reply(update, "No projects available for issue creation.")
                return ConversationHandler.END

            context.user_data["projects"] = {str(p["id"]): p["name"] for p in projects}

            buttons = [[InlineKeyboardButton(p["name"], callback_data=f"proj_{p['id']}")] for p in projects[:10]]
            await self._reply(update, "Select a project:", reply_markup=InlineKeyboardMarkup(buttons))
            return self.ASK_PROJECT

        except Exception as e:
            logger.exception("Error starting create issue flow: %s", e)
            await self._reply(update, "Failed to start issue creation. Please check your setup with /setup.")
            return ConversationHandler.END

    async def handle_project_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        project_id = query.data.replace("proj_", "")
        context.user_data["project_id"] = int(project_id)
        project_name = context.user_data["projects"].get(project_id, "Unknown Project")
        await query.message.reply_text(f"Selected project: *{project_name}*\n\nEnter issue subject:", parse_mode="Markdown")
        return self.ASK_SUBJECT

    async def handle_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["subject"] = update.message.text.strip()
        await update.message.reply_text("Enter a short description for the issue:")
        return self.ASK_DESCRIPTION

    async def handle_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["description"] = update.message.text.strip()

        buttons = [
            [
                InlineKeyboardButton("Low", callback_data="priority_1"),
                InlineKeyboardButton("Normal", callback_data="priority_2"),
                InlineKeyboardButton("High", callback_data="priority_3"),
                InlineKeyboardButton("Urgent", callback_data="priority_4"),
            ]
        ]
        await update.message.reply_text("Select priority:", reply_markup=InlineKeyboardMarkup(buttons))
        return self.ASK_PRIORITY

    async def handle_priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data["priority_id"] = int(query.data.replace("priority_", ""))

        telegram_id = str(update.effective_user.id)
        redmine = self._get_redmine_service(telegram_id)
        trackers = redmine.get_trackers().get("trackers", [])

        context.user_data["trackers"] = {str(t["id"]): t["name"] for t in trackers}
        buttons = [[InlineKeyboardButton(t["name"], callback_data=f"tracker_{t['id']}")] for t in trackers[:10]]

        await query.message.reply_text("Select tracker:", reply_markup=InlineKeyboardMarkup(buttons))
        return self.ASK_TRACKER

    async def handle_tracker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        tracker_id = int(query.data.replace("tracker_", ""))
        context.user_data["tracker_id"] = tracker_id
        await query.message.reply_text(
            f"Tracker selected: {context.user_data['trackers'][str(tracker_id)]}\n\n"
            f"Confirm creation of issue:\n"
            f"Project: {context.user_data['projects'][str(context.user_data['project_id'])]}\n"
            f"Subject: {context.user_data['subject']}\n"
            f"Description: {context.user_data['description']}\n"
            f"Priority ID: {context.user_data['priority_id']}\n"
        )

        buttons = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_create"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_create"),
            ]
        ]
        await query.message.reply_text("Ready to create issue?", reply_markup=InlineKeyboardMarkup(buttons))
        return self.CONFIRM_CREATE

    async def confirm_create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_create":
            await query.message.reply_text("Issue creation cancelled. Go to /menu")
            return ConversationHandler.END

        telegram_id = str(update.effective_user.id)
        try:
            redmine = self._get_redmine_service(telegram_id)
            current_user_id = self._get_current_user_id(telegram_id)

            issue_data = {
                "project_id": context.user_data["project_id"],
                "subject": context.user_data["subject"],
                "description": context.user_data["description"],
                "priority_id": context.user_data["priority_id"],
                "tracker_id": context.user_data["tracker_id"],
                "assigned_to_id": current_user_id, 
            }

            await query.message.reply_text("⏳ Creating issue in Redmine...")
            result = redmine.create_issue(issue_data)
            issue_id = result.get("issue", {}).get("id")

            if issue_id:
                await query.message.reply_text(f"Issue created successfully! (ID: #{issue_id}). Go to /menu")
            else:
                await query.message.reply_text("Error: Issue created but no ID returned. Go to /menu")

        except Exception as e:
            logger.exception("Error creating issue: %s", e)
            await query.message.reply_text("Failed to create issue. Please try again. Go to /menu")

        return ConversationHandler.END
