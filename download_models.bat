@echo off
rem This script downloads the necessary models for the LLM Image Similarity feature.

echo Starting download of LLM models. This will take a significant amount of time and requires approximately 5 GB of free disk space.
echo.

cd models

echo [1/2] Downloading LLaVA v1.5 7B model (llava-v1.5-7b-Q5_K_M.gguf)... 
curl -L -o "llava-v1.5-7b-Q5_K_M.gguf" "https://huggingface.co/second-state/Llava-v1.5-7B-GGUF/resolve/main/llava-v1.5-7b-Q5_K_M.gguf"
if %errorlevel% neq 0 (
    echo ERROR: Failed to download the main model. Please check your internet connection or the URL.
    exit /b %errorlevel%
)
echo.


echo [2/2] Downloading Multimodal Projector (mmproj-model-f16.gguf)...
curl -L -o "mmproj-model-f16.gguf" "https://huggingface.co/second-state/Llava-v1.5-7B-GGUF/resolve/main/llava-v1.5-7b-mmproj-model-f16.gguf"
if %errorlevel% neq 0 (
    echo ERROR: Failed to download the projector model. Please check your internet connection or the URL.
    exit /b %errorlevel%
)
echo.

echo Download complete! The models are now in the 'models' directory.
echo You can now try running the application again.

cd ..
