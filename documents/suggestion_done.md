# Implemented Suggestions

This file contains suggestions that have been implemented.

---

## 4. Configuration Management

**Observation:**
Configuration is scattered across `settings.json`, `llm_settings.json`, and hardcoded paths in `ai_engine/engine.py`. This makes configuration difficult to manage.

**Suggestions:**

*   **Create a Centralized `Config` Class:** Implement a singleton `Config` class that loads all settings from all configuration files (`settings.json`, `llm_settings.json`, etc.) upon application startup.
    *   This class would provide a single, consistent interface for the rest of the application to access configuration values (e.g., `Config.get('log_level')`, `Config.get('llm.similarity_threshold')`).
    *   This removes the need for multiple `try...except` blocks for file loading throughout the code.

*   **Move Hardcoded Paths to Configuration:** The model paths `LLAVA_MODEL_PATH` and `MMPROJ_MODEL_PATH` in `ai_engine/engine.py` should be removed and placed into `settings.json` or a new `models.json` config file. This allows users to change model locations without editing the source code.

*   **Externalize More Settings:** The file extension lists (`VIDEO_EXTENSIONS`, `AUDIO_EXTENSIONS`, `DOCUMENT_EXTENSIONS`) in `strategies/utils.py` should be moved into `settings.json` to make them user-configurable.

---
