import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from adapters.base_adapter import BaseChatAdapter
from handlers.auth_handler import AuthHandler
from handlers.issue_handler import IssueHandler
from handlers.project_handler import ProjectHandler
from handlers.time_entry_handler import TimeEntryHandler

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class TelegramBotAdapter(BaseChatAdapter):
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()

        # Handlers / services
        self.auth_handler = AuthHandler()
        self.issue_handler = IssueHandler()
        self.project_handler = ProjectHandler()
        self.time_entry_handler = TimeEntryHandler()

        self.register_handlers()

    async def start(self):
        logger.info("Telegram bot starting...")
        await self.app.initialize()
        await self.app.start()
        await self.app.run_polling()

    async def send_message(self, chat_id: str, message: str):
        await self.app.bot.send_message(chat_id=chat_id, text=message)

    async def send_buttons(self, chat_id: str, message: str, buttons: list):
        keyboard = [[InlineKeyboardButton(btn["text"], callback_data=btn["data"])] for btn in buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self.app.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

    def register_handlers(self):
        logger.debug("Registering handlers...")

        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))

        # Auth conversation
        auth_conv = ConversationHandler(
            entry_points=[CommandHandler("setup", self.auth_handler.start_setup)],
            states={
                self.auth_handler.EMPLOYEE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.get_employee_id)],
                self.auth_handler.REDMINE_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.get_redmine_url)],
                self.auth_handler.API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.get_api_key)],
                self.auth_handler.PROJECT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_handler.get_project_id)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        self.app.add_handler(auth_conv)

        # Log time conversation
        time_conv = ConversationHandler(
            entry_points=[
                CommandHandler("logtime", self.time_entry_handler.start_log_time),
                CallbackQueryHandler(self.time_entry_handler.start_log_time, pattern="^menu_logtime$")
            ],
            states={
                self.time_entry_handler.GETTING_WORK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.time_entry_handler.process_work_log)
                ],
                self.time_entry_handler.CONFIRMING: [
                    CallbackQueryHandler(self.time_entry_handler.confirm_log)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
            allow_reentry=True,
        )
        self.app.add_handler(time_conv)

        # Issue creation conversation
        issue_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.issue_handler.start_create_issue, pattern="^menu_create_issue$")],
            states={
                self.issue_handler.ASK_PROJECT: [CallbackQueryHandler(self.issue_handler.handle_project_choice)],
                self.issue_handler.ASK_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.issue_handler.handle_subject)],
                self.issue_handler.ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.issue_handler.handle_description)],
                self.issue_handler.ASK_PRIORITY: [CallbackQueryHandler(self.issue_handler.handle_priority)],
                self.issue_handler.ASK_TRACKER: [CallbackQueryHandler(self.issue_handler.handle_tracker)],
                self.issue_handler.CONFIRM_CREATE: [CallbackQueryHandler(self.issue_handler.confirm_create_issue)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
            allow_reentry=True,
        )
        self.app.add_handler(issue_conv)

        # General handlers
        self.app.add_handler(CallbackQueryHandler(self.issue_selected_callback, pattern=r"^logtime_"))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.time_entry_handler.quick_log_for_selected_issue))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logger.debug("Handler registration complete.")

    # --------------------- Commands ---------------------
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_msg = f"""
👋 *Welcome to Redmine Integrated Chatbot(RIC) for Lumiq*, {user.first_name}!

I can help you view and log time to your Redmine tasks, projects, and issues — all right here.

*Get started:*
Step1: /setup - Connect your Redmine account 
Step2: /menu - Open the control panel and access all features

Once setup is completed and authenticated, you can also use natural language to access all features like:
> "Show my open issues"  
> "Log 2 hours for bug fix"

* Enter /help to view commands to access full feature set of the chatbot.
"""
        logger.debug("start_command invoked by user=%s", user.id)
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = """
*Available Commands:*

**Setup**
- /setup — Configure Redmine credentials
- /menu — Show main menu

**Quick Actions**
- /logtime — Log time entries
- /myissues — View assigned issues
- /projects — View your projects

**Other**
- /help — Show this message
- /cancel — Cancel current operation
"""
        await update.message.reply_text(help_msg, parse_mode="Markdown")

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        buttons = [
            {"text": "📋 My Issues", "data": "menu_issues"},
            {"text": "📁 My Projects", "data": "menu_projects"},
            {"text": "⏱️ Log Time", "data": "menu_logtime"},
            {"text": "➕ Create Issue", "data": "menu_create_issue"},
            {"text": "⚙️ Setup", "data": "menu_settings"},
            {"text": "🤡 RIC", "data": "RIC"},
        ]

        keyboard = [
            [InlineKeyboardButton(buttons[0]["text"], callback_data=buttons[0]["data"]),
             InlineKeyboardButton(buttons[1]["text"], callback_data=buttons[1]["data"])],
            [InlineKeyboardButton(buttons[2]["text"], callback_data=buttons[2]["data"]),
             InlineKeyboardButton(buttons[3]["text"], callback_data=buttons[3]["data"])],
            [InlineKeyboardButton(buttons[4]["text"], callback_data=buttons[4]["data"]),
             InlineKeyboardButton(buttons[5]["text"], callback_data=buttons[5]["data"])],
        ]

        await update.message.reply_text(
            "🤖 *Main Menu*\nChoose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # --------------------- Callbacks ---------------------
    async def issue_selected_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        parts = query.data.split("_", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            await query.message.reply_text("Invalid issue selection. Try /myissues again.")
            return

        issue_id = parts[1]
        context.user_data["selected_issue_id"] = issue_id
        context.user_data["in_conversation"] = True

        await query.message.reply_text(
            f"Logging time to issue #{issue_id}.\n\n"
            f"Now describe your work in natural language for this issue. Example:\n"
            f"'Worked 2h fixing login bug yesterday'\n\n"
            f"When ready, send your message below 👇"
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        action = query.data

        if action == "menu_issues":
            await self.issue_handler.show_my_issues(update, context)
        elif action == "menu_projects":
            await self.project_handler.show_projects(update, context)
        elif action == "menu_logtime":
            context.user_data.clear()
            await query.edit_message_text("Let's log your time entry...")
            await self.time_entry_handler.start_log_time(update, context)
        elif action == "menu_create_issue":
            await self.issue_handler.start_create_issue(update, context)
        elif action == "menu_settings":
            await self.auth_handler.show_settings(update, context)
        elif action == "RIC":
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            keyboard = [[InlineKeyboardButton("Check Out RIC", url=url)]]
            await query.edit_message_text(text="Click below 👇", reply_markup=InlineKeyboardMarkup(keyboard))
        elif action in ["confirm_log", "cancel_log"]:
            await self.time_entry_handler.confirm_log(update, context)
        else:
            await query.message.reply_text("Unknown action. Use /menu to start over.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("in_conversation"):
            return

        message = update.message.text.lower()
        if any(word in message for word in ["issue", "task", "bug"]):
            await self.issue_handler.show_my_issues(update, context)
        elif any(word in message for word in ["project", "projects"]):
            await self.project_handler.show_projects(update, context)
        elif any(word in message for word in ["time", "log", "work"]):
            await update.message.reply_text(
                "To log time, use /logtime or click *Log Time* from /menu", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("I'm not sure what you mean. Try /help or /menu.")

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text("Operation cancelled. Use /menu to start over.")
        return ConversationHandler.END
