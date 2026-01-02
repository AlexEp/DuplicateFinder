from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IView(ABC):
    """Interface for the UI view."""
    
    @abstractmethod
    def update_status(self, message: str, progress_value: Optional[float] = None):
        """Update the status message and progress bar."""
        pass


    @abstractmethod
    def set_ui_state(self, enabled: bool):
        """Enable/disable UI controls."""
        pass

    @abstractmethod
    def remove_result_item(self, item_id: Any):
        """Remove a specific item from the results view."""
        pass

    @property
    @abstractmethod
    def root(self):
        """The root Tkinter window."""
        pass
