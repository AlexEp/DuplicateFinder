# Constants used throughout the application

# Option keys
COMPARE_NAME = 'compare_name'
COMPARE_DATE = 'compare_date'
COMPARE_SIZE = 'compare_size'
COMPARE_CONTENT_MD5 = 'compare_content_md5'
COMPARE_HISTOGRAM = 'compare_histogram'
COMPARE_LLM = 'compare_llm'
HISTOGRAM_METHOD = 'histogram_method'
HISTOGRAM_THRESHOLD = 'histogram_threshold'
LLM_SIMILARITY_THRESHOLD = 'llm_similarity_threshold'
INCLUDE_SUBFOLDERS = 'include_subfolders'

# Metadata keys
METADATA_NAME = 'name'
METADATA_DATE = 'date'
METADATA_SIZE = 'size'
METADATA_MD5 = 'md5'
METADATA_HISTOGRAM = 'histogram'
METADATA_LLM_EMBEDDING = 'llm_embedding'
METADATA_FULLPATH = 'fullpath'
METADATA_RELATIVE_PATH = 'relative_path'

# Default values
DEFAULT_HISTOGRAM_THRESHOLD = 0.9
DEFAULT_DISTANCE_THRESHOLD = 0.1
DEFAULT_LLM_SIMILARITY_THRESHOLD = 0.8

# Magic strings
ALL_FILES_GROUP_KEY = 'all_files'
SIMILARITY_METRICS = ['Correlation', 'Intersection']

# UI Modes
UI_MODE_COMPARE = 'compare'
UI_MODE_DUPLICATES = 'duplicates'

# UI File Types
UI_FILE_TYPE_ALL = 'all'
UI_FILE_TYPE_IMAGE = 'image'
UI_FILE_TYPE_VIDEO = 'video'
UI_FILE_TYPE_AUDIO = 'audio'
UI_FILE_TYPE_DOCUMENT = 'document'

# UI TreeView Tags
UI_TREE_TAG_FILE = 'file_row'
