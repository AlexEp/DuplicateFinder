# LLM Settings (`llm_settings.json`)

This file allows you to configure the behavior of the LLM (Large Language Model) for image similarity analysis.

## Parameters

*   `"prompt"`: **(string)**
    *   This is the text prompt that is sent to the LLM to generate a description of each image. The model's understanding of the image is based on this description.
    *   **Impact**: A more descriptive prompt can lead to better similarity analysis but may take longer to process. A shorter prompt is faster but might be less accurate.
    *   **Example**: `"Describe this image in detail."`

*   `"embedding_model"`: **(string)**
    *   This setting is reserved for future use. It will allow you to specify different models for generating the embeddings from the text descriptions.
    *   **Current Value**: `"default"` (This is the only option available right now).

*   `"similarity_threshold"`: **(float, 0.0 to 100.0)**
    *   This is the minimum similarity score (as a percentage) required for two images to be considered duplicates.
    *   **Impact**:
        *   A **higher** value (e.g., `95.0`) will result in fewer, but more confident, matches.
        *   A **lower** value (e.g., `85.0`) will find more potential duplicates, but may also include images that are only loosely related.
    *   **Default**: `90.0`
