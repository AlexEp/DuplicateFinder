Requirements Specification for an LLM-Powered Image Similarity Engine
Part 1: Strategic Analysis and Technology Stack Recommendation
This section outlines the foundational technology choices for the AI engine. It provides a detailed analysis and justification for the selection of a specific Vision Language Model (VLM), a local inference architecture, and a quantization strategy. These recommendations are tailored to meet the project's core constraints: zero cost, local execution on standard consumer hardware, and seamless integration into an existing Python application.

1.1 VLM Selection: LLaVA for Nuanced Similarity vs. CLIP for Baseline Comparison
The selection of the core Vision Language Model is the most critical architectural decision, as it directly determines the system's capabilities, performance profile, and implementation complexity. The primary objective is to assess the similarity between two images with a high degree of accuracy, particularly for identifying near-duplicates. While numerous open-source VLMs are available , the analysis narrows the choice to two principal architectures: OpenAI's foundational CLIP model and the more advanced LLaVA family of models.   

A baseline approach to image similarity involves using a model like CLIP (Contrastive Language-Image Pre-training). CLIP's architecture consists of two parallel encoders, one for images and one for text, which are trained to map corresponding image-text pairs into a shared, high-dimensional embedding space. The similarity between two images can then be quantified by calculating the cosine similarity between their respective embedding vectors. This method is direct, computationally efficient, and well-supported by numerous libraries, making it a strong candidate for general-purpose image search tasks.   

However, the LLaVA (Large Language and Vision Assistant) architecture represents a significant evolution of this concept. LLaVA extends the CLIP framework by connecting a pre-trained and frozen CLIP vision encoder to a powerful Large Language Model (LLM), such as Vicuna or Llama, through a trainable projection matrix. This design enables LLaVA to move beyond simple image-text matching and perform complex visual reasoning, engaging in conversational dialogue about image content.   

For the specific task of duplicate image detection, this architectural difference is paramount. A superficial analysis might conclude that since LLaVA utilizes the same CLIP vision encoder, its raw image embedding capabilities would be identical to CLIP's. However, empirical evidence demonstrates a crucial distinction. LLaVA has been shown to successfully differentiate between images that are nearly indistinguishable within CLIP's own embedding space (i.e., having a cosine similarity greater than 0.99), a scenario where the CLIP model itself performs at random chance. This phenomenon, termed "erroneous agreements" in CLIP, highlights a limitation in its vision-language alignment; the raw embedding contains the necessary information for differentiation, but CLIP's matching mechanism cannot effectively access it.   

The LLaVA architecture overcomes this limitation. The combination of the projection matrix and the subsequent layers of the LLM acts as a sophisticated post-processing and refinement stage for the initial CLIP embedding. The LLM is not merely a passive text generator; it actively participates in the visual understanding process. It provides a "better extraction and utilization strategy" for the nuanced visual information that is present but latent within the CLIP vector. By processing the visual features through its vast network, the LLM generates a more contextually rich and semantically discriminative final embedding. This capability is indispensable for a duplicate detection application, where the goal is to identify subtle differences—such as minor edits, different compression artifacts, or slight changes in composition—that distinguish a near-match from a true duplicate.   

Therefore, LLaVA is the recommended model architecture for this engine. While a CLIP-only implementation would be simpler, LLaVA's demonstrated superiority in handling highly similar images makes it the more robust and effective choice for the specified use case.

The following table provides a comparative summary to justify this strategic decision.

Model/Architecture	Core Mechanism	Similarity Method	Capability for Nuance	Implementation Complexity	Suitability for Duplicate Detection
CLIP	Image & Text Encoders map to a shared embedding space.	Direct cosine similarity on generated embeddings.	
Moderate. Prone to "erroneous agreements" on highly similar images.   

Low. Well-established libraries and straightforward encode_image methods.   

Good. Effective for general similarity and finding visually similar items.
LLaVA	CLIP Vision Encoder output is projected into an LLM's embedding space.	Generate a final, context-aware embedding, then compute cosine similarity.	
High. Can distinguish between images with >0.99 CLIP similarity by leveraging the LLM for deeper analysis.   

Moderate. Requires managing both an LLM GGUF and a multimodal projector (mmproj) file, using lower-level APIs for embedding generation.   

Excellent. Superior for identifying the subtle differences that disqualify an image as a true duplicate.
1.2 Local Inference Architecture: llama-cpp-python for Performance and Control
To run the selected LLaVA model locally on consumer hardware, a highly efficient inference engine is non-negotiable. The landscape of local LLM tools includes user-friendly platforms like Ollama and LM Studio, as well as lower-level programming libraries such as llama-cpp-python.   

Ollama provides an exceptionally streamlined experience for downloading, managing, and running local models through a simple command-line interface or a clean Python API. Its design philosophy prioritizes ease of use, abstracting away much of the complexity of model configuration. While excellent for rapid prototyping and general chat applications, its high-level API for generating embeddings is less mature and may not expose the fine-grained control necessary to implement the specific LLaVA embedding workflow required for this project.   

In contrast, llama-cpp-python serves as a direct Python binding for the llama.cpp library, a C++ implementation renowned for its performance and optimization for a wide range of hardware, including CPUs and consumer GPUs. This library provides a more granular, powerful API that allows for direct manipulation of the model's context, precise control over GPU layer offloading, and, most importantly, access to the low-level functions required to generate image embeddings via LLaVA's unique two-stage process. This level of control is essential for integrating the AI engine into an existing application where resource management, performance tuning, and predictable behavior are critical.   

Therefore, llama-cpp-python is the recommended inference library. Its superior performance, direct API for embedding generation, and detailed control over hardware acceleration make it the optimal choice for a production-oriented feature.

The feasibility of this entire solution is a testament to the collaborative and layered nature of the open-source AI ecosystem. This project stands on the shoulders of several distinct yet interconnected initiatives. The process begins with the release of powerful open-weight LLMs like Meta's Llama series. Researchers then build upon this foundation, combining it with other open technologies like CLIP to create novel multimodal architectures such as LLaVA. Concurrently, a separate community effort, led by the    

llama.cpp project, focuses on creating a high-performance C++ runtime capable of executing these large models efficiently on consumer-grade hardware. This runtime effort leads to the development of a standardized and highly efficient file format, GGUF, which is specifically designed for quantized models that can run on CPUs with optional GPU offloading. To make this powerful C++ backend accessible to the world's most popular data science language, developers create robust Python bindings like    

llama-cpp-python. Finally, model specialists in the community, such as "TheBloke," leverage this entire toolchain to quantize and distribute thousands of models in the GGUF format, making them readily accessible to developers. The proposed AI engine is not the product of a single piece of software but rather the culmination of this entire open-source value chain.   

1.3 Quantization Strategy: GGUF for Optimal CPU/GPU Hybrid Performance
The full-precision, floating-point versions of LLaVA models are prohibitively large for typical consumer hardware, with a 7-billion-parameter model requiring over 14 GB of VRAM for the weights alone, before accounting for the context cache. Quantization—the process of reducing the numerical precision of a model's weights—is therefore a mandatory step. This technique significantly reduces the model's memory footprint (both on disk and in RAM/VRAM) and often increases inference speed, with a minimal and often imperceptible impact on accuracy.   

The GGUF (GGML Universal Format) is the modern standard file format for models intended to be run with llama.cpp. It is engineered for CPU-first execution but includes metadata that allows the    

llama.cpp runtime to seamlessly offload a specified number of model layers to a GPU if one is available. This hybrid CPU/GPU approach is perfectly suited to the project's constraint of running on a "standard home computer," which encompasses a wide variety of hardware configurations, from CPU-only laptops to desktops with consumer-grade GPUs.   

GGUF models are offered at various quantization levels, denoted by names like Q2_K, Q4_K_M, Q5_K_M, and Q8_0. These levels represent a trade-off: lower bit-per-weight values result in smaller file sizes and faster performance on CPU, but with a greater potential for accuracy degradation. For a 7-billion-parameter model, quantization levels in the 4-bit to 5-bit range are widely considered to offer the best balance of performance and quality.   

Therefore, a Q4_K_M or Q5_K_M quantized GGUF version of llava-v1.5-7b is recommended. This reduces the model's file size from approximately 14 GB (in 16-bit float) to a much more manageable 4-5 GB. This size is viable for systems with 16 GB of total system RAM and allows for full offloading to consumer GPUs with 8 GB or more of VRAM, while retaining a very high level of accuracy for visual understanding tasks. Community benchmarks confirm that models of this size and quantization level can achieve real-time or near-real-time performance on typical consumer hardware.   

Part 2: AI Engine Technical Requirements Specification
This section provides a formal, step-by-step specification for the AI engine. It defines the system's architecture, its external interface contract, the precise sequence of internal operations, and the expected data formats.

2.1 System Architecture and Data Flow
The AI engine shall be implemented as a self-contained module with a clear separation of concerns. The architecture comprises the following logical components:

Input Handler: A public-facing function that accepts the file paths of the two images to be compared. It is responsible for validating the existence of the files.

Metadata Extractor: A dedicated utility module that utilizes the Pillow library to read and parse image properties. It extracts both basic metadata (format, dimensions, mode) and detailed EXIF data where available.

LLaVA Inference Core: The central processing unit of the engine, powered by the llama-cpp-python library. This component is responsible for loading the necessary model files at initialization and managing the inference process. It requires two distinct model files to function:

The main quantized LLaVA model in GGUF format (e.g., llava-v1.5-7b-Q5_K_M.gguf).

The corresponding multimodal projector file, also in GGUF format (e.g., mmproj-model-f16.gguf), which contains the trained CLIP vision encoder and the projection matrix.   

Embedding Cache: An optional but highly recommended component to enhance performance. This can be implemented as a simple in-memory dictionary or a more persistent disk-based key-value store (e.g., using shelve or a lightweight database). It will store previously computed image embeddings, using the image file path or a content hash as the key, to avoid redundant and computationally expensive inference operations.

Similarity Calculator: A utility module containing the logic to compute the cosine similarity between two embedding vectors.

Output Formatter: A final stage that assembles the extracted metadata and the computed similarity score into the specified JSON structure for output.

The data flow through the system is sequential:

The Input Handler receives two image file paths.

For each path, the Metadata Extractor is invoked to load the image and extract its metadata.

For each path, the LLaVA Inference Core is invoked (checking the Embedding Cache first) to generate a high-dimensional embedding vector.

The two resulting embedding vectors are passed to the Similarity Calculator.

The Output Formatter combines the metadata from both images and the final similarity score into a single data structure.

The final JSON object is returned to the caller.

2.2 Interface Contract (Input/Output)
The AI engine shall expose a single, well-defined function that adheres to the following contract.

Function Signature (Python):

Python

def calculate_similarity(image_path_1: str, image_path_2: str) -> dict:
    """
    Calculates the similarity between two images and extracts their metadata.

    Args:
        image_path_1: The file path to the first image.
        image_path_2: The file path to the second image.

    Returns:
        A dictionary containing the metadata of both images and their
        similarity score as a percentage.
    """
    # Implementation follows the processing pipeline defined in section 2.3.
    pass
Input:

image_path_1 (str): An absolute or relative path to the first image file.

image_path_2 (str): An absolute or relative path to the second image file.

Output:

The function shall return a JSON object (represented as a Python dict) with the following structure. All keys are mandatory. If EXIF data is not present in an image, the "exif" key should map to an empty dictionary {}.

JSON

{
  "image_1_metadata": {
    "filename": "path/to/image1.jpg",
    "format": "JPEG",
    "mode": "RGB",
    "size": ,
    "exif": {
      "Make": "Canon",
      "Model": "Canon EOS R5",
      "DateTime": "2023:10:27 10:30:00"
    }
  },
  "image_2_metadata": {
    "filename": "path/to/image2.png",
    "format": "PNG",
    "mode": "RGBA",
    "size": ,
    "exif": {}
  },
  "similarity_score_percent": 95.7
}
2.3 Step-by-Step Processing Pipeline
The internal logic of the calculate_similarity function shall follow this precise pipeline.

Step 1: Initialization and Model Loading

This step shall be performed once during the application's startup phase to create a singleton instance of the engine, avoiding the high cost of reloading the model on every call.

Instantiate the Llava15ChatHandler from llama_cpp.llama_chat_format. This handler is responsible for managing the multimodal components.

The constructor requires the clip_model_path argument, which must point to the mmproj-model-f16.gguf file.   

Instantiate the main LLaVA model using llama_cpp.Llama. The constructor must be configured with the following critical parameters:

model_path: Path to the main quantized LLaVA GGUF file (e.g., llava-v1.5-7b-Q5_K_M.gguf).

chat_handler: The Llava15ChatHandler instance created in the previous step.

n_ctx (Context Size): Must be set to a value sufficient to hold the image embedding tokens plus any prompt tokens. A value of 2048 or 4096 is recommended. LLaVA 1.5 generates 576 tokens for its image embedding.   

n_gpu_layers: The number of model layers to offload to the GPU. Set to 0 for CPU-only operation, -1 to offload all possible layers, or a positive integer for partial offloading. This value should be configurable based on the end-user's hardware.   

embedding: This must be explicitly set to True. This flag enables the llm.embed() method and the underlying functionality for generating embeddings.   

logits_all: This should be set to True as it is required for the LLaVA chat handler to function correctly.   

Step 2: Metadata Extraction

For each of the two input image paths:

Open the image file using PIL.Image.open(image_path).   

Extract basic metadata attributes directly from the Image object: image.filename, image.format, image.mode, and image.size.   

Retrieve the raw EXIF data by calling image.getexif(). This returns an Exif object, which behaves like a dictionary where keys are integer tag IDs.   

If the returned Exif object is not empty, iterate through its items. For each tag_id, value pair, look up the human-readable tag name from the PIL.ExifTags.TAGS dictionary. Store these name-value pairs in a new dictionary for the final output.   

If getexif() returns an empty object or raises an exception, the image has no EXIF data. The corresponding "exif" field in the output JSON shall be an empty dictionary. This is common for formats like PNG or for JPEGs that have been stripped of their metadata.   

Assemble the extracted information into the image_N_metadata dictionary structure.

Step 3: Image Embedding Generation

This is the most computationally intensive and technically complex step. It must be executed for each of the two images.

Cache Check: Before processing, check the Embedding Cache using the image's file path (or a more robust content hash) as the key. If a pre-computed embedding exists, retrieve it and proceed to the next image, skipping the following sub-steps.

Image Loading: Open the image file and read its entire content into a byte array.   

CLIP Projection: Use the low-level C++ bindings exposed through the chat_handler to process the image bytes. This involves calling llava.llava_image_embed_make_with_bytes. This function passes the image data through the CLIP vision encoder and the projection layer (both contained within the mmproj file) to produce an initial, projected embedding structure.   

LLM Evaluation: The projected embedding from the previous step is not the final embedding. It represents the image in a format that the LLM can understand, but it has not yet been processed by the LLM's own layers. This is accomplished by calling llava.llava_eval_image_embed. This function takes the projected embedding and "evaluates" it within the main LLM's context, effectively processing it through the initial layers of the language model to create a context-aware representation.   

Final Embedding Extraction: After the evaluation step, the final, semantically rich embedding is present in the LLM's internal state. Extract this embedding as a NumPy array by calling llama_cpp.llama_get_embeddings on the LLM context. This vector represents the engine's complete understanding of the image's content.   

Cache Update: Store the newly generated NumPy embedding vector in the Embedding Cache with its corresponding key.

Context Reset: This is a critical and mandatory final action. After generating an embedding for a single image, the LLM's internal state (its context) must be cleared by calling llm.reset(). Failure to do so will cause the state from the first image to "leak" into the processing of the second image, contaminating the results and leading to incorrect similarity scores.   

Step 4: Similarity Computation

With the two embedding vectors, vec1 and vec2 (as NumPy arrays), from Step 3, compute their cosine similarity. Cosine similarity is preferred over Euclidean distance for high-dimensional vectors like these because it is invariant to vector magnitude and focuses solely on the orientation (angle) of the vectors, which better captures semantic relatedness. In high-dimensional spaces, Euclidean distance can be misleading due to the "curse of dimensionality," where distances between most points become almost uniform.   

The cosine similarity is calculated as the dot product of the vectors divided by the product of their L2 norms (magnitudes).   

similarity= 
∥ 
v 
1


​
 ∥∥ 
v 
2
​

​
 ∥
v 
1
​
 ⋅ 
v 
2
​
​
 
This can be implemented efficiently in NumPy:

Python

import numpy as np

# Normalize the vectors to unit length
vec1_norm = vec1 / np.linalg.norm(vec1)
vec2_norm = vec2 / np.linalg.norm(vec2)

# Compute the dot product, which is equivalent to cosine similarity for unit vectors
similarity = np.dot(vec1_norm, vec2_norm)
The resulting similarity score will be in the range [−1.0,1.0], where 1.0 indicates identical vectors, 0.0 indicates orthogonality (no relation), and −1.0 indicates diametrically opposed vectors.

Convert this score to a percentage in the range $$. A linear mapping is appropriate:

percentage= 
2
(similarity+1)
​
 ×100
Step 5: Response Assembly

Combine the two metadata dictionaries generated in Step 2 and the final similarity percentage from Step 4 into a single dictionary.

Ensure this final dictionary strictly conforms to the structure defined in the Interface Contract (Section 2.2).

Return the completed dictionary.

Part 3: Implementation Guidance and Performance Considerations
This section provides practical guidance for the implementing engineer, covering hardware considerations, environment setup, and strategies for handling potential errors and edge cases.

3.1 Hardware Profiling and Optimization
The performance of the AI engine is heavily dependent on the end-user's hardware. The system must be designed to function on a baseline configuration while taking full advantage of more powerful hardware when available.

Baseline (CPU-only): On a modern multi-core CPU (e.g., Intel 8th gen or newer, AMD Ryzen), a 7B parameter model quantized to Q4_K_M is functional. However, the embedding generation process will be slow, potentially taking several seconds per image. Prompt processing performance on CPU is highly dependent on matrix multiplication kernels and memory bandwidth. This performance level is acceptable for background or batch processing tasks but not for real-time interactive use.   

GPU Offloading: The most significant performance gain comes from offloading model layers to a GPU. A "standard home computer" in 2025 is likely to have a discrete NVIDIA GPU (e.g., RTX 3060 with 8GB or 12GB VRAM) or an Apple Silicon Mac with unified memory.   

The n_gpu_layers parameter in the Llama constructor is the key control for this. The developer should aim to offload as many layers as possible without exceeding the GPU's available VRAM.

For a llava-v1.5-7b model quantized to Q5_K_M (~4.7 GB), a GPU with 8 GB of VRAM can comfortably offload all layers (n_gpu_layers = -1). This will dramatically accelerate the embedding generation process, reducing the time from seconds to hundreds of milliseconds per image.   

Community benchmarks show that even partial offloading provides substantial speed improvements over CPU-only inference. The application should ideally expose this as a user-configurable setting.   

RAM Requirements: A minimum of 16 GB of system RAM is strongly recommended. This memory must accommodate the operating system, the Python application itself, the model weights (the portion not offloaded to VRAM), and the model's key-value cache during inference. Running with less than 16 GB is possible with smaller models or more aggressive quantization but may lead to heavy use of swap space and poor performance.   

3.2 Dependencies and Environment Setup
A robust and correctly configured environment is crucial for the engine's stability and performance.

Python Packages: A requirements.txt or equivalent dependency management file should specify the following core packages:

llama-cpp-python: The core inference library.

numpy: For all numerical vector operations.

Pillow: For all image I/O and metadata extraction tasks.   

Compilation of llama-cpp-python: A standard pip install llama-cpp-python will often result in a CPU-only build with suboptimal performance. To enable hardware acceleration, the package must be compiled from source with specific environment variables set prior to installation.

For NVIDIA GPUs (CUDA): The CUDA Toolkit must be installed on the system. The installation command must be prefixed with the appropriate environment variable: CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir.   

For Apple Silicon (Metal): To leverage the GPU on M-series Macs, the Metal backend must be enabled during compilation: CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir.   

For Optimized CPU (OpenBLAS/BLAS): To achieve better performance in CPU-only scenarios, it is recommended to compile with support for a Basic Linear Algebra Subprograms (BLAS) library like OpenBLAS: CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python --force-reinstall --no-cache-dir.   

3.3 Edge Cases and Error Handling
The engine must be robust against common failures and unexpected inputs.

Invalid or Corrupted Image Files: The call to PIL.Image.open() should be wrapped in a try...except block to handle IOError and other PIL.UnidentifiedImageError exceptions that occur when a file is not a valid image, is corrupted, or is in an unsupported format. The engine should return a descriptive error message in such cases.   

Missing Model Files: The engine's initialization routine must verify the existence of both the main LLaVA GGUF file and the mmproj GGUF file at their specified paths. If either file is missing, the application should fail to start with a clear, user-friendly error message indicating which file is missing and where it is expected to be.

Out-of-Memory (OOM) Errors: If the user attempts to load a model that is too large for their available RAM or VRAM, the llama.cpp backend may crash. While difficult to catch gracefully from Python, the application documentation should clearly state the memory requirements for different quantization levels and advise users to select a smaller model or reduce the number of offloaded GPU layers (n_gpu_layers) if they encounter crashes.

Transparent Images (e.g., PNG with Alpha Channel): Some VLMs can produce inconsistent results when processing images with an alpha (transparency) channel. To ensure consistent and reliable processing, it is a mandatory pre-processing step to convert all images to a standard    

RGB format before they are passed to the embedding generator. This can be done easily with Pillow: image = image.convert("RGB"). This removes the alpha channel by blending the image against a default black background.   

Appendix
A.1 Reference Code Snippet for LLaVA Embedding Generation
The following Python code provides a reference implementation for the most critical and complex part of the pipeline: initializing the LLaVA model with llama-cpp-python and generating a single image embedding. This snippet encapsulates the logic derived from community examples and technical deep dives.   

Python

import llama_cpp
import llama_cpp.llama_chat_format as llama_chat_format
import numpy as np
import array
import ctypes

# --- Configuration ---
# These paths must point to the downloaded GGUF model files.
LLAVA_MODEL_PATH = "./models/llava-v1.5-7b-Q5_K_M.gguf"
MMPROJ_MODEL_PATH = "./models/mmproj-model-f16.gguf"

class LlavaEmbeddingEngine:
    def __init__(self, llava_path, mmproj_path, gpu_layers=0):
        """
        Initializes the LLaVA embedding engine. This is a costly operation
        and should be done only once per application lifecycle.
        """
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

        # 1. Load image into a byte array.
        with open(image_path, "rb") as f:
            image_bytes = f.read()

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

# --- Example Usage ---
# if __name__ == "__main__":
#     engine = LlavaEmbeddingEngine(LLAVA_MODEL_PATH, MMPROJ_MODEL_PATH, gpu_layers=-1)
#     embedding1 = engine.get_image_embedding("path/to/image1.jpg")
#     embedding2 = engine.get_image_embedding("path/to/image2.jpg")
#     print("Embedding 1 Shape:", embedding1.shape)
#     print("Embedding 2 Shape:", embedding2.shape)
A.2 GGUF Quantization Level Reference Table
The following table serves as a practical guide for selecting the appropriate GGUF quantization file for a 7-billion-parameter model like llava-v1.5-7b. The choice depends on the available hardware and the desired balance between performance, memory usage, and accuracy. The "K-Quants" (_K) are generally recommended as they use a more sophisticated mixed-precision approach, offering better quality for a given file size compared to older methods.   

Quant Method	Bits per Weight (Effective)	Size (7B Model)	Min. RAM/VRAM Required	Quality / Perplexity	Recommended Use Case
F16 (Unquantized)	16.0	~13.5 GB	~15 GB	None (Baseline)	Research, benchmarking, or systems with >24 GB VRAM.
Q8_0	8.0	~7.1 GB	~8 GB	Extremely low loss.	High-quality inference on systems with >=12 GB VRAM or >16 GB RAM.
Q6_K	6.56	~5.5 GB	~6.5 GB	Very low loss. Excellent quality.	A high-quality option for GPUs with 8-12 GB VRAM.
Q5_K_M	5.5	~4.7 GB	~5.5 GB	Low loss. Recommended balance.	Recommended. Excellent balance of size, speed, and quality for 8 GB VRAM GPUs and 16 GB RAM systems.
Q4_K_M	4.5	~4.3 GB	~5 GB	Small, acceptable loss.	Recommended. A slightly smaller and faster alternative to Q5_K_M, ideal for memory-constrained systems.
Q3_K_M	3.44	~3.4 GB	~4 GB	Medium loss. Noticeable quality drop.	For very low-resource environments where size is the primary constraint.
Q2_K	2.56	~2.9 GB	~3.5 GB	High loss. Significant quality drop.	Not recommended for nuanced tasks like image similarity. For experimental use only.

Export to Sheets
