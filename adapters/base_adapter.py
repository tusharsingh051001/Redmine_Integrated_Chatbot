from abc import ABC, abstractmethod

class BaseChatAdapter(ABC):
    """Abstract base class for chat platform adapters"""
    
    @abstractmethod
    def start(self):
        """Start the bot"""
        pass
    
    @abstractmethod
    def send_message(self, chat_id: str, message: str):
        """Send a text message"""
        pass
    
    @abstractmethod
    def send_buttons(self, chat_id: str, message: str, buttons: list):
        """Send a message with buttons"""
        pass
    
    @abstractmethod
    def register_handlers(self):
        """Register all message handlers"""
        pass