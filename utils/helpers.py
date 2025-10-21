from datetime import datetime
import re

def parse_duration(text: str) -> float:
    text = text.lower().strip()
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*h(?:our)?s?', text)
    minutes_match = re.search(r'(\d+)\s*m(?:in)?(?:ute)?s?', text)
    
    hours = 0.0
    
    if hours_match:
        hours += float(hours_match.group(1))
    
    if minutes_match:
        hours += float(minutes_match.group(1)) / 60.0
    
    return hours


def format_date(date_str: str) -> str:
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date.strftime('%B %d, %Y')
    except:
        return date_str


def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'


def validate_url(url: str) -> bool:
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)', re.IGNORECASE)
    return pattern.match(url) is not None