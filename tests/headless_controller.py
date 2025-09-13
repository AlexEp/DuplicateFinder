import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from controller import AppController

class HeadlessAppController(AppController):
    def __init__(self, view):
        # We need to call the parent constructor, but we don't have a real view.
        # So we'll pass in the mock view and set is_test to True.
        super().__init__(view, is_test=True)

    def _bind_variables_to_view(self):
        # This method in the parent class tries to access view attributes.
        # We'll override it to do nothing, since we're using a mock view.
        pass

    def _ensure_llm_engine_loaded(self):
        # This method in the parent class can show a messagebox, which we want to avoid in tests.
        # We'll override it to do nothing.
        pass
