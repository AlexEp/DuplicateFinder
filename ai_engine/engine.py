
import base64
import llama_cpp
import llama_cpp.llama_chat_format as llama_chat_format
import numpy as np
import array
import ctypes
from PIL import Image
import os

# --- Configuration ---
# These paths must point to the downloaded GGUF model files.
LLAVA_MODEL_PATH = "./models/llava-v1.5-7b-Q5_K_M.gguf"
MMPROJ_MODEL_PATH = "./models/mmproj-model-f16.gguf"

class LlavaEmbeddingEngine:
    def __init__(self, llava_path=LLAVA_MODEL_PATH, mmproj_path=MMPROJ_MODEL_PATH, gpu_layers=0):
        """
        Initializes the LLaVA embedding engine. This is a costly operation
        and should be done only once per application lifecycle.
        """
        if not os.path.exists(llava_path) or not os.path.exists(mmproj_path):
            raise FileNotFoundError(f"Model files not found. Please ensure '{llava_path}' and '{mmproj_path}' exist.")

        try:
            chat_handler = llama_chat_format.Llava15ChatHandler(
                clip_model_path=mmproj_path,
                verbose=True
            )
            self.llm = llama_cpp.Llama(
                model_path=llava_path,
                chat_handler=chat_handler,
                n_ctx=2048,
                n_gpu_layers=gpu_layers,
                logits_all=True,
                embedding=True,
                verbose=True
            )
        except Exception as e:
            print(f"Error initializing LLaVA model: {e}")
            raise

    def get_image_embedding(self, image_path: str) -> np.ndarray:
        """
        Generates a semantically rich embedding for a single image.
        """
        self.llm.reset()
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            image_data = f"data:image/jpeg;base64,{image_base64}"

            response = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_data}},
                            {"type": "text", "content": "Describe this image in one sentence."}
                        ]
                    }
                ]
            )
            description = response['choices'][0]['message']['content']
            
            embedding_response = self.llm.create_embedding(description)
            embedding = embedding_response['data'][0]['embedding']

            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            if "Failed to create bitmap from image bytes" in str(e):
                print(f"Warning: Could not process image {image_path}. Unsupported format.")
                return None
            else:
                print(f"Error generating embedding for image {image_path}: {e}")
                return None
