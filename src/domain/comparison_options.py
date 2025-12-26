from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ComparisonOptions:
    """Value object for UI selections and settings."""
    file_type_filter: str = "all"
    include_subfolders: bool = True
    compare_name: bool = False
    compare_date: bool = False
    compare_size: bool = True
    compare_content_md5: bool = False
    compare_histogram: bool = False
    compare_llm: bool = False
    histogram_method: str = "intersection"
    histogram_threshold: float = 0.9
    llm_similarity_threshold: float = 0.8
    move_to_path: str = ""

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Provides a dictionary compatible with legacy components.
        Includes both top-level keys for calculators/comparators and 
        the nested 'options' key for strategy discovery.
        """
        flat = {
            "file_type_filter": self.file_type_filter,
            "move_to_path": self.move_to_path,
            "include_subfolders": self.include_subfolders,
            "compare_name": self.compare_name,
            "compare_date": self.compare_date,
            "compare_size": self.compare_size,
            "compare_content_md5": self.compare_content_md5,
            "compare_histogram": self.compare_histogram,
            "compare_llm": self.compare_llm,
            "histogram_method": self.histogram_method,
            "histogram_threshold": self.histogram_threshold,
            "llm_similarity_threshold": self.llm_similarity_threshold
        }
        # Nested 'options' part for find_duplicates_strategy.run logic
        flat["options"] = flat.copy()
        return flat

    def to_save_dict(self) -> Dict[str, Any]:
        """Bridge method to return old-style nested options dictionary for database persistence."""
        return {
            "file_type_filter": self.file_type_filter,
            "move_to_path": self.move_to_path,
            "options": {
                "include_subfolders": self.include_subfolders,
                "compare_name": self.compare_name,
                "compare_date": self.compare_date,
                "compare_size": self.compare_size,
                "compare_content_md5": self.compare_content_md5,
                "compare_histogram": self.compare_histogram,
                "compare_llm": self.compare_llm,
                "histogram_method": self.histogram_method,
                "histogram_threshold": self.histogram_threshold,
                "llm_similarity_threshold": self.llm_similarity_threshold
            }
        }
