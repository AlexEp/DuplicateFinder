from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IView(ABC):
    """Interface for the UI view."""
    
    @abstractmethod
    def update_status(self, message: str, progress_value: Optional[float] = None):
        """Update the status message and progress bar."""
        pass

    @abstractmethod
    def _set_main_ui_state(self, state: str = 'normal'):
        """Set the UI state (e.g., 'normal' or 'disabled')."""
        pass

    @property
    @abstractmethod
    def root(self):
        """The root Tkinter window."""
        pass
