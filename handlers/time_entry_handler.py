import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.database_service import DatabaseService
from services.redmine_service import RedmineService
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class TimeEntryHandler:

    GETTING_WORK, CONFIRMING = range(2)

    def __init__(self):
        self.db = DatabaseService()
        self.gemini = GeminiService()

    def _get_redmine_service(self, telegram_id: str) -> RedmineService:
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found. Run /setup first.")
        return RedmineService(user['redmine_url'], user['api_key'])

    async def start_log_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['in_conversation'] = True

        msg_obj = update.callback_query.message if update.callback_query else update.message
        message = """
⏱️ **Log Time Entries**

Please describe your work. Include:
- What you worked on
- How long you spent
- When (if not today)
- Issue IDs (mandatory)

**Example:**
"Today I worked on bug fixes for 3 hours and code review for 1.5 hours for issue #1234 and #5678."

Type your work log below:
"""
        await msg_obj.reply_text(message, parse_mode="Markdown")
        return self.GETTING_WORK

    async def process_work_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)
        work_text = update.message.text
        msg_obj = update.message

        await msg_obj.reply_text("🔄 Processing your work log with AI... Please wait.")

        try:
            redmine = self._get_redmine_service(telegram_id)
            user_data = self.db.get_user_by_telegram_id(telegram_id)
            activities_result = await redmine.get_time_entry_activities()
            activities = activities_result.get('time_entry_activities', [])

            if not activities:
                await msg_obj.reply_text("❌ No time entry activities found in Redmine.")
                context.user_data['in_conversation'] = False
                return ConversationHandler.END

            parsed_entries = self.gemini.parse_time_entries(work_text, activities)
            activity_map = {a['name'].lower(): a['id'] for a in activities}

            for entry in parsed_entries:
                activity_name = entry['activity'].lower()
                matched_id = None
                for act_name, act_id in activity_map.items():
                    if activity_name in act_name or act_name in activity_name:
                        matched_id = act_id
                        break
                if not matched_id:
                    matched_id = activities[0]['id']
                entry['activity_id'] = matched_id
                entry['activity_name'] = next((a['name'] for a in activities if a['id'] == matched_id), 'Unknown')

            context.user_data['parsed_entries'] = parsed_entries
            context.user_data['project_id'] = user_data.get('default_project_id')

            summary = "**Work Summary:**\n\n"
            total_hours = 0
            for i, entry in enumerate(parsed_entries, 1):
                summary += f"{i}. **{entry['date']}** - {entry['hours']}h\n" \
                           f"   Activity: {entry['activity_name']}\n" \
                           f"   Description: {entry['comments']}\n" \
                           f"   Issue ID: {entry['issue_id']}\n\n"
                total_hours += entry['hours']
            summary += f"**Total: {total_hours} hours**\n\nIs this correct?"

            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm & Log", callback_data="confirm_log"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_log")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await msg_obj.reply_text(summary, parse_mode="Markdown", reply_markup=reply_markup)
            return self.CONFIRMING

        except Exception as e:
            logger.error(f"Error processing work log: {e}")
            await msg_obj.reply_text(f"Could not parse work log: {e}\nPlease try again.")
            context.user_data['in_conversation'] = False
            return ConversationHandler.END


    async def confirm_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        msg_obj = query.message if query else update.message

        if query:
            await query.answer()

        if query and query.data == "cancel_log":
            await msg_obj.reply_text("Time logging cancelled. Use /logtime to try again. Go back to /menu.")
            context.user_data['in_conversation'] = False
            return ConversationHandler.END

        user = update.effective_user
        telegram_id = str(user.id)
        parsed_entries = context.user_data.get("parsed_entries", [])
        project_id = context.user_data.get("project_id")

        if not project_id:
            await msg_obj.reply_text("No default project set. Please run /setup first.")
            context.user_data['in_conversation'] = False
            return ConversationHandler.END

        redmine = self._get_redmine_service(telegram_id)
        await msg_obj.reply_text("⏳ Submitting time entries to Redmine...")

        success_count = 0
        errors = []

        for entry in parsed_entries:
            try:
                data = {
                    "project_id": project_id,
                    "spent_on": entry["date"],
                    "hours": entry["hours"],
                    "activity_id": entry["activity_id"],
                    "comments": entry["comments"],
                    "issue_id": entry.get("issue_id")
                }
                await redmine.create_time_entry(data)
                success_count += 1
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    error_msg = f"Issue {entry.get('issue_id')} might be closed or invalid."
                    logger.warning(f"422 Error for time entry {entry}: {e.response.text}")
                else:
                    error_msg = f"{e.response.status_code} Error: {e.response.text}"
                errors.append(f"{entry['date']}: {error_msg}")
            except Exception as e:
                logger.error(f"Failed to log time entry: {e}")
                errors.append(f"{entry['date']}: {e}")

        msg_text = ""
        if success_count >= 1:
            msg_text = f"✅ **Logged {success_count} time entries successfully!**\n\n"
        if errors:
            msg_text += "⚠️ **Some entries failed:**\n" + "\n".join(f"- {e}" for e in errors[:5])
        msg_text += "\nUse /menu to continue."

        await msg_obj.reply_text(msg_text, parse_mode="Markdown")

        context.user_data.clear()
        return ConversationHandler.END
