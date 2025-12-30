from ..base_comparison_strategy import BaseComparisonStrategy, StrategyMetadata

class DummyStrategy(BaseComparisonStrategy):
    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            option_key='compare_dummy',
            display_name='Dummy Strategy',
            description='A fake strategy for testing',
            tooltip='This is a dummy strategy to verify dynamic UI generation.',
            requires_calculation=False
        )

    @property
    def option_key(self):
        return 'compare_dummy'

    def compare(self, file1_info, file2_info, opts=None):
        return False

    @property
    def db_key(self):
        return 'id' # Just some valid key
