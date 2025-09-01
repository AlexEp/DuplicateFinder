
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
        # CRITICAL: Reset the LLM context to prevent state leakage.
        self.llm.reset()

        try:
            # Per instructions, convert all images to RGB to handle transparency.
            image = Image.open(image_path).convert("RGB")
            
            # The reference code uses a complex way to get bytes. PIL can do this easily.
            # However, the reference code uses a low-level C++ binding that expects bytes.
            # Let's stick to the reference implementation's method of reading bytes from file.
            with open(image_path, "rb") as f:
                image_bytes = f.read()

        except Exception as e:
            print(f"Error reading or converting image {image_path}: {e}")
            return None


        # 2. Use the chat_handler's low-level C++ bindings to create a
        #    projected embedding from the image bytes via the CLIP model.
        data_array = array.array("B", image_bytes)
        c_ubyte_ptr = (ctypes.c_ubyte * len(data_array)).from_buffer(data_array)
        
        embed_ptr = self.llm.chat_handler._llava_cpp.llava_image_embed_make_with_bytes(
            ctx_clip=self.llm.chat_handler.clip_ctx,
            n_threads=self.llm.n_threads,
            image_bytes=c_ubyte_ptr,
            image_bytes_length=len(image_bytes),
        )

        try:
            # 3. Evaluate the projected embedding within the LLM's context.
            n_past = ctypes.c_int(self.llm.n_tokens)
            n_past_ptr = ctypes.pointer(n_past)
            
            self.llm.chat_handler._llava_cpp.llava_eval_image_embed(
                ctx_llama=self.llm.ctx,
                embed=embed_ptr,
                n_batch=self.llm.n_batch,
                n_past=n_past_ptr,
            )
            self.llm.n_tokens = n_past.value

            # 4. Extract the final embedding from the LLM's state.
            # The embedding size for Llama-2 7B is 4096.
            embedding_size = self.llm.n_embd()
            embedding_array = (ctypes.c_float * embedding_size)()
            
            llama_cpp.llama_get_embeddings(self.llm.ctx, embedding_array)
            
            embedding = np.array(embedding_array, dtype=np.float32)
            return embedding

        finally:
            # 5. Free the memory allocated for the embedding structure.
            self.llm.chat_handler._llava_cpp.llava_image_embed_free(embed_ptr)
