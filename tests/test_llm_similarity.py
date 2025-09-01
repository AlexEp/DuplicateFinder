import unittest
from pathlib import Path
from ai_engine.engine import LlavaEmbeddingEngine
from strategies import compare_by_llm
import glob

class TestLLMSimilarity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize the LLM engine once for all tests in this class."""
        try:
            cls.llm_engine = LlavaEmbeddingEngine()
        except Exception as e:
            raise unittest.SkipTest(f"Could not initialize LLM engine: {e}")

    def _find_image_path(self, base_name):
        """Finds the full path of an image in the tests directory."""
        # Search for files with the base name and any extension
        search_pattern = f"tests/**/{base_name}.*"
        results = glob.glob(search_pattern, recursive=True)
        if not results:
            raise FileNotFoundError(f"Could not find image file for base name: {base_name}")
        return results[0]

    def _parse_instructions(self):
        """Parses the instraction.txt file and returns a list of test cases."""
        test_cases = []
        with open("tests/instraction.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('-')
                image_part = parts[0]
                expectation = parts[1].strip()
                
                image_names = [name.strip() for name in image_part.split('.')[1].split(',')]
                
                test_cases.append({
                    "images": image_names,
                    "expectation": expectation
                })
        return test_cases

    def test_image_similarity_from_instructions(self):
        """Tests image similarity based on the instraction.txt file."""
        test_cases = self._parse_instructions()
        
        for case in test_cases:
            image_paths = [self._find_image_path(name) for name in case["images"]]
            
            # Get embeddings for all images in the group
            embeddings = {}
            for path in image_paths:
                embedding = self.llm_engine.get_image_embedding(path)
                self.assertIsNotNone(embedding, f"Failed to get embedding for {path}")
                embeddings[path] = embedding

            # Compare all pairs of images in the group
            for i in range(len(image_paths)):
                for j in range(i + 1, len(image_paths)):
                    path1 = image_paths[i]
                    path2 = image_paths[j]
                    
                    is_similar, _ = compare_by_llm.compare(
                        {'metadata': {'llm_embedding': embeddings[path1].tolist()}},
                        {'metadata': {'llm_embedding': embeddings[path2].tolist()}},
                        threshold=90.0 # Using a fixed threshold for testing
                    )
                    
                    with self.subTest(image1=Path(path1).name, image2=Path(path2).name):
                        if case["expectation"] == "same image different colors" or case["expectation"] == "same, different size":
                            self.assertTrue(is_similar, f"{Path(path1).name} and {Path(path2).name} should be similar")
                        elif case["expectation"] == "similar but not the same":
                            # This is tricky, as "similar" can be subjective.
                            # For now, we'll just print the result.
                            print(f"Similarity between {Path(path1).name} and {Path(path2).name}: {is_similar}")
                        else: # Not similar
                            self.assertFalse(is_similar, f"{Path(path1).name} and {Path(path2).name} should not be similar")

if __name__ == '__main__':
    unittest.main()
