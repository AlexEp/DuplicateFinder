import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def run(info, options, search_query):
    """
    Finds files matching the search query.
    The search is a simple case-insensitive substring match on the file name.
    """
    logger.info(f"Running find_files strategy with query: '{search_query}'")
    results = []
    if not search_query:
        logger.warning("Search query is empty, returning no results.")
        return results

    search_query = search_query.lower()

    for path_str, file_info in info.items():
        path = Path(path_str)
        if search_query in path.name.lower():
            results.append(file_info)

    logger.info(f"Found {len(results)} files matching the query.")
    return results
