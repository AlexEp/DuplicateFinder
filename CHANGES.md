# Changelog

## 2025-08-31

- **Feature**: Add LLM-powered image similarity engine.
  - Integrates a LLaVA model to perform semantic comparison of images.
  - Adds a new "LLM Content" comparison option.
  - The engine runs locally and requires users to download model files (see `models/README.md`).
  - This is a resource-intensive feature and works best with GPU acceleration.


## 2025-08-30

- **Feat**: Add preview functionality to context menu.
- **Fix**: Fix context menu functionality.
- **Fix**: Corrected the logic for displaying preview options in the context menu.
- **Feat**: Added support for .flv and .wmv video file previews.

## 2024-07-15
- **Feature**: Add preview for media files.
  - Adds a "Preview" option to the right-click context menu for image, video, and audio files.
  - Images are displayed in a new window.
  - Audio/video files are opened with the default system player.
- **Feature**: Display comparison results in a grid.
  - The results view now shows file name, size, and relative path in a grid format.
  - This provides more information at a glance and is easier to read.
- Initial creation of the changelog.