import base64
import json
import llama_cpp
import llama_cpp.llama_chat_format as llama_chat_format
import numpy as np
import array
import ctypes
from PIL import Image
import os
import llama_cpp.llava_cpp as llava_cpp
from config import config

class LlavaEmbeddingEngine:
    def __init__(self, gpu_layers=0):
        """
        Initializes the LLaVA embedding engine. This is a costly operation
        and should be done only once per application lifecycle.
        """
        llava_path = config.get("models.llava_model_path")
        mmproj_path = config.get("models.mmproj_model_path")

        if not llava_path or not mmproj_path:
            raise ValueError("Model paths are not defined in the configuration.")

        if not os.path.exists(llava_path) or not os.path.exists(mmproj_path):
            raise FileNotFoundError(f"Model files not found. Please ensure '{llava_path}' and '{mmproj_path}' exist.")

        self.mmproj_path = mmproj_path
        self.clip_ctx = llava_cpp.clip_model_load(self.mmproj_path.encode("utf-8"), 0)
        if self.clip_ctx is None:
            raise RuntimeError(f"Failed to load CLIP model from {self.mmproj_path}")

        try:
            # We don't need a chat handler for embeddings
            self.llm = llama_cpp.Llama(
                model_path=llava_path,
                n_ctx=2048,
                n_gpu_layers=gpu_layers,
                logits_all=True,
                embedding=True,
                verbose=True
            )
        except Exception as e:
            print(f"Error initializing LLaVA model: {e}")
            self.__del__() # Manually call destructor to free clip context
            raise

    def __del__(self):
        """Frees the CLIP model context when the object is destroyed."""
        if hasattr(self, 'clip_ctx') and self.clip_ctx:
            llava_cpp.clip_free(self.clip_ctx)
            self.clip_ctx = None

    def get_image_embedding(self, image_path: str) -> np.ndarray:
        """
        Generates a semantically rich embedding for a single image.
        """
        self.llm.reset()
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return None

        data_array = array.array("B", image_bytes)
        c_ubyte_ptr = (ctypes.c_ubyte * len(data_array)).from_buffer(data_array)

        embed_ptr = llava_cpp.llava_image_embed_make_with_bytes(
            ctx_clip=self.clip_ctx,
            n_threads=self.llm.n_threads,
            image_bytes=c_ubyte_ptr,
            image_bytes_length=len(image_bytes),
        )

        if not embed_ptr:
            print(f"Warning: Could not process image {image_path}. Unsupported format.")
            return None
        
        try:
            n_past = ctypes.c_int(self.llm.n_tokens)
            n_past_ptr = ctypes.pointer(n_past)
            
            llava_cpp.llava_eval_image_embed(
                ctx_llama=self.llm.ctx,
                embed=embed_ptr,
                n_batch=self.llm.n_batch,
                n_past=n_past_ptr,
            )
            self.llm.n_tokens = n_past.value

            embedding_size = self.llm.n_embd()
            embedding_array = (ctypes.c_float * embedding_size)()
            
            llama_cpp.llama_get_embeddings(self.llm.ctx, embedding_array)
            
            embedding = np.array(embedding_array, dtype=np.float32)
            return embedding

        finally:
            llava_cpp.llava_image_embed_free(embed_ptr)