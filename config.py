import json
import logging

logger = logging.getLogger(__name__)

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.config = {}
        self._load_json("settings.json")
        self._load_json("llm_settings.json", parent_key="llm")

    def _load_json(self, filename, parent_key=None):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                if parent_key:
                    self.config[parent_key] = data
                else:
                    self.config.update(data)
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load or parse {filename}: {e}")

    def get(self, key, default=None):
        """
        Retrieves a value from the configuration using dot notation.
        Example: config.get('llm.similarity_threshold')
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

# Global instance for easy access
config = Config()
