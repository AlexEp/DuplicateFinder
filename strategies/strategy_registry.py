from . import compare_by_size, compare_by_date, compare_by_content_md5, compare_by_histogram, compare_by_llm
import constants

_strategies = {
    constants.COMPARE_SIZE: compare_by_size.compare,
    constants.COMPARE_DATE: compare_by_date.compare,
    constants.COMPARE_CONTENT_MD5: compare_by_content_md5.compare,
    constants.COMPARE_HISTOGRAM: compare_by_histogram.compare,
    constants.COMPARE_LLM: compare_by_llm.compare,
}

def get_active_strategies(opts):
    """Returns a list of active strategies based on the options."""
    active_strategies = []
    for key, strategy in _strategies.items():
        if opts.get(key):
            active_strategies.append(strategy)
    return active_strategies
