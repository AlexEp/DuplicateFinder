import logging
from typing import List, Dict, Any, Optional
from domain.file_info import FileInfo
from domain.comparison_options import ComparisonOptions
from interfaces.repository_interface import IFileRepository
from interfaces.service_interface import IComparisonService
import logic
from strategies import utils, find_duplicates_strategy

logger = logging.getLogger(__name__)

class ComparisonService(IComparisonService):
    """Concrete implementation of IComparisonService."""
    
    def __init__(self, repository: IFileRepository):
        self._repository = repository

    def compare_folders(self, folder_indices: List[int], options: ComparisonOptions) -> List[List[Dict[str, Any]]]:
        """
        Compares files across multiple folders.
        """
        all_files = []
        for idx in folder_indices:
            files_dict = self._repository.get_all_files(idx, options.file_type_filter)
            all_files.extend(files_dict)
        
        # logic.run_comparison expects a list of dicts. 
        # Since it compares info1 and info2, we can split or pass one empty.
        # But logic.run_comparison is designed for two lists.
        # For multi-folder comparison, we might need a better approach or split all_files.
        # For now, let's stick to two-folder comparison if folder_indices has 2 elements.
        if len(folder_indices) == 2:
            info1 = self._repository.get_all_files(folder_indices[0], options.file_type_filter)
            info2 = self._repository.get_all_files(folder_indices[1], options.file_type_filter)
            return logic.run_comparison(info1, info2, options.to_dict())
        
        return []

    def find_duplicates(self, folder_indices: List[int], options: ComparisonOptions, 
                        file_infos: Optional[List[Dict[str, Any]]] = None) -> List[List[Dict[str, Any]]]:
        """
        Finds duplicates across given folders using the find_duplicates_strategy.
        """
        conn = self._repository.connection
        opts_dict = options.to_dict()
        
        return find_duplicates_strategy.run(
            conn, 
            opts_dict, 
            folder_index=folder_indices, 
            file_infos=file_infos
        )
