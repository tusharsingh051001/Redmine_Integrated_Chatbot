###Disclaimer: This readme file is generated using AI. The file may not be completely accurate due to accuracy rate of LLMs. Kindly update owner if any discrepencies are found

# Redmine Integrated Chatbot (RIC)

AI-powered chatbot for Redmine task management. Manage your Redmine tasks, projects, and time entries directly from Telegram, with AI-assisted natural language parsing.

---

## ✨ Features

- 🔗 **Seamless Redmine Integration** – Connect to your Redmine instance and manage tasks effortlessly
- ⏱️ **Natural Language Time Logging** – Log work hours using plain English
- 📋 **Issue Management** – View, create, and manage your assigned issues
- 🤖 **AI-Powered Parsing** – Intelligent interpretation of work logs using Google Gemini
- 🎯 **Interactive Interface** – Easy navigation with buttons and menus
- 🔄 **Modular Architecture** – Easily adaptable to WhatsApp or other chat platforms

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Gemini API Key
- NeonDB database instance
- Redmine instance with API access

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/redmine-integrated-chatbot.git
cd redmine-integrated-chatbot
```

### 2️⃣ Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI Service
GEMINI_API_KEY=your_gemini_api_key_here

# Database
NEONDB_URL=postgresql://user:password@host/database

# Redmine (optional global default)
REDMINE_URL=https://your-redmine-instance.com
```

### 4️⃣ Set Up the Database

Run the database schema in your NeonDB instance:

```bash
psql $NEONDB_URL -f schema.sql
```

### 5️⃣ Run the Bot

```bash
python main.py
```

🎉 Your bot is now running! Open Telegram and start chatting with your bot.

---

## 📖 How to Use

### Available Commands

| Command | Description |
|---------|-------------|
| `/setup` | Configure your Redmine credentials (Employee ID, API Key, Project ID) |
| `/menu` | Show the main menu with interactive buttons |
| `/logtime` | Log your work hours using natural language |
| `/myissues` | View your assigned issues |
| `/projects` | List your projects |
| `/help` | Show all commands and usage tips |
| `/cancel` | Cancel any ongoing operation |

### 💬 Natural Language Time Logging Examples

The AI understands various formats for logging time:

```text
Worked on bug #1234 for 3h and code review for 1.5h on #5678
```

```text
Monday: Development 4h, Testing 2h, issue #2345
Tuesday: Meeting 1h, Documentation 3h, issue #3456
```

```text
Spent 2 hours debugging issue #9876 and 1.5 hours in planning meeting
```

The chatbot will parse your message and automatically create time entries in Redmine.

---

## 📁 Project Structure

```
redmine-integrated-chatbot/
├── adapters/
│   ├── base_adapter.py           # Abstract base class for chat adapters
│   └── telegram_adapter.py       # Telegram-specific implementation
│
├── handlers/
│   ├── auth_handler.py           # Authentication & Redmine setup
│   ├── issue_handler.py          # Issue management operations
│   ├── project_handler.py        # Project-related actions
│   └── time_entry_handler.py     # Time logging with AI parsing
│
├── services/
│   ├── database_service.py       # Database operations
│   ├── redmine_service.py        # Redmine API wrapper
│   └── gemini_service.py         # Google Gemini AI integration
│
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── schema.sql                    # Database schema
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

### Architecture Overview

**Adapters** provide platform-specific implementations for different chat services. The `TelegramBotAdapter` handles Telegram-specific events and can be replaced with adapters for other platforms.

**Handlers** contain the business logic for different features (authentication, issues, projects, time entries). They are platform-agnostic and can be reused across different adapters.

**Services** manage external integrations with Redmine, AI services, and the database. This separation ensures clean code organization and easy testing.

---

## 🔄 Adapting to Other Platforms

Want to use this with WhatsApp, Slack, or Discord? Here's how:

1. **Create a new adapter** in `adapters/` (e.g., `whatsapp_adapter.py`) that inherits from `BaseChatAdapter`

2. **Implement required methods:**
   ```python
   class WhatsAppAdapter(BaseChatAdapter):
       def send_message(self, chat_id, message):
           # Platform-specific message sending
           pass
       
       def send_buttons(self, chat_id, message, buttons):
           # Platform-specific button rendering
           pass
       
       def register_handlers(self):
           # Map platform events to handlers
           pass
   ```

3. **Reuse existing handlers and services** – they're already platform-agnostic!

4. **Update `main.py`** to instantiate your new adapter instead of `TelegramBotAdapter`

---

## 🐛 Troubleshooting

### Bot doesn't respond
- Verify your `TELEGRAM_BOT_TOKEN` is correct
- Ensure the bot is running (`python main.py`)
- Check that you've started a conversation with your bot in Telegram

### Database connection issues
- Confirm your `NEONDB_URL` is correct and accessible
- Verify the database schema has been applied (`schema.sql`)
- Check network connectivity to your NeonDB instance

### AI parsing errors
- Validate your `GEMINI_API_KEY` is active and has quota
- Check the API key has permissions for text generation
- Review the error logs for specific API error messages

### Time entries not logging
- Verify your Redmine API Key in the bot setup
- Confirm the Project ID exists and you have access
- Check that time logging is enabled in your Redmine project
- Ensure the issue numbers you reference exist

### General debugging
- Check the console output for error messages
- Enable debug logging by adding `logging.basicConfig(level=logging.DEBUG)` in `main.py`
- Test Redmine API connectivity manually using your credentials

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

---

## 🙏 Acknowledgments

-Highly supportive and inspiring team from lumiq.ai
---
