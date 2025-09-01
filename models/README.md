# Models for LLM Similarity Engine

To use the LLM-based image similarity feature, you need to download the required model files and place them in this directory.

This feature uses the LLaVA 1.5 architecture. You will need two files:

1.  **The main LLaVA model (GGUF format):** This is the core language and vision model.
    -   **Recommended Model:** `llava-v1.5-7b-Q5_K_M.gguf`
    -   **Download Link:** You can find this model on Hugging Face, typically from a community member like "TheBloke". Search for "TheBloke llava-v1.5-7b GGUF".
    -   **File Size:** Approximately 4.7 GB.

2.  **The Multimodal Projector (mmproj) file:** This file contains the CLIP vision encoder needed to process the images.
    -   **Required File:** `mmproj-model-f16.gguf`
    -   **Download Link:** This is usually provided alongside the main model on its Hugging Face page.
    -   **File Size:** Approximately 300 MB.

**Instructions:**

1.  Download both `.gguf` files.
2.  Place them directly inside this `models/` directory.
3.  Ensure the filenames are exactly as listed above.

Once the files are in place, restart the application. The "LLM Content" comparison option should become available.

**Note on Performance:** Running this model is resource-intensive. A minimum of 16 GB of system RAM is recommended. Performance will be significantly better if you have a compatible GPU (NVIDIA or Apple Silicon) and have installed the `llama-cpp-python` library with the correct hardware acceleration flags. See the main project documentation for more details.
