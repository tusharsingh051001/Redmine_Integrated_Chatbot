import os
import logging
import json
from datetime import date, datetime
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def parse_time_entries(self, natural_text: str, activities: list):

        today_str = date.today().strftime("%Y-%m-%d") # Use your server's date/timezone
        activity_names = [a["name"] for a in activities]
        logger.debug(natural_text)
        prompt = f"""
            Parse the following work log into structured time entries. Use today's date if no date is mentioned.

            Work Log:
            {natural_text}

            Available Activities: {', '.join(activity_names)}

            Return ONLY a JSON array like this:
            [
            {{
                "date": "YYYY-MM-DD", default to '{today_str}' if date is not specified in the work log
                "hours": float,
                "activity": "activity_name",
                "comments": "description",
                "issue_id": "mandatory issue id"
            }}
            ]

            Rules:
            - Match activities to the closest available activity name
            - Use decimal hours (e.g., 1.5 for 1 hour 30 minutes)
            - If no date mentioned, use the provided default date: {today_str}
            - Comments should be concise
            - Issue ID is mandatory; return a placeholder like 'Unknown' if not mentioned
            - Return valid JSON only, no extra text
            """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            logger.info(f"Gemini response: {text}")
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            entries = json.loads(text)

            if not isinstance(entries, list):
                raise ValueError("Gemini response is not a list")

            for entry in entries:
                required = ["date", "hours", "activity", "comments", "issue_id"]
                if not all(k in entry for k in required):
                    raise ValueError(f"Missing required fields in entry: {entry}")

                if not entry["issue_id"]:
                    entry["issue_id"] = "Unknown"

                entry_date = entry.get("date")
                if entry_date:
                    try:
                        parsed_date = datetime.strptime(entry_date, "%Y-%m-%d")
                        entry["date"] = parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        entry["date"] = date.today().strftime("%Y-%m-%d")
                else:
                    entry["date"] = date.today().strftime("%Y-%m-%d")

            return entries

        except Exception as e:
            logger.error(f"Gemini parsing error: {e}")
            raise ValueError(f"Could not parse work log: {str(e)}")

    def summarize_work(self, time_entries: list):
        if not time_entries:
            return "No work entries found for the specified period."

        entries_text = "\n".join(
            [
                f"- {e.get('date', 'Date')}: {e.get('hours', 0)}h "
                f"on {e.get('activity', 'Task')} - {e.get('comments', 'No description')} "
                f"(Issue: {e.get('issue_id', 'Unknown')})"
                for e in time_entries
            ]
        )

        prompt = f"""
            Create a concise professional summary from these time entries:

            {entries_text}

            Provide:
            1. Total hours worked
            2. Key activities breakdown
            3. Brief highlights

            Keep it under 150 words.
            """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini summary error: {e}")
            return "Could not generate summary. Please check your time entries manually."
